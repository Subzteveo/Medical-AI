"""A2 source-version-record and freshness tests (the trust root).

Negative controls (tampered digest, source-id mismatch, blank version, retracted/
superseded freshness) and positive/connector controls (the real PubMed and
ClinicalTrials.gov parsers emit verifiable records and explicit freshness). Every
answer, supported or not, carries the use notice. Synthetic, non-PHI data only.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from conftest import make_engine, synthetic_version_record
from medical_ai.authority_resolver import AuthorityResolver
from medical_ai.connectors.clinical_trials import ClinicalTrialsConnector
from medical_ai.connectors.pubmed import PubMedConnector
from medical_ai.schemas import (
    USE_NOTICE,
    AnswerStatus,
    ClaimRecord,
    ConsequenceLevel,
    EvidenceAuthorityState,
    FreshnessAssessment,
    FreshnessState,
    InfluenceReasonCode,
    SourceRecord,
    SourceVersionRecord,
    VerificationStatus,
    source_version_content_sha256,
)

_RESOLVER = AuthorityResolver()


def _claim() -> ClaimRecord:
    return ClaimRecord(
        claim_id="c1", claim_text="Treatment X reduced symptom scores.",
        consequence_level=ConsequenceLevel.MODERATE, evidence_ids=["e1"], source_ids=["s1"],
        verification_status=VerificationStatus.PASS, entailment_status="SUPPORTED_EXACT_PASSAGE",
    )


def _source(
    *, version_record: SourceVersionRecord | None, freshness_state: FreshnessState = FreshnessState.CURRENT
) -> SourceRecord:
    return SourceRecord(
        source_id="s1", authority="NLM/NCBI PubMed", publisher="Example Journal",
        source_type="indexed_biomedical_literature", title="T", record_id="r1",
        stable_url="https://pubmed.ncbi.nlm.nih.gov/r1/", identifiers={"PMID": "r1"},
        version_record=version_record,
        freshness=FreshnessAssessment(
            state=freshness_state, basis="test-fixture", assessed_at=datetime.now(timezone.utc)
        ),
    )


def _valid_record() -> SourceVersionRecord:
    return synthetic_version_record(
        source_id="s1", record_id="r1", upstream_version="r1.1",
        connector_name="test-connector", connector_version="test-v1",
    )


def _resolve(source: SourceRecord):
    return _RESOLVER.resolve_claim_authority(
        _claim(), source_class="biomedical_literature", public_non_phi=True,
        source_records=[source], trace_ref="t",
    )


def test_tampered_content_sha256_is_denied() -> None:
    record = _valid_record().model_copy(update={"content_sha256": "sha256:" + "0" * 64})
    res = _resolve(_source(version_record=record))
    assert not res.authorized
    assert res.evidence_authority is EvidenceAuthorityState.UNKNOWN


def test_source_id_mismatch_is_denied() -> None:
    record = _valid_record().model_copy(update={"source_id": "pubmed:other"})
    res = _resolve(_source(version_record=record))
    assert not res.authorized
    assert res.evidence_authority is EvidenceAuthorityState.UNKNOWN


def test_blank_upstream_version_is_denied() -> None:
    # A blank version is constructible but must be rejected at verification.
    record = SourceVersionRecord(
        source_id="s1", upstream_record_id="r1", upstream_version="",
        retrieved_at=datetime.now(timezone.utc), connector_name="test-connector",
        connector_version="test-v1",
        content_sha256=source_version_content_sha256(
            source_id="s1", upstream_record_id="r1", upstream_version=""
        ),
    )
    res = _resolve(_source(version_record=record))
    assert not res.authorized
    assert res.evidence_authority is EvidenceAuthorityState.UNKNOWN


def test_missing_record_is_denied() -> None:
    res = _resolve(_source(version_record=None))
    assert not res.authorized
    assert res.evidence_authority is EvidenceAuthorityState.UNKNOWN


@pytest.mark.parametrize("state", [FreshnessState.RETRACTED, FreshnessState.SUPERSEDED])
def test_retracted_and_superseded_freshness_are_denied(state: FreshnessState) -> None:
    res = _resolve(_source(version_record=_valid_record(), freshness_state=state))
    assert not res.authorized
    assert res.evidence_authority is EvidenceAuthorityState.DENIED


# --- Real PubMed parser -----------------------------------------------------

_SUPPORTED_ABSTRACT = (
    "This cross-sectional study sampled 30 university students. "
    "Mindfulness was associated with attention. "
    "This association does not establish causation or generalise to other populations."
)


def _pubmed_xml(*, version: str | None = "1", ref_type: str | None = None, abstract: str = _SUPPORTED_ABSTRACT) -> str:
    pmid = f'<PMID Version="{version}">555</PMID>' if version is not None else "<PMID>555</PMID>"
    corrections = (
        f'<CommentsCorrectionsList><CommentsCorrections RefType="{ref_type}"/></CommentsCorrectionsList>'
        if ref_type
        else ""
    )
    return (
        "<PubmedArticleSet><PubmedArticle><MedlineCitation>"
        f"{pmid}{corrections}"
        "<Article><ArticleTitle>Mindfulness and attention</ArticleTitle>"
        f"<Abstract><AbstractText>{abstract}</AbstractText></Abstract></Article>"
        "</MedlineCitation><PubmedData><ArticleIdList>"
        '<ArticleId IdType="pubmed">555</ArticleId></ArticleIdList></PubmedData>'
        "</PubmedArticle></PubmedArticleSet>"
    )


class _PubMedFixture(PubMedConnector):
    def __init__(self, xml: str) -> None:
        super().__init__()
        self._xml = xml

    async def search_and_fetch(self, query: str, limit: int = 5):
        return self._parse_pubmed_xml(self._xml)


def test_pubmed_parser_emits_verified_record_and_current_freshness() -> None:
    sources, _ = PubMedConnector._parse_pubmed_xml(_pubmed_xml())
    record = sources[0].version_record
    assert record is not None
    assert record.upstream_version == "555.1"
    assert record.source_id == sources[0].source_id
    assert record.content_sha256 == source_version_content_sha256(
        source_id=record.source_id, upstream_record_id=record.upstream_record_id,
        upstream_version=record.upstream_version,
    )
    assert sources[0].freshness is not None
    assert sources[0].freshness.state is FreshnessState.CURRENT


@pytest.mark.asyncio
async def test_real_pubmed_parser_supported_path() -> None:
    engine = make_engine(_PubMedFixture(_pubmed_xml()))
    answer = await engine.answer("Find literature about mindfulness and attention")
    assert answer.status == AnswerStatus.ANSWER_SUPPORTED_WITH_QUALIFICATIONS
    assert answer.claims
    assert answer.sources[0].version_record is not None
    assert answer.sources[0].freshness is not None and answer.sources[0].freshness.state is FreshnessState.CURRENT
    # Use notice present on a supported answer.
    assert answer.use_notice == USE_NOTICE
    assert USE_NOTICE in answer.answer_markdown


@pytest.mark.asyncio
async def test_pubmed_updatein_is_superseded_and_denied() -> None:
    engine = make_engine(_PubMedFixture(_pubmed_xml(ref_type="UpdateIn")))
    answer = await engine.answer("Find literature about mindfulness and attention")
    assert answer.claims == []
    assert answer.status not in {
        AnswerStatus.ANSWER_SUPPORTED, AnswerStatus.ANSWER_SUPPORTED_WITH_QUALIFICATIONS,
    }
    assert any(
        InfluenceReasonCode.EVIDENCE_AUTHORITY_DENIED in d.reasons for d in answer.influence_decisions
    )
    # Use notice present on a denied answer too.
    assert answer.use_notice == USE_NOTICE
    assert USE_NOTICE in answer.answer_markdown


def test_pubmed_parser_updatein_freshness_is_superseded() -> None:
    sources, _ = PubMedConnector._parse_pubmed_xml(_pubmed_xml(ref_type="UpdateIn"))
    assert sources[0].freshness is not None
    assert sources[0].freshness.state is FreshnessState.SUPERSEDED


def test_pubmed_parser_without_version_emits_no_record() -> None:
    sources, _ = PubMedConnector._parse_pubmed_xml(_pubmed_xml(version=None))
    assert sources[0].version_record is None


@pytest.mark.asyncio
async def test_pubmed_without_version_is_denied_unknown() -> None:
    engine = make_engine(_PubMedFixture(_pubmed_xml(version=None)))
    answer = await engine.answer("Find literature about mindfulness and attention")
    assert answer.claims == []
    assert any(
        InfluenceReasonCode.EVIDENCE_AUTHORITY_UNKNOWN in d.reasons for d in answer.influence_decisions
    )


# --- Real ClinicalTrials.gov parser ----------------------------------------

def _ctgov_payload(*, with_update: bool) -> dict:
    status = {"overallStatus": "RECRUITING"}
    if with_update:
        status["lastUpdateSubmitDate"] = "2026-09-20"
    return {"studies": [{"protocolSection": {
        "identificationModule": {"nctId": "NCT12345678", "briefTitle": "Example trial",
                                 "organization": {"fullName": "Example University"}},
        "statusModule": status,
        "designModule": {"studyType": "INTERVENTIONAL"},
        "conditionsModule": {"conditions": ["Hypertension"]},
    }}]}


def test_ctgov_parser_emits_record_with_update_date() -> None:
    sources, _ = ClinicalTrialsConnector._parse_payload(_ctgov_payload(with_update=True))
    record = sources[0].version_record
    assert record is not None
    assert record.upstream_version == "NCT12345678@2026-09-20"
    assert sources[0].freshness is not None and sources[0].freshness.state is FreshnessState.CURRENT


def test_ctgov_parser_emits_no_record_without_update_date() -> None:
    sources, _ = ClinicalTrialsConnector._parse_payload(_ctgov_payload(with_update=False))
    assert sources[0].version_record is None
    assert sources[0].freshness is not None and sources[0].freshness.state is FreshnessState.UNKNOWN


@pytest.mark.asyncio
async def test_terminal_answer_carries_use_notice() -> None:
    # A patient-specific request is blocked before any connector call; it is still an
    # answer and must carry the use notice.
    engine = make_engine(_PubMedFixture(_pubmed_xml()))
    answer = await engine.answer("My patient has symptoms; what dose of treatment X should I give?")
    assert answer.status == AnswerStatus.OUTSIDE_VALIDATED_CAPABILITY
    assert answer.use_notice == USE_NOTICE
    assert USE_NOTICE in answer.answer_markdown
