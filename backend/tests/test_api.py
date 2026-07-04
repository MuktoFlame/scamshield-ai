import pytest
from fastapi.testclient import TestClient

from app.db import get_db
from app.main import app


@pytest.fixture()
def client():
    # Fresh in-memory DB per test (mongomock backs get_db when MONGO_URI unset)
    get_db.cache_clear()
    with TestClient(app) as c:
        yield c
    get_db.cache_clear()


def register(client, email="senior@test.com", role="senior", name="Test User"):
    r = client.post("/api/auth/register", json={
        "name": name, "email": email, "password": "password123", "role": role,
    })
    assert r.status_code == 201, r.text
    data = r.json()
    return data["token"], data["user"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_health(client):
    assert client.get("/api/health").json()["status"] == "ok"


def test_guest_scan_works_and_is_not_saved(client):
    r = client.post("/api/scan", json={"text": "hello there"})
    assert r.status_code == 200
    assert r.json()["saved"] is False


def test_scam_scan_returns_high_risk_with_flags(client):
    r = client.post("/api/scan", json={
        "text": "URGENT: verify your PIN at chase-verify.tk or account will "
                "be suspended! Pay fee with gift cards.",
        "channel": "sms",
    })
    body = r.json()
    assert body["risk_level"] == "high"
    assert body["flags"]
    assert body["summary"]
    assert body["recommended_action"]
    assert body["explanation_source"] in ("llm", "rules")


def test_duplicate_email_rejected(client):
    register(client)
    r = client.post("/api/auth/register", json={
        "name": "X", "email": "senior@test.com",
        "password": "password123", "role": "senior",
    })
    assert r.status_code == 409


def test_login_wrong_password(client):
    register(client)
    r = client.post("/api/auth/login", json={
        "email": "senior@test.com", "password": "wrong-password",
    })
    assert r.status_code == 401


def test_history_requires_auth(client):
    assert client.get("/api/history").status_code == 401


def test_logged_in_scan_is_saved_to_history(client):
    token, _ = register(client)
    client.post("/api/scan", json={"text": "you won a lottery, send fee"},
                headers=auth(token))
    r = client.get("/api/history", headers=auth(token))
    assert len(r.json()["scans"]) == 1


def test_caregiver_link_flow(client):
    s_token, s_user = register(client, "senior@test.com", "senior", "Senior")
    c_token, _ = register(client, "care@test.com", "caregiver", "Carer")

    client.post("/api/scan", json={"text": "urgent gift card scam text"},
                headers=auth(s_token))

    code = client.post("/api/caregiver/code",
                       headers=auth(s_token)).json()["code"]
    r = client.post("/api/caregiver/link", json={"code": code},
                    headers=auth(c_token))
    assert r.status_code == 200

    r = client.get(f"/api/history/{s_user['id']}", headers=auth(c_token))
    assert r.status_code == 200
    assert len(r.json()["scans"]) == 1


def test_caregiver_cannot_view_unlinked_senior(client):
    _, s_user = register(client, "senior@test.com", "senior")
    c_token, _ = register(client, "care@test.com", "caregiver")
    r = client.get(f"/api/history/{s_user['id']}", headers=auth(c_token))
    assert r.status_code == 403


def test_caregiver_cannot_generate_code(client):
    c_token, _ = register(client, "care@test.com", "caregiver")
    assert client.post("/api/caregiver/code",
                       headers=auth(c_token)).status_code == 403


def test_senior_cannot_redeem_code(client):
    s_token, _ = register(client, "senior@test.com", "senior")
    assert client.post("/api/caregiver/link", json={"code": "123456"},
                       headers=auth(s_token)).status_code == 403


def test_expired_or_bad_code_rejected(client):
    c_token, _ = register(client, "care@test.com", "caregiver")
    r = client.post("/api/caregiver/link", json={"code": "000000"},
                    headers=auth(c_token))
    assert r.status_code == 404


def test_model_info_exposed(client):
    body = client.get("/api/model/info").json()
    assert body["available"] is True
    assert body["f1"] > 0.9


def test_patterns_library(client):
    body = client.get("/api/patterns").json()
    assert len(body["patterns"]) >= 6
