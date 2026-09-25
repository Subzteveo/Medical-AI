# Medical AI

Evidence-bound medical research and education software built around authoritative sources, explicit provenance, controlled state, and fail-closed safety boundaries.

Developed by Oli and Stevie.

## Current status

**Pre-release development. Not approved for clinical use, diagnosis, prescribing, patient-specific treatment decisions, or public/commercial medical release.**

The repository is being bootstrapped before application source is imported. The latest remediated application artifact has passed its bounded automated/package verification, but live-source, regulatory/intended-purpose, independent high-consequence verification, accessibility, and public-release gates remain separate evidence requirements.

See [`project_docs/PROJECT_INDEX.md`](project_docs/PROJECT_INDEX.md) for the source-of-truth map and [`project_docs/STATUS.md`](project_docs/STATUS.md) for the current development checkpoint.

## Engineering principles

- A model is never evidence.
- No user-visible medical factual claim without recoverable provenance.
- Source authority is claim-specific and jurisdiction-aware.
- Known, unknown, inferred, and source-supported information remain distinct.
- High-consequence medical claims fail closed.
- Conflict and abstention are legitimate outputs.
- PHI approval and evidence approval are separate.
- Generated prose is a view over verified state; generation must not create medical truth.

## Git workflow

`main` is the stable integration branch. Development happens on short-lived branches and enters `main` through reviewed pull requests. Do not push feature work directly to `main` once branch protection is enabled.

## Privacy

Do **not** place real patient identifiers, Medicare numbers, medical-record data, secrets, access tokens, or other sensitive information in issues, pull requests, commits, fixtures, screenshots, logs, or CI artifacts.

## Licensing

Do not copy proprietary medical content into the repository unless the project has explicit rights to store and redistribute it. Source adapters must preserve licensing/access constraints.
