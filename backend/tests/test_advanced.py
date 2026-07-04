"""Tests for the advanced features: Bangla explanations + screenshot scanning."""
import pytest
from fastapi.testclient import TestClient

from app.db import get_db
from app.main import app


@pytest.fixture()
def client():
    get_db.cache_clear()
    with TestClient(app) as c:
        yield c
    get_db.cache_clear()


def test_bangla_explanation_fallback(client):
    r = client.post("/api/scan", json={
        "text": "URGENT: verify your PIN or account will be suspended! Pay "
                "with gift cards now.",
        "language": "bn",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["risk_level"] == "high"
    # Fallback templates are used without an API key; Bangla text present
    assert any("ঀ" <= ch <= "৿" for ch in body["summary"])


def test_invalid_language_rejected(client):
    r = client.post("/api/scan", json={"text": "hello", "language": "xx"})
    assert r.status_code == 422


def test_image_scan_invalid_base64(client):
    r = client.post("/api/scan/image", json={
        "image_b64": "!!!not-base64!!!",
        "mime_type": "image/png",
    })
    assert r.status_code == 400


def test_image_scan_unavailable_without_key(client, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "gemini_api_key", "")
    r = client.post("/api/scan/image", json={
        "image_b64": "aGVsbG8=",  # valid base64
        "mime_type": "image/png",
    })
    assert r.status_code == 503
    assert "paste" in r.json()["detail"].lower()


def test_image_scan_bad_mime_rejected(client):
    r = client.post("/api/scan/image", json={
        "image_b64": "aGVsbG8=",
        "mime_type": "application/pdf",
    })
    assert r.status_code == 422
