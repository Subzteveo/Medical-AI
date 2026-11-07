"""Durable pilot browser-session state.

Only random session-ID digests and bounded access metadata are retained. This
state is *not* a medical audit store and never grants medical evidence authority.
The shared SQLite path must be accessible to every worker in the proposed
single-host pilot; a database outage is a denial, not stateless fallback.
"""
from __future__ import annotations

import hashlib
import os
import sqlite3
import stat
from contextlib import closing
from pathlib import Path


SESSION_DB_ENV = "MEDICAL_AI_PILOT_SESSION_DB"


class SessionStoreUnavailable(RuntimeError):
    """Required session state cannot be accessed safely."""


def _digest_session_id(session_id: str) -> str:
    return hashlib.sha256(session_id.encode("ascii")).hexdigest()


class PilotSessionStore:
    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser().absolute()
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            # Avoid following a final-component symlink into an unintended file.
            flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
            fd = os.open(self.path, flags, 0o600)
            os.close(fd)
            if not stat.S_ISREG(self.path.stat().st_mode):
                raise SessionStoreUnavailable("Pilot session store is not a regular file")
            if stat.S_IMODE(self.path.stat().st_mode) & 0o077:
                raise SessionStoreUnavailable("Pilot session store permissions are too broad")
            with closing(sqlite3.connect(self.path, timeout=5)) as db, db:
                db.execute(
                    """
                    CREATE TABLE IF NOT EXISTS pilot_sessions (
                        session_id_digest TEXT PRIMARY KEY,
                        participant_id TEXT NOT NULL,
                        credential_id TEXT NOT NULL,
                        expires_at INTEGER NOT NULL,
                        revoked INTEGER NOT NULL CHECK (revoked IN (0,1))
                    )
                    """
                )
        except (OSError, sqlite3.Error) as exc:
            raise SessionStoreUnavailable("Pilot session store unavailable") from exc

    @classmethod
    def from_environment(cls) -> "PilotSessionStore":
        configured = os.getenv(SESSION_DB_ENV)
        path = Path(configured) if configured else Path.home() / ".medical_ai" / "pilot_sessions.sqlite3"
        return cls(path)

    def issue(
        self, session_id: str, participant_id: str, credential_id: str, *,
        expires_at: int, now: int,
    ) -> None:
        try:
            with closing(sqlite3.connect(self.path, timeout=5)) as db, db:
                # Expired records can be removed; active revocations remain durable.
                db.execute("DELETE FROM pilot_sessions WHERE expires_at <= ?", (now,))
                db.execute(
                    """INSERT INTO pilot_sessions
                    (session_id_digest, participant_id, credential_id, expires_at, revoked)
                    VALUES (?, ?, ?, ?, 0)""",
                    (_digest_session_id(session_id), participant_id, credential_id, expires_at),
                )
        except (OSError, sqlite3.Error) as exc:
            raise SessionStoreUnavailable("Pilot session store unavailable") from exc

    def is_active(
        self, session_id: str, participant_id: str, credential_id: str, *,
        expires_at: int, now: int,
    ) -> bool:
        try:
            with closing(sqlite3.connect(self.path, timeout=5)) as db:
                row = db.execute(
                    """SELECT participant_id, credential_id, expires_at, revoked
                       FROM pilot_sessions WHERE session_id_digest = ?""",
                    (_digest_session_id(session_id),),
                ).fetchone()
        except (OSError, sqlite3.Error) as exc:
            raise SessionStoreUnavailable("Pilot session store unavailable") from exc
        return bool(
            row is not None
            and row[0] == participant_id
            and row[1] == credential_id
            and row[2] == expires_at
            and row[2] > now
            and row[3] == 0
        )

    def revoke(self, session_id: str) -> bool:
        try:
            with closing(sqlite3.connect(self.path, timeout=5)) as db, db:
                result = db.execute(
                    "UPDATE pilot_sessions SET revoked = 1 WHERE session_id_digest = ? AND revoked = 0",
                    (_digest_session_id(session_id),),
                )
                return result.rowcount == 1
        except (OSError, sqlite3.Error) as exc:
            raise SessionStoreUnavailable("Pilot session store unavailable") from exc
