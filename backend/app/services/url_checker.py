"""Phishing website checker.

Verdict is grounded in three signal groups, then explained by the LLM layer:
  1. Lexical analysis of the URL itself (url_features.analyze_url)
  2. The trained phishing-URL classifier (PhiUSIIL, F1 ~0.99)
  3. Live page inspection over an SSRF-guarded fetch (safe_fetch)
"""
from __future__ import annotations

import json
import logging
import re
from functools import lru_cache
from pathlib import Path

from bs4 import BeautifulSoup

from . import classifier, explainer, safe_fetch, url_features
from .pipeline import RiskReport, fuse, level_for
from .rules import Flag

log = logging.getLogger(__name__)

POPULAR_PATH = (Path(__file__).resolve().parents[3]
                / "ml" / "artifacts" / "popular_domains.json")

# ccTLD second-level labels for a simple eTLD+1 approximation
_CC_SLD = {"co", "com", "org", "net", "ac", "gov", "edu"}


@lru_cache(maxsize=1)
def _popular_domains() -> frozenset[str]:
    if POPULAR_PATH.exists():
        return frozenset(json.loads(POPULAR_PATH.read_text()))
    return frozenset()


def registered_domain(host: str) -> str:
    """Approximate eTLD+1: google.com from en.m.google.com,
    bbc.co.uk from news.bbc.co.uk."""
    parts = host.split(".")
    if len(parts) >= 3 and parts[-2] in _CC_SLD and len(parts[-1]) == 2:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


def is_popular(host: str) -> bool:
    return registered_domain(host) in _popular_domains()


def _rule_score(flags: list[Flag]) -> float:
    score = 1.0
    for f in flags:
        score *= (1.0 - f.severity)
    return round(1.0 - score, 4)


def _inspect_page(html: str, final_url: str) -> list[Flag]:
    """Content signals from the fetched page."""
    flags: list[Flag] = []
    soup = BeautifulSoup(html, "html.parser")
    domain = url_features.domain_of(final_url)

    if soup.find("input", {"type": "password"}) is not None:
        flags.append(Flag(
            "login_form", "Page asks for a password",
            "The page contains a login form. Combined with a suspicious "
            "address, this is the classic setup for stealing passwords.",
            0.5, ["password field found on the page"]))

    for form in soup.find_all("form"):
        action = form.get("action") or ""
        if action.startswith("http"):
            action_domain = url_features.domain_of(action)
            if action_domain and action_domain != domain:
                flags.append(Flag(
                    "foreign_form", "Form sends your data to a different site",
                    "Anything typed into this page is sent to a completely "
                    "different website — legitimate sites almost never do this.",
                    0.7, [action_domain]))
                break

    title = (soup.title.get_text(" ", strip=True) if soup.title else "")
    text_sample = f"{title} {soup.get_text(' ', strip=True)[:2000]}".lower()
    for brand in url_features.KNOWN_BRANDS:
        if brand in text_sample and brand not in domain.replace("-", "").replace(".", ""):
            flags.append(Flag(
                "brand_content_mismatch",
                f"Page talks about {brand.title()} but isn't their site",
                "The page presents itself as a well-known company, but the web "
                "address does not belong to that company.",
                0.6, [f"mentions '{brand}', address is {domain}"]))
            break

    meta = soup.find("meta", attrs={"http-equiv": re.compile("^refresh$", re.I)})
    if meta is not None:
        flags.append(Flag(
            "meta_refresh", "Page silently forwards you elsewhere",
            "The page automatically redirects visitors, a technique often "
            "used to bounce people to a scam destination.",
            0.4, [str(meta.get("content", ""))[:60]]))

    return flags


def check(url: str, language: str = "en",
          guidance: list[dict] | None = None) -> dict:
    """Full website check. Returns a dict shaped like a message-scan result
    plus url-specific extras (normalized_url, domain, fetched, final_url).
    """
    url = url.strip()
    if "://" not in url:
        url = "https://" + url
    domain = url_features.domain_of(url)

    flags = [Flag(**f) for f in url_features.analyze_url(url)]

    # Allowlist first: exact registered-domain match against the Tranco top
    # sites. A char-n-gram model can't distinguish "google.com" from
    # "google-verify.tk" by substrings alone, so known-popular domains skip
    # the classifier — the same shortcut real safe-browsing systems use.
    known_site = bool(domain) and is_popular(domain)
    if known_site:
        clf_prob = 0.02
    else:
        # The URL model is trained on hostnames (see ml/train_url.py docstring)
        clf_prob = classifier.url_probability(domain) if domain else None

    fetched, final_url, fetch_note = False, url, None
    try:
        page = safe_fetch.fetch(url)
        fetched = True
        final_url = page.final_url
        final_domain = url_features.domain_of(final_url)
        # Page signals only apply to unknown domains: a login form or meta
        # refresh on github.com is normal; on secure-github-login.tk it isn't.
        if not known_site:
            flags.extend(_inspect_page(page.html, final_url))
            if final_domain and final_domain != domain:
                flags.append(Flag(
                    "redirect_elsewhere", "Address redirects to a different site",
                    "The link does not lead where it appears to — visitors are "
                    "forwarded to a different website.",
                    0.5, [f"{domain} → {final_domain}"]))
    except safe_fetch.UnsafeUrl:
        raise  # bubbled to the router: request is rejected outright
    except safe_fetch.FetchFailed as exc:
        fetch_note = str(exc)

    rule_score = _rule_score(flags)
    score, confidence = fuse(clf_prob, rule_score)

    report = RiskReport(
        risk_level=level_for(score),
        risk_score=score,
        confidence=confidence,
        classifier_probability=clf_prob,
        rule_score=rule_score,
        flags=[f.to_dict() for f in flags],
    )
    report = explainer.explain(
        f"URL: {url}" + (f" (page could not be loaded: {fetch_note})" if fetch_note else ""),
        report, language, subject="website link", guidance=guidance)

    result = report.to_dict()
    result.update({
        "normalized_url": url,
        "domain": domain,
        "known_site": known_site,
        "fetched": fetched,
        "final_url": final_url,
        "fetch_note": fetch_note,
    })
    return result
