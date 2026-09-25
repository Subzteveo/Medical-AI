from medical_ai.planner import plan_query
from medical_ai.schemas import ConsequenceLevel


def test_dose_is_high_consequence():
    plan = plan_query("What dose of medicine X is used?")
    assert plan.consequence_level == ConsequenceLevel.HIGH
    assert plan.required_second_pass is True


def test_tga_question_requires_regulator():
    plan = plan_query("Is medicine X TGA approved?")
    assert "regulator" in plan.required_source_classes
    assert plan.jurisdiction_material is True


def test_trial_query_selects_registry():
    plan = plan_query("Are there recruiting clinical trials for treatment X?")
    assert "TRIAL_QUERY" in plan.intent
    assert plan.required_source_classes == ["clinical_trial_registry"]


def test_patient_specific_request_is_flagged():
    plan = plan_query("My patient is taking treatment X. What evidence exists?")
    assert plan.patient_specific is True
    assert "PATIENT_SPECIFIC" in plan.safety_flags
