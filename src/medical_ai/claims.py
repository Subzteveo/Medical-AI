from __future__ import annotations

import hashlib

from .planner import classify_consequence
from .schemas import ClaimRecord, ConsequenceLevel, EvidenceUnit, QueryPlan


def build_claims(units: list[EvidenceUnit], plan: QueryPlan) -> list[ClaimRecord]:
    claims: list[ClaimRecord] = []
    for unit in units:
        cid = "clm_" + hashlib.sha256(unit.evidence_id.encode()).hexdigest()[:16]
        claim_level, _ = classify_consequence(unit.proposition)
        consequence = ConsequenceLevel.HIGH if (
            plan.consequence_level == ConsequenceLevel.HIGH or claim_level == ConsequenceLevel.HIGH
        ) else plan.consequence_level
        claims.append(ClaimRecord(
            claim_id=cid,
            claim_text=unit.proposition,
            claim_type="DIRECT",
            consequence_level=consequence,
            evidence_ids=[unit.evidence_id],
            source_ids=[unit.source_id],
            jurisdiction=unit.jurisdiction,
        ))
    return claims
