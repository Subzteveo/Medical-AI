"""Alpha3 A2 — trusted, policy-driven authority resolver.

A2 replaces the engine's self-declared ``evidence_authority=APPROVED`` /
``validation_passed=True`` with authority *independently resolved* from the merged
A1 policies (``authority_policy``). The resolver is the only component that may turn
a verified claim into an ``APPROVED`` influence subject, and it does so only when the
trusted, versioned, digest-verified policies admit the claim's actual scope across
every mandatory dimension.

Fail-closed properties:

* An engine constructed without a resolver resolves no authority at all: every claim
  is ``UNKNOWN`` / ``validation_passed=False`` and the influence gate denies it. A
  verifier ``PASS`` and connector admission are not authority.
* Retracted/superseded sources, a source class outside its claim class, a
  non-public information class, or a denied data-plane transition all resolve to a
  denial even when a resolver is present.
* Every ``ALLOW`` the resolver returns is backed by A1 decision records that carry an
  independent authority source, the matching policy digest, an input-state hash,
  scope, (empty) reasons and a trace reference.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .authority import (
    AuthorityDecisionEnvelope,
    AuthorityOperation,
    AuthorityPurpose,
    ClaimType,
    DataPlaneTransitionDecision,
    DecisionResult,
    EvidenceAuthorityDecision,
    FreshnessState,
    InformationClassification,
    InformationHandlingDecision,
    SourceClass,
)
from .authority_policy import (
    RuleScope,
    ScopedDecision,
    ScopedDecisionReason,
    compile_aggregation_policy,
    compile_authority_policy,
    evaluate_scope,
    resolve_required_dimensions,
)
from .schemas import (
    ClaimRecord,
    DataPlane,
    EvidenceAuthorityState,
    InformationClass,
    InformationHandlingAuthorityState,
    SourceRecord,
    source_version_content_sha256,
)

_EVIDENCE_POLICY = "evidence-authority-v0.2.yaml"
_INFORMATION_POLICY = "information-handling-v0.2.yaml"
_DATA_PLANE_POLICY = "data-plane-transitions-v0.2.yaml"
_AGGREGATION_POLICY = "influence-aggregation-v0.2.yaml"

# Trusted mapping from the engine's source-class strings to A1 closed types.
_SOURCE_CLASS: dict[str, SourceClass] = {
    "biomedical_literature": SourceClass.PUBMED_INDEXED_LITERATURE,
    "clinical_trial_registry": SourceClass.CLINICALTRIALS_GOV_REGISTRY,
}
_CLAIM_TYPE: dict[str, ClaimType] = {
    "biomedical_literature": ClaimType.BIOMEDICAL_LITERATURE,
    "clinical_trial_registry": ClaimType.TRIAL_REGISTRATION_FACT,
}
_COMPONENT: dict[str, str] = {
    "biomedical_literature": "pubmed_public_connector",
    "clinical_trial_registry": "clinicaltrials_public_connector",
}
_PURPOSE: dict[str, AuthorityPurpose] = {
    "biomedical_literature": AuthorityPurpose.LITERATURE_DISCOVERY,
    "clinical_trial_registry": AuthorityPurpose.TRIAL_REGISTRATION_DISCOVERY,
}
_ENVIRONMENT = "production_public_readonly"

# Worst-across-sources ranking: a higher rank dominates. RETRACTED beats SUPERSEDED,
# which beats UNKNOWN (and missing), which beats CURRENT.
_FRESHNESS_RANK: dict[FreshnessState, int] = {
    FreshnessState.CURRENT: 0,
    FreshnessState.UNKNOWN: 1,
    FreshnessState.SUPERSEDED: 2,
    FreshnessState.RETRACTED: 3,
}
# The user-facing claim freshness_status. CURRENT appears only when every source was
# assessed CURRENT; any missing or unknown assessment yields UNKNOWN.
_FRESHNESS_STATUS: dict[FreshnessState, str] = {
    FreshnessState.CURRENT: "CURRENT",
    FreshnessState.SUPERSEDED: "SUPERSEDED",
    FreshnessState.RETRACTED: "RETRACTED",
    FreshnessState.UNKNOWN: "UNKNOWN",
}


@dataclass(frozen=True)
class ClaimAuthorityResolution:
    """The resolved authority for a single claim, ready to drive an InfluenceSubject."""

    evidence_authority: EvidenceAuthorityState
    information_handling_authority: InformationHandlingAuthorityState
    information_class: InformationClass
    validation_passed: bool
    reason_codes: tuple[str, ...] = ()
    decisions: tuple[AuthorityDecisionEnvelope, ...] = field(default_factory=tuple)
    freshness_status: str = "NOT_ASSESSED"

    @property
    def authorized(self) -> bool:
        return (
            self.evidence_authority is EvidenceAuthorityState.APPROVED
            and self.information_handling_authority is InformationHandlingAuthorityState.APPROVED
            and self.validation_passed
            and self.information_class is not InformationClass.UNKNOWN
        )


# The resolution used when no trusted resolver is configured: nothing is authorised.
UNRESOLVED = ClaimAuthorityResolution(
    evidence_authority=EvidenceAuthorityState.UNKNOWN,
    information_handling_authority=InformationHandlingAuthorityState.UNKNOWN,
    information_class=InformationClass.UNKNOWN,
    validation_passed=False,
    reason_codes=("NO_INDEPENDENT_AUTHORITY_RESOLVER",),
)


def _input_state_hash(claim: ClaimRecord, scope: RuleScope) -> str:
    material = {
        "claim": claim.model_dump(mode="json"),
        "scope": scope.model_dump(mode="json"),
    }
    canonical = json.dumps(material, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _envelope_fields(
    *,
    dimension_label: str,
    claim: ClaimRecord,
    scope: RuleScope,
    scoped: ScopedDecision,
    policy_id: str,
    policy_digest: str,
    trace_ref: str,
) -> dict[str, object]:
    allow = scoped.result is DecisionResult.ALLOW
    reason_codes: tuple[str, ...] = () if allow else (scoped.reason.value, *scoped.matched_rule_ids)
    return dict(
        decision_id=str(uuid.uuid4()),
        subject_ref=claim.claim_id,
        scope=f"{dimension_label}:{claim.claim_id}",
        policy_ref=policy_id,
        policy_digest=policy_digest,
        input_state_hash=_input_state_hash(claim, scope),
        authority_source_ref=(f"authority-policy:{policy_id}@{policy_digest[:16]}" if allow else None),
        evidence_refs=(scoped.evidence_requirements if allow else ()),
        observed_at=datetime.now(timezone.utc),
        result=scoped.result,
        reason_codes=reason_codes,
        trace_ref=trace_ref,
    )


def _evidence_state(scoped: ScopedDecision) -> EvidenceAuthorityState:
    if scoped.result is DecisionResult.ALLOW:
        return EvidenceAuthorityState.APPROVED
    if scoped.reason is ScopedDecisionReason.PROHIBITED_BY_RULE:
        return EvidenceAuthorityState.DENIED
    return EvidenceAuthorityState.UNKNOWN


def _information_state(scoped: ScopedDecision) -> InformationHandlingAuthorityState:
    if scoped.result is DecisionResult.ALLOW:
        return InformationHandlingAuthorityState.APPROVED
    if scoped.reason is ScopedDecisionReason.PROHIBITED_BY_RULE:
        return InformationHandlingAuthorityState.DENIED
    return InformationHandlingAuthorityState.UNKNOWN


class AuthorityResolver:
    """Resolve claim-scoped authority from the trusted A1 policies."""

    version = "medical-ai-authority-resolver-a2-v0.1"

    def __init__(self) -> None:
        self._evidence = compile_authority_policy(_EVIDENCE_POLICY)
        self._information = compile_authority_policy(_INFORMATION_POLICY)
        self._data_plane = compile_authority_policy(_DATA_PLANE_POLICY)
        self._aggregation = compile_aggregation_policy(_AGGREGATION_POLICY)

    def resolve_claim_authority(
        self,
        claim: ClaimRecord,
        *,
        source_class: str,
        public_non_phi: bool,
        source_records: Sequence[SourceRecord],
        trace_ref: str,
    ) -> ClaimAuthorityResolution:
        reasons: list[str] = []
        a1_source_class = _SOURCE_CLASS.get(source_class, SourceClass.UNKNOWN)
        claim_type = _CLAIM_TYPE.get(source_class, ClaimType.UNKNOWN)
        component = _COMPONENT.get(source_class)
        purpose = _PURPOSE.get(source_class)
        # Freshness is derived from each source's explicit assessment, worst across the
        # claim's sources. A missing assessment is UNKNOWN, never silently CURRENT.
        freshness = self._claim_freshness(source_records)
        freshness_status = _FRESHNESS_STATUS[freshness]
        # Trust root: every source must carry a verifiable source-version record. A
        # well-formed reference string is not authority. A failure here makes evidence
        # authority UNKNOWN (absent), distinct from a policy DENY on freshness.
        record_failure = self._verify_source_version_records(source_records)
        info_class = (
            InformationClassification.PUBLIC_EVIDENCE if public_non_phi else InformationClassification.UNKNOWN
        )
        operation = AuthorityOperation.RETRIEVE_PUBLIC_EVIDENCE
        decisions: list[AuthorityDecisionEnvelope] = []

        # 1. Evidence authority.
        evidence_scope = RuleScope(
            claim_type=claim_type,
            jurisdiction=claim.jurisdiction or "INTERNATIONAL",
            population_context=claim.population or "UNSPECIFIED",
            source_class=a1_source_class,
            freshness=freshness,
            operation=operation,
            consequence=claim.consequence_level,
        )
        evidence = evaluate_scope(self._evidence, evidence_scope)
        if record_failure is not None:
            # No independently verified source-version record. Resolve to UNKNOWN by
            # replacing the policy decision with a NO_MATCHING_RULE denial (which maps
            # to UNKNOWN, not DENIED), so it surfaces as EVIDENCE_AUTHORITY_UNKNOWN.
            evidence = ScopedDecision(
                result=DecisionResult.DENY,
                reason=ScopedDecisionReason.NO_MATCHING_RULE,
                policy_id=self._evidence.policy_id,
                policy_digest=self._evidence.policy_digest,
                matched_rule_ids=(record_failure,),
            )
        evidence_state = _evidence_state(evidence)
        evidence_envelope = _envelope_fields(
            dimension_label="evidence-authority", claim=claim, scope=evidence_scope, scoped=evidence,
            policy_id=self._evidence.policy_id, policy_digest=self._evidence.policy_digest, trace_ref=trace_ref,
        )
        evidence_envelope.update(
            claim_evidence_link_ref=f"claim-evidence:{claim.claim_id}",
            source_version_ref=f"source-version:{source_class}:{claim.claim_id}",
            claim_type=claim_type,
            context_ref=f"context:{claim.claim_id}",
            permitted_operations=((operation,) if evidence.result is DecisionResult.ALLOW else ()),
        )
        decisions.append(EvidenceAuthorityDecision.model_validate(evidence_envelope))
        if evidence_state is not EvidenceAuthorityState.APPROVED:
            reasons.append(f"EVIDENCE_{evidence.reason.value}")

        # 2. Information-handling authority.
        if component is None or purpose is None:
            information_state = InformationHandlingAuthorityState.UNKNOWN
            reasons.append("INFORMATION_UNMAPPED_SOURCE_CLASS")
        else:
            information_scope = RuleScope(
                component=component, information_class=info_class, operation=operation,
                purpose=purpose, environment=_ENVIRONMENT,
            )
            information = evaluate_scope(self._information, information_scope)
            information_state = _information_state(information)
            info_envelope = _envelope_fields(
                dimension_label="information-handling", claim=claim, scope=information_scope, scoped=information,
                policy_id=self._information.policy_id, policy_digest=self._information.policy_digest, trace_ref=trace_ref,
            )
            info_envelope.update(
                component_ref=component, information_class=info_class, operation=operation,
                purpose=purpose, environment=_ENVIRONMENT,
            )
            decisions.append(InformationHandlingDecision.model_validate(info_envelope))
            if information_state is not InformationHandlingAuthorityState.APPROVED:
                reasons.append(f"INFORMATION_{information.reason.value}")

        # 3. Data-plane transition.
        data_plane_allowed = False
        if purpose is not None:
            data_plane_scope = RuleScope(
                from_plane=DataPlane.EVIDENCE, to_plane=DataPlane.EVIDENCE,
                information_class=info_class, operation=operation, purpose=purpose,
            )
            data_plane = evaluate_scope(self._data_plane, data_plane_scope)
            data_plane_allowed = data_plane.result is DecisionResult.ALLOW
            dp_envelope = _envelope_fields(
                dimension_label="data-plane-transition", claim=claim, scope=data_plane_scope, scoped=data_plane,
                policy_id=self._data_plane.policy_id, policy_digest=self._data_plane.policy_digest, trace_ref=trace_ref,
            )
            dp_envelope.update(
                from_plane=DataPlane.EVIDENCE, to_plane=DataPlane.EVIDENCE, information_class=info_class,
                operation=operation, purpose=purpose, component_ref=(component or "unmapped"),
            )
            decisions.append(DataPlaneTransitionDecision.model_validate(dp_envelope))
            if not data_plane_allowed:
                reasons.append(f"DATA_PLANE_{data_plane.reason.value}")
        else:
            reasons.append("DATA_PLANE_UNMAPPED_SOURCE_CLASS")

        # 4. Aggregation: every mandatory dimension resolved and allowed.
        aggregate = resolve_required_dimensions(
            self._aggregation, tuple(self._aggregation.required_dimensions)
        )
        all_allowed = (
            evidence_state is EvidenceAuthorityState.APPROVED
            and information_state is InformationHandlingAuthorityState.APPROVED
            and data_plane_allowed
            and aggregate.result is DecisionResult.ALLOW
        )
        resolved_info_class = (
            InformationClass.PUBLIC if (public_non_phi and data_plane_allowed) else InformationClass.UNKNOWN
        )
        return ClaimAuthorityResolution(
            evidence_authority=evidence_state,
            information_handling_authority=information_state,
            information_class=resolved_info_class,
            validation_passed=all_allowed,
            reason_codes=tuple(reasons),
            decisions=tuple(decisions),
            freshness_status=freshness_status,
        )

    @staticmethod
    def _claim_freshness(source_records: Sequence[SourceRecord]) -> FreshnessState:
        """Worst freshness across a claim's sources; missing/empty is UNKNOWN."""
        if not source_records:
            return FreshnessState.UNKNOWN
        worst = FreshnessState.CURRENT
        for source in source_records:
            assessment = source.freshness
            state = assessment.state if assessment is not None else FreshnessState.UNKNOWN
            if _FRESHNESS_RANK[state] > _FRESHNESS_RANK[worst]:
                worst = state
        return worst

    @staticmethod
    def _verify_source_version_records(source_records: Sequence[SourceRecord]) -> str | None:
        """Verify each source's version record; return a reason string on first failure.

        Checks that the record exists, its ``source_id`` matches the source, every
        required field is present and non-blank, and ``content_sha256`` recomputes
        exactly. Returns ``None`` only when every source passes.
        """
        if not source_records:
            return "SOURCE_VERSION_RECORD_MISSING"
        for source in source_records:
            record = source.version_record
            if record is None:
                return "SOURCE_VERSION_RECORD_MISSING"
            if record.source_id != source.source_id:
                return "SOURCE_VERSION_RECORD_SOURCE_MISMATCH"
            required = (
                record.source_id,
                record.upstream_record_id,
                record.upstream_version,
                record.connector_name,
                record.connector_version,
                record.content_sha256,
            )
            if any((not value) or value != value.strip() for value in required):
                return "SOURCE_VERSION_RECORD_FIELD_BLANK"
            expected = source_version_content_sha256(
                source_id=record.source_id,
                upstream_record_id=record.upstream_record_id,
                upstream_version=record.upstream_version,
            )
            if record.content_sha256 != expected:
                return "SOURCE_VERSION_RECORD_DIGEST_MISMATCH"
        return None
