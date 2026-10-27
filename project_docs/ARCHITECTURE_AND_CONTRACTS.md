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

Purpose: biomedical literature discovery and abstract-level evidence extraction. PubMed retains all nonempty AbstractText sections in source order, separated by two newlines, as one Article/Abstract passage. Extraction preserves that whole passage; the browser and Markdown identify it as a publication abstract. Original section labels prefix their sections and remain in source metadata. This prevents keyword matching from discarding neighbouring qualifications, but does not assess study quality or semantic entailment. Source class: `biomedical_literature`. PHI route: not approved.

### ClinicalTrials.gov

Purpose: trial discovery and registered-study facts. Source class: `clinical_trial_registry`. PHI route: not approved. Registry presence/status/metadata **must not be converted into efficacy/safety conclusions**.

## Persistence decision

SQLite is sufficient for the current single-user engineering alpha because only small local audit metadata must survive. A network database would add authentication, network failure, migration and operational boundaries without solving a present requirement. Reconsider when multi-user access, distributed deployment, regulated retention, concurrent writers or centralized audit requirements become real.

## API surface

- `GET /` — local browser workbench.
- `GET /health` — version/status only.
- `POST /v1/evidence/query` — validated evidence query.

No public trace lookup endpoint exists in alpha2; exposing stored traces requires an access-control decision first.

## Context → loop → harness → graph: evidence-bound integration candidate (28 October 2026)

**Status: proposed architecture/acceptance mapping, not a runtime feature, release decision, or replacement authority.**
This candidate is anchored to integrated baseline `c5edb081dfefef022a3b8f7c25095930e83f1177` (PRs [#32](https://github.com/Subzteveo/Medical-AI/pull/32), [#33](https://github.com/Subzteveo/Medical-AI/pull/33), [#34](https://github.com/Subzteveo/Medical-AI/pull/34)). Existing `EvidenceAnswer`, `ExecutionTrace`, `CitationMapping`, `validate_output_provenance`, and the influence controller are the authoritative implementation. The terms **Prompt → Context → Loop → Harness → Graph** describe overlapping responsibilities, not a maturity ladder or a request to create five frameworks.

### One controlled transition path

```text
General, non-patient-specific question (intended purpose / access validation)
  -> deterministic plan (jurisdiction, source class, consequence, PHI boundaries)
  -> approved connector and original source version/record
  -> complete attributed passage + evidence unit
  -> extractive claim + exact-passage/provenance checks
  -> independent-of-model influence authority + output revalidation
  -> supported / withheld / unavailable answer state + existing execution trace
  -> read-only evidence/provenance graph inspection
  -> revision-bound external outcome check (not a medical influence grant)
  -> ACCEPT within exact measured scope | INVESTIGATE earliest observed gap | STOP
```

**Context graph.** The user question is ephemeral; the bounded context for a run is its `QueryPlan`, source identity, retrieved source/version and qualified passages. The existing claim/evidence/passage/source IDs and citation mappings already form a validated provenance graph. `validate_output_provenance` requires every displayed claim to have complete, internally consistent, extractive support. A graph view must be derived **only after** current `EvidenceAnswer` validation and point-of-use influence authorisation; it may not mint source authority or reveal withheld claims/passages. The audit store keeps trace metadata, not raw questions, abstracts or patient identifiers. An unobserved transition is **UNKNOWN**, never implied by a diagram.

**Workflow graph.** Runtime branching already exists for patient-specific input, missing regulator, retrieval failure, insufficiency, high consequence, denied influence and qualified answer. No LLM agent may bypass those branches, lower the consequence level, reinterpret a regulatory question, self-approve a citation or change a terminal withheld status. Multi-agent execution is **not implemented or authorised** by this mapping. A future specialist agent may suggest only a typed, reviewable revision in an offline development task; the controller, CI, source records, independent reviewer and human owner remain separately responsible for authority, acceptance and release.

**Correction loop.** For every demonstrated defect, bind (1) user outcome and baseline commit, (2) original source/response digest or reproducible synthetic fixture, (3) observed trace and first divergence, (4) minimal code or policy correction, (5) adverse negative controls, (6) candidate commit and exact-head deterministic/browser evidence, and (7) human acceptance or explicit unresolved hold. Then return to the **same** intended outcome. Stop on repeat failure, missing source authority, ambiguous impact, unavailable independent review, or changed scope. Do not autonomously retry blocked patient-specific, regulatory or high-consequence requests with weaker sources.

**PR #32 → #33 → #34 as an actual loop.** #32 restored registry field attribution. #33 restored full PubMed abstract and study-context preservation but exposed the conservative 'interactions' withholding. #34 reproduced the original XML trace, restricted the non-drug exception, then fixed a newly discovered unsafe statistical suffix match after eight failing tests. These were successive **human-reviewed engineering revisions**, not a single self-improving deployed agent. Their passing checks establish scoped evidence fidelity, not semantic clinical truth or future correctness.

**Handoff into Outcome Alignment.** The external evaluator receives only project goal/actor, exact baseline and candidate SHA, test IDs and results, source-digest references, known failures, and independent reviewer observations. It does **not** receive unredacted source abstracts, patient data, model-inferred clinical conclusions or a self-awarded PASS. The evaluator can conclude `ACHIEVED_OBSERVED` solely for a specifically measured **engineering/research-user** outcome, otherwise `PARTIAL`, `NOT_ESTABLISHED`, or `BLOCKED`. An OA conclusion cannot mutate `EvidenceAnswer`, influence-controller state, repository release status, or the regulatory intended-use boundary.

### Guardrails and non-implementation

This change adds documentation of an existing trace/provenance mapping and a proposed outcome handoff only. It does **not** add an orchestration dependency, graph database, second authority store, model-agent executor, new endpoint, background loop, telemetry feed, clinical capability, public pilot or deployment. The current trace summarizes states rather than proving every internal stage occurred: a future runtime transition log would require its own privacy/security and negative-case review before implementation. Continue using `docs/INTENDED_USE.md`, the original influence policies, product acceptance checks, exact-head CI and human governance as the controlling sources.
