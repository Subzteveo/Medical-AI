from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from medical_ai.authority_resolver import AuthorityResolver
from medical_ai.engine import EvidenceEngine
from medical_ai.evals.alpha3_evidence_fidelity import (
    Alpha3Case,
    FixtureConnector,
    load_case_set,
)
from medical_ai.evals.answer_harm_adapter import answer_action_ids, score_evidence_answer
from medical_ai.evals.clinical_harm import (
    HarmSeverity,
    decision_resilience,
    require_complete_case_set,
)
from medical_ai.schemas import AnswerStatus, EvidenceAnswer


RUNNER_VERSION = "medai-eval-002-harness-v0.1"
EVALUATION_SCOPE = "SYNTHETIC ENGINEERING FIXTURES ONLY - NOT CLINICALLY REVIEWED"
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MANIFEST_PATH = REPO_ROOT / "evals/clinical_harm/medai-eval-002-v0.1.json"


class EvalCaseSpec(BaseModel):
    case_id: str
    mode: Literal["runtime", "contract_supported"] = "runtime"
    base_case_id: str
    question: str | None = None
    scenario_transform: Literal["none", "empty_results"] = "none"
    expected_status: AnswerStatus
    runtime_source_expected_status: AnswerStatus | None = None
    severity: HarmSeverity
    expected_abstention: bool
    expected_source_class: str
    expected_provenance: Literal["complete", "withheld"]
    expected_citations: Literal["verified", "none"]
    expected_authority: Literal["authorized", "none"]
    required_actions: dict[str, HarmSeverity]
    harmful_actions: dict[str, HarmSeverity] = Field(default_factory=dict)


class PerturbationVariant(BaseModel):
    variant_id: str
    question: str


class PerturbationSpec(BaseModel):
    base_case_id: str
    expected_status: AnswerStatus
    tracked_decisions: dict[str, HarmSeverity]
    minimum_resilience: float = Field(ge=0.5, le=1.0)
    variants: list[PerturbationVariant]


class EvalManifest(BaseModel):
    suite_id: str
    suite_version: str
    runner_version: str
    alpha3_case_set_version: str
    expected_case_ids: list[str]
    cases: list[EvalCaseSpec]
    perturbation: PerturbationSpec

    @model_validator(mode="after")
    def validate_manifest(self) -> "EvalManifest":
        case_ids = [case.case_id for case in self.cases]
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("duplicate MEDAI-EVAL-002 case ids")
        if len(self.expected_case_ids) != len(set(self.expected_case_ids)):
            raise ValueError("duplicate expected case ids")
        if set(case_ids) != set(self.expected_case_ids):
            raise ValueError("manifest cases must exactly match expected_case_ids")
        if self.runner_version != RUNNER_VERSION:
            raise ValueError("runner_version does not match executing runner")
        if len(self.perturbation.variants) < 2:
            raise ValueError("perturbation layer requires at least two variants")
        return self


class EvalCaseResult(BaseModel):
    case_id: str
    mode: Literal["runtime", "contract_supported"]
    severity: HarmSeverity
    expected_status: AnswerStatus
    observed_status: AnswerStatus
    runtime_source_status: AnswerStatus | None = None
    observed_actions: list[str]
    weighted_precision: float
    weighted_recall: float
    weighted_f1: float
    omission_weight: int
    commission_weight: int
    severe_harm: bool
    failures: list[str]
    passed: bool


class PerturbationVariantResult(BaseModel):
    variant_id: str
    observed_status: AnswerStatus
    observed_actions: list[str]


class PerturbationResult(BaseModel):
    executed: bool
    resilience: float | None = None
    minimum_resilience: float
    variants: list[PerturbationVariantResult] = Field(default_factory=list)
    failures: list[str] = Field(default_factory=list)
    passed: bool


class MedaiEval002Report(BaseModel):
    report_version: str = "medai-eval-002-report-v0.1"
    generated_at: datetime
    repository_commit_sha: str
    suite_id: str
    suite_version: str
    runner_version: str
    alpha3_case_set_version: str
    manifest_sha256: str
    evaluation_scope: str = EVALUATION_SCOPE
    expected_case_ids: list[str]
    executed_case_ids: list[str]
    comparable: bool
    runtime_case_count: int
    contract_case_count: int
    case_results: list[EvalCaseResult]
    perturbation: PerturbationResult
    omissions_detected: int
    commissions_detected: int
    severe_failures: int
    aggregate_weighted_f1: float
    failure_ledger: list[str]
    passed: bool


def default_manifest_path() -> Path:
    return DEFAULT_MANIFEST_PATH


def load_manifest(path: Path | str | None = None) -> EvalManifest:
    manifest_path = Path(path) if path is not None else default_manifest_path()
    return EvalManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))


def _manifest_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _current_commit_sha() -> str:
    completed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return "UNKNOWN"
    return completed.stdout.strip() or "UNKNOWN"


def _alpha3_cases() -> dict[str, Alpha3Case]:
    case_set = load_case_set()
    return {case.case_id: case for case in case_set.cases}


async def _answer_for_case(
    spec: EvalCaseSpec,
    alpha3_cases: dict[str, Alpha3Case],
) -> tuple[EvidenceAnswer, AnswerStatus]:
    base = alpha3_cases[spec.base_case_id]
    scenario = base.scenario.model_copy(deep=True)
    if spec.scenario_transform == "empty_results":
        scenario.sources = []
        scenario.passages = []
        scenario.behavior = "return_fixture"
        scenario.error_type = None
        scenario.error_message = None

    question = spec.question or base.question
    engine = EvidenceEngine(
        FixtureConnector(scenario),
        authority_resolver=AuthorityResolver(),
    )
    runtime_answer = await engine.answer(question, jurisdiction=base.jurisdiction)
    runtime_status = runtime_answer.status

    if spec.mode == "runtime":
        return runtime_answer, runtime_status

    contract_trace = runtime_answer.trace.model_copy(
        update={"final_status": AnswerStatus.ANSWER_SUPPORTED},
        deep=True,
    )
    contract_answer = runtime_answer.model_copy(
        update={
            "status": AnswerStatus.ANSWER_SUPPORTED,
            "trace": contract_trace,
        },
        deep=True,
    )
    validated = EvidenceAnswer.model_validate(contract_answer.model_dump(mode="python"))
    return validated, runtime_status


def _metadata_failures(
    spec: EvalCaseSpec,
    answer: EvidenceAnswer,
    actions: set[str],
    runtime_source_status: AnswerStatus,
) -> list[str]:
    failures: list[str] = []
    if answer.status != spec.expected_status:
        failures.append(
            f"status mismatch: expected {spec.expected_status.value}, observed {answer.status.value}"
        )
    if spec.runtime_source_expected_status is not None:
        if runtime_source_status != spec.runtime_source_expected_status:
            failures.append(
                "runtime source status mismatch: "
                f"expected {spec.runtime_source_expected_status.value}, "
                f"observed {runtime_source_status.value}"
            )

    expected_control = "control/abstained" if spec.expected_abstention else "control/supported"
    if expected_control not in actions:
        failures.append(f"missing expected control action: {expected_control}")

    source_action = f"source-class/{spec.expected_source_class}"
    if source_action not in actions:
        failures.append(f"missing expected source-class action: {source_action}")

    provenance_action = "evidence/provenance-complete"
    if spec.expected_provenance == "complete":
        if provenance_action not in actions:
            failures.append("expected complete visible provenance")
    elif provenance_action in actions:
        failures.append("visible provenance unexpectedly survived a withheld-output case")

    citation_action = "output/citations-verified"
    if spec.expected_citations == "verified":
        if citation_action not in actions:
            failures.append("expected verified visible citations")
    elif "output/citations" in actions or citation_action in actions:
        failures.append("citations unexpectedly visible in a no-citation case")

    authority_action = "authority/claims-authorized"
    if spec.expected_authority == "authorized":
        if authority_action not in actions:
            failures.append("expected authorized visible claims")
    elif authority_action in actions:
        failures.append("claim authority unexpectedly visible in a no-authority case")

    return failures


async def _run_case(
    spec: EvalCaseSpec,
    alpha3_cases: dict[str, Alpha3Case],
) -> EvalCaseResult:
    answer, runtime_source_status = await _answer_for_case(spec, alpha3_cases)
    actions = answer_action_ids(answer)
    score = score_evidence_answer(
        answer,
        required_actions=spec.required_actions,
        harmful_actions=spec.harmful_actions,
    )
    failures = _metadata_failures(spec, answer, actions, runtime_source_status)
    failures.extend(
        f"{event.harm_type}:{event.action_id}:{event.severity.value}"
        for event in score.events
    )

    return EvalCaseResult(
        case_id=spec.case_id,
        mode=spec.mode,
        severity=spec.severity,
        expected_status=spec.expected_status,
        observed_status=answer.status,
        runtime_source_status=(
            runtime_source_status if spec.mode == "contract_supported" else None
        ),
        observed_actions=sorted(actions),
        weighted_precision=score.weighted_precision,
        weighted_recall=score.weighted_recall,
        weighted_f1=score.weighted_f1,
        omission_weight=score.omission_weight,
        commission_weight=score.commission_weight,
        severe_harm=score.severe_harm,
        failures=failures,
        passed=not failures,
    )


async def _run_perturbation(
    spec: PerturbationSpec,
    alpha3_cases: dict[str, Alpha3Case],
) -> PerturbationResult:
    base = alpha3_cases[spec.base_case_id]
    action_sets: list[set[str]] = []
    variant_results: list[PerturbationVariantResult] = []
    failures: list[str] = []

    for variant in spec.variants:
        engine = EvidenceEngine(
            FixtureConnector(base.scenario.model_copy(deep=True)),
            authority_resolver=AuthorityResolver(),
        )
        answer = await engine.answer(variant.question, jurisdiction=base.jurisdiction)
        actions = answer_action_ids(answer)
        action_sets.append(actions)
        variant_results.append(
            PerturbationVariantResult(
                variant_id=variant.variant_id,
                observed_status=answer.status,
                observed_actions=sorted(actions),
            )
        )
        if answer.status != spec.expected_status:
            failures.append(
                f"{variant.variant_id}: expected {spec.expected_status.value}, "
                f"observed {answer.status.value}"
            )

    resilience = decision_resilience(
        variant_action_sets=action_sets,
        decision_weights=spec.tracked_decisions,
    )
    if resilience < spec.minimum_resilience:
        failures.append(
            f"decision resilience {resilience:.6f} below minimum "
            f"{spec.minimum_resilience:.6f}"
        )

    return PerturbationResult(
        executed=True,
        resilience=resilience,
        minimum_resilience=spec.minimum_resilience,
        variants=variant_results,
        failures=failures,
        passed=not failures,
    )


async def evaluate_manifest(
    manifest: EvalManifest,
    *,
    manifest_path: Path | str | None = None,
) -> MedaiEval002Report:
    alpha3_case_set = load_case_set()
    if alpha3_case_set.case_set_version != manifest.alpha3_case_set_version:
        raise ValueError(
            "manifest alpha3_case_set_version does not match the loaded Alpha3 case set"
        )

    alpha3_cases = {case.case_id: case for case in alpha3_case_set.cases}
    case_results = [await _run_case(case, alpha3_cases) for case in manifest.cases]
    executed_ids = [result.case_id for result in case_results]
    failure_ledger: list[str] = []
    comparable = True
    try:
        require_complete_case_set(
            expected_case_ids=manifest.expected_case_ids,
            observed_case_ids=executed_ids,
        )
    except ValueError as exc:
        comparable = False
        failure_ledger.append(str(exc))

    for result in case_results:
        failure_ledger.extend(f"{result.case_id}: {failure}" for failure in result.failures)

    base_cases_passed = comparable and all(result.passed for result in case_results)
    if base_cases_passed:
        perturbation = await _run_perturbation(manifest.perturbation, alpha3_cases)
        failure_ledger.extend(
            f"PERTURBATION: {failure}" for failure in perturbation.failures
        )
    else:
        perturbation = PerturbationResult(
            executed=False,
            minimum_resilience=manifest.perturbation.minimum_resilience,
            failures=["base synthetic case gate did not pass; perturbation not executed"],
            passed=False,
        )

    omissions = sum(
        1
        for result in case_results
        for failure in result.failures
        if failure.startswith("omission:")
    )
    commissions = sum(
        1
        for result in case_results
        for failure in result.failures
        if failure.startswith("commission:")
    )
    severe_failures = sum(1 for result in case_results if result.severe_harm)
    aggregate_f1 = (
        sum(result.weighted_f1 for result in case_results) / len(case_results)
        if case_results
        else 0.0
    )

    path = Path(manifest_path) if manifest_path is not None else default_manifest_path()
    passed = base_cases_passed and perturbation.passed

    return MedaiEval002Report(
        generated_at=datetime.now(timezone.utc),
        repository_commit_sha=_current_commit_sha(),
        suite_id=manifest.suite_id,
        suite_version=manifest.suite_version,
        runner_version=manifest.runner_version,
        alpha3_case_set_version=manifest.alpha3_case_set_version,
        manifest_sha256=_manifest_sha256(path),
        expected_case_ids=list(manifest.expected_case_ids),
        executed_case_ids=executed_ids,
        comparable=comparable,
        runtime_case_count=sum(1 for case in manifest.cases if case.mode == "runtime"),
        contract_case_count=sum(
            1 for case in manifest.cases if case.mode == "contract_supported"
        ),
        case_results=case_results,
        perturbation=perturbation,
        omissions_detected=omissions,
        commissions_detected=commissions,
        severe_failures=severe_failures,
        aggregate_weighted_f1=aggregate_f1,
        failure_ledger=failure_ledger,
        passed=passed,
    )


def _render_human_report(report: MedaiEval002Report) -> str:
    lines = [
        "MEDAI-EVAL-002 Synthetic Clinical-Harm Evaluation",
        f"scope: {report.evaluation_scope}",
        f"commit_sha: {report.repository_commit_sha}",
        (
            f"suite: {report.suite_id} @ {report.suite_version}; "
            f"manifest_sha256={report.manifest_sha256}"
        ),
        (
            f"cases: {len(report.executed_case_ids)}/{len(report.expected_case_ids)} "
            f"executed; comparable={report.comparable}"
        ),
        (
            f"harm: omissions={report.omissions_detected}, "
            f"commissions={report.commissions_detected}, "
            f"severe_failures={report.severe_failures}, "
            f"aggregate_weighted_f1={report.aggregate_weighted_f1:.6f}"
        ),
    ]
    for result in report.case_results:
        lines.append(
            f"  - [{'PASS' if result.passed else 'FAIL'}] {result.case_id}: "
            f"expected={result.expected_status.value} observed={result.observed_status.value}"
        )
        if result.runtime_source_status is not None:
            lines.append(
                f"      contract-derived from runtime={result.runtime_source_status.value}"
            )
        for failure in result.failures:
            lines.append(f"      FAIL: {failure}")
    lines.append(
        "perturbation: "
        + (
            f"resilience={report.perturbation.resilience:.6f}, "
            f"minimum={report.perturbation.minimum_resilience:.6f}, "
            f"passed={report.perturbation.passed}"
            if report.perturbation.executed and report.perturbation.resilience is not None
            else "not executed"
        )
    )
    for failure in report.failure_ledger:
        lines.append(f"FAILURE_LEDGER: {failure}")
    lines.append(f"result: {'PASS' if report.passed else 'HOLD'}")
    return "\n".join(lines)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the bounded MEDAI-EVAL-002 synthetic clinical-harm suite."
    )
    parser.add_argument(
        "--manifest",
        default=str(default_manifest_path()),
        help="Path to the MEDAI-EVAL-002 manifest JSON.",
    )
    parser.add_argument(
        "--json-out",
        default=None,
        help="Optional path to write the revision-bound JSON report.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    manifest_path = Path(args.manifest)
    try:
        manifest = load_manifest(manifest_path)
        report = asyncio.run(evaluate_manifest(manifest, manifest_path=manifest_path))
    except (OSError, ValueError) as exc:
        print(f"MEDAI-EVAL-002 configuration failure: {exc}", file=sys.stderr)
        return 1

    report_json = json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True)
    print(_render_human_report(report))
    print("\nJSON report:")
    print(report_json)
    if args.json_out:
        Path(args.json_out).write_text(report_json + "\n", encoding="utf-8")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
