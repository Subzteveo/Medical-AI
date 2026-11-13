from __future__ import annotations

from pathlib import Path

import pytest

from medical_ai.evals.medai_eval_002 import (
    default_manifest_path,
    evaluate_manifest,
    load_manifest,
)


@pytest.mark.asyncio
async def test_medai_eval_002_full_manifest_passes_and_runs_perturbations():
    manifest = load_manifest(default_manifest_path())
    report = await evaluate_manifest(manifest, manifest_path=default_manifest_path())

    assert report.comparable is True
    assert report.executed_case_ids == report.expected_case_ids
    assert len(report.executed_case_ids) == 9
    assert report.runtime_case_count == 8
    assert report.contract_case_count == 1
    assert all(result.passed for result in report.case_results)
    assert report.omissions_detected == 0
    assert report.commissions_detected == 0
    assert report.severe_failures == 0
    assert report.aggregate_weighted_f1 == pytest.approx(1.0)
    assert report.perturbation.executed is True
    assert report.perturbation.resilience == pytest.approx(1.0)
    assert report.perturbation.passed is True
    assert report.failure_ledger == []
    assert report.passed is True


@pytest.mark.asyncio
async def test_medai_eval_002_partial_case_set_fails_closed_and_skips_perturbation(
    tmp_path: Path,
):
    manifest = load_manifest(default_manifest_path()).model_copy(deep=True)
    manifest.cases.pop()

    manifest_copy = tmp_path / "manifest.json"
    manifest_copy.write_text(
        default_manifest_path().read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    report = await evaluate_manifest(manifest, manifest_path=manifest_copy)

    assert report.comparable is False
    assert report.passed is False
    assert report.perturbation.executed is False
    assert any(
        "missing=MEDAI-EVAL-002-009-NO-AUTHORITATIVE-SOURCE" in failure
        for failure in report.failure_ledger
    )


@pytest.mark.asyncio
async def test_medai_eval_002_plain_supported_is_explicitly_contract_only():
    manifest = load_manifest(default_manifest_path())
    report = await evaluate_manifest(manifest, manifest_path=default_manifest_path())
    result = next(
        result
        for result in report.case_results
        if result.case_id == "MEDAI-EVAL-002-001-SUPPORTED-CONTRACT"
    )

    assert result.mode == "contract_supported"
    assert result.observed_status == "ANSWER_SUPPORTED"
    assert result.runtime_source_status == "ANSWER_SUPPORTED_WITH_QUALIFICATIONS"
    assert result.passed is True


def test_medai_eval_002_manifest_is_revision_bound_and_complete():
    path = default_manifest_path()
    manifest = load_manifest(path)

    assert manifest.suite_id == "MEDAI-EVAL-002"
    assert manifest.suite_version == "v0.1.0"
    assert manifest.runner_version == "medai-eval-002-harness-v0.1"
    assert manifest.alpha3_case_set_version == "v0.1.0"
    assert len(manifest.expected_case_ids) == 9
    assert len(manifest.cases) == 9
    assert path.name == "medai-eval-002-v0.1.json"
