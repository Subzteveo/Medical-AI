from __future__ import annotations

from dataclasses import dataclass

from .policy_loader import source_policy as load_source_policy
from .schemas import QueryPlan, SourceRecord

_POLICY = load_source_policy()


@dataclass(frozen=True)
class Qualification:
    admitted: bool
    reason: str


def qualify_source(source: SourceRecord, plan: QueryPlan) -> Qualification:
    if not source.provenance_complete:
        return Qualification(False, "PROVENANCE_INCOMPLETE")
    if source.superseded:
        return Qualification(False, "SOURCE_SUPERSEDED")
    if "regulator" in plan.required_source_classes:
        return Qualification(False, "REGULATORY_SOURCE_REQUIRED")
    if "clinical_trial_registry" in plan.required_source_classes:
        allowed = _POLICY.get("claims", {}).get("trial_discovery", {}).get("alpha2_allowed_sources", [])
        if "clinicaltrials_gov_registry" not in allowed or source.source_type != "clinical_trial_registry":
            return Qualification(False, "SOURCE_CLASS_NOT_ADMITTED")
        return Qualification(True, "ADMITTED_TRIAL_DISCOVERY")
    if "biomedical_literature" in plan.required_source_classes:
        allowed = _POLICY.get("claims", {}).get("biomedical_literature", {}).get("alpha2_allowed_sources", [])
        if "pubmed_indexed_literature" not in allowed or source.source_type != "indexed_biomedical_literature":
            return Qualification(False, "SOURCE_CLASS_NOT_ADMITTED")
        return Qualification(True, "ADMITTED_LITERATURE")
    return Qualification(False, "SOURCE_CLASS_NOT_ADMITTED")
