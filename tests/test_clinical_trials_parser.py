from medical_ai.connectors.clinical_trials import ClinicalTrialsConnector

PAYLOAD = {
    "studies": [{
        "protocolSection": {
            "identificationModule": {
                "nctId": "NCT12345678",
                "briefTitle": "Example trial",
                "organization": {"fullName": "Example University"}
            },
            "statusModule": {"overallStatus": "RECRUITING", "lastUpdateSubmitDate": "2026-09-20"},
            "designModule": {"studyType": "INTERVENTIONAL", "phases": ["PHASE2"]},
            "conditionsModule": {"conditions": ["Hypertension"]},
            "descriptionModule": {"briefSummary": "This study evaluates treatment X in adults with hypertension."}
        }
    }]
}


def test_clinical_trials_payload_maps_to_source_and_passages():
    sources, passages = ClinicalTrialsConnector._parse_payload(PAYLOAD)
    assert sources[0].identifiers["NCT"] == "NCT12345678"
    assert sources[0].source_type == "clinical_trial_registry"
    assert sources[0].raw_metadata["overall_status"] == "RECRUITING"
    assert any("RECRUITING" in p.text for p in passages)
    assert any(p.section == "BRIEF_SUMMARY" for p in passages)


async def test_registry_title_sentences_keep_registry_attribution():
    """A title is registered metadata, never a standalone efficacy assertion."""
    from copy import deepcopy
    from medical_ai.engine import EvidenceEngine
    from medical_ai.schemas import AnswerStatus

    payload = deepcopy(PAYLOAD)
    title = "Example trial. Treatment X cures insomnia."
    payload["studies"][0]["protocolSection"]["identificationModule"]["briefTitle"] = title

    class FixtureConnector(ClinicalTrialsConnector):
        async def search_and_fetch(self, query, limit=5):
            return self._parse_payload(payload)

    answer = await EvidenceEngine(FixtureConnector()).answer("Find clinical trials for insomnia")
    assert answer.status == AnswerStatus.ANSWER_SUPPORTED_WITH_QUALIFICATIONS
    title_claims = [c.claim_text for c in answer.claims if "cures insomnia" in c.claim_text]
    assert title_claims == [f"ClinicalTrials.gov lists NCT12345678 with the title: {title}."]
    assert all(c.claim_text.startswith(("ClinicalTrials.gov lists", "The registry", "The registered")) for c in answer.claims)


def test_registry_fact_locators_resolve_to_original_api_fields():
    _, passages = ClinicalTrialsConnector._parse_payload(PAYLOAD)
    expected = {
        "protocolSection.identificationModule.briefTitle": "Example trial",
        "protocolSection.statusModule.overallStatus": "RECRUITING",
        "protocolSection.designModule.studyType": "INTERVENTIONAL",
        "protocolSection.designModule.phases": ["PHASE2"],
        "protocolSection.conditionsModule.conditions": ["Hypertension"],
    }
    facts = [p for p in passages if p.section == "REGISTRY_FACT"]
    assert {p.locator for p in facts} == set(expected)
    for passage in facts:
        value = PAYLOAD["studies"][0]
        for key in passage.locator.split("."):
            value = value[key]
        assert value == expected[passage.locator]


def test_registry_official_title_fallback_has_correct_locator():
    from copy import deepcopy
    payload = deepcopy(PAYLOAD)
    identification = payload["studies"][0]["protocolSection"]["identificationModule"]
    identification["officialTitle"] = identification.pop("briefTitle")
    _, passages = ClinicalTrialsConnector._parse_payload(payload)
    assert passages[0].locator == "protocolSection.identificationModule.officialTitle"
