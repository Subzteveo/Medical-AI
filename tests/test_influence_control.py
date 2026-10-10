import pytest

from medical_ai.influence import InfluenceController
from medical_ai.schemas import (
    DataPlane,
    EvidenceAuthorityState,
    DataPlaneTransition,
    DependencyDimension,
    InfluenceObjectType,
    InfluenceRequest,
    InfluenceSubject,
    InformationClass,
    InformationHandlingAuthorityState,
)


def subject(
    object_id="evidence:1",
    *,
    plane=DataPlane.EVIDENCE,
    evidence=EvidenceAuthorityState.APPROVED,
    information=InformationHandlingAuthorityState.APPROVED,
    provenance=True,
    validation=True,
    safety=True,
    monitoring=True,
    revision=1,
):
    return InfluenceSubject(
        object_id=object_id,
        object_type=InfluenceObjectType.EVIDENCE_OBJECT,
        data_plane=plane,
        evidence_authority=evidence,
        information_handling_authority=information,
        provenance_complete=provenance,
        validation_passed=validation,
        safety_passed=safety,
        monitoring_enabled=monitoring,
        version="fixture-v1",
        revision=revision,
    )


def request(subj, downstream="claim:1", *, target=DataPlane.EVIDENCE, info=InformationClass.PUBLIC, deps=None):
    kwargs = {}
    if deps is not None:
        kwargs["required_dependency_dimensions"] = deps
    return InfluenceRequest(
        subject=subj,
        proposition_id=downstream,
        transition=DataPlaneTransition(
            source_plane=subj.data_plane,
            target_plane=target,
            information_class=info,
        ),
        **kwargs,
    )


def test_authorized_evidence_object_gets_inspectable_allow_decision():
    controller = InfluenceController()
    decision = controller.authorize(request(subject()))
    assert decision.allowed is True
    assert decision.policy_version == controller.policy_version
    assert decision.evaluated_dimensions["evidence_authority"] == "APPROVED"
    assert decision.evaluated_dimensions["information_handling_authority"] == "APPROVED"
    assert controller.get_downstream_state("claim:1").active is True


def test_evidence_approval_does_not_grant_information_handling_authority():
    controller = InfluenceController()
    decision = controller.authorize(request(subject(information=InformationHandlingAuthorityState.DENIED), info=InformationClass.PHI))
    assert decision.allowed is False
    assert "INFORMATION_HANDLING_AUTHORITY_DENIED" in decision.reasons


def test_information_handling_approval_does_not_grant_evidence_authority():
    controller = InfluenceController()
    decision = controller.authorize(request(subject(evidence=EvidenceAuthorityState.DENIED)))
    assert decision.allowed is False
    assert "EVIDENCE_AUTHORITY_DENIED" in decision.reasons


def test_unknown_authority_and_information_class_fail_closed():
    controller = InfluenceController()
    subj = subject(evidence=EvidenceAuthorityState.UNKNOWN, information=InformationHandlingAuthorityState.UNKNOWN)
    decision = controller.authorize(request(subj, info=InformationClass.UNKNOWN))
    assert decision.allowed is False
    assert "EVIDENCE_AUTHORITY_UNKNOWN" in decision.reasons
    assert "INFORMATION_HANDLING_AUTHORITY_UNKNOWN" in decision.reasons
    assert "INFORMATION_CLASS_UNKNOWN" in decision.reasons


def test_clinical_and_research_planes_cannot_directly_establish_evidence():
    for plane in (DataPlane.CLINICAL, DataPlane.RESEARCH):
        controller = InfluenceController()
        decision = controller.authorize(request(subject(plane=plane), target=DataPlane.EVIDENCE))
        assert decision.allowed is False
        assert "TRANSITION_NOT_ALLOWED" in decision.reasons


def test_transition_source_plane_mismatch_fails_closed():
    controller = InfluenceController()
    subj = subject(plane=DataPlane.EVIDENCE)
    malformed = InfluenceRequest(
        subject=subj,
        proposition_id="claim:mismatched-plane",
        transition=DataPlaneTransition(
            source_plane=DataPlane.CLINICAL,
            target_plane=DataPlane.EVIDENCE,
            information_class=InformationClass.PUBLIC,
        ),
    )
    decision = controller.authorize(malformed)
    assert decision.allowed is False
    assert "SUBJECT_PLANE_MISMATCH" in decision.reasons
    assert "TRANSITION_NOT_ALLOWED" in decision.reasons


def test_explicitly_empty_transition_policy_denies_all_transitions():
    controller = InfluenceController([])
    decision = controller.authorize(request(subject()))

    assert decision.allowed is False
    assert "TRANSITION_NOT_ALLOWED" in decision.reasons


def test_missing_provenance_validation_safety_or_monitoring_fails_closed():
    cases = [
        (dict(provenance=False), "PROVENANCE_INCOMPLETE"),
        (dict(validation=False), "VALIDATION_NOT_PASSED"),
        (dict(safety=False), "SAFETY_NOT_PASSED"),
        (dict(monitoring=False), "MONITORING_NOT_ENABLED"),
    ]
    for changes, reason in cases:
        controller = InfluenceController()
        decision = controller.authorize(request(subject(**changes)))
        assert decision.allowed is False
        assert reason in decision.reasons


def test_revocation_propagates_only_along_matching_authority_dimension():
    controller = InfluenceController()
    subj = subject()
    evidence_request = request(
        subj,
        downstream="claim:evidence-dependent",
        deps=[DependencyDimension.EVIDENCE_AUTHORITY],
    )
    information_request = request(
        subj,
        downstream="route:information-dependent",
        deps=[DependencyDimension.INFORMATION_HANDLING_AUTHORITY],
    )
    assert controller.authorize(evidence_request).allowed is True
    assert controller.authorize(information_request).allowed is True

    result = controller.revoke_authority(subj.object_id, DependencyDimension.EVIDENCE_AUTHORITY)

    assert result.invalidated_downstream_ids == ["claim:evidence-dependent"]
    assert result.unaffected_downstream_ids == ["route:information-dependent"]
    assert controller.get_downstream_state("claim:evidence-dependent").active is False
    assert controller.get_downstream_state("route:information-dependent").active is True
    assert controller.get_subject(subj.object_id).information_handling_authority == InformationHandlingAuthorityState.APPROVED


def test_revoked_subject_cannot_bypass_gate_with_stale_approved_request():
    controller = InfluenceController()
    subj = subject()
    assert controller.authorize(request(subj, downstream="claim:first")).allowed is True
    controller.revoke_authority(subj.object_id, DependencyDimension.EVIDENCE_AUTHORITY)

    stale_copy = subject()
    decision = controller.authorize(request(stale_copy, downstream="claim:second"))
    assert decision.allowed is False
    assert "EVIDENCE_AUTHORITY_REVOKED" in decision.reasons


def test_conflicting_subject_snapshot_denies_and_requires_higher_revision_update():
    controller = InfluenceController()
    approved = subject()
    assert controller.authorize(request(approved, downstream="claim:first")).allowed is True

    denied = subject(evidence=EvidenceAuthorityState.DENIED)
    decision = controller.authorize(request(denied, downstream="claim:denied"))
    assert decision.allowed is False
    assert "SUBJECT_SNAPSHOT_CONFLICT" in decision.reasons
    assert controller.get_subject(approved.object_id).evidence_authority == EvidenceAuthorityState.DENIED
    assert controller.get_downstream_state("claim:first").active is False

    stale_decision = controller.authorize(request(approved, downstream="claim:stale"))
    assert stale_decision.allowed is False
    assert "SUBJECT_SNAPSHOT_CONFLICT" in stale_decision.reasons

    with pytest.raises(ValueError, match="higher revision"):
        controller.update_subject(subject(revision=1))

    controller.update_subject(subject(revision=2))
    refreshed_decision = controller.authorize(
        request(subject(revision=2), downstream="claim:refreshed")
    )
    assert refreshed_decision.allowed is True


def test_canonical_object_model_is_machine_readable():
    from medical_ai.schemas import (
        CitationMapping,
        Claim,
        ConnectorApproval,
        ConsequenceLevel,
        EvidenceObject,
        PHIClassification,
        Source,
        VerificationResult,
        VerificationStatus,
        WorkflowRun,
    )

    source_obj = Source(
        source_id="pubmed:1",
        authority="NLM",
        publisher="NLM",
        source_type="literature_index",
        title="Fixture",
        record_id="1",
        stable_url="https://example.invalid/1",
    )
    evidence_obj = EvidenceObject(
        evidence_id="ev:1",
        source_id=source_obj.source_id,
        passage_ids=["p:1"],
        proposition="Treatment X reduced symptom scores.",
    )
    claim_obj = Claim(
        claim_id="claim:1",
        claim_text=evidence_obj.proposition,
        consequence_level=ConsequenceLevel.MODERATE,
        evidence_ids=[evidence_obj.evidence_id],
        source_ids=[source_obj.source_id],
    )
    citation = CitationMapping(
        mapping_id="map:1",
        claim_id=claim_obj.claim_id,
        evidence_id=evidence_obj.evidence_id,
        source_id=source_obj.source_id,
        passage_ids=["p:1"],
        entailment_status="SUPPORTED",
        verified=True,
    )
    approval = ConnectorApproval(
        connector_id="pubmed",
        source_class="biomedical_literature",
        evidence_authority=EvidenceAuthorityState.APPROVED,
        information_handling_authority=InformationHandlingAuthorityState.DENIED,
        permitted_planes=[DataPlane.EVIDENCE],
    )
    phi = PHIClassification(
        classification_id="phi:1",
        object_id="query:1",
        information_class=InformationClass.PUBLIC,
        contains_phi=False,
    )
    verification = VerificationResult(
        verification_id="verify:1",
        claim_id=claim_obj.claim_id,
        status=VerificationStatus.PASS,
        verifier_id="exact-passage",
        verifier_version="fixture-v1",
    )
    workflow = WorkflowRun(
        workflow_run_id="run:1",
        source_ids=[source_obj.source_id],
        evidence_ids=[evidence_obj.evidence_id],
        claim_ids=[claim_obj.claim_id],
    )

    for obj in (source_obj, evidence_obj, claim_obj, citation, approval, phi, verification, workflow):
        assert obj.model_dump(mode="json")
    assert approval.evidence_authority == EvidenceAuthorityState.APPROVED
    assert approval.information_handling_authority == InformationHandlingAuthorityState.DENIED
