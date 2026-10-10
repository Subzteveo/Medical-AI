from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Iterable

from .schemas import (
    AuthorizedClaimView,
    ClaimRecord,
    DataPlane,
    DependencyDimension,
    DependencyEdge,
    DownstreamInfluenceState,
    EvidenceAuthorityState,
    GateStatus,
    InfluenceAuthorization,
    InfluenceAuthorizationState,
    InfluenceDecision,
    InfluenceDecisionStatus,
    InfluenceEvaluation,
    InfluenceReasonCode,
    InfluenceRequest,
    InfluenceSubject,
    InfluenceObjectType,
    InformationClass,
    InformationHandlingAuthorityState,
    InvalidationReasonCode,
    InvalidationRecord,
    RevocationResult,
    TransitionAuthorization,
    TransitionDecision,
    VerificationStatus,
)


class InfluenceController:
    """Machine-enforced gate for whether an object may influence medical output.

    The controller keeps authority dimensions independent, fails closed on unknown
    state or transitions, emits a typed authorization capability only for ALLOW
    decisions, and records typed dependencies so revocation propagates only through
    the dimension that changed.
    """

    policy_version = "medical-ai-influence-v0.2-typesafe"

    def __init__(
        self,
        allowed_transitions: Iterable[tuple[DataPlane, DataPlane]] | None = None,
    ) -> None:
        defaults: set[tuple[DataPlane, DataPlane]] = {
            (DataPlane.EVIDENCE, DataPlane.EVIDENCE),
            (DataPlane.TERMINOLOGY, DataPlane.TERMINOLOGY),
            (DataPlane.CLINICAL, DataPlane.CLINICAL),
            (DataPlane.RESEARCH, DataPlane.RESEARCH),
        }
        self.allowed_transitions: set[tuple[DataPlane, DataPlane]] = set(
            defaults if allowed_transitions is None else allowed_transitions
        )
        self._subjects: dict[str, InfluenceSubject] = {}
        self._conflicted_subjects: set[str] = set()
        self._decisions: dict[str, InfluenceDecision] = {}
        self._authorizations: dict[str, InfluenceAuthorization] = {}
        self._claim_digests: dict[str, str] = {}
        self._authorization_revisions: dict[str, int] = {}
        self._dependencies: list[DependencyEdge] = []
        self._downstream_states: dict[str, DownstreamInfluenceState] = {}

    @property
    def decisions(self) -> list[InfluenceDecision]:
        return list(self._decisions.values())

    def authorize(
        self, request: InfluenceRequest, *, claim: ClaimRecord | None = None
    ) -> InfluenceDecision:
        if claim is not None and (
            request.subject.object_type != InfluenceObjectType.CLAIM_RECORD
            or claim.claim_id != request.subject.object_id
            or claim.verification_status != VerificationStatus.PASS
        ):
            raise ValueError("Claim authorization requires a matching verified claim snapshot")
        object_id = request.subject.object_id
        subject = self._subjects.get(object_id)
        snapshot_conflict = False
        if subject is None:
            subject = request.subject.model_copy(deep=True)
            self._subjects[object_id] = subject
        elif subject.model_dump() != request.subject.model_dump():
            snapshot_conflict = True
            self._conflicted_subjects.add(object_id)
            subject.evidence_authority = self._restrict_evidence_authority(
                subject.evidence_authority,
                request.subject.evidence_authority,
            )
            subject.information_handling_authority = self._restrict_information_authority(
                subject.information_handling_authority,
                request.subject.information_handling_authority,
            )
            self._invalidate_subject_dependents(object_id)
            self._revoke_subject_authorizations(object_id)

        reasons: list[InfluenceReasonCode] = []
        if snapshot_conflict or object_id in self._conflicted_subjects:
            reasons.append(InfluenceReasonCode.SUBJECT_SNAPSHOT_CONFLICT)

        transition = request.transition
        transition_allowed = (
            subject.data_plane == transition.source_plane
            and transition.information_class != InformationClass.UNKNOWN
            and (transition.source_plane, transition.target_plane) in self.allowed_transitions
        )
        if subject.data_plane != transition.source_plane:
            reasons.append(InfluenceReasonCode.SUBJECT_PLANE_MISMATCH)
        if transition.information_class == InformationClass.UNKNOWN:
            reasons.append(InfluenceReasonCode.INFORMATION_CLASS_UNKNOWN)
        if (transition.source_plane, transition.target_plane) not in self.allowed_transitions:
            reasons.append(InfluenceReasonCode.TRANSITION_NOT_ALLOWED)

        if subject.evidence_authority != EvidenceAuthorityState.APPROVED:
            reasons.append(self._evidence_authority_reason(subject.evidence_authority))
        if (
            subject.information_handling_authority
            != InformationHandlingAuthorityState.APPROVED
        ):
            reasons.append(
                self._information_handling_reason(
                    subject.information_handling_authority
                )
            )
        if not subject.provenance_complete:
            reasons.append(InfluenceReasonCode.PROVENANCE_INCOMPLETE)
        if not subject.validation_passed:
            reasons.append(InfluenceReasonCode.VALIDATION_NOT_PASSED)
        if not subject.safety_passed:
            reasons.append(InfluenceReasonCode.SAFETY_NOT_PASSED)
        if not subject.monitoring_enabled:
            reasons.append(InfluenceReasonCode.MONITORING_NOT_ENABLED)

        allowed = not reasons
        decision_id = str(uuid.uuid4())
        transition_authorization = TransitionAuthorization(
            transition=transition,
            decision=TransitionDecision.ALLOW if transition_allowed else TransitionDecision.DENY,
            policy_version=self.policy_version,
        )
        evaluation = InfluenceEvaluation(
            evidence_authority=subject.evidence_authority,
            information_handling_authority=subject.information_handling_authority,
            data_plane=subject.data_plane,
            information_class=transition.information_class,
            provenance=GateStatus.PASS if subject.provenance_complete else GateStatus.FAIL,
            validation=GateStatus.PASS if subject.validation_passed else GateStatus.FAIL,
            safety=GateStatus.PASS if subject.safety_passed else GateStatus.FAIL,
            monitoring=GateStatus.PASS if subject.monitoring_enabled else GateStatus.FAIL,
        )
        authorization: InfluenceAuthorization | None = None
        if allowed:
            authorization = InfluenceAuthorization(
                decision_id=decision_id,
                object_id=subject.object_id,
                proposition_id=request.proposition_id,
                required_dependency_dimensions=list(
                    request.required_dependency_dimensions
                ),
            )
            self._authorizations[authorization.authorization_id] = authorization
            self._authorization_revisions[authorization.authorization_id] = subject.revision
            if claim is not None:
                self._claim_digests[authorization.authorization_id] = self._claim_digest(claim)

        decision = InfluenceDecision(
            decision_id=decision_id,
            request_id=request.request_id,
            object_id=subject.object_id,
            proposition_id=request.proposition_id,
            status=(
                InfluenceDecisionStatus.ALLOW
                if allowed
                else InfluenceDecisionStatus.DENY
            ),
            reasons=reasons,
            policy_version=self.policy_version,
            evaluated_dimensions=evaluation,
            transition_authorization=transition_authorization,
            authorization=authorization,
        )
        self._decisions[decision.decision_id] = decision
        if allowed:
            self._record_dependencies(request)
        return decision

    @staticmethod
    def _claim_digest(claim: ClaimRecord) -> str:
        """Hash the entire canonical claim, not just its reusable identifier."""
        serialized = json.dumps(
            claim.model_dump(mode="json"), sort_keys=True, separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(serialized).hexdigest()

    def validate_authorized_claim_view(self, view: AuthorizedClaimView) -> None:
        """Revalidate at the point of output against controller-owned live state."""
        current = self._authorizations.get(view.authorization.authorization_id)
        if current is None or current.state != InfluenceAuthorizationState.ACTIVE:
            raise ValueError("Authorization is revoked or not registered as active")
        if view.authorization.model_dump() != current.model_dump():
            raise ValueError("Authorization does not match the registered capability")
        if current.object_id != view.claim.claim_id:
            raise ValueError("Authorization capability does not belong to this claim")
        digest = self._claim_digests.get(current.authorization_id)
        if digest is None or digest != self._claim_digest(view.claim):
            raise ValueError("Claim snapshot digest mismatch or missing authorization")
        subject = self._subjects.get(current.object_id)
        if (
            subject is None
            or current.object_id in self._conflicted_subjects
            or self._authorization_revisions.get(current.authorization_id) != subject.revision
            or subject.evidence_authority != EvidenceAuthorityState.APPROVED
            or subject.information_handling_authority != InformationHandlingAuthorityState.APPROVED
            or not subject.provenance_complete
            or not subject.validation_passed
            or not subject.safety_passed
            or not subject.monitoring_enabled
        ):
            raise ValueError("Authorization is stale or authority is no longer approved")
        decision = self._decisions.get(current.decision_id)
        if (
            decision is None
            or decision.status != InfluenceDecisionStatus.ALLOW
            or decision.authorization is None
            or decision.authorization.authorization_id != current.authorization_id
            or decision.policy_version != self.policy_version
            or decision.transition_authorization.transition.source_plane != subject.data_plane
            or (
                decision.transition_authorization.transition.source_plane,
                decision.transition_authorization.transition.target_plane,
            ) not in self.allowed_transitions
        ):
            raise ValueError("Authorization is not backed by a current controller decision")

    def build_authorized_claim_view(
        self,
        claim: ClaimRecord,
        decision: InfluenceDecision,
    ) -> AuthorizedClaimView:
        stored = self._decisions.get(decision.decision_id)
        if stored is None or stored.status != InfluenceDecisionStatus.ALLOW:
            raise ValueError("Claim rendering requires a stored ALLOW decision")
        authorization = stored.authorization
        if authorization is None:
            raise ValueError("ALLOW decision is missing its authorization capability")
        current = self._authorizations.get(authorization.authorization_id)
        if current is None or current.state != InfluenceAuthorizationState.ACTIVE:
            raise ValueError("Claim rendering requires an active authorization capability")
        if current.object_id != claim.claim_id:
            raise ValueError("Authorization capability does not belong to this claim")
        view = AuthorizedClaimView(claim=claim.model_copy(deep=True), authorization=current)
        self.validate_authorized_claim_view(view)
        return view

    @staticmethod
    def _restrict_evidence_authority(
        current: EvidenceAuthorityState,
        incoming: EvidenceAuthorityState,
    ) -> EvidenceAuthorityState:
        rank: dict[EvidenceAuthorityState, int] = {
            EvidenceAuthorityState.APPROVED: 0,
            EvidenceAuthorityState.UNKNOWN: 1,
            EvidenceAuthorityState.DENIED: 2,
            EvidenceAuthorityState.REVOKED: 3,
        }
        return current if rank[current] >= rank[incoming] else incoming

    @staticmethod
    def _restrict_information_authority(
        current: InformationHandlingAuthorityState,
        incoming: InformationHandlingAuthorityState,
    ) -> InformationHandlingAuthorityState:
        rank: dict[InformationHandlingAuthorityState, int] = {
            InformationHandlingAuthorityState.APPROVED: 0,
            InformationHandlingAuthorityState.UNKNOWN: 1,
            InformationHandlingAuthorityState.DENIED: 2,
            InformationHandlingAuthorityState.REVOKED: 3,
        }
        return current if rank[current] >= rank[incoming] else incoming

    @staticmethod
    def _evidence_authority_reason(
        state: EvidenceAuthorityState,
    ) -> InfluenceReasonCode:
        if state == EvidenceAuthorityState.DENIED:
            return InfluenceReasonCode.EVIDENCE_AUTHORITY_DENIED
        if state == EvidenceAuthorityState.UNKNOWN:
            return InfluenceReasonCode.EVIDENCE_AUTHORITY_UNKNOWN
        if state == EvidenceAuthorityState.REVOKED:
            return InfluenceReasonCode.EVIDENCE_AUTHORITY_REVOKED
        raise ValueError("Approved evidence authority has no denial reason")

    @staticmethod
    def _information_handling_reason(
        state: InformationHandlingAuthorityState,
    ) -> InfluenceReasonCode:
        if state == InformationHandlingAuthorityState.DENIED:
            return InfluenceReasonCode.INFORMATION_HANDLING_AUTHORITY_DENIED
        if state == InformationHandlingAuthorityState.UNKNOWN:
            return InfluenceReasonCode.INFORMATION_HANDLING_AUTHORITY_UNKNOWN
        if state == InformationHandlingAuthorityState.REVOKED:
            return InfluenceReasonCode.INFORMATION_HANDLING_AUTHORITY_REVOKED
        raise ValueError("Approved information-handling authority has no denial reason")

    def _invalidate_subject_dependents(self, object_id: str) -> None:
        for edge in self._dependencies:
            if edge.upstream_object_id != object_id:
                continue
            state = self._downstream_states.setdefault(
                edge.downstream_object_id,
                DownstreamInfluenceState(object_id=edge.downstream_object_id),
            )
            state.active = False
            record = InvalidationRecord(
                code=InvalidationReasonCode.SUBJECT_SNAPSHOT_CONFLICT,
                upstream_object_id=object_id,
                dimension=edge.dimension,
            )
            if record not in state.invalidation_reasons:
                state.invalidation_reasons.append(record)

    def _revoke_subject_authorizations(self, object_id: str) -> None:
        for authorization in self._authorizations.values():
            if authorization.object_id == object_id:
                self._authorizations[authorization.authorization_id] = authorization.model_copy(
                    update={"state": InfluenceAuthorizationState.REVOKED}
                )

    def _revoke_authorizations_for_dimension(
        self,
        object_id: str,
        dimension: DependencyDimension,
    ) -> None:
        for authorization in self._authorizations.values():
            if (
                authorization.object_id == object_id
                and dimension in authorization.required_dependency_dimensions
            ):
                self._authorizations[authorization.authorization_id] = authorization.model_copy(
                    update={"state": InfluenceAuthorizationState.REVOKED}
                )

    def update_subject(self, subject: InfluenceSubject) -> None:
        """Apply an authoritative snapshot only when its revision increases."""
        current = self._subjects.get(subject.object_id)
        if current is not None and subject.revision <= current.revision:
            raise ValueError("Authoritative subject updates require a higher revision")
        self._subjects[subject.object_id] = subject.model_copy(deep=True)
        self._conflicted_subjects.discard(subject.object_id)
        if current is not None:
            # Every earlier capability was bound to a previous authoritative revision.
            self._revoke_subject_authorizations(subject.object_id)
            if (
                current.evidence_authority == EvidenceAuthorityState.APPROVED
                and subject.evidence_authority != EvidenceAuthorityState.APPROVED
            ):
                self._invalidate_dimension_dependents(
                    subject.object_id, DependencyDimension.EVIDENCE_AUTHORITY
                )
            if (
                current.information_handling_authority == InformationHandlingAuthorityState.APPROVED
                and subject.information_handling_authority != InformationHandlingAuthorityState.APPROVED
            ):
                self._invalidate_dimension_dependents(
                    subject.object_id, DependencyDimension.INFORMATION_HANDLING_AUTHORITY
                )

    def _invalidate_dimension_dependents(
        self, object_id: str, dimension: DependencyDimension
    ) -> None:
        for edge in self._dependencies:
            if edge.upstream_object_id != object_id or edge.dimension != dimension:
                continue
            state = self._downstream_states.setdefault(
                edge.downstream_object_id,
                DownstreamInfluenceState(object_id=edge.downstream_object_id),
            )
            state.active = False
            record = InvalidationRecord(
                code=InvalidationReasonCode.AUTHORITY_REVOKED,
                upstream_object_id=object_id,
                dimension=dimension,
            )
            if record not in state.invalidation_reasons:
                state.invalidation_reasons.append(record)

    def _record_dependencies(self, request: InfluenceRequest) -> None:
        state = self._downstream_states.setdefault(
            request.proposition_id,
            DownstreamInfluenceState(object_id=request.proposition_id),
        )
        if not state.active:
            return
        existing: set[tuple[str, str, DependencyDimension]] = {
            (edge.upstream_object_id, edge.downstream_object_id, edge.dimension)
            for edge in self._dependencies
        }
        for dimension in request.required_dependency_dimensions:
            key = (request.subject.object_id, request.proposition_id, dimension)
            if key in existing:
                continue
            self._dependencies.append(
                DependencyEdge(
                    upstream_object_id=request.subject.object_id,
                    downstream_object_id=request.proposition_id,
                    dimension=dimension,
                )
            )

    def revoke_authority(
        self,
        object_id: str,
        dimension: DependencyDimension,
    ) -> RevocationResult:
        subject = self._subjects.get(object_id)
        if subject is None:
            raise KeyError(f"Unknown influence subject: {object_id}")
        if dimension == DependencyDimension.EVIDENCE_AUTHORITY:
            subject.evidence_authority = EvidenceAuthorityState.REVOKED
        elif dimension == DependencyDimension.INFORMATION_HANDLING_AUTHORITY:
            subject.information_handling_authority = (
                InformationHandlingAuthorityState.REVOKED
            )
        else:
            raise ValueError(
                "Only authority dimensions can be revoked with revoke_authority"
            )

        self._revoke_authorizations_for_dimension(object_id, dimension)
        impacted: set[str] = {
            edge.downstream_object_id
            for edge in self._dependencies
            if edge.upstream_object_id == object_id and edge.dimension == dimension
        }
        related: set[str] = {
            edge.downstream_object_id
            for edge in self._dependencies
            if edge.upstream_object_id == object_id
        }
        for downstream_id in impacted:
            state = self._downstream_states.setdefault(
                downstream_id,
                DownstreamInfluenceState(object_id=downstream_id),
            )
            state.active = False
            record = InvalidationRecord(
                code=InvalidationReasonCode.AUTHORITY_REVOKED,
                upstream_object_id=object_id,
                dimension=dimension,
            )
            if record not in state.invalidation_reasons:
                state.invalidation_reasons.append(record)
        return RevocationResult(
            upstream_object_id=object_id,
            dimension=dimension,
            invalidated_downstream_ids=sorted(impacted),
            unaffected_downstream_ids=sorted(related - impacted),
        )

    def get_downstream_state(
        self,
        object_id: str,
    ) -> DownstreamInfluenceState | None:
        state = self._downstream_states.get(object_id)
        return state.model_copy(deep=True) if state is not None else None

    def get_subject(self, object_id: str) -> InfluenceSubject | None:
        subject = self._subjects.get(object_id)
        return subject.model_copy(deep=True) if subject is not None else None

    def get_authorization(
        self,
        authorization_id: str,
    ) -> InfluenceAuthorization | None:
        authorization = self._authorizations.get(authorization_id)
        return authorization.model_copy(deep=True) if authorization is not None else None
