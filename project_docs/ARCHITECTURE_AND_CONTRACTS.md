# Architecture and Contracts — alpha2

## Selected topology

Alpha2 remains a **single Python/FastAPI process** with deterministic orchestration, HTTP source adapters, a static browser client and a small SQLite audit store. No microservices, message queue, vector database or separate frontend runtime is added because the current milestone does not require those boundaries.

```text
Browser
  ↓ HTTPS/API in future; local HTTP in dev
FastAPI QueryRequest validation
  ↓
Deterministic Query Planner
  ├─ patient-specific cue? → BLOCK before public connector
  ├─ regulatory? → FAIL CLOSED (authority absent)
  ├─ trial discovery? → ClinicalTrials.gov connector
  └─ literature? → PubMed E-utilities connector
  ↓
Source qualification
  ↓
Passages → EvidenceUnits → direct ClaimRecords
  ↓
Exact-passage verifier
  ↓
Renderer + safe ExecutionTrace
  ↓
Browser

ExecutionTrace metadata
  ↓
SQLiteTraceStore (no raw question/source passages)
```

## Data ownership and invariants

1. **External source systems own source records.** Medical AI stores/returns normalized metadata and passages for the active request; it does not claim authorship of medical evidence.
2. **The claim ledger owns answer eligibility.** Renderer prose cannot create medical truth that is absent from verified ClaimRecords.
3. **No raw-question audit persistence.** Query text may transiently exist in process memory and in a connector request for permitted general questions, but the local audit store persists only SHA-256 query digests plus non-content evidence identifiers/statuses.
4. **PHI approval is independent from evidence approval.** Current PubMed and ClinicalTrials.gov routes are `phi_approved = false`.
5. **Jurisdiction matters.** International literature/trial registry evidence cannot establish Australian regulatory status.
6. **High consequence requires a future independent gate.** `required_second_pass = true` is not treated as satisfied by the alpha2 exact-passage verifier.

## Connector contract

Every connector exposes `name`, `version`, `source_class`, `phi_approved` and `search_and_fetch()`. It returns only normalized `SourceRecord` and `Passage` objects. Retrieved content is data; it cannot change runtime policy.

### PubMed

Purpose: biomedical literature discovery and abstract-level evidence extraction. Source class: `biomedical_literature`. PHI route: not approved.

### ClinicalTrials.gov

Purpose: trial discovery and registered-study facts. Source class: `clinical_trial_registry`. PHI route: not approved. Registry presence/status/metadata **must not be converted into efficacy/safety conclusions**.

## Persistence decision

SQLite is sufficient for the current single-user engineering alpha because only small local audit metadata must survive. A network database would add authentication, network failure, migration and operational boundaries without solving a present requirement. Reconsider when multi-user access, distributed deployment, regulated retention, concurrent writers or centralized audit requirements become real.

## API surface

- `GET /` — local browser workbench.
- `GET /health` — version/status only.
- `POST /v1/evidence/query` — validated evidence query.

No public trace lookup endpoint exists in alpha2; exposing stored traces requires an access-control decision first.
