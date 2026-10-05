import pytest
from medical_ai.evals.retrieval import first_authoritative_rank, recall_at_k, evaluate_cases


def test_recall_at_k():
    assert recall_at_k({"a", "b"}, ["a", "c", "b"], 2) == 0.5
    assert recall_at_k({"a", "b"}, ["a", "c", "b"], 3) == 1.0


def test_recall_requires_gold_ids():
    with pytest.raises(ValueError):
        recall_at_k(set(), ["a"], 3)


def test_evaluate_cases_reports_mean_and_min():
    out = evaluate_cases([
        {"expected_ids": ["a"], "ranked_ids": ["a"]},
        {"expected_ids": ["b"], "ranked_ids": ["x", "b"]},
    ], k=1)
    assert out["mean_recall_at_k"] == 0.5
    assert out["min_recall_at_k"] == 0.0


def test_first_authoritative_rank():
    assert first_authoritative_rank({"pubmed:2"}, ["pubmed:1", "pubmed:2"]) == 2
    assert first_authoritative_rank({"pubmed:3"}, ["pubmed:1", "pubmed:2"]) is None
