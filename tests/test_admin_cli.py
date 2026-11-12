from __future__ import annotations

import hashlib
import json
import stat
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

import medical_ai.api as api
from medical_ai import admin_cli
from medical_ai.access import authenticate_invite_token, load_access_config
from medical_ai.engine import EvidenceEngine

SESSION_SECRET = "session-secret-" + ("S" * 40)
FUTURE = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()


@pytest.fixture
def allowlist(tmp_path, monkeypatch):
    path = tmp_path / "allowlist.json"
    monkeypatch.delenv("MEDICAL_AI_PILOT_ACCESS_JSON", raising=False)
    monkeypatch.setenv("MEDICAL_AI_PILOT_ACCESS_FILE", str(path))
    monkeypatch.setenv("MEDICAL_AI_PILOT_SESSION_SECRET", SESSION_SECRET)
    monkeypatch.setenv("MEDICAL_AI_PILOT_COOKIE_SECURE", "false")
    return path


def run(capsys, *argv: str) -> tuple[int, str, str]:
    code = admin_cli.main(list(argv))
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def invite(capsys, allowlist, participant="pilot-001", credential="cred-001", *extra: str) -> str:
    expiry = extra or ("--ttl-days", "30")
    code, out, _ = run(
        capsys, "invite", "--allowlist", str(allowlist),
        "--participant-id", participant, "--credential-id", credential, *expiry,
    )
    assert code == 0
    return out.strip()


def mode(path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


def authenticates(token: str) -> bool:
    return authenticate_invite_token(token, load_access_config()) is not None


def test_invite_prints_token_once_on_stdout_only(capsys, allowlist):
    code, out, err = run(
        capsys, "invite", "--allowlist", str(allowlist),
        "--participant-id", "pilot-001", "--credential-id", "cred-001", "--ttl-days", "30",
    )
    assert code == 0
    token = out.strip()
    assert out == token + "\n"
    assert len(token) >= 40
    assert token not in err
    assert token not in allowlist.read_text(encoding="utf-8")
    summary = json.loads(err)
    assert summary["participant_id"] == "pilot-001"
    assert summary["credential_id"] == "cred-001"
    assert summary["token_sha256"] == hashlib.sha256(token.encode()).hexdigest()
    assert set(summary) == {"participant_id", "credential_id", "expires_at", "token_sha256"}


def test_invite_creates_owner_only_file_and_token_authenticates(capsys, allowlist):
    token = invite(capsys, allowlist)
    assert mode(allowlist) == 0o600
    assert authenticates(token)
    document = json.loads(allowlist.read_text(encoding="utf-8"))
    assert set(document) == {"participants"}
    assert document["participants"][0]["revoked"] is False


def test_invited_token_works_through_the_api(capsys, allowlist, monkeypatch, fake_connector):
    token = invite(capsys, allowlist)
    monkeypatch.setattr(api, "build_engine", lambda: EvidenceEngine(fake_connector))
    response = TestClient(api.app).post(
        "/v1/evidence/query",
        json={"question": "What evidence exists for exercise reducing blood pressure?"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200


def test_second_invite_appends_and_keeps_first(capsys, allowlist):
    first = invite(capsys, allowlist, "pilot-001", "cred-001")
    second = invite(capsys, allowlist, "pilot-002", "cred-002")
    assert first != second
    assert authenticates(first) and authenticates(second)
    assert mode(allowlist) == 0o600


def test_explicit_expiry_is_recorded(capsys, allowlist):
    invite(capsys, allowlist, "pilot-001", "cred-001", "--expires-at", FUTURE)
    stored = json.loads(allowlist.read_text(encoding="utf-8"))["participants"][0]["expires_at"]
    assert datetime.fromisoformat(stored) == datetime.fromisoformat(FUTURE)


@pytest.mark.parametrize("expiry", [
    ("--expires-at", "2027-01-01T00:00:00"),      # no timezone offset
    ("--expires-at", "next tuesday"),
    ("--ttl-days", "0"),
    ("--ttl-days", "-3"),
    ("--ttl-days", "100000"),
])
def test_invalid_expiry_is_rejected_and_file_not_created(capsys, allowlist, expiry):
    code, out, _ = run(
        capsys, "invite", "--allowlist", str(allowlist),
        "--participant-id", "pilot-001", "--credential-id", "cred-001", *expiry,
    )
    assert code != 0
    assert out == ""
    assert not allowlist.exists()


@pytest.mark.parametrize("participant,credential", [
    ("pilot-001", "cred-999"),     # duplicate participant
    ("pilot-999", "cred-001"),     # duplicate credential
    ("bad id with spaces", "cred-999"),
])
def test_conflicting_or_malformed_ids_leave_file_unchanged(capsys, allowlist, participant, credential):
    invite(capsys, allowlist)
    before = allowlist.read_bytes()
    code, out, err = run(
        capsys, "invite", "--allowlist", str(allowlist),
        "--participant-id", participant, "--credential-id", credential, "--ttl-days", "30",
    )
    assert code == 1
    assert out == ""
    assert err.startswith("medical-ai-admin:")
    assert allowlist.read_bytes() == before


def test_revoke_blocks_the_token_without_restart(capsys, allowlist):
    token = invite(capsys, allowlist)
    assert authenticates(token)
    code, out, _ = run(capsys, "revoke", "--allowlist", str(allowlist), "--participant-id", "pilot-001")
    assert code == 0 and out == ""
    assert not authenticates(token)
    assert mode(allowlist) == 0o600
    # Idempotent.
    assert run(capsys, "revoke", "--allowlist", str(allowlist), "--participant-id", "pilot-001")[0] == 0


def test_revoke_unknown_participant_exits_one(capsys, allowlist):
    invite(capsys, allowlist)
    before = allowlist.read_bytes()
    code, _, err = run(capsys, "revoke", "--allowlist", str(allowlist), "--participant-id", "nobody")
    assert code == 1
    assert "nobody" not in err or err.startswith("medical-ai-admin:")
    assert allowlist.read_bytes() == before


def test_rotate_invalidates_old_token_and_accepts_new(capsys, allowlist):
    old = invite(capsys, allowlist)
    code, out, err = run(
        capsys, "rotate", "--allowlist", str(allowlist),
        "--participant-id", "pilot-001", "--credential-id", "cred-002",
    )
    assert code == 0
    new = out.strip()
    assert new and new != old
    assert new not in err and new not in allowlist.read_text(encoding="utf-8")
    assert not authenticates(old)
    assert authenticates(new)
    entry = json.loads(allowlist.read_text(encoding="utf-8"))["participants"][0]
    assert entry["credential_id"] == "cred-002"
    assert mode(allowlist) == 0o600


def test_rotate_restores_a_revoked_participant_and_keeps_expiry(capsys, allowlist):
    invite(capsys, allowlist, "pilot-001", "cred-001", "--expires-at", FUTURE)
    run(capsys, "revoke", "--allowlist", str(allowlist), "--participant-id", "pilot-001")
    code, out, _ = run(
        capsys, "rotate", "--allowlist", str(allowlist),
        "--participant-id", "pilot-001", "--credential-id", "cred-002",
    )
    assert code == 0
    assert authenticates(out.strip())
    stored = json.loads(allowlist.read_text(encoding="utf-8"))["participants"][0]["expires_at"]
    assert datetime.fromisoformat(stored) == datetime.fromisoformat(FUTURE)


def test_rotate_requires_a_new_credential_id(capsys, allowlist):
    old = invite(capsys, allowlist)
    before = allowlist.read_bytes()
    code, out, _ = run(
        capsys, "rotate", "--allowlist", str(allowlist),
        "--participant-id", "pilot-001", "--credential-id", "cred-001",
    )
    assert code == 1 and out == ""
    assert allowlist.read_bytes() == before
    assert authenticates(old)


def test_rotate_unknown_participant_exits_one(capsys, allowlist):
    invite(capsys, allowlist)
    code, out, _ = run(
        capsys, "rotate", "--allowlist", str(allowlist),
        "--participant-id", "nobody", "--credential-id", "cred-002",
    )
    assert code == 1 and out == ""


def test_list_shows_no_token_and_no_full_digest(capsys, allowlist):
    token = invite(capsys, allowlist)
    digest = hashlib.sha256(token.encode()).hexdigest()
    code, out, _ = run(capsys, "list", "--allowlist", str(allowlist))
    assert code == 0
    assert "pilot-001" in out and "cred-001" in out
    assert digest[:8] in out
    assert digest not in out
    assert token not in out


def test_check_exit_codes(capsys, allowlist):
    assert run(capsys, "check", "--allowlist", str(allowlist))[0] == 1   # missing file
    invite(capsys, allowlist)
    assert run(capsys, "check", "--allowlist", str(allowlist))[0] == 0
    allowlist.write_text("{not json", encoding="utf-8")
    assert run(capsys, "check", "--allowlist", str(allowlist))[0] == 1


def test_symlinked_allowlist_is_refused(capsys, allowlist, tmp_path):
    invite(capsys, allowlist)
    link = tmp_path / "link.json"
    link.symlink_to(allowlist)
    before = allowlist.read_bytes()
    for argv in (
        ("check", "--allowlist", str(link)),
        ("list", "--allowlist", str(link)),
        ("revoke", "--allowlist", str(link), "--participant-id", "pilot-001"),
        ("invite", "--allowlist", str(link), "--participant-id", "pilot-002",
         "--credential-id", "cred-002", "--ttl-days", "1"),
    ):
        code, out, _ = run(capsys, *argv)
        assert code == 1 and out == ""
    assert link.is_symlink()
    assert allowlist.read_bytes() == before


def test_dangling_symlink_is_not_written_through(capsys, tmp_path):
    target = tmp_path / "elsewhere.json"
    link = tmp_path / "link.json"
    link.symlink_to(target)
    code, out, _ = run(
        capsys, "invite", "--allowlist", str(link),
        "--participant-id", "pilot-001", "--credential-id", "cred-001", "--ttl-days", "1",
    )
    assert code == 1 and out == ""
    assert not target.exists()


def test_group_readable_allowlist_is_refused(capsys, allowlist):
    invite(capsys, allowlist)
    allowlist.chmod(0o640)
    code, out, _ = run(capsys, "revoke", "--allowlist", str(allowlist), "--participant-id", "pilot-001")
    assert code == 1 and out == ""


def test_missing_parent_directory_fails_cleanly(capsys, tmp_path):
    code, out, err = run(
        capsys, "invite", "--allowlist", str(tmp_path / "absent" / "allowlist.json"),
        "--participant-id", "pilot-001", "--credential-id", "cred-001", "--ttl-days", "1",
    )
    assert code == 1 and out == ""
    assert err.startswith("medical-ai-admin:")


def test_no_temporary_files_are_left_behind(capsys, allowlist):
    invite(capsys, allowlist)
    run(capsys, "revoke", "--allowlist", str(allowlist), "--participant-id", "pilot-001")
    assert sorted(p.name for p in allowlist.parent.iterdir()) == ["allowlist.json"]


def test_allowlist_argument_is_required(capsys):
    assert run(capsys, "list")[0] == 2
    assert run(capsys)[0] == 2
