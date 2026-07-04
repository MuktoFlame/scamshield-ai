"""Loads the trained models and exposes probability scores.

Three artifacts, all TF-IDF + LogisticRegression sklearn Pipelines trained by
the scripts in ml/ and committed to the repo:
  model.joblib      - scam/spam message classifier
  url_model.joblib  - phishing URL classifier
  news_model.joblib - fake-news style classifier
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path

import joblib

log = logging.getLogger(__name__)

ARTIFACTS = Path(__file__).resolve().parents[3] / "ml" / "artifacts"


@lru_cache(maxsize=None)
def _load(filename: str):
    path = ARTIFACTS / filename
    if not path.exists():
        log.warning("Model artifact missing: %s", path)
        return None
    return joblib.load(path)


def _probability(filename: str, text: str) -> float | None:
    model = _load(filename)
    if model is None:
        return None
    return round(float(model.predict_proba([text])[0, 1]), 4)


def scam_probability(text: str) -> float | None:
    """Probability (0..1) that a message is a scam."""
    return _probability("model.joblib", text)


def url_probability(url: str) -> float | None:
    """Probability (0..1) that a URL is a phishing URL."""
    return _probability("url_model.joblib", url)


def news_probability(text: str) -> float | None:
    """Probability (0..1) that an article reads like fake news (style signal)."""
    return _probability("news_model.joblib", text)


def _metrics(metrics_file: str, model_file: str) -> dict:
    path = ARTIFACTS / metrics_file
    if path.exists():
        info = json.loads(path.read_text())
        info["available"] = _load(model_file) is not None
        return info
    return {"available": False}


def model_info() -> dict:
    """Training metrics for all models — served by /api/model/info.

    Keeps the original top-level message-model fields for backward
    compatibility, and adds per-model entries under "models".
    """
    message = _metrics("metrics.json", "model.joblib")
    return {
        **message,
        "models": {
            "message": message,
            "url": _metrics("url_metrics.json", "url_model.joblib"),
            "news": _metrics("news_metrics.json", "news_model.joblib"),
        },
    }
