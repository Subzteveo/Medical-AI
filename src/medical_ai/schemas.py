from __future__ import annotations

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


class EvidenceAnswer(BaseModel):
    status: AnswerStatus
    answer_markdown: str
    claims: list[ClaimRecord]
    sources: list[SourceRecord]
    passages: list[Passage] = Field(default_factory=list)
    trace: ExecutionTrace
