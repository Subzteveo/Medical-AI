"""A2 residual authority RED regressions (Issue #25, A2 self-audit).

Two defects inside A2's own resolver code (``src/medical_ai/authority_resolver.py``)
at base ``main`` ``df50749eb669c4f8031f9050706f9fffbecea525`` are reproduced here as
RED regressions at the engine's observable influence-gate boundary. Both tests
are expected to FAIL against current code; neither this file nor the session
that writes it is authorised to repair them.

Independence limit
------------------
No runtime field can yet express "source-version record present" or "explicitly
current". Both tests therefore use the same kind of fixture (one public,
non-PHI source with no date fields and the default ``superseded=False``) and
will fail for the same observable reason. A later repair of one defect may
turn both green. Neither test isolates its defect.

Scope
-----
These tests only assert at the engine's observable boundary — the trace, the
``InfluenceDecision.allowed`` flag, its ``reasons`` list, the delivered claims
and the ``AnswerStatus``. They do not inspect internal reference strings,
resolver envelopes or policy decision records, and they do not add or assert
any reason-code name that does not already exist. Which existing
``InfluenceReasonCode`` should carry the explanation (candidates include
``EVIDENCE_AUTHORITY_UNKNOWN`` and ``VALIDATION_NOT_PASSED``) is for the repair
tranche to decide.
"""

from __future__ import annotations

import pytest

from conftest import make_engine
from medical_ai.schemas import (
    AnswerStatus,
    InformationClass,
    Passage,
    PHIClassification,
    SourceRecord,
    VerificationStatus,
)


_QUESTION = "What evidence shows treatment X reduces symptom scores?"
_SUPPORTING_TEXT = (
    "Treatment X reduced symptom scores compared with placebo "
    "in the studied adult population."
)


class _SyntheticConnector:
    """Minimal evidence-approved connector; one public, non-PHI source + passage.

    Fixture shape (recorded explicitly so the test documents what is and is not
    present at the resolver boundary):

    - ``SourceRecord.superseded`` defaults to ``False`` (``schemas.py`` line 155).
      This is the only freshness-state field on the runtime source model.
    - ``version``, ``publication_date``, ``updated_date`` and ``effective_date``
      are all left unset (``None``). No date field is supplied, so this fixture
      cannot be read as either "current" or "stale" from a date.
    - ``provenance_complete=True`` (the ``SourceRecord`` default).
    - ``PHIClassification.information_class=PUBLIC`` and ``contains_phi=False``.
    - No independently verified source-version record exists for this source;
      the resolver nevertheless builds a well-formed ``source-version:...``
      reference string from the source class and the claim id.
    """

    name = "synthetic-public"
    version = "a2-residual-red-v1"
    source_class = "biomedical_literature"
    evidence_approved = True
    phi_approved = False

    def __init__(self) -> None:
        self.called = False
        self._source = SourceRecord(
            source_id="synthetic:X1",
            authority="synthetic authority (test fixture)",
            publisher="synthetic publisher (test fixture)",
            source_type="indexed_biomedical_literature",
            title="Synthetic evidence about treatment X",
            record_id="X1",
            stable_url="https://example.invalid/X1",
            identifiers={"PMID": "X1"},
            # NOTE: no version, publication_date, updated_date, effective_date.
            phi_classification=PHIClassification(
                classification_id="public:synthetic:X1",
                object_id="synthetic:X1",
                information_class=InformationClass.PUBLIC,
                contains_phi=False,
            ),
        )
        self._passage = Passage(
            passage_id="sp1",
            source_id="synthetic:X1",
            section="RESULTS",
            text=_SUPPORTING_TEXT,
            locator="AbstractText[0]",
        )

    async def search_and_fetch(self, query: str, limit: int = 5):
        self.called = True
        return [self._source], [self._passage]


def _assert_reached_gate(answer) -> None:
    """A test that passes because the claim never reached the gate is invalid."""
    assert answer.trace.candidate_claim_ids, (
        "fixture must reach claim construction"
    )
    assert (
        VerificationStatus.PASS.value
        in answer.trace.verification_results.values()
    ), "fixture must exercise an otherwise verified claim"
    assert answer.influence_decisions, "fixture must reach the influence gate"


def _assert_withheld(answer) -> None:
    """Required behaviour at the observable boundary: DENY, no supported claim."""
    assert not any(d.allowed for d in answer.influence_decisions), (
        "a policy ALLOW alone must not grant medical influence; "
        "no supported claim without an independently resolvable authority record"
    )
    # A withheld decision must carry at least one reason code; the specific code
    # name is not asserted here (that belongs to the repair tranche).
    assert answer.influence_decisions[0].reasons, (
        "withheld InfluenceDecision must carry at least one reason code"
    )
    assert answer.claims == []
    assert answer.status != AnswerStatus.ANSWER_SUPPORTED_WITH_QUALIFICATIONS


@pytest.mark.asyncio
async def test_defect_a_unresolvable_source_version_record_must_withhold():
    """Defect A: reference strings do not resolve to verified records.

    At ``authority_resolver.py`` lines 219-222 (df50749) the resolver builds
    ``source-version:{source_class}:{claim.claim_id}`` and
    ``claim-evidence:{claim.claim_id}`` strings for the A1 decision envelope.
    Nothing establishes that these strings resolve to independently verified
    source-version or claim-evidence records. The engine then copies only the
    four authority *states* into the influence subject
    (``engine.py`` about lines 241-266); the envelopes and their reference
    strings are never passed on to user-visible output. The only reason the
    output carries is ``InfluenceDecision.reasons``, a closed
    ``InfluenceReasonCode`` enum with no source-version or claim-evidence
    member.

    Required behaviour at the observable boundary: DENY and no supported
    medical claim. A well-formed reference string is not evidence of an
    independently verified record.

    Expected against current code: RED.
    """
    connector = _SyntheticConnector()
    answer = await make_engine(connector).answer(_QUESTION)
    assert connector.called, "fixture must exercise the evidence engine"
    _assert_reached_gate(answer)
    _assert_withheld(answer)


@pytest.mark.asyncio
async def test_defect_b_absent_supersession_must_not_default_to_current():
    """Defect B: missing freshness collapses into ``FreshnessState.CURRENT``.

    At ``authority_resolver.py`` line 195 the resolver computes
    ``freshness = FreshnessState.SUPERSEDED if any_source_superseded else
    FreshnessState.CURRENT``. The parameter is a plain ``bool`` so "unknown"
    cannot be expressed at the resolver level.

    The runtime source model has only one freshness-state field
    (``SourceRecord.superseded: bool = False``; ``schemas.py`` line 155) and
    no field for "explicitly current" or "unknown". Date fields exist
    (``version``, ``publication_date``, ``updated_date``, ``effective_date``;
    lines 150-153) but nothing maps them to a freshness state. Separately,
    ``ClaimRecord.freshness_status`` defaults to the merged value
    ``"CURRENT_OR_NOT_ASSESSED"`` (line 202), which is the same defect in
    user-facing data (reported here, not changed).

    This fixture leaves every freshness-state field and every date field
    unset. The absence of a supersession flag is therefore the only
    "freshness" signal in play, and it does not establish currency.

    Required behaviour at the observable boundary: DENY or UNKNOWN, never a
    current-authority ALLOW, and no supported medical claim.

    Expected against current code: RED.
    """
    connector = _SyntheticConnector()
    answer = await make_engine(connector).answer(_QUESTION)
    assert connector.called, "fixture must exercise the evidence engine"
    _assert_reached_gate(answer)
    # Freshness-state and date fields are absent; document that in the assertion.
    assert connector._source.superseded is False
    assert connector._source.version is None
    assert connector._source.publication_date is None
    assert connector._source.updated_date is None
    assert connector._source.effective_date is None
    _assert_withheld(answer)
