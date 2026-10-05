from __future__ import annotations

import pytest

from medical_ai.evals.alpha3_evidence_fidelity import (
    default_case_set_path,
    evaluate_case_set,
    load_case_set,
)


def _case(case_set, case_id: str):
    return next(case for case in case_set.cases if case.case_id == case_id)


@pytest.mark.asyncio
async def test_alpha3_harness_baseline_case_set_passes_required_checks():
    case_set = load_case_set(default_case_set_path())
    report = await evaluate_case_set(case_set)
    assert report.counts["total_cases"] == 6
    assert report.counts["required_cases"] == 4
    assert report.counts["required_failed"] == 0
    assert report.counts["blocked_checks"] == 2
    assert report.harness_failures == []


@pytest.mark.asyncio
async def test_alpha3_harness_fails_when_expected_rejection_is_reported_supported():
    case_set = load_case_set(default_case_set_path()).model_copy(deep=True)
    supported_case = _case(case_set, "ALPHA3-FIX-001-SUPPORTED")
    supported_case.expected_terminal_state = "PROVENANCE_INCOMPLETE"
    supported_case.expected_failure_code = "PROVENANCE_INCOMPLETE"

    report = await evaluate_case_set(case_set)
    assert report.counts["required_failed"] >= 1
    assert any(
        "ALPHA3-FIX-001-SUPPORTED: expected terminal state PROVENANCE_INCOMPLETE" in failure
        for failure in report.failures
    )


@pytest.mark.asyncio
async def test_alpha3_harness_fails_when_required_provenance_is_missing():
    case_set = load_case_set(default_case_set_path()).model_copy(deep=True)
    supported_case = _case(case_set, "ALPHA3-FIX-001-SUPPORTED")
    supported_case.scenario.sources[0].provenance_complete = False

    report = await evaluate_case_set(case_set)
    case_result = next(result for result in report.case_results if result.case_id == "ALPHA3-FIX-001-SUPPORTED")
    assert case_result.outcome == "FAIL"
    assert any("required provenance completeness was not satisfied" in failure for failure in case_result.failures)


@pytest.mark.asyncio
async def test_alpha3_harness_fails_when_expected_failure_code_differs():
    case_set = load_case_set(default_case_set_path()).model_copy(deep=True)
    outage_case = _case(case_set, "ALPHA3-FIX-003-SOURCE-UNAVAILABLE")
    outage_case.expected_failure_code = "CONNECTOR_ERROR:TimeoutError"

    report = await evaluate_case_set(case_set)
    assert report.counts["required_failed"] >= 1
    assert any(
        "ALPHA3-FIX-003-SOURCE-UNAVAILABLE: expected failure code CONNECTOR_ERROR:TimeoutError" in failure
        for failure in report.failures
    )


@pytest.mark.asyncio
async def test_alpha3_harness_fails_when_required_case_is_not_executed():
    case_set = load_case_set(default_case_set_path())
    required_case_ids = set(case_set.required_case_ids)
    required_case_ids.add("ALPHA3-FIX-999-MISSING")

    report = await evaluate_case_set(case_set, required_case_ids=required_case_ids)
    assert report.counts["harness_failures"] == 1
    assert "required case IDs were not executed: ALPHA3-FIX-999-MISSING" in report.harness_failures[0]
