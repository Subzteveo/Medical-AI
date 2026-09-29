from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from pydantic import BaseModel, Field


class AnswerStatus(StrEnum):
    ANSWER_SUPPORTED = "ANSWER_SUPPORTED"
    ANSWER_SUPPORTED_WITH_QUALIFICATIONS = "ANSWER_SUPPORTED_WITH_QUALIFICATIONS"
    EVIDENCE_INSUFFICIENT = "EVIDENCE_INSUFFICIENT"
    EVIDENCE_CONFLICTING = "EVIDENCE_CONFLICTING"
    SOURCE_OUTDATED = "SOURCE_OUTDATED"
    POPULATION_MISMATCH = "POPULATION_MISMATCH"
    NO_AUTHORITATIVE_SOURCE = "NO_AUTHORITATIVE_SOURCE"
    JURISDICTION_UNCLEAR = "JURISDICTION_UNCLEAR"
    PROVENANCE_INCOMPLETE = "PROVENANCE_INCOMPLETE"
    HIGH_CONSEQUENCE_VERIFICATION_FAILED = "HIGH_CONSEQUENCE_VERIFICATION_FAILED"
    OUTSIDE_VALIDATED_CAPABILITY = "OUTSIDE_VALIDATED_CAPABILITY"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    INFLUENCE_DENIED = "INFLUENCE_DENIED"


class ConsequenceLevel(StrEnum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"


class VerificationStatus(StrEnum):
    PASS = "PASS"
    QUALIFY = "QUALIFY"
    FAIL = "FAIL"
    CONFLICT = "CONFLICT"


class Applicability(StrEnum):
    DIRECT = "DIRECT"
    PARTIAL = "PARTIAL"
    INDIRECT = "INDIRECT"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class AuthorityState(StrEnum):
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    UNKNOWN = "UNKNOWN"
    REVOKED = "REVOKED"


class DataPlane(StrEnum):
    EVIDENCE = "EVIDENCE"
    TERMINOLOGY = "TERMINOLOGY"
    CLINICAL = "CLINICAL"
    RESEARCH = "RESEARCH"


class InformationClass(StrEnum):
    PUBLIC = "PUBLIC"
    SENSITIVE = "SENSITIVE"
    PHI = "PHI"
    UNKNOWN = "UNKNOWN"


class DependencyDimension(StrEnum):
    EVIDENCE_AUTHORITY = "EVIDENCE_AUTHORITY"
    INFORMATION_HANDLING_AUTHORITY = "INFORMATION_HANDLING_AUTHORITY"
    PROVENANCE = "PROVENANCE"
    VALIDATION = "VALIDATION"
    SAFETY = "SAFETY"
    MONITORING = "MONITORING"


class InfluenceDecisionStatus(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"


class SourceRecord(BaseModel):
    source_id: str
    authority: str
    publisher: str
    source_type: str
    title: str
    jurisdiction: str = "INTERNATIONAL"
    record_id: str
    stable_url: str
    identifiers: dict[str, str] = Field(default_factory=dict)
    version: str | None = None
    publication_date: str | None = None
    updated_date: str | None = None
    effective_date: str | None = None
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    superseded: bool = False
    licence_class: str = "public_metadata"
    evidence_class: str = "primary_or_indexed_literature"
    population: str | None = None
    phi_status: str = "non_phi"
    provenance_complete: bool = True
    raw_metadata: dict[str, Any] = Field(default_factory=dict)


class Passage(BaseModel):
    passage_id: str
    source_id: str
    section: str
    text: str
    locator: str
    start_offset: int | None = None
    end_offset: int | None = None


class EvidenceUnit(BaseModel):
    evidence_id: str
    source_id: str
    passage_ids: list[str]
    proposition: str
    evidence_type: str = "abstract_text"
    population: str | None = None
    intervention_or_exposure: str | None = None
    comparator: str | None = None
    outcome: str | None = None
    effect: str | None = None
    uncertainty: str | None = None
    jurisdiction: str = "INTERNATIONAL"
    limitations: list[str] = Field(default_factory=list)


class ClaimRecord(BaseModel):
    claim_id: str
    claim_text: str
    claim_type: str = "DIRECT"
    consequence_level: ConsequenceLevel
    evidence_ids: list[str]
    source_ids: list[str] = Field(default_factory=list)
    jurisdiction: str = "INTERNATIONAL"
    population: str | None = None
    applicability: Applicability = Applicability.DIRECT
    evidence_certainty: str = "NOT_ASSESSED"
    freshness_status: str = "CURRENT_OR_NOT_ASSESSED"
    conflict_status: str = "NONE_DETECTED"
    entailment_status: str = "UNVERIFIED"
    verification_status: VerificationStatus = VerificationStatus.FAIL
    model_id: str = "none-extractive-alpha2"
    prompt_version: str = "alpha2-extractive"


class QueryPlan(BaseModel):
    intent: list[str]
    user_mode: str
    patient_specific: bool
    known_user_facts: list[str] = Field(default_factory=list)
    unknown_material_facts: list[str] = Field(default_factory=list)
    jurisdiction: str
    jurisdiction_material: bool = False
    temporal_sensitivity: str
    consequence_level: ConsequenceLevel
    required_source_classes: list[str]
    retrieval_questions: list[str]
    required_second_pass: bool = False
    safety_flags: list[str] = Field(default_factory=list)


class ExecutionTrace(BaseModel):
    trace_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    query_plan: QueryPlan
    retrieval_query_digests: list[str]
    connectors_used: list[str]
    source_ids: list[str]
    evidence_ids: list[str]
    candidate_claim_ids: list[str]
    verification_results: dict[str, str]
    safety_flags: list[str]
    component_versions: dict[str, str]
    final_status: AnswerStatus
    authorization_decision_ids: list[str] = Field(default_factory=list)


class Source(SourceRecord):
    """Canonical source object used by the v0.2 influence-control core."""


class EvidenceObject(EvidenceUnit):
    """Canonical evidence object; models may transform it but are never evidence themselves."""


class Claim(ClaimRecord):
    """Canonical claim object prior to or after influence authorization."""


class CitationMapping(BaseModel):
    mapping_id: str
    claim_id: str
    evidence_id: str
    source_id: str
    passage_ids: list[str] = Field(default_factory=list)
    entailment_status: str = "UNVERIFIED"
    verified: bool = False


class ConnectorApproval(BaseModel):
    connector_id: str
    source_class: str
    evidence_authority: AuthorityState = AuthorityState.UNKNOWN
    information_handling_authority: AuthorityState = AuthorityState.UNKNOWN
    permitted_planes: list[DataPlane] = Field(default_factory=list)
    policy_version: str = "medical-ai-influence-v0.2"


class PHIClassification(BaseModel):
    classification_id: str
    object_id: str
    information_class: InformationClass = InformationClass.UNKNOWN
    contains_phi: bool | None = None
    policy_version: str = "medical-ai-influence-v0.2"


class VerificationResult(BaseModel):
    verification_id: str
    claim_id: str
    status: VerificationStatus
    reasons: list[str] = Field(default_factory=list)
    verifier_id: str
    verifier_version: str


class WorkflowRun(BaseModel):
    workflow_run_id: str
    source_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    claim_ids: list[str] = Field(default_factory=list)
    authorization_decision_ids: list[str] = Field(default_factory=list)
    component_versions: dict[str, str] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None


class InfluenceSubject(BaseModel):
    object_id: str
    object_type: str
    data_plane: DataPlane
    evidence_authority: AuthorityState = AuthorityState.UNKNOWN
    information_handling_authority: AuthorityState = AuthorityState.UNKNOWN
    provenance_complete: bool = False
    validation_passed: bool = False
    safety_passed: bool = False
    monitoring_enabled: bool = False
    version: str


class DataPlaneTransition(BaseModel):
    source_plane: DataPlane
    target_plane: DataPlane
    information_class: InformationClass = InformationClass.UNKNOWN


class InfluenceRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    subject: InfluenceSubject
    proposition_id: str
    transition: DataPlaneTransition
    required_dependency_dimensions: list[DependencyDimension] = Field(
        default_factory=lambda: [
            DependencyDimension.EVIDENCE_AUTHORITY,
            DependencyDimension.INFORMATION_HANDLING_AUTHORITY,
            DependencyDimension.PROVENANCE,
            DependencyDimension.VALIDATION,
            DependencyDimension.SAFETY,
            DependencyDimension.MONITORING,
        ]
    )


class InfluenceDecision(BaseModel):
    decision_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str
    object_id: str
    proposition_id: str
    status: InfluenceDecisionStatus
    allowed: bool
    reasons: list[str] = Field(default_factory=list)
    policy_version: str
    evaluated_dimensions: dict[str, str]
    transition: DataPlaneTransition
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DependencyEdge(BaseModel):
    dependency_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    upstream_object_id: str
    downstream_object_id: str
    dimension: DependencyDimension


class DownstreamInfluenceState(BaseModel):
    object_id: str
    active: bool = True
    invalidation_reasons: list[str] = Field(default_factory=list)


class RevocationResult(BaseModel):
    upstream_object_id: str
    dimension: DependencyDimension
    invalidated_downstream_ids: list[str] = Field(default_factory=list)
    unaffected_downstream_ids: list[str] = Field(default_factory=list)


class EvidenceAnswer(BaseModel):
    status: AnswerStatus
    answer_markdown: str
    claims: list[ClaimRecord]
    sources: list[SourceRecord]
    passages: list[Passage] = Field(default_factory=list)
    trace: ExecutionTrace
    influence_decisions: list[InfluenceDecision] = Field(default_factory=list)
