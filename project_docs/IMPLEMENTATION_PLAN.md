# Implementation Plan — App by AI D5

## Current integrated milestone: alpha2

| Slice | Outcome | Evidence state |
|---|---|---|
| M5.1 PHI-route hardening | obvious patient-specific wording blocked before public connectors | **Executed / passed** automated checks; comprehensive PHI detection is **unproven** |
| M5.2 Source routing | PubMed literature vs ClinicalTrials.gov trial discovery vs regulatory fail-closed | **Executed / passed** fixture routing/parser checks; live ClinicalTrials network call **unproven** in this environment |
| M5.3 Durable safe trace | SQLite audit persistence without raw question/source passages | **Executed / passed** automated persistence inspection |
| M5.4 Browser workbench | one-page query/source/trace workflow with labelled native controls | **Generated / inspected / automated shell check passed**; real browser keyboard/screen-reader run **unexecuted** |
| M5.5 Retrieval evaluation plumbing | recall@k functions + fixture gold format | **Executed / passed** metric unit checks; ≥98% authoritative-source target **not established** |
| M5.6 Canonical project foundation | fresh-chat navigable project_docs and App by AI lifecycle ledger | **Generated / inspected**; repository review/commit **unproven** |

## Why single-lane

This increment intentionally remains one implementation lane. Connector routing, query planning, schemas, trace shape, API output and tests share contracts and changed together. Splitting them into concurrent branches would create shared-surface merge risk without enough independence to justify App by AI multi-agent coordination.

## Next bounded slice — alpha3 candidate

**Goal:** establish retrieval quality before allowing generative evidence synthesis.

1. Create a clinician/researcher-reviewed gold set of general medical literature/trial-discovery queries with expected authoritative source identifiers or source classes.
2. Run PubMed/ClinicalTrials.gov live retrieval in a network-capable controlled environment against the frozen revision.
3. Measure recall@k, source-class correctness, no-result behaviour and query-routing errors.
4. Record exact environment, connector versions, timestamps and failures.
5. Add current-source freshness/version monitoring for the adapters.
6. Only after retrieval is acceptably evidenced, design a constrained generative synthesis experiment behind the ClaimRecord verifier; do not promote it to production influence automatically.

## Gated future work

- **TGA/PBS adapters:** prerequisite for Australian regulatory/medicines claims.
- **SNOMED CT-AU/AMT/Ontoserver:** terminology plane after licence/environment decisions.
- **Independent high-consequence verifier:** prerequisite for high-consequence claim release.
- **Authentication/PHI-approved route:** prerequisite before patient-specific data or public multi-user deployment.
- **D3 Git/GitHub:** blocked until exact target repository/local linkage is supplied and verified.
