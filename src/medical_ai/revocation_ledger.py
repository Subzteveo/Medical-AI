"""Single-host, shared SQLite deny-state for DES-04 (engineering candidate).

This ledger persists only keyed HMAC subject tokens, revisions and dimension-specific
tombstones, not approved subject snapshots, PHI, claims or medical content.
It deliberately cannot grant/reapprove medical influence. A separate independently
authorised issuer and rollback-resistant external high-watermark are NOT implemented.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import sqlite3
import stat
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .schemas import DependencyDimension


class DurableAuthorityUnavailable(RuntimeError):
    """Authority state cannot be safely consulted; medical influence must be denied."""


def _mac(key: bytes, *values: object) -> str:
    payload = json.dumps(values, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hmac.new(key, payload, hashlib.sha256).hexdigest()


class DurableRevocationSession:
    def __init__(self, db: sqlite3.Connection, key: bytes):
        self.db = db
        self.key = key

    def _token(self, object_id: str) -> str:
        return _mac(self.key, "subject", object_id)

    def _read(self, object_id: str) -> tuple[int, int, int, str] | None:
        token = self._token(object_id)
        row = self.db.execute(
            "SELECT revision, evidence_revoked, information_revoked, policy, row_mac "
            "FROM authority_state WHERE subject_token = ?", (token,),
        ).fetchone()
        if row is None:
            return None
        rev, er, ir, policy, signature = row
        if type(rev) is not int or type(er) is not int or type(ir) is not int:
            raise DurableAuthorityUnavailable("authority row type mismatch")
        if rev < 1 or er < 0 or ir < 0 or er > rev or ir > rev or not isinstance(policy, str):
            raise DurableAuthorityUnavailable("authority revision corrupt")
        if not hmac.compare_digest(str(signature), _mac(self.key, token, rev, er, ir, policy)):
            raise DurableAuthorityUnavailable("authority row integrity mismatch")
        return rev, er, ir, policy

    def _write(self, object_id: str, revision: int, er: int, ir: int, policy: str) -> None:
        token = self._token(object_id)
        self.db.execute(
            "INSERT INTO authority_state(subject_token, revision, evidence_revoked, "
            "information_revoked, policy, row_mac) VALUES(?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(subject_token) DO UPDATE SET "
            "revision=excluded.revision, evidence_revoked=excluded.evidence_revoked, "
            "information_revoked=excluded.information_revoked, policy=excluded.policy, "
            "row_mac=excluded.row_mac",
            (token, revision, er, ir, policy, _mac(self.key, token, revision, er, ir, policy)),
        )

    def admission(self, object_id: str, revision: int, policy: str) -> tuple[bool, bool, bool]:
        """Returns (stale_or_policy_mismatch, evidence_revoked, information_revoked).

        Admission and capability issuance are serialized with revocation by the
        caller's BEGIN IMMEDIATE transaction. A request cannot enroll a higher
        revision: only explicit update_subject may advance the watermark.
        """
        current = self._read(object_id)
        if current is None:
            self._write(object_id, revision, 0, 0, policy)
            return False, False, False
        stored, er, ir, stored_policy = current
        return revision != stored or policy != stored_policy, er != 0, ir != 0

    def check_active(\n        self, object_id: str, revision: int, policy: str,\n        dimensions: tuple[DependencyDimension, ...],\n    ) -> bool:
        current = self._read(object_id)
        return bool(
            current is not None and current[0] == revision and
            (current[1] == 0 or DependencyDimension.EVIDENCE_AUTHORITY not in dimensions) and\n            (current[2] == 0 or DependencyDimension.INFORMATION_HANDLING_AUTHORITY not in dimensions) and\n            current[3] == policy
        )

    def advance_revision(self, object_id: str, revision: int, policy: str) -> None:
        current = self._read(object_id)
        if current is None:
            # No historical state to bypass: a new subject needs independent
            # admission; this operation cannot create an approval.
            raise DurableAuthorityUnavailable("authority subject not enrolled")
        stored, er, ir, stored_policy = current
        if policy != stored_policy or revision <= stored:
            raise DurableAuthorityUnavailable("stale revision or changed authority policy")
        # A higher revision is NOT sufficient proof of legitimate reapproval.
        # Tombstones remain until an independently authorised grant protocol exists.
        self._write(object_id, revision, er, ir, policy)

    def revoke(self, object_id: str, dimension: DependencyDimension, policy: str) -> None:
        current = self._read(object_id)
        if current is None or current[3] != policy:
            raise DurableAuthorityUnavailable("authority subject or policy unavailable")
        rev, er, ir, _ = current
        if dimension == DependencyDimension.EVIDENCE_AUTHORITY:
            er = rev
        elif dimension == DependencyDimension.INFORMATION_HANDLING_AUTHORITY:
            ir = rev
        else:
            raise ValueError("only authority dimensions can be revoked")
        self._write(object_id, rev, er, ir, policy)


class DurableRevocationLedger:
    """SQLite transactions serialize controller operations on ONE shared host/path.

    Missing files, damaged bytes, bad keys and inaccessible storage raise; there
    is no automatic in-memory substitute. Provisioning is an explicit separate
    operation, never part of a controller's first request.
    """

    def __init__(self, path: str | Path, hmac_key: bytes):
        self.path = Path(path).expanduser().absolute()
        self.key = hmac_key
        if len(hmac_key) < 32:
            raise DurableAuthorityUnavailable("revocation HMAC key not configured")

    @classmethod
    def provision(cls, path: str | Path, hmac_key: bytes) -> "DurableRevocationLedger":
        """Explicit initialization for an approved operator or synthetic fixture."""
        instance = cls(path, hmac_key)
        instance.path.parent.mkdir(parents=True, exist_ok=True)
        if instance.path.is_symlink():
            raise DurableAuthorityUnavailable("symlink authority state forbidden")
        conn = sqlite3.connect(str(instance.path), timeout=3)
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=FULL")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS authority_state("
                "subject_token TEXT PRIMARY KEY, revision INTEGER NOT NULL, "
                "evidence_revoked INTEGER NOT NULL, information_revoked INTEGER NOT NULL, "
                "policy TEXT NOT NULL, row_mac TEXT NOT NULL)"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS authority_meta("
                "id INTEGER PRIMARY KEY CHECK(id = 1), version INTEGER NOT NULL, mac TEXT NOT NULL)"
            )
            marker = _mac(instance.key, "schema", 1)
            old = conn.execute("SELECT version, mac FROM authority_meta WHERE id=1").fetchone()
            if old is None:
                conn.execute("INSERT INTO authority_meta VALUES(1, 1, ?)", (marker,))
            elif old != (1, marker):
                raise DurableAuthorityUnavailable("authority schema/key mismatch")
            conn.commit()
        finally:
            conn.close()
        return instance

    @contextmanager
    def transaction(self) -> Iterator[DurableRevocationSession]:
        db: sqlite3.Connection | None = None
        try:
            st = os.lstat(self.path)
            if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1:
                raise DurableAuthorityUnavailable("authority path is not a regular private file")
            db = sqlite3.connect(f"file:{self.path}?mode=rw", uri=True, timeout=3)
            db.execute("PRAGMA busy_timeout=3000")
            db.execute("BEGIN IMMEDIATE")
            if db.execute("PRAGMA quick_check").fetchone() != ("ok",):
                raise DurableAuthorityUnavailable("authority database corrupt")
            marker = db.execute("SELECT version, mac FROM authority_meta WHERE id=1").fetchone()
            if marker != (1, _mac(self.key, "schema", 1)):
                raise DurableAuthorityUnavailable("authority schema/key mismatch")
            # Detect a missing table before any approval can be considered.
            db.execute("SELECT subject_token FROM authority_state LIMIT 0")
            yield DurableRevocationSession(db, self.key)
            db.commit()
        except (OSError, sqlite3.Error, DurableAuthorityUnavailable) as exc:
            if db is not None:
                db.rollback()
            raise DurableAuthorityUnavailable("durable authority state unavailable") from exc
        except BaseException:
            if db is not None:
                db.rollback()
            raise
        finally:
            if db is not None:
                db.close()
