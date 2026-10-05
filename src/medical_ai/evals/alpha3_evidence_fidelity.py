from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import sys
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from medical_ai.engine import EvidenceEngine
from medical_ai.evals.retrieval import first_authoritative_rank, recall_at_k
from medical_ai.retrieval_query import normalize_search_query
from medical_ai.schemas import AnswerStatus, Passage, SourceRecord


RUNNER_VERSION = "alpha3-evidence-fidelity-harness-v0.2"
FIXTURE_LABEL = "ENGINEERING FIXTURE — NOT CLINICALLY REVIEWED"
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CASE_SET_PATH = REPO_ROOT / "evals/evidence_fidelity/alpha3-engineering-v0.1.json"


BASELINE_EXECUTION_IDS = frozenset({
    'ALPHA3-FIX-001-SUPPORTED',
    'ALPHA3-FIX-002-PROVENANCE-INCOMPLETE',
    'ALPHA3-FIX-003-SOURCE-UNAVAILABLE',
    'ALPHA3-FIX-004-HIGH-CONSEQUENCE-FAIL-CLOSED',
    'ALPHA3-FIX-005-CONFLICT-BLOCKED',
    'ALPHA3-FIX-006-POPULATION-MISMATCH-BLOCKED',
})
BASELINE_REQUIRED_PASS_IDS = frozenset({
    'ALPHA3-FIX-001-SUPPORTED',
    'ALPHA3-FIX-002-PROVENANCE-INCOMPLETE',
    'ALPHA3-FIX-003-SOURCE-UNAVAILABLE',
    'ALPHA3-FIX-004-HIGH-CONSEQUENCE-FAIL-CLOSED',
})
METRIC_BOUNDARY = (
    "Synthetic fixture source order after pipeline admission, as recorded in trace.source_ids; "
    "not live retrieval or ranking performance. Normalization is observed in the fixture connector."
)


class ExpectationTier(StrEnum):
    REQUIRED = "REQUIRED"
    BLOCKED = "BLOCKED"
    UNPROVEN = "UNPROVEN"
    UNAVAILABLE = "UNAVAILABLE"


class CaseOutcome(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    UNPROVEN = "UNPROVEN"
    UNAVAILABLE = "UNAVAILABLE"


class RequiredAssertions(BaseModel):
    require_claim_ids: bool = False
    require_evidence_ids: bool = False
    require_citation_linkage: bool = False
    require_provenance_complete: bool | None = None
    require_influence_authorized: bool | None = None


class ConnectorScenario(BaseModel):
    connector_name: str
    source_class: str
    behavior: Literal["return_fixture", "raise_error"] = "return_fixture"
    error_type: str | None = None
    error_message: str | None = None
    sources: list[SourceRecord] = Field(default_factory=list)
    passages: list[Passage] = Field(default_factory=list)


class Alpha3Case(BaseModel):
    case_id: str
    case_set_version: str
    question: str
    intended_claim_type: str
    expected_authority_or_source_class: str
    jurisdiction: str = "AU"
    population_or_applicability_expectation: str | None = None
    freshness_requirement: str | None = None
    expected_terminal_state: str
    expected_failure_code: str | None = None
    review_classification: str
    expectation_tier: ExpectationTier = ExpectationTier.REQUIRED
    expectation_note: str | None = None
    expected_authoritative_source_ids: list[str] = Field(default_factory=list)
    authoritative_recall_k: int = Field(default=5, ge=1)
    expected_query_normalization: str | None = None
    required_assertions: RequiredAssertions = Field(default_factory=RequiredAssertions)
    scenario: ConnectorScenario


class Alpha3CaseSet(BaseModel):
    case_set_id: str
    case_set_version: str
    runner_version: str = RUNNER_VERSION
    execution_case_ids: list[str]
    required_pass_case_ids: list[str]
    cases: list[Alpha3Case]

    @model_validator(mode="after")
    def validate_case_set(self) -> "Alpha3CaseSet":
        if len(self.cases) > 6:
            raise ValueError("Alpha3 bounded slice allows at most 6 cases")
        case_ids = [case.case_id for case in self.cases]
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("Duplicate case_id values are not allowed")
        if set(self.execution_case_ids) != BASELINE_EXECUTION_IDS:
            raise ValueError("execution_case_ids must preserve the six-case engineering baseline")
        if set(self.required_pass_case_ids) != BASELINE_REQUIRED_PASS_IDS:
            raise ValueError("required_pass_case_ids must preserve the four required baseline cases")
        if len(self.execution_case_ids) != len(set(self.execution_case_ids)) or len(self.required_pass_case_ids) != len(set(self.required_pass_case_ids)):
            raise ValueError("Duplicate policy case IDs are not allowed")
        if self.runner_version != RUNNER_VERSION:
            raise ValueError("runner_version does not match the executing runner")
        required_tier_ids = {case.case_id for case in self.cases if case.expectation_tier == ExpectationTier.REQUIRED}
        if required_tier_ids != BASELINE_REQUIRED_PASS_IDS:
            raise ValueError("Required expectation tiers cannot be downgraded or removed")
        if any(case.expectation_tier != ExpectationTier.BLOCKED for case in self.cases if case.case_id not in BASELINE_REQUIRED_PASS_IDS):
            raise ValueError("Unresolved baseline cases must remain BLOCKED")
        missing_required = sorted(set(self.execution_case_ids) - set(case_ids))
        if missing_required:
            raise ValueError(f"execution_case_ids missing from cases: {', '.join(missing_required)}")
        wrong_version = [case.case_id for case in self.cases if case.case_set_version != self.case_set_version]
        if wrong_version:
            raise ValueError(
                "case_set_version mismatch for cases: " + ", ".join(wrong_version)
            )
        wrong_label = [case.case_id for case in self.cases if case.review_classification != FIXTURE_LABEL]
        if wrong_label:
            raise ValueError(
                "cases missing required review classification label: " + ", ".join(wrong_label)
            )
        return self


class Alpha3CaseResult(BaseModel):
    case_id: str
    expectation_tier: ExpectationTier
    outcome: CaseOutcome
    expected_authority_or_source_class: str
    observed_required_source_classes: list[str] = Field(default_factory=list)
    expected_terminal_state: str
    observed_terminal_state: str
    expected_failure_code: str | None = None
    observed_failure_code: str | None = None
    expected_authoritative_source_ids: list[str] = Field(default_factory=list)
    observed_source_ids: list[str] = Field(default_factory=list)
    authoritative_recall_k: int | None = None
    authoritative_recall_at_k: float | None = None
    first_authoritative_source_rank: int | None = None
    raw_query: str | None = None
    normalized_query: str | None = None
    claim_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    citation_linkage_complete: bool = False
    provenance_complete: bool | None = None
    influence_authorized: bool | None = None
    failures: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class Alpha3HarnessReport(BaseModel):
    report_version: str = "alpha3-evidence-fidelity-report-v0.2"
    generated_at: datetime
    repository_commit_sha: str
    case_set_id: str
    case_set_version: str
    runner_version: str
    runner_configuration: dict[str, str]
    case_results: list[Alpha3CaseResult]
    harness_failures: list[str]
    failures: list[str]
    blocked_checks: list[str]
    unproven_checks: list[str]
    unavailable_checks: list[str]
    counts: dict[str, int]
    metric_boundary: str = METRIC_BOUNDARY
    evaluation_scope: str = FIXTURE_LABEL


class FixtureConnector:
    version = "alpha3-fixture-connector-v0.1"
    evidence_approved = True
    phi_approved = False

    _EXC_TYPES = {
        "OSError": OSError,
        "TimeoutError": TimeoutError,
        "RuntimeError": RuntimeError,
        "ValueError": ValueError,
    }

    def __init__(self, scenario: ConnectorScenario):
        self.name = scenario.connector_name
        self.source_class = scenario.source_class
        self._scenario = scenario
        self.raw_queries: list[str] = []
        self.normalized_queries: list[str] = []

    async def search_and_fetch(self, query: str, limit: int = 5) -> tuple[list[SourceRecord], list[Passage]]:
        self.raw_queries.append(query)
        self.normalized_queries.append(normalize_search_query(query))
        if self._scenario.behavior == "raise_error":
            exc_type = self._EXC_TYPES.get(self._scenario.error_type or "", RuntimeError)
            raise exc_type(self._scenario.error_message or "synthetic source failure")
        return list(self._scenario.sources), list(self._scenario.passages)


def default_case_set_path() -> Path:
    return DEFAULT_CASE_SET_PATH


def load_case_set(path: Path | str | None = None) -> Alpha3CaseSet:
    case_path = Path(path) if path is not None else default_case_set_path()
    payload = json.loads(case_path.read_text(encoding="utf-8"))
    return Alpha3CaseSet.model_validate(payload)


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


def _derive_failure_code(status: AnswerStatus, *, safety_flags: list[str], influence_reasons: list[str]) -> str | None:
    if status in {AnswerStatus.ANSWER_SUPPORTED, AnswerStatus.ANSWER_SUPPORTED_WITH_QUALIFICATIONS}:
        return None
    if status == AnswerStatus.SOURCE_UNAVAILABLE:
        connector_errors = [flag for flag in safety_flags if flag.startswith("CONNECTOR_ERROR:")]
        if connector_errors:
            return connector_errors[0]
    if status == AnswerStatus.INFLUENCE_DENIED and influence_reasons:
        return influence_reasons[0]
    return status.value


def _citation_linkage_complete(claim_ids: set[str], evidence_ids: set[str], source_ids: set[str], passage_ids: set[str], mappings) -> bool:
    if not mappings:
        return False
    for mapping in mappings:
        if mapping.claim_id not in claim_ids:
            return False
        if mapping.evidence_id not in evidence_ids:
            return False
        if mapping.source_id not in source_ids:
            return False
        if not mapping.passage_ids:
            return False
        if any(passage_id not in passage_ids for passage_id in mapping.passage_ids):
            return False
    return True


async def _run_case(case: Alpha3Case) -> Alpha3CaseResult:
    connector = FixtureConnector(case.scenario)
    answer = await EvidenceEngine(connector).answer(
        case.question,
        jurisdiction=case.jurisdiction,
    )

    claim_ids = [claim.claim_id for claim in answer.claims]
    evidence_ids = [evidence.evidence_id for evidence in answer.evidence_objects]
    source_ids = [source.source_id for source in answer.sources]
    observed_required_source_classes = list(answer.trace.query_plan.required_source_classes)
    provenance_complete = (
        all(source.provenance_complete for source in answer.sources)
        if answer.sources
        else None
    )
    influence_reasons = [reason for decision in answer.influence_decisions for reason in decision.reasons]
    influence_authorized = (
        all(decision.allowed for decision in answer.influence_decisions)
        if answer.influence_decisions
        else None
    )
    observed_failure_code = _derive_failure_code(
        answer.status,
        safety_flags=answer.trace.safety_flags,
        influence_reasons=influence_reasons,
    )
    citation_complete = _citation_linkage_complete(
        set(claim_ids),
        set(evidence_ids),
        set(source_ids),
        {passage.passage_id for passage in answer.passages},
        answer.citation_mappings,
    )

    recall_value: float | None = None
    first_rank: int | None = None
    if case.expected_authoritative_source_ids:
        expected_ids = set(case.expected_authoritative_source_ids)
        ranked_ids = list(answer.trace.source_ids)
        recall_value = recall_at_k(expected_ids, ranked_ids, case.authoritative_recall_k)
        first_rank = first_authoritative_rank(expected_ids, ranked_ids)

    failures: list[str] = []
    notes: list[str] = []
    if case.expectation_tier == ExpectationTier.REQUIRED:
        if answer.status.value != case.expected_terminal_state:
            failures.append(
                f"expected terminal state {case.expected_terminal_state}, observed {answer.status.value}"
            )
        if case.expected_failure_code is not None and observed_failure_code != case.expected_failure_code:
            failures.append(
                f"expected failure code {case.expected_failure_code}, observed {observed_failure_code}"
            )
        if case.expected_query_normalization is not None:
            observed_query = connector.normalized_queries[0] if connector.normalized_queries else None
            if observed_query != case.expected_query_normalization:
                failures.append(
                    f"expected normalized query {case.expected_query_normalization!r}, observed {observed_query!r}"
                )
        if case.expected_authority_or_source_class not in observed_required_source_classes:
            failures.append(
                "expected authority/source class "
                f"{case.expected_authority_or_source_class!r} not selected by query plan "
                f"(observed {observed_required_source_classes})"
            )
        if case.required_assertions.require_claim_ids and not claim_ids:
            failures.append("required claim identifiers were missing")
        if case.required_assertions.require_evidence_ids and not evidence_ids:
            failures.append("required evidence identifiers were missing")
        if case.required_assertions.require_citation_linkage and not citation_complete:
            failures.append("required citation/passage linkage was incomplete")
        if case.required_assertions.require_provenance_complete is not None:
            if provenance_complete is not case.required_assertions.require_provenance_complete:
                failures.append(
                    "required provenance completeness was not satisfied "
                    f"(expected {case.required_assertions.require_provenance_complete}, observed {provenance_complete})"
                )
        if case.required_assertions.require_influence_authorized is not None:
            if influence_authorized is not case.required_assertions.require_influence_authorized:
                failures.append(
                    "required influence authorization result did not match "
                    f"(expected {case.required_assertions.require_influence_authorized}, observed {influence_authorized})"
                )
    else:
        if case.expectation_note:
            notes.append(case.expectation_note)
        if (
            answer.status.value == case.expected_terminal_state
            and (
                case.expected_failure_code is None
                or observed_failure_code == case.expected_failure_code
            )
        ):
            notes.append("blocked/unproven target appears met; promote this case after review")
        else:
            notes.append(
                f"observed {answer.status.value} while target state remains {case.expected_terminal_state}"
            )

    if case.expectation_tier == ExpectationTier.REQUIRED:
        outcome = CaseOutcome.PASS if not failures else CaseOutcome.FAIL
    elif case.expectation_tier == ExpectationTier.BLOCKED:
        outcome = CaseOutcome.BLOCKED
    elif case.expectation_tier == ExpectationTier.UNPROVEN:
        outcome = CaseOutcome.UNPROVEN
    else:
        outcome = CaseOutcome.UNAVAILABLE

    return Alpha3CaseResult(
        case_id=case.case_id,
        expectation_tier=case.expectation_tier,
        outcome=outcome,
        expected_authority_or_source_class=case.expected_authority_or_source_class,
        observed_required_source_classes=observed_required_source_classes,
        expected_terminal_state=case.expected_terminal_state,
        observed_terminal_state=answer.status.value,
        expected_failure_code=case.expected_failure_code,
        observed_failure_code=observed_failure_code,
        expected_authoritative_source_ids=list(case.expected_authoritative_source_ids),
        observed_source_ids=list(answer.trace.source_ids),
        authoritative_recall_k=case.authoritative_recall_k if case.expected_authoritative_source_ids else None,
        authoritative_recall_at_k=recall_value,
        first_authoritative_source_rank=first_rank,
        raw_query=connector.raw_queries[0] if connector.raw_queries else None,
        normalized_query=connector.normalized_queries[0] if connector.normalized_queries else None,
        claim_ids=claim_ids,
        evidence_ids=evidence_ids,
        citation_linkage_complete=citation_complete,
        provenance_complete=provenance_complete,
        influence_authorized=influence_authorized,
        failures=failures,
        notes=notes,
    )


async def evaluate_case_set(
    case_set: Alpha3CaseSet,
    *,
    required_case_ids: set[str] | None = None,
) -> Alpha3HarnessReport:
    # Revalidate mutable models so programmatic callers cannot silently downgrade policy.
    case_set = Alpha3CaseSet.model_validate(case_set.model_dump())
    case_results = [await _run_case(case) for case in case_set.cases]
    observed_case_ids = {result.case_id for result in case_results}
    required_ids = set(case_set.execution_case_ids) | set(required_case_ids or ())
    missing_required_ids = sorted(required_ids - observed_case_ids)
    harness_failures = []
    if missing_required_ids:
        harness_failures.append(
            "required case IDs were not executed: " + ", ".join(missing_required_ids)
        )

    required_results = [result for result in case_results if result.expectation_tier == ExpectationTier.REQUIRED]
    required_passed = [result for result in required_results if result.outcome == CaseOutcome.PASS]
    required_failed = [result for result in required_results if result.outcome == CaseOutcome.FAIL]
    blocked_checks = [result.case_id for result in case_results if result.outcome == CaseOutcome.BLOCKED]
    unproven_checks = [result.case_id for result in case_results if result.outcome == CaseOutcome.UNPROVEN]
    unproven_checks.extend(["current_pipeline_live_retrieval_recall", "live_source_ranking", "clinical_claim_to_passage_entailment"])
    unavailable_checks = [result.case_id for result in case_results if result.outcome == CaseOutcome.UNAVAILABLE]
    case_failures = [
        f"{result.case_id}: {failure}"
        for result in required_failed
        for failure in result.failures
    ]

    counts = {
        "total_cases": len(case_results),
        "required_cases": len(required_results),
        "required_passed": len(required_passed),
        "required_failed": len(required_failed),
        "blocked_checks": len(blocked_checks),
        "unproven_checks": len(unproven_checks),
        "unavailable_checks": len(unavailable_checks),
        "harness_failures": len(harness_failures),
    }

    return Alpha3HarnessReport(
        generated_at=datetime.now(timezone.utc),
        repository_commit_sha=_current_commit_sha(),
        case_set_id=case_set.case_set_id,
        case_set_version=case_set.case_set_version,
        runner_version=case_set.runner_version,
        runner_configuration={
            "module": "medical_ai.evals.alpha3_evidence_fidelity",
            "python": sys.version.split()[0],
        },
        case_results=case_results,
        harness_failures=harness_failures,
        failures=[*harness_failures, *case_failures],
        blocked_checks=blocked_checks,
        unproven_checks=unproven_checks,
        unavailable_checks=unavailable_checks,
        counts=counts,
    )


def _render_human_report(report: Alpha3HarnessReport) -> str:
    lines = [
        "Alpha3 Evidence Fidelity Harness",
        f"scope: {report.evaluation_scope}",
        f"metric_boundary: {report.metric_boundary}",
        f"commit_sha: {report.repository_commit_sha}",
        f"case_set: {report.case_set_id} @ {report.case_set_version}",
        f"runner: {report.runner_version}",
        (
            "required_cases: "
            f"{report.counts['required_passed']}/{report.counts['required_cases']} passed, "
            f"{report.counts['required_failed']} failed"
        ),
        (
            "non-required checks: "
            f"blocked={report.counts['blocked_checks']}, "
            f"unproven={report.counts['unproven_checks']}, "
            f"unavailable={report.counts['unavailable_checks']}"
        ),
    ]
    if report.harness_failures:
        lines.append("harness_failures:")
        lines.extend(f"  - {failure}" for failure in report.harness_failures)
    lines.append("case_results:")
    for result in report.case_results:
        lines.append(
            f"  - [{result.outcome}] {result.case_id} ({result.expectation_tier}) "
            f"expected={result.expected_terminal_state} observed={result.observed_terminal_state}"
        )
        if result.expected_failure_code is not None or result.observed_failure_code is not None:
            lines.append(
                f"      failure_code expected={result.expected_failure_code} observed={result.observed_failure_code}"
            )
        if result.first_authoritative_source_rank is not None:
            lines.append(
                "      authoritative_recall: "
                f"recall@{result.authoritative_recall_k}={result.authoritative_recall_at_k} "
                f"first_rank={result.first_authoritative_source_rank}"
            )
        if result.normalized_query is not None:
            lines.append(
                f"      query_normalization raw={result.raw_query!r} normalized={result.normalized_query!r}"
            )
        for failure in result.failures:
            lines.append(f"      FAIL: {failure}")
        for note in result.notes:
            lines.append(f"      NOTE: {note}")
    if report.failures:
        lines.append("failures:")
        lines.extend(f"  - {failure}" for failure in report.failures)
    return "\n".join(lines)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run deterministic Alpha3 evidence-fidelity engineering fixtures."
    )
    parser.add_argument(
        "--case-set",
        default=str(default_case_set_path()),
        help="Path to the Alpha3 case-set JSON file.",
    )
    parser.add_argument(
        "--json-out",
        default=None,
        help="Optional path to write the JSON report.",
    )
    parser.add_argument(
        "--required-case-id",
        action="append",
        default=[],
        help="Additional execution requirements; cannot replace baseline membership or required-pass policy.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        case_set = load_case_set(args.case_set)
    except (ValueError, OSError) as exc:
        print(f"Invalid case set: {exc}", file=sys.stderr)
        return 1
    required_case_ids = set(args.required_case_id) if args.required_case_id else None
    report = asyncio.run(
        evaluate_case_set(case_set, required_case_ids=required_case_ids)
    )
    report_json = json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True)
    print(_render_human_report(report))
    print("\nJSON report:")
    print(report_json)
    if args.json_out:
        Path(args.json_out).write_text(report_json + "\n", encoding="utf-8")
    if report.counts["required_failed"] > 0 or report.counts["harness_failures"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
