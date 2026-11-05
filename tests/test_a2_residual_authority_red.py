"""A2 residual-authority repair regressions (Defects A and B, now fixed).

Two residual gaps inside A2's own resolver code (``authority_resolver.py``),
reproduced at the observable engine boundary, and now closed by the A2 authority
repair. These are NOT the pre-A2 gap that ``tests/test_authority_origin_regression.py``
covers; they are defects that survived *inside* the merged A2 resolver.

Defect A — unresolvable source-version authority (REPAIRED)
    The resolver built reference strings such as ``source-version:<class>:<claim_id>``
    but nothing established that they resolved to independently verified
    source-version records. The repair makes the resolver verify a real
    ``SourceVersionRecord`` per source; without one, evidence authority is UNKNOWN
    and surfaces as ``EVIDENCE_AUTHORITY_UNKNOWN``. A well-formed reference string is
    no longer authority.

Defect B — missing freshness defaults to CURRENT (REPAIRED)
    ``resolve_claim_authority`` used to receive a plain ``bool`` and compute
    ``SUPERSEDED if any_source_superseded else CURRENT``, so the *absence* of a
    freshness state was silently treated as current. The repair passes the claim's
    source records; a source with no ``FreshnessAssessment`` resolves to UNKNOWN
    freshness, which the merged ``ea-unknown-freshness`` DENY rule denies, surfacing
    as ``EVIDENCE_AUTHORITY_DENIED``.

Each test now isolates its defect: Defect A has an explicit CURRENT freshness and no
version record (so only the record gate fails); Defect B has a valid version record
and no freshness (so only the freshness gate fails). Fixtures use synthetic, non-PHI
data only.
"""

from __future__ import annotations

from collections.abc import Sequence

import pytest

from conftest import FakePubMedConnector
from medical_ai.authority_resolver import AuthorityResolver, ClaimAuthorityResolution
from medical_ai.engine import EvidenceEngine
from medical_ai.schemas import AnswerStatus, InfluenceReasonCode, SourceRecord, VerificationStatus

_QUESTION = "What evidence shows treatment X reduces symptom scores?"


class _RecordingResolver(AuthorityResolver):
    """The real, trusted A2 resolver, wrapped to prove that a verified claim
    actually reaches it and to capture the resolution it produced.

    The wrapper changes no resolver behaviour. It exists only so the tests can
    assert, explicitly, that the claim traversed the authority path (a test that
    passed because the claim never reached the resolver would be invalid) and so
    the diagnostic below can inspect what the resolver decided. The RED
    assertions themselves stay at the engine's observable output.
    """

    def __init__(self) -> None:
        super().__init__()
        self.calls: list[dict[str, object]] = []
        self.resolutions: list[ClaimAuthorityResolution] = []

    def resolve_claim_authority(  # type: ignore[override]
        self,
        claim,
        *,
        source_class: str,
        public_non_phi: bool,
        source_records: Sequence[SourceRecord],
        trace_ref: str,
    ) -> ClaimAuthorityResolution:
        resolution = super().resolve_claim_authority(
            claim,
            source_class=source_class,
            public_non_phi=public_non_phi,
            source_records=source_records,
            trace_ref=trace_ref,
        )
        self.calls.append(
            {
                "claim_id": claim.claim_id,
                "source_class": source_class,
                "public_non_phi": public_non_phi,
                "has_version_record": all(s.version_record is not None for s in source_records),
                "freshness_states": [
                    (s.freshness.state.value if s.freshness is not None else None) for s in source_records
                ],
            }
        )
        self.resolutions.append(resolution)
        return resolution


@pytest.mark.asyncio
async def test_defect_a_reference_string_is_not_a_resolved_source_version_record():
    """Defect A: a well-formed source-version reference string, backed by no
    independently verified record, must not yield a supported medical claim.

    Repaired: the engine denies the claim with ``EVIDENCE_AUTHORITY_UNKNOWN`` because
    no verified source-version record exists, even though freshness is CURRENT.
    """
    resolver = _RecordingResolver()
    # Explicit CURRENT freshness but NO source-version record: isolates the record
    # (trust-root) gate from the freshness gate.
    base = FakePubMedConnector()
    no_record = base.sources[0].model_copy(update={"version_record": None})
    assert no_record.version_record is None
    assert no_record.freshness is not None and no_record.freshness.state.value == "CURRENT"
    connector = FakePubMedConnector([no_record], base.passages)
    engine = EvidenceEngine(connector, authority_resolver=resolver)

    answer = await engine.answer(_QUESTION)

    # 1. The claim genuinely reaches the authority resolver and the influence gate
    #    (it is not short-circuited earlier in the pipeline).
    assert connector.called, "fixture must exercise the evidence engine"
    assert resolver.calls, "claim must reach the authority resolver"
    assert answer.trace.candidate_claim_ids, "fixture must reach claim construction"
    assert VerificationStatus.PASS.value in answer.trace.verification_results.values(), (
        "fixture must exercise an otherwise verified claim"
    )
    assert answer.influence_decisions, "claim must reach the influence gate"

    # 2. Diagnostic (NOT the RED assertion): the resolver still emits the reference
    #    string, but it no longer confers authority without a verified record.
    resolution = resolver.resolutions[0]
    resolved_claim_id = resolver.calls[0]["claim_id"]
    source_version_refs = [
        getattr(decision, "source_version_ref", None) for decision in resolution.decisions
    ]
    assert f"source-version:biomedical_literature:{resolved_claim_id}" in source_version_refs, (
        "resolver still emits a reference string for traceability"
    )
    assert not resolution.authorized, (
        "a reference string without a verified source-version record is not authority"
    )

    # 3. REQUIRED behaviour (RED against df50749): without an independently
    #    resolvable source-version record the claim must be denied, and no
    #    supported medical claim may appear in the engine output.
    assert not any(decision.allowed for decision in answer.influence_decisions), (
        "a well-formed source-version reference string must not substitute for a "
        "resolved, independently verified source-version record"
    )
    assert all(decision.reasons for decision in answer.influence_decisions), (
        "a denied decision must carry at least one reason"
    )
    assert answer.claims == [], "no supported medical claim may be rendered"
    assert answer.status not in {
        AnswerStatus.ANSWER_SUPPORTED,
        AnswerStatus.ANSWER_SUPPORTED_WITH_QUALIFICATIONS,
    }

    # Per-defect reason code (3.4): a missing verified record is EVIDENCE_AUTHORITY_UNKNOWN.
    assert any(
        InfluenceReasonCode.EVIDENCE_AUTHORITY_UNKNOWN in decision.reasons
        for decision in answer.influence_decisions
    ), "Defect A must surface as EVIDENCE_AUTHORITY_UNKNOWN"
    assert not any(
        InfluenceReasonCode.EVIDENCE_AUTHORITY_DENIED in decision.reasons
        for decision in answer.influence_decisions
    ), "Defect A is an absent record (UNKNOWN), not a policy DENY"


@pytest.mark.asyncio
async def test_defect_b_missing_freshness_must_not_default_to_current_allow():
    """Defect B: admitted evidence carrying no freshness assessment must not be
    treated as current authority.

    Repaired: the source carries a valid version record but no freshness assessment,
    so freshness resolves to UNKNOWN and ``ea-unknown-freshness`` denies it with
    ``EVIDENCE_AUTHORITY_DENIED``.
    """
    base = FakePubMedConnector()
    # Valid version record, but freshness genuinely ABSENT (not a convenient value).
    freshnessless = base.sources[0].model_copy(update={"freshness": None})
    resolver = _RecordingResolver()
    connector = FakePubMedConnector([freshnessless], base.passages)
    engine = EvidenceEngine(connector, authority_resolver=resolver)

    answer = await engine.answer(_QUESTION)

    # Freshness is genuinely absent from the input, but the version record is valid.
    src = connector.sources[0]
    assert src.freshness is None, "freshness assessment left unset"
    assert src.version_record is not None, "a valid source-version record is present"

    # 1. The evidence reaches the resolver; a missing freshness assessment is UNKNOWN,
    #    never silently 'not superseded'.
    assert connector.called, "fixture must exercise the evidence engine"
    assert resolver.calls, "evidence must reach the authority resolver"
    assert resolver.calls[0]["freshness_states"] == [None], (
        "the source carries no freshness assessment; the resolver treats it as UNKNOWN"
    )
    assert answer.influence_decisions, "claim must reach the influence gate"

    # 2/3. REQUIRED behaviour (RED against df50749): the absence of a supersession
    #    flag does not establish currency. The claim must be denied or unknown,
    #    never a current-authority ALLOW, and no supported claim may appear.
    assert not any(decision.allowed for decision in answer.influence_decisions), (
        "absence of a supersession flag must not establish current authority"
    )
    assert all(decision.reasons for decision in answer.influence_decisions), (
        "a denied decision must carry at least one reason"
    )
    assert answer.claims == [], "no supported medical claim may be rendered"
    assert answer.status not in {
        AnswerStatus.ANSWER_SUPPORTED,
        AnswerStatus.ANSWER_SUPPORTED_WITH_QUALIFICATIONS,
    }

    # Per-defect reason code (3.4): unknown freshness is the explicit DENY rule.
    assert any(
        InfluenceReasonCode.EVIDENCE_AUTHORITY_DENIED in decision.reasons
        for decision in answer.influence_decisions
    ), "Defect B must surface as EVIDENCE_AUTHORITY_DENIED"


@pytest.mark.asyncio
async def test_dated_source_with_record_but_no_freshness_is_denied():
    """A dated source (publication_date set) with a valid version record but no
    freshness assessment must still be denied with EVIDENCE_AUTHORITY_DENIED: a
    publication date is not a freshness assessment.
    """
    base = FakePubMedConnector()
    dated = base.sources[0].model_copy(update={"freshness": None})
    assert dated.publication_date is not None, "the source carries a publication date"
    assert dated.version_record is not None, "the source carries a valid version record"
    assert dated.freshness is None, "but no explicit freshness assessment"
    resolver = _RecordingResolver()
    connector = FakePubMedConnector([dated], base.passages)
    engine = EvidenceEngine(connector, authority_resolver=resolver)

    answer = await engine.answer(_QUESTION)

    assert resolver.calls, "claim must reach the authority resolver"
    assert answer.influence_decisions, "claim must reach the influence gate"
    assert not any(decision.allowed for decision in answer.influence_decisions)
    assert answer.claims == [], "a publication date must not stand in for freshness"
    assert answer.status not in {
        AnswerStatus.ANSWER_SUPPORTED,
        AnswerStatus.ANSWER_SUPPORTED_WITH_QUALIFICATIONS,
    }
    assert any(
        InfluenceReasonCode.EVIDENCE_AUTHORITY_DENIED in decision.reasons
        for decision in answer.influence_decisions
    ), "an unknown freshness must surface as EVIDENCE_AUTHORITY_DENIED"
