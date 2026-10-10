"""Controlled, synthetic adversarial regressions for PR #21.

Boundary: untrusted runtime objects may not mint or revive user-visible medical
claim influence. All records below are inert fixture data, never patient data.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from medical_ai.influence import InfluenceController
from medical_ai.schemas import (
    AuthorizedClaimView,
    ClaimRecord,
    ConsequenceLevel,
    DataPlane,
    DataPlaneTransition,
    DependencyDimension,
    EvidenceAuthorityState,
    InfluenceAuthorization,
    InfluenceAuthorizationState,
    InfluenceDecision,
    InfluenceObjectType,
    InfluenceRequest,
    InfluenceSubject,
    InformationClass,
    InformationHandlingAuthorityState,
    VerificationStatus,
)
from medical_ai.renderer import render_answer


def _claim(text: str = "Synthetic proposition A.") -> ClaimRecord:
    return ClaimRecord(
        claim_id="claim:adversarial",
        claim_text=text,
        consequence_level=ConsequenceLevel.MODERATE,
        evidence_ids=["evidence:fixture"],
        source_ids=["source:fixture"],
        verification_status=VerificationStatus.PASS,
    )


def _request() -> InfluenceRequest:
    return InfluenceRequest(
        subject=InfluenceSubject(
            object_id="claim:adversarial",
            object_type=InfluenceObjectType.CLAIM_RECORD,
            data_plane=DataPlane.EVIDENCE,
            evidence_authority=EvidenceAuthorityState.APPROVED,
            information_handling_authority=InformationHandlingAuthorityState.APPROVED,
            provenance_complete=True,
            validation_passed=True,
            safety_passed=True,
            monitoring_enabled=True,
            version="fixture-v1",
        ),
        proposition_id="user-output:claim:adversarial",
        transition=DataPlaneTransition(
            source_plane=DataPlane.EVIDENCE,
            target_plane=DataPlane.EVIDENCE,
            information_class=InformationClass.PUBLIC,
        ),
    )


def test_forged_active_view_cannot_render_medical_proposition() -> None:
    forged = InfluenceAuthorization(
        decision_id="forged",
        object_id="claim:adversarial",
        proposition_id="user-output:claim:adversarial",
        state=InfluenceAuthorizationState.ACTIVE,
        required_dependency_dimensions=[DependencyDimension.EVIDENCE_AUTHORITY],
    )
    view = AuthorizedClaimView(claim=_claim(), authorization=forged)
    with pytest.raises((ValueError, TypeError)):
        render_answer([view], [])


def test_caller_cannot_reactivate_revoked_authorization() -> None:
    controller = InfluenceController()
    decision = controller.authorize(_request())
    authorization = decision.authorization
    assert authorization is not None
    controller.revoke_authority("claim:adversarial", DependencyDimension.EVIDENCE_AUTHORITY)
    with pytest.raises((ValidationError, AttributeError, TypeError)):
        authorization.state = InfluenceAuthorizationState.ACTIVE


def test_authorized_claim_id_cannot_be_reused_for_changed_text() -> None:
    controller = InfluenceController()
    decision = controller.authorize(_request(), claim=_claim())
    controller.build_authorized_claim_view(_claim(), decision)
    with pytest.raises(ValueError, match="snapshot|digest|claim"):
        controller.build_authorized_claim_view(_claim("Different synthetic proposition B."), decision)


def test_revoked_copy_cannot_be_replayed_for_rendering() -> None:
    controller = InfluenceController()
    decision = controller.authorize(_request(), claim=_claim())
    view = controller.build_authorized_claim_view(_claim(), decision)
    copied = AuthorizedClaimView.model_validate_json(view.model_dump_json())
    controller.revoke_authority("claim:adversarial", DependencyDimension.EVIDENCE_AUTHORITY)
    with pytest.raises(ValueError, match="revoked|active|registered|current"):
        render_answer([copied], [], influence_controller=controller)


def test_higher_revision_weakened_authority_revokes_capabilities() -> None:
    controller = InfluenceController()
    decision = controller.authorize(_request())
    auth = decision.authorization
    assert auth is not None
    weakened = _request().subject.model_copy(
        update={"revision": 2, "evidence_authority": EvidenceAuthorityState.DENIED}
    )
    controller.update_subject(weakened)
    registered = controller.get_authorization(auth.authorization_id)
    assert registered is not None
    assert registered.state == InfluenceAuthorizationState.REVOKED


def test_revoked_decision_remains_serializable_audit_evidence() -> None:
    controller = InfluenceController()
    decision = controller.authorize(_request())
    controller.revoke_authority("claim:adversarial", DependencyDimension.EVIDENCE_AUTHORITY)
    restored = InfluenceDecision.model_validate_json(decision.model_dump_json())
    assert restored.decision_id == decision.decision_id
    assert restored.status == decision.status


def test_api_requests_share_authoritative_controller_state() -> None:
    from medical_ai.api import build_engine

    first = build_engine().influence_controller
    second = build_engine().influence_controller
    assert first is second


def test_boundary_guard_rejects_qualified_any(tmp_path, monkeypatch) -> None:
    from scripts import verify_influence_boundary as guard

    file_path = tmp_path / "qualified_any.py"
    file_path.write_text("import typing as t\nunsafe: t.Any = None\n", encoding="utf-8")
    monkeypatch.setattr(guard, "AUTHORITATIVE_FILES", (*guard.AUTHORITATIVE_FILES, file_path))
    assert guard.main() == 1


@pytest.mark.parametrize("expression", [
    "AuthorizedClaimView.model_construct()",
    "InfluenceAuthorization.model_validate({})",
    "Alias()",
])
def test_boundary_guard_rejects_indirect_capability_creation(
    tmp_path, monkeypatch, expression: str
) -> None:
    from scripts import verify_influence_boundary as guard

    source = (
        "from medical_ai.schemas import AuthorizedClaimView, InfluenceAuthorization\n"
        "Alias = AuthorizedClaimView\n"
        f"{expression}\n"
    )
    runtime = tmp_path / "src" / "medical_ai"
    runtime.mkdir(parents=True)
    (runtime / "escape.py").write_text(source, encoding="utf-8")
    monkeypatch.setattr(guard, "RUNTIME_ROOT", runtime)
    assert guard.main() == 1
