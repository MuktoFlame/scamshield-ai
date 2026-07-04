"""Tests for the website checker: lexical features, SSRF guard, endpoint."""
import pytest
from fastapi.testclient import TestClient

from app.db import get_db
from app.main import app
from app.services import safe_fetch, url_features
from app.services.url_checker import registered_domain


@pytest.fixture()
def client():
    get_db.cache_clear()
    with TestClient(app) as c:
        yield c
    get_db.cache_clear()


# ---------- lexical features ----------

def finding_ids(url):
    return {f["id"] for f in url_features.analyze_url(url)}


def test_lookalike_domain():
    assert "lookalike_domain" in finding_ids("http://paypal-verify-account.tk/login")


def test_homoglyph_lookalike():
    assert "lookalike_domain" in finding_ids("https://netfIix-billing.com")


def test_ip_url():
    assert "ip_url" in finding_ids("http://203.0.113.7/login")


def test_at_sign_decoy():
    assert "at_in_url" in finding_ids("http://google.com@evil.example/paypal")


def test_deep_subdomains():
    assert "deep_subdomains" in finding_ids("http://secure.login.account.verify.example.com")


def test_clean_url_no_findings():
    assert finding_ids("https://example.org/about") == set()


def test_domain_of_strips_www_prefix_only():
    assert url_features.domain_of("https://www.google.com/x") == "google.com"
    # must not eat leading w's of the real domain
    assert url_features.domain_of("https://wellsfargo.com") == "wellsfargo.com"


def test_registered_domain():
    assert registered_domain("en.m.wikipedia.org") == "wikipedia.org"
    assert registered_domain("news.bbc.co.uk") == "bbc.co.uk"


# ---------- SSRF guard ----------

@pytest.mark.parametrize("url", [
    "http://127.0.0.1/admin",
    "http://localhost:8000/",
    "http://192.168.1.1/router",
    "http://10.0.0.5/internal",
    "http://169.254.169.254/latest/meta-data/",
    "ftp://example.com/file",
])
def test_ssrf_guard_rejects(url):
    with pytest.raises((safe_fetch.UnsafeUrl, safe_fetch.FetchFailed)):
        safe_fetch.fetch(url)


# ---------- endpoint (network mocked) ----------

def test_check_url_endpoint_phishing(client, monkeypatch):
    monkeypatch.setattr(
        safe_fetch, "fetch",
        lambda url: (_ for _ in ()).throw(safe_fetch.FetchFailed("unreachable")))
    r = client.post("/api/check/url",
                    json={"url": "http://paypal-account-verify.tk/signin"})
    assert r.status_code == 200
    body = r.json()
    assert body["risk_level"] == "high"
    assert body["known_site"] is False
    assert body["fetched"] is False
    assert any(f["id"] == "lookalike_domain" for f in body["flags"])
    assert body["summary"]


def test_check_url_endpoint_rejects_private(client):
    r = client.post("/api/check/url", json={"url": "http://127.0.0.1/x"})
    assert r.status_code == 400


def test_check_url_known_site_low(client, monkeypatch):
    from app.services import url_checker
    monkeypatch.setattr(url_checker, "_popular_domains",
                        lambda: frozenset({"wikipedia.org"}))
    monkeypatch.setattr(
        safe_fetch, "fetch",
        lambda url: safe_fetch.FetchedPage(url, 200, "<html></html>", 0))
    r = client.post("/api/check/url",
                    json={"url": "https://en.wikipedia.org/wiki/Bangladesh"})
    body = r.json()
    assert body["known_site"] is True
    assert body["risk_level"] == "low"


def test_check_url_saved_to_typed_history(client, monkeypatch):
    monkeypatch.setattr(
        safe_fetch, "fetch",
        lambda url: (_ for _ in ()).throw(safe_fetch.FetchFailed("unreachable")))
    reg = client.post("/api/auth/register", json={
        "name": "U", "email": "u@test.com",
        "password": "password123", "role": "senior"})
    token = reg.json()["token"]
    client.post("/api/check/url", json={"url": "http://scam-verify.tk/x"},
                headers={"Authorization": f"Bearer {token}"})
    hist = client.get("/api/history",
                      headers={"Authorization": f"Bearer {token}"}).json()
    assert hist["scans"][0]["type"] == "url"
