"""Typed runtime settings read from the process environment.

Settings are parsed on every call and never cached: tests and operators change the
environment after import, and pilot access configuration is re-read per request.
Secret values are never stored on these objects; only presence flags are kept, and
validation errors name the variable without echoing its value.
"""

from __future__ import annotations

import math
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

HOST_ENV = "MEDICAL_AI_HOST"
PORT_ENV = "MEDICAL_AI_PORT"
WORKERS_ENV = "MEDICAL_AI_WORKERS"
LOG_LEVEL_ENV = "MEDICAL_AI_LOG_LEVEL"
TRUSTED_PROXY_COUNT_ENV = "MEDICAL_AI_TRUSTED_PROXY_COUNT"
TRACE_DB_ENV = "MEDICAL_AI_TRACE_DB"
SESSION_DB_ENV = "MEDICAL_AI_PILOT_SESSION_DB"
HTTP_TIMEOUT_ENV = "MEDICAL_AI_HTTP_TIMEOUT_SECONDS"
NCBI_EMAIL_ENV = "NCBI_EMAIL"
NCBI_API_KEY_ENV = "NCBI_API_KEY"
TRACE_HMAC_KEY_ENV = "MEDICAL_AI_TRACE_HMAC_KEY"
ACCESS_JSON_ENV = "MEDICAL_AI_PILOT_ACCESS_JSON"
ACCESS_FILE_ENV = "MEDICAL_AI_PILOT_ACCESS_FILE"
RATE_LIMIT_ENABLED_ENV = "MEDICAL_AI_RATE_LIMIT_ENABLED"
RATE_LIMIT_ACCESS_ENV = "MEDICAL_AI_RATE_LIMIT_ACCESS_PER_MINUTE"
RATE_LIMIT_QUERY_ENV = "MEDICAL_AI_RATE_LIMIT_QUERY_PER_MINUTE"

MIN_TRACE_HMAC_KEY_BYTES = 32
_LOG_LEVELS = frozenset({"debug", "info", "warning", "error"})

AccessSource = Literal["json", "file", "missing"]


class SettingsError(ValueError):
    """A runtime setting is missing, malformed or out of range."""


@dataclass(frozen=True)
class ServerSettings:
    host: str = "127.0.0.1"
    port: int = 8000
    # Influence revocation state is held per process until the A3 persistent
    # ledger exists, so more than one worker would silently fragment it.
    workers: int = 1
    log_level: str = "info"
    trusted_proxy_count: int = 0


@dataclass(frozen=True)
class StorageSettings:
    trace_db: Path
    session_db: Path


@dataclass(frozen=True)
class ConnectorSettings:
    ncbi_email: str | None = None
    ncbi_api_key: str | None = None
    http_timeout_seconds: float = 20.0


@dataclass(frozen=True)
class RateLimitSettings:
    enabled: bool = True
    access_per_minute: int = 10
    query_per_minute: int = 30


@dataclass(frozen=True)
class Settings:
    server: ServerSettings
    storage: StorageSettings
    connectors: ConnectorSettings
    rate_limits: RateLimitSettings
    trace_hmac_key_configured: bool
    access_source: AccessSource


def parse_bool(value: str, *, default: bool, name: str) -> bool:
    if value == "":
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise SettingsError(f"{name} must be true or false")


def _int_in_range(environ: Mapping[str, str], name: str, default: int, low: int, high: int) -> int:
    raw = environ.get(name, "").strip()
    if raw == "":
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise SettingsError(f"{name} must be an integer") from exc
    if value < low or value > high:
        raise SettingsError(f"{name} must be between {low} and {high}")
    return value


def _float_in_range(
    environ: Mapping[str, str], name: str, default: float, low: float, high: float
) -> float:
    raw = environ.get(name, "").strip()
    if raw == "":
        return default
    try:
        value = float(raw)
    except ValueError as exc:
        raise SettingsError(f"{name} must be a number") from exc
    if not math.isfinite(value) or value < low or value > high:
        raise SettingsError(f"{name} must be between {low:g} and {high:g}")
    return value


def _optional_text(environ: Mapping[str, str], name: str) -> str | None:
    value = environ.get(name, "").strip()
    return value or None


def _state_path(environ: Mapping[str, str], name: str, default_filename: str) -> Path:
    configured = environ.get(name, "").strip()
    path = Path(configured) if configured else Path.home() / ".medical_ai" / default_filename
    return path.expanduser().absolute()


def trace_db_path(environ: Mapping[str, str]) -> Path:
    """Absolute trace database path. Never raises, so it is safe at import time."""

    return _state_path(environ, TRACE_DB_ENV, "medical_ai_traces.sqlite3")


def session_db_path(environ: Mapping[str, str]) -> Path:
    return _state_path(environ, SESSION_DB_ENV, "pilot_sessions.sqlite3")


def _access_source(environ: Mapping[str, str]) -> AccessSource:
    has_json = bool(environ.get(ACCESS_JSON_ENV, ""))
    has_file = bool(environ.get(ACCESS_FILE_ENV, ""))
    if has_json and has_file:
        raise SettingsError(f"Set only one of {ACCESS_JSON_ENV} and {ACCESS_FILE_ENV}")
    if has_json:
        return "json"
    if has_file:
        return "file"
    return "missing"


def load_settings(environ: Mapping[str, str] | None = None) -> Settings:
    env: Mapping[str, str] = os.environ if environ is None else environ

    host = env.get(HOST_ENV, "127.0.0.1")
    if not host.strip():
        raise SettingsError(f"{HOST_ENV} must not be blank")
    log_level = (env.get(LOG_LEVEL_ENV, "").strip() or "info").lower()
    if log_level not in _LOG_LEVELS:
        raise SettingsError(f"{LOG_LEVEL_ENV} must be one of debug, info, warning, error")
    raw_workers = env.get(WORKERS_ENV, "").strip() or "1"
    if raw_workers != "1":
        raise SettingsError(
            f"{WORKERS_ENV} must be 1: revocation state is per-process until a persistent ledger exists"
        )

    server = ServerSettings(
        host=host.strip(),
        port=_int_in_range(env, PORT_ENV, 8000, 1, 65535),
        workers=1,
        log_level=log_level,
        trusted_proxy_count=_int_in_range(env, TRUSTED_PROXY_COUNT_ENV, 0, 0, 2),
    )
    storage = StorageSettings(trace_db=trace_db_path(env), session_db=session_db_path(env))
    connectors = ConnectorSettings(
        ncbi_email=_optional_text(env, NCBI_EMAIL_ENV),
        ncbi_api_key=_optional_text(env, NCBI_API_KEY_ENV),
        http_timeout_seconds=_float_in_range(env, HTTP_TIMEOUT_ENV, 20.0, 1.0, 60.0),
    )
    rate_limits = RateLimitSettings(
        enabled=parse_bool(
            env.get(RATE_LIMIT_ENABLED_ENV, ""), default=True, name=RATE_LIMIT_ENABLED_ENV
        ),
        access_per_minute=_int_in_range(env, RATE_LIMIT_ACCESS_ENV, 10, 1, 10_000),
        query_per_minute=_int_in_range(env, RATE_LIMIT_QUERY_ENV, 30, 1, 10_000),
    )
    hmac_key = env.get(TRACE_HMAC_KEY_ENV, "")
    return Settings(
        server=server,
        storage=storage,
        connectors=connectors,
        rate_limits=rate_limits,
        trace_hmac_key_configured=len(hmac_key.encode("utf-8")) >= MIN_TRACE_HMAC_KEY_BYTES,
        access_source=_access_source(env),
    )
