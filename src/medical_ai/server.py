"""Console entry point: ``medical-ai-serve``.

Validates runtime configuration and starts the single-process API server. The
configuration report prints names, counts and booleans only; it never prints a
secret, a token digest or a filesystem path.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field

import uvicorn

from .access import AccessConfigurationError, load_access_config
from .authority_resolver import AuthorityResolver
from .session_store import PilotSessionStore, SessionStoreUnavailable
from .settings import TRACE_HMAC_KEY_ENV, Settings, SettingsError, load_settings
from .trace_store import SQLiteTraceStore

APP_IMPORT_STRING = "medical_ai.api:app"


def _access_check() -> tuple[bool, int]:
    try:
        config = load_access_config()
    except AccessConfigurationError:
        return False, 0
    return True, len(config.participants)


def _session_store_check(settings: Settings) -> bool:
    try:
        PilotSessionStore(settings.storage.session_db)
    except SessionStoreUnavailable:
        return False
    return True


def _trace_store_check(settings: Settings) -> bool:
    try:
        SQLiteTraceStore(settings.storage.trace_db)
    except Exception:
        return False
    return True


def _policies_check() -> bool:
    # Compiling the resolver verifies every digest-bound authority policy.
    try:
        AuthorityResolver()
    except Exception:
        return False
    return True


@dataclass(frozen=True)
class ConfigReport:
    """Redacted start-up report: names, counts and booleans only."""

    checks: dict[str, bool]
    details: dict[str, str | int | bool] = field(default_factory=lambda: {})
    error: str | None = None

    @property
    def ready(self) -> bool:
        return self.error is None and all(self.checks.values())

    def failed_checks(self) -> list[str]:
        return sorted(name for name, passed in self.checks.items() if not passed)

    def to_json(self) -> str:
        payload: dict[str, object] = {
            "status": "ok" if self.ready else "error",
            "checks": self.checks,
            **self.details,
        }
        if self.error is not None:
            payload["error"] = self.error
        return json.dumps(payload, sort_keys=True)


def check_config() -> ConfigReport:
    """Run every start-up check and return a redacted report."""

    checks: dict[str, bool] = {
        "settings": False,
        "trace_hmac_key": False,
        "access_config": False,
        "session_store": False,
        "trace_store": False,
        "policies": _policies_check(),
    }
    try:
        settings = load_settings()
    except SettingsError as exc:
        return ConfigReport(checks=checks, error=str(exc))

    checks["settings"] = True
    checks["trace_hmac_key"] = settings.trace_hmac_key_configured
    access_ok, participants = _access_check()
    checks["access_config"] = access_ok
    checks["session_store"] = _session_store_check(settings)
    checks["trace_store"] = _trace_store_check(settings)
    details: dict[str, str | int | bool] = {
        "host": settings.server.host,
        "port": settings.server.port,
        "workers": settings.server.workers,
        "log_level": settings.server.log_level,
        "trusted_proxy_count": settings.server.trusted_proxy_count,
        "access_source": settings.access_source,
        "participants": participants,
        "ncbi_email_configured": settings.connectors.ncbi_email is not None,
        "ncbi_api_key_configured": settings.connectors.ncbi_api_key is not None,
    }
    return ConfigReport(checks=checks, details=details)


def _failure_message(report: ConfigReport) -> str:
    if report.error is not None:
        return report.error
    failed = report.failed_checks()
    if "trace_hmac_key" in failed:
        return f"{TRACE_HMAC_KEY_ENV} must be set to at least 32 bytes before the server starts"
    return "start-up checks failed: " + ", ".join(failed)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="medical-ai-serve",
        description="Start the Medical AI evidence workbench API server.",
    )
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="validate configuration, print a redacted JSON report and exit",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    report = check_config()
    if args.check_config:
        print(report.to_json())
        return 0 if report.ready else 1
    if not report.ready:
        print(f"medical-ai-serve: {_failure_message(report)}", file=sys.stderr)
        return 1

    settings = load_settings()
    uvicorn.run(
        APP_IMPORT_STRING,
        host=settings.server.host,
        port=settings.server.port,
        workers=1,
        log_level=settings.server.log_level,
        # Query text and credentials must never reach request logs, and forwarded
        # headers are not trusted until an explicit proxy boundary is configured.
        access_log=False,
        proxy_headers=False,
        server_header=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
