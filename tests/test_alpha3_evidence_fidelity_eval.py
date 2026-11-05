from __future__ import annotations

import pytest

from medical_ai.evals.alpha3_evidence_fidelity import (
    default_case_set_path,
    evaluate_case_set,
    load_case_set,
)
from conftest import make_engine


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
    required_case_ids = set(case_set.execution_case_ids)
    required_case_ids.add("ALPHA3-FIX-999-MISSING")

    report = await evaluate_case_set(case_set, required_case_ids=required_case_ids)
    assert report.counts["harness_failures"] == 1
    assert "required case IDs were not executed: ALPHA3-FIX-999-MISSING" in report.harness_failures[0]


def _cli(tmp_path, payload, *extra_args):
    import json
    import subprocess
    import sys

    case_path = tmp_path / 'cases.json'
    report_path = tmp_path / 'report.json'
    case_path.write_text(json.dumps(payload), encoding='utf-8')
    completed = subprocess.run(
        [sys.executable, '-m', 'medical_ai.evals.alpha3_evidence_fidelity',
         '--case-set', str(case_path), '--json-out', str(report_path), *extra_args],
        capture_output=True, text=True,
    )
    report = json.loads(report_path.read_text()) if report_path.exists() else None
    return completed, report


def _payload():
    return load_case_set().model_dump(mode='json')


def test_cli_required_expectation_mismatch_exits_nonzero(tmp_path):
    payload = _payload()
    payload['cases'][0]['expected_terminal_state'] = 'PROVENANCE_INCOMPLETE'
    completed, report = _cli(tmp_path, payload)
    assert completed.returncode == 1
    assert report['counts']['required_failed'] == 1
    assert report['counts']['blocked_checks'] == 2


def test_cli_missing_extra_execution_requirement_exits_nonzero(tmp_path):
    completed, report = _cli(tmp_path, _payload(), '--required-case-id', 'MISSING')
    assert completed.returncode == 1
    assert report['harness_failures'] == ['required case IDs were not executed: MISSING']


@pytest.mark.parametrize('mutation', ['duplicate', 'missing', 'empty', 'zero_required', 'remove_policy'])
def test_cli_rejects_invalid_membership_and_policy(tmp_path, mutation):
    payload = _payload()
    if mutation == 'duplicate':
        payload['cases'][1] = payload['cases'][0]
    elif mutation == 'missing':
        payload['cases'].pop(0)
    elif mutation == 'empty':
        payload['cases'] = []
    elif mutation == 'zero_required':
        for case in payload['cases']:
            case['expectation_tier'] = 'BLOCKED'
        payload['required_pass_case_ids'] = []
    else:
        payload['execution_case_ids'] = payload['execution_case_ids'][1:]
        payload['required_pass_case_ids'] = payload['required_pass_case_ids'][1:]
        payload['cases'].pop(0)
    completed, report = _cli(tmp_path, payload, '--required-case-id', payload['execution_case_ids'][-1])
    assert completed.returncode == 1
    assert 'Invalid case set:' in completed.stderr
    assert report is None


@pytest.mark.parametrize('tier', ['BLOCKED', 'UNPROVEN', 'UNAVAILABLE'])
def test_cli_cannot_downgrade_required_case(tmp_path, tier):
    payload = _payload()
    payload['cases'][0]['expectation_tier'] = tier
    completed, _ = _cli(tmp_path, payload)
    assert completed.returncode == 1
    assert 'cannot be downgraded' in completed.stderr


@pytest.mark.asyncio
async def test_programmatic_override_cannot_replace_baseline_membership(monkeypatch):
    import medical_ai.evals.alpha3_evidence_fidelity as harness

    original = harness._run_case

    async def mislabeled_result(case):
        result = await original(case)
        if case.case_id == 'ALPHA3-FIX-001-SUPPORTED':
            result.case_id = 'SILENTLY-REPLACED'
        return result

    monkeypatch.setattr(harness, '_run_case', mislabeled_result)
    report = await evaluate_case_set(load_case_set(), required_case_ids={'ALPHA3-FIX-003-SOURCE-UNAVAILABLE'})
    assert any('ALPHA3-FIX-001-SUPPORTED' in failure for failure in report.harness_failures)


def test_cli_baseline_reports_bounded_success(tmp_path):
    completed, report = _cli(tmp_path, _payload())
    assert completed.returncode == 0
    assert report['counts']['required_passed'] == 4
    assert report['counts']['blocked_checks'] == 2
    assert 'not live retrieval' in report['metric_boundary']
    assert 'current_pipeline_live_retrieval_recall' in report['unproven_checks']

@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("case_id", "expected_status"),
    [
        ("ALPHA3-FIX-005-CONFLICT-BLOCKED", "EVIDENCE_CONFLICTING"),
        ("ALPHA3-FIX-006-POPULATION-MISMATCH-BLOCKED", "POPULATION_MISMATCH"),
    ],
)
async def test_explicit_synthetic_conflict_and_population_exclusion_withhold_all_claims(case_id, expected_status):
    """Independent regression: blocked benchmark cases cannot authorize medical claims."""
    from medical_ai.engine import EvidenceEngine
    from medical_ai.evals.alpha3_evidence_fidelity import FixtureConnector
    from medical_ai.schemas import AnswerStatus

    case = _case(load_case_set(default_case_set_path()), case_id)
    answer = await make_engine(FixtureConnector(case.scenario)).answer(
        case.question, jurisdiction=case.jurisdiction
    )
    assert answer.status == AnswerStatus(expected_status)
    assert answer.trace.final_status == answer.status
    assert expected_status in answer.trace.safety_flags
    assert answer.claims == []
    assert answer.sources == []
    assert answer.evidence_objects == []
    assert answer.citation_mappings == []
    assert answer.influence_decisions == []

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "non_conflicting_text",
    [
        "Treatment Y did not reduce symptom scores compared with placebo in adults.",
        "Treatment X did not improve sleep quality compared with placebo in adults.",
    ],
)
async def test_explicit_conflict_guard_does_not_equate_unrelated_interventions_or_outcomes(non_conflicting_text):
    from medical_ai.engine import EvidenceEngine
    from medical_ai.evals.alpha3_evidence_fidelity import FixtureConnector
    from medical_ai.schemas import AnswerStatus

    case = _case(load_case_set(), "ALPHA3-FIX-005-CONFLICT-BLOCKED")
    case.scenario.passages[1].text = non_conflicting_text
    answer = await make_engine(FixtureConnector(case.scenario)).answer(case.question)
    assert answer.status == AnswerStatus.ANSWER_SUPPORTED_WITH_QUALIFICATIONS
    assert answer.claims
    assert "EVIDENCE_CONFLICTING" not in answer.trace.safety_flags


@pytest.mark.asyncio
async def test_explicit_conflict_guard_requires_independent_source_records():
    from medical_ai.engine import EvidenceEngine
    from medical_ai.evals.alpha3_evidence_fidelity import FixtureConnector
    from medical_ai.schemas import AnswerStatus

    case = _case(load_case_set(), "ALPHA3-FIX-005-CONFLICT-BLOCKED")
    case.scenario.passages[1].source_id = case.scenario.sources[0].source_id
    answer = await make_engine(FixtureConnector(case.scenario)).answer(case.question)
    assert answer.status == AnswerStatus.ANSWER_SUPPORTED_WITH_QUALIFICATIONS
    assert "EVIDENCE_CONFLICTING" not in answer.trace.safety_flags


@pytest.mark.asyncio
async def test_population_guard_withholds_when_explicit_exclusion_starts_below_requested_age():
    from medical_ai.engine import EvidenceEngine
    from medical_ai.evals.alpha3_evidence_fidelity import FixtureConnector
    from medical_ai.schemas import AnswerStatus

    case = _case(load_case_set(), "ALPHA3-FIX-006-POPULATION-MISMATCH-BLOCKED")
    case.scenario.passages[0].text = (
        "Treatment X reduced symptom scores in adults aged 40 to 65; "
        "adults older than 70 were not evaluated."
    )
    answer = await make_engine(FixtureConnector(case.scenario)).answer(case.question)
    assert answer.status == AnswerStatus.POPULATION_MISMATCH
    assert answer.claims == []


@pytest.mark.asyncio
async def test_population_guard_does_not_convert_explicit_inclusion_into_exclusion():
    from medical_ai.engine import EvidenceEngine
    from medical_ai.evals.alpha3_evidence_fidelity import FixtureConnector
    from medical_ai.schemas import AnswerStatus

    case = _case(load_case_set(), "ALPHA3-FIX-006-POPULATION-MISMATCH-BLOCKED")
    case.scenario.passages[0].text = (
        "Treatment X reduced symptom scores in adults older than 80 years old."
    )
    answer = await make_engine(FixtureConnector(case.scenario)).answer(case.question)
    assert answer.status == AnswerStatus.ANSWER_SUPPORTED_WITH_QUALIFICATIONS
    assert answer.claims
    assert "POPULATION_MISMATCH" not in answer.trace.safety_flags
