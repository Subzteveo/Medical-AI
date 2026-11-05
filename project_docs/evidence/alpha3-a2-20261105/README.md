# Alpha3 A2 — independent authority-origin resolution — 5 November 2026

**Issue:** [#25 Alpha3 A2: resolve claim-specific evidence and handling authority independently](https://github.com/Subzteveo/Medical-AI/issues/25)
**Base `main`:** `102532f79ddc45925c450b9c16f11062b1d47d15` (A1 merged via PR #45)
**Recorded:** 5 November 2026, Australia/Darwin
**Disposition:** **IMPLEMENTED (candidate) + TESTED + PASSED locally.** NOT VALIDATED, VERIFIED, APPROVED, MERGED or RELEASE_READY. Clinical/privacy/release posture unchanged (NO-GO).

Engineering-governance evidence only. A2 integrates the A1 authority kernel into the
engine's claim loop; it does not broaden medical scope, add connectors, change the
renderer's contract, or persist revocations (A3).

## 1. The defect A2 closes

At the A1 baseline the engine's claim loop constructed every `InfluenceSubject` with
`evidence_authority=APPROVED` and `validation_passed=True` hard-coded — a verifier
`PASS` plus connector admission were treated as authority (the Issue #25
authority-origin trust gap; the owner-approved RED regression from PR #40).

## 2. What was implemented

- `src/medical_ai/authority_resolver.py` — a trusted `AuthorityResolver` that resolves
  each verified claim's four authority dimensions from the merged, digest-verified A1
  policies over the claim's **actual scope** (claim type, source class, freshness/
  retraction, operation, purpose, information class, data plane, consequence,
  jurisdiction, population). Every `ALLOW` is backed by A1 decision records carrying an
  independent authority source, the matching policy digest, an input-state hash, scope,
  empty reasons and a trace reference. `UNRESOLVED` authorises nothing.
- `src/medical_ai/engine.py` — the claim loop now sets `InfluenceSubject`
  `evidence_authority` / `information_handling_authority` / `validation_passed` and the
  transition's information class **only** from the resolver's result. The hard-coded
  `APPROVED` / `validation_passed=True` are removed. **The engine takes an optional
  `authority_resolver`; without one it resolves no authority and every claim fails
  closed at the influence gate.**
- `src/medical_ai/api.py` and the Alpha3 eval harness wire in `AuthorityResolver()` so
  the real product and the harness resolve authority; a bare engine denies.
- `src/medical_ai/policies/data-plane-transitions-v0.2.yaml` gained one rule
  (`dp-evidence-retrieve-registry`) so the trial-registration discovery path is admitted
  end-to-end; digest recomputed and mirrored under `policies/`.
- Tests: `tests/test_authority_resolver.py` (resolver unit behaviour),
  `tests/test_authority_origin_regression.py` (the PR #40 RED fixture, now green, plus a
  positive control and a retracted-source denial), and the supported-path engine tests
  updated to construct the engine through a `make_engine` helper that injects the
  resolver. One assertion in `test_vertical_slice` changed from the
  `INFORMATION_HANDLING_AUTHORITY_UNKNOWN` reason to the now-stronger explicit
  `INFORMATION_HANDLING_AUTHORITY_DENIED`; the gate still denies and nothing is bypassed.
- Strict Pyright and the influence-boundary source guard extended to cover
  `authority_resolver.py` (8 authoritative files). Manifest, `STATUS.md`,
  `PROJECT_INDEX.md` updated.

## 3. Behaviour exercised (deterministic)

- Bare `EvidenceEngine(connector)` (no resolver): a verified claim reaches the influence
  gate and is **DENIED** (`INFLUENCE_DENIED`, no claims) — the RED regression passes.
- The identical fixture **with** the resolver resolves to
  `ANSWER_SUPPORTED_WITH_QUALIFICATIONS`; the only difference is the independent resolver,
  not the evidence. The allowed decision's evidence authority is `APPROVED` from the
  resolver, never a self-declared flag.
- Retracted/superseded source, non-public/unknown information class, source class outside
  its claim class, unmapped source class and high-consequence claims all fail closed, with
  the dimension-specific reason.

## 4. Local check results at the working tree (pre-merge)

Clean `.[dev]` environment on base `102532f`:

- strict Pyright (incl. the resolver): **0 errors, 0 warnings**;
- influence-boundary source guard: **passed** (8 authoritative files);
- deterministic pytest suite: **369 passed, 1 warning** (was 358; +11 A2 tests);
- checksum, hygiene, policy parity, compile/import: **passed**;
- Alpha3 engineering harness CLI: ran to completion (blocked/unproven fidelity cases unchanged).

## 5. Not done / still gated

- A3 persistent/transactional revocation and full API status projection; A4 adversarial
  assurance suite.
- Independent human review and **exact PR-head CI** — read from the PR, not this file.
- A designated **independent human reviewer** acceptance of behaviour and safety trace
  (an Issue #25 acceptance item) remains the owner's/reviewer's act at merge.
- Clinical/privacy/regulatory validation and any release decision — **NO-GO unchanged.**
