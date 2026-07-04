"""Train the phishing-URL classifier.

Dataset: PhiUSIIL Phishing URL Dataset (UCI #967) — ~235k labeled URLs.

We train on the HOSTNAME only, not the full URL. PhiUSIIL's legitimate set is
dominated by bare homepage URLs, so a full-URL model learns "has a long path
=> phishing" and misfires on ordinary deep links (e.g. Wikipedia articles).
The durable phishing signal is in the domain's shape — hyphenated brand
imitations, token stuffing, suspicious TLDs — and path-level tricks are
covered by the rule engine and live page inspection instead. Hosts are
deduplicated before the split so no host appears in both train and test.

Model: char 3-5 gram TF-IDF (capped vocabulary) -> Logistic Regression.

Outputs: ml/artifacts/url_model.joblib + ml/artifacts/url_metrics.json
"""
from __future__ import annotations

import io
import json
import sys
import zipfile
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import joblib
import pandas as pd
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

ML_DIR = Path(__file__).parent
DATA_DIR = ML_DIR / "data"
ARTIFACTS = ML_DIR / "artifacts"
UCI_URL = "https://archive.ics.uci.edu/static/public/967/phiusiil+phishing+url+dataset.zip"
TRANCO_URL = "https://tranco-list.eu/top-1m.csv.zip"
SEED = 42
PER_CLASS = 30_000   # balanced subsample size per class
TRANCO_TRAIN = 20_000  # extra legit hosts added from Tranco
TRANCO_ALLOWLIST = 10_000  # exported for the inference-time allowlist

# Tiny embedded fallback so the pipeline never breaks if the download fails.
FALLBACK = [
    ("https://www.google.com/search?q=weather", 0),
    ("https://en.wikipedia.org/wiki/Bangladesh", 0),
    ("https://github.com/features/actions", 0),
    ("https://www.amazon.com/dp/B08N5WRWNW", 0),
    ("http://paypal-account-verify.secure-login.tk/signin", 1),
    ("http://192.168.12.4/chase/login.php", 1),
    ("https://netfIix-billing-update.com/renew", 1),
    ("http://secure-bankofamerica.co.xyz/verify?id=8842", 1),
]


def load_dataset() -> pd.DataFrame:
    cached = DATA_DIR / "phiusiil.csv"
    if cached.exists():
        print(f"Using cached {cached}")
        return pd.read_csv(cached, usecols=["URL", "label"])

    print(f"Downloading PhiUSIIL dataset from {UCI_URL} ...")
    resp = requests.get(UCI_URL, timeout=180)
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        csv_name = next(n for n in zf.namelist() if n.lower().endswith(".csv"))
        with zf.open(csv_name) as f:
            df = pd.read_csv(f, usecols=["URL", "label"])
    DATA_DIR.mkdir(exist_ok=True)
    df.to_csv(cached, index=False)
    return df


def load_tranco() -> list[str]:
    """Top popular domains (Tranco). Used two ways: extra legitimate training
    samples, and an inference-time allowlist artifact. PhiUSIIL's phishing set
    is full of brand-abuse hosts (google-verify.tk …), which otherwise teaches
    the model that brand substrings mean phishing."""
    cached = DATA_DIR / "tranco.csv"
    if not cached.exists():
        print(f"Downloading Tranco top sites from {TRANCO_URL} ...")
        resp = requests.get(TRANCO_URL, timeout=180)
        resp.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            name = zf.namelist()[0]
            DATA_DIR.mkdir(exist_ok=True)
            cached.write_bytes(zf.read(name))
    df = pd.read_csv(cached, header=None, names=["rank", "domain"],
                     nrows=max(TRANCO_TRAIN, TRANCO_ALLOWLIST))
    return df["domain"].astype(str).str.lower().tolist()


def main() -> int:
    try:
        df = load_dataset()
        # PhiUSIIL: label 1 = legitimate, 0 = phishing. Normalize so 1 = phishing.
        df["label"] = 1 - df["label"].astype(int)
        df = df.rename(columns={"URL": "url"})
        source = "PhiUSIIL Phishing URL Dataset (UCI #967)"
    except Exception as exc:
        print(f"WARNING: dataset download failed ({exc}); using embedded fallback.")
        df = pd.DataFrame(FALLBACK, columns=["url", "label"])
        source = "embedded fallback mini-dataset"

    df = df.dropna()

    def to_host(u: str) -> str:
        """Hostname without leading www. — must match inference-time
        normalization in backend url_features.domain_of()."""
        if "://" not in u:
            u = "http://" + u
        try:
            host = (urlparse(u).hostname or "").lower()
        except ValueError:
            return ""
        return host.removeprefix("www.")

    df["host"] = df["url"].astype(str).map(to_host)
    df = df[df["host"].str.contains(r"\.", regex=True)]
    # One row per host so identical hosts can't leak across the split
    df = df.drop_duplicates(subset=["host"])

    # Balanced subsample to keep the artifact small
    parts = []
    for label, group in df.groupby("label"):
        parts.append(group.sample(min(len(group), PER_CLASS), random_state=SEED))
    df = pd.concat(parts)[["host", "label"]]

    tranco: list[str] = []
    try:
        tranco = load_tranco()
        extra = pd.DataFrame({"host": tranco[:TRANCO_TRAIN], "label": 0})
        df = pd.concat([df, extra]).drop_duplicates(subset=["host"], keep="last")
        print(f"Added {TRANCO_TRAIN} Tranco popular domains as legit samples")
    except Exception as exc:
        print(f"WARNING: Tranco download failed ({exc}); continuing without it.")

    df = df.sample(frac=1.0, random_state=SEED)
    print(f"Training set: {len(df)} unique hosts "
          f"({int(df['label'].sum())} phishing / {int((1 - df['label']).sum())} legit)")

    X, y = df["host"].astype(str), df["label"].astype(int)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=SEED)

    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5),
                                  max_features=120_000, sublinear_tf=True,
                                  lowercase=True, min_df=3)),
        ("clf", LogisticRegression(max_iter=2000, C=10.0,
                                   class_weight="balanced")),
    ])
    print("Training ...")
    pipe.fit(X_train, y_train)

    y_pred = pipe.predict(X_test)
    y_prob = pipe.predict_proba(X_test)[:, 1]
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()

    metrics = {
        "model": "char 3-5g TF-IDF + LogisticRegression (hostnames, host-deduped)",
        "task": "phishing URL detection",
        "trained_on": str(date.today()),
        "dataset": {"total": int(len(df)), "phishing": int(y.sum()),
                    "legit": int(len(df) - y.sum()), "sources": [source]},
        "test_split": 0.2,
        "accuracy": round(accuracy_score(y_test, y_pred), 4),
        "precision": round(precision_score(y_test, y_pred), 4),
        "recall": round(recall_score(y_test, y_pred), 4),
        "f1": round(f1_score(y_test, y_pred), 4),
        "roc_auc": round(roc_auc_score(y_test, y_prob), 4),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp),
                             "fn": int(fn), "tp": int(tp)},
    }

    ARTIFACTS.mkdir(exist_ok=True)
    joblib.dump(pipe, ARTIFACTS / "url_model.joblib", compress=3)
    (ARTIFACTS / "url_metrics.json").write_text(json.dumps(metrics, indent=2))
    if tranco:
        (ARTIFACTS / "popular_domains.json").write_text(
            json.dumps(sorted(tranco[:TRANCO_ALLOWLIST])))
        print(f"Saved popular_domains.json ({TRANCO_ALLOWLIST} domains)")
    print(json.dumps(metrics, indent=2))
    size_mb = (ARTIFACTS / "url_model.joblib").stat().st_size / 1e6
    print(f"\nSaved url_model.joblib ({size_mb:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
