"""RAG safety-guidance retrieval.

A curated knowledge base of safety guidance (ml/kb/*.md) is chunked and
indexed with BM25 by ml/build_kb.py into ml/artifacts/kb_index.json. Every
check response retrieves the most relevant guidance snippets; the explainer
can cite them and the UI shows them as "Learn more".

BM25 keeps retrieval fully offline and deterministic — no embedding API, no
network, works with zero configuration.
"""
from __future__ import annotations

import json
import logging
import re
from functools import lru_cache
from pathlib import Path

log = logging.getLogger(__name__)

INDEX_PATH = (Path(__file__).resolve().parents[3]
              / "ml" / "artifacts" / "kb_index.json")

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


@lru_cache(maxsize=1)
def _load():
    """Returns (bm25, chunks) or None when the index isn't built."""
    if not INDEX_PATH.exists():
        log.warning("Guidance KB index missing at %s", INDEX_PATH)
        return None
    try:
        from rank_bm25 import BM25Okapi
    except ImportError:
        log.warning("rank_bm25 not installed — guidance retrieval disabled")
        return None
    data = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    chunks = data["chunks"]
    bm25 = BM25Okapi([_tokenize(c["text"]) for c in chunks])
    return bm25, chunks


def retrieve(query: str, k: int = 3) -> list[dict]:
    """Top-k guidance snippets for a query: [{title, snippet, doc_id}]."""
    loaded = _load()
    if loaded is None:
        return []
    bm25, chunks = loaded
    tokens = _tokenize(query)
    if not tokens:
        return []
    scores = bm25.get_scores(tokens)
    ranked = sorted(range(len(chunks)), key=lambda i: -scores[i])[:k]
    return [
        {
            "title": chunks[i]["title"],
            "snippet": chunks[i]["text"],
            "doc_id": chunks[i]["doc_id"],
        }
        for i in ranked if scores[i] > 0
    ]
