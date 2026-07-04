"""SSRF-guarded HTTP fetching for user-supplied URLs.

The URL and news checkers fetch pages the *user* asks about, which means the
server is making requests to attacker-controllable destinations. Guards:

  - scheme must be http/https
  - every hostname is DNS-resolved and ALL resolved addresses must be global
    (rejects loopback, RFC1918/private, link-local, reserved, multicast) —
    re-checked on every redirect hop
  - max 3 redirects, 5 s timeout per request, 1 MB body cap, HTML/text only

Note: a determined attacker could still attempt DNS rebinding between our
check and the connect; for this application (read-only GET, response never
executed server-side, body size capped) the residual risk is acceptable and
documented.
"""
from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import requests

MAX_REDIRECTS = 3
TIMEOUT = 5
MAX_BYTES = 1_000_000
USER_AGENT = "Mozilla/5.0 (compatible; ScamShieldBot/1.0; safety checker)"


class UnsafeUrl(Exception):
    """URL rejected by the safety policy (never fetched)."""


class FetchFailed(Exception):
    """URL passed the safety policy but could not be fetched."""


@dataclass
class FetchedPage:
    final_url: str
    status: int
    html: str
    redirects: int


def _assert_public_host(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise UnsafeUrl("Only http and https addresses can be checked.")
    host = parsed.hostname
    if not host:
        raise UnsafeUrl("That does not look like a valid web address.")
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        raise FetchFailed("The website's address could not be found.")
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if not ip.is_global:
            raise UnsafeUrl("This address points to a private or internal "
                            "network and cannot be checked.")


def fetch(url: str) -> FetchedPage:
    """GET a user-supplied URL under the safety policy."""
    current = url
    for hop in range(MAX_REDIRECTS + 1):
        _assert_public_host(current)
        try:
            resp = requests.get(
                current, timeout=TIMEOUT, stream=True, allow_redirects=False,
                headers={"User-Agent": USER_AGENT,
                         "Accept": "text/html,application/xhtml+xml"},
            )
        except requests.RequestException as exc:
            raise FetchFailed(f"The page could not be loaded ({type(exc).__name__}).")

        if resp.is_redirect or resp.is_permanent_redirect:
            location = resp.headers.get("Location")
            resp.close()
            if not location:
                raise FetchFailed("The page redirected without a destination.")
            current = urljoin(current, location)
            continue

        content_type = resp.headers.get("Content-Type", "")
        if "text" not in content_type and "html" not in content_type:
            resp.close()
            raise FetchFailed("The address does not point to a normal web page.")

        chunks, total = [], 0
        for chunk in resp.iter_content(chunk_size=65536):
            chunks.append(chunk)
            total += len(chunk)
            if total >= MAX_BYTES:
                break
        resp.close()
        html = b"".join(chunks)[:MAX_BYTES].decode(
            resp.encoding or "utf-8", errors="replace")
        return FetchedPage(final_url=current, status=resp.status_code,
                           html=html, redirects=hop)

    raise FetchFailed("The page redirected too many times.")
