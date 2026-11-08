"""EAX-001 TS-01 regression: synthetic rejected values only; no real PHI/secrets."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from pydantic import BaseModel

from medical_ai import api


MARKER = "EAX001-TEST-ONLY-REJECTED-INPUT-SYNTHETIC"
TOKEN = "eax001-test-invite-" + "X" * 40
BAD_HOST = "testserver/decoy?probe="


class OrdinaryPayload(BaseModel):
    text: str


SENSITIVE = (
    ("/access/session", "token", "Invalid pilot credential request"),
    ("/v1/evidence/query", "question", "Invalid evidence query request"),
)


@pytest.fixture
def configured_app(tmp_path, monkeypatch):
    config = {"participants": [{
        "participant_id": "eax001-test-only",
        "credential_id": "synthetic-eax001-credential",
        "token_sha256": hashlib.sha256(TOKEN.encode()).hexdigest(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
        "revoked": False,
    }]}
    monkeypatch.setenv("MEDICAL_AI_PILOT_ACCESS_JSON", json.dumps(config))
    monkeypatch.setenv("MEDICAL_AI_PILOT_SESSION_SECRET", "EAX001-SYNTHETIC-SECRET-DO-NOT-USE-REAL")
    monkeypatch.setenv("MEDICAL_AI_PILOT_SESSION_DB", str(tmp_path / "sessions.sqlite3"))
    monkeypatch.setenv("MEDICAL_AI_PILOT_COOKIE_SECURE", "true")
    original = api.app.exception_handlers[RequestValidationError]
    try:
        yield api.app, original
    finally:
        api.app.exception_handlers[RequestValidationError] = original
        api.app.middleware_stack = None


def _request(app, path, field, *, host=BAD_HOST):
    with TestClient(app, base_url="https://testserver") as client:
        return client.post(
            path,
            json={field: {"synthetic_marker": MARKER}},
            headers={"Host": host, "Authorization": f"Bearer {TOKEN}"},
        )


def _assert_redacted(response, expected):
    assert response.status_code == 422
    assert response.json() == {"detail": expected}
    assert response.headers.get("cache-control") == "no-store"
    assert MARKER not in response.text


@pytest.mark.parametrize("path,field,expected", SENSITIVE)
@pytest.mark.parametrize("host", ["testserver", BAD_HOST])
def test_rejected_inputs_do_not_leak_for_sensitive_endpoints(configured_app, path, field, expected, host):
    app, _ = configured_app
    _assert_redacted(_request(app, path, field, host=host), expected)


@pytest.mark.parametrize("path,field,expected", SENSITIVE)
@pytest.mark.parametrize("mutation", ["absent", "wrong_route", "list_route", "non_string_route", "property_error"])
def test_untrusted_matched_route_cannot_bypass_redaction(configured_app, path, field, expected, mutation):
    app, original = configured_app

    class ErrorRoute:
        @property
        def path(self):
            raise RuntimeError("synthetic route-metadata failure")

    async def inject(request, exc):
        if mutation == "absent":
            request.scope.pop("route", None)
        elif mutation == "property_error":
            request.scope["route"] = ErrorRoute()
        else:
            request.scope["route"] = SimpleNamespace(path={
                "wrong_route": "/other", "list_route": [], "non_string_route": 123
            }[mutation])
        return await original(request, exc)

    app.exception_handlers[RequestValidationError] = inject
    app.middleware_stack = None
    _assert_redacted(_request(app, path, field), expected)


@pytest.mark.parametrize("path,field,_expected", SENSITIVE)
def test_unknown_path_and_route_fail_closed(configured_app, path, field, _expected):
    app, original = configured_app

    async def inject(request, exc):
        request.scope["path"] = None
        request.scope["route"] = None
        return await original(request, exc)

    app.exception_handlers[RequestValidationError] = inject
    app.middleware_stack = None
    _assert_redacted(_request(app, path, field), "Invalid request")


@pytest.mark.parametrize("path,field,expected", SENSITIVE)
def test_matched_route_identifies_sensitive_endpoint_if_scope_path_bad(configured_app, path, field, expected):
    app, original = configured_app

    async def inject(request, exc):
        request.scope["path"] = []
        return await original(request, exc)

    app.exception_handlers[RequestValidationError] = inject
    app.middleware_stack = None
    _assert_redacted(_request(app, path, field), expected)


def test_unrelated_validation_errors_are_conservatively_redacted():
    other = FastAPI()
    other.add_exception_handler(RequestValidationError, api.sensitive_validation_error)

    @other.post("/ordinary")
    def ordinary(req: OrdinaryPayload):
        return {"ok": True}

    _assert_redacted(_request(other, "/ordinary", "text"), "Invalid request")


def test_health_endpoint_is_still_accessible(configured_app):
    app, _ = configured_app
    with TestClient(app, base_url="https://testserver") as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
