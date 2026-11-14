> **14 November 2026 — build-plan chunk C4: readiness endpoint, structured no-content logging and request id (engineering only, candidate).** On base `7f5dcd18015cc00e5203ba869ae27c6fa1439b84` (C3 merged via PR #61), chunk C4 adds public `GET /health/ready` (booleans per dependency, 503 when not ready), a per-request `X-Request-ID` (caller-supplied only behind a trusted proxy), and JSON-lines application logging restricted to an allowlist of fields — matched route template, method, status and duration only; no query string, body, cookie, token, question or answer — with `httpx`/`httpcore` held at WARNING because connector URLs carry search terms. No engine, renderer, connector, policy, authority-kernel or UI change. This is **generated + executed + passed locally only** and was exercised through the in-process test client, not a running server; it is not verified, audited, merged or deployed. **Public, pilot, commercial and clinical release remain NO-GO.** See the [C4 evidence record](evidence/observability-core-20261114/README.md).

> **13 November 2026 — build-plan chunk C3: container image, dependency lock and CI smoke (engineering only, candidate).** On base `f292523` (C2 merged via PR #60), chunk C3 adds a digest-pinned two-stage `Dockerfile` running as uid 10001, a default-deny `.dockerignore`, an exact-pinned dependency lock, a hardened single-service `deploy/docker-compose.yml` (no host ports, read-only root, all capabilities dropped), a documented `deploy/medical-ai.env.example`, a repository-hygiene rule rejecting tracked `*.env` files, and an independent CI job `container-smoke` that builds the image and exercises the running container. No engine, renderer, connector, policy, authority-kernel, route or UI change. This is **generated + statically tested locally only**: the image build and container run are **unproven** until that CI job executes; no Docker daemon was available locally. Not verified, audited, merged or deployed. **Public, pilot, commercial and clinical release remain NO-GO.** See the [C3 evidence record](evidence/container-image-20261113/README.md).

> **12 November 2026 — build-plan chunk C2: invitation admin tool (engineering only, candidate).** On base `bec3a066ae7d796d03c1ef7f8d2339d5ffedc78d` (C1 merged via PR #59), chunk C2 adds `medical-ai-admin` (`src/medical_ai/admin_cli.py`) to issue, revoke, rotate, list and check pilot invitations in the owner-only allowlist file. Tokens are printed once and never stored; writes are validated and atomic; symlinked or broadly readable files are refused. No engine, renderer, connector, policy, authority-kernel, route or UI change. Local checks on the working tree: strict typing 0 errors, influence-boundary guard passed, **469 pytest passed (was 442; +27)**, checksum/hygiene/parity passed, Alpha3 harness ran. This is **generated + executed + passed locally only** — not verified, audited, merged or deployed; no Kilo Claw audit record exists yet for C1 or C2. The tool does not authorize issuing real invitations. **Public, pilot, commercial and clinical release remain NO-GO.** See the [C2 evidence record](evidence/admin-cli-20261112/README.md).

> **12 November 2026 — build-plan chunk C1: settings module and server entry point (engineering only, candidate).** On base `8a326342343c797e113e58967b712a4b7b86b4ab`, chunk C1 of the [full application build plan](plans/2026-11-11-full-app-build-plan.md) adds typed runtime settings (`src/medical_ai/settings.py`), the `medical-ai-serve` start command with fail-closed start-up checks (`src/medical_ai/server.py`), an out-of-repository allowlist file option (`MEDICAL_AI_PILOT_ACCESS_FILE`) and test isolation from the real state directory. No engine, renderer, connector, policy, authority-kernel or UI change. Local checks on the working tree: strict typing 0 errors, influence-boundary guard passed, **442 pytest passed (was 400; +42)**, checksum/hygiene/parity passed, Alpha3 harness ran. This is **generated + executed + passed locally only** — not verified, audited, merged or deployed. Exact PR-head CI, the Kilo Claw audit and owner review are read from the pull request. **Public, pilot, commercial and clinical release remain NO-GO.** See the [C1 evidence record](evidence/server-settings-entrypoint-20261112/README.md).

> **5 November 2026 — Alpha3 A2 independent authority-origin resolution (engineering only, candidate).** On base `102532f79ddc45925c450b9c16f11062b1d47d15` (A1 merged via PR #45), Issue [#25](https://github.com/Subzteveo/Medical-AI/issues/25) was implemented: the engine's claim loop no longer hard-codes `evidence_authority=APPROVED`/`validation_passed=True`. A trusted `AuthorityResolver` (`src/medical_ai/authority_resolver.py`) now resolves each verified claim's four authority dimensions from the merged, digest-verified A1 policies over the claim's actual scope, and the engine sets influence-subject authority only from that result. The engine takes an optional resolver and **fails closed without one**, so a verifier PASS plus connector admission no longer grant influence — closing the PR #40 authority-origin gap (that RED regression is now green). `api.py` and the Alpha3 harness wire the resolver in; one data-plane policy rule was added for the trial path (digest recomputed, mirrored). No renderer/connector/medical-scope change; A3 revocation/projection and A4 assurance remain out of scope. Local checks on the working tree: strict typing 0 errors, influence-boundary guard passed (8 files), **369 pytest passed (was 358; +11)**, checksum/hygiene/parity passed, Alpha3 harness ran. This is **IMPLEMENTED (candidate) + TESTED + PASSED locally only** — NOT VALIDATED, VERIFIED, APPROVED, MERGED or RELEASE_READY, and Issue #25's independent-reviewer acceptance remains outstanding. Exact PR-head CI and human review are read from the draft PR. **Public, pilot, commercial and clinical release remain NO-GO.** See the [A2 implementation evidence record](evidence/alpha3-a2-20261105/README.md).

> **5 November 2026 — Alpha3 A1 authority-contract implementation candidate (engineering only).** With G0 preconditions now closed — [#2](https://github.com/Subzteveo/Medical-AI/issues/2) repository enforcement and [#26](https://github.com/Subzteveo/Medical-AI/issues/26) Tranche A contract preservation — a bounded, additive A1 implementation was prepared on base `29296f62fdf0b9a7203b4e4b8e14939a48ce575c` for Issue [#24](https://github.com/Subzteveo/Medical-AI/issues/24). It adds closed, immutable authority schemas (`src/medical_ai/authority.py`), a digest-verified deny-by-default policy compiler (`src/medical_ai/authority_policy.py`), five mirrored packaged policies and four deterministic test files, with strict Pyright and the influence-boundary guard extended to cover the new code. No `engine.py`/`renderer.py`/`api.py`/connector/active-runtime change was made; the authority modules are not imported by the runtime, so the A2 self-declared-authority gap is unchanged. Local checks on the working tree: strict typing 0 errors, influence-boundary guard passed, **358 pytest passed (was 311; +47)**, policy parity/checksum/hygiene passed, Alpha3 harness ran (blocked/unproven cases unchanged). This is **IMPLEMENTED (candidate) + TESTED + PASSED locally only**; it is **NOT VALIDATED, VERIFIED, APPROVED, MERGED or RELEASE_READY**. Exact PR-head CI and human review are read from the draft PR, not from this note. **Public, pilot, commercial and clinical release remain NO-GO.** See the [A1 implementation evidence record](evidence/alpha3-a1-20261105/README.md). Older observations below are historical.

> **4 November 2026 — pre-Claude delivery audit (read-only, revision-bound).** The inspected `main` revision was `93c20dbf77148d2ab0c0bac2b31767107eea5533`; its [exact-SHA deterministic CI](https://github.com/Subzteveo/Medical-AI/actions/runs/41334337248) reported **311 passing pytest tests, one warning**, a passed strict type-safety gate and a passed Alpha3 engineering fixture run (four required passes; two formally BLOCKED cases despite matching terminal states; three UNPROVEN checks). The active ruleset `LAB AI Sec` (`24023881`) still had only deletion/non-fast-forward rules; required PR and CI enforcement were not demonstrated (separate branch-protection read 403). Issues [#2](https://github.com/Subzteveo/Medical-AI/issues/2), [#26](https://github.com/Subzteveo/Medical-AI/issues/26) and the gated A1/A2 work remain unresolved. The invite-only access gate and responsive browser source exist, but no new deployed/mobile-device/clinical/privacy/regulatory validation occurred in this audit. **Public, pilot, commercial and clinical release remain NO-GO; no deployment or merge approved.** See [dated coordination plan #38](https://github.com/Subzteveo/Medical-AI/issues/38) and [pre-Claude handoff](PRE_CLAUDE_HANDOFF_2026-11-04.md). Older observations below are historical.

> **27 October 2026 — focused interaction-context correction.** Baseline `a55b0eb` includes merged PR #33. Application revision `8efd7b0` resolves the reproduced research-variable interaction false positive while retaining conservative medicine/mixed/unknown cases and complete abstract context. 292 local regressions pass. Authenticated local-browser-to-live-PubMed execution now returns three complete abstracts for the original broad mindfulness/attention query; original XML, titles, headings and citations match. Clinical correctness remains unproven. See [execution evidence](evidence/research-interactions-20261027/README.md); the PR records final-head CI and integration. No deployment.

> **27 October 2026 — PubMed context correction candidate.** PR #32 is confirmed merged at `de96e7fba8b0a1847a75943bd56d00591bffcb73`. Candidate `c9ff9b3d6ef36b632bbbab633589686258359e96` preserves complete attributed PubMed abstracts, including structured section headings. Local 223-test regression, type/influence and browser checks passed; live targeted discovery matched one original abstract. The broad query now conservatively abstains because the existing classifier mistakes research-variable “interactions” for drug interactions. See [execution evidence and limitations](evidence/pubmed-discovery-20261027/README.md). Current PR/CI determines integration; this checkpoint does not assert merge. No deployment or clinical validation.

> **27 October 2026 — observed engineering progress.** PRs #30 and #31 are merged, preserving query-response privacy/cache corrections and literal Markdown rendering. Registry-attribution correction and a live browser/API trial-discovery demonstration are in PR #32, code revision `341bed920cebf1f5c020f24dc834e3a48f137d94`. See [the revision-bound execution evidence](evidence/trial-discovery-20261027/README.md). Local 218-test regression and live supported/unsupported/unsafe scenarios passed within the documented scope. CI and integration status must be read from the current PR; this checkpoint does not assert its merge. Clinical, privacy and regulatory release boundaries remain unchanged. Earlier dated checkpoints below are historical.

> **21 October 2026 observation and branch candidate.** Live GitHub `main` remains `9aaf79627acf2bdc85940764aebd4eb2737e8203` (PR #27). Its [deterministic run](https://github.com/Subzteveo/Medical-AI/actions/runs/39411640802) and Code Quality/CodeQL runs passed for that SHA; those runs do not cover the new branch below.
>
> Branch `fix/provenance-integrity-passport` contains a bounded local output-integrity repair (`ac804d3fc3942619a180033bbb72c211271b7d69`) followed by a Passport/boundary-panel candidate. See [the UI contract](EVIDENCE_ATLAS_UI.md) for implemented behaviour and verification limits. Local Python and DOM checks passed; browser execution is blocked by a runtime socket restriction. New-head GitHub CI and human review remain pending. No merge, deployment, live-source/clinical validation or release approval is established.
>
> **Governance remains separate and unresolved.** [Issue #2](https://github.com/Subzteveo/Medical-AI/issues/2) and [issue #26](https://github.com/Subzteveo/Medical-AI/issues/26) are open. Active ruleset `24023881` contains only `deletion` and `non_fast_forward` rules, with no required-PR or required-CI rules. The separate branch-protection read returned 403; no broader enforcement assurance follows. The exact original approved Tranche A contract is still required. **A1 remains gated.** Earlier dated observations below are historical.

---


> **11 October 2026 addendum — revision-bound repository observation.** The 5 October checkpoint below remains historical and must not be read as the present branch head. On 11 October, `main` was observed at `13fadd41e628ff60de2cdfff933b3e2be19f1327` (merged PR #21, type-safe influence-control hardening). The `source-and-tests` and code-quality checks returned successful outcomes for that exact revision. This is engineering-check evidence only, not medical validation. The active `LAB AI Sec` ruleset was observed to enforce deletion/non-fast-forward prohibitions **without** demonstrated required PR and required CI-check gates. Issue #2 is closed but its GitHub enforcement requirements remain unproven. Issue #4 is closed but current Alpha3 live/clinician-reviewed fidelity remains unproven. The proposed four-dimension Tranche A engineering contract has received conversation-level owner approval; no machine-evaluated project-status approval, clinical authorization or release-readiness claim follows. See [G0 checkpoint](ALPHA3_TRANCHE_A_G0_CHECKPOINT.md). **Safety-kernel merge remains gated on GitHub enforcement read-back and human-reviewed exact-head checks.**

---

# Project Status

**Checkpoint date:** 5 October 2026  
**Repository:** `Subzteveo/Medical-AI`  
**Current observed `main`:** `c5bd93b4f8c8234f83dfa88efdf656cc92b60d16`  
**Stage:** engineering alpha / evidence-control architecture  
**Release posture:** **NO-GO for clinical use or public/commercial medical deployment**

## Current repository state

The exact alpha2.1 remediation application source has been imported into GitHub and merged. The repository now contains executable application source, deterministic tests/CI, evidence policies, provenance records and the v0.2 evidence-influence control core.

PR #10 (`feat: add v0.2 evidence influence control core`) is merged into `main`.

The final PR head (`0c8ee71b08f9514d76a715f3f48a82c44f346b7a`) had revision-bound deterministic CI evidence including:

- exact-SHA checkout: passed;
- 76 source checksums verified;
- 93 tracked files passed targeted hygiene checks;
- exact-pinned install: passed;
- complete deterministic pytest suite: **85 passed, 1 dependency deprecation warning**;
- compile/import: passed; and
- installed policy parity/parse: passed.

These results establish bounded engineering assertions for that revision. They do not establish clinical safety, production readiness, regulatory compliance or real-world evidence accuracy.

## Canonical product direction

The long-term product direction is defined in `project_docs/NORTH_STAR.md`:

> **Medical AI is an Australian-first, globally extensible, evidence-bound medical learning and research platform that is Google-simple on the surface and medical-evidence infrastructure underneath.**

The product goal is to turn authoritative medical, regulatory, legal and public-health information into a fast, understandable and traceable evidence experience without allowing an AI model to become the source of medical truth.

This north star is direction, not release authority. The current validated/intended scope remains bounded by `docs/INTENDED_USE.md`, `project_docs/PRODUCT_FOUNDATION.md`, implementation state and validation evidence.

## Implemented architectural baseline

The central rule remains:

> **A model is never evidence.**

Medical AI v0.2 now includes a machine-enforced influence-control layer with:

- canonical typed objects for sources, evidence, claims, citations, connector approval, PHI classification, workflow runs and verification results;
- separate evidence-authority and information-handling/PHI authority states;
- explicit `EVIDENCE`, `TERMINOLOGY`, `CLINICAL` and `RESEARCH` planes;
- fail-closed typed transition policy;
- inspectable authorization artefacts before a verified claim may render;
- dependency tracking and authority-dimension-selective revocation/invalidation;
- stale approved-state replay protection; and
- execution-trace retention of authorization decisions.

The application remains a bounded engineering alpha, not a production medical assistant.

## Current evidence path

The current high-level path remains:

`Question -> request validation -> deterministic query planning -> consequence/jurisdiction routing -> approved source connector -> source/passages -> evidence units -> claims -> claim/evidence verification -> influence authorization -> fail-closed renderer -> answer state + trace`

The current source layer supports PubMed and ClinicalTrials.gov for bounded purposes. They are not substitutes for Australian regulators, current medicines authority, or a high-consequence clinical verification path.

## Current release blockers / unproven areas

Still unproven, incomplete or outside the present validated scope include:

- clinically reviewed authoritative-source retrieval benchmarks and the proposed release-scale recall targets;
- release-scale citation-entailment/correctness evidence;
- statistically meaningful critical-safety evaluation;
- genuinely independent high-consequence verification;
- complete PHI detection and a PHI-approved production processing route;
- authentication, authorization and multi-user tenancy;
- production monitoring, incident response, rollback and operational SLOs;
- TGA and PBS authority integration;
- SNOMED CT-AU / AMT / NCTS terminology integration;
- Australian privacy and health-data compliance implementation/evidence;
- final Australian intended-purpose / medical-device regulatory determination;
- live external-source validation on a release candidate;
- subgroup evaluation;
- real browser, keyboard, screen-reader and mobile accessibility validation;
- complete web/iOS/Android product experience;
- production-grade analytics, onboarding, pricing and commercial operations.

Passing the current test suite does not resolve those blockers.

## Current product boundaries

The current product remains intended for education, evidence retrieval, literature/trial discovery, research support and clinician-facing evidence inspection.

It is not currently validated for autonomous diagnosis, prescribing, treatment selection, emergency triage or patient-specific clinical decision support. Patient-identifying data must not be routed through non-PHI-approved public evidence connectors.

## Immediate development direction

The next build tranches should preserve the working v0.2 control core while moving toward the north star in evidence-backed increments:

1. **Evidence Fidelity:** clinically reviewed benchmarks for source authority, retrieval recall, citation entailment, applicability, freshness, conflict and abstention.
2. **Australian authority foundation:** TGA, PBS and SNOMED CT-AU/AMT/NCTS as first-class jurisdiction/terminology infrastructure, subject to licensing and validation.
3. **Evidence experience:** evolve the browser product from an engineering workbench toward a progressively inspectable, simple evidence experience without hiding uncertainty or provenance.
4. **Privacy and identity:** production-grade authentication/authorization plus enforceable PHI/data-plane boundaries before any patient-context expansion.
5. **Lifecycle assurance:** monitoring, rollback, change control, accessibility and operational evidence before release claims.

Do not begin broad patient-specific or autonomous clinical functionality merely because the infrastructure can technically support it.
