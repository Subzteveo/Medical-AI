"""Alpha3 A2 — unit tests for the trusted authority resolver.

The resolver maps a verified claim's actual scope onto the merged A1 policies and
returns an authority resolution plus A1 decision records. These tests exercise the
fail-closed behaviour directly, independent of the engine.
"""

from __future__ import annotations

import pytest

from medical_ai.authority import DecisionResult
from medical_ai.authority_resolver import UNRESOLVED, AuthorityResolver
from medical_ai.schemas import (
    ClaimRecord,
    ConsequenceLevel,
    EvidenceAuthorityState,
    InformationClass,
    InformationHandlingAuthorityState,
    VerificationStatus,
)


def _claim(**kw: object) -> ClaimRecord:
    base: dict[str, object] = dict(
        claim_id="c1", claim_text="Treatment X reduced symptom scores.",
        consequence_level=ConsequenceLevel.MODERATE, evidence_ids=["e1"], source_ids=["s1"],
        verification_status=VerificationStatus.PASS, entailment_status="SUPPORTED_EXACT_PASSAGE",
    )
    base.update(kw)
    return ClaimRecord(**base)


@pytest.fixture(scope="module")
def resolver() -> AuthorityResolver:
    return AuthorityResolver()


def test_literature_public_current_is_authorized(resolver: AuthorityResolver) -> None:
    res = resolver.resolve_claim_authority(
        _claim(), source_class="biomedical_literature", public_non_phi=True,
        any_source_superseded=False, trace_ref="t",
    )
    assert res.authorized
    assert res.evidence_authority is EvidenceAuthorityState.APPROVED
    assert res.information_handling_authority is InformationHandlingAuthorityState.APPROVED
    assert res.information_class is InformationClass.PUBLIC
    assert res.validation_passed


def test_trial_registry_is_authorized(resolver: AuthorityResolver) -> None:
    res = resolver.resolve_claim_authority(
        _claim(), source_class="clinical_trial_registry", public_non_phi=True,
        any_source_superseded=False, trace_ref="t",
    )
    assert res.authorized


def test_retracted_denies_evidence_authority(resolver: AuthorityResolver) -> None:
    res = resolver.resolve_claim_authority(
        _claim(), source_class="biomedical_literature", public_non_phi=True,
        any_source_superseded=True, trace_ref="t",
    )
    assert not res.authorized
    assert res.evidence_authority is EvidenceAuthorityState.DENIED
    assert not res.validation_passed


def test_non_public_denies_information_handling(resolver: AuthorityResolver) -> None:
    res = resolver.resolve_claim_authority(
        _claim(), source_class="biomedical_literature", public_non_phi=False,
        any_source_superseded=False, trace_ref="t",
    )
    assert not res.authorized
    assert res.information_handling_authority is InformationHandlingAuthorityState.DENIED
    assert res.information_class is InformationClass.UNKNOWN


def test_unknown_source_class_fails_closed(resolver: AuthorityResolver) -> None:
    res = resolver.resolve_claim_authority(
        _claim(), source_class="horoscope_feed", public_non_phi=True,
        any_source_superseded=False, trace_ref="t",
    )
    assert not res.authorized
    assert res.evidence_authority is not EvidenceAuthorityState.APPROVED


def test_high_consequence_denies(resolver: AuthorityResolver) -> None:
    res = resolver.resolve_claim_authority(
        _claim(consequence_level=ConsequenceLevel.HIGH), source_class="biomedical_literature",
        public_non_phi=True, any_source_superseded=False, trace_ref="t",
    )
    assert not res.authorized
    assert res.evidence_authority is EvidenceAuthorityState.DENIED


def test_allow_decisions_carry_independent_references(resolver: AuthorityResolver) -> None:
    res = resolver.resolve_claim_authority(
        _claim(), source_class="biomedical_literature", public_non_phi=True,
        any_source_superseded=False, trace_ref="trace-xyz",
    )
    assert res.decisions
    for decision in res.decisions:
        if decision.result is DecisionResult.ALLOW:
            assert decision.authority_source_ref  # independent authority source
            assert decision.policy_digest
            assert decision.input_state_hash.startswith("sha256:")
            assert decision.evidence_refs  # policy-required evidence
            assert decision.reason_codes == ()
            assert decision.trace_ref == "trace-xyz"


def test_unresolved_sentinel_authorizes_nothing() -> None:
    assert not UNRESOLVED.authorized
    assert UNRESOLVED.evidence_authority is EvidenceAuthorityState.UNKNOWN
    assert not UNRESOLVED.validation_passed
