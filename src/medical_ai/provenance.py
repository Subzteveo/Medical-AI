"""Structural output checks. Passing these checks does not grant influence authority."""
from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from typing import TypeVar
from urllib.parse import urlsplit

from .schemas import CitationMapping, ClaimRecord, EvidenceUnit, Passage, SourceRecord, VerificationStatus

T = TypeVar("T")


def safe_source_url(value: str) -> str | None:
    """Permit explicit HTTPS links only; this says nothing about medical authority."""
    if not value.lower().startswith("https://") or re.search(r"[\s\x00-\x1f\x7f\\]", value):
        return None
    try:
        parts = urlsplit(value)
        host = parts.hostname
        if (parts.scheme.lower() != "https" or not host or parts.username is not None
                or parts.password is not None or not re.fullmatch(r"[A-Za-z0-9.:-]+", host)):
            return None
        # Reading port checks malformed and out-of-range ports.
        if parts.port is not None and not 1 <= parts.port <= 65535:
            return None
    except ValueError:
        return None
    return value


def unique_ids(ids: Sequence[str], *, required: bool = False) -> set[str]:
    if (required and not ids) or any(not value or value != value.strip() for value in ids):
        raise ValueError("Provenance IDs must be nonempty and unambiguous")
    values = set(ids)
    if len(values) != len(ids):
        raise ValueError("Duplicate provenance ID")
    return values


def index_records(records: Sequence[T], key: Callable[[T], str]) -> dict[str, T]:
    unique_ids([key(record) for record in records])
    return {key(record): record for record in records}


def validate_retrieved_records(sources: Sequence[SourceRecord], passages: Sequence[Passage]) -> None:
    source_map = index_records(sources, lambda source: source.source_id)
    index_records(passages, lambda passage: passage.passage_id)
    if any(safe_source_url(source.stable_url) is None for source in sources):
        raise ValueError("Source link is not permitted HTTPS")
    if any(passage.source_id not in source_map for passage in passages):
        raise ValueError("Passage has no matching source")


def validate_output_provenance(
    claims: Sequence[ClaimRecord], sources: Sequence[SourceRecord],
    evidence_objects: Sequence[EvidenceUnit], passages: Sequence[Passage],
    citation_mappings: Sequence[CitationMapping],
) -> None:
    """Require a closed, unambiguous graph for this extractive runtime's output.

    Every delivered object must participate in a claim's exact-passage mapping.
    The issuing controller must independently validate each claim capability.
    """
    validate_retrieved_records(sources, passages)
    source_map = index_records(sources, lambda source: source.source_id)
    claim_map = index_records(claims, lambda claim: claim.claim_id)
    unit_map = index_records(evidence_objects, lambda unit: unit.evidence_id)
    passage_map = index_records(passages, lambda passage: passage.passage_id)
    index_records(citation_mappings, lambda mapping: mapping.mapping_id)
    if any(not source.provenance_complete or source.superseded for source in sources):
        raise ValueError("Delivered source provenance is incomplete or superseded")

    used_sources: set[str] = set()
    used_evidence: set[str] = set()
    used_passages: set[str] = set()
    expected_pairs: set[tuple[str, str]] = set()
    for claim in claims:
        if (claim.verification_status != VerificationStatus.PASS or not claim.claim_text.strip()
                or claim.entailment_status != "SUPPORTED_EXACT_PASSAGE"):
            raise ValueError("Claim is not verified by this extractive runtime")
        source_ids = unique_ids(claim.source_ids, required=True)
        evidence_ids = unique_ids(claim.evidence_ids, required=True)
        if not source_ids <= source_map.keys() or not evidence_ids <= unit_map.keys():
            raise ValueError("Claim references missing provenance")
        evidence_sources: set[str] = set()
        for evidence_id in evidence_ids:
            unit = unit_map[evidence_id]
            passage_ids = unique_ids(unit.passage_ids, required=True)
            if unit.source_id not in source_ids or unit.proposition != claim.claim_text:
                raise ValueError("Evidence does not match the claim and source")
            if not passage_ids <= passage_map.keys():
                raise ValueError("Evidence references a missing passage")
            for passage_id in passage_ids:
                passage = passage_map[passage_id]
                if (passage.source_id != unit.source_id or not passage.locator.strip()
                        or not passage.section.strip() or claim.claim_text not in passage.text):
                    raise ValueError("Passage does not support the mapped extractive claim")
            evidence_sources.add(unit.source_id)
            used_passages.update(passage_ids)
            expected_pairs.add((claim.claim_id, evidence_id))
        if evidence_sources != source_ids:
            raise ValueError("Claim source references do not match its evidence")
        used_sources.update(source_ids)
        used_evidence.update(evidence_ids)

    actual_pairs: set[tuple[str, str]] = set()
    for mapping in citation_mappings:
        pair = (mapping.claim_id, mapping.evidence_id)
        if pair not in expected_pairs or pair in actual_pairs:
            raise ValueError("Missing or duplicate claim/evidence mapping")
        claim, unit = claim_map[mapping.claim_id], unit_map[mapping.evidence_id]
        if (not mapping.verified or mapping.entailment_status != claim.entailment_status
                or mapping.source_id != unit.source_id
                or unique_ids(mapping.passage_ids, required=True) != set(unit.passage_ids)):
            raise ValueError("Citation mapping disagrees with evidence and passage provenance")
        actual_pairs.add(pair)
    if (actual_pairs != expected_pairs or used_sources != source_map.keys()
            or used_evidence != unit_map.keys() or used_passages != passage_map.keys()):
        raise ValueError("Delivered provenance graph is incomplete or contains unreferenced records")
