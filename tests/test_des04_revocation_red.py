"""DES-04 synthetic RED acceptance cases (issue #53).

This file intentionally contains failing safety requirements on the original
controller. It is a test-only, isolated branch. No PHI, clinical advice, live
connector access, migration, deployment, or release authorization.

A source-approved InfluenceSubject fixture is deliberately replayed unchanged.
These tests exercise controller revocation continuity; they DO NOT establish
an end-to-end medical output exploit or bypass of AuthorityResolver.

Run: python -m pytest -q tests/test_des04_revocation_red.py
"""
from __future__ import annotations

import multiprocessing

import pytest

from medical_ai.influence import InfluenceController
from medical_ai.schemas import (
    DataPlane,
    DataPlaneTransition,
    DependencyDimension,
    EvidenceAuthorityState,
    InfluenceObjectType,
    InfluenceRequest,
    InfluenceSubject,
    InformationClass,
    InformationHandlingAuthorityState,
)


def _approved_subject(*, revision: int = 1) -> InfluenceSubject:
    return InfluenceSubject(
        object_id="synthetic:des04:evidence",
        object_type=InfluenceObjectType.EVIDENCE_OBJECT,
        data_plane=DataPlane.EVIDENCE,
        evidence_authority=EvidenceAuthorityState.APPROVED,
        information_handling_authority=InformationHandlingAuthorityState.APPROVED,
        provenance_complete=True,
        validation_passed=True,
        safety_passed=True,
        monitoring_enabled=True,
        version="des04-synthetic-only",
        revision=revision,
    )


def _request(*, revision: int = 1, downstream: str = "synthetic:des04:claim") -> InfluenceRequest:
    return InfluenceRequest(
        subject=_approved_subject(revision=revision),
        proposition_id=downstream,
        transition=DataPlaneTransition(
            source_plane=DataPlane.EVIDENCE,
            target_plane=DataPlane.EVIDENCE,
            information_class=InformationClass.PUBLIC,
        ),
    )


def _fresh_process_authorize(out_queue: multiprocessing.Queue) -> None:
    controller = InfluenceController()
    decision = controller.authorize(_request(downstream="synthetic:after-restart"))
    out_queue.put(decision.allowed)


def _preexisting_worker_authorize(
    out_queue: multiprocessing.Queue,
    ready: multiprocessing.Event,
    resume: multiprocessing.Event,
) -> None:
    controller = InfluenceController()
    first = controller.authorize(_request(downstream="synthetic:worker-before"))
    out_queue.put(("before", first.allowed))
    ready.set()
    if not resume.wait(timeout=25):
        out_queue.put(("error", "release-timeout"))
        return
    second = controller.authorize(_request(downstream="synthetic:worker-after"))
    out_queue.put(("after", second.allowed))


def test_control_initial_approval_and_local_revocation() -> None:
    controller = InfluenceController()
    first = controller.authorize(_request())
    assert first.allowed is True
    assert first.authorization is not None
    controller.revoke_authority(
        _approved_subject().object_id, DependencyDimension.EVIDENCE_AUTHORITY
    )
    stale = controller.authorize(_request(downstream="synthetic:local-stale"))
    assert stale.allowed is False
    assert "EVIDENCE_AUTHORITY_REVOKED" in stale.reasons


def test_control_old_capability_not_registered_in_fresh_controller() -> None:
    original = InfluenceController()
    allowed = original.authorize(_request())
    assert allowed.authorization is not None
    fresh = InfluenceController()
    assert fresh.get_authorization(allowed.authorization.authorization_id) is None


def test_control_unknown_authority_denied() -> None:
    req = _request()
    req.subject.evidence_authority = EvidenceAuthorityState.UNKNOWN
    assert InfluenceController().authorize(req).allowed is False


@pytest.mark.parametrize(
    "dimension",
    [
        DependencyDimension.EVIDENCE_AUTHORITY,
        DependencyDimension.INFORMATION_HANDLING_AUTHORITY,
    ],
)
def test_red_revocation_survives_new_controller_same_revision(
    dimension: DependencyDimension,
) -> None:
    original = InfluenceController()
    assert original.authorize(_request()).allowed is True
    original.revoke_authority(_approved_subject().object_id, dimension)

    # After a restart, a previously approved snapshot must NOT mint a new
    # authorization in the absence of durable revision-bound revocation.
    restarted = InfluenceController()
    stale = restarted.authorize(_request(downstream="synthetic:replayed"))
    assert stale.allowed is False, (
        "DES-04 RED: fresh controller minted ALLOW from a pre-revocation "
        "same-revision approved subject"
    )


def test_red_restarted_worker_process_rejects_stale_approval() -> None:
    original = InfluenceController()
    assert original.authorize(_request()).allowed is True
    original.revoke_authority(
        _approved_subject().object_id, DependencyDimension.EVIDENCE_AUTHORITY
    )

    context = multiprocessing.get_context("spawn")
    out_queue = context.Queue()
    worker = context.Process(target=_fresh_process_authorize, args=(out_queue,))
    worker.start()
    try:
        observed_allow = out_queue.get(timeout=25)
        worker.join(timeout=20)
        assert worker.exitcode == 0
        assert observed_allow is False, (
            "DES-04 RED: separately started process accepted stale approval"
        )
    finally:
        if worker.is_alive():
            worker.terminate()
            worker.join(timeout=5)
        out_queue.close()


def test_red_other_live_worker_observes_revocation() -> None:
    context = multiprocessing.get_context("spawn")
    out_queue = context.Queue()
    ready = context.Event()
    resume = context.Event()
    worker = context.Process(
        target=_preexisting_worker_authorize,
        args=(out_queue, ready, resume),
    )
    worker.start()
    try:
        assert ready.wait(timeout=25), "worker never established baseline"
        assert out_queue.get(timeout=10) == ("before", True)

        controlling_worker = InfluenceController()
        assert controlling_worker.authorize(_request()).allowed is True
        controlling_worker.revoke_authority(
            _approved_subject().object_id, DependencyDimension.EVIDENCE_AUTHORITY
        )
        resume.set()

        assert out_queue.get(timeout=20) == ("after", False), (
            "DES-04 RED: already-live worker continued to allow after "
            "another controller revoked the same subject"
        )
        worker.join(timeout=10)
        assert worker.exitcode == 0
    finally:
        resume.set()
        if worker.is_alive():
            worker.terminate()
            worker.join(timeout=5)
        out_queue.close()


def test_red_restart_cannot_reset_authoritative_revision_watermark() -> None:
    original = InfluenceController()
    assert original.authorize(_request()).allowed is True
    original.revoke_authority(
        _approved_subject().object_id, DependencyDimension.EVIDENCE_AUTHORITY
    )

    restarted = InfluenceController()
    restarted.update_subject(_approved_subject(revision=1))
    assert restarted.authorize(_request(downstream="synthetic:watermark")).allowed is False, (
        "DES-04 RED: new controller accepted replay of the revoked revision"
    )
