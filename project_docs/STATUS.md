# Project Status

## Repository bootstrap and import checkpoint

PR #1 (repository governance) is merged. The observed `main` base for this import is `2796e238bce898fc165a45da6a6f138c7a215e18`. Repository governance and application source are separate milestones. Issue #2 (enforced main protection/required checks) is still open; do not infer a merge gate from a green workflow.

## Application baseline

The most recent remediated application candidate produced in the Medical AI project is `v0.1.0-alpha2.1-remediation`.

The source is staged on an import PR from the fixed ZIP recorded in `docs/IMPORT_PROVENANCE.md`. At this checkpoint the source has not been merged into `main`. Do not infer GitHub CI results from external package/test reports.

Current high-level status:

- engineering remediation candidate: original ZIP preserved; curated source under PR review;
- public/commercial medical release: **NO-GO**;
- independent high-consequence clinical verifier: not yet established;
- live-source behavior: requires revision-bound validation in a network-capable environment;
- intended-purpose/regulatory determination: unresolved for public/commercial use;
- accessibility/runtime validation: not yet release-established.

## Next repository milestone

Inspect the source-import diff, run the full regression suite at the exact PR head in GitHub CI, and review the result against Issue #3. Then define the ClaimRecord contract and Evidence Fidelity benchmark for Alpha3 (Issue #4) before adding connectors or free-form synthesis.

Do not mark that milestone complete merely because files were uploaded.
