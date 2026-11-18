"""Offline experiment integrity checks; not clinical validation."""
import copy
import json
import socket

import pytest

from medical_ai.evals import lexical_baseline as baseline
from medical_ai.extractor import extract_evidence


def dataset():
    return baseline.load_frozen_inputs()


def result(case_id):
    return baseline.evaluate_case(next(c for c in dataset().cases if c.case_id == case_id))


def test_all_cases_execute_reproducibly_without_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Offline benchmark attempted network access")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    first = baseline.run_experiment()
    second = baseline.run_experiment()
    assert len(first.results) == 30
    assert first.results == second.results
    assert first.summaries == second.summaries
    assert first.results_sha256 == second.results_sha256
    assert first.quality_status == "UNPROVEN_NOT_A_RELEASE_GATE"
    assert first.candidate_status == "NOT_IMPLEMENTED"
    assert first.execution_status == "EXECUTED"
    assert first.execution_file_sha256


def test_uses_actual_extractor_and_preserves_whole_abstract():
    case = next(c for c in dataset().cases if c.case_id == "RET-DEV-02")
    sources, passages, plan = baseline.prepare_case(case)
    actual = extract_evidence(case.question, sources, passages, max_units=5)
    out = baseline.evaluate_case(case)
    assert out.selected_passage_ids == [p for unit in actual for p in unit.passage_ids]
    assert actual[0].proposition == passages[0].text
    assert "LIMITATIONS:" in actual[0].proposition
    assert out.selected[0].text_sha256 == baseline.digest(passages[0].text.encode())
    assert plan.required_source_classes == ["biomedical_literature"]


@pytest.mark.parametrize("cid", ["RET-DEV-03", "RET-DEV-04", "RET-HOLD-03", "RET-HOLD-04"])
def test_semantic_matches_are_not_fabricated_into_lexical_success(cid):
    out = result(cid)
    assert out.candidate_pool_recall == 1.0
    assert out.selected_recall_at_5 == 0.0
    assert out.first_relevant_rank is None


def test_candidate_failure_is_separate_from_rank_failure():
    missing = result("RET-DEV-06")
    cutoff = result("RET-DEV-05")
    assert missing.candidate_pool_recall == 0.0
    assert missing.selected_recall_at_5 == 0.0
    assert cutoff.candidate_pool_recall == 1.0
    assert cutoff.post_qualification_recall == 1.0
    assert cutoff.selected_recall_at_5 == 0.0
    assert cutoff.first_relevant_rank == 7
    assert len(cutoff.selected_passage_ids) == 5


@pytest.mark.parametrize("cid", ["RET-DEV-07", "RET-DEV-08", "RET-DEV-09", "RET-DEV-14"])
def test_existing_source_and_extraction_exclusions(cid):
    out = result(cid)
    assert out.excluded_selected_ids == []
    assert out.selected_recall_at_5 == 1.0


@pytest.mark.parametrize("cid", ["RET-DEV-10", "RET-DEV-11", "RET-DEV-13"])
def test_pre_authority_limitations_are_reported_not_hidden(cid):
    out = result(cid)
    assert out.excluded_selected_ids
    assert out.selection_is_medical_authorization is False


def test_empty_gold_is_not_perfect_recall_or_correct_abstention():
    out = result("RET-DEV-15")
    assert out.candidate_pool_recall is None
    assert out.post_qualification_recall is None
    assert out.selected_recall_at_5 is None
    assert out.first_relevant_rank is None
    assert out.nonempty_selection_without_relevant_evidence is True
    assert out.precision_at_5 == 0.0


def test_conflict_pair_requires_both_passages():
    out = result("RET-DEV-12")
    assert len(out.selected_passage_ids) == 2
    assert out.selected_recall_at_5 == 1.0
    assert out.precision_at_5 == 0.4


@pytest.mark.parametrize("mutation", ["missing_case", "duplicate_case", "unknown_gold", "duplicate_candidate", "overlapping_labels", "unknown_candidate", "duplicate_source", "wrong_split", "extra_field", "wrong_k", "live_source"])
def test_invalid_datasets_fail_closed(mutation):
    raw = json.loads(baseline.CASES_PATH.read_text())
    case = raw["cases"][0]
    if mutation == "missing_case":
        raw["cases"].pop()
    elif mutation == "duplicate_case":
        raw["cases"][1] = copy.deepcopy(case)
    elif mutation == "unknown_gold":
        case["relevant_ids"].append("missing")
    elif mutation == "duplicate_candidate":
        case["candidate_ids"].append(case["candidate_ids"][0])
    elif mutation == "overlapping_labels":
        case["excluded_ids"] = case["relevant_ids"]
    elif mutation == "unknown_candidate":
        case["candidate_ids"] = ["missing"]
    elif mutation == "duplicate_source":
        case["corpus"][1]["source_id"] = case["corpus"][0]["source_id"]
    elif mutation == "wrong_split":
        case["split"] = "held_out_engineering"
    elif mutation == "extra_field":
        case["ranked_ids"] = case["candidate_ids"]
    elif mutation == "wrong_k":
        raw["k"] = 1
    elif mutation == "live_source":
        case["corpus"][0]["stable_url"] = "https://pubmed.ncbi.nlm.nih.gov/123/"
    with pytest.raises(ValueError):
        baseline.CaseSet.model_validate(raw)


def frozen_copy(tmp_path):
    lock = baseline.Freeze.model_validate_json(baseline.FREEZE_PATH.read_bytes())
    for name in lock.sha256:
        dest = tmp_path / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((baseline.REPO_ROOT / name).read_bytes())
    freeze = tmp_path / baseline.FREEZE_PATH.relative_to(baseline.REPO_ROOT)
    freeze.write_bytes(baseline.FREEZE_PATH.read_bytes())
    return freeze


@pytest.mark.parametrize("target", ["evals/retrieval/ret-exp-001-v0.1/cases.json", "src/medical_ai/extractor.py", "project_docs/plans/RET-EXP-001-v0.1.md"])
def test_freeze_rejects_changed_bytes(tmp_path, target):
    freeze = frozen_copy(tmp_path)
    with (tmp_path / target).open("ab") as output:
        output.write(b"\n")
    with pytest.raises(ValueError, match="digest"):
        baseline.verify_freeze(tmp_path, freeze)


def test_freeze_rejects_removed_pin_and_path_traversal(tmp_path):
    freeze = frozen_copy(tmp_path)
    raw = json.loads(freeze.read_text())
    raw["sha256"].pop("src/medical_ai/extractor.py")
    raw["sha256"]["../escape"] = "0" * 64
    freeze.write_text(json.dumps(raw))
    with pytest.raises(ValueError, match="pin set"):
        baseline.verify_freeze(tmp_path, freeze)


@pytest.mark.parametrize("mutation", ["text", "id", "duplicate", "source"])
def test_ranking_fabrication_is_rejected(monkeypatch, mutation):
    original = baseline.extract_evidence

    def changed(*args, **kwargs):
        units = original(*args, **kwargs)
        if mutation == "text":
            units[0].proposition = "Fabricated content absent from the frozen source."
        elif mutation == "id":
            units[0].passage_ids = ["invented-passage"]
        elif mutation == "duplicate":
            units.append(units[0])
        else:
            units[0].source_id = "invented-source"
        return units

    monkeypatch.setattr(baseline, "extract_evidence", changed)
    with pytest.raises(ValueError):
        result("RET-DEV-01")


def test_cli_writes_report_and_refuses_overwrite(tmp_path, capsys):
    output = tmp_path / "result.json"
    assert baseline.main(["--json-out", str(output)]) == 0
    first = output.read_bytes()
    report = json.loads(first)
    assert report["results_sha256"]
    assert baseline.main(["--json-out", str(output)]) != 0
    assert output.read_bytes() == first
    assert "FAILED" in capsys.readouterr().err


def test_cli_does_not_emit_partial_report_on_invalid_inputs(tmp_path, monkeypatch):
    def broken():
        raise ValueError("fixture digest mismatch")

    monkeypatch.setattr(baseline, "load_frozen_inputs", broken)
    output = tmp_path / "result.json"
    assert baseline.main(["--json-out", str(output)]) != 0
    assert not output.exists()
