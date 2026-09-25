# Contributing

## Branches

Create work from the latest `main` using a short-lived branch:

- `feat/<name>` — new application behavior
- `fix/<name>` — defect repair
- `test/<name>` — evaluation/regression work
- `docs/<name>` — documentation only
- `chore/<name>` — repository/tooling maintenance

## Pull requests

Each PR should state:

- observable behavior being changed;
- requirement/safety invariant affected;
- files or contracts changed;
- checks actually run and their results;
- checks not run, blocked, or unproven;
- privacy/security implications;
- rollback or compatibility implications where relevant.

Use precise evidence language. A test file is not a test run. A green unit suite is not live connector verification. A package build is not deployment.

## Medical safety changes

For changes touching medical claims, consequence classification, source admissibility, provenance, retractions, jurisdiction, PHI routing, or abstention:

1. reproduce the defect or define the failing acceptance condition;
2. add a regression test that fails before the fix where possible;
3. implement the narrowest fix;
4. run the affected focused tests and the full regression suite;
5. preserve adverse evidence and unresolved gaps in the PR.

## Sensitive information

Never commit or paste real patient data, credentials, tokens, private keys, Medicare numbers, medical-record exports, or other identifying health information. Use synthetic fixtures.

## Source material

Prefer first-party regulators, guidelines, registries, and primary literature according to the claim-specific source policy. Do not copy proprietary medical content into the repository without explicit rights.
