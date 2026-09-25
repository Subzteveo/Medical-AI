from __future__ import annotations
from typing import Protocol
from medical_ai.schemas import Passage, SourceRecord


class EvidenceConnector(Protocol):
    name: str
    version: str
    source_class: str
    phi_approved: bool

    async def search_and_fetch(self, query: str, limit: int = 5) -> tuple[list[SourceRecord], list[Passage]]: ...
