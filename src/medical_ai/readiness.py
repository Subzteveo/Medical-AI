"""Readiness checks shared by ``medical-ai-serve`` and ``GET /health/ready``.

Each check returns a boolean only. No path, secret, participant id or exception
text leaves this module.
"""

from __future__ import annotations

from functools import lru_cache

from .access import AccessConfigurationError, load_access_config
from .authority_resolver import AuthorityResolver
from .session_store import PilotSessionStore, SessionStoreUnavailable
from .settings import Settings, SettingsError, load_settings
from .trace_store import SQLiteTraceStore


def access_check() -> tuple[bool, int]:
    try:
        config = load_access_config()
    except AccessConfigurationError:
        return False, 0
    return True, len(config.participants)


def session_store_check(settings: Settings) -> bool:
    try:
        PilotSessionStore(settings.storage.session_db)
    except SessionStoreUnavailable:
        return False
    return True


def trace_store_check(settings: Settings) -> bool:
    try:
        SQLiteTraceStore(settings.storage.trace_db)
    except Exception:
        return False
    return True


@lru_cache(maxsize=1)
def _policies_compile() -> bool:
    # Policy files are immutable for the life of the process, so one successful
    # or failed compilation is authoritative; it is not repeated per request.
    try:
        AuthorityResolver()
    except Exception:
        return False
    return True


def policies_check() -> bool:
    # Compiling the resolver verifies every digest-bound authority policy.
    return _policies_compile()


def readiness_checks() -> dict[str, bool]:
    """Boolean result for each dependency the request path needs."""

    access_ok, _participants = access_check()
    checks = {
        "access_config": access_ok,
        "session_store": False,
        "trace_store": False,
        "policies": policies_check(),
    }
    try:
        settings = load_settings()
    except SettingsError:
        return checks  # unreadable settings fail the store checks closed
    checks["session_store"] = session_store_check(settings)
    checks["trace_store"] = trace_store_check(settings)
    return checks
