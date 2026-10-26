"""Output integrity uses real engine, renderer, schema and authenticated API interfaces.

All records are synthetic. These tests establish structural safety, not clinical validity.
"""
from copy import deepcopy

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from medical_ai import api
from medical_ai.engine import EvidenceEngine
from medical_ai.renderer import render_answer
from medical_ai.schemas import AnswerStatus, DependencyDimension, EvidenceAnswer
from test_api_ui import TOKEN, _configure


QUESTION = "What evidence exists about treatment X?"
UNSAFE_URLS = [
    "javascript:alert(1)", "data:text/html,unsafe", "http://example.org/",
    "//example.org/", "https:example.org", "https://", "https://user@example.org/",
    "https://example.org:bad/", "https://example.org\\@evil.test/",
    "https://exam\nple.org/", " https://example.org/",
]
MUTATIONS = [
    "missing_source", "duplicate_source", "empty_source_id", "missing_claim_source",
    "duplicate_claim_source", "missing_evidence", "duplicate_evidence",
    "missing_passage", "duplicate_passage", "wrong_passage_source", "wrong_evidence_source",
    "wrong_proposition", "unsupported_passage", "missing_mapping", "duplicate_mapping",
    "wrong_mapping_source", "wrong_mapping_passage", "unverified_mapping",
    "empty_supported", "claims_in_abstention", "trace_status", "trace_claim",
    "missing_decision", "duplicate_decision", "revoked_decision", "wrong_decision_object",
]


def corrupt(payload, case):
    data = deepcopy(payload)
    if case == "missing_source": data["sources"] = []
    elif case == "duplicate_source": data["sources"].append(deepcopy(data["sources"][0]))
    elif case == "empty_source_id": data["sources"][0]["source_id"] = ""
    elif case == "missing_claim_source": data["claims"][0]["source_ids"] = ["absent"]
    elif case == "duplicate_claim_source": data["claims"][0]["source_ids"] *= 2
    elif case == "missing_evidence": data["evidence_objects"] = []
    elif case == "duplicate_evidence": data["evidence_objects"].append(deepcopy(data["evidence_objects"][0]))
    elif case == "missing_passage": data["passages"] = []
    elif case == "duplicate_passage": data["passages"].append(deepcopy(data["passages"][0]))
    elif case == "wrong_passage_source": data["passages"][0]["source_id"] = "absent"
    elif case == "wrong_evidence_source": data["evidence_objects"][0]["source_id"] = "absent"
    elif case == "wrong_proposition": data["evidence_objects"][0]["proposition"] = "Unrelated assertion."
    elif case == "unsupported_passage": data["passages"][0]["text"] = "Unrelated passage."
    elif case == "missing_mapping": data["citation_mappings"] = []
    elif case == "duplicate_mapping": data["citation_mappings"].append(deepcopy(data["citation_mappings"][0]))
    elif case == "wrong_mapping_source": data["citation_mappings"][0]["source_id"] = "absent"
    elif case == "wrong_mapping_passage": data["citation_mappings"][0]["passage_ids"] = ["absent"]
    elif case == "unverified_mapping": data["citation_mappings"][0]["verified"] = False
    elif case == "empty_supported": data["claims"] = []
    elif case == "claims_in_abstention": data["status"] = data["trace"]["final_status"] = "EVIDENCE_INSUFFICIENT"
    elif case == "trace_status": data["trace"]["final_status"] = "EVIDENCE_INSUFFICIENT"
    elif case == "trace_claim": data["trace"]["candidate_claim_ids"] = []
    elif case == "missing_decision": data["influence_decisions"] = []
    elif case == "duplicate_decision": data["influence_decisions"].append(deepcopy(data["influence_decisions"][0]))
    elif case == "revoked_decision": data["influence_decisions"][0]["authorization"]["state"] = "REVOKED"
    elif case == "wrong_decision_object": data["influence_decisions"][0]["object_id"] = "absent"
    else: raise AssertionError(case)
    return data


@pytest.fixture
async def supported(fake_connector):
    engine = EvidenceEngine(fake_connector)
    result = await engine.answer(QUESTION)
    assert result.status == AnswerStatus.ANSWER_SUPPORTED_WITH_QUALIFICATIONS
    assert result.claims
    return engine, result


@pytest.mark.parametrize("case", MUTATIONS)
async def test_response_schema_rejects_broken_provenance(supported, case):
    _, result = supported
    with pytest.raises(ValidationError):
        EvidenceAnswer.model_validate(corrupt(result.model_dump(mode="json"), case))


@pytest.mark.parametrize("url", UNSAFE_URLS)
async def test_response_schema_rejects_unsafe_links(supported, url):
    _, result = supported
    data = result.model_dump(mode="json")
    data["sources"][0]["stable_url"] = url
    with pytest.raises(ValidationError):
        EvidenceAnswer.model_validate(data)


async def test_renderer_rejects_orphan_even_with_real_controller_authorization(supported):
    engine, result = supported
    view = engine.influence_controller.build_authorized_claim_view(result.claims[0], result.influence_decisions[0])
    with pytest.raises(ValueError):
        render_answer([view], [], influence_controller=engine.influence_controller)


async def test_renderer_still_rejects_revoked_authorization(supported):
    engine, result = supported
    view = engine.influence_controller.build_authorized_claim_view(result.claims[0], result.influence_decisions[0])
    engine.influence_controller.revoke_authority(view.claim.claim_id, DependencyDimension.EVIDENCE_AUTHORITY)
    with pytest.raises(ValueError, match="revoked|active"):
        render_answer([view], result.sources, influence_controller=engine.influence_controller)


async def test_valid_response_round_trips_without_loss(supported):
    _, result = supported
    assert EvidenceAnswer.model_validate_json(result.model_dump_json()) == result
    assert result.claims[0].claim_text in result.passages[0].text
    assert result.sources[0].stable_url in result.answer_markdown


@pytest.mark.parametrize("case", ["duplicate_source", "duplicate_passage", "wrong_passage_source", "unsafe_link"])
async def test_engine_fails_closed_on_ambiguous_connector_records(fake_connector, case):
    if case == "duplicate_source": fake_connector.sources *= 2
    elif case == "duplicate_passage": fake_connector.passages *= 2
    elif case == "wrong_passage_source": fake_connector.passages[0].source_id = "absent"
    else: fake_connector.sources[0].stable_url = "javascript:alert(1)"
    result = await EvidenceEngine(fake_connector).answer(QUESTION)
    assert result.status == AnswerStatus.PROVENANCE_INCOMPLETE
    assert not result.claims and not result.sources and not result.passages
    assert "Treatment X reduced" not in result.answer_markdown


@pytest.mark.parametrize("case", ["positive", "missing_source", "duplicate_source", "revoked", "forged_decision", "markdown_injection"])
async def test_authenticated_api_rechecks_output_and_live_authorization(supported, monkeypatch, case):
    engine, result = supported
    original_text = result.claims[0].claim_text
    if case == "missing_source": result.sources.clear()
    elif case == "duplicate_source": result.sources.append(result.sources[0])
    elif case == "revoked":
        engine.influence_controller.revoke_authority(result.claims[0].claim_id, DependencyDimension.EVIDENCE_AUTHORITY)
    elif case == "forged_decision": result.influence_decisions[0].policy_version = "caller-invented-policy"
    elif case == "markdown_injection": result.answer_markdown = "UNAUTHORISED_OUTPUT_SENTINEL"

    async def tampered_answer(*args, **kwargs): return result
    monkeypatch.setattr(engine, "answer", tampered_answer)
    monkeypatch.setattr(api, "build_engine", lambda: engine)
    _configure(monkeypatch)
    with TestClient(api.app) as client:
        assert client.post("/access/session", json={"token": TOKEN}).status_code == 200
        response = client.post("/v1/evidence/query", json={"question": QUESTION})
    assert response.status_code == 200
    data = response.json()
    if case in {"positive", "markdown_injection"}:
        assert data["status"] == "ANSWER_SUPPORTED_WITH_QUALIFICATIONS"
        assert data["claims"][0]["claim_text"] == original_text
        assert "UNAUTHORISED_OUTPUT_SENTINEL" not in data["answer_markdown"]
    else:
        assert data["status"] in {"PROVENANCE_INCOMPLETE", "INFLUENCE_DENIED"}
        assert not data["claims"] and not data["sources"]
        assert original_text not in response.text


@pytest.mark.parametrize("separator", ["\n- ", "\r\n- ", "\r- ", "\n1) ", "\n# "])
async def test_multiline_source_claim_is_one_markdown_list_item(fake_connector, separator):
    """One authorised claim must remain one Markdown item even with source line breaks."""
    text = (
        "Treatment X reduced symptom scores" + separator
        + "additional recorded context compared with placebo in the studied adult population."
    )
    fake_connector.passages[0].text = text
    engine = EvidenceEngine(fake_connector)
    response = await engine.answer(QUESTION)

    assert response.status == AnswerStatus.ANSWER_SUPPORTED_WITH_QUALIFICATIONS
    assert len(response.claims) == 1
    assert response.claims[0].claim_text == text
    assert response.passages[0].text == text

    claim_block = response.answer_markdown.split("\n\n### Sources", 1)[0].split(
        "### Evidence-bound answer\n\n", 1
    )[1]
    assert claim_block.startswith("- ")
    assert len(claim_block.splitlines()) == 1, claim_block
    assert "additional recorded context" in claim_block

    checked = engine.revalidate_output(response)
    assert checked.status == response.status
    assert checked.answer_markdown == response.answer_markdown


async def test_multiline_source_title_and_identifier_remain_one_markdown_item(fake_connector):
    """Untrusted source display fields cannot forge extra Markdown source/citation items."""
    original_title = "Evidence about treatment X\n- apparent additional citation"
    fake_connector.sources[0].title = original_title
    fake_connector.sources[0].identifiers["PMID"] = "123\n- apparent additional reference"
    response = await EvidenceEngine(fake_connector).answer(QUESTION)

    assert response.status == AnswerStatus.ANSWER_SUPPORTED_WITH_QUALIFICATIONS
    assert response.sources[0].title == original_title
    assert response.sources[0].identifiers["PMID"].endswith("additional reference")
    claim_block, source_block = response.answer_markdown.split("\n\n### Sources\n", 1)
    assert len(claim_block.split("### Evidence-bound answer\n\n", 1)[1].splitlines()) == 1
    assert len(source_block.split("\n\n*Alpha2", 1)[0].splitlines()) == 1
