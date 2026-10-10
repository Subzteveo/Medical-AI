# Alpha3 Tranche A — G0 Governance and Revision-Bound Checkpoint

**Recorded:** 11 October 2026 (Australia/Darwin)  
**Repository:** `Subzteveo/Medical-AI`  
**Inspected `main`:** `13fadd41e628ff60de2cdfff933b3e2be19f1327`  
**Disposition:** governance reconciliation **proposed on a review branch**. This document does not attest that GitHub enforcement, medical validation, or release approval is complete.

## Scope of the owner's decision

The project owner replied `Approved` to the 11 October 2026 *Medical AI — Alpha3 Tranche A: Medical Evidence Influence Control Kernel* implementation contract in the Medical AI project conversation. Treat this as authorization to progress the **engineering plan and its bounded PR workflow**, not as authorization to bypass human review, branch rules, medical authority gates or public/clinical release criteria. This conversation approval is not itself a machine-evaluated `StatusClaimRecord`. Preserve the full reviewed contract as a separate immutable artifact when importing it; do not replace it with this checkpoint.

The approved engineering direction remains inside **Alpha3**, preserving the existing v0.2 controller and PR #21 type-safety protections. The core invariants remain **a model is never evidence** and **medical influence must have current, inspectable authorization**. Status labels such as `IMPLEMENTED`, `PASSED`, `VALIDATED`, `APPROVED`, `MERGED`, and `RELEASE_READY` are independently scoped, revision-bound status claims.

## Evidence read-back on 11 October 2026

| Assertion | Observed authoritative evidence | Current bounded conclusion |
|---|---|---|
| PR #21 merged | [Merge commit](https://github.com/Subzteveo/Medical-AI/commit/13fadd41e628ff60de2cdfff933b3e2be19f1327) | `MERGED` for that change; not an approval for clinical use |
| Deterministic CI succeeded | [Exact-SHA run](https://github.com/Subzteveo/Medical-AI/actions/runs/38063860401) | `PASSED` for the referenced commit/job, not an arbitrary subsequent revision |
| Code-quality check succeeded | [Exact-SHA run](https://github.com/Subzteveo/Medical-AI/actions/runs/38063858617) | `PASSED` for that referenced check; not medical validation |
| Ruleset `LAB AI Sec` active | Ruleset ID `24023881`, read back via GitHub: `deletion`, `non_fast_forward` | Basic protection demonstrated; **required PR/check gates NOT demonstrated** |
| Traditional branch protection | Read-back for `main` shows `required_status_checks.enforcement_level=off`, no required contexts | No evidence that `source-and-tests` is a required merge check |
| Issue #2 | [Repository hardening issue](https://github.com/Subzteveo/Medical-AI/issues/2) is closed | Issue closure does **not** satisfy its unfulfilled hardening criteria |
| Issue #4 | [Alpha3 Evidence Fidelity issue](https://github.com/Subzteveo/Medical-AI/issues/4) is closed; fixture harness records blocked conflict/population cases | Issue closure does **not** establish live or clinician-reviewed benchmark validation |
| Issue #5 | [Release-boundary issue](https://github.com/Subzteveo/Medical-AI/issues/5) remains open | External clinical/public release remains blocked |
| Issue #20 | [Type-safe influence control](https://github.com/Subzteveo/Medical-AI/issues/20) remains open; PR #21 is merged | Completion requires revision-bound acceptance-evidence reconciliation |

The previous 5 October checkpoint in `project_docs/STATUS.md` is **historical**; do not silently re-label its CI numbers as results from 10 October.

## G0 mandatory acceptance evidence (NOT YET SATISFIED)

1. Establish enforced **PR-based changes** for the default branch; prevent direct feature pushes except an explicit documented emergency-recovery procedure.
2. Make exact-head deterministic `source-and-tests` (and any separately designated required security checks) **required** before merge. Read back the active GitHub ruleset/check contexts after the change; workflow existence and green run histories do not suffice.
3. Preserve non-fast-forward / force-push and deletion protection; document effective bypass actors and human merge authority.
4. Demonstrate the effective rules through a non-bypass test or another trustworthy GitHub read-back, bound to the ruleset revision.
5. Reconcile Issue #2's closed status without rewriting its history. A current issue/record should track the still-open enforcement gap until observed.
6. Keep all status evidence qualified by subject, scope, observed revision, source, run/trace reference and observation time. No inference that `MERGED` or `PASSED` equals `VALIDATED`, `APPROVED` or `RELEASE_READY`.

**Stop condition:** Do not merge the safety-control kernel until G0 is evidenced, deterministic checks pass on each exact PR head and a human reviews the diff. GitHub administration is an independent authority, not an assistant-generated claim.

## Subsequent approved work sequence (not marked implemented)

- **PR A1** — closed canonical schemas, source/version/claim-link envelopes, typed policy and status-claim contracts; deny-by-default tests; **no runtime medical influence promotion**.
- **PR A2** — independently resolved claim-specific evidence, handling/transition decisions and revision-bound status authority; conservative integration.
- **PR A3** — typed provenance dependency graph, append-only selective revocation, restart-safe authority projection, point-of-use authorized rendering and API projection.
- **PR A4** — 24 targeted adversarial tests, exact-head evidence, status reconciliation, and full regression/strict type safety checks.

Continue to exclude patient-specific CDS, autonomous diagnosis/treatment/prescribing, free-form synthesis, FHIR/OMOP expansion, new medical connectors, deployment and public/commercial clinical release. No clinical safety or regulatory compliance claim is made.
