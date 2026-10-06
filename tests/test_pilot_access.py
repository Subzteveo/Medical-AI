from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

import medical_ai.api as api


VALID_TOKEN = "pilot-token-" + ("A" * 40)
SESSION_SECRET = "session-secret-" + ("S" * 40)


class StubEngine:
    async def answer(self, question, *, user_mode, jurisdiction, limit):
        return {
            "status": "EVIDENCE_INSUFFICIENT",
            "question_seen": question,
            "user_mode": user_mode,
            "jurisdiction": jurisdiction,
            "limit": limit,
        }


def _access_document(*, revoked=False, expires_at=None):
    expiry = expires_at or (datetime.now(timezone.utc) + timedelta(days=30))
    return {
        "participants": [
            {
                "participant_id": "pilot-001",
                "credential_id": "credential-001",
                "token_sha256": hashlib.sha256(VALID_TOKEN.encode("utf-8")).hexdigest(),
                "expires_at": expiry.isoformat(),
                "revoked": revoked,
            }
        ]
    }


@pytest.fixture
def configured_access(monkeypatch):
    monkeypatch.setenv("MEDICAL_AI_PILOT_ACCESS_JSON", json.dumps(_access_document()))
    monkeypatch.setenv("MEDICAL_AI_PILOT_SESSION_SECRET", SESSION_SECRET)
    monkeypatch.setenv("MEDICAL_AI_PILOT_COOKIE_SECURE", "false")
    monkeypatch.setattr(api, "build_engine", lambda: StubEngine())


def _query_payload(**extra):
    payload = {
        "question": "What evidence exists for exercise reducing blood pressure?",
        "user_mode": "student",
        "jurisdiction": "AU",
        "limit": 3,
    }
    payload.update(extra)
    return payload


def test_missing_configuration_fails_closed(monkeypatch):
    monkeypatch.delenv("MEDICAL_AI_PILOT_ACCESS_JSON", raising=False)
    monkeypatch.delenv("MEDICAL_AI_PILOT_SESSION_SECRET", raising=False)
    response = TestClient(api.app).post("/v1/evidence/query", json=_query_payload())
    assert response.status_code == 503


def test_unauthenticated_evidence_query_is_rejected(configured_access):
    response = TestClient(api.app).post("/v1/evidence/query", json=_query_payload())
    assert response.status_code == 401


def test_invalid_bearer_credential_is_rejected(configured_access):
    response = TestClient(api.app).post(
        "/v1/evidence/query",
        json=_query_payload(),
        headers={"Authorization": "Bearer not-a-valid-pilot-token"},
    )
    assert response.status_code == 401


def test_valid_invited_participant_can_use_direct_api(configured_access):
    response = TestClient(api.app).post(
        "/v1/evidence/query",
        json=_query_payload(),
        headers={"Authorization": f"Bearer {VALID_TOKEN}"},
    )
    assert response.status_code == 200
    assert response.json()["user_mode"] == "student"


def test_expired_participant_is_rejected(configured_access, monkeypatch):
    expired = datetime.now(timezone.utc) - timedelta(minutes=1)
    monkeypatch.setenv(
        "MEDICAL_AI_PILOT_ACCESS_JSON",
        json.dumps(_access_document(expires_at=expired)),
    )
    response = TestClient(api.app).post(
        "/v1/evidence/query",
        json=_query_payload(),
        headers={"Authorization": f"Bearer {VALID_TOKEN}"},
    )
    assert response.status_code == 401


def test_revoked_participant_is_rejected(configured_access, monkeypatch):
    monkeypatch.setenv(
        "MEDICAL_AI_PILOT_ACCESS_JSON",
        json.dumps(_access_document(revoked=True)),
    )
    response = TestClient(api.app).post(
        "/v1/evidence/query",
        json=_query_payload(),
        headers={"Authorization": f"Bearer {VALID_TOKEN}"},
    )
    assert response.status_code == 401


def test_revocation_invalidates_existing_session(configured_access, monkeypatch):
    client = TestClient(api.app)
    assert client.post("/access/session", json={"token": VALID_TOKEN}).status_code == 200

    monkeypatch.setenv(
        "MEDICAL_AI_PILOT_ACCESS_JSON",
        json.dumps(_access_document(revoked=True)),
    )
    response = client.post("/v1/evidence/query", json=_query_payload())
    assert response.status_code == 401


def test_expiry_invalidates_existing_session(configured_access, monkeypatch):
    client = TestClient(api.app)
    assert client.post("/access/session", json={"token": VALID_TOKEN}).status_code == 200

    expired = datetime.now(timezone.utc) - timedelta(minutes=1)
    monkeypatch.setenv(
        "MEDICAL_AI_PILOT_ACCESS_JSON",
        json.dumps(_access_document(expires_at=expired)),
    )
    response = client.post("/v1/evidence/query", json=_query_payload())
    assert response.status_code == 401


def test_browser_entry_requires_session_then_serves_workbench(configured_access):
    client = TestClient(api.app)
    anonymous = client.get("/")
    assert anonymous.status_code == 200
    assert "Medical AI Pilot" in anonymous.text
    assert 'id="question"' not in anonymous.text

    login = client.post("/access/session", json={"token": VALID_TOKEN})
    assert login.status_code == 200
    assert login.json()["participant_id"] == "pilot-001"

    authenticated = client.get("/")
    assert authenticated.status_code == 200
    assert "Medical AI Evidence Workbench" in authenticated.text
    assert 'id="question"' in authenticated.text


def test_docs_and_openapi_require_access(configured_access):
    client = TestClient(api.app)
    assert client.get("/docs").status_code == 401
    assert client.get("/openapi.json").status_code == 401

    assert client.post("/access/session", json={"token": VALID_TOKEN}).status_code == 200
    assert client.get("/docs").status_code == 200
    schema = client.get("/openapi.json")
    assert schema.status_code == 200
    assert "/v1/evidence/query" in schema.json()["paths"]


def test_request_body_cannot_override_participant_identity(configured_access):
    response = TestClient(api.app).post(
        "/v1/evidence/query",
        json=_query_payload(participant_id="different-user"),
        headers={"Authorization": f"Bearer {VALID_TOKEN}"},
    )
    assert response.status_code == 422


def test_raw_invite_token_not_echoed_to_response_cookie_or_logs(configured_access, caplog):
    client = TestClient(api.app)
    response = client.post("/access/session", json={"token": VALID_TOKEN})
    assert response.status_code == 200
    assert VALID_TOKEN not in response.text
    assert VALID_TOKEN not in response.headers.get("set-cookie", "")
    assert VALID_TOKEN not in caplog.text


def test_health_is_intentionally_public(configured_access):
    response = TestClient(api.app).get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
