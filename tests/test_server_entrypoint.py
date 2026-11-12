from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone

import pytest

from medical_ai import server

TOKEN = "pilot-token-" + ("E" * 40)
SESSION_SECRET = "session-secret-" + ("S" * 40)
HMAC_KEY = "trace-hmac-key-" + ("H" * 40)
NCBI_KEY = "synthetic-ncbi-api-key-value"


def _allowlist() -> str:
    return json.dumps({"participants": [{
        "participant_id": "pilot-001",
        "credential_id": "credential-001",
        "token_sha256": hashlib.sha256(TOKEN.encode()).hexdigest(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        "revoked": False,
    }]})


@pytest.fixture
def configured(monkeypatch, tmp_path):
    monkeypatch.setenv("MEDICAL_AI_PILOT_ACCESS_JSON", _allowlist())
    monkeypatch.setenv("MEDICAL_AI_PILOT_SESSION_SECRET", SESSION_SECRET)
    monkeypatch.setenv("MEDICAL_AI_TRACE_HMAC_KEY", HMAC_KEY)
    monkeypatch.setenv("NCBI_API_KEY", NCBI_KEY)
    monkeypatch.setenv("MEDICAL_AI_TRACE_DB", str(tmp_path / "traces.sqlite3"))
    monkeypatch.setenv("MEDICAL_AI_PILOT_SESSION_DB", str(tmp_path / "sessions.sqlite3"))
    for name in ("MEDICAL_AI_HOST", "MEDICAL_AI_PORT", "MEDICAL_AI_WORKERS",
                 "MEDICAL_AI_LOG_LEVEL", "MEDICAL_AI_PILOT_ACCESS_FILE"):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def recorded_run(monkeypatch):
    calls: list[tuple[tuple, dict]] = []
    monkeypatch.setattr(server.uvicorn, "run", lambda *args, **kwargs: calls.append((args, kwargs)))
    return calls


def test_run_passes_safe_uvicorn_options(configured, recorded_run, monkeypatch):
    monkeypatch.setenv("MEDICAL_AI_HOST", "0.0.0.0")
    monkeypatch.setenv("MEDICAL_AI_PORT", "8123")
    assert server.main([]) == 0
    (args, kwargs), = recorded_run
    assert args == ("medical_ai.api:app",)
    assert kwargs["host"] == "0.0.0.0"
    assert kwargs["port"] == 8123
    assert kwargs["workers"] == 1
    assert kwargs["access_log"] is False
    assert kwargs["proxy_headers"] is False
    assert kwargs["server_header"] is False
    assert kwargs["log_level"] == "info"


def test_refuses_to_start_without_trace_hmac_key(configured, recorded_run, monkeypatch, capsys):
    monkeypatch.delenv("MEDICAL_AI_TRACE_HMAC_KEY")
    assert server.main([]) == 1
    assert recorded_run == []
    assert "MEDICAL_AI_TRACE_HMAC_KEY" in capsys.readouterr().err


def test_refuses_to_start_with_short_trace_hmac_key(configured, recorded_run, monkeypatch):
    monkeypatch.setenv("MEDICAL_AI_TRACE_HMAC_KEY", "too-short")
    assert server.main([]) == 1
    assert recorded_run == []


def test_refuses_to_start_with_invalid_settings(configured, recorded_run, monkeypatch, capsys):
    monkeypatch.setenv("MEDICAL_AI_WORKERS", "4")
    assert server.main([]) == 1
    assert recorded_run == []
    assert "MEDICAL_AI_WORKERS" in capsys.readouterr().err


def test_refuses_to_start_without_access_configuration(configured, recorded_run, monkeypatch):
    monkeypatch.delenv("MEDICAL_AI_PILOT_ACCESS_JSON")
    assert server.main([]) == 1
    assert recorded_run == []


def test_check_config_reports_ready_without_starting_or_leaking(configured, recorded_run, capsys):
    assert server.main(["--check-config"]) == 0
    assert recorded_run == []
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert report["status"] == "ok"
    assert report["checks"] == {
        "settings": True, "trace_hmac_key": True, "access_config": True,
        "session_store": True, "trace_store": True, "policies": True,
    }
    assert report["participants"] == 1
    assert report["access_source"] == "json"
    assert report["ncbi_api_key_configured"] is True
    for secret in (TOKEN, SESSION_SECRET, HMAC_KEY, NCBI_KEY,
                   hashlib.sha256(TOKEN.encode()).hexdigest()):
        assert secret not in captured.out
        assert secret not in captured.err


def test_check_config_fails_closed_and_names_failed_check(configured, recorded_run, monkeypatch, capsys):
    monkeypatch.setenv("MEDICAL_AI_PILOT_SESSION_SECRET", "short")
    assert server.main(["--check-config"]) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "error"
    assert report["checks"]["access_config"] is False
    assert report["checks"]["policies"] is True


def test_check_config_reports_unusable_session_store(configured, monkeypatch, tmp_path, capsys):
    blocker = tmp_path / "not-a-directory"
    blocker.write_text("x")
    monkeypatch.setenv("MEDICAL_AI_PILOT_SESSION_DB", str(blocker / "sessions.sqlite3"))
    assert server.main(["--check-config"]) == 1
    assert json.loads(capsys.readouterr().out)["checks"]["session_store"] is False


def test_importing_api_needs_no_environment(tmp_path):
    # CI's import smoke runs with no pilot configuration at all, and a malformed
    # server setting must not break importing the application module.
    import os
    import subprocess
    import sys

    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": str(tmp_path),
        "PYTHONPATH": os.pathsep.join(sys.path),
        "MEDICAL_AI_PORT": "not-a-port",
    }
    result = subprocess.run(
        [sys.executable, "-c",
         "import medical_ai.api as a, pathlib; "
         "assert a.app is not None; assert pathlib.Path(a.TRACE_DB).is_absolute()"],
        env=env, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert not (tmp_path / ".medical_ai").exists()
