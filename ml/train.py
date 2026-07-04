"""Train the ScamShield scam/spam text classifier.

Model: TF-IDF (word 1-2 grams + char 3-5 grams) -> Logistic Regression.
Chosen over heavier transformer models because it trains in seconds, is fully
reproducible, ships as a ~1 MB artifact that loads instantly on a free-tier
server, and reaches ~0.98 F1 on this corpus — the LLM layer handles nuance.

Outputs (committed to the repo so deployment never needs to retrain):
  ml/artifacts/model.joblib   - fitted sklearn Pipeline
  ml/artifacts/metrics.json   - evaluation metrics + dataset/model metadata
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score, roc_auc_score,
    confusion_matrix,
)
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import FeatureUnion, Pipeline

ML_DIR = Path(__file__).parent
DATA = ML_DIR / "data" / "combined.csv"
ARTIFACTS = ML_DIR / "artifacts"
SEED = 42


def build_pipeline() -> Pipeline:
    features = FeatureUnion([
        ("word", TfidfVectorizer(
            ngram_range=(1, 2), sublinear_tf=True, min_df=2,
            strip_accents="unicode", lowercase=True,
        )),
        ("char", TfidfVectorizer(
            analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True, min_df=2,
        )),
    ])
    clf = LogisticRegression(max_iter=2000, C=10.0, class_weight="balanced")
    return Pipeline([("features", features), ("clf", clf)])


def main() -> int:
    if not DATA.exists():
        print("No training data. Run download_data.py first.")
        return 1

    df = pd.read_csv(DATA)
    X, y = df["text"].astype(str), df["label"].astype(int)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=SEED
    )

    pipe = build_pipeline()
    print(f"Training on {len(X_train)} samples ...")
    pipe.fit(X_train, y_train)

    y_pred = pipe.predict(X_test)
    y_prob = pipe.predict_proba(X_test)[:, 1]
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()

    print("Running 5-fold cross-validation ...")
    cv_f1 = cross_val_score(build_pipeline(), X, y, cv=5, scoring="f1")

    metrics = {
        "model": "TF-IDF (word 1-2g + char 3-5g) + LogisticRegression",
        "trained_on": str(date.today()),
        "dataset": {
            "total": int(len(df)),
            "scam": int(y.sum()),
            "legit": int(len(df) - y.sum()),
            "sources": ["UCI SMS Spam Collection", "curated scam/phishing samples"],
        },
        "test_split": 0.2,
        "accuracy": round(accuracy_score(y_test, y_pred), 4),
        "precision": round(precision_score(y_test, y_pred), 4),
        "recall": round(recall_score(y_test, y_pred), 4),
        "f1": round(f1_score(y_test, y_pred), 4),
        "roc_auc": round(roc_auc_score(y_test, y_prob), 4),
        "cv_f1_mean": round(cv_f1.mean(), 4),
        "cv_f1_std": round(cv_f1.std(), 4),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    }

    ARTIFACTS.mkdir(exist_ok=True)
    joblib.dump(pipe, ARTIFACTS / "model.joblib", compress=3)
    (ARTIFACTS / "metrics.json").write_text(json.dumps(metrics, indent=2))

    print(json.dumps(metrics, indent=2))
    print(f"\nSaved model -> {ARTIFACTS / 'model.joblib'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
