# Project Index

This file is the entry point for durable project state in GitHub.

## Canonical repository documents

- `README.md` — project identity, boundaries, engineering principles, and current public status.
- `AGENTS.md` — repository instructions for AI-assisted development.
- `CONTRIBUTING.md` — branch, PR, testing, and sensitive-data rules.
- `SECURITY.md` — security/privacy handling and safety-critical defect definition.
- `project_docs/STATUS.md` — current development checkpoint and evidence state.
- `project_docs/DEVELOPMENT_WORKFLOW.md` — branch/PR/check/release flow.

## Documents expected when application source is imported

The application package should bring or establish canonical owners for:

- product requirements and intended use;
- architecture and typed domain contracts;
- Medical Evidence Influence Policy;
- claim/source/consequence policies;
- PHI routing policy;
- validation/evaluation plan;
- release-readiness and known-limitations records;
- source/licensing register;
- versioned runtime/worker prompts.

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
