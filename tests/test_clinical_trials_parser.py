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
