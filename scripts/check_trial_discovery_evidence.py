"""Check a captured trial-discovery answer against original API response fields.

Offline engineering evidence only: does not assess medical efficacy, study quality,
registry accuracy, or current recruitment. Inputs are public test-run captures.
Usage: python scripts/check_trial_discovery_evidence.py ORIGINAL.json ANSWER.json
ORIGINAL.json is the HTTP capture envelope with a `body.studies` array.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def check(original: dict, answer: dict) -> dict:
    assert original["status"] == 200
    assert answer["status"] == "ANSWER_SUPPORTED_WITH_QUALIFICATIONS"
    studies = {s["protocolSection"]["identificationModule"]["nctId"]: s for s in original["body"]["studies"]}
    sources = {s["source_id"]: s for s in answer["sources"]}
    passages = {p["passage_id"]: p for p in answer["passages"]}
    evidence = {e["evidence_id"]: e for e in answer["evidence_objects"]}
    checked = []
    for claim in answer["claims"]:
        assert len(claim["evidence_ids"]) == 1
        unit = evidence[claim["evidence_ids"][0]]
        assert len(unit["passage_ids"]) == 1
        passage = passages[unit["passage_ids"][0]]
        source = sources[unit["source_id"]]
        nct = source["record_id"]
        study = studies[nct]
        value = study
        for key in passage["locator"].split("."):
            value = value[key]
        field = passage["locator"]
        prefix = "protocolSection."
        if field in {prefix + "identificationModule.briefTitle", prefix + "identificationModule.officialTitle", prefix + "identificationModule.nctId"}:
            expected = f"ClinicalTrials.gov lists {nct} with the title: {value}."
        elif field == prefix + "statusModule.overallStatus":
            expected = f"The registry status for {nct} is {value}."
        elif field == prefix + "designModule.studyType":
            expected = f"The registered study type for {nct} is {value}."
        elif field == prefix + "designModule.phases":
            expected = f"The registered phase for {nct} is {', '.join(value)}."
        elif field == prefix + "conditionsModule.conditions":
            expected = f"The registered conditions for {nct} include {', '.join(value)}."
        else:
            raise AssertionError(f"Unsupported registry fact field: {field}")
        assert claim["claim_text"] == unit["proposition"] == passage["text"] == expected
        assert claim["source_ids"] == [source["source_id"]]
        assert passage["source_id"] == source["source_id"]
        assert source["stable_url"] == f"https://clinicaltrials.gov/study/{nct}"
        assert any(m["claim_id"] == claim["claim_id"] and m["source_id"] == source["source_id"] and m["passage_ids"] == [passage["passage_id"]] for m in answer["citation_mappings"])
        checked.append({"claim": expected, "original_field": field, "original_value": value, "citation": source["stable_url"]})
    assert checked, "No displayed claims to verify"
    return {"result": "PASS", "scope": "Exact registry-field attribution and citation identity; not clinical validation", "checked_claims": checked}


if __name__ == "__main__":
    print(json.dumps(check(json.loads(Path(sys.argv[1]).read_text()), json.loads(Path(sys.argv[2]).read_text())), indent=2))
