"""Conservative, source-bound hazard holds for explicit literature discrepancies.

These are narrow negative safety checks, not clinical conflict resolution,
population generalisation, source approval or a clinical verifier. Failure to
detect a hazard MUST NOT be interpreted as proof of absence.
"""
from __future__ import annotations

import re

from .schemas import AnswerStatus, Passage, SourceRecord


_EFFECT = re.compile(
    r"\b(?P<subject>(?:treatment|intervention)\s+[A-Za-z0-9-]+)\s+"
    r"(?P<negative>did not |does not )?"
    r"(?P<effect>reduce|reduced|improve|improved|increase|increased|decrease|decreased)\s+"
    r"(?P<outcome>[^.!?;]{4,200})",
    re.I,
)
_EFFECT_ROOT = {
    "reduce": "reduce", "reduced": "reduce",
    "improve": "improve", "improved": "improve",
    "increase": "increase", "increased": "increase",
    "decrease": "decrease", "decreased": "decrease",
}
_OLDER_THAN_QUERY = re.compile(
    r"\b(?:over|older than|above)\s+(?P<age>\d{1,3})"
    r"(?:\s+years?(?:\s+old)?)?\b",
    re.I,
)
_EXPLICIT_EXCLUSION = re.compile(
    r"\b(?:adults?|patients?|participants?|people|subjects?)\s+"
    r"(?:over|older than|above)\s+(?P<age>\d{1,3})"
    r"(?:\s+years?(?:\s+old)?)?\s+"
    r"(?:were|was)\s+(?:not|never)\s+"
    r"(?:evaluated|studied|included|enrolled)\b",
    re.I,
)


def _normalise(value: str) -> str:
    return " ".join(value.casefold().split())


def explicit_evidence_hold(
    question: str, sources: list[SourceRecord], passages: list[Passage]
) -> AnswerStatus | None:
    """Withhold for narrow, explicit text hazards from admitted literature only.

    Do not infer that other evidence is conflict-free or population-matched.
    This guard may abstain conservatively and must not grant ALLOW.
    """
    literature_ids = {
        source.source_id for source in sources
        if source.source_type == "indexed_biomedical_literature"
    }
    relevant = [
        passage for passage in passages
        if passage.source_id in literature_ids and passage.section != "TITLE"
    ]
    signatures: dict[tuple[str, str, str], dict[bool, set[str]]] = {}
    question_text = _normalise(question)
    for passage in relevant:
        for matched in _EFFECT.finditer(passage.text):
            subject = _normalise(matched.group("subject"))
            if subject not in question_text:
                continue
            key = (
                subject,
                _EFFECT_ROOT[matched.group("effect").casefold()],
                _normalise(matched.group("outcome")),
            )
            sign = matched.group("negative") is not None
            signatures.setdefault(key, {True: set(), False: set()})[sign].add(
                passage.source_id
            )
    if any(
        positive_id != negative_id
        for signs in signatures.values()
        for positive_id in signs[False]
        for negative_id in signs[True]
    ):
        return AnswerStatus.EVIDENCE_CONFLICTING

    requested_cutoffs = [
        int(matched.group("age"))
        for matched in _OLDER_THAN_QUERY.finditer(question)
    ]
    if requested_cutoffs:
        for passage in relevant:
            for matched in _EXPLICIT_EXCLUSION.finditer(passage.text):
                excluded_cutoff = int(matched.group("age"))
                if any(excluded_cutoff <= requested for requested in requested_cutoffs):
                    return AnswerStatus.POPULATION_MISMATCH
    return None
