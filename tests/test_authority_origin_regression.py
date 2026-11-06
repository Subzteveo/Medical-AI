"""Authority-origin regression for independent medical influence authority (Issue #25).

Originally the owner-approved RED fixture from PR #40: the synthetic connector
supplies indexed evidence, but the engine is constructed without a trusted authority
resolver, so there is no independently resolved, current, claim-scoped authority
decision. A verifier PASS and connector admission are not authority, so the claim
must be withheld. A2 (the authority resolver + fail-closed engine) makes this pass.
"""

from __future__ import annotations

import pytest

from conftest import FakePubMedConnector, make_engine
from medical_ai.engine import EvidenceEngine
from medical_ai.schemas import AnswerStatus, VerificationStatus


@pytest.mark.asyncio
async def test_claim_without_independently_resolved_authority_must_be_withheld():
    connector = FakePubMedConnector()
    # No authority resolver supplied: the engine can resolve no authority at all.
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
    assert not any(decision.allowed for decision in answer.influence_decisions), (
        "Self-assigned APPROVED/validation flags must not grant medical influence"
    )
    assert answer.claims == []
    assert answer.status == AnswerStatus.INFLUENCE_DENIED


@pytest.mark.asyncio
async def test_same_claim_is_supported_once_authority_is_independently_resolved():
    """The identical fixture, with the trusted resolver wired in, is admissible.

    This is the positive control: the only difference from the denial above is the
    presence of the independent authority resolver, not any change to the evidence.
    """
    connector = FakePubMedConnector()
    answer = await make_engine(connector).answer(
        "What evidence shows treatment X reduces symptom scores?"
    )
    assert answer.status == AnswerStatus.ANSWER_SUPPORTED_WITH_QUALIFICATIONS
    assert answer.claims
    assert any(decision.allowed for decision in answer.influence_decisions)
    # Even allowed, authority came from the resolver, never a self-declared flag.
    allowed = next(d for d in answer.influence_decisions if d.allowed)
    assert allowed.evaluated_dimensions.evidence_authority.value == "APPROVED"


@pytest.mark.asyncio
async def test_retracted_source_is_denied_even_with_resolver():
    """A retracted/superseded source fails closed at the evidence-authority dimension."""
    base = FakePubMedConnector()
    retracted = base.sources[0].model_copy(update={"superseded": True})
    answer = await make_engine(
        FakePubMedConnector([retracted], base.passages)
    ).answer("What evidence shows treatment X reduces symptom scores?")
    assert answer.claims == []
    assert answer.status != AnswerStatus.ANSWER_SUPPORTED_WITH_QUALIFICATIONS
