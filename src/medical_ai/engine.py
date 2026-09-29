from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import uuid
from typing import Mapping

from .schemas import (
    AnswerStatus,
    AuthorityState,
    CitationMapping,
    DataPlane,
    DataPlaneTransition,
    EvidenceAnswer,
    ExecutionTrace,
    InfluenceRequest,
    InfluenceSubject,
    InformationClass,
    VerificationStatus,
)
from .planner import plan_query
from .source_policy import qualify_source
from .extractor import extract_evidence
from .claims import build_claims
from .verifier import verify_claims
from .renderer import render_answer
from .connectors.base import require_evidence_approved
from .policy_loader import phi_routing_policy, evidence_influence_policy
from .influence import InfluenceController

_TRACE_HMAC_KEY = (
    os.getenv("MEDICAL_AI_TRACE_HMAC_KEY", "").encode("utf-8")
    or secrets.token_bytes(32)
)


def _digest_query(text: str) -> str:
    return "hmac-sha256:" + hmac.new(_TRACE_HMAC_KEY, text.encode("utf-8"), hashlib.sha256).hexdigest()


class EvidenceEngine:
    version = "0.2.0-influence-control-core"

    def __init__(self, connectors: Mapping[str, object] | object, trace_store=None, influence_controller=None):
        # Load and enforce packaged runtime policies rather than treating YAML as documentation only.
        phi_policy = phi_routing_policy()
        evidence_policy = evidence_influence_policy()
        if evidence_policy.get("alpha2", {}).get("generative_medical_claims") is not False:
            raise RuntimeError("This extractive runtime requires generative_medical_claims=false")
        if phi_policy.get("rule") is None:
            raise RuntimeError("PHI routing policy is missing its governing rule")
        if isinstance(connectors, Mapping):
            self.connectors = {
                source_class: require_evidence_approved(connector, source_class)
                for source_class, connector in connectors.items()
            }
        else:
            source_class = getattr(connectors, "source_class", "biomedical_literature")
            self.connectors = {source_class: require_evidence_approved(connectors, source_class)}
        self.trace_store = trace_store
        self.influence_controller = influence_controller or InfluenceController()

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
        try:
            connector = require_evidence_approved(connector, source_class)
        except ValueError as exc:
            return self._terminal(
                plan=plan,
                digest=digest,
                status=AnswerStatus.NO_AUTHORITATIVE_SOURCE,
                message=(
                    "### Evidence-bound answer\n\n"
                    f"No evidence-approved {source_class} connector is configured for this workflow."
                ),
                safety_flags=[*plan.safety_flags, f"EVIDENCE_APPROVAL_BLOCKED:{type(exc).__name__}"],
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

        influence_decisions = []
        authorized_claims = []
        for claim in verified:
            if claim.verification_status != VerificationStatus.PASS:
                continue
            claim_sources = [source for source in admitted if source.source_id in claim.source_ids]
            public_non_phi = bool(claim_sources) and all(
                source.phi_status == "non_phi" for source in claim_sources
            )
            subject = InfluenceSubject(
                object_id=claim.claim_id,
                object_type="ClaimRecord",
                data_plane=DataPlane.EVIDENCE,
                evidence_authority=AuthorityState.APPROVED,
                information_handling_authority=(
                    AuthorityState.APPROVED if public_non_phi else AuthorityState.UNKNOWN
                ),
                provenance_complete=bool(claim_sources) and all(
                    source.provenance_complete for source in claim_sources
                ),
                validation_passed=True,
                safety_passed=claim.consequence_level.value != "HIGH",
                # Every answer creates an ExecutionTrace with component versions and gate outcomes.
                monitoring_enabled=True,
                version=self.version,
            )
            decision = self.influence_controller.authorize(InfluenceRequest(
                subject=subject,
                proposition_id=f"user-output:{claim.claim_id}",
                transition=DataPlaneTransition(
                    source_plane=DataPlane.EVIDENCE,
                    target_plane=DataPlane.EVIDENCE,
                    information_class=(
                        InformationClass.PUBLIC if public_non_phi else InformationClass.UNKNOWN
                    ),
                ),
            ))
            influence_decisions.append(decision)
            if decision.allowed:
                authorized_claims.append(claim)

        if any(c.consequence_level.value == "HIGH" for c in verified):
            status = AnswerStatus.HIGH_CONSEQUENCE_VERIFICATION_FAILED
        elif authorized_claims:
            status = AnswerStatus.ANSWER_SUPPORTED_WITH_QUALIFICATIONS
        elif influence_decisions and any(not decision.allowed for decision in influence_decisions):
            status = AnswerStatus.INFLUENCE_DENIED
        elif not admitted:
            if any(s.superseded for s in sources):
                status = AnswerStatus.SOURCE_OUTDATED
            elif any(not s.provenance_complete for s in sources):
                status = AnswerStatus.PROVENANCE_INCOMPLETE
            else:
                status = AnswerStatus.NO_AUTHORITATIVE_SOURCE
        else:
            status = AnswerStatus.EVIDENCE_INSUFFICIENT

        authorized_evidence_ids = {
            evidence_id
            for claim in authorized_claims
            for evidence_id in claim.evidence_ids
        }
        visible_units = [unit for unit in units if unit.evidence_id in authorized_evidence_ids]
        visible_passage_ids = {
            passage_id
            for unit in visible_units
            for passage_id in unit.passage_ids
        }
        visible_passages = [
            passage for passage in admitted_passages
            if passage.passage_id in visible_passage_ids
        ]
        unit_by_id = {unit.evidence_id: unit for unit in visible_units}
        citation_mappings = []
        for claim in authorized_claims:
            for evidence_id in claim.evidence_ids:
                unit = unit_by_id.get(evidence_id)
                if unit is None:
                    continue
                citation_mappings.append(CitationMapping(
                    mapping_id=f"{claim.claim_id}:{evidence_id}",
                    claim_id=claim.claim_id,
                    evidence_id=evidence_id,
                    source_id=unit.source_id,
                    passage_ids=list(unit.passage_ids),
                    entailment_status=claim.entailment_status,
                    verified=claim.verification_status == VerificationStatus.PASS,
                ))

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
            authorization_decision_ids=[decision.decision_id for decision in influence_decisions],
        )
        self._persist(trace)
        return EvidenceAnswer(
            status=status,
            answer_markdown=render_answer(
                authorized_claims,
                admitted,
                trial_discovery="TRIAL_QUERY" in plan.intent,
            ),
            claims=authorized_claims,
            sources=admitted,
            evidence_objects=visible_units,
            citation_mappings=citation_mappings,
            passages=visible_passages,
            trace=trace,
            influence_decisions=influence_decisions,
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
            "influence_controller": self.influence_controller.policy_version,
            "renderer": "alpha2.1",
        }
