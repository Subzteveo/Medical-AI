"""Read-only Outcome Alignment handoff for general research tasks.

This is NOT a medical verifier, a runtime agent, or an Outcome Alignment approval.
It projects only current controller-authorised, internally consistent identifiers.
Source digests are external observations; matching supplied hashes does not
authenticate the original publisher, clinical truth, or retrieval completeness.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from .renderer import render_answer
from .schemas import AnswerStatus, EvidenceAnswer

if TYPE_CHECKING:
    from .engine import EvidenceEngine

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_TASK = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9._:/-]{2,95}\Z")
_SUPPORTED = {AnswerStatus.ANSWER_SUPPORTED, AnswerStatus.ANSWER_SUPPORTED_WITH_QUALIFICATIONS}
_OUTCOME_ID = "medical-ai/research-evidence-context-continuity/v0.1-candidate"


def build_research_outcome_handoff(
    answer: EvidenceAnswer,
    *,
    engine: EvidenceEngine,
    task_id: str,
    baseline_revision: str,
    candidate_revision: str,
    expected_source_sha256: Mapping[str, str] | None = None,
    observed_source_sha256: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Project a single completed run for independent outcome evaluation.

    The caller must supply an opaque, non-patient task ID and exact Git SHAs.
    Digests, if given, are independently obtained input references rather than
    runtime-verified originals. Nothing is persisted and no capability is minted.
    This function never assigns an ACHIEVED or clinical-readiness verdict.
    """
    if not _TASK.fullmatch(task_id):
        raise ValueError("task_id must be an opaque non-content reference")
    # Git SHA-1 identifiers are 40 hex characters. Reject branch names and labels.
    if any(re.fullmatch(r"[0-9a-f]{40}", revision) is None for revision in (baseline_revision, candidate_revision)):
        raise ValueError("Both Git revisions must be exact 40-character lowercase Git SHAs")
    if (expected_source_sha256 is None) != (observed_source_sha256 is None):
        raise ValueError("Source digest comparison requires both expected and observed maps")
    for mapping in (expected_source_sha256, observed_source_sha256):
        if mapping is not None and any(not _SHA256.fullmatch(value) for value in mapping.values()):
            raise ValueError("Source digests must be lowercase SHA-256 hex")

    handoff: dict[str, Any] = {
        "schema": "medical-ai.outcome-handoff/v0.1",
        "outcome_id": _OUTCOME_ID,
        "task_id": task_id,
        "baseline_revision": baseline_revision,
        "candidate_revision": candidate_revision,
        "runtime_answer_status": answer.status.value,
        "provenance_graph": [],
        "source_ids": [],
        "authorization_decision_ids": [],
        "query_digests": [],
        "component_versions": {},
        "trace_id": None,
        "snapshot_comparison": "UNKNOWN",
        "current_authorization": "NOT_ESTABLISHED",
        "handoff_disposition": "WITHHELD",
        "transition_observability": {
            "source_bytes": "UNKNOWN",
            "internal_step_events": "UNKNOWN",
            "independent_user_result": "NOT_RUN",
        },
        "outcome_alignment_verdict": "NOT_ESTABLISHED",
        "clinical_correctness": "NOT_ESTABLISHED",
        "commercial_release": "NOT_AUTHORIZED",
    }

    try:
        checked = EvidenceAnswer.model_validate(answer.model_dump(mode="python"))
        # The controller is the *issuing* authority. Reuse its current checks
        # without calling engine.revalidate_output(), whose failure path writes
        # an audit trace and therefore is not strictly read-only.
        stored = {decision.decision_id: decision for decision in engine.influence_controller.decisions}
        views = []
        for claim in checked.claims:
            decision = next(
                d for d in checked.influence_decisions
                if d.object_id == claim.claim_id and d.allowed
            )
            current = stored.get(decision.decision_id)
            if current is None or current.model_dump() != decision.model_dump():
                raise ValueError("Detached claim decision is not the issuing current decision")
            views.append(engine.influence_controller.build_authorized_claim_view(claim, decision))
        if checked.status in _SUPPORTED:
            # A detached/synthetic answer cannot turn unrendered text into a
            # positive inspection record. The actual rendered output must match.
            expected_markdown = render_answer(
                views, checked.sources,
                trial_discovery="TRIAL_QUERY" in checked.trace.query_plan.intent,
                influence_controller=engine.influence_controller,
                evidence_objects=checked.evidence_objects,
                passages=checked.passages,
                citation_mappings=checked.citation_mappings,
            )
            if expected_markdown != checked.answer_markdown:
                raise ValueError("Original browser-facing representation changed")
    except (ValueError, StopIteration, KeyError, TypeError):
        handoff["runtime_answer_status"] = "INTEGRITY_OR_AUTHORIZATION_HOLD"
        return handoff

    handoff["runtime_answer_status"] = checked.status.value
    handoff["trace_id"] = checked.trace.trace_id
    handoff["component_versions"] = dict(checked.trace.component_versions)

    if checked.status not in _SUPPORTED:
        # Withheld trace metadata may refer to *candidate* source/claim IDs.
        # Do not export them; the trace does not grant their display authority.
        handoff["current_authorization"] = "NOT_APPLICABLE_WITHHELD"
        return handoff

    source_ids = {s.source_id for s in checked.sources}
    if expected_source_sha256 is not None and observed_source_sha256 is not None:
        if (set(expected_source_sha256) != source_ids
                or set(observed_source_sha256) != source_ids
                or any(expected_source_sha256[k] != observed_source_sha256[k] for k in source_ids)):
            handoff["snapshot_comparison"] = "MISSING_OR_CHANGED_SOURCE_HOLD"
            return handoff
        handoff["snapshot_comparison"] = "SUPPLIED_DIGESTS_MATCH_NOT_INDEPENDENTLY_AUTHENTICATED"

    handoff["source_ids"] = sorted(source_ids)
    handoff["query_digests"] = list(checked.trace.retrieval_query_digests)
    handoff["authorization_decision_ids"] = sorted(
        d.decision_id for d in checked.influence_decisions if d.allowed
    )
    handoff["provenance_graph"] = [
        {
            "claim_id": m.claim_id,
            "evidence_id": m.evidence_id,
            "passage_ids": list(m.passage_ids),
            "source_id": m.source_id,
        }
        for m in checked.citation_mappings
    ]
    handoff["current_authorization"] = "RECHECKED_BY_ISSUING_CONTROLLER"
    handoff["handoff_disposition"] = "ENGINEERING_INSPECTION_ONLY"
    return handoff
