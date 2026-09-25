# Project Status

## Repository state

Status: **governance bootstrap merged; enforcement and application import pending**.

Observed repository state at this checkpoint:

- repository: `9TEVE-O/Medical-AI`;
- visibility: private;
- default branch: `main`;
- current `main`: `2796e238bce898fc165a45da6a6f138c7a215e18`;
- PR #1 (`chore: bootstrap Medical AI repository governance`) is merged;
- governance files are present on `main`;
- `main` branch protection is still not established;
- no required CI status checks are currently established on `main`;
- application source has not yet been imported.

Issue #2 remains the repository-enforcement gate. Issue #3 remains the exact-source import and CI gate.

## Application baseline

The most recent remediated application candidate produced outside this repository is `v0.1.0-alpha2.1-remediation`.

Reported artifact provenance:

- artifact SHA-256: `9f574ff4998ee11ca3ff2a77e6014312159bc96d63457e25f41702fac74f95d8`;
- external package verification reported 63/63 deterministic tests passing from the extracted artifact;
- those results are external artifact evidence, not yet GitHub-revision verification.

The exact remediation source has **not yet been imported into this GitHub repository**. Do not reconstruct it from summaries or copy unrelated development-framework source into this repository. Import must use the exact remediation artifact/source and preserve its provenance.

Current high-level state:

- engineering remediation candidate: available outside the repository;
- repository application implementation: not yet established;
- public/commercial medical release: **NO-GO**;
- independent high-consequence clinical verifier: not yet established;
- live-source behavior: requires revision-bound validation in a network-capable environment;
- intended-purpose/regulatory determination: unresolved for public/commercial use;
- accessibility/runtime validation: not yet release-established.

## Product architecture checkpoint

Working product thesis:

> **Medical AI is an evidence operating system with a conversational interface.**

The fundamental product object is the **claim and its evidence state**, not merely an answer or retrieved document.

`ClaimRecord` is to be mandatory internal infrastructure and the conceptual basis for progressively inspectable evidence. Generated prose is a view over verified state; a model does not create medical truth.

The governing rule remains:

> **A model is never evidence.**

See `CLAIM_RECORD_EPISTEMIC_CONTRACT.md` for the current claim-influence contract.

## Alpha3 direction

Alpha3 is now framed as **Evidence Fidelity**, not retrieval quality alone.

The milestone must establish that Medical AI can correctly construct and gate evidence state before meaningful free-form medical synthesis is allowed:

`Question -> claim/intention classification -> authoritative retrieval -> authority selection -> source admissibility/rejection -> evidence extraction -> ClaimRecord -> claim/evidence verification -> applicability/conflict/freshness checks -> safety gate -> supported/qualified/abstained state`

Retrieval recall@k remains an important metric, but is not sufficient evidence of milestone completion.

See `ALPHA3_EVIDENCE_FIDELITY.md`.

## Next repository milestones

1. Complete Issue #2: enforce the intended PR/check protection on `main` and read back the active configuration.
2. Complete Issue #3: import the exact `alpha2.1-remediation` source, preserve artifact provenance, and establish deterministic CI bound to the PR head.
3. Execute Alpha3 against the imported revision using the Evidence Fidelity contract and revision-bound evaluation evidence.

Do not begin broad generative medical synthesis before these gates are established.
