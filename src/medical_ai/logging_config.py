"""Structured, content-free logging.

Log lines are JSON objects with a fixed allowlist of fields. Request content —
query strings, bodies, cookies, authorization values, questions and answers — is
never a log field, and exception text and tracebacks are never serialised (only
the exception type name). Third-party loggers that record full URLs (``httpx``,
``httpcore``) are held at WARNING because connector URLs can carry search terms.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import TextIO

_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
}
# Fields a request log record may carry as ``extra``; nothing else is serialised.
_EXTRA_FIELDS = ("request_id", "method", "path", "status", "duration_ms")
_QUIET_LOGGERS = ("httpx", "httpcore")
_HANDLER_MARK = "_medical_ai_json_handler"


class JsonLogFormatter(logging.Formatter):
    """Render a record as one JSON line using allowlisted fields only."""

    def format(self, record: logging.LogRecord) -> str:
        created = datetime.fromtimestamp(record.created, tz=timezone.utc)
        payload: dict[str, object] = {
            "ts": created.strftime("%Y-%m-%dT%H:%M:%S.") + f"{created.microsecond // 1000:03d}Z",
            "level": record.levelname.lower(),
            "logger": record.name,
            "event": str(getattr(record, "event", None) or record.getMessage()),
        }
        for name in _EXTRA_FIELDS:
            value: object = getattr(record, name, None)
            if value is not None:
                payload[name] = value
        if record.exc_info and record.exc_info[0] is not None:
            payload["error_type"] = record.exc_info[0].__name__
        return json.dumps(payload, sort_keys=True, ensure_ascii=True)


def configure_logging(level: str, *, stream: TextIO | None = None) -> None:
    """Send every log record to ``stream`` (default stderr) as JSON lines.

    Idempotent: a previously installed handler is replaced, never duplicated.
    """

    normalized = level.strip().lower()
    if normalized not in _LEVELS:
        raise ValueError(f"log level must be one of {sorted(_LEVELS)}")
    root = logging.getLogger()
    for handler in list(root.handlers):
        if getattr(handler, _HANDLER_MARK, False):
            root.removeHandler(handler)
    handler = logging.StreamHandler(stream if stream is not None else sys.stderr)
    handler.setFormatter(JsonLogFormatter())
    setattr(handler, _HANDLER_MARK, True)
    root.addHandler(handler)
    root.setLevel(_LEVELS[normalized])
    for name in _QUIET_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)
