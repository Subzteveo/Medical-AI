from __future__ import annotations

import pytest

from medical_ai.evals.clinical_harm import (
    HarmSeverity,
    decision_resilience,
    require_complete_case_set,
    score_clinical_actions,
)


def test_score_clinical_actions_detects_omission_and_commission_harm():
    score = score_clinical_actions(
        required_actions={
            "check-red-flags": HarmSeverity.SEVERE,
            "review-medications": HarmSeverity.MODERATE,
        },
        observed_actions={"review-medications", "unsafe-dose-change"},
        harmful_actions={"unsafe-dose-change": HarmSeverity.SEVERE},
    )

    assert score.weighted_recall == pytest.approx(24 / 96)
    assert score.weighted_precision == pytest.approx(24 / 96)
    assert score.weighted_f1 == pytest.approx(24 / 96)
    assert score.omission_weight == 72
    assert score.commission_weight == 72
    assert score.severe_harm is True
    assert {(event.action_id, event.harm_type) for event in score.events} == {
        ("check-red-flags", "omission"),
        ("unsafe-dose-change", "commission"),
    }


def test_score_clinical_actions_perfect_supported_action_set():
    score = score_clinical_actions(
        required_actions={
            "cite-guideline": HarmSeverity.MODERATE,
            "state-limit": HarmSeverity.MILD,
        },
        observed_actions={"cite-guideline", "state-limit", "extra-neutral-context"},
    )

    assert score.weighted_precision == 1.0
    assert score.weighted_recall == 1.0
    assert score.weighted_f1 == 1.0
    assert score.events == ()
    assert score.severe_harm is False


def test_score_rejects_action_that_is_both_required_and_harmful():
    with pytest.raises(ValueError, match="both required and harmful"):
        score_clinical_actions(
            required_actions={"same": HarmSeverity.SEVERE},
            observed_actions={"same"},
            harmful_actions={"same": HarmSeverity.SEVERE},
        )


def test_require_complete_case_set_fails_closed_on_missing_extra_or_duplicate():
    with pytest.raises(ValueError, match="missing=b"):
        require_complete_case_set(
            expected_case_ids={"a", "b"},
            observed_case_ids=["a"],
        )

    with pytest.raises(ValueError, match="extra=c"):
        require_complete_case_set(
            expected_case_ids={"a", "b"},
            observed_case_ids=["a", "b", "c"],
        )

    with pytest.raises(ValueError, match="duplicate=a"):
        require_complete_case_set(
            expected_case_ids={"a", "b"},
            observed_case_ids=["a", "a", "b"],
        )


def test_require_complete_case_set_accepts_exact_manifest_once_each():
    require_complete_case_set(
        expected_case_ids={"a", "b"},
        observed_case_ids=["b", "a"],
    )


def test_decision_resilience_is_severity_weighted_and_bounded():
    score = decision_resilience(
        variant_action_sets=[
            {"critical", "minor"},
            {"critical"},
            {"critical", "minor"},
            {"critical"},
        ],
        decision_weights={
            "critical": HarmSeverity.SEVERE,
            "minor": HarmSeverity.MILD,
        },
    )

    expected = (72 * 1.0 + 3 * 0.5) / 75
    assert score == pytest.approx(expected)
    assert 0.5 <= score <= 1.0


def test_decision_resilience_requires_multiple_variants():
    with pytest.raises(ValueError, match="at least two variants"):
        decision_resilience(
            variant_action_sets=[{"a"}],
            decision_weights={"a": HarmSeverity.MILD},
        )
