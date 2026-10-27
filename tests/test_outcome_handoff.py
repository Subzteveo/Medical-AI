"""One controlled research-task handoff; this is not a clinical/user-value study."""
from __future__ import annotations

import json

import pytest

from medical_ai.connectors.clinical_trials import ClinicalTrialsConnector
from medical_ai.engine import EvidenceEngine
from medical_ai.outcome_handoff import build_research_outcome_handoff
from medical_ai.schemas import AnswerStatus, DependencyDimension
from test_pubmed_context import FixtureConnector, xml_abstract

BASE = "56825f009cffc0acbb99c54124f5173705ce4d0d"
CANDIDATE = "a" * 40
KW = {"task_id": "literature-context-001", "baseline_revision": BASE, "candidate_revision": CANDIDATE}


def project(engine, answer, **kw):
    return build_research_outcome_handoff(answer, engine=engine, **(KW | kw))


async def supported():
    xml = xml_abstract(
        ("METHODS", "We surveyed thirty university students at one time point."),
        ("RESULTS", "Mindfulness was associated with attention."),
        ("CONCLUSION", "Causal effects cannot be inferred from this study design."),
    )
    engine = EvidenceEngine(FixtureConnector(xml))
    answer = await engine.answer("Find literature about mindfulness and attention")
    assert answer.status == AnswerStatus.ANSWER_SUPPORTED_WITH_QUALIFICATIONS
    return engine, answer


@pytest.mark.asyncio
async def test_supported_context_is_read_only_and_has_authorised_graph_only():
    engine, answer = await supported()
    original = answer.model_dump(mode="json")
    n_decisions = len(engine.influence_controller.decisions)
    item = project(engine, answer)
    assert item["handoff_disposition"] == "ENGINEERING_INSPECTION_ONLY"
    assert item["current_authorization"] == "RECHECKED_BY_ISSUING_CONTROLLER"
    assert item["outcome_alignment_verdict"] == "NOT_ESTABLISHED"
    assert item["commercial_release"] == "NOT_AUTHORIZED"
    assert item["snapshot_comparison"] == "UNKNOWN"
    assert item["baseline_revision"] == BASE and item["candidate_revision"] == CANDIDATE
    assert item["query_digests"] == answer.trace.retrieval_query_digests
    assert {edge["claim_id"] for edge in item["provenance_graph"]} == {c.claim_id for c in answer.claims}
    assert {edge["source_id"] for edge in item["provenance_graph"]} == {s.source_id for s in answer.sources}
    assert set(item["provenance_graph"][0]["passage_ids"]) == {p.passage_id for p in answer.passages}
    assert item["authorization_decision_ids"] == [d.decision_id for d in answer.influence_decisions if d.allowed]
    assert "METHODS" in answer.claims[0].claim_text
    assert "CONCLUSION" in answer.claims[0].claim_text
    # No source text, raw question, rendered text or medical claim may cross the OA seam.
    payload = json.dumps(item)
    for phrase in ("We surveyed", "Mindfulness was associated", "Causal effects", "Find literature"):
        assert phrase not in payload
    assert answer.model_dump(mode="json") == original
    assert len(engine.influence_controller.decisions) == n_decisions


@pytest.mark.asyncio
async def test_existing_registry_attribution_survives_without_rewriting_claims():
    title = "Example trial. Treatment X cures insomnia."
    payload = {"studies": [{"protocolSection": {
        "identificationModule": {"nctId": "NCT12345678", "briefTitle": title, "organization": {"fullName": "University"}},
        "statusModule": {"overallStatus": "RECRUITING"},
        "designModule": {"studyType": "INTERVENTIONAL"},
        "conditionsModule": {"conditions": ["Insomnia"]},
    }}]}
    class RegistryFixture(ClinicalTrialsConnector):
        async def search_and_fetch(self, query, limit=5):
            return self._parse_payload(payload)
    engine = EvidenceEngine(RegistryFixture())
    answer = await engine.answer("Find clinical trials for insomnia")
    assert answer.status == AnswerStatus.ANSWER_SUPPORTED_WITH_QUALIFICATIONS
    assert any(c.claim_text == f"ClinicalTrials.gov lists NCT12345678 with the title: {title}." for c in answer.claims)
    assert all(p.locator.startswith("protocolSection.") for p in answer.passages)
    item = project(engine, answer, task_id="registry-context-001")
    assert item["handoff_disposition"] == "ENGINEERING_INSPECTION_ONLY"
    assert item["provenance_graph"]
    assert title not in json.dumps(item)


@pytest.mark.asyncio
@pytest.mark.parametrize("mutation", ["claim", "citation", "passage", "markdown", "missing_source"])
async def test_tampered_output_never_promotes_to_outcome(mutation):
    engine, answer = await supported()
    tampered = answer.model_copy(deep=True)
    if mutation == "claim":
        tampered.claims[0].claim_text = "Mindfulness cures every condition."
    elif mutation == "citation":
        tampered.citation_mappings[0].source_id = "pubmed:forged"
    elif mutation == "passage":
        tampered.passages[0].text = "Misleading isolated text."
    elif mutation == "markdown":
        tampered.answer_markdown = "A fabricated medical conclusion"
    else:
        tampered.sources = []
    result = project(engine, tampered)
    assert result["handoff_disposition"] == "WITHHELD"
    assert result["outcome_alignment_verdict"] == "NOT_ESTABLISHED"
    assert result["provenance_graph"] == []
    assert result["source_ids"] == []
    assert result["authorization_decision_ids"] == []
    assert result["query_digests"] == []


@pytest.mark.asyncio
async def test_authority_revocation_is_not_bypassed_by_detached_allow():
    engine, answer = await supported()
    claim_id = answer.claims[0].claim_id
    assert project(engine, answer)["handoff_disposition"] == "ENGINEERING_INSPECTION_ONLY"
    engine.influence_controller.revoke_authority(claim_id, DependencyDimension.EVIDENCE_AUTHORITY)
    result = project(engine, answer)
    assert result["handoff_disposition"] == "WITHHELD"
    assert result["provenance_graph"] == []
    assert result["current_authorization"] == "NOT_ESTABLISHED"


@pytest.mark.asyncio
async def test_source_snapshot_mismatch_invalidates_handoff_not_medical_runtime():
    engine, answer = await supported()
    ids = {s.source_id for s in answer.sources}
    matching = {source_id: "1" * 64 for source_id in ids}
    changed = {source_id: "2" * 64 for source_id in ids}
    before = answer.model_dump(mode="json")
    result = project(engine, answer, expected_source_sha256=matching, observed_source_sha256=changed)
    assert result["snapshot_comparison"] == "MISSING_OR_CHANGED_SOURCE_HOLD"
    assert result["provenance_graph"] == [] and result["source_ids"] == []
    assert result["outcome_alignment_verdict"] == "NOT_ESTABLISHED"
    matched = project(engine, answer, expected_source_sha256=matching, observed_source_sha256=matching)
    assert matched["snapshot_comparison"] == "SUPPLIED_DIGESTS_MATCH_NOT_INDEPENDENTLY_AUTHENTICATED"
    assert matched["outcome_alignment_verdict"] == "NOT_ESTABLISHED"
    assert answer.model_dump(mode="json") == before


@pytest.mark.asyncio
async def test_withheld_high_consequence_and_no_source_exposure():
    xml = xml_abstract(("", "The tacrolimus-by-age-by-sex interaction was significant. Mindfulness and attention were measured."))
    engine = EvidenceEngine(FixtureConnector(xml))
    answer = await engine.answer("Find literature about mindfulness and attention")
    assert answer.status == AnswerStatus.HIGH_CONSEQUENCE_VERIFICATION_FAILED
    item = project(engine, answer)
    assert item["handoff_disposition"] == "WITHHELD"
    assert item["provenance_graph"] == [] and item["source_ids"] == []
    assert "tacrolimus" not in json.dumps(item)
    assert item["runtime_answer_status"] == "HIGH_CONSEQUENCE_VERIFICATION_FAILED"


@pytest.mark.asyncio
async def test_patient_specific_and_regulator_routes_export_no_content_or_claims():
    engine = EvidenceEngine(FixtureConnector(xml_abstract(("", "Mindfulness and attention were measured."))))
    for task, question, status in [
        ("patient-block-001", "My patient needs a warfarin dose", AnswerStatus.OUTSIDE_VALIDATED_CAPABILITY),
        ("regulator-block-001", "Is mindfulness approved by the TGA?", AnswerStatus.NO_AUTHORITATIVE_SOURCE),
    ]:
        answer = await engine.answer(question)
        assert answer.status == status
        item = project(engine, answer, task_id=task)
        assert item["source_ids"] == [] and item["provenance_graph"] == []
        assert "warfarin" not in json.dumps(item) and "mindfulness approved" not in json.dumps(item)


def test_handoff_requires_exact_revisions_and_complete_digest_pair():
    from medical_ai.schemas import EvidenceAnswer, ExecutionTrace, QueryPlan, ConsequenceLevel
    from medical_ai.schemas import AnswerStatus
    engine = EvidenceEngine(FixtureConnector(xml_abstract(("", "Mindfulness and attention were measured."))))
    answer = EvidenceAnswer(
        status=AnswerStatus.EVIDENCE_INSUFFICIENT, answer_markdown="Not established",
        claims=[], sources=[], trace=ExecutionTrace(
            trace_id="trace", query_plan=QueryPlan(
                intent=["EVIDENCE_SYNTHESIS"], user_mode="researcher", patient_specific=False,
                jurisdiction="AU", temporal_sensitivity="moderate",
                consequence_level=ConsequenceLevel.MODERATE, required_source_classes=["biomedical_literature"],
                retrieval_questions=["no raw text exported"]),
            retrieval_query_digests=[], connectors_used=[], source_ids=[],
            evidence_ids=[], candidate_claim_ids=[], verification_results={},
            safety_flags=[], component_versions={}, final_status=AnswerStatus.EVIDENCE_INSUFFICIENT),
    )
    with pytest.raises(ValueError, match="40-character"):
        project(engine, answer, candidate_revision="main")
    with pytest.raises(ValueError, match="both expected and observed"):
        project(engine, answer, expected_source_sha256={"pubmed:123": "1" * 64})
    with pytest.raises(ValueError, match="opaque non-content"):
        project(engine, answer, task_id="my private patient identifier")
