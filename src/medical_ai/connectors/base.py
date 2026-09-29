from __future__ import annotations
from typing import Protocol
from medical_ai.schemas import Passage, SourceRecord


class EvidenceConnector(Protocol):
    name: str
    version: str
    source_class: str
    evidence_approved: bool
    phi_approved: bool

    async def search_and_fetch(self, query: str, limit: int = 5) -> tuple[list[SourceRecord], list[Passage]]: ...


def require_evidence_approved(connector: object, expected_source_class: str) -> object:
    configured_source_class = getattr(connector, "source_class", None)
    if configured_source_class != expected_source_class:
        raise ValueError(
            f"Connector source class mismatch: expected {expected_source_class}, got {configured_source_class!r}"
        )
    evidence_approved = getattr(connector, "evidence_approved", None)
    if evidence_approved is not True:
        raise ValueError(
            f"Connector {getattr(connector, 'name', 'unknown')} is not evidence-approved for {expected_source_class}"
        )
    return connector
