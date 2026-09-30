from __future__ import annotations

from collections.abc import Iterable

from .schemas import (
    AuthorityState,
    DataPlane,
    DependencyDimension,
    DownstreamInfluenceState,
    InfluenceDecision,
    InfluenceDecisionStatus,
    InfluenceRequest,
    InfluenceSubject,
    InformationClass,
    RevocationResult,
)


class InfluenceController:
    """Machine-enforced gate for whether an object may influence medical output.

    The controller keeps authority dimensions independent, fails closed on unknown
    state or transitions, emits an inspectable decision artefact, and records typed
    dependencies so revocation propagates only through the dimension that changed.
    """

    policy_version = "medical-ai-influence-v0.2"

    def __init__(self, allowed_transitions: Iterable[tuple[DataPlane, DataPlane]] | None = None):
        defaults = {
            (DataPlane.EVIDENCE, DataPlane.EVIDENCE),
            (DataPlane.TERMINOLOGY, DataPlane.TERMINOLOGY),
            (DataPlane.CLINICAL, DataPlane.CLINICAL),
            (DataPlane.RESEARCH, DataPlane.RESEARCH),
        }
        self.allowed_transitions = set(defaults if allowed_transitions is None else allowed_transitions)
        self._subjects: dict[str, InfluenceSubject] = {}
        self._conflicted_subjects: set[str] = set()
        self._decisions: dict[str, InfluenceDecision] = {}
        self._dependencies = []
        self._downstream_states: dict[str, DownstreamInfluenceState] = {}

    @property
    def decisions(self) -> list[InfluenceDecision]:
        return list(self._decisions.values())

    def authorize(self, request: InfluenceRequest) -> InfluenceDecision:
        object_id = request.subject.object_id
        subject = self._subjects.get(object_id)
        snapshot_conflict = False
        if subject is None:
            subject = request.subject.model_copy(deep=True)
            self._subjects[object_id] = subject
        elif subject.model_dump() != request.subject.model_dump():
            snapshot_conflict = True
            self._conflicted_subjects.add(object_id)
            subject.evidence_authority = self._restrict_authority(
                subject.evidence_authority, request.subject.evidence_authority
            )
            subject.information_handling_authority = self._restrict_authority(
                subject.information_handling_authority,
                request.subject.information_handling_authority,
            )
            self._invalidate_subject_dependents(object_id)

        reasons: list[str] = []
        if snapshot_conflict or object_id in self._conflicted_subjects:
            reasons.append("SUBJECT_SNAPSHOT_CONFLICT")
        transition = request.transition

        if subject.data_plane != transition.source_plane:
            reasons.append("SUBJECT_PLANE_MISMATCH")
        if transition.information_class == InformationClass.UNKNOWN:
            reasons.append("INFORMATION_CLASS_UNKNOWN")
        if (transition.source_plane, transition.target_plane) not in self.allowed_transitions:
            reasons.append("TRANSITION_NOT_ALLOWED")
        if subject.evidence_authority != AuthorityState.APPROVED:
            reasons.append(f"EVIDENCE_AUTHORITY_{subject.evidence_authority.value}")
        if subject.information_handling_authority != AuthorityState.APPROVED:
            reasons.append(
                f"INFORMATION_HANDLING_AUTHORITY_{subject.information_handling_authority.value}"
            )
        if not subject.provenance_complete:
            reasons.append("PROVENANCE_INCOMPLETE")
        if not subject.validation_passed:
            reasons.append("VALIDATION_NOT_PASSED")
        if not subject.safety_passed:
            reasons.append("SAFETY_NOT_PASSED")
        if not subject.monitoring_enabled:
            reasons.append("MONITORING_NOT_ENABLED")

        allowed = not reasons
        decision = InfluenceDecision(
            request_id=request.request_id,
            object_id=subject.object_id,
            proposition_id=request.proposition_id,
            status=InfluenceDecisionStatus.ALLOW if allowed else InfluenceDecisionStatus.DENY,
            allowed=allowed,
            reasons=reasons,
            policy_version=self.policy_version,
            evaluated_dimensions={
                "evidence_authority": subject.evidence_authority.value,
                "information_handling_authority": subject.information_handling_authority.value,
                "data_plane": subject.data_plane.value,
                "information_class": transition.information_class.value,
                "provenance": "PASS" if subject.provenance_complete else "FAIL",
                "validation": "PASS" if subject.validation_passed else "FAIL",
                "safety": "PASS" if subject.safety_passed else "FAIL",
                "monitoring": "PASS" if subject.monitoring_enabled else "FAIL",
            },
            transition=transition,
        )
        self._decisions[decision.decision_id] = decision
        if allowed:
            self._record_dependencies(request)
        return decision

    @staticmethod
    def _restrict_authority(current: AuthorityState, incoming: AuthorityState) -> AuthorityState:
        restriction = {
            AuthorityState.APPROVED: 0,
            AuthorityState.UNKNOWN: 1,
            AuthorityState.DENIED: 2,
            AuthorityState.REVOKED: 3,
        }
        return max((current, incoming), key=restriction.__getitem__)

    def _invalidate_subject_dependents(self, object_id: str) -> None:
        for edge in self._dependencies:
            if edge.upstream_object_id != object_id:
                continue
            state = self._downstream_states.setdefault(
                edge.downstream_object_id,
                DownstreamInfluenceState(object_id=edge.downstream_object_id),
            )
            state.active = False
            reason = f"UPSTREAM_SUBJECT_SNAPSHOT_CONFLICT:{object_id}"
            if reason not in state.invalidation_reasons:
                state.invalidation_reasons.append(reason)

    def update_subject(self, subject: InfluenceSubject) -> None:
        """Apply an authoritative snapshot only when its revision increases."""
        current = self._subjects.get(subject.object_id)
        if current is not None and subject.revision <= current.revision:
            raise ValueError("Authoritative subject updates require a higher revision")
        self._subjects[subject.object_id] = subject.model_copy(deep=True)
        self._conflicted_subjects.discard(subject.object_id)

    def _record_dependencies(self, request: InfluenceRequest) -> None:
        from .schemas import DependencyEdge

        state = self._downstream_states.setdefault(
            request.proposition_id,
            DownstreamInfluenceState(object_id=request.proposition_id),
        )
        if not state.active:
            return
        existing = {
            (edge.upstream_object_id, edge.downstream_object_id, edge.dimension)
            for edge in self._dependencies
        }
        for dimension in request.required_dependency_dimensions:
            key = (request.subject.object_id, request.proposition_id, dimension)
            if key in existing:
                continue
            self._dependencies.append(DependencyEdge(
                upstream_object_id=request.subject.object_id,
                downstream_object_id=request.proposition_id,
                dimension=dimension,
            ))

    def revoke_authority(
        self,
        object_id: str,
        dimension: DependencyDimension,
    ) -> RevocationResult:
        subject = self._subjects.get(object_id)
        if subject is None:
            raise KeyError(f"Unknown influence subject: {object_id}")
        if dimension == DependencyDimension.EVIDENCE_AUTHORITY:
            subject.evidence_authority = AuthorityState.REVOKED
        elif dimension == DependencyDimension.INFORMATION_HANDLING_AUTHORITY:
            subject.information_handling_authority = AuthorityState.REVOKED
        else:
            raise ValueError("Only authority dimensions can be revoked with revoke_authority")

        impacted = {
            edge.downstream_object_id
            for edge in self._dependencies
            if edge.upstream_object_id == object_id and edge.dimension == dimension
        }
        related = {
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
            reason = f"UPSTREAM_{dimension.value}_REVOKED:{object_id}"
            if reason not in state.invalidation_reasons:
                state.invalidation_reasons.append(reason)
        return RevocationResult(
            upstream_object_id=object_id,
            dimension=dimension,
            invalidated_downstream_ids=sorted(impacted),
            unaffected_downstream_ids=sorted(related - impacted),
        )

    def get_downstream_state(self, object_id: str) -> DownstreamInfluenceState | None:
        state = self._downstream_states.get(object_id)
        return state.model_copy(deep=True) if state is not None else None

    def get_subject(self, object_id: str) -> InfluenceSubject | None:
        subject = self._subjects.get(object_id)
        return subject.model_copy(deep=True) if subject is not None else None
