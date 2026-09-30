from __future__ import annotations

import hashlib
from typing import Any

import httpx

from medical_ai.retrieval_query import normalize_search_query
from medical_ai.schemas import InformationClass, Passage, PHIClassification, SourceRecord

API_BASE = "https://clinicaltrials.gov/api/v2/studies"


def _hash_id(prefix: str, value: str) -> str:
    return f"{prefix}_{hashlib.sha256(value.encode('utf-8')).hexdigest()[:16]}"


def _nested(obj: dict[str, Any], *keys: str, default=None):
    current: Any = obj
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
        if current is None:
            return default
    return current


class ClinicalTrialsConnector:
    """ClinicalTrials.gov API v2 adapter for trial discovery only."""

    name = "clinicaltrials-gov-v2"
    version = "alpha2.1-red-remediation"
    source_class = "clinical_trial_registry"
    evidence_approved = True
    phi_approved = False

    def __init__(self, *, timeout: float = 20.0):
        self.timeout = timeout

    async def search_and_fetch(self, query: str, limit: int = 5) -> tuple[list[SourceRecord], list[Passage]]:
        params = {
            "query.term": normalize_search_query(query),
            "pageSize": str(limit),
            "format": "json",
        }
        if "recruiting" in query.lower():
            params["filter.overallStatus"] = "RECRUITING"
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            response = await client.get(API_BASE, params=params)
            response.raise_for_status()
            return self._parse_payload(response.json())

    @staticmethod
    def _parse_payload(payload: dict[str, Any]) -> tuple[list[SourceRecord], list[Passage]]:
        sources: list[SourceRecord] = []
        passages: list[Passage] = []
        for study in payload.get("studies", []):
            protocol = study.get("protocolSection", {})
            identification = protocol.get("identificationModule", {})
            status = protocol.get("statusModule", {})
            design = protocol.get("designModule", {})
            description = protocol.get("descriptionModule", {})

            nct_id = identification.get("nctId")
            if not nct_id:
                continue
            title = identification.get("briefTitle") or identification.get("officialTitle") or nct_id
            org = _nested(identification, "organization", "fullName", default="Study sponsor/investigator")
            overall_status = status.get("overallStatus")
            study_type = design.get("studyType")
            phases = design.get("phases") or []
            last_update = _nested(status, "lastUpdateSubmitDate") or _nested(status, "studyFirstSubmitDate")
            conditions = _nested(protocol, "conditionsModule", "conditions", default=[]) or []

            src = SourceRecord(
                source_id=f"ctgov:{nct_id}",
                authority="ClinicalTrials.gov / U.S. National Library of Medicine",
                publisher=str(org),
                source_type="clinical_trial_registry",
                title=title,
                jurisdiction="INTERNATIONAL",
                record_id=nct_id,
                stable_url=f"https://clinicaltrials.gov/study/{nct_id}",
                identifiers={"NCT": nct_id},
                updated_date=last_update,
                evidence_class="trial_registry_record",
                phi_classification=PHIClassification(
                    classification_id=f"public:ctgov:{nct_id}",
                    object_id=f"ctgov:{nct_id}",
                    information_class=InformationClass.PUBLIC,
                    contains_phi=False,
                ),
                provenance_complete=True,
                raw_metadata={
                    "overall_status": overall_status,
                    "study_type": study_type,
                    "phases": phases,
                    "conditions": conditions,
                },
            )
            sources.append(src)

            structured_facts = [f"ClinicalTrials.gov lists {nct_id} with the title: {title}."]
            if overall_status:
                structured_facts.append(f"The registry status for {nct_id} is {overall_status}.")
            if study_type:
                structured_facts.append(f"The registered study type for {nct_id} is {study_type}.")
            if phases:
                structured_facts.append(f"The registered phase for {nct_id} is {', '.join(phases)}.")
            if conditions:
                structured_facts.append(f"The registered conditions for {nct_id} include {', '.join(conditions)}.")

            for idx, text in enumerate(structured_facts):
                passages.append(Passage(
                    passage_id=_hash_id("passage", f"{nct_id}:fact:{idx}:{text}"),
                    source_id=src.source_id,
                    section="REGISTRY_FACT",
                    text=text,
                    locator=f"protocolSection.fact[{idx}]",
                ))

            # Preserve sponsor/investigator narrative for inspection/provenance,
            # but the extractor will not promote it to efficacy/safety claims.
            for key, label in (("briefSummary", "BRIEF_SUMMARY"), ("detailedDescription", "DETAILED_DESCRIPTION")):
                text = description.get(key)
                if text:
                    passages.append(Passage(
                        passage_id=_hash_id("passage", f"{nct_id}:{key}:{text}"),
                        source_id=src.source_id,
                        section=label,
                        text=text,
                        locator=f"protocolSection.descriptionModule.{key}",
                    ))
        return sources, passages
