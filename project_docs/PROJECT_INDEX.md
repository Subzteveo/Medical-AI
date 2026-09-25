# Project Index

This file is the entry point for durable project state in GitHub.

## Canonical repository documents

- `README.md` — project identity, boundaries, engineering principles, and current public status.
- `AGENTS.md` — repository instructions for AI-assisted development.
- `CONTRIBUTING.md` — branch, PR, testing, and sensitive-data rules.
- `SECURITY.md` — security/privacy handling and safety-critical defect definition.
- `project_docs/STATUS.md` — current development checkpoint and evidence state.
- `project_docs/DEVELOPMENT_WORKFLOW.md` — branch/PR/check/release flow.

## Application source and current document owners

The alpha2.1 source import adds `src/medical_ai/`, `tests/`, `evals/`, `policies/`, and `prompts/`. The originating ZIP and the curated tree are accounted for in `docs/IMPORT_PROVENANCE.md` and `provenance/SOURCE_SHA256SUMS`.

Key document owners:

- `docs/INTENDED_USE.md` and `project_docs/PRODUCT_FOUNDATION.md` — purpose and audience;
- `project_docs/ARCHITECTURE_AND_CONTRACTS.md` — architecture and typed contracts;
- `docs/MEDICAL_EVIDENCE_INFLUENCE_POLICY_v0.1.md` — evidence influence rules;
- `policies/` — source, consequence, PHI routing and evidence influence policies; `src/medical_ai/policies/` is the identical packaged copy;
- `docs/VALIDATION_PLAN.md` and `project_docs/VALIDATION_AND_EVIDENCE.md` — validation;
- `docs/RELEASE_READINESS.md` and `docs/KNOWN_LIMITATIONS.md` — release boundaries;
- `docs/LICENCE_REGISTER.md` and `docs/SOURCE_MAP.md` — licensing and source mapping;
- `prompts/` — versioned runtime and worker prompts.

Do not duplicate the same durable fact across multiple files. Update the existing owner when its truth changes.

## Reading order for a fresh development session

1. `README.md`
2. `AGENTS.md`
3. this file
4. `project_docs/STATUS.md`
5. `project_docs/DEVELOPMENT_WORKFLOW.md`
6. the specific requirement/policy/architecture document affected by the requested work

## Evidence rule

Repository text describes intent unless backed by execution evidence. Preserve the distinction between proposed, generated, inspected, executed, passed, verified, blocked, and unproven.
