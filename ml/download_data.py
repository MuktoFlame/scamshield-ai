"""Download and normalize the training datasets for the ScamShield classifier.

Sources:
  1. UCI SMS Spam Collection (public, no auth) - 5,574 labeled SMS messages.
  2. Curated scam/phishing samples bundled with this repo (ml/curated_samples.csv)
     covering scam families the SMS corpus under-represents: gift-card demands,
     tech-support fraud, delivery smishing, romance/investment scams.

Output: ml/data/combined.csv with columns [text, label] where label is 1 (scam/spam)
or 0 (legitimate). Raw downloads land in ml/data/ and are gitignored.
"""
from __future__ import annotations

import io
import sys
import zipfile
from pathlib import Path

import pandas as pd
import requests

ML_DIR = Path(__file__).parent
DATA_DIR = ML_DIR / "data"
UCI_URL = "https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip"


def download_uci_sms() -> pd.DataFrame:
    print(f"Downloading UCI SMS Spam Collection from {UCI_URL} ...")
    resp = requests.get(UCI_URL, timeout=60)
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        with zf.open("SMSSpamCollection") as f:
            df = pd.read_csv(
                f, sep="\t", header=None, names=["label", "text"],
                quoting=3, encoding="utf-8",
            )
    df["label"] = (df["label"] == "spam").astype(int)
    print(f"  -> {len(df)} messages ({df['label'].sum()} spam)")
    return df[["text", "label"]]


def load_curated() -> pd.DataFrame:
    path = ML_DIR / "curated_samples.csv"
    if not path.exists():
        print("  (no curated_samples.csv found, skipping)")
        return pd.DataFrame(columns=["text", "label"])
    df = pd.read_csv(path)
    print(f"Curated samples: {len(df)} messages ({df['label'].sum()} scam)")
    return df[["text", "label"]]


def main() -> int:
    DATA_DIR.mkdir(exist_ok=True)
    frames = []
    try:
        frames.append(download_uci_sms())
    except Exception as exc:  # network failures shouldn't kill the pipeline
        print(f"WARNING: UCI download failed ({exc}); continuing without it.")
    frames.append(load_curated())

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.dropna(subset=["text"])
    combined["text"] = combined["text"].astype(str).str.strip()
    combined = combined[combined["text"].str.len() > 0]
    before = len(combined)
    combined = combined.drop_duplicates(subset=["text"])
    print(f"Deduplicated {before - len(combined)} rows")

    if combined.empty:
        print("ERROR: no training data could be assembled.")
        return 1

    out = DATA_DIR / "combined.csv"
    combined.to_csv(out, index=False)
    print(f"Wrote {len(combined)} rows -> {out}")
    print(combined["label"].value_counts().rename({0: "legit", 1: "scam"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
