# Project Index

This file is the entry point for durable project state in GitHub.

## Canonical repository documents

- `README.md` — project identity, release boundary, engineering principles, and current public status.
- `project_docs/NORTH_STAR.md` — canonical long-term product direction, Australian-first posture, whole-product scope, user experience target, and product decision test.
- `AGENTS.md` — repository instructions for AI-assisted development and north-star alignment.
- `CONTRIBUTING.md` — branch, PR, testing, and sensitive-data rules.
- `SECURITY.md` — security/privacy handling and safety-critical defect definition.
- `project_docs/STATUS.md` — current development checkpoint and evidence state.
- `project_docs/DEVELOPMENT_WORKFLOW.md` — branch/PR/check/release flow.
- `project_docs/CLAIM_RECORD_EPISTEMIC_CONTRACT.md` — claim-level evidence/influence contract and model authority boundaries.
- `docs/INFLUENCE_CONTROL_CORE_v0.2.md` — current machine-enforced influence-control mechanism.
- `project_docs/ALPHA3_EVIDENCE_FIDELITY.md` — Alpha3 milestone scope, benchmark contract, evaluation dimensions, gates, and completion evidence.

## Long-term direction versus current authority

`project_docs/NORTH_STAR.md` defines where the product is going. It must not be read as evidence that a capability is currently implemented, validated, legally cleared, clinically safe, or released.

Current capability and release authority remain with the relevant implementation, intended-use, policy, validation and status documents. A milestone may intentionally implement only a bounded subset of the north star, but it must not silently weaken the governing evidence, provenance, privacy, jurisdiction or safety boundaries.

## Application source and current document owners

The alpha2.1 source import established `src/medical_ai/`, `tests/`, `evals/`, `policies/`, and `prompts/`. The originating ZIP and curated tree are accounted for in `docs/IMPORT_PROVENANCE.md` and `provenance/SOURCE_SHA256SUMS`. Medical AI v0.2 subsequently added the influence-control core and associated tests/documentation.

Key document owners:

- `project_docs/NORTH_STAR.md` — long-term product direction and product-level decision test;
- `docs/INTENDED_USE.md` — current intended purpose and explicit non-intended uses;
- `project_docs/PRODUCT_FOUNDATION.md` — current bounded product/MVP contract;
- `project_docs/ARCHITECTURE_AND_CONTRACTS.md` — architecture and typed contracts;
- `project_docs/EVIDENCE_ATLAS_UI.md` — output provenance boundary, Evidence Passport, deterministic limitations panel and UI verification scope;
- `docs/MEDICAL_EVIDENCE_INFLUENCE_POLICY_v0.1.md` — evidence influence rules;
- `docs/INFLUENCE_CONTROL_CORE_v0.2.md` — machine-enforced influence-control implementation contract;
- `src/medical_ai/authority.py` and `src/medical_ai/authority_policy.py` — Alpha3 A1 candidate closed authority schemas and the deny-by-default policy compiler;
- `src/medical_ai/authority_resolver.py` — Alpha3 A2 trusted resolver that resolves each verified claim's authority from the A1 policies and drives the engine's influence subject; the engine fails closed without it;
- `policies/` — source, consequence, PHI routing and evidence influence policies, plus the Alpha3 A1 authority/handling/data-plane/status/aggregation policies (`*-v0.2.yaml`, `status-claims-v0.1.yaml`); `src/medical_ai/policies/` is the identical packaged copy;
- `docs/VALIDATION_PLAN.md` and `project_docs/VALIDATION_AND_EVIDENCE.md` — validation;
- `docs/RELEASE_READINESS.md` — release boundary, Issue #5 assessment/decision record, unresolved conditions and final disposition;
- `docs/PILOT_CANDIDATE_ASSESSMENT.md` — frozen source assessment for the proposed invitation-only pilot on 1 November 2026; capabilities, access gaps, primary-source regulatory findings and unresolved approval conditions.
- `docs/PILOT_OPERATING_BOUNDARY_AND_REVIEW_BRIEF.md` — supplied operator/hosting/participant boundaries, updated candidate and professional review engagement brief.
- `docs/KNOWN_LIMITATIONS.md` — bounded capability and verification limitations;
- `docs/LICENCE_REGISTER.md` and `docs/SOURCE_MAP.md` — licensing and source mapping;
- `prompts/` — versioned runtime and worker prompts.

Do not duplicate the same durable fact across multiple files. Update the existing owner when its truth changes.

## Reading order for a fresh development session

1. `README.md`
2. `project_docs/NORTH_STAR.md`
3. `AGENTS.md`
4. this file
5. `project_docs/STATUS.md`
6. `project_docs/DEVELOPMENT_WORKFLOW.md`
7. `docs/INTENDED_USE.md` for the current product boundary
8. `project_docs/CLAIM_RECORD_EPISTEMIC_CONTRACT.md` and `docs/INFLUENCE_CONTROL_CORE_v0.2.md` for claim/evidence/influence behavior
9. `project_docs/ALPHA3_EVIDENCE_FIDELITY.md` for the current evidence milestone
10. the specific requirement/policy/architecture/validation document affected by the requested work

## Evidence rule

Repository text describes intent unless backed by execution evidence. Preserve the distinction between proposed, generated, inspected, executed, passed, verified, blocked, and unproven.

## Alpha3 tranche evidence records

- [Alpha3 A1 authority-contract implementation candidate — 5 November 2026](evidence/alpha3-a1-20261105/README.md) — revision-bound engineering evidence for the additive A1 schemas, policy compiler, policies and tests (Issue #24). IMPLEMENTED/TESTED/PASSED locally only; not validated, approved, merged or released.
- [Alpha3 A2 independent authority-origin resolution — 5 November 2026](evidence/alpha3-a2-20261105/README.md) — revision-bound engineering evidence for wiring the trusted authority resolver into the engine so claims fail closed without independently resolved authority (Issue #25). IMPLEMENTED/TESTED/PASSED locally only; not validated, approved, merged or released.

## Preserved authority records

- [Tranche A contract preservation — 5 November 2026](evidence/tranche-a-contract-20261105/README.md) — SHA-256 pin, provenance and owner sign-off for the original 11 October 2026 *Alpha3 Tranche A: Medical Evidence Influence Control Kernel* implementation contract (Issue #26). The full text is held privately by the owner; the G0 checkpoint and A1 review remain derivative records.

## Dated, non-canonical coordination handoffs

- [RET-EXP-001 v0.1](plans/RET-EXP-001-v0.1.md) — frozen offline lexical-baseline
  experiment; [execution evidence](evidence/ret-exp-001-20261113/README.md).
  Synthetic pre-authority selection only; separate from Alpha3 A4 assurance.
  No runtime integration, clinical validation or release authority.

- [Pre-Claude engineering handoff — 4 November 2026](PRE_CLAUDE_HANDOFF_2026-11-04.md) — revision-bound review snapshot, blockers, staged plan and next-agent prompt. It is not a substitute for `STATUS.md`, approved requirements, GitHub enforcement or release authority.
- [Full application build plan — 11 November 2026](plans/2026-11-11-full-app-build-plan.md) and [Kilo Claw audit protocol](plans/KILO_CLAW_AUDIT_PROTOCOL.md) — proposed chunked plan for the self-hosted server, Australian authority adapters, evidence experience and operations, with the per-chunk audit procedure. Nothing in it is implemented; it grants no kernel, deployment or release authority.
