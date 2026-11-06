"""ToxSec DES-02: synthetic session lifecycle regressions.

Only temporary test accounts and copied test cookies are used. No real users.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

import medical_ai.api as api
from medical_ai.access import (
    SESSION_COOKIE_NAME,
    authenticate_session_token,
    create_session_token,
    load_access_config,
)
from medical_ai.engine import EvidenceEngine


TOKEN_A = "synthetic-a-" + "A" * 40
TOKEN_B = "synthetic-b-" + "B" * 40
SECRET = "synthetic-secret-" + "S" * 40


@pytest.fixture
def configured_sessions(monkeypatch, tmp_path, fake_connector):
    expiry = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    participants = [
        {"participant_id": who, "credential_id": f"cred-{who}",
         "token_sha256": hashlib.sha256(token.encode()).hexdigest(),
         "expires_at": expiry, "revoked": False}
        for who, token in (("pilot-a", TOKEN_A), ("pilot-b", TOKEN_B))
    ]
    monkeypatch.setenv("MEDICAL_AI_PILOT_ACCESS_JSON", json.dumps({"participants": participants}))
    monkeypatch.setenv("MEDICAL_AI_PILOT_SESSION_SECRET", SECRET)
    monkeypatch.setenv("MEDICAL_AI_PILOT_COOKIE_SECURE", "false")
    monkeypatch.setenv("MEDICAL_AI_PILOT_SESSION_DB", str(tmp_path / "sessions.sqlite3"))
    monkeypatch.setattr(api, "build_engine", lambda: EvidenceEngine(fake_connector))
    return tmp_path / "sessions.sqlite3"


def test_copied_cookie_is_invalid_after_logout_without_ending_other_session(configured_sessions):
    a, b = TestClient(api.app), TestClient(api.app)
    assert a.post("/access/session", json={"token": TOKEN_A}).status_code == 200
    assert b.post("/access/session", json={"token": TOKEN_B}).status_code == 200
    saved_cookie = a.cookies.get(SESSION_COOKIE_NAME)
    assert saved_cookie
    assert a.get("/docs").status_code == 200
    assert b.get("/docs").status_code == 200

    assert a.post("/access/logout").status_code == 200
    copy = TestClient(api.app)
    copy.cookies.set(SESSION_COOKIE_NAME, saved_cookie)
    assert copy.get("/docs").status_code == 401
    assert copy.get("/openapi.json").status_code == 401
    assert b.get("/docs").status_code == 200


def test_sessions_have_distinct_revocable_identity_even_at_same_timestamp(configured_sessions):
    config = load_access_config()
    now = datetime.now(timezone.utc)
    first, _ = create_session_token(config.participants[0], config, now=now)
    second, _ = create_session_token(config.participants[0], config, now=now)
    assert first != second
    assert authenticate_session_token(first, config, now=now) is not None
    assert authenticate_session_token(second, config, now=now) is not None


def test_copied_cookie_rejected_by_fresh_authenticator_after_logout(configured_sessions):
    client = TestClient(api.app)
    assert client.post("/access/session", json={"token": TOKEN_A}).status_code == 200
    saved_cookie = client.cookies.get(SESSION_COOKIE_NAME)
    assert client.post("/access/logout").status_code == 200
    # A newly constructed access configuration and independent DB read.
    assert authenticate_session_token(saved_cookie, load_access_config()) is None


def test_missing_session_storage_fails_closed_on_issuance(configured_sessions, monkeypatch, tmp_path):
    # A directory cannot be a SQLite session database; no stateless fallback.
    monkeypatch.setenv("MEDICAL_AI_PILOT_SESSION_DB", str(tmp_path))
    response = TestClient(api.app).post("/access/session", json={"token": TOKEN_A})
    assert response.status_code == 503
    assert SESSION_COOKIE_NAME not in response.headers.get("set-cookie", "")


def test_session_secret_is_not_persisted_as_plain_cookie(configured_sessions):
    client = TestClient(api.app)
    assert client.post("/access/session", json={"token": TOKEN_A}).status_code == 200
    saved_cookie = client.cookies.get(SESSION_COOKIE_NAME)
    assert configured_sessions.exists()
    data = configured_sessions.read_bytes()
    assert saved_cookie.encode() not in data
    assert TOKEN_A.encode() not in data
