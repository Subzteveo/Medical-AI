# Medical AI

An **Australian-first, globally extensible, evidence-bound medical learning and research platform** built around authoritative sources, explicit provenance, controlled influence, and fail-closed safety boundaries.

The product north star is simple on the surface and rigorous underneath: **Google-simple on the surface; medical-evidence infrastructure underneath.** See [`project_docs/NORTH_STAR.md`](project_docs/NORTH_STAR.md).

Developed by Oli and Stevie.

## Current status

**Engineering alpha / pre-release development. Not approved for clinical use, diagnosis, prescribing, patient-specific treatment decisions, or public/commercial medical release.**

The exact alpha2.1 remediation source has been imported and merged. Medical AI v0.2 now includes a machine-enforced evidence-influence control core with independent evidence-authority and information-handling/PHI authority dimensions, typed data planes, authorization artefacts, dependency tracking, selective revocation, and fail-closed rendering integration. PR #10 merged this control core; deterministic CI at its final PR head passed with **85 tests**.

Those engineering results establish only the tested implementation behavior. They do **not** establish clinical safety, production readiness, Australian privacy or medical-device compliance, validated real-world retrieval accuracy, release-scale citation correctness, complete PHI protection, independent high-consequence verification, or live external-source validation.

See [`project_docs/NORTH_STAR.md`](project_docs/NORTH_STAR.md) for the canonical long-term product direction, [`project_docs/PROJECT_INDEX.md`](project_docs/PROJECT_INDEX.md) for the source-of-truth map, [`project_docs/STATUS.md`](project_docs/STATUS.md) for the current development checkpoint, and [`docs/INTENDED_USE.md`](docs/INTENDED_USE.md) for the current intended-use boundary.

## Engineering principles

- A model is never evidence.
- No user-visible medical factual claim without recoverable provenance.
- Source authority is claim-specific and jurisdiction-aware.
- Australian sources, terminology and jurisdiction are first-class where relevant.
- Known, unknown, inferred, and source-supported information remain distinct.
- High-consequence medical claims fail closed.
- Conflict and abstention are legitimate outputs.
- PHI approval and evidence approval are separate.
- Evidence, terminology, clinical-data and research-data planes remain explicitly separated.
- Generated prose is a view over verified state; generation must not create medical truth.
- Passing engineering tests does not by itself establish clinical safety or release readiness.

## Git workflow

`main` is the stable integration branch. Development happens on short-lived branches and enters `main` through reviewed pull requests. Do not push feature work directly to `main`.

## Privacy

Do **not** place real patient identifiers, Medicare numbers, medical-record data, secrets, access tokens, or other sensitive information in issues, pull requests, commits, fixtures, screenshots, logs, or CI artifacts.

## Licensing

Do not copy proprietary medical content into the repository unless the project has explicit rights to store and redistribute it. Source adapters must preserve licensing/access constraints.
