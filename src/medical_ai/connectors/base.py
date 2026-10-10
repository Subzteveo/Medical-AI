from __future__ import annotations

from typing import Protocol, runtime_checkable

from medical_ai.schemas import Passage, SourceRecord


@runtime_checkable
class EvidenceConnector(Protocol):
    name: str
    version: str
    source_class: str
    evidence_approved: bool
    phi_approved: bool

    async def search_and_fetch(
        self,
        query: str,
        limit: int = 5,
    ) -> tuple[list[SourceRecord], list[Passage]]: ...


def require_evidence_approved(
    connector: object,
    expected_source_class: str,
) -> EvidenceConnector:
    if not isinstance(connector, EvidenceConnector):
        raise ValueError("Connector does not satisfy the typed EvidenceConnector contract")
    if connector.source_class != expected_source_class:
        raise ValueError(
            "Connector source class mismatch: "
            f"expected {expected_source_class}, got {connector.source_class!r}"
        )
    if connector.evidence_approved is not True:
        raise ValueError(
            f"Connector {connector.name} is not evidence-approved for {expected_source_class}"
        )
    return connector
