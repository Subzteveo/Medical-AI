"""Red regression for independent medical influence authority (Issue #25).

The synthetic connector supplies indexed evidence, but no independently resolved,
current, claim-scoped authority decision. This test intentionally remains red
until the G0/A1-gated A2 authority-origin repair is separately authorised.
"""

from __future__ import annotations

import pytest

from conftest import FakePubMedConnector
from medical_ai.engine import EvidenceEngine
from medical_ai.schemas import AnswerStatus, VerificationStatus


@pytest.mark.asyncio
async def test_claim_without_independently_resolved_authority_must_be_withheld():
    connector = FakePubMedConnector()
    answer = await EvidenceEngine(connector).answer(
        "What evidence shows treatment X reduces symptom scores?"
    )

    assert connector.called, "fixture must exercise the evidence engine"
    assert answer.trace.candidate_claim_ids, "fixture must reach claim construction"
    assert VerificationStatus.PASS.value in answer.trace.verification_results.values(), (
        "fixture must exercise an otherwise verified claim"
    )
    assert answer.influence_decisions, "fixture must reach the influence gate"

    # Connector admission and a verifier PASS are not independent claim authority.
    # This fixture supplies no trusted, current, claim-scoped authority decision.
    assert not any(decision.allowed for decision in answer.influence_decisions), (
        "Self-assigned APPROVED/validation flags must not grant medical influence"
    )
    assert answer.claims == []
    assert answer.status == AnswerStatus.INFLUENCE_DENIED
