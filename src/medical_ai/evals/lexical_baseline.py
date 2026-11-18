"""RET-EXP-001: offline pre-authority lexical measurement, never a medical answer."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from time import perf_counter
from typing import Literal, Sequence

from pydantic import BaseModel, ConfigDict, Field, model_validator

from medical_ai.extractor import extract_evidence
from medical_ai.provenance import validate_retrieved_records
from medical_ai.schemas import (
    ConsequenceLevel, EvidenceUnit, FreshnessAssessment, FreshnessState,
    Passage, QueryPlan, SourceRecord,
)
from medical_ai.source_policy import qualify_source

REPO_ROOT = Path(__file__).resolve().parents[3]
INPUT_DIR = "evals/retrieval/ret-exp-001-v0.1"
CASES_PATH = REPO_ROOT / INPUT_DIR / "cases.json"
FREEZE_PATH = REPO_ROOT / INPUT_DIR / "freeze.json"
BASE_REVISION = "f292523c3fd94983b2df48812739dbeba6ac0d06"
CONTRACT_PATH = "project_docs/plans/RET-EXP-001-v0.1.md"
BASELINE_FILES = frozenset({
    "src/medical_ai/__init__.py", "src/medical_ai/extractor.py",
    "src/medical_ai/provenance.py", "src/medical_ai/schemas.py",
    "src/medical_ai/source_policy.py", "src/medical_ai/policy_loader.py",
    "src/medical_ai/policies/__init__.py",
    "src/medical_ai/policies/source-policy-v0.1.yaml",
})
PINNED_FILES = BASELINE_FILES | {f"{INPUT_DIR}/cases.json", CONTRACT_PATH}
CATEGORIES = (
    "exact_match", "whole_abstract", "paraphrase", "abbreviation",
    "distractor_cutoff", "missing_candidate", "wrong_source_class",
    "registry_narrative", "supersession", "retraction", "jurisdiction",
    "conflict_pair", "population", "injection", "no_evidence",
)
FIXTURE_DATE = datetime(2026, 11, 13, tzinfo=timezone.utc)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class ClosedModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class CorpusPassage(ClosedModel):
    passage_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    source_type: Literal["indexed_biomedical_literature", "clinical_trial_registry"]
    jurisdiction: Literal["AU", "US", "INTERNATIONAL"]
    section: Literal["ABSTRACT", "REGISTRY_FACT", "DESCRIPTION", "TITLE"]
    text: str = Field(min_length=20)
    superseded: bool
    freshness: Literal["CURRENT", "SUPERSEDED", "RETRACTED", "UNKNOWN"]
    population: str
    provenance_complete: bool


class Case(ClosedModel):
    case_id: str
    split: Literal["development", "held_out_engineering"]
    category: str
    question: str = Field(min_length=1)
    source_class: Literal["biomedical_literature", "clinical_trial_registry"]
    jurisdiction: Literal["AU"]
    rationale: str = Field(min_length=1)
    corpus: list[CorpusPassage]
    candidate_ids: list[str]
    relevant_ids: list[str]
    excluded_ids: list[str]

    @model_validator(mode="after")
    def references_are_closed(self) -> Case:
        ids = [p.passage_id for p in self.corpus]
        source_ids = [p.source_id for p in self.corpus]
        for values in (ids, source_ids, self.candidate_ids, self.relevant_ids, self.excluded_ids):
            if len(values) != len(set(values)):
                raise ValueError("duplicate identity")
        if any(not p.startswith(self.case_id + "-") for p in ids + source_ids):
            raise ValueError("corpus identity must be case-scoped")
        if not set(self.candidate_ids + self.relevant_ids + self.excluded_ids) <= set(ids):
            raise ValueError("unknown corpus reference")
        if set(self.relevant_ids) & set(self.excluded_ids):
            raise ValueError("overlapping relevance/exclusion labels")
        if self.category not in CATEGORIES:
            raise ValueError("unknown category")
        return self


class CaseSet(ClosedModel):
    experiment_id: Literal["RET-EXP-001"]
    version: Literal["0.1"]
    label: Literal["SYNTHETIC ENGINEERING FIXTURES — NOT CLINICALLY REVIEWED"]
    k: Literal[5]
    cases: list[Case]

    @model_validator(mode="after")
    def complete_frozen_case_set(self) -> CaseSet:
        expected = {f"RET-{prefix}-{i:02}" for prefix in ("DEV", "HOLD") for i in range(1, 16)}
        if len(self.cases) != 30 or {c.case_id for c in self.cases} != expected:
            raise ValueError("must preserve all 30 distinct cases")
        for prefix, split in (("DEV", "development"), ("HOLD", "held_out_engineering")):
            subset = [c for c in self.cases if c.case_id.startswith(f"RET-{prefix}-")]
            if any(c.split != split for c in subset):
                raise ValueError("case split changed")
            if Counter(c.category for c in subset) != Counter(CATEGORIES):
                raise ValueError("case categories missing or duplicated")
        return self


class Freeze(ClosedModel):
    experiment_id: Literal["RET-EXP-001"]
    version: Literal["0.1"]
    baseline_revision: Literal["f292523c3fd94983b2df48812739dbeba6ac0d06"]
    sha256: dict[str, str]


def verify_freeze(root: Path, freeze_path: Path) -> Freeze:
    lock = Freeze.model_validate_json(freeze_path.read_bytes())
    if frozenset(lock.sha256) != PINNED_FILES:
        raise ValueError("freeze pin set differs from the contract")
    for name, expected in lock.sha256.items():
        target = root / name
        if (target.is_symlink() or not target.is_file()
                or not target.resolve().is_relative_to(root.resolve())
                or digest(target.read_bytes()) != expected):
            raise ValueError(f"frozen digest mismatch: {name}")
    return lock


def load_frozen_inputs() -> CaseSet:
    verify_freeze(REPO_ROOT, FREEZE_PATH)
    return CaseSet.model_validate_json(CASES_PATH.read_bytes())


def prepare_case(case: Case) -> tuple[list[SourceRecord], list[Passage], QueryPlan]:
    corpus = {p.passage_id: p for p in case.corpus}
    sources: list[SourceRecord] = []
    passages: list[Passage] = []
    for pid in case.candidate_ids:
        item = corpus[pid]
        sources.append(SourceRecord(
            source_id=item.source_id, authority="SYNTHETIC — NOT MEDICAL AUTHORITY",
            publisher="RET-EXP-001 invented fixture", source_type=item.source_type,
            title="Synthetic engineering passage", record_id=item.source_id,
            stable_url=f"https://example.invalid/{item.source_id}",
            jurisdiction=item.jurisdiction, superseded=item.superseded,
            population=item.population, provenance_complete=item.provenance_complete,
            retrieved_at=FIXTURE_DATE, licence_class="authored_synthetic_fixture",
            freshness=FreshnessAssessment(
                state=FreshnessState(item.freshness), basis="synthetic-label-not-assessment",
                assessed_at=FIXTURE_DATE,
            ),
        ))
        passages.append(Passage(
            passage_id=pid, source_id=item.source_id, section=item.section,
            text=item.text, locator=f"fixture:{pid}",
        ))
    validate_retrieved_records(sources, passages)
    plan = QueryPlan(
        intent=["OFFLINE_RETRIEVAL_EVALUATION"], user_mode="researcher",
        patient_specific=False, jurisdiction=case.jurisdiction,
        temporal_sensitivity="fixture", consequence_level=ConsequenceLevel.MODERATE,
        required_source_classes=[case.source_class], retrieval_questions=[case.question],
    )
    return sources, passages, plan


class Selection(ClosedModel):
    evidence_id: str
    source_id: str
    passage_id: str
    text_sha256: str


class CaseResult(ClosedModel):
    case_id: str
    split: str
    category: str
    candidate_passage_ids: list[str]
    source_qualification: dict[str, str]
    admitted_passage_ids: list[str]
    ranked_passage_ids: list[str]
    selected_passage_ids: list[str]
    selected: list[Selection]
    candidate_pool_recall: float | None
    post_qualification_recall: float | None
    selected_recall_at_5: float | None
    precision_at_5: float
    first_relevant_rank: int | None
    missing_from_candidate_pool: list[str]
    missing_after_qualification: list[str]
    missing_from_selection: list[str]
    excluded_selected_ids: list[str]
    nonempty_selection_without_relevant_evidence: bool
    selection_is_medical_authorization: Literal[False] = False


def _inspect_units(units: list[EvidenceUnit], passages: list[Passage]) -> list[Selection]:
    by_id = {p.passage_id: p for p in passages}
    inspected: list[Selection] = []
    seen: set[str] = set()
    for unit in units:
        if len(unit.passage_ids) != 1:
            raise ValueError("one whole passage required")
        pid = unit.passage_ids[0]
        if pid not in by_id or pid in seen:
            raise ValueError("unknown or duplicated selected passage")
        passage = by_id[pid]
        if unit.source_id != passage.source_id or unit.proposition != passage.text.strip():
            raise ValueError("selected content/source changed")
        expected_id = "ev_" + digest(f"{unit.source_id}:{unit.proposition}".encode())[:16]
        if unit.evidence_id != expected_id:
            raise ValueError("evidence identity changed")
        seen.add(pid)
        inspected.append(Selection(
            evidence_id=unit.evidence_id, source_id=unit.source_id,
            passage_id=pid, text_sha256=digest(unit.proposition.encode()),
        ))
    return inspected


def evaluate_case(case: Case) -> CaseResult:
    sources, passages, plan = prepare_case(case)
    decisions = {s.source_id: qualify_source(s, plan) for s in sources}
    admitted_sources = [s for s in sources if decisions[s.source_id].admitted]
    admitted_ids = {s.source_id for s in admitted_sources}
    admitted = [p for p in passages if p.source_id in admitted_ids]
    ranked = _inspect_units(extract_evidence(
        case.question, admitted_sources, admitted, max_units=max(1, len(admitted)),
    ), admitted)
    selected = _inspect_units(extract_evidence(
        case.question, admitted_sources, admitted, max_units=5,
    ), admitted)
    if selected != ranked[:5]:
        raise ValueError("truncated extraction differs from ranking prefix")
    ranked_ids = [s.passage_id for s in ranked]
    selected_ids = [s.passage_id for s in selected]
    admitted_pids = [p.passage_id for p in admitted]
    expected = set(case.relevant_ids)

    def recall(ids: list[str]) -> float | None:
        return len(expected.intersection(ids)) / len(expected) if expected else None

    return CaseResult(
        case_id=case.case_id, split=case.split, category=case.category,
        candidate_passage_ids=case.candidate_ids,
        source_qualification={sid: d.reason for sid, d in decisions.items()},
        admitted_passage_ids=admitted_pids, ranked_passage_ids=ranked_ids,
        selected_passage_ids=selected_ids, selected=selected,
        candidate_pool_recall=recall(case.candidate_ids),
        post_qualification_recall=recall(admitted_pids), selected_recall_at_5=recall(selected_ids),
        precision_at_5=len(expected.intersection(selected_ids)) / 5,
        first_relevant_rank=next((i for i, pid in enumerate(ranked_ids, 1) if pid in expected), None),
        missing_from_candidate_pool=sorted(expected - set(case.candidate_ids)),
        missing_after_qualification=sorted(expected - set(admitted_pids)),
        missing_from_selection=sorted(expected - set(selected_ids)),
        excluded_selected_ids=sorted(set(case.excluded_ids).intersection(selected_ids)),
        nonempty_selection_without_relevant_evidence=not expected and bool(selected_ids),
    )


class Summary(ClosedModel):
    cases: int
    nonempty_gold_cases: int
    mean_candidate_pool_recall: float | None
    mean_post_qualification_recall: float | None
    mean_selected_recall_at_5: float | None
    mean_precision_at_5: float
    cases_with_excluded_selection: int
    empty_gold_nonempty_selection_cases: int


def summarise(results: list[CaseResult]) -> Summary:
    def mean(values: list[float | None]) -> float | None:
        present = [v for v in values if v is not None]
        return sum(present) / len(present) if present else None

    return Summary(
        cases=len(results), nonempty_gold_cases=sum(r.selected_recall_at_5 is not None for r in results),
        mean_candidate_pool_recall=mean([r.candidate_pool_recall for r in results]),
        mean_post_qualification_recall=mean([r.post_qualification_recall for r in results]),
        mean_selected_recall_at_5=mean([r.selected_recall_at_5 for r in results]),
        mean_precision_at_5=sum(r.precision_at_5 for r in results) / len(results),
        cases_with_excluded_selection=sum(bool(r.excluded_selected_ids) for r in results),
        empty_gold_nonempty_selection_cases=sum(r.nonempty_selection_without_relevant_evidence for r in results),
    )


class Report(ClosedModel):
    experiment_id: Literal["RET-EXP-001"] = "RET-EXP-001"
    experiment_version: Literal["0.1"] = "0.1"
    execution_status: Literal["EXECUTED"] = "EXECUTED"
    quality_status: Literal["UNPROVEN_NOT_A_RELEASE_GATE"] = "UNPROVEN_NOT_A_RELEASE_GATE"
    candidate_status: Literal["NOT_IMPLEMENTED"] = "NOT_IMPLEMENTED"
    metric_boundary: str = "Synthetic pre-authority passage selection; not live retrieval, clinical authority recall, or rendered answers."
    baseline_revision: str = BASE_REVISION
    repository_head: str
    worktree_dirty: bool
    generated_at: str
    elapsed_ms: float
    dependency_versions: dict[str, str]
    execution_file_sha256: dict[str, str]
    results: list[CaseResult]
    summaries: dict[str, Summary]
    results_sha256: str


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args], capture_output=True,
        text=True, check=True,
    ).stdout.strip()


def run_experiment() -> Report:
    data = load_frozen_inputs()
    started = perf_counter()
    results = [evaluate_case(c) for c in data.cases]
    elapsed_ms = (perf_counter() - started) * 1000
    summaries = {"all": summarise(results)}
    for split in ("development", "held_out_engineering"):
        summaries[f"split:{split}"] = summarise([r for r in results if r.split == split])
    for category in CATEGORIES:
        summaries[f"category:{category}"] = summarise([r for r in results if r.category == category])
    stable = {"results": [r.model_dump() for r in results],
              "summaries": {key: val.model_dump() for key, val in summaries.items()}}
    paths = PINNED_FILES | {
        f"{INPUT_DIR}/freeze.json", "src/medical_ai/evals/__init__.py",
        "src/medical_ai/evals/lexical_baseline.py", "pyproject.toml",
    }
    return Report(
        repository_head=_git("rev-parse", "HEAD"), worktree_dirty=bool(_git("status", "--porcelain")),
        generated_at=datetime.now(timezone.utc).isoformat(), elapsed_ms=elapsed_ms,
        dependency_versions={"python": platform.python_version(), "pydantic": version("pydantic"),
                             "pydantic-core": version("pydantic-core"), "PyYAML": version("PyYAML")},
        execution_file_sha256={name: digest((REPO_ROOT / name).read_bytes()) for name in sorted(paths)},
        results=results, summaries=summaries,
        results_sha256=digest(json.dumps(stable, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()),
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args(argv)
    output: Path = args.json_out
    try:
        report = run_experiment()
        # Exclusive creation prevents clobbering a frozen input or a prior report.
        with output.open("x", encoding="utf-8") as stream:
            stream.write(report.model_dump_json(indent=2) + "\n")
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"RET-EXP-001 FAILED: {type(exc).__name__}", file=sys.stderr)
        return 1
    print(f"RET-EXP-001 EXECUTED: {len(report.results)} cases; quality remains UNPROVEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
