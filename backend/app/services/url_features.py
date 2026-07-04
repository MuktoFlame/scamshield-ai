"""Shared URL lexical analysis.

Used in two places: rules.py scans free text for suspicious links, and
url_checker.py analyzes a single submitted URL in depth. All heuristics
return Flag objects (defined in rules.py) with evidence spans.
"""
from __future__ import annotations

import re
from urllib.parse import urlparse

# ¡-￿ keeps internationalized (incl. punycode-decoded) domains matchable
URL_RE = re.compile(
    r"(?:https?://)?(?:www\.)?([a-z0-9¡-￿-]+(?:\.[a-z0-9¡-￿-]+)+)(/[^\s]*)?",
    re.I,
)

SHORTENERS = {
    "bit.ly", "tinyurl.com", "goo.gl", "t.co", "is.gd", "cutt.ly", "rb.gy",
    "shorturl.at", "ow.ly", "buff.ly", "rebrand.ly", "t.ly",
}
SUSPICIOUS_TLDS = {"tk", "ml", "ga", "cf", "gq", "top", "xyz", "info", "club", "buzz", "icu"}
KNOWN_BRANDS = [
    "paypal", "amazon", "apple", "microsoft", "netflix", "google", "facebook",
    "whatsapp", "chase", "wellsfargo", "bankofamerica", "citibank", "hsbc",
    "usps", "fedex", "ups", "dhl", "irs", "bkash", "nagad",
]

IP_RE = re.compile(r"(\d{1,3}\.){3}\d{1,3}")


def is_ip(domain: str) -> bool:
    return bool(IP_RE.fullmatch(domain))


def brand_lookalike(domain: str) -> str | None:
    """Return the imitated brand name if the domain mimics one, else None."""
    flat = domain.replace("-", "").replace(".", "")
    for brand in KNOWN_BRANDS:
        official = brand in (domain.split(".")[0],) or domain.endswith(f"{brand}.com")
        if brand in flat and not official:
            return brand
        # homoglyph normalization: capital I for l, 0 for o, 1 for l
        normalized = flat.replace("1", "l").replace("0", "o").replace("i", "l")
        brand_norm = brand.replace("1", "l").replace("0", "o").replace("i", "l")
        if brand_norm in normalized and brand not in flat:
            return brand
    return None


def domain_of(url: str) -> str:
    """Normalized hostname of a URL, without a leading www.
    (empty string if unparseable)."""
    if "://" not in url:
        url = "http://" + url
    try:
        host = (urlparse(url).hostname or "").lower()
    except ValueError:
        return ""
    return host.removeprefix("www.")


def analyze_url(url: str) -> list[dict]:
    """Deep lexical analysis of one URL. Returns raw flag dicts
    (id/title/description/severity/evidence) — rules.py wraps them as Flags.
    """
    findings: list[dict] = []
    if "://" not in url:
        url = "http://" + url
    try:
        parsed = urlparse(url)
    except ValueError:
        return findings
    host = (parsed.hostname or "").lower()
    if not host:
        return findings

    def add(id_, title, description, severity, evidence):
        findings.append({"id": id_, "title": title, "description": description,
                         "severity": severity, "evidence": [evidence]})

    brand = brand_lookalike(host)
    if brand:
        add("lookalike_domain", "Address imitates a well-known company",
            f"The address looks related to {brand.title()}, but it is not that "
            "company's real website. Scammers register lookalike addresses to "
            "steal logins and card numbers.", 0.9, host)
    if is_ip(host):
        add("ip_url", "Address is a raw numeric address",
            "Legitimate companies almost never use links made of raw numbers. "
            "This is a common way to hide where a link really goes.", 0.8, host)
    if host.removeprefix("www.") in SHORTENERS:
        add("shortened_url", "Shortened link hides the destination",
            "This link has been shortened so you cannot see where it leads "
            "before clicking.", 0.5, host)
    tld = host.rsplit(".", 1)[-1] if "." in host else ""
    if tld in SUSPICIOUS_TLDS:
        add("suspicious_tld", "Domain ending common in scams",
            f"The address ends in .{tld}, a domain type that is cheap to "
            "register and heavily used by scammers.", 0.5, host)
    if host.startswith("xn--") or ".xn--" in host:
        add("punycode", "Address uses disguised international characters",
            "The address uses special characters that can imitate normal "
            "letters — a trick to make a fake address look real.", 0.8, host)
    if host.count(".") >= 4:
        add("deep_subdomains", "Unusually long chain of subdomains",
            "Many nested subdomains are often used to bury a trusted-looking "
            "name inside a scam address.", 0.5, host)
    if host.count("-") >= 3:
        add("hyphen_stuffing", "Address stuffed with hyphens",
            "Long hyphenated addresses (like secure-login-account-verify) are "
            "typical of phishing sites.", 0.4, host)
    if "@" in url.split("://", 1)[-1].split("/")[0]:
        add("at_in_url", "Hidden real destination after an @ sign",
            "Everything before the @ in this address is a decoy — browsers "
            "actually navigate to what comes after it.", 0.9, url[:80])
    if parsed.port and parsed.port not in (80, 443):
        add("odd_port", "Non-standard connection port",
            "The address points to an unusual port, which legitimate websites "
            "rarely use.", 0.5, f"{host}:{parsed.port}")
    if len(url) > 100:
        add("very_long_url", "Extremely long web address",
            "Very long addresses are often used to hide the real destination "
            "or to sneak past filters.", 0.3, url[:60] + "…")
    return findings


def find_url_findings_in_text(text: str) -> list[dict]:
    """Scan free text for URLs and aggregate findings (used by rules.py)."""
    merged: dict[str, dict] = {}
    for m in URL_RE.finditer(text):
        candidate = m.group(0)
        for f in analyze_url(candidate):
            if f["id"] in merged:
                for ev in f["evidence"]:
                    if ev not in merged[f["id"]]["evidence"]:
                        merged[f["id"]]["evidence"].append(ev)
            else:
                merged[f["id"]] = f
    # Cap evidence lists
    for f in merged.values():
        f["evidence"] = f["evidence"][:4]
    return list(merged.values())
