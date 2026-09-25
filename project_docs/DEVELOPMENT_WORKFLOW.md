# Development Workflow

## Branch model

Use a simple trunk-based model:

- `main` — stable integration branch;
- short-lived feature/fix/test/docs/chore branches;
- pull request into `main` for every material change.

No permanent `develop` branch is planned unless a future release topology creates a concrete need.

## Required PR evidence

Before merge, the PR should identify:

1. the intended behavior or defect;
2. affected requirement/safety invariant;
3. exact revision under test;
4. focused checks and full regression checks actually run;
5. blocked/unexecuted checks;
6. security/privacy impact;
7. whether live external-source behavior was exercised;
8. whether artifact/package checks apply.

A green exit code supports only the assertions actually exercised. It does not prove deployment, live-source correctness, clinical safety, or regulatory compliance.

## Safety-first implementation order

For reproduced safety defects:

1. capture failing regression evidence;
2. add/confirm the failing regression test;
3. implement the narrowest repair;
4. rerun focused and full suites;
5. update documents whose truth changed;
6. package and verify the exact artifact when release evidence is required.

## CI target

Before application code is merged, GitHub Actions should run at minimum:

- dependency/install check from locked or exact-pinned dependencies;
- unit/regression tests;
- Python compile/import checks;
- checksum verification when a manifest is present (never regenerate it as the verification step);
- targeted secret scanning;
- policy/package consistency checks.

Live PubMed/ClinicalTrials checks should be a separate explicit job or controlled validation path so transient network failure is not confused with deterministic regression failure.

## Merge gate

Do not merge when required checks are failed, skipped, stale, absent, or bound to a different head SHA.

## Release gate

Merge to `main` is not release approval. Packaging, public distribution, clinical intended-purpose approval, deployment, and observed operation remain separate gates.
