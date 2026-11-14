"""C4: readiness endpoint, structured no-content logging and request ids."""
from __future__ import annotations

import hashlib
import io
import json
import logging
import re
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import medical_ai.api as api
from medical_ai import logging_config, server
from medical_ai.engine import EvidenceEngine

VALID_TOKEN = "pilot-token-" + ("B" * 40)
SESSION_SECRET = "session-secret-" + ("T" * 40)
SYNTHETIC_QUESTION = "synthetic-question-marker zebra-quartz-17 about hypertension"
SYNTHETIC_QUERY_STRING = "probe=synthetic-query-marker-quartz-99"
LOG_FIELDS = {"ts", "level", "logger", "event", "request_id", "method", "path", "status", "duration_ms"}


def _allowlist() -> str:
    expiry = datetime.now(timezone.utc) + timedelta(days=30)
    return json.dumps(
        {
            "participants": [
                {
                    "participant_id": "pilot-001",
                    "credential_id": "credential-001",
                    "token_sha256": hashlib.sha256(VALID_TOKEN.encode("utf-8")).hexdigest(),
                    "expires_at": expiry.isoformat(),
                    "revoked": False,
                }
            ]
        }
    )


@pytest.fixture
def configured(monkeypatch, fake_connector):
    monkeypatch.setenv("MEDICAL_AI_PILOT_ACCESS_JSON", _allowlist())
    monkeypatch.setenv("MEDICAL_AI_PILOT_SESSION_SECRET", SESSION_SECRET)
    monkeypatch.setenv("MEDICAL_AI_PILOT_COOKIE_SECURE", "false")
    monkeypatch.setattr(api, "build_engine", lambda: EvidenceEngine(fake_connector))


@pytest.fixture(autouse=True)
def restore_logging_state():
    root = logging.getLogger()
    handlers, level = list(root.handlers), root.level
    quiet = {name: logging.getLogger(name).level for name in ("httpx", "httpcore")}
    yield
    root.handlers[:] = handlers
    root.setLevel(level)
    for name, value in quiet.items():
        logging.getLogger(name).setLevel(value)


def _capture_with_production_logging(caplog: pytest.LogCaptureFixture) -> None:
    """Capture records under the same logging set-up ``medical-ai-serve`` installs.

    The in-process test client is built on httpx, whose own INFO line records the
    full request URL; production configuration holds that logger at WARNING, so
    the capture must too or it would measure the test client, not the server.
    """
    logging_config.configure_logging("debug", stream=io.StringIO())
    caplog.set_level(logging.DEBUG)


def _client() -> TestClient:
    return TestClient(api.app)


# --- readiness ---------------------------------------------------------------


def test_ready_reports_all_checks_when_configured(configured):
    response = _client().get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "checks": {"access_config": True, "session_store": True, "trace_store": True, "policies": True},
    }
    assert response.headers["cache-control"] == "no-store"


def test_ready_is_503_and_names_the_failed_check_without_access_config(monkeypatch):
    monkeypatch.delenv("MEDICAL_AI_PILOT_ACCESS_JSON", raising=False)
    monkeypatch.delenv("MEDICAL_AI_PILOT_ACCESS_FILE", raising=False)
    response = _client().get("/health/ready")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "not_ready"
    assert body["checks"]["access_config"] is False
    assert body["checks"]["policies"] is True


def test_ready_reports_unusable_session_store(configured, monkeypatch, tmp_path):
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory")
    monkeypatch.setenv("MEDICAL_AI_PILOT_SESSION_DB", str(blocker / "sessions.sqlite3"))
    response = _client().get("/health/ready")
    assert response.status_code == 503
    assert response.json()["checks"]["session_store"] is False


def test_ready_body_never_contains_paths_secrets_or_participants(configured, tmp_path):
    for response in (_client().get("/health/ready"),):
        text = response.text
        assert str(tmp_path) not in text
        assert SESSION_SECRET not in text
        assert VALID_TOKEN not in text
        assert "pilot-001" not in text
        assert "sqlite" not in text.lower()


def test_ready_is_public_and_needs_no_session(configured):
    assert _client().get("/health/ready").status_code in (200, 503)
    assert _client().get("/health/ready", headers={"Cookie": "bogus=1"}).status_code in (200, 503)


def test_ready_is_503_when_settings_are_invalid(configured, monkeypatch):
    monkeypatch.setenv("MEDICAL_AI_WORKERS", "4")
    response = _client().get("/health/ready")
    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"


# --- request id --------------------------------------------------------------


def test_request_id_is_generated_and_echoed_without_proxy(configured):
    response = _client().get("/health")
    request_id = response.headers["x-request-id"]
    assert str(uuid.UUID(request_id)) == request_id


def test_inbound_request_id_ignored_when_proxy_count_is_zero(configured):
    response = _client().get("/health", headers={"X-Request-ID": "caller-supplied-id-123"})
    assert response.headers["x-request-id"] != "caller-supplied-id-123"


def test_inbound_request_id_honoured_behind_trusted_proxy(configured, monkeypatch):
    monkeypatch.setenv("MEDICAL_AI_TRUSTED_PROXY_COUNT", "1")
    response = _client().get("/health", headers={"X-Request-ID": "proxy-supplied-id-123"})
    assert response.headers["x-request-id"] == "proxy-supplied-id-123"


@pytest.mark.parametrize("bad", ["short", "has space in it 12345", "semi;colon;12345678", "x" * 65, "new\tline-12345"])
def test_malformed_inbound_request_id_is_replaced(configured, monkeypatch, bad):
    monkeypatch.setenv("MEDICAL_AI_TRUSTED_PROXY_COUNT", "1")
    response = _client().get("/health", headers={"X-Request-ID": bad})
    assert response.headers["x-request-id"] != bad
    assert re.fullmatch(r"[0-9a-f-]{36}", response.headers["x-request-id"])


def test_request_id_present_on_error_responses(configured):
    assert "x-request-id" in _client().post("/v1/evidence/query", json={}).headers  # 401
    assert "x-request-id" in _client().post("/access/session", json={"token": "x"}).headers  # 422
    assert "x-request-id" in _client().get("/no/such/route").headers  # 404


# --- logging -----------------------------------------------------------------


def _render_all(records: list[logging.LogRecord]) -> list[str]:
    formatter = logging_config.JsonLogFormatter()
    return [formatter.format(record) for record in records]


def test_request_log_has_only_allowlisted_fields(configured, caplog):
    _capture_with_production_logging(caplog)
    _client().get("/health")
    rendered = [json.loads(line) for line in _render_all(caplog.records)]
    request_lines = [line for line in rendered if line.get("event") == "request.completed"]
    assert request_lines, "no request.completed log line was emitted"
    for line in request_lines:
        assert set(line) <= LOG_FIELDS
        assert line["method"] == "GET"
        assert line["path"] == "/health"
        assert line["status"] == 200
        assert isinstance(line["duration_ms"], (int, float))
        assert line["request_id"]


def test_logs_never_contain_request_content(configured, caplog):
    _capture_with_production_logging(caplog)
    client = _client()
    session = client.post(f"/access/session?{SYNTHETIC_QUERY_STRING}", json={"token": VALID_TOKEN})
    assert session.status_code == 200
    cookie_value = session.cookies.get("medical_ai_session") or next(iter(session.cookies.values()))
    answer = client.post(
        f"/v1/evidence/query?{SYNTHETIC_QUERY_STRING}",
        json={"question": SYNTHETIC_QUESTION, "user_mode": "student", "jurisdiction": "AU"},
    )
    assert answer.status_code == 200
    # Also a rejected request carrying the same text, and an unauthenticated one.
    client.post("/v1/evidence/query", json={"question": SYNTHETIC_QUESTION, "bogus": 1})
    TestClient(api.app).post(
        f"/v1/evidence/query?{SYNTHETIC_QUERY_STRING}",
        json={"question": SYNTHETIC_QUESTION},
    )
    answer_text = answer.json()["answer"] if isinstance(answer.json().get("answer"), str) else ""

    combined = "\n".join(_render_all(caplog.records)) + caplog.text
    for forbidden in (
        VALID_TOKEN,
        SESSION_SECRET,
        cookie_value,
        SYNTHETIC_QUESTION,
        "zebra-quartz-17",
        SYNTHETIC_QUERY_STRING,
        "synthetic-query-marker-quartz-99",
        "authorization",
        "pilot-001",
    ):
        assert forbidden not in combined, forbidden
    if answer_text:
        assert answer_text not in combined


def test_unknown_paths_are_not_logged_verbatim(configured, caplog):
    _capture_with_production_logging(caplog)
    _client().get("/probe/synthetic-path-marker-zq91")
    combined = "\n".join(_render_all(caplog.records))
    assert "synthetic-path-marker-zq91" not in combined
    assert '"path": "unmatched"' in combined


def test_failing_route_metadata_does_not_break_the_request_or_the_log(configured):
    class HostileRoute:
        @property
        def path(self) -> str:
            raise RuntimeError("synthetic route-metadata failure")

    request = SimpleNamespace(scope={"route": HostileRoute()})
    assert api._route_template(request) == "unmatched"  # type: ignore[arg-type]


def test_error_responses_are_logged_with_their_status(configured, caplog):
    _capture_with_production_logging(caplog)
    _client().post("/v1/evidence/query", json={"question": SYNTHETIC_QUESTION})
    statuses = [
        json.loads(line)["status"]
        for line in _render_all(caplog.records)
        if json.loads(line).get("event") == "request.completed"
    ]
    assert 401 in statuses


def test_unhandled_exception_is_logged_without_message_text(configured, caplog, monkeypatch):
    _capture_with_production_logging(caplog)

    async def boom(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError(f"boom {SYNTHETIC_QUESTION}")

    monkeypatch.setattr(EvidenceEngine, "answer", boom)
    client = TestClient(api.app, raise_server_exceptions=False)
    client.post("/access/session", json={"token": VALID_TOKEN})
    response = client.post("/v1/evidence/query", json={"question": SYNTHETIC_QUESTION})
    assert response.status_code == 500
    combined = "\n".join(_render_all(caplog.records))
    assert SYNTHETIC_QUESTION not in combined
    assert "zebra-quartz-17" not in combined
    assert any(
        json.loads(line).get("status") == 500 for line in _render_all(caplog.records) if json.loads(line).get("event") == "request.completed"
    )


def test_formatter_never_serialises_unallowlisted_extras_or_tracebacks():
    try:
        raise ValueError("secret-exception-text")
    except ValueError:
        import sys

        exc_info = sys.exc_info()
    record = logging.LogRecord("medical_ai.test", logging.ERROR, __file__, 1, "plain event", None, exc_info)
    record.question = "secret-question-text"  # type: ignore[attr-defined]
    record.cookie = "secret-cookie-text"  # type: ignore[attr-defined]
    line = logging_config.JsonLogFormatter().format(record)
    assert "secret-exception-text" not in line
    assert "secret-question-text" not in line
    assert "secret-cookie-text" not in line
    payload = json.loads(line)
    assert set(payload) <= LOG_FIELDS | {"error_type"}
    assert payload["error_type"] == "ValueError"


def test_configure_logging_emits_json_lines_to_stderr(capsys):
    logging_config.configure_logging("info")
    logging.getLogger("medical_ai.test").info("hello-event")
    err = capsys.readouterr().err.strip().splitlines()
    assert err, "nothing was written to stderr"
    payload = json.loads(err[-1])
    assert payload["event"] == "hello-event"
    assert payload["level"] == "info"
    assert payload["logger"] == "medical_ai.test"
    assert payload["ts"].endswith("Z")


def test_configure_logging_is_idempotent_and_honours_level(capsys):
    logging_config.configure_logging("info")
    logging_config.configure_logging("warning")
    logging.getLogger("medical_ai.test").info("should-not-appear")
    logging.getLogger("medical_ai.test").warning("should-appear")
    out = capsys.readouterr().err
    assert "should-not-appear" not in out
    assert out.count("should-appear") == 1


def test_configure_logging_rejects_unknown_level():
    with pytest.raises(ValueError):
        logging_config.configure_logging("verbose")


def test_configure_logging_covers_uvicorn_loggers(capsys):
    logging_config.configure_logging("info")
    logging.getLogger("uvicorn.error").info("uvicorn-line")
    line = capsys.readouterr().err.strip().splitlines()[-1]
    assert json.loads(line)["event"] == "uvicorn-line"


def test_http_client_loggers_that_record_urls_are_held_at_warning():
    stream = io.StringIO()
    logging_config.configure_logging("debug", stream=stream)
    logging.getLogger("httpx").info("HTTP Request: GET https://example.invalid/?term=synthetic-term-marker")
    logging.getLogger("httpcore").debug("synthetic-term-marker")
    assert "synthetic-term-marker" not in stream.getvalue()
    logging.getLogger("httpx").warning("kept-warning")
    assert "kept-warning" in stream.getvalue()


def test_stream_can_be_redirected_for_tests():
    stream = io.StringIO()
    logging_config.configure_logging("info", stream=stream)
    logging.getLogger("medical_ai.test").info("redirected")
    assert "redirected" in stream.getvalue()


# --- server wiring -------------------------------------------------------------


def test_server_configures_logging_and_disables_uvicorn_log_config(monkeypatch, tmp_path):
    monkeypatch.setenv("MEDICAL_AI_PILOT_ACCESS_JSON", _allowlist())
    monkeypatch.setenv("MEDICAL_AI_PILOT_SESSION_SECRET", SESSION_SECRET)
    monkeypatch.setenv("MEDICAL_AI_TRACE_HMAC_KEY", "h" * 40)
    calls: list[dict[str, object]] = []
    configured_levels: list[str] = []
    monkeypatch.setattr(server.uvicorn, "run", lambda *_a, **kw: calls.append(kw))
    monkeypatch.setattr(server, "configure_logging", lambda level, **_kw: configured_levels.append(level))
    assert server.main([]) == 0
    assert configured_levels == ["info"]
    assert calls[0]["log_config"] is None
    assert calls[0]["access_log"] is False


def test_check_config_does_not_reconfigure_logging(monkeypatch, tmp_path):
    monkeypatch.setenv("MEDICAL_AI_PILOT_ACCESS_JSON", _allowlist())
    monkeypatch.setenv("MEDICAL_AI_PILOT_SESSION_SECRET", SESSION_SECRET)
    monkeypatch.setenv("MEDICAL_AI_TRACE_HMAC_KEY", "h" * 40)
    called: list[str] = []
    monkeypatch.setattr(server, "configure_logging", lambda level, **_kw: called.append(level))
    server.main(["--check-config"])
    assert called == []
