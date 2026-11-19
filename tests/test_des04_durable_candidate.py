"""DES-04 durable-controller adversarial regression candidate.

Synthetic fixtures only, with a fresh, explicit one-host database per pytest
case. Original tests/test_des04_revocation_red.py assertions remain untouched.
"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pytest

from medical_ai.influence import InfluenceController
from medical_ai.schemas import (
    DataPlane, DataPlaneTransition, DependencyDimension,
    EvidenceAuthorityState, InfluenceObjectType, InfluenceRequest,
    InfluenceSubject, InformationClass, InformationHandlingAuthorityState,
    InfluenceAuthorizationState,
)


def request(*, revision: int = 1, proposition: str = "synthetic:des04:output",
            dims: tuple[DependencyDimension, ...] | None = None) -> InfluenceRequest:
    subject = InfluenceSubject(
        object_id="synthetic:des04:durable",
        object_type=InfluenceObjectType.EVIDENCE_OBJECT,
        data_plane=DataPlane.EVIDENCE,
        evidence_authority=EvidenceAuthorityState.APPROVED,
        information_handling_authority=InformationHandlingAuthorityState.APPROVED,
        provenance_complete=True, validation_passed=True,
        safety_passed=True, monitoring_enabled=True,
        version="synthetic-no-medical-claim", revision=revision,
    )
    options = {} if dims is None else {"required_dependency_dimensions": dims}
    return InfluenceRequest(
        subject=subject, proposition_id=proposition,
        transition=DataPlaneTransition(
            source_plane=DataPlane.EVIDENCE, target_plane=DataPlane.EVIDENCE,
            information_class=InformationClass.PUBLIC,
        ), **options,
    )


def ledger_path() -> Path:
    return Path(os.environ["MEDICAL_AI_INFLUENCE_REVOCATION_DB"])


def test_des04_revoke_survives_two_fresh_controllers() -> None:
    initial = InfluenceController()
    assert initial.authorize(request()).allowed
    initial.revoke_authority("synthetic:des04:durable", DependencyDimension.EVIDENCE_AUTHORITY)
    for _ in range(2):
        restarted = InfluenceController()
        assert not restarted.authorize(request()).allowed


def test_des04_storage_loss_denies_instead_of_memory_fallback() -> None:
    controller = InfluenceController()
    first = controller.authorize(request())
    assert first.allowed
    ledger_path().unlink()
    assert not controller.authorize(request(proposition="synthetic:retry")).allowed
    assert first.authorization is not None
    assert controller.get_authorization(first.authorization.authorization_id).state == InfluenceAuthorizationState.REVOKED


def test_des04_damaged_sqlite_denies() -> None:
    controller = InfluenceController()
    assert controller.authorize(request()).allowed
    ledger_path().write_bytes(b"not a sqlite authority state")
    restarted = InfluenceController()
    assert not restarted.authorize(request()).allowed


def test_des04_modified_record_mac_denies() -> None:
    controller = InfluenceController()
    assert controller.authorize(request()).allowed
    with sqlite3.connect(ledger_path()) as db:
        db.execute("UPDATE authority_state SET evidence_revoked=1")
    assert not InfluenceController().authorize(request()).allowed


def test_des04_stale_policy_never_reauthorizes() -> None:
    assert InfluenceController().authorize(request()).allowed
    stale = InfluenceController()
    stale.policy_version = "replaced-and-unverified-policy-v999"
    assert not stale.authorize(request()).allowed


def test_des04_unrequested_higher_revision_denied() -> None:
    original = InfluenceController()
    assert original.authorize(request()).allowed
    assert not InfluenceController().authorize(request(revision=2)).allowed


def test_des04_revocation_cannot_be_cleared_by_higher_revision_flag() -> None:
    original = InfluenceController()
    assert original.authorize(request()).allowed
    original.revoke_authority("synthetic:des04:durable", DependencyDimension.EVIDENCE_AUTHORITY)
    subsequent = InfluenceController()
    subsequent.update_subject(request(revision=2).subject)
    assert not subsequent.authorize(request(revision=2)).allowed


def test_des04_selective_dependency_invalidation_is_preserved() -> None:
    evidence = DependencyDimension.EVIDENCE_AUTHORITY
    information = DependencyDimension.INFORMATION_HANDLING_AUTHORITY
    controller = InfluenceController()
    d1 = controller.authorize(request(proposition="synthetic:e", dims=(evidence,)))
    d2 = controller.authorize(request(proposition="synthetic:i", dims=(information,)))
    assert d1.authorization is not None and d2.authorization is not None
    result = controller.revoke_authority("synthetic:des04:durable", evidence)
    assert "synthetic:e" in result.invalidated_downstream_ids
    assert "synthetic:i" in result.unaffected_downstream_ids
    assert controller.get_authorization(d1.authorization.authorization_id).state == InfluenceAuthorizationState.REVOKED
    assert controller.get_authorization(d2.authorization.authorization_id).state == InfluenceAuthorizationState.ACTIVE


def test_des04_unconfigured_required_store_denies(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MEDICAL_AI_INFLUENCE_REVOCATION_DB")
    monkeypatch.delenv("MEDICAL_AI_INFLUENCE_REVOCATION_HMAC_KEY")
    assert not InfluenceController(require_durable=True).authorize(request()).allowed


def test_des04_adversarial_tombstone_row_deletion_never_reauthorizes() -> None:
    """Independent challenge: deleting a row must not recreate its authority."""
    controlling = InfluenceController()
    assert controlling.authorize(request()).allowed
    controlling.revoke_authority(
        "synthetic:des04:durable", DependencyDimension.EVIDENCE_AUTHORITY
    )
    with sqlite3.connect(ledger_path()) as db:
        db.execute("DELETE FROM authority_state")
    # If storage is internally self-consistent but a tombstone vanished,
    # re-enrollment from the previous APPROVED input must still be denied.
    assert not InfluenceController().authorize(request(proposition="synthetic:deleted-row")).allowed


def test_des04_adversarial_backup_rollback_never_reauthorizes() -> None:
    """Independent challenge: restored old DB bytes must not reset revocations."""
    controlling = InfluenceController()
    assert controlling.authorize(request()).allowed
    old_snapshot = ledger_path().with_name("synthetic_old_authority_backup.sqlite3")
    with sqlite3.connect(ledger_path()) as source:
        with sqlite3.connect(old_snapshot) as backup:
            source.backup(backup)
    controlling.revoke_authority(
        "synthetic:des04:durable", DependencyDimension.EVIDENCE_AUTHORITY
    )
    for suffix in ("-wal", "-shm"):
        ledger_path().with_name(ledger_path().name + suffix).unlink(missing_ok=True)
    os.replace(old_snapshot, ledger_path())
    assert not InfluenceController().authorize(
        request(proposition="synthetic:restored-pre-revocation-db")
    ).allowed
