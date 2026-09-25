# App by AI v0.7.0 Execution Report — Medical AI

Date: 25 September 2026
Candidate: `medical-ai-v0.1.0-alpha2`
Project classification: **In-flight development**
Requested operation: **Implement + Review**
Lifecycle owner: **app-development-guide**

## Governing evidence discipline

This execution preserves App by AI's evidence states:

`proposed → generated → inspected → executed → passed → verified`

with `blocked` and `unproven` retained where evidence does not justify promotion.

## D0–D8 lifecycle reconciliation

| Stage | Status | Evidence / outcome |
|---|---|---|
| **D0 Idea exploration** | Satisfied by existing project evidence | The Medical AI project already has a defined evidence-bound product direction; no new ideation was needed. |
| **D1 Product and use cases** | Satisfied / canonicalised | Primary users, intended use, MVP/non-goals and observable requirements are recorded in `PRODUCT_FOUNDATION.md`. |
| **D2 Foundation design** | Generated + inspected | Canonical project docs, architecture/contracts, REQ→AC→VAL mapping, decisions/risks and bounded D5 plan now exist. |
| **D3 Git/local bootstrap** | **Unproven / blocked** | No exact GitHub repository + local checkout pair was supplied and verified in this execution. No remote mutation was attempted. |
| **D4 First runnable slice** | Existing evidence + superseded by alpha2 integrated run | Alpha1 provided the first executable evidence slice. Alpha2 retains that evidence contract and extends it. |
| **D5 Incremental delivery** | **Active; alpha2 implemented** | PHI route gate, trial-discovery connector, safe trace store, browser workbench, retrieval-eval plumbing and canonical docs implemented. Automated regression suite executed. |
| **D6 Release readiness** | **NO-GO for public medical release** | Material gates remain unverified/unsatisfied: live source contracts in this environment, real retrieval benchmark, high-consequence verifier, AU regulator sources, PHI production route, browser accessibility runtime, Git provenance. |
| **D7 Deployment/distribution** | Unexecuted / not authorised | No deployment, publication or installation target was requested/verified. |
| **D8 Maintenance** | Planned only | Source/API drift, dependency, defect and evaluation work belong here after a real release/operational target exists. |

## 14-skill processing ledger

| App by AI skill | Internal version inspected | Role in this execution | State |
|---|---:|---|---|
| `app-development-guide` | 0.5.0 | Lifecycle owner; classified project/stage and preserved evidence semantics | **Activated** |
| `application-foundation-architect` | 0.4.0 | Canonicalised the smallest sufficient project foundation and bounded next slices | **Activated** |
| `local-github-development` | 0.3.0 | Assessed D3 evidence boundary; refused to imply local/GitHub linkage without exact repo evidence | **Applied as gate; D3 unproven** |
| `phase-roadmap-tracker` | 1.1.0 | Reconciled D0–D8 implementation/acceptance/delivery states | **Activated** |
| `repository-aware-implementation-engineer` | 0.5.0 | Modified the observed alpha1 baseline into bounded alpha2 changes and tests | **Activated** |
| `engineering-workflow-router` | 0.5.0 | Secondary router was **not activated**, because the App Development Guide already had unambiguous lifecycle ownership | **Correctly inactive** |
| `backend-data-architect` | 1.0.0 | Selected single-process FastAPI + minimal SQLite trace metadata and connector contracts | **Activated** |
| `evidence-based-engineering-researcher` | 0.2.0 | Used official/current source evidence to bound PubMed/ClinicalTrials connector roles; no compliance claims | **Activated** |
| `release-and-lifecycle-engineer` | 0.2.0 | Defined D6 package/readiness states and kept package ≠ publication ≠ deployment distinct | **Activated** |
| `reliability-and-diagnostics-engineer` | 0.3.0 | Preserved source-outage fail-safe behavior and explicit unknown/unavailable outcomes | **Activated** |
| `reliable-powershell-engineer` | 0.5.0 | No Windows/PowerShell execution or handoff was needed in this Linux build environment | **Not applicable this increment** |
| `risk-based-security-privacy-engineer` | 0.2.0 | Found and closed the raw patient-specific public-connector path; constrained trace persistence | **Activated** |
| `ui-ux-accessibility-engineer` | 0.2.0 | Designed/implemented the scoped browser evidence path and accessibility-oriented semantics | **Activated; runtime AT checks unexecuted** |
| `verification-and-evidence-engineer` | 0.3.0 | Mapped claims to checks and executed the integrated regression suite | **Activated** |

## Conditional multi-agent decision

**Single implementation lane selected deliberately.** Alpha2 changes share the QueryPlan, connector contract, engine orchestration, ExecutionTrace schema, API and tests. Those surfaces are tightly coupled enough that parallel lanes would require a shared-contract owner and merge choreography without producing meaningful independent verification. This matches App by AI's rule to decline unnecessary parallelisation.

## Integrated implementation delta from alpha1

1. **Patient-specific route hardening:** detected patient-specific wording now exits before a non-PHI-approved connector is invoked.
2. **Connector routing:** deterministic source-class routing now distinguishes literature, trial discovery and regulatory-authority requirements.
3. **ClinicalTrials.gov adapter:** trial discovery / registered-study facts only; never promoted to efficacy authority.
4. **Trace minimisation:** raw retrieval queries were replaced in ExecutionTrace with SHA-256 digests; SQLite persistence excludes raw question and source text.
5. **Browser workbench:** one accessible-oriented local interface exposes answer status, sources and execution rationale.
6. **Retrieval evaluation plumbing:** recall@k metric and fixture format added, while explicitly not claiming the target is met.
7. **Canonical foundation:** fresh-chat documentation and versioned Medical AI prompt pack added.

## Directly executed evidence

Initial integrated alpha2 test run:

```text
python -m pytest
22 passed in 0.90s
```

A final package verification run is required after all documentation/prompt/package changes; the final observed result supersedes this checkpoint.

## Evidence not promoted beyond its scope

- Static UI inspection does not establish screen-reader/browser compatibility.
- Parser/fixture tests do not establish live ClinicalTrials.gov availability.
- The metric harness does not establish ≥98% authoritative-source recall@k.
- Heuristic patient-specific detection does not establish PHI safety/compliance.
- Package creation does not establish public release or deployment.
- No GitHub/local repository connection is claimed.

## Durable checkpoint

**Current objective:** establish retrieval quality and live source behavior before introducing controlled generative synthesis.

**Next smallest milestone:** alpha3 retrieval-evidence benchmark with clinician/researcher-reviewed gold cases, live network-capable PubMed/ClinicalTrials runs on an exact frozen revision, source-class/freshness checks, and recorded recall@k/error evidence.


## 25 September 2026 ultrareview addendum

The original alpha2 green suite remains a historical execution fact, but later independent ultrareview demonstrated that the suite did **not** establish several safety claims it was being used to support. See `project_docs/ULTRAREVIEW_REMEDIATION_2026-09-25.md`. The alpha2 baseline must not be described as safety-verified on the basis of the original 22 tests.
