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
