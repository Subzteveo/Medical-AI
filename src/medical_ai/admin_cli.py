"""Console entry point: ``medical-ai-admin``.

Issues, revokes and rotates pilot invitations in an owner-only allowlist file (the
file named by ``MEDICAL_AI_PILOT_ACCESS_FILE`` on the server). The raw invite token
is printed once on standard output and is never written to disk, to standard error
or into an error message; only its SHA-256 digest is stored.
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
from collections.abc import Sequence
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from .access import (
    AccessConfigurationError,
    PilotParticipant,
    parse_access_document,
    parse_access_json,
    parse_expiry,
    read_access_file,
    token_digest,
)

PROG = "medical-ai-admin"
MAX_TTL_DAYS = 3650
_SOURCE = "allowlist file"


class AdminError(RuntimeError):
    """An operator-facing failure. Messages never contain a token."""


def _load(path: str, *, missing_ok: bool = False) -> list[PilotParticipant]:
    # lexists, not exists: a dangling symlink must be refused, not written through.
    if not os.path.lexists(path):
        if missing_ok:
            return []
        raise AdminError("allowlist file does not exist")
    try:
        return list(parse_access_json(read_access_file(path), source=_SOURCE))
    except AccessConfigurationError as exc:
        raise AdminError(_describe(exc)) from exc


def _describe(exc: AccessConfigurationError) -> str:
    # access.py names the server environment variable; the operator supplied a path.
    return str(exc).replace("MEDICAL_AI_PILOT_ACCESS_FILE", _SOURCE)


def _serialise(participants: Sequence[PilotParticipant]) -> str:
    document = {
        "participants": [
            {
                "participant_id": item.participant_id,
                "credential_id": item.credential_id,
                "token_sha256": item.token_sha256,
                "expires_at": item.expires_at.isoformat(),
                "revoked": item.revoked,
            }
            for item in participants
        ]
    }
    return json.dumps(document, indent=2) + "\n"


def _save(path: str, participants: Sequence[PilotParticipant]) -> None:
    """Validate, then replace the allowlist atomically with an owner-only file."""

    text = _serialise(participants)
    try:
        parse_access_document(json.loads(text), source=_SOURCE)
    except AccessConfigurationError as exc:
        raise AdminError(_describe(exc)) from exc

    directory = os.path.dirname(os.path.abspath(path))
    temporary = os.path.join(directory, f".{os.path.basename(path)}.{secrets.token_hex(8)}.tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(temporary, flags, 0o600)
    except OSError as exc:
        raise AdminError("allowlist directory is not writable") from exc
    try:
        try:
            os.write(fd, text.encode("utf-8"))
            os.fsync(fd)
        finally:
            os.close(fd)
        os.replace(temporary, path)
    except OSError as exc:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise AdminError("allowlist file could not be written") from exc


def _expiry_from(args: argparse.Namespace) -> datetime | None:
    expires_at: str | None = args.expires_at
    ttl_days: int | None = args.ttl_days
    if expires_at is not None:
        try:
            return parse_expiry(expires_at)
        except AccessConfigurationError as exc:
            raise AdminError(str(exc).replace("participant expires_at", "--expires-at")) from exc
    if ttl_days is not None:
        if ttl_days < 1 or ttl_days > MAX_TTL_DAYS:
            raise AdminError(f"--ttl-days must be between 1 and {MAX_TTL_DAYS}")
        return datetime.now(timezone.utc) + timedelta(days=ttl_days)
    return None


def _announce(token: str, participant: PilotParticipant) -> None:
    summary = {
        "participant_id": participant.participant_id,
        "credential_id": participant.credential_id,
        "expires_at": participant.expires_at.isoformat(),
        "token_sha256": participant.token_sha256,
    }
    print(json.dumps(summary, sort_keys=True), file=sys.stderr)
    # The only place the raw token is ever emitted.
    print(token)


def _find(participants: Sequence[PilotParticipant], participant_id: str) -> int:
    for index, item in enumerate(participants):
        if item.participant_id == participant_id:
            return index
    raise AdminError("no participant with that participant-id")


def _cmd_invite(args: argparse.Namespace) -> int:
    expires_at = _expiry_from(args)
    if expires_at is None:
        raise AdminError("one of --expires-at or --ttl-days is required")
    participants = _load(args.allowlist, missing_ok=True)
    token = secrets.token_urlsafe(32)
    participant = PilotParticipant(
        participant_id=args.participant_id,
        credential_id=args.credential_id,
        token_sha256=token_digest(token),
        expires_at=expires_at,
        revoked=False,
    )
    _save(args.allowlist, [*participants, participant])
    _announce(token, participant)
    return 0


def _cmd_revoke(args: argparse.Namespace) -> int:
    participants = _load(args.allowlist)
    index = _find(participants, args.participant_id)
    participants[index] = replace(participants[index], revoked=True)
    _save(args.allowlist, participants)
    print(f"revoked {participants[index].participant_id}", file=sys.stderr)
    return 0


def _cmd_rotate(args: argparse.Namespace) -> int:
    participants = _load(args.allowlist)
    index = _find(participants, args.participant_id)
    current = participants[index]
    if args.credential_id == current.credential_id:
        # Existing sessions are bound to the credential id; reusing it would keep them alive.
        raise AdminError("--credential-id must differ from the current credential id")
    token = secrets.token_urlsafe(32)
    rotated = replace(
        current,
        credential_id=args.credential_id,
        token_sha256=token_digest(token),
        expires_at=_expiry_from(args) or current.expires_at,
        revoked=False,
    )
    participants[index] = rotated
    _save(args.allowlist, participants)
    _announce(token, rotated)
    return 0


def _cmd_list(args: argparse.Namespace) -> int:
    participants = _load(args.allowlist)
    now = datetime.now(timezone.utc)
    print("participant_id\tcredential_id\texpires_at\tstate\tdigest_prefix")
    for item in participants:
        state = "revoked" if item.revoked else ("expired" if item.expires_at <= now else "active")
        print(
            f"{item.participant_id}\t{item.credential_id}\t{item.expires_at.isoformat()}"
            f"\t{state}\t{item.token_sha256[:8]}"
        )
    return 0


def _cmd_check(args: argparse.Namespace) -> int:
    count = len(_load(args.allowlist))
    print(f"allowlist is valid: {count} participant(s)", file=sys.stderr)
    return 0


def _add_expiry(parser: argparse.ArgumentParser, *, required: bool) -> None:
    group = parser.add_mutually_exclusive_group(required=required)
    group.add_argument("--expires-at", help="ISO-8601 timestamp with a timezone offset")
    group.add_argument("--ttl-days", type=int, help=f"days from now (1-{MAX_TTL_DAYS})")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROG, description="Manage the Medical AI pilot invitation allowlist file."
    )
    commands = parser.add_subparsers(dest="command", required=True)

    def command(name: str, summary: str) -> argparse.ArgumentParser:
        sub = commands.add_parser(name, help=summary, description=summary)
        sub.add_argument("--allowlist", required=True, help="path to the allowlist JSON file")
        return sub

    invite = command("invite", "Add a participant and print a new invite token once.")
    invite.add_argument("--participant-id", required=True)
    invite.add_argument("--credential-id", required=True)
    _add_expiry(invite, required=True)
    invite.set_defaults(handler=_cmd_invite)

    revoke = command("revoke", "Mark a participant revoked.")
    revoke.add_argument("--participant-id", required=True)
    revoke.set_defaults(handler=_cmd_revoke)

    rotate = command("rotate", "Replace a participant's credential and print the new token once.")
    rotate.add_argument("--participant-id", required=True)
    rotate.add_argument("--credential-id", required=True, help="new credential id")
    _add_expiry(rotate, required=False)
    rotate.set_defaults(handler=_cmd_rotate)

    command("list", "List participants without tokens or full digests.").set_defaults(
        handler=_cmd_list
    )
    command("check", "Validate the allowlist file.").set_defaults(handler=_cmd_check)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = _parser().parse_args(list(argv) if argv is not None else None)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2
    try:
        handler = args.handler
        return int(handler(args))
    except AdminError as exc:
        print(f"{PROG}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
