from __future__ import annotations

import re

from .policy_loader import consequence_policy
from .schemas import ConsequenceLevel, QueryPlan


# Keys deliberately mirror the canonical consequence policy categories.
HIGH_CONSEQUENCE_PATTERNS = {
    "medication_dose": r"\b(dose|doses|dosage|dosing|mg|mcg|µg|micrograms?|milligrams?)\b",
    "contraindication": r"\bcontraindicat(?:e|ed|es|ion|ions)?\b",
    "drug_interaction": r"\binteractions?\b|\binteract(?:s|ed|ing)?\s+with\b",
    "pregnancy": r"\b(pregnan(?:cy|t)|breastfeed(?:ing)?|lactat(?:e|ed|ion|ing)?)\b",
    "paediatrics": r"\b(child|children|paediatric|pediatric|infant|neonate|neonatal|adolescent)\b",
    "renal_or_hepatic_adjustment": r"(?=.*\b(renal|kidney|hepatic|liver)\b)(?=.*\b(adjust|adjusted|adjustment|dose|dosing)\b)",
    "anticoagulation": r"\b(anticoag(?:ulation|ulant|ulated|ulate)?|warfarin|apixaban|rivaroxaban|dabigatran|heparin)\b",
    "allergy_related_prescribing": r"\b(allerg(?:y|ic)|hypersensitiv(?:ity|e)|anaphylaxis)\b",
    "emergency_treatment": r"\b(emergency|resuscitat(?:e|ed|ion|ive)?|cardiac arrest|status epilepticus|anaphylaxis)\b",
    "toxicology": r"\b(overdose|toxicology|poison(?:ing|ed)?|toxicity|toxic dose)\b",
    "diagnostic_exclusion": r"\b(exclude|excluded|excluding|rule out|ruling out)\b|\bnegative\b.{0,80}\b(pulmonary embolism|dvt|deep vein thrombosis|myocardial infarction|meningitis|sepsis)\b",
    "treatment_start_or_stop": r"\b(start|started|starting|initiate|initiated|initiation|stop|stopped|stopping|discontinue|discontinued|discontinuation)\b",
    "cancer_therapy": r"\b(cancer|oncolog(?:y|ic)|melanoma|leukaemia|leukemia|lymphoma|carcinoma|sarcoma|metastatic|chemotherapy|immunotherapy|radiotherapy)\b",
}

_POLICY_CATEGORIES = set(consequence_policy().get("high_consequence", []))
if _POLICY_CATEGORIES != set(HIGH_CONSEQUENCE_PATTERNS):
    missing = sorted(_POLICY_CATEGORIES - set(HIGH_CONSEQUENCE_PATTERNS))
    extra = sorted(set(HIGH_CONSEQUENCE_PATTERNS) - _POLICY_CATEGORIES)
    raise RuntimeError(f"Consequence policy/runtime mismatch; missing={missing}, extra={extra}")

# Patient/identifier detection remains conservative and deterministic. It is a
# safety gate, not a de-identification guarantee.
IDENTIFIER_PATTERNS = [
    r"\bDOB\b\s*[:=]?\s*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
    r"\bMedicare\b\s*(?:no\.?|number)?\s*[:=]?\s*[0-9 ]{9,15}\b",
    r"\b(?:Mr|Mrs|Ms|Miss|Dr)\.?\s+[A-Z][a-z]+\b",
    r"\bbed\s*\d+\b",
]
PATIENT_CONTEXT_PATTERNS = [
    r"\bmy\s+(?:patient|child|mum|mom|mother|dad|father|husband|wife|partner|medication|medicine|symptoms?|diagnosis|results?|blood|scan|test)\b",
    r"\b(?:my patient|the patient|this patient)\b",
    r"\bPt\b\s+(?:is\s+)?(?:a\s+)?\d{1,3}(?:yo|y/o|\s*year[- ]old)?\b",
    r"\b\d{1,3}\s*[MF]\b",
    r"\b\d{1,3}\s*(?:yo|y/o|year[- ]old)\b",
    r"\b(?:i am|i'm|i was|i take|i'm taking|i am taking)\b.{0,100}\b(?:mg|mcg|µg|medicine|medication|drug|tablet|capsule|diagnos|symptom|egfr|t2dm|diabetes|cancer|pregnan)\b",
    r"\b(?:he|she)\s+(?:is\s+)?taking\b",
    r"\begfr\s*\d+\b",
    r"\bT2DM\b",
]
PATIENT_CUES = re.compile("|".join(f"(?:{p})" for p in IDENTIFIER_PATTERNS + PATIENT_CONTEXT_PATTERNS), re.I)

# Regulatory routing requires actual regulatory intent, not isolated words such
# as "registered nurse" or "approved outcome measure".
REGULATORY_CUES = re.compile(
    r"\b(tga|fda|pbs|ema|mhra)\b|"
    r"\b(product information|product label|regulatory status|market authorisation|marketing authorization)\b|"
    r"\b(approved|registered|authorised|authorized)\b.{0,50}\b(tga|fda|ema|mhra|regulator|medicine|drug|indication|use)\b|"
    r"\b(is|was|has)\b.{0,30}\b(approved|registered|authorised|authorized)\b\??$",
    re.I,
)

# Registry routing is for discovery/registry questions. Questions asking what
# trials "show" about efficacy remain literature/evidence-synthesis questions.
TRIAL_DISCOVERY_CUES = re.compile(
    r"\b(recruiting|enrolling|ongoing|active)\b.{0,50}\b(clinical trials?|stud(?:y|ies))\b|"
    r"\b(clinical trial registry|trial registry|clinicaltrials\.gov|nct\d+)\b|"
    r"\b(find|list|identify|are there)\b.{0,60}\bclinical trials?\b",
    re.I,
)


def classify_consequence(text: str) -> tuple[ConsequenceLevel, list[str]]:
    matched = [name for name, pattern in HIGH_CONSEQUENCE_PATTERNS.items() if re.search(pattern, text, re.I)]
    return (ConsequenceLevel.HIGH if matched else ConsequenceLevel.MODERATE, matched)


def is_patient_specific_or_identifying(text: str) -> bool:
    return bool(PATIENT_CUES.search(text))


def plan_query(question: str, user_mode: str = "clinician", jurisdiction: str = "AU") -> QueryPlan:
    consequence_level, matched = classify_consequence(question)
    high = consequence_level == ConsequenceLevel.HIGH
    patient_specific = is_patient_specific_or_identifying(question)
    regulatory = bool(REGULATORY_CUES.search(question))
    trial_query = bool(TRIAL_DISCOVERY_CUES.search(question))

    intent = ["EVIDENCE_SYNTHESIS"]
    required = ["biomedical_literature"]
    if trial_query:
        intent.append("TRIAL_QUERY")
        required = ["clinical_trial_registry"]
    if regulatory:
        intent.append("REGULATORY_QUERY")
        required = ["regulator"]
    if patient_specific:
        intent.append("PATIENT_SPECIFIC_REQUEST")

    safety_flags = [f"HIGH_CONSEQUENCE:{x}" for x in matched]
    if patient_specific:
        safety_flags.extend(["PATIENT_SPECIFIC", "PATIENT_SPECIFIC_OR_IDENTIFYING"])
    if regulatory:
        safety_flags.append("REGULATORY_SOURCE_REQUIRED")
    if trial_query:
        safety_flags.append("TRIAL_REGISTRY_DISCOVERY_ONLY")

    return QueryPlan(
        intent=intent,
        user_mode=user_mode,
        patient_specific=patient_specific,
        known_user_facts=[],
        unknown_material_facts=[],
        jurisdiction=jurisdiction,
        jurisdiction_material=regulatory,
        temporal_sensitivity="high" if regulatory or trial_query else "moderate",
        consequence_level=consequence_level,
        required_source_classes=required,
        retrieval_questions=[question],
        required_second_pass=high,
        safety_flags=safety_flags,
    )
