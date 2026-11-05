"""A2 residual-authority RED regressions (gate before A3).

Two residual gaps inside A2's own resolver code (``authority_resolver.py``),
reproduced at the observable engine boundary. These are NOT the pre-A2 gap that
``tests/test_authority_origin_regression.py`` already covers (that regression is
green at ``df50749``); they are defects that survive *inside* the merged A2
resolver.

Defect A — unresolvable source-version authority
    The resolver builds reference strings such as
    ``source-version:<class>:<claim_id>`` and ``claim-evidence:<claim_id>`` but
    nothing establishes that they resolve to independently verified
    source-version records. A policy ALLOW plus a well-formed reference string is
    treated as authority. The reference string never reaches the engine output
    (``engine.py`` copies only the four authority states into the influence
    subject), so the defect is proven through the observable result: a supported
    medical claim appears even though no source-version record exists.

Defect B — missing freshness defaults to CURRENT
    ``authority_resolver.resolve_claim_authority`` receives a plain ``bool``
    (``any_source_superseded``) and computes
    ``SUPERSEDED if any_source_superseded else CURRENT`` (about line 195). The
    boolean cannot express "unknown", so the *absence* of a supersession flag is
    silently treated as current authority.

Observable RED contract (shared by both tests, per the v6 prompt):
    "traceable" at the boundary means the claim's ``InfluenceDecision`` is not
    allowed and its ``reasons`` list is not empty. No reason *name* is asserted,
    and none is added: the closed ``InfluenceReasonCode`` enum has no
    source-version or freshness member today, and choosing one belongs to the A2
    repair tranche, not here.

Independence limit:
    No runtime field can yet express "source-version record present" or
    "explicitly current", so both tests necessarily use the same kind of fixture
    and fail for the same observable reason. A later repair of either defect may
    turn both green. Neither test isolates its defect from the other.

Fixtures use synthetic, non-PHI data only. Against ``df50749`` both tests are
expected to FAIL (RED): the current engine returns a supported, allowed claim.
"""

from __future__ import annotations

import pytest

from conftest import FakePubMedConnector
from medical_ai.authority_resolver import AuthorityResolver, ClaimAuthorityResolution
from medical_ai.engine import EvidenceEngine
from medical_ai.schemas import AnswerStatus, VerificationStatus

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
        any_source_superseded: bool,
        trace_ref: str,
    ) -> ClaimAuthorityResolution:
        resolution = super().resolve_claim_authority(
            claim,
            source_class=source_class,
            public_non_phi=public_non_phi,
            any_source_superseded=any_source_superseded,
            trace_ref=trace_ref,
        )
        self.calls.append(
            {
                "claim_id": claim.claim_id,
                "source_class": source_class,
                "public_non_phi": public_non_phi,
                "any_source_superseded": any_source_superseded,
            }
        )
        self.resolutions.append(resolution)
        return resolution


@pytest.mark.asyncio
async def test_defect_a_reference_string_is_not_a_resolved_source_version_record():
    """Defect A: a well-formed source-version reference string, backed by no
    independently verified record, must not yield a supported medical claim.

    RED against df50749: the engine returns an ALLOW decision and a supported
    claim because the resolver treats the policy ALLOW plus the reference string
    as authority.
    """
    resolver = _RecordingResolver()
    # The shared fixture carries publication_date="2026" (a *date* field, not a
    # freshness state) and no source-version record of any kind.
    connector = FakePubMedConnector()
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

    # 2. Diagnostic (NOT the RED assertion): the resolver authorised this claim on
    #    a policy ALLOW plus a well-formed source-version reference *string*, with
    #    no backing source-version record. The string never reaches the engine
    #    output, so the defect can only be proven through the observable result.
    resolution = resolver.resolutions[0]
    resolved_claim_id = resolver.calls[0]["claim_id"]
    source_version_refs = [
        getattr(decision, "source_version_ref", None) for decision in resolution.decisions
    ]
    assert f"source-version:biomedical_literature:{resolved_claim_id}" in source_version_refs, (
        "resolver emits only a reference string, not a resolved source-version record"
    )
    assert resolution.authorized, (
        "diagnostic baseline: current resolver treats the reference string as "
        "sufficient authority (this is the behaviour under test)"
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


@pytest.mark.asyncio
async def test_defect_b_missing_freshness_must_not_default_to_current_allow():
    """Defect B: admitted evidence carrying no freshness-state or retraction
    metadata must not be treated as current authority.

    RED against df50749: the engine returns an ALLOW decision and a supported
    claim because ``any_source_superseded`` is False (the absence of a
    supersession flag is indistinguishable from "not superseded").
    """
    base = FakePubMedConnector()
    # Strip the only non-default date the fixture carries so freshness is
    # genuinely ABSENT, not set to a convenient value. ``superseded`` stays at its
    # default (False) — the only freshness-state field on the runtime source model
    # (schemas.py line 155) — and version/updated_date/effective_date are already
    # None. No freshness state and no retraction state are set anywhere.
    freshnessless = base.sources[0].model_copy(update={"publication_date": None})
    resolver = _RecordingResolver()
    connector = FakePubMedConnector([freshnessless], base.passages)
    engine = EvidenceEngine(connector, authority_resolver=resolver)

    answer = await engine.answer(_QUESTION)

    # Freshness is genuinely absent from the input (reported, not asserted away):
    src = connector.sources[0]
    assert src.superseded is False, "supersession flag left unset (defaults to False)"
    assert src.version is None
    assert src.publication_date is None
    assert src.updated_date is None
    assert src.effective_date is None

    # 1. The evidence reaches the resolver, and the engine can only pass a plain
    #    bool, so "unknown freshness" is indistinguishable from "not superseded".
    assert connector.called, "fixture must exercise the evidence engine"
    assert resolver.calls, "evidence must reach the authority resolver"
    assert resolver.calls[0]["any_source_superseded"] is False, (
        "the engine passes only a bool; absence of a supersession flag is "
        "indistinguishable from 'not superseded'"
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
