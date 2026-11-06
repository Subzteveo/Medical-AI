"""Alpha3 A2 — unit tests for the trusted authority resolver.

The resolver maps a verified claim's actual scope onto the merged A1 policies and
returns an authority resolution plus A1 decision records. These tests exercise the
fail-closed behaviour directly, independent of the engine.

A2 repair: the resolver now receives the claim's source records (not a bare
``any_source_superseded`` bool) and verifies each source's source-version record and
explicit freshness assessment. These tests therefore build source records with a
valid version record and an explicit freshness state; the assertions are unchanged
in intent (authorized/denied, evidence/information-handling states).
"""

from __future__ import annotations

import pytest

from conftest import synthetic_version_record
from medical_ai.authority import DecisionResult, FreshnessState
from medical_ai.authority_resolver import UNRESOLVED, AuthorityResolver
from medical_ai.schemas import (
    ClaimRecord,
    ConsequenceLevel,
    EvidenceAuthorityState,
    FreshnessAssessment,
    InformationClass,
    InformationHandlingAuthorityState,
    SourceRecord,
    VerificationStatus,
)
from datetime import datetime, timezone


def _claim(**kw: object) -> ClaimRecord:
    base: dict[str, object] = dict(
        claim_id="c1", claim_text="Treatment X reduced symptom scores.",
        consequence_level=ConsequenceLevel.MODERATE, evidence_ids=["e1"], source_ids=["s1"],
        verification_status=VerificationStatus.PASS, entailment_status="SUPPORTED_EXACT_PASSAGE",
    )
    base.update(kw)
    return ClaimRecord(**base)


def _sources(
    *, freshness_state: FreshnessState = FreshnessState.CURRENT, with_record: bool = True
) -> list[SourceRecord]:
    record = (
        synthetic_version_record(
            source_id="s1", record_id="r1", upstream_version="r1.1",
            connector_name="test-connector", connector_version="test-v1",
        )
        if with_record
        else None
    )
    return [SourceRecord(
        source_id="s1", authority="NLM/NCBI PubMed", publisher="Example Journal",
        source_type="indexed_biomedical_literature", title="Evidence about treatment X",
        record_id="r1", stable_url="https://pubmed.ncbi.nlm.nih.gov/r1/", identifiers={"PMID": "r1"},
        version_record=record,
        freshness=FreshnessAssessment(
            state=freshness_state, basis="test-fixture", assessed_at=datetime.now(timezone.utc)
        ),
    )]


@pytest.fixture(scope="module")
def resolver() -> AuthorityResolver:
    return AuthorityResolver()


def test_literature_public_current_is_authorized(resolver: AuthorityResolver) -> None:
    res = resolver.resolve_claim_authority(
        _claim(), source_class="biomedical_literature", public_non_phi=True,
        source_records=_sources(), trace_ref="t",
    )
    assert res.authorized
    assert res.evidence_authority is EvidenceAuthorityState.APPROVED
    assert res.information_handling_authority is InformationHandlingAuthorityState.APPROVED
    assert res.information_class is InformationClass.PUBLIC
    assert res.validation_passed
    assert res.freshness_status == "CURRENT"


def test_trial_registry_is_authorized(resolver: AuthorityResolver) -> None:
    res = resolver.resolve_claim_authority(
        _claim(), source_class="clinical_trial_registry", public_non_phi=True,
        source_records=_sources(), trace_ref="t",
    )
    assert res.authorized


def test_retracted_denies_evidence_authority(resolver: AuthorityResolver) -> None:
    res = resolver.resolve_claim_authority(
        _claim(), source_class="biomedical_literature", public_non_phi=True,
        source_records=_sources(freshness_state=FreshnessState.RETRACTED), trace_ref="t",
    )
    assert not res.authorized
    assert res.evidence_authority is EvidenceAuthorityState.DENIED
    assert not res.validation_passed
    assert res.freshness_status == "RETRACTED"


def test_missing_source_version_record_is_unknown(resolver: AuthorityResolver) -> None:
    # Trust root: a current freshness assessment with no source-version record must
    # resolve evidence authority to UNKNOWN (absent), not APPROVED.
    res = resolver.resolve_claim_authority(
        _claim(), source_class="biomedical_literature", public_non_phi=True,
        source_records=_sources(with_record=False), trace_ref="t",
    )
    assert not res.authorized
    assert res.evidence_authority is EvidenceAuthorityState.UNKNOWN


def test_unknown_freshness_denies_evidence_authority(resolver: AuthorityResolver) -> None:
    # A verified record but an UNKNOWN freshness must be denied by ea-unknown-freshness.
    res = resolver.resolve_claim_authority(
        _claim(), source_class="biomedical_literature", public_non_phi=True,
        source_records=_sources(freshness_state=FreshnessState.UNKNOWN), trace_ref="t",
    )
    assert not res.authorized
    assert res.evidence_authority is EvidenceAuthorityState.DENIED
    assert res.freshness_status == "UNKNOWN"


def test_non_public_denies_information_handling(resolver: AuthorityResolver) -> None:
    res = resolver.resolve_claim_authority(
        _claim(), source_class="biomedical_literature", public_non_phi=False,
        source_records=_sources(), trace_ref="t",
    )
    assert not res.authorized
    assert res.information_handling_authority is InformationHandlingAuthorityState.DENIED
    assert res.information_class is InformationClass.UNKNOWN


def test_unknown_source_class_fails_closed(resolver: AuthorityResolver) -> None:
    res = resolver.resolve_claim_authority(
        _claim(), source_class="horoscope_feed", public_non_phi=True,
        source_records=_sources(), trace_ref="t",
    )
    assert not res.authorized
    assert res.evidence_authority is not EvidenceAuthorityState.APPROVED


def test_high_consequence_denies(resolver: AuthorityResolver) -> None:
    res = resolver.resolve_claim_authority(
        _claim(consequence_level=ConsequenceLevel.HIGH), source_class="biomedical_literature",
        public_non_phi=True, source_records=_sources(), trace_ref="t",
    )
    assert not res.authorized
    assert res.evidence_authority is EvidenceAuthorityState.DENIED


def test_allow_decisions_carry_independent_references(resolver: AuthorityResolver) -> None:
    res = resolver.resolve_claim_authority(
        _claim(), source_class="biomedical_literature", public_non_phi=True,
        source_records=_sources(), trace_ref="trace-xyz",
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
    assert UNRESOLVED.freshness_status == "NOT_ASSESSED"
