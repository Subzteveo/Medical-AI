# Alpha3 A1 — Authority Policy Review Cases (Non-runtime Fixture Specification)

**Authoring date:** 11 October 2026 (Australia/Darwin)  
**Baseline revision:** `13fadd41e628ff60de2cdfff933b3e2be19f1327`  
**Authority:** **NONE**. This is a documentation-only set of expected tests, not executable policy, an executed test suite, validation evidence or a source of medical facts.

Use alongside [A1 canonical schema/policy review contract](ALPHA3_A1_SCHEMA_POLICY_REVIEW.md). After G0 governance read-back, translate these cases into tests for the *actual* packaged policy loader and authority evaluator. The expected results below must never be used as proof the system passed them.

## Review-only policy input contract

All five future rule registries must declare exact `schema_version`, `policy_id`, `revision`, `default_decision: DENY`, nonempty unique `rule_id`, closed operation/purpose/enumeration values, narrow match scope, evidence requirements and a verifiable policy digest. The compiler rejects ambiguity, absent/unknown fields and contradictory same-scope rules, and never resolves unknown input by permissive fallback.

Suggested closed operation names: `RETRIEVE_PUBLIC_EVIDENCE`, `EXTRACT_PASSAGE`, `VERIFY_EXACT_PASSAGE`, `AUTHORIZE_CLAIM_LINK`, `RENDER_EDUCATIONAL_CLAIM`, `READ_CLINICAL_CONTEXT`, `DERIVE_RESEARCH_RESULT`, `PROMOTE_TO_EVIDENCE`, `ASSERT_PROJECT_STATUS`. Names are proposals to align with existing code before final compile; unknown names fail closed.

Suggested closed purpose names: `LITERATURE_DISCOVERY`, `TRIAL_REGISTRATION_DISCOVERY`, `EDUCATIONAL_EVIDENCE_RENDER`, `INTERNAL_PROJECT_ASSURANCE`, `CLINICAL_CONTEXT`, `RESEARCH_ANALYSIS`. Unspecified purpose is never equivalent to educational use.

## Candidate policy decision examples

| ID | Scope / stimulus | Expected policy-level decision | Separate required constraint |
|---|---|---|---|
| A1-POL-001 | Public PubMed indexed passage; general biomedical-literature discovery | Eligible for **conditional admission**, not unconditional ALLOW | Provenance, exact claim, fresh/versioned source and verification still required |
| A1-POL-002 | ClinicalTrials.gov registration fact; trial-discovery purpose | Eligible for **conditional admission** only for registry facts | Registry narrative is not proof of efficacy |
| A1-POL-003 | ClinicalTrials.gov sponsor narrative offered as treatment-efficacy evidence | **DENY** | High-confidence semantic entailment cannot override |
| A1-POL-004 | PubMed study offered as proof of Australian marketing approval | **DENY** | Correct regulator required; no substitute |
| A1-POL-005 | Superseded/retracted source offered as current guideline/effectiveness authority | **DENY** | Historical context, if ever supported, is separately scoped |
| A1-POL-006 | Unknown source version/unknown mandatory freshness | **DENY** | No “most recent” assumption |
| A1-POL-007 | PUBLIC_EVIDENCE through approved public retrieval component, bound discovery purpose | **Conditional permit** | Scope cannot carry patient-specific query content |
| A1-POL-008 | IDENTIFIABLE_HEALTH_INFORMATION passed to PubMed/ClinicalTrials public connector | **DENY** | Evidence approval does not grant handling permission |
| A1-POL-009 | DEIDENTIFIED_HEALTH_INFORMATION without a verified class determination | **DENY** | A string flag saying deidentified is not authorization |
| A1-POL-010 | RESTRICTED_RESEARCH_DATA routed through unapproved model, cache or logging component | **DENY** | Explicit component+operation+environment decision required |
| A1-POL-011 | EVIDENCE → EVIDENCE, PUBLIC_EVIDENCE, permitted extractive operation | **Conditional permit** | Exact purpose and all separate authority gates needed |
| A1-POL-012 | CLINICAL → EVIDENCE, clinical observation promoted to generalized efficacy | **DENY** | Must not silently generalize individual record |
| A1-POL-013 | RESEARCH → EVIDENCE without explicit approved promotion policy | **DENY** | Future workflow not inferred from data availability |
| A1-POL-014 | Same-plane request with UNKNOWN information class/operation/purpose | **DENY** | Same-plane is not blanket authorization |
| A1-POL-015 | Caller removes a mandatory `EVIDENCE_AUTHORITY` dependency from request | **DENY** | Trusted policy selects dimensions; not client |
| A1-POL-016 | Caller presents `validation_passed=True` with no validation evidence ref | **DENY** | Self-certifying field is not proof |
| A1-POL-017 | Policy has overlapping contradictory ALLOW/DENY rules for identical scope | **Reject policy or deterministic DENY** | Never insertion-order-dependent permission |
| A1-POL-018 | Unknown enum, missing rule ID, duplicate ID or digest mismatch | **Reject load / DENY** | Failed policy not cached as active |
| A1-POL-019 | Legacy `InformationClass.SENSITIVE` without verified mapping | **UNKNOWN → DENY** | No implicit PHI/deidentified assumption |
| A1-POL-020 | Old authorization uses policy revision A after mandatory policy revision B takes effect | **STALE/DENY** | Historical proof retained |
| A1-STA-001 | Current document exists at exact identified revision | `DOCUMENTED AUTHORIZED` only | Does not imply `IMPLEMENTED` |
| A1-STA-002 | Documentation claims code implemented, executable artifact absent | `IMPLEMENTED UNAUTHORIZED` | Docs do not grant implementation state |
| A1-STA-003 | Unit-test file exists; no run event | `TESTED UNAUTHORIZED` | Test presence is not execution |
| A1-STA-004 | CI successful at commit A; assertion concerns commit B | `PASSED UNAUTHORIZED` for B; historical A retained | Revision binding mandatory |
| A1-STA-005 | Unit tests pass; no independent validation protocol executed | `VALIDATED UNAUTHORIZED` | `PASSED` is not `VALIDATED` |
| A1-STA-006 | Assistant recommends approval, designated approver event missing | `APPROVED UNAUTHORIZED` | Conversational engineering approval only covers its authorized scope |
| A1-STA-007 | GitHub PR merged at exact revision, with merge event | `MERGED AUTHORIZED` for that PR/revision only | No implicit clinical approval |
| A1-STA-008 | Required protection or release gate is unsatisfied | `RELEASE_READY UNAUTHORIZED`, `RELEASE_BLOCKED` only with gate evidence | Issue closure cannot override ruleset read-back |
| A1-STA-009 | Status event expired or upstream approval withdrawn | New event/projection `STALE` or revoked | Retain historical assertion |
| A1-STA-010 | New code revision without new check run | Old `PASSED` retained historically; new revision unverified | No floating pass labels |
| A1-STA-011 | Contradictory same-scope/revision status claims | Quarantine/unauthorized pending reconciliation | No automatic latest-wins |
| A1-STA-012 | Approval to implement Alpha3 contract used as clinical approval | `APPROVED UNAUTHORIZED` for clinical release scope | Authority is action- and purpose-specific |

## A1 test implementation target after G0

Create deterministic `tests/test_authority_schemas.py`, `tests/test_authority_policy_compile.py`, `tests/test_information_class_migration.py` and `tests/test_status_claim_contract.py`. Required asserts: strict Pydantic rejection of unexpected fields, disallow naive timestamps, invalid nonempty refs, immutable decision mutation, JSON round-trip without enum widening, policy hash reproducibility, policy parity, no implicit wildcard, no effect on current `AuthorizedClaimView` and existing PubMed/ClinicalTrials alpha behavior.

Each executed case must record `case_id`, test revision SHA, policy digest, expected status, observed status, explicit failure code and result; `BLOCKED`/`NOT_EXECUTED` never count as `PASSED`. Create checks in the same PR as runtime code and update the checksum manifest deliberately. Strict Pyright and the repository's influence-boundary source guard must include any new code capable of granting/denying authority.

## Scope and review gate

This file is **DOCUMENTED only**. It does not satisfy `TESTED`, `PASSED`, `IMPLEMENTED`, `VALIDATED`, `APPROVED` for an operating feature, or `RELEASE_READY`. No medical output must depend on any example in this file. The runnable A1 PR must wait until required-PR and exact-head CI enforcement are read back from GitHub and human code review is possible.
