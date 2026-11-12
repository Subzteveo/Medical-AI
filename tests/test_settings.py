from __future__ import annotations

from pathlib import Path

import pytest

from medical_ai.settings import (
    SettingsError,
    load_settings,
    parse_bool,
    trace_db_path,
)


def test_defaults_are_local_single_worker_and_absolute_paths():
    settings = load_settings({})
    assert settings.server.host == "127.0.0.1"
    assert settings.server.port == 8000
    assert settings.server.workers == 1
    assert settings.server.log_level == "info"
    assert settings.server.trusted_proxy_count == 0
    assert settings.storage.trace_db.is_absolute()
    assert settings.storage.trace_db.name == "medical_ai_traces.sqlite3"
    assert settings.storage.session_db.is_absolute()
    assert settings.storage.session_db.name == "pilot_sessions.sqlite3"
    assert settings.connectors.ncbi_email is None
    assert settings.connectors.ncbi_api_key is None
    assert settings.connectors.http_timeout_seconds == 20.0
    assert settings.rate_limits.enabled is True
    assert settings.rate_limits.access_per_minute == 10
    assert settings.rate_limits.query_per_minute == 30
    assert settings.trace_hmac_key_configured is False
    assert settings.access_source == "missing"


def test_environment_values_are_applied():
    settings = load_settings({
        "MEDICAL_AI_HOST": "0.0.0.0",
        "MEDICAL_AI_PORT": "9000",
        "MEDICAL_AI_LOG_LEVEL": "WARNING",
        "MEDICAL_AI_TRUSTED_PROXY_COUNT": "1",
        "MEDICAL_AI_TRACE_DB": "/var/lib/medical-ai/t.sqlite3",
        "MEDICAL_AI_PILOT_SESSION_DB": "/var/lib/medical-ai/s.sqlite3",
        "MEDICAL_AI_HTTP_TIMEOUT_SECONDS": "7.5",
        "NCBI_EMAIL": "ops@example.invalid",
        "NCBI_API_KEY": "synthetic-ncbi-key",
        "MEDICAL_AI_TRACE_HMAC_KEY": "k" * 32,
        "MEDICAL_AI_PILOT_ACCESS_JSON": "{}",
    })
    assert settings.server.host == "0.0.0.0"
    assert settings.server.port == 9000
    assert settings.server.log_level == "warning"
    assert settings.server.trusted_proxy_count == 1
    assert settings.storage.trace_db == Path("/var/lib/medical-ai/t.sqlite3")
    assert settings.storage.session_db == Path("/var/lib/medical-ai/s.sqlite3")
    assert settings.connectors.http_timeout_seconds == 7.5
    assert settings.connectors.ncbi_email == "ops@example.invalid"
    assert settings.connectors.ncbi_api_key == "synthetic-ncbi-key"
    assert settings.trace_hmac_key_configured is True
    assert settings.access_source == "json"


@pytest.mark.parametrize("environ", [
    {"MEDICAL_AI_PORT": "0"},
    {"MEDICAL_AI_PORT": "65536"},
    {"MEDICAL_AI_PORT": "eighty"},
    {"MEDICAL_AI_HOST": "  "},
    {"MEDICAL_AI_LOG_LEVEL": "verbose"},
    {"MEDICAL_AI_TRUSTED_PROXY_COUNT": "-1"},
    {"MEDICAL_AI_TRUSTED_PROXY_COUNT": "3"},
    {"MEDICAL_AI_HTTP_TIMEOUT_SECONDS": "0.5"},
    {"MEDICAL_AI_HTTP_TIMEOUT_SECONDS": "61"},
    {"MEDICAL_AI_HTTP_TIMEOUT_SECONDS": "nan"},
    {"MEDICAL_AI_RATE_LIMIT_ENABLED": "maybe"},
    {"MEDICAL_AI_RATE_LIMIT_ACCESS_PER_MINUTE": "0"},
    {"MEDICAL_AI_RATE_LIMIT_QUERY_PER_MINUTE": "100000"},
])
def test_invalid_values_are_rejected(environ):
    with pytest.raises(SettingsError):
        load_settings(environ)


@pytest.mark.parametrize("workers", ["0", "2", "8", "many"])
def test_workers_above_one_rejected(workers):
    # Revocation state and (later) rate limits are per-process until A3.
    with pytest.raises(SettingsError):
        load_settings({"MEDICAL_AI_WORKERS": workers})


def test_json_and_file_access_sources_conflict():
    with pytest.raises(SettingsError):
        load_settings({
            "MEDICAL_AI_PILOT_ACCESS_JSON": "{}",
            "MEDICAL_AI_PILOT_ACCESS_FILE": "/etc/medical-ai/allowlist.json",
        })
    only_file = load_settings({"MEDICAL_AI_PILOT_ACCESS_FILE": "/etc/medical-ai/allowlist.json"})
    assert only_file.access_source == "file"


def test_short_trace_hmac_key_is_not_reported_as_configured():
    assert load_settings({"MEDICAL_AI_TRACE_HMAC_KEY": "short"}).trace_hmac_key_configured is False


def test_settings_error_never_echoes_the_rejected_value():
    with pytest.raises(SettingsError) as excinfo:
        load_settings({"MEDICAL_AI_PORT": "synthetic-secret-looking-value"})
    assert "synthetic-secret-looking-value" not in str(excinfo.value)
    assert "MEDICAL_AI_PORT" in str(excinfo.value)


def test_load_settings_reads_environment_on_every_call(monkeypatch):
    monkeypatch.setenv("MEDICAL_AI_PORT", "8101")
    assert load_settings().server.port == 8101
    monkeypatch.setenv("MEDICAL_AI_PORT", "8102")
    assert load_settings().server.port == 8102


def test_trace_db_path_is_absolute_and_never_raises():
    assert trace_db_path({}).is_absolute()
    assert trace_db_path({"MEDICAL_AI_TRACE_DB": "relative/t.sqlite3"}).is_absolute()
    assert trace_db_path({"MEDICAL_AI_TRACE_DB": ""}).is_absolute()


def test_parse_bool():
    assert parse_bool("", default=True, name="X") is True
    assert parse_bool(" Off ", default=True, name="X") is False
    assert parse_bool("YES", default=False, name="X") is True
    with pytest.raises(SettingsError):
        parse_bool("2", default=True, name="X")
