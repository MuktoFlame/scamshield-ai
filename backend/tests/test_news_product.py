"""Tests for the news & fact-check and product checkers (network mocked)."""
import pytest
from fastapi.testclient import TestClient

from app.db import get_db
from app.main import app
from app.services import factcheck, news_checker, product_checker


@pytest.fixture()
def client(monkeypatch):
    # Fact-check retrieval is network-bound; tests inject evidence directly.
    monkeypatch.setattr(factcheck, "retrieve_evidence", lambda claim: [])
    get_db.cache_clear()
    with TestClient(app) as c:
        yield c
    get_db.cache_clear()


# ---------- fact-check unit behavior ----------

def test_extract_claims_fallback_without_llm():
    claims = factcheck.extract_claims(
        "The moon is made of cheese. It orbits the earth.")
    assert claims
    assert "moon" in claims[0].lower()


def test_judge_without_evidence_is_unverifiable():
    verdict = factcheck.judge("Anything at all", [])
    assert verdict["verdict"] == "unverifiable"


def test_chunking_respects_size():
    text = "\n".join(f"Paragraph {i} " + "word " * 60 for i in range(10))
    chunks = factcheck._chunk(text, "T")
    assert all(len(c["text"]) <= 700 for c in chunks)
    assert len(chunks) > 1


# ---------- news checker fusion ----------

def test_refuted_claim_floors_high(monkeypatch):
    monkeypatch.setattr(factcheck, "check_claims", lambda text: [
        {"claim": "X", "verdict": "refuted", "rationale": "r", "sources": []},
    ])
    result = news_checker.check("Some very sober text about facts.")
    assert result["risk_level"] == "high"
    assert any(f["id"] == "refuted_claims" for f in result["flags"])


def test_supported_claims_cap_risk(monkeypatch):
    monkeypatch.setattr(factcheck, "check_claims", lambda text: [
        {"claim": "X", "verdict": "supported", "rationale": "r", "sources": []},
        {"claim": "Y", "verdict": "supported", "rationale": "r", "sources": []},
    ])
    result = news_checker.check(
        "SHOCKING!!! You won't BELIEVE this INSANE trick!!!")
    assert result["risk_level"] != "high"


# ---------- endpoints ----------

def test_news_endpoint_requires_input(client):
    r = client.post("/api/check/news", json={})
    assert r.status_code == 422


def test_news_endpoint_text(client):
    r = client.post("/api/check/news", json={
        "text": "BREAKING!!! Miracle cure DESTROYS all disease overnight, "
                "doctors HATE it! Share before it gets deleted!!!"})
    assert r.status_code == 200
    body = r.json()
    assert body["style_score"] > 0.5
    assert body["claims"]
    assert body["summary"]


def test_product_endpoint_scam_listing(client):
    r = client.post("/api/check/product", json={
        "title": "New iPhone 15 Pro Max sealed box",
        "price": "$99",
        "description": "today only! contact me on WhatsApp, payment by "
                       "western union or gift card only",
    })
    body = r.json()
    assert r.status_code == 200
    assert body["risk_level"] == "high"
    ids = {f["id"] for f in body["flags"]}
    assert {"too_cheap", "untraceable_payment", "offsite_contact"} <= ids


def test_product_endpoint_normal_listing(client):
    r = client.post("/api/check/product", json={
        "title": "Used office chair, good condition",
        "price": "$45",
        "description": "Pickup preferred. Minor scratches on the base.",
    })
    assert r.json()["risk_level"] == "low"


def test_product_price_parsing():
    assert product_checker._parse_price("$1,299.99") == 1299.99
    assert product_checker._parse_price("Tk 950") == 950
    assert product_checker._parse_price("free!!") is None


def test_typed_history_for_new_checkers(client):
    reg = client.post("/api/auth/register", json={
        "name": "N", "email": "n@test.com",
        "password": "password123", "role": "senior"})
    token = reg.json()["token"]
    hdr = {"Authorization": f"Bearer {token}"}
    client.post("/api/check/news", json={"text": "A plain statement of fact "
                "that is long enough to analyze."}, headers=hdr)
    client.post("/api/check/product",
                json={"title": "A very ordinary lamp"}, headers=hdr)
    hist = client.get("/api/history", headers=hdr).json()["scans"]
    assert {s["type"] for s in hist} == {"news", "product"}
