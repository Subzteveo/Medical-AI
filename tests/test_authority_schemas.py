"""Alpha3 A1 — canonical authority schema contract tests.

These exercise the closed-type, immutability, fail-closed and timezone invariants
of ``medical_ai.authority``. They assert that an ``ALLOW`` cannot be minted from a
prefilled field or an empty reason list, independent of any policy.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from medical_ai.authority import (
    AuthorityDimension,
    AuthorityOperation,
    AuthorityPurpose,
    ClaimType,
    DataPlaneTransitionDecision,
    DecisionResult,
    EvidenceAuthorityDecision,
    FreshnessState,
    InformationClassification,
    InformationHandlingDecision,
    RetractionState,
    SourceVersion,
    StatusClaimRecord,
    StatusResult,
    StatusValue,
    TypedJudgment,
    JudgmentType,
)
from medical_ai.schemas import DataPlane

AWARE = datetime(2026, 11, 5, 0, 0, tzinfo=timezone.utc)
NAIVE = datetime(2026, 11, 5, 0, 0)


def _evidence_decision(**overrides: object) -> EvidenceAuthorityDecision:
    base: dict[str, object] = dict(
        decision_id="d-1",
        subject_ref="claim-1",
        scope="evidence-authority:claim-1",
        policy_ref="evidence-authority-v0.2",
        policy_digest="deadbeef",
        input_state_hash="h-1",
        authority_source_ref="auth-src-1",
        evidence_refs=("prov-1",),
        observed_at=AWARE,
        result=DecisionResult.ALLOW,
        reason_codes=(),
        trace_ref="t-1",
        claim_evidence_link_ref="link-1",
        source_version_ref="sv-1",
        claim_type=ClaimType.BIOMEDICAL_LITERATURE,
        context_ref="ctx-1",
        permitted_operations=(AuthorityOperation.RETRIEVE_PUBLIC_EVIDENCE,),
    )
    base.update(overrides)
    return EvidenceAuthorityDecision(**base)


def test_allow_requires_authority_source_and_evidence() -> None:
    _evidence_decision()  # valid ALLOW
    with pytest.raises(ValidationError):
        _evidence_decision(authority_source_ref=None)
    with pytest.raises(ValidationError):
        _evidence_decision(evidence_refs=())


def test_allow_rejects_blocking_reason_codes() -> None:
    with pytest.raises(ValidationError):
        _evidence_decision(reason_codes=("SHOULD_NOT_BE_HERE",))


def test_allow_evidence_authority_must_name_operations() -> None:
    with pytest.raises(ValidationError):
        _evidence_decision(permitted_operations=())


def test_deny_requires_reason_and_forbids_authority_source() -> None:
    deny = _evidence_decision(
        result=DecisionResult.DENY,
        authority_source_ref=None,
        evidence_refs=(),
        reason_codes=("WRONG_REGULATOR_FOR_CLAIM",),
        permitted_operations=(),
    )
    assert deny.result is DecisionResult.DENY
    with pytest.raises(ValidationError):  # DENY with no reason codes
        _evidence_decision(result=DecisionResult.DENY, authority_source_ref=None, evidence_refs=(), reason_codes=(), permitted_operations=())
    with pytest.raises(ValidationError):  # DENY must not carry an authority source
        _evidence_decision(result=DecisionResult.DENY, evidence_refs=(), reason_codes=("X",), permitted_operations=())


def test_records_are_immutable() -> None:
    decision = _evidence_decision()
    with pytest.raises(ValidationError):
        decision.result = DecisionResult.DENY  # type: ignore[misc]


def test_extra_fields_forbidden() -> None:
    with pytest.raises(ValidationError):
        _evidence_decision(unexpected_field="x")


def test_naive_timestamp_rejected() -> None:
    with pytest.raises(ValidationError):
        _evidence_decision(observed_at=NAIVE)


def test_blank_identifiers_rejected() -> None:
    with pytest.raises(ValidationError):
        _evidence_decision(decision_id="   ")
    with pytest.raises(ValidationError):
        _evidence_decision(decision_id="")


def test_dimension_is_fixed_per_decision_type() -> None:
    info = InformationHandlingDecision(
        decision_id="d-2", subject_ref="q-1", scope="ih:q-1", policy_ref="information-handling-v0.2",
        policy_digest="beef", input_state_hash="h", authority_source_ref="a", evidence_refs=("c",),
        observed_at=AWARE, result=DecisionResult.ALLOW, trace_ref="t", component_ref="pubmed_public_connector",
        information_class=InformationClassification.PUBLIC_EVIDENCE, operation=AuthorityOperation.RETRIEVE_PUBLIC_EVIDENCE,
        purpose=AuthorityPurpose.LITERATURE_DISCOVERY, environment="production_public_readonly",
    )
    assert info.dimension is AuthorityDimension.INFORMATION_HANDLING
    with pytest.raises(ValidationError):
        InformationHandlingDecision(
            decision_id="d-2", dimension=AuthorityDimension.EVIDENCE_AUTHORITY, subject_ref="q-1", scope="ih:q-1",
            policy_ref="p", policy_digest="beef", input_state_hash="h", authority_source_ref="a", evidence_refs=("c",),
            observed_at=AWARE, result=DecisionResult.ALLOW, trace_ref="t", component_ref="c1",
            information_class=InformationClassification.PUBLIC_EVIDENCE, operation=AuthorityOperation.RETRIEVE_PUBLIC_EVIDENCE,
            purpose=AuthorityPurpose.LITERATURE_DISCOVERY, environment="env",
        )


def test_data_plane_decision_roundtrip_preserves_enums() -> None:
    decision = DataPlaneTransitionDecision(
        decision_id="d-3", subject_ref="t-1", scope="dp:t-1", policy_ref="data-plane-transitions-v0.2",
        policy_digest="beef", input_state_hash="h", authority_source_ref="a", evidence_refs=("c",),
        observed_at=AWARE, result=DecisionResult.ALLOW, trace_ref="t", from_plane=DataPlane.EVIDENCE,
        to_plane=DataPlane.EVIDENCE, information_class=InformationClassification.PUBLIC_EVIDENCE,
        operation=AuthorityOperation.RETRIEVE_PUBLIC_EVIDENCE, purpose=AuthorityPurpose.LITERATURE_DISCOVERY,
        component_ref="pubmed_public_connector",
    )
    restored = DataPlaneTransitionDecision.model_validate_json(decision.model_dump_json())
    assert restored == decision
    assert restored.from_plane is DataPlane.EVIDENCE
    assert restored.information_class is InformationClassification.PUBLIC_EVIDENCE


def test_source_version_freshness_derivation() -> None:
    def version(**kw: object) -> SourceVersion:
        base: dict[str, object] = dict(
            source_version_id="sv", source_id="s", record_id="r", content_or_version_digest="dg",
            retrieved_at=AWARE, jurisdiction="AU", retraction_state=RetractionState.NOT_RETRACTED,
            provenance_ref="p", trace_ref="t",
        )
        base.update(kw)
        return SourceVersion(**base)

    assert version().freshness is FreshnessState.CURRENT
    assert version(retraction_state=RetractionState.RETRACTED).freshness is FreshnessState.RETRACTED
    assert version(retraction_state=RetractionState.SUPERSEDED).freshness is FreshnessState.SUPERSEDED
    assert version(retraction_state=RetractionState.UNKNOWN).freshness is FreshnessState.UNKNOWN
    assert version(superseded_by_ref="sv2").freshness is FreshnessState.SUPERSEDED


def test_typed_judgment_confidence_is_bounded_and_optional() -> None:
    judgment = TypedJudgment(
        judgment_id="j", judgment_type=JudgmentType.CLAIM_EVIDENCE_ENTAILMENT, subject_refs=("c-1",),
        input_state_hash="h", result="SUPPORTED_EXACT_PASSAGE", method_id="extractive-exact", created_at=AWARE,
        trace_ref="t",
    )
    assert judgment.confidence is None
    with pytest.raises(ValidationError):
        TypedJudgment(
            judgment_id="j", judgment_type=JudgmentType.CLAIM_EVIDENCE_ENTAILMENT, subject_refs=(),
            input_state_hash="h", result="x", method_id="m", created_at=AWARE, trace_ref="t",
        )
    with pytest.raises(ValidationError):
        TypedJudgment(
            judgment_id="j", judgment_type=JudgmentType.CLAIM_EVIDENCE_ENTAILMENT, subject_refs=("c",),
            input_state_hash="h", result="x", method_id="m", created_at=AWARE, trace_ref="t", confidence=1.5,
        )


def test_status_claim_authorized_requires_authority_and_evidence() -> None:
    def record(**kw: object) -> StatusClaimRecord:
        base: dict[str, object] = dict(
            status_claim_id="sc", subject_ref="pr-12", status=StatusValue.MERGED, scope="pr-12",
            revision_ref="abc123", authority_type="github-merge", authority_ref="merge-commit-abc",
            evidence_refs=("merge-event-1",), asserted_at=AWARE, observed_at=AWARE,
            result=StatusResult.AUTHORIZED, trace_ref="t",
        )
        base.update(kw)
        return StatusClaimRecord(**base)

    assert record().result is StatusResult.AUTHORIZED
    with pytest.raises(ValidationError):
        record(authority_ref=None)
    with pytest.raises(ValidationError):
        record(evidence_refs=())
    with pytest.raises(ValidationError):
        record(reason_codes=("UNEXPECTED",))
    unauth = record(result=StatusResult.UNAUTHORIZED, authority_ref=None, evidence_refs=(), reason_codes=("NO_MERGE_EVENT",))
    assert unauth.result is StatusResult.UNAUTHORIZED
    with pytest.raises(ValidationError):  # UNAUTHORIZED needs a reason
        record(result=StatusResult.UNAUTHORIZED, authority_ref=None, evidence_refs=(), reason_codes=())
