# Pre-Claude Code handoff — Medical AI

**Observed:** 4 November 2026  
**Status:** Proposed coordination handoff / not an owner-approved contract  
**Repository:** `Subzteveo/Medical-AI`  
**Read-only audit base:** `93c20dbf77148d2ab0c0bac2b31767107eea5533`  
**Tracking issue:** [#38](https://github.com/Subzteveo/Medical-AI/issues/38)

This is a dated engineering handoff. It does not replace `AGENTS.md`, the product contracts, `project_docs/STATUS.md`, or `docs/RELEASE_READINESS.md`. Recheck `main` and the relevant exact-SHA checks before relying on any status here.

## Verified engineering context at audit base

- `main` is public and active; zero open PRs at audit time and six pre-existing open issues (#2, #5, #20, #24, #25, #26).
- Application entry point is FastAPI `src/medical_ai/api.py`. The existing application has PubMed and ClinicalTrials.gov adapters, an extractive evidence pipeline, influence controller, a static Evidence Atlas browser UI, SQLite trace storage and a source-level invitation/session access gate.
- Existing interface has responsive CSS; actual iOS/Android, real-browser accessibility and human-factors acceptance remain unverified.
- [Exact-HEAD CI](https://github.com/Subzteveo/Medical-AI/actions/runs/41334337248) reported **311 passing pytest tests and one warning**, a passed strict type-safety step, and a passed Alpha3 fixture CLI. Four required cases passed; two cases remained formally **BLOCKED** despite observed expected terminal states; three checks remained **UNPROVEN**. These are engineering fixtures, not clinical validation.
- CodeQL Python and JavaScript/TypeScript checks also succeeded at the audit SHA.
- The active `LAB AI Sec` ruleset (ID `24023881`) protects against deletion and non-fast-forward history, but does **not** include required PR or required-check rules. The separate branch protection read was denied (HTTP 403), so other enforcement cannot be ruled out; required enforcement has **not been demonstrated**.

## Binding constraints and owner decisions

1. **A model is never evidence.** Preserve the independent evidence, information-handling/PHI, typed plane-transition and applicable revision-bound status authority dimensions. Do not interpret a passing verifier or model-populated `APPROVED` field as independent authority.
2. The authoritative Alpha3 A1–A4 engineering contract must be recovered **verbatim**, scope/approval verified, and preserved before implementation merges. Issue [#26](https://github.com/Subzteveo/Medical-AI/issues/26) is open; derivative summaries are insufficient.
3. [Issue #2](https://github.com/Subzteveo/Medical-AI/issues/2) governs required-PR and exact-head CI enforcement. This is a human-approved GitHub-admin change; a passing workflow is not equivalent to enforced merge protection.
4. [Issues #24](https://github.com/Subzteveo/Medical-AI/issues/24) and [#25](https://github.com/Subzteveo/Medical-AI/issues/25) remain G0/A1-gated. Current `engine.py` assigns `evidence_authority=APPROVED` and `validation_passed=True` when constructing an influence subject. This is a **reviewed authority-origin trust gap**, not a demonstrated exploit.
5. Current intended use is education, literature/trial discovery, general research and clinician evidence inspection. Do not permit patient-specific CDS, prescribing, diagnosis, autonomous treatment, public PHI routing or emergency triage.
6. The existing pilot operating brief records an individual operator and *proposed* Australian hosting. This task references LAB AI & Tech Solutions. Do not silently change operator/entity or assume hosting has been selected. Australian hosting alone does not establish Australian-only processing.
7. External pen-test access, deployment, pilot invitations, public/commercial release and any clinical expansion each require **separate explicit authorisation**. [Release gate #5](https://github.com/Subzteveo/Medical-AI/issues/5) remains open.

## Pre-Claude preparation (Issue #38)

Proposed review branch: `chore/pre-claude-handoff-20261104`.

- Dated documentation handoff; no updates to frozen medical/IP specifications.
- Optional local, **read-only** helper: `python scripts/check_agent_preflight.py --expected-sha <verified-40-character-SHA>`. It checks the local Git root, head, clean worktree and mandatory contract paths, returning JSON. It does **not** check remote GitHub protection, source integrity, medical safety, regulated intended purpose or release approval.
- Submit this small preparation branch as **draft PR**. Do not merge without owner review and exact-head checks.

## Next execution order for Claude Code

| Gate | Narrow next action | Acceptance evidence | Owner/reviewer decision |
| --- | --- | --- | --- |
| G0 review | Recheck `main`, draft PR and actual CI | Exact SHA, branch/check readbacks | Accept or reject pre-Claude handoff |
| G1 governance | Fix required PR and required `source-and-tests` enforcement via authorised GitHub admin process; separately locate and preserve original Tranche A contract | Read-back enforced rules and exact contract/provenance | Explicit human approval before A1 |
| A1 | Implement closed schemas and deny-by-default policy compiler under original approved contract | Safety regressions, strict typing, policy parity, exact-head CI, human review | Separate A1 approval |
| A2–A4 | Independently resolved authority, selective revocation and adversarial test obligations as approved | Typed threat/negative cases and exact-revision evidence | Separate gate at each tranche |
| App/mobile | Finish only the approved education/evidence product; responsive mobile web first | API/real-browser/mobile accessibility and user-journey evidence | Approve bounded UX |
| Security / pen test | Independent threat assessment then isolated synthetic-data environment and written rules of engagement | Environment-isolation checks, tester authorisation, finding/retest report | Approve each separate stage |
| Deployment | Select Australian hosting provider/region/processor controls and build private controlled artifact | Deployed SHA identity, smoke tests, monitoring and rollback | Separate deployment decision |
| Release | Clinically reviewed evidence validation, privacy/regulatory/accessibility/operations dossier | Named independent reviews | NO-GO until explicit release approval |

## Claude Code prompt (single initial session)

> You are the Medical AI coding agent for `Subzteveo/Medical-AI`. Read `AGENTS.md`, `README.md`, `project_docs/NORTH_STAR.md`, `project_docs/PROJECT_INDEX.md`, `project_docs/STATUS.md`, `project_docs/DEVELOPMENT_WORKFLOW.md`, `docs/INTENDED_USE.md`, `docs/RELEASE_READINESS.md`, and the applicable Alpha3 G0/A1 documents. Check the live `main` SHA and inspect GitHub Issue #38 and its linked draft PR. Establish what is currently implemented, tested, blocked and unproven, distinguishing source code from verified real-world behaviour. Start with a **read-only** reconciliation of #2 and #26, including actual required PR/CI enforcement and whether the verbatim owner-approved Tranche A contract is present. Present the minimal repair plan, exact files/risks/test commands and explicit human decisions. Do not infer approval, reconstruct missing contract text, edit the medical influence core, merge, deploy, expose PHI or grant external testers access. Stop at the next owner decision gate.

## Final handoff format

Return base/head SHA, work actually done, checks executed with pass/fail/skipped counts and evidence links, open blockers, safety/privacy effects, gate classification (PASS / FAIL / BLOCKED / UNVERIFIED) and **human approval pending**. Do not continue to the next stage without approval.
