"""Train the fake-news style classifier.

IMPORTANT caveat (also stated in the docs and the UI): a text classifier can
only judge *how an article is written* — sensationalism, clickbait phrasing,
source-style artifacts — not whether its claims are true. That is why this
model is one signal inside the News & Fact Check module, alongside the
RAG-based claim verification, and is labeled "style analysis" in the UI.

Dataset: WELFake (72k articles merging four standard fake-news corpora;
public download from Zenodo). Fallback: LIAR (UCSB) short political claims.

Model: word 1-2g TF-IDF + LogisticRegression (same family as the other two
models: fast, tiny artifact, reproducible).

Outputs: ml/artifacts/news_model.joblib + ml/artifacts/news_metrics.json
"""
from __future__ import annotations

import io
import json
import sys
import zipfile
from datetime import date
from pathlib import Path

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
WELFAKE_URL = "https://zenodo.org/records/4561253/files/WELFake_Dataset.csv"
LIAR_URL = "https://www.cs.ucsb.edu/~william/data/liar_dataset.zip"
SEED = 42
PER_CLASS = 15_000


def load_welfake() -> tuple[pd.DataFrame, str]:
    cached = DATA_DIR / "welfake.csv"
    if not cached.exists():
        print(f"Downloading WELFake from {WELFAKE_URL} ...")
        resp = requests.get(WELFAKE_URL, timeout=300)
        resp.raise_for_status()
        DATA_DIR.mkdir(exist_ok=True)
        cached.write_bytes(resp.content)
    df = pd.read_csv(cached)
    # WELFake: label 1 = fake, 0 = real — verified empirically: rows containing
    # "(Reuters)" attribution average label 0.001, shouty-caps titles 0.995.
    df["text"] = (df["title"].fillna("") + " " + df["text"].fillna("")).str.strip()
    df["label"] = df["label"].astype(int)
    return df[["text", "label"]], "WELFake (Zenodo record 4561253)"


def load_liar() -> tuple[pd.DataFrame, str]:
    print(f"Downloading LIAR from {LIAR_URL} ...")
    resp = requests.get(LIAR_URL, timeout=120)
    resp.raise_for_status()
    frames = []
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        for name in ("train.tsv", "valid.tsv", "test.tsv"):
            with zf.open(name) as f:
                part = pd.read_csv(f, sep="\t", header=None, usecols=[1, 2],
                                   names=["label", "text"])
                frames.append(part)
    df = pd.concat(frames)
    fake = {"false", "pants-fire", "barely-true"}
    df["label"] = df["label"].isin(fake).astype(int)
    return df[["text", "label"]], "LIAR (UCSB)"


def main() -> int:
    try:
        df, source = load_welfake()
    except Exception as exc:
        print(f"WARNING: WELFake failed ({exc}); trying LIAR ...")
        df, source = load_liar()

    df = df.dropna(subset=["text"])
    df = df[df["text"].str.len() > 30].drop_duplicates(subset=["text"])
    parts = [g.sample(min(len(g), PER_CLASS), random_state=SEED)
             for _, g in df.groupby("label")]
    df = pd.concat(parts).sample(frac=1.0, random_state=SEED)
    print(f"Training set: {len(df)} articles "
          f"({int(df['label'].sum())} fake / {int((1 - df['label']).sum())} real)")

    X, y = df["text"].astype(str), df["label"].astype(int)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=SEED)

    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=150_000,
                                  sublinear_tf=True, min_df=3,
                                  strip_accents="unicode")),
        ("clf", LogisticRegression(max_iter=2000, C=5.0,
                                   class_weight="balanced")),
    ])
    print("Training ...")
    pipe.fit(X_train, y_train)

    y_pred = pipe.predict(X_test)
    y_prob = pipe.predict_proba(X_test)[:, 1]
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()

    metrics = {
        "model": "word 1-2g TF-IDF + LogisticRegression",
        "task": "fake-news style detection (writing-style signal, not truth)",
        "trained_on": str(date.today()),
        "dataset": {"total": int(len(df)), "fake": int(y.sum()),
                    "real": int(len(df) - y.sum()), "sources": [source]},
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
    joblib.dump(pipe, ARTIFACTS / "news_model.joblib", compress=3)
    (ARTIFACTS / "news_metrics.json").write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics, indent=2))
    size_mb = (ARTIFACTS / "news_model.joblib").stat().st_size / 1e6
    print(f"\nSaved news_model.joblib ({size_mb:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
