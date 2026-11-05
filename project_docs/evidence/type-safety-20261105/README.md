# Issue #20 typed control-plane evidence — 5 November 2026

**Issue:** [#20 Type-safe influence control: 100% typed control-plane coverage](https://github.com/Subzteveo/Medical-AI/issues/20)
**Inspected `main`:** `29296f62fdf0b9a7203b4e4b8e14939a48ce575c` (after PR #44)
**Recorded:** 5 November 2026, about 16:45 Australia/Darwin
**Status:** revision-bound engineering evidence for the #20 definition of done. Closing #20 is the owner's decision.

This record says nothing about medical correctness, clinical safety, regulatory compliance or production readiness, matching #20's own non-claims. It does not implement or approve A1 (#24) or A2 (#25).

## 1. Checks executed

| Check | Where | Result | Evidence state |
| --- | --- | --- | --- |
| Strict Pyright over the 5 authoritative files (`schemas.py`, `influence.py`, `engine.py`, `renderer.py`, `connectors/base.py`), `typeCheckingMode = "strict"` | Local, exact revision above | `0 errors, 0 warnings, 0 informations` | passed |
| Influence-boundary static guard (`scripts/verify_influence_boundary.py`) | Local | "5 authoritative files checked; renderer, output, and capability construction paths are singular" | passed |
| Type-safety gate verdict (`scripts/run_type_safety_gate.py`) | Local | `PASSED`; JSON in [`type-safety.json`](type-safety.json), SHA-256 `ffac6058e23fa754d6ef8a63e8a15402935804b470812860743cd7f132dae0f9` | passed |
| Full deterministic regression suite | Local | 311 passed, 1 dependency warning | passed |
| `Deterministic checks` workflow on `main` at this revision (includes the strict type-safety step) | GitHub Actions run #285 | Completed successfully | passed |
| `# type: ignore` / `pyright: ignore`, `Any`, `cast(` in the 5 files | `grep` | 0 / 0 / 0 occurrences | inspected |

## 2. Definition-of-done mapping

| # | #20 item | Evidence | State |
| --- | --- | --- | --- |
| 1 | Influence-capable objects use canonical schemas | `test_canonical_object_model_is_machine_readable`; strict typing of `schemas.py` | passed |
| 2 | Authority dimensions use closed types | `test_unknown_authority_and_information_class_fail_closed`; `test_influence_decision_round_trip_preserves_closed_types_and_authorization` | passed |
| 3 | External input validated before entering the core | `test_malformed_authority_state_is_rejected_at_canonical_construction_boundary`; `test_boundary_guard_rejects_qualified_any` | passed |
| 4 | Authoritative transitions require a typed authorization artefact | Typed artefact required: `test_renderer_view_requires_current_active_authorization`, `test_forged_active_view_cannot_render_medical_proposition`. **Caveat:** the artefact is typed, but `engine.py` still supplies `evidence_authority=APPROVED` and `validation_passed=True` itself. Independent resolution is Issue #25's scope (RED test: PR #40), not a typing defect | passed (typing); independence open in #25 |
| 5 | No direct `ClaimRecord` influence-state mutation outside the transition path | `grep` finds no direct influence-state assignment in `src/`; `test_authorized_claim_id_cannot_be_reused_for_changed_text` | inspected |
| 6 | Renderer bypass without authorization is impossible | `test_renderer_rejects_raw_verified_claim_without_authorization_capability`; `test_revoked_copy_cannot_be_replayed_for_rendering`; boundary guard "renderer … paths are singular" | passed |
| 7 | Dependency and revocation are dimension-typed | `test_revocation_propagates_only_along_matching_authority_dimension` | passed |
| 8 | Exhaustive state-transition tests pass | Transition tests pass (`test_transition_source_plane_mismatch_fails_closed`, `test_explicitly_empty_transition_policy_denies_all_transitions`, `test_conflicting_subject_snapshot_denies_and_requires_higher_revision_update`, `test_higher_revision_weakened_authority_revokes_capabilities`). No test enumerates every state pair, so "exhaustive" is not proven | passed (listed tests); exhaustiveness unproven |
| 9 | Serialization preserves type/state invariants | `test_influence_decision_round_trip_preserves_closed_types_and_authorization`; `test_revoked_decision_remains_serializable_audit_evidence` | passed |
| 10 | Strict static checking reports zero errors for the core | §1 | passed |
| 11 | Malformed/untyped objects fail closed | `test_malformed_authority_state_is_rejected_at_canonical_construction_boundary`; `test_missing_provenance_validation_safety_or_monitoring_fails_closed` | passed |
| 12 | Unrelated authority survives selective revocation | `test_revocation_propagates_only_along_matching_authority_dimension`; `test_evidence_approval_does_not_grant_information_handling_authority` | passed |
| 13 | CI requires static type checking and runtime safety tests | `ci.yml` step "Run strict influence type-safety gate" inside `source-and-tests`, which ruleset `24023881` requires on `main` (see the [G0 enforcement record](../g0-enforcement-20261105/README.md)) | passed |
| 14 | Current v0.2 regression suite remains green | §1 | passed |
| 15 | Revision-bound evidence recorded before closure | This record and `type-safety.json` | passed |

## 3. Limits

- Pyright's strict mode covers the 5 files listed in `pyproject.toml`. Other modules (for example `verifier.py`, `planner.py`, `source_policy.py`) are outside this check. The "100% typed control plane" claim holds for the configured authoritative path, not the whole package.
- Items 4 and 8 carry the caveats in §2. Neither is a type error, but neither should be read as stronger than stated.
- Local results come from a Linux environment with the project's pinned dependencies; GitHub run #285 is the independent confirmation.

## 4. Issue #20 closure

Every definition-of-done item has evidence at `29296f6`, with the two caveats above recorded rather than hidden. Whether those caveats are acceptable for closing #20, or should stay open as follow-ups, is the owner's decision.
