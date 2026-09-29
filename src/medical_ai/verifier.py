from __future__ import annotations
from .schemas import ClaimRecord, EvidenceUnit, Passage, VerificationStatus


def verify_claims(claims: list[ClaimRecord], units: list[EvidenceUnit], passages: list[Passage], high_consequence_supported: bool = False) -> list[ClaimRecord]:
    unit_map = {u.evidence_id: u for u in units}
    passage_map = {p.passage_id: p for p in passages}
    verified: list[ClaimRecord] = []
    for claim in claims:
        evidence = [unit_map[e] for e in claim.evidence_ids if e in unit_map]
        passage_texts = [passage_map[pid].text for u in evidence for pid in u.passage_ids if pid in passage_map]
        exact = bool(evidence) and any(claim.claim_text in text for text in passage_texts)
        if not exact:
            claim.entailment_status = "UNSUPPORTED"
            claim.verification_status = VerificationStatus.FAIL
        elif claim.consequence_level == "HIGH" and not high_consequence_supported:
            # PubMed abstract evidence alone cannot satisfy the alpha2 high-consequence gate.
            claim.entailment_status = "SUPPORTED_EXTRACTIVELY"
            claim.verification_status = VerificationStatus.FAIL
        else:
            claim.entailment_status = "SUPPORTED_EXACT_PASSAGE"
            claim.verification_status = VerificationStatus.PASS
        verified.append(claim)
    return verified
