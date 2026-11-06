# Alpha3 A1 — authority contracts implementation candidate — 5 November 2026

**Issue:** [#24 Alpha3 A1: closed authority schemas and deny-by-default policy compiler](https://github.com/Subzteveo/Medical-AI/issues/24)
**Base `main`:** `29296f62fdf0b9a7203b4e4b8e14939a48ce575c`
**Recorded:** 5 November 2026, Australia/Darwin
**Disposition:** **IMPLEMENTED (candidate) + TESTED + PASSED locally** for the A1 schema/compiler/policy scope. **NOT VALIDATED, NOT VERIFIED, NOT APPROVED, NOT MERGED, NOT RELEASE_READY.**

This is revision-bound engineering evidence only. It says nothing about medical
safety, clinical validation, privacy compliance or release readiness, and it does
not wire the A1 kernel into the runtime engine (that is A2, separately gated).

## 1. Gate preconditions observed before this work

- **G0 (#2)** enforcement recorded and the issue **closed** by the owner on 5 November 2026
  (required PR + required exact-head `source-and-tests`, force-push/deletion blocked, empty bypass list):
  see [`g0-enforcement-20261105`](../g0-enforcement-20261105/README.md).
- **Tranche A contract (#26)** recovered, owner-signed-off and **hash-pinned**, issue **closed**:
  see [`tranche-a-contract-20261105`](../tranche-a-contract-20261105/README.md).

These were the stated prerequisites for an A1 implementation PR. Merge itself remains
the owner's act after human review; this record does not assert merge or approval.

## 2. What was implemented (additive only)

Per [A1 review contract](../../ALPHA3_A1_SCHEMA_POLICY_REVIEW.md) and
[A1 policy review cases](../../ALPHA3_A1_POLICY_REVIEW_CASES.md):

- `src/medical_ai/authority.py` — closed, immutable (`frozen=True`, `extra="forbid"`)
  canonical types: `SourceVersion`, `ClaimEvidenceLink`, `TypedJudgment`, the shared
  `AuthorityDecisionEnvelope`, `EvidenceAuthorityDecision`, `InformationHandlingDecision`,
  `DataPlaneTransitionDecision`, `StatusClaimRecord`; closed enums; timezone-aware
  timestamps; nonblank identifiers; and the denial-preserving `migrate_information_class`
  adapter (`SENSITIVE -> UNKNOWN`; no legacy flag becomes de-identified/restricted).
- `src/medical_ai/authority_policy.py` — the policy compiler
  (`YAML decode -> strict closed schema -> digest-verified immutable bundle -> scoped decision`),
  with prohibition-dominant, order-independent resolution and default DENY.
- Five packaged policies under `src/medical_ai/policies/`, mirrored byte-for-byte under
  `policies/`: `evidence-authority-v0.2.yaml`, `information-handling-v0.2.yaml`,
  `data-plane-transitions-v0.2.yaml`, `status-claims-v0.1.yaml`,
  `influence-aggregation-v0.2.yaml`. Each carries a reproducible `policy_digest`.
- Tests: `tests/test_authority_schemas.py`, `tests/test_authority_policy_compile.py`,
  `tests/test_information_class_migration.py`, `tests/test_status_claim_contract.py`.
- `pyproject.toml` and `scripts/verify_influence_boundary.py` extended so the strict
  Pyright gate and the influence-boundary source guard both cover the new authority code.
- `provenance/SOURCE_SHA256SUMS` updated to list the new source files.

No change was made to `engine.py`, `renderer.py`, `api.py`, `connectors/`, the existing
`policies/*-v0.1.yaml`, the existing deterministic suite, `AuthorizedClaimView`, or the
active influence runtime. The authority modules are not imported by the runtime.

## 3. Candidate policy decision behaviour exercised

The packaged policies and compiler reproduce the documented A1-POL / A1-STA candidate
expectations as deterministic tests, including: PubMed literature and ClinicalTrials.gov
registration facts as **conditional admission**; registry narrative as treatment efficacy,
PubMed as AU regulatory approval, retracted/superseded/unknown-freshness sources, identifiable/
de-identified/restricted information classes, CLINICAL/RESEARCH→EVIDENCE promotion, and
`PROMOTE_TO_EVIDENCE` all **DENY**; underspecified requests and caller-omitted mandatory
dimensions **DENY**; digest mismatch, duplicate rule IDs, unknown enum/field, non-DENY default
and out-of-dimension scope keys **reject the load**.

A policy-level ALLOW is a *conditional admission*: provenance, exact claim, source
version/freshness and verification remain separate required gates, and ALLOW decisions
cannot be constructed without an independent authority source and policy-required evidence.

## 4. Local check results at the working tree (pre-merge)

Run in a clean `.[dev]` environment on base `29296f62`:

- strict Pyright (`pyproject.toml` scope incl. both new modules): **0 errors, 0 warnings**;
- influence-boundary source guard: **passed** (7 authoritative files);
- deterministic pytest suite: **358 passed, 1 warning** (was 311; +47 A1 tests);
- `python -m compileall -q src`, package import, and `verify_package_policies.py` parity: **passed**;
- `verify_source_checksums.py` and `check_repo_hygiene.py`: **passed**;
- Alpha3 engineering harness CLI: ran to completion (blocked/unproven fidelity cases unchanged).

## 5. Not done / still gated

- A2 engine/renderer/API integration of independently-resolved authority (Issue #25); the
  self-declared-authority gap in the current engine is **unchanged** by this PR.
- Independent human review and **exact PR-head CI** — read these from the PR, not this file.
- Clinical/privacy/regulatory validation and any release decision — **NO-GO is unchanged**.

`PASSED`/`TESTED` here are bound to the stated base and the PR head recorded on the PR.
A green exit code supports only the engineering assertions actually exercised above.
