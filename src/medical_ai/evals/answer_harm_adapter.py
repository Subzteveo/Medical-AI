from __future__ import annotations

from collections.abc import Iterable, Mapping

from medical_ai.schemas import AnswerStatus, ConsequenceLevel, EvidenceAnswer

from .clinical_harm import ClinicalHarmScore, HarmSeverity, score_clinical_actions


_SUPPORTED = frozenset(
    {
        AnswerStatus.ANSWER_SUPPORTED,
        AnswerStatus.ANSWER_SUPPORTED_WITH_QUALIFICATIONS,
    }
)


def answer_action_ids(answer: EvidenceAnswer) -> set[str]:
    """Project an observable EvidenceAnswer into deterministic evaluation actions.

    The adapter uses delivered output, trace, provenance and authorization state
    only. It does not infer hidden model reasoning or create clinical authority.
    """
    actions = {f"status/{answer.status.value}"}

    if answer.status in _SUPPORTED:
        actions.add("control/supported")
    else:
        actions.add("control/abstained")

    if answer.claims:
        actions.add("output/claims")
    if answer.sources:
        actions.add("output/sources")
        if all(source.provenance_complete for source in answer.sources):
            actions.add("evidence/provenance-complete")
    if answer.evidence_objects:
        actions.add("output/evidence")
    if answer.citation_mappings:
        actions.add("output/citations")
        if all(mapping.verified for mapping in answer.citation_mappings):
            actions.add("output/citations-verified")
    if answer.influence_decisions and all(
        decision.allowed for decision in answer.influence_decisions
    ):
        actions.add("authority/claims-authorized")

    query_plan = answer.trace.query_plan
    if query_plan.patient_specific:
        actions.add("query/patient-specific")
    if query_plan.consequence_level == ConsequenceLevel.HIGH:
        actions.add("query/high-consequence")

    for source_class in query_plan.required_source_classes:
        actions.add(f"source-class/{source_class}")
    for flag in answer.trace.safety_flags:
        actions.add(f"safety/{flag}")

    return actions


def score_evidence_answer(
    answer: EvidenceAnswer,
    *,
    required_actions: Mapping[str, HarmSeverity],
    harmful_actions: Mapping[str, HarmSeverity] | None = None,
    additional_observed_actions: Iterable[str] = (),
) -> ClinicalHarmScore:
    """Score one observable Medical-AI answer against an explicit evaluation rubric."""
    observed = answer_action_ids(answer)
    observed.update(
        action.strip() for action in additional_observed_actions if action.strip()
    )
    return score_clinical_actions(
        required_actions=required_actions,
        observed_actions=observed,
        harmful_actions=harmful_actions,
    )
