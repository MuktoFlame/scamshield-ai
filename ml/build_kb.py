"""Build the BM25 index for the safety-guidance knowledge base.

Reads ml/kb/*.md, splits each file into sections at '##' headings (one
section = one retrievable chunk), and writes ml/artifacts/kb_index.json.
The backend (services/guidance.py) builds the BM25 scorer from this file at
startup — retrieval is fully offline and deterministic.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ML_DIR = Path(__file__).parent
KB_DIR = ML_DIR / "kb"
OUT = ML_DIR / "artifacts" / "kb_index.json"


def main() -> int:
    chunks = []
    for path in sorted(KB_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        doc_title_match = re.match(r"#\s+(.+)", text)
        doc_title = doc_title_match.group(1).strip() if doc_title_match else path.stem

        sections = re.split(r"\n##\s+", text)
        for section in sections[1:]:  # sections[0] is the doc header/intro
            lines = section.strip().split("\n", 1)
            heading = lines[0].strip()
            body = lines[1].strip().replace("\n", " ") if len(lines) > 1 else ""
            if not body:
                continue
            chunks.append({
                "doc_id": path.stem,
                "title": f"{doc_title} — {heading}",
                "text": re.sub(r"\s+", " ", body),
            })

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({"chunks": chunks}, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print(f"Indexed {len(chunks)} guidance chunks from "
          f"{len(list(KB_DIR.glob('*.md')))} documents -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
