from __future__ import annotations


def recall_at_k(expected_ids: set[str], ranked_ids: list[str], k: int) -> float:
    if not expected_ids:
        raise ValueError("expected_ids must not be empty")
    if k < 1:
        raise ValueError("k must be >= 1")
    found = expected_ids.intersection(ranked_ids[:k])
    return len(found) / len(expected_ids)


def evaluate_cases(cases: list[dict], k: int) -> dict[str, float]:
    values = [recall_at_k(set(case["expected_ids"]), list(case["ranked_ids"]), k) for case in cases]
    return {
        "cases": float(len(values)),
        "mean_recall_at_k": sum(values) / len(values) if values else 0.0,
        "min_recall_at_k": min(values) if values else 0.0,
    }
