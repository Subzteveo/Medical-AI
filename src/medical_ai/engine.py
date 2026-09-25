from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import uuid
from typing import Mapping

from .schemas import AnswerStatus, EvidenceAnswer, ExecutionTrace, VerificationStatus
from .planner import plan_query
from .source_policy import qualify_source
from .extractor import extract_evidence
from .claims import build_claims
from .verifier import verify_claims
from .renderer import render_answer
from .policy_loader import phi_routing_policy, evidence_influence_policy

_TRACE_HMAC_KEY = (
    os.getenv("MEDICAL_AI_TRACE_HMAC_KEY", "").encode("utf-8")
    or secrets.token_bytes(32)
)


def _digest_query(text: str) -> str:
    return "hmac-sha256:" + hmac.new(_TRACE_HMAC_KEY, text.encode("utf-8"), hashlib.sha256).hexdigest()


class EvidenceEngine:
    version = "0.1.0-alpha2.1-remediation"

    def __init__(self, connectors: Mapping[str, object] | object, trace_store=None):
        # Load and enforce packaged runtime policies rather than treating YAML as documentation only.
        phi_policy = phi_routing_policy()
        evidence_policy = evidence_influence_policy()
        if evidence_policy.get("alpha2", {}).get("generative_medical_claims") is not False:
            raise RuntimeError("This extractive runtime requires generative_medical_claims=false")
        if phi_policy.get("rule") is None:
            raise RuntimeError("PHI routing policy is missing its governing rule")
        if isinstance(connectors, Mapping):
            self.connectors = dict(connectors)
        else:
            source_class = getattr(connectors, "source_class", "biomedical_literature")
            self.connectors = {source_class: connectors}
        self.trace_store = trace_store

    async def answer(self, question: str, *, user_mode: str = "clinician", jurisdiction: str = "AU", limit: int = 5) -> EvidenceAnswer:
        plan = plan_query(question, user_mode=user_mode, jurisdiction=jurisdiction)
        digest = _digest_query(question)

        if plan.patient_specific:
            return self._terminal(
                plan=plan,
                digest=digest,
                status=AnswerStatus.OUTSIDE_VALIDATED_CAPABILITY,
                message=(
                    "### Evidence-bound answer\n\n"
                    "This request appears to contain patient-specific or identifying health information. "
                    "This build does not send that text to public evidence connectors. Reframe it as a de-identified general evidence question."
                ),
                safety_flags=[*plan.safety_flags, "PHI_ROUTE_BLOCKED"],
            )

        if "regulator" in plan.required_source_classes:
            jurisdiction_label = {
                "AU": "Australian",
                "US": "United States",
                "UK": "United Kingdom",
                "EU": "European Union",
            }.get(plan.jurisdiction.upper(), plan.jurisdiction)
            return self._terminal(
                plan=plan,
                digest=digest,
                status=AnswerStatus.NO_AUTHORITATIVE_SOURCE,
                message=(
                    "### Evidence-bound answer\n\n"
                    f"This question requires an authoritative {jurisdiction_label} regulatory source. "
                    "This build will not substitute PubMed or ClinicalTrials.gov for the required regulator."
                ),
            )

        source_class = plan.required_source_classes[0]
        connector = self.connectors.get(source_class)
        if connector is None:
            return self._terminal(
                plan=plan,
                digest=digest,
                status=AnswerStatus.NO_AUTHORITATIVE_SOURCE,
                message=f"### Evidence-bound answer\n\nNo approved {source_class} connector is configured for this workflow.",
            )
        if not getattr(connector, "phi_approved", False) and plan.patient_specific:
            return self._terminal(
                plan=plan,
                digest=digest,
                status=AnswerStatus.OUTSIDE_VALIDATED_CAPABILITY,
                message="### Evidence-bound answer\n\nThe selected connector is not approved for patient-specific information.",
                safety_flags=[*plan.safety_flags, "PHI_ROUTE_BLOCKED"],
            )

        try:
            sources, passages = await connector.search_and_fetch(question, limit=limit)
        except Exception as exc:
            return self._terminal(
                plan=plan,
                digest=digest,
                status=AnswerStatus.SOURCE_UNAVAILABLE,
                message=(
                    "### Evidence-bound answer\n\nThe required authoritative source is currently unavailable, so the system is not producing a medical evidence answer from memory or fallback generation."
                ),
                connectors_used=[getattr(connector, "name", "unknown")],
                safety_flags=[*plan.safety_flags, f"CONNECTOR_ERROR:{type(exc).__name__}"],
            )

        if not sources:
            return self._terminal(
                plan=plan,
                digest=digest,
                status=AnswerStatus.EVIDENCE_INSUFFICIENT,
                message=(
                    "### Evidence-bound answer\n\nThe configured authoritative source returned no matching records for the retrieval query. "
                    "That does not mean that no authoritative evidence exists."
                ),
                connectors_used=[getattr(connector, "name", "unknown")],
            )

        admitted = [s for s in sources if qualify_source(s, plan).admitted]
        admitted_ids = {s.source_id for s in admitted}
        admitted_passages = [p for p in passages if p.source_id in admitted_ids]

        units = extract_evidence(question, admitted, admitted_passages)
        claims = build_claims(units, plan)
        verified = verify_claims(claims, units, admitted_passages, high_consequence_supported=False)
        passed = [c for c in verified if c.verification_status == VerificationStatus.PASS]

        if any(c.consequence_level.value == "HIGH" for c in verified):
            status = AnswerStatus.HIGH_CONSEQUENCE_VERIFICATION_FAILED
        elif passed:
            status = AnswerStatus.ANSWER_SUPPORTED_WITH_QUALIFICATIONS
        elif not admitted:
            if any(s.superseded for s in sources):
                status = AnswerStatus.SOURCE_OUTDATED
            elif any(not s.provenance_complete for s in sources):
                status = AnswerStatus.PROVENANCE_INCOMPLETE
            else:
                status = AnswerStatus.NO_AUTHORITATIVE_SOURCE
        else:
            status = AnswerStatus.EVIDENCE_INSUFFICIENT

        trace = ExecutionTrace(
            trace_id=str(uuid.uuid4()),
            query_plan=plan,
            retrieval_query_digests=[digest],
            connectors_used=[getattr(connector, "name", "unknown")],
            source_ids=[s.source_id for s in admitted],
            evidence_ids=[e.evidence_id for e in units],
            candidate_claim_ids=[c.claim_id for c in verified],
            verification_results={c.claim_id: c.verification_status.value for c in verified},
            safety_flags=plan.safety_flags,
            component_versions=self._versions(connector),
            final_status=status,
        )
        self._persist(trace)
        return EvidenceAnswer(
            status=status,
            answer_markdown=render_answer(verified, admitted, trial_discovery="TRIAL_QUERY" in plan.intent),
            claims=verified,
            sources=admitted,
            passages=[],
            trace=trace,
        )

    def _terminal(self, *, plan, digest, status, message, connectors_used=None, safety_flags=None) -> EvidenceAnswer:
        trace = ExecutionTrace(
            trace_id=str(uuid.uuid4()),
            query_plan=plan,
            retrieval_query_digests=[digest],
            connectors_used=connectors_used or [],
            source_ids=[], evidence_ids=[], candidate_claim_ids=[], verification_results={},
            safety_flags=safety_flags if safety_flags is not None else plan.safety_flags,
            component_versions=self._versions(None), final_status=status,
        )
        self._persist(trace)
        return EvidenceAnswer(status=status, answer_markdown=message, claims=[], sources=[], passages=[], trace=trace)

    def _persist(self, trace: ExecutionTrace) -> None:
        if self.trace_store is not None:
            self.trace_store.save(trace)

    def _versions(self, connector) -> dict[str, str]:
        return {
            "engine": self.version,
            "connector": getattr(connector, "version", "none") if connector else "none",
            "planner": "alpha2.1-policy-bound",
            "extractor": "alpha2.1-extractive-safety-filtered",
            "claim_builder": "alpha2.1-claim-consequence",
            "verifier": "alpha2.1-exact-passage-high-consequence",
            "renderer": "alpha2.1",
        }
