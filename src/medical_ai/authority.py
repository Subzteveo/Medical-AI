"""Alpha3 A1 — closed canonical authority schemas and denial-preserving adapters.

These types implement the A1 schema contract in
``project_docs/ALPHA3_A1_SCHEMA_POLICY_REVIEW.md``. They are a candidate control
layer: they define *how* authority to influence a medical proposition must be
represented, not whether any particular object is approved. Nothing in this module
is wired into ``engine.py``/``renderer.py``/``api.py`` — that integration is A2 and
is separately gated.

Design invariants:

* A model is never evidence. A populated field, a ``validation_passed`` flag, or a
  verifier ``PASS`` never authorises influence.
* Every record is immutable (``frozen=True``) and rejects unexpected fields
  (``extra="forbid"``).
* Every ``ALLOW`` decision must carry an independently resolvable authority source
  and the policy-required evidence. ``ALLOW`` cannot be constructed from an empty
  reason list plus prefilled attributes.
* Timestamps are timezone-aware; identifiers are nonblank and unpadded.
* Unknown/ambiguous input fails closed.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import AfterValidator, AwareDatetime, BaseModel, ConfigDict, Field
from typing import Annotated

from .schemas import DataPlane as DataPlane, FreshnessState as FreshnessState, InformationClass


# ---------------------------------------------------------------------------
# Reusable constrained field types
# ---------------------------------------------------------------------------
def _nonblank(value: str) -> str:
    if not value or value != value.strip():
        raise ValueError("reference identifiers must be nonblank and unpadded")
    return value


NonBlankStr = Annotated[str, AfterValidator(_nonblank)]


# ---------------------------------------------------------------------------
# Closed enumerations
# ---------------------------------------------------------------------------
class AuthorityDimension(StrEnum):
    """The four independent authority dimensions of the Tranche A kernel."""

    EVIDENCE_AUTHORITY = "EVIDENCE_AUTHORITY"
    INFORMATION_HANDLING = "INFORMATION_HANDLING"
    DATA_PLANE_TRANSITION = "DATA_PLANE_TRANSITION"
    STATUS_AUTHORITY = "STATUS_AUTHORITY"


class DecisionResult(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"


class StatusResult(StrEnum):
    """Evaluation outcome for a status claim. Not a new approved status."""

    AUTHORIZED = "AUTHORIZED"
    UNAUTHORIZED = "UNAUTHORIZED"
    STALE = "STALE"


class InformationClassification(StrEnum):
    """A1 closed information classification. Unknown is deny-preserving."""

    PUBLIC_EVIDENCE = "PUBLIC_EVIDENCE"
    IDENTIFIABLE_HEALTH_INFORMATION = "IDENTIFIABLE_HEALTH_INFORMATION"
    DEIDENTIFIED_HEALTH_INFORMATION = "DEIDENTIFIED_HEALTH_INFORMATION"
    RESTRICTED_RESEARCH_DATA = "RESTRICTED_RESEARCH_DATA"
    UNKNOWN = "UNKNOWN"


class AuthorityOperation(StrEnum):
    RETRIEVE_PUBLIC_EVIDENCE = "RETRIEVE_PUBLIC_EVIDENCE"
    EXTRACT_PASSAGE = "EXTRACT_PASSAGE"
    VERIFY_EXACT_PASSAGE = "VERIFY_EXACT_PASSAGE"
    AUTHORIZE_CLAIM_LINK = "AUTHORIZE_CLAIM_LINK"
    RENDER_EDUCATIONAL_CLAIM = "RENDER_EDUCATIONAL_CLAIM"
    READ_CLINICAL_CONTEXT = "READ_CLINICAL_CONTEXT"
    DERIVE_RESEARCH_RESULT = "DERIVE_RESEARCH_RESULT"
    PROMOTE_TO_EVIDENCE = "PROMOTE_TO_EVIDENCE"
    ASSERT_PROJECT_STATUS = "ASSERT_PROJECT_STATUS"


class AuthorityPurpose(StrEnum):
    LITERATURE_DISCOVERY = "LITERATURE_DISCOVERY"
    TRIAL_REGISTRATION_DISCOVERY = "TRIAL_REGISTRATION_DISCOVERY"
    EDUCATIONAL_EVIDENCE_RENDER = "EDUCATIONAL_EVIDENCE_RENDER"
    INTERNAL_PROJECT_ASSURANCE = "INTERNAL_PROJECT_ASSURANCE"
    CLINICAL_CONTEXT = "CLINICAL_CONTEXT"
    RESEARCH_ANALYSIS = "RESEARCH_ANALYSIS"


class ClaimType(StrEnum):
    BIOMEDICAL_LITERATURE = "BIOMEDICAL_LITERATURE"
    TRIAL_REGISTRATION_FACT = "TRIAL_REGISTRATION_FACT"
    TREATMENT_EFFICACY = "TREATMENT_EFFICACY"
    AU_REGULATORY_APPROVAL = "AU_REGULATORY_APPROVAL"
    AU_SUBSIDY_STATUS = "AU_SUBSIDY_STATUS"
    PROJECT_STATUS = "PROJECT_STATUS"
    UNKNOWN = "UNKNOWN"


class SourceClass(StrEnum):
    PUBMED_INDEXED_LITERATURE = "PUBMED_INDEXED_LITERATURE"
    CLINICALTRIALS_GOV_REGISTRY = "CLINICALTRIALS_GOV_REGISTRY"
    TGA = "TGA"
    PBS = "PBS"
    UNKNOWN = "UNKNOWN"


class RetractionState(StrEnum):
    NOT_RETRACTED = "NOT_RETRACTED"
    RETRACTED = "RETRACTED"
    SUPERSEDED = "SUPERSEDED"
    UNKNOWN = "UNKNOWN"


class JudgmentType(StrEnum):
    CLAIM_EVIDENCE_ENTAILMENT = "CLAIM_EVIDENCE_ENTAILMENT"
    APPLICABILITY_ASSESSMENT = "APPLICABILITY_ASSESSMENT"
    FRESHNESS_ASSESSMENT = "FRESHNESS_ASSESSMENT"
    CONFLICT_ASSESSMENT = "CONFLICT_ASSESSMENT"


class StatusValue(StrEnum):
    PROPOSED = "PROPOSED"
    DOCUMENTED = "DOCUMENTED"
    IMPLEMENTED = "IMPLEMENTED"
    TESTED = "TESTED"
    PASSED = "PASSED"
    VALIDATED = "VALIDATED"
    VERIFIED = "VERIFIED"
    APPROVED = "APPROVED"
    MERGED = "MERGED"
    RELEASE_BLOCKED = "RELEASE_BLOCKED"
    RELEASE_READY = "RELEASE_READY"
    DEFERRED = "DEFERRED"
    SUPERSEDED = "SUPERSEDED"
    DEPRECATED = "DEPRECATED"


# ---------------------------------------------------------------------------
# Denial-preserving legacy information-class migration
# ---------------------------------------------------------------------------
_LEGACY_INFORMATION_CLASS: dict[InformationClass, InformationClassification] = {
    InformationClass.PUBLIC: InformationClassification.PUBLIC_EVIDENCE,
    InformationClass.PHI: InformationClassification.IDENTIFIABLE_HEALTH_INFORMATION,
    # No assumed-safe mapping: SENSITIVE and UNKNOWN both become UNKNOWN (deny).
    InformationClass.SENSITIVE: InformationClassification.UNKNOWN,
    InformationClass.UNKNOWN: InformationClassification.UNKNOWN,
}


def migrate_information_class(legacy: InformationClass) -> InformationClassification:
    """Map a legacy ``InformationClass`` to the A1 classification, deny-preserving.

    ``SENSITIVE`` has no assumed-safe mapping and becomes ``UNKNOWN``. De-identification
    requires a separately authorised determination, so no legacy flag may become
    ``DEIDENTIFIED_HEALTH_INFORMATION`` or ``RESTRICTED_RESEARCH_DATA`` here.
    """

    return _LEGACY_INFORMATION_CLASS.get(legacy, InformationClassification.UNKNOWN)


# ---------------------------------------------------------------------------
# Base record configuration
# ---------------------------------------------------------------------------
class _FrozenRecord(BaseModel):
    """Immutable, closed record base for all A1 canonical types."""

    model_config = ConfigDict(extra="forbid", frozen=True)


# ---------------------------------------------------------------------------
# Source, link and judgment records
# ---------------------------------------------------------------------------
class SourceVersion(_FrozenRecord):
    source_version_id: NonBlankStr
    source_id: NonBlankStr
    record_id: NonBlankStr
    content_or_version_digest: NonBlankStr
    retrieved_at: AwareDatetime
    jurisdiction: NonBlankStr
    retraction_state: RetractionState
    provenance_ref: NonBlankStr
    trace_ref: NonBlankStr
    source_class: SourceClass = SourceClass.UNKNOWN
    effective_at: AwareDatetime | None = None
    supersedes_ref: NonBlankStr | None = None
    superseded_by_ref: NonBlankStr | None = None

    @property
    def freshness(self) -> FreshnessState:
        """Freshness derived only from recorded state; unknown blocks current-effect use."""

        if self.retraction_state is RetractionState.RETRACTED:
            return FreshnessState.RETRACTED
        if self.retraction_state is RetractionState.SUPERSEDED or self.superseded_by_ref is not None:
            return FreshnessState.SUPERSEDED
        if self.retraction_state is RetractionState.UNKNOWN:
            return FreshnessState.UNKNOWN
        return FreshnessState.CURRENT


class ClaimEvidenceLink(_FrozenRecord):
    link_id: NonBlankStr
    claim_id: NonBlankStr
    evidence_id: NonBlankStr
    source_version_id: NonBlankStr
    passage_refs: tuple[NonBlankStr, ...] = Field(min_length=1)
    claim_type: ClaimType
    jurisdiction: NonBlankStr
    population_context: NonBlankStr
    required_authority_class: SourceClass
    applicability: NonBlankStr
    verification_ref: NonBlankStr
    evidence_authority_decision_ref: NonBlankStr
    dependency_refs: tuple[NonBlankStr, ...] = Field(default_factory=tuple)
    result: DecisionResult
    trace_ref: NonBlankStr


class TypedJudgment(_FrozenRecord):
    """A semantic assessment. Confidence is advisory and never grants permission."""

    judgment_id: NonBlankStr
    judgment_type: JudgmentType
    subject_refs: tuple[NonBlankStr, ...] = Field(min_length=1)
    input_state_hash: NonBlankStr
    result: NonBlankStr
    method_id: NonBlankStr
    created_at: AwareDatetime
    trace_ref: NonBlankStr
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Shared immutable decision envelope and the three allow/deny decisions
# ---------------------------------------------------------------------------
class AuthorityDecisionEnvelope(_FrozenRecord):
    """Shared immutable decision envelope.

    An ``ALLOW`` result must carry an independently verifiable authority source and
    at least one policy-required evidence reference, and must carry no blocking
    reason codes. A ``DENY`` must record at least one reason code and must not carry
    an authority source. These checks make it impossible to express an empty-reason
    ``ALLOW`` or an unexplained ``DENY``.
    """

    decision_id: NonBlankStr
    dimension: AuthorityDimension
    subject_ref: NonBlankStr
    scope: NonBlankStr
    policy_ref: NonBlankStr
    policy_digest: NonBlankStr
    input_state_hash: NonBlankStr
    authority_source_ref: NonBlankStr | None = None
    evidence_refs: tuple[NonBlankStr, ...] = Field(default_factory=tuple)
    observed_at: AwareDatetime
    result: DecisionResult
    reason_codes: tuple[NonBlankStr, ...] = Field(default_factory=tuple)
    trace_ref: NonBlankStr

    def model_post_init(self, _context: object) -> None:
        if self.result is DecisionResult.ALLOW:
            if self.authority_source_ref is None:
                raise ValueError("ALLOW requires an independent authority source reference")
            if not self.evidence_refs:
                raise ValueError("ALLOW requires at least one policy-required evidence reference")
            if self.reason_codes:
                raise ValueError("ALLOW must not carry blocking reason codes")
        else:
            if not self.reason_codes:
                raise ValueError("DENY requires at least one reason code")
            if self.authority_source_ref is not None:
                raise ValueError("DENY must not carry an authority source reference")


class EvidenceAuthorityDecision(AuthorityDecisionEnvelope):
    dimension: AuthorityDimension = AuthorityDimension.EVIDENCE_AUTHORITY
    claim_evidence_link_ref: NonBlankStr
    source_version_ref: NonBlankStr
    claim_type: ClaimType
    context_ref: NonBlankStr
    permitted_operations: tuple[AuthorityOperation, ...] = Field(default_factory=tuple)

    def model_post_init(self, _context: object) -> None:
        super().model_post_init(_context)
        if self.dimension is not AuthorityDimension.EVIDENCE_AUTHORITY:
            raise ValueError("EvidenceAuthorityDecision dimension is fixed")
        if self.result is DecisionResult.ALLOW and not self.permitted_operations:
            raise ValueError("ALLOW evidence authority must name the permitted operations")


class InformationHandlingDecision(AuthorityDecisionEnvelope):
    dimension: AuthorityDimension = AuthorityDimension.INFORMATION_HANDLING
    component_ref: NonBlankStr
    information_class: InformationClassification
    operation: AuthorityOperation
    purpose: AuthorityPurpose
    environment: NonBlankStr

    def model_post_init(self, _context: object) -> None:
        super().model_post_init(_context)
        if self.dimension is not AuthorityDimension.INFORMATION_HANDLING:
            raise ValueError("InformationHandlingDecision dimension is fixed")


class DataPlaneTransitionDecision(AuthorityDecisionEnvelope):
    dimension: AuthorityDimension = AuthorityDimension.DATA_PLANE_TRANSITION
    from_plane: DataPlane
    to_plane: DataPlane
    information_class: InformationClassification
    operation: AuthorityOperation
    purpose: AuthorityPurpose
    component_ref: NonBlankStr

    def model_post_init(self, _context: object) -> None:
        super().model_post_init(_context)
        if self.dimension is not AuthorityDimension.DATA_PLANE_TRANSITION:
            raise ValueError("DataPlaneTransitionDecision dimension is fixed")


# ---------------------------------------------------------------------------
# Status claim record
# ---------------------------------------------------------------------------
class StatusClaimRecord(_FrozenRecord):
    """A revision-bound status assertion with an independent evaluation result.

    ``AUTHORIZED`` requires a named external authority reference and supporting
    evidence. ``UNAUTHORIZED``/``STALE`` require reason codes. No status label
    implies any other status.
    """

    status_claim_id: NonBlankStr
    subject_ref: NonBlankStr
    status: StatusValue
    scope: NonBlankStr
    revision_ref: NonBlankStr
    authority_type: NonBlankStr
    authority_ref: NonBlankStr | None = None
    evidence_refs: tuple[NonBlankStr, ...] = Field(default_factory=tuple)
    asserted_at: AwareDatetime
    observed_at: AwareDatetime
    result: StatusResult
    reason_codes: tuple[NonBlankStr, ...] = Field(default_factory=tuple)
    trace_ref: NonBlankStr
    recheck_expires_at: AwareDatetime | None = None

    def model_post_init(self, _context: object) -> None:
        if self.result is StatusResult.AUTHORIZED:
            if self.authority_ref is None:
                raise ValueError("AUTHORIZED status requires a named authority reference")
            if not self.evidence_refs:
                raise ValueError("AUTHORIZED status requires supporting evidence references")
            if self.reason_codes:
                raise ValueError("AUTHORIZED status must not carry blocking reason codes")
        else:
            if not self.reason_codes:
                raise ValueError("UNAUTHORIZED/STALE status requires at least one reason code")
