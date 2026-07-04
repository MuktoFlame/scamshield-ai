"""Article main-text extraction from a URL (for the News & Fact Check module).

Uses the same SSRF-guarded fetcher as the URL checker, then trafilatura for
boilerplate removal, with a plain BeautifulSoup fallback.
"""
from __future__ import annotations

import logging

from bs4 import BeautifulSoup

from . import safe_fetch

log = logging.getLogger(__name__)

MAX_CHARS = 20_000


def extract_from_url(url: str) -> tuple[str, str]:
    """Returns (title, main_text). Raises safe_fetch.UnsafeUrl / FetchFailed."""
    page = safe_fetch.fetch(url)
    title, text = "", ""
    try:
        import trafilatura
        text = trafilatura.extract(page.html, include_comments=False,
                                   include_tables=False) or ""
        meta = trafilatura.extract_metadata(page.html)
        title = (meta.title if meta and meta.title else "") or ""
    except Exception as exc:
        log.warning("trafilatura failed (%s); using soup fallback", exc)

    if not text:
        soup = BeautifulSoup(page.html, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
            tag.decompose()
        title = soup.title.get_text(strip=True) if soup.title else ""
        paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
        text = "\n".join(p for p in paragraphs if len(p) > 40)

    if not text.strip():
        raise safe_fetch.FetchFailed(
            "No readable article text was found at that address.")
    return title.strip(), text.strip()[:MAX_CHARS]
