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
    monkeypatch.setattr(api, "build_engine", StubEngine)


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


@pytest.mark.parametrize('defect', ['missing_revoked', 'misspelt_revoked', 'extra_field', 'root_field', 'duplicate_key'])
def test_malformed_allowlist_invalidates_invites_and_sessions(configured_access, monkeypatch, defect):
    client = TestClient(api.app)
    assert client.post('/access/session', json={'token': VALID_TOKEN}).status_code == 200
    document = _access_document()
    entry = document['participants'][0]
    if defect == 'missing_revoked':
        del entry['revoked']
    elif defect == 'misspelt_revoked':
        del entry['revoked']
        entry['revokd'] = True
    elif defect == 'extra_field':
        entry['revokd'] = True
    elif defect == 'root_field':
        document['particpants'] = []
    raw = json.dumps(document)
    if defect == 'duplicate_key':
        raw = raw.replace('"revoked": false', '"revoked": true, "revoked": false')
    monkeypatch.setenv('MEDICAL_AI_PILOT_ACCESS_JSON', raw)
    assert client.post('/v1/evidence/query', json=_query_payload()).status_code == 503
    assert client.post('/v1/evidence/query', json=_query_payload(),
                       headers={'Authorization': f'Bearer {VALID_TOKEN}'}).status_code == 503


@pytest.mark.parametrize('token', ['tiny', 'X' * 513])
def test_invalid_length_token_cannot_use_bearer_or_exchange(configured_access, monkeypatch, token):
    document = _access_document()
    document['participants'][0]['token_sha256'] = hashlib.sha256(token.encode()).hexdigest()
    monkeypatch.setenv('MEDICAL_AI_PILOT_ACCESS_JSON', json.dumps(document))
    client = TestClient(api.app)
    assert client.post('/v1/evidence/query', json=_query_payload(),
                       headers={'Authorization': f'Bearer {token}'}).status_code == 401
    response = client.post('/access/session', json={'token': token})
    assert response.status_code == 422
    assert token not in response.text


@pytest.mark.parametrize('cookie', ['é.AA', 'AA.é'])
def test_non_ascii_session_cookie_is_rejected(configured_access, cookie):
    from http.cookies import SimpleCookie
    jar = SimpleCookie()
    jar['medical_ai_pilot_session'] = cookie
    response = TestClient(api.app).get('/docs', headers={'Cookie': jar.output(header='').strip()})
    assert response.status_code == 401


@pytest.mark.parametrize('segment', [0, 1])
def test_tampered_session_is_rejected_on_protected_routes(configured_access, segment):
    client = TestClient(api.app)
    assert client.post('/access/session', json={'token': VALID_TOKEN}).status_code == 200
    parts = client.cookies.get('medical_ai_pilot_session').split('.')
    parts[segment] = ('A' if parts[segment][0] != 'A' else 'B') + parts[segment][1:]
    client.cookies.clear()
    client.cookies.set('medical_ai_pilot_session', '.'.join(parts))
    assert client.get('/docs').status_code == 401
    assert client.get('/openapi.json').status_code == 401
    assert client.post('/v1/evidence/query', json=_query_payload()).status_code == 401


def test_credential_rotation_invalidates_existing_session(configured_access, monkeypatch):
    client = TestClient(api.app)
    assert client.post('/access/session', json={'token': VALID_TOKEN}).status_code == 200
    assert client.get('/docs').status_code == 200
    document = _access_document()
    document['participants'][0]['credential_id'] = 'credential-002'
    replacement = 'replacement-invite-' + 'Z' * 40
    document['participants'][0]['token_sha256'] = hashlib.sha256(replacement.encode()).hexdigest()
    monkeypatch.setenv('MEDICAL_AI_PILOT_ACCESS_JSON', json.dumps(document))
    assert client.get('/docs').status_code == 401
    assert client.post('/v1/evidence/query', json=_query_payload(),
                       headers={'Authorization': f'Bearer {VALID_TOKEN}'}).status_code == 401
    assert client.post('/access/session', json={'token': replacement}).status_code == 200
    assert client.get('/docs').status_code == 200


def test_default_session_cookie_security_and_logout(configured_access, monkeypatch):
    from http.cookies import SimpleCookie
    monkeypatch.delenv('MEDICAL_AI_PILOT_COOKIE_SECURE', raising=False)
    client = TestClient(api.app, base_url='https://testserver')
    response = client.post('/access/session', json={'token': VALID_TOKEN})
    assert response.status_code == 200
    jar = SimpleCookie()
    jar.load(response.headers['set-cookie'])
    cookie = jar['medical_ai_pilot_session']
    assert cookie['httponly']
    assert cookie['secure']
    assert cookie['samesite'].lower() == 'strict'
    assert cookie['path'] == '/'
    assert 0 < int(cookie['max-age']) <= 28800
    assert client.get('/docs').status_code == 200
    assert client.post('/access/logout').status_code == 200
    assert client.get('/docs').status_code == 401


def test_session_ttl_is_enforced_independently_of_participant_expiry(configured_access):
    from medical_ai.access import authenticate_session_token, create_session_token, load_access_config
    config = load_access_config()
    now = datetime.now(timezone.utc)
    token, _ = create_session_token(config.participants[0], config, now=now)
    assert authenticate_session_token(token, config, now=now) is not None
    assert authenticate_session_token(token, config, now=now + timedelta(seconds=config.session_ttl_seconds)) is None


def test_validation_errors_never_echo_credentials(configured_access):
    client = TestClient(api.app)
    for payload in [{'token': VALID_TOKEN, 'extra': VALID_TOKEN}, {'token': {'secret': VALID_TOKEN}}]:
        response = client.post('/access/session', json=payload)
        assert response.status_code == 422
        assert VALID_TOKEN not in response.text
    response = client.post('/access/session', content='{"token":"' + VALID_TOKEN,
                           headers={'Content-Type': 'application/json'})
    assert response.status_code == 422
    assert VALID_TOKEN not in response.text


@pytest.mark.parametrize('change', [{'participant_id': 'é'}, {'credential_id': 'é'}, {'exp': True}])
def test_signed_malformed_session_payload_is_rejected(configured_access, change):
    import base64
    import hmac
    payload = {'v': 1, 'participant_id': 'pilot-001', 'credential_id': 'credential-001',
               'exp': int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())}
    payload.update(change)
    encoded = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
    signature = hmac.new(SESSION_SECRET.encode(), encoded.encode(), hashlib.sha256).digest()
    token = encoded + '.' + base64.urlsafe_b64encode(signature).decode().rstrip('=')
    client = TestClient(api.app)
    client.cookies.set('medical_ai_pilot_session', token)
    assert client.get('/docs').status_code == 401


def test_oversized_session_cookie_is_rejected(configured_access):
    client = TestClient(api.app)
    client.cookies.set('medical_ai_pilot_session', 'A' * 4097)
    assert client.get('/docs').status_code == 401
