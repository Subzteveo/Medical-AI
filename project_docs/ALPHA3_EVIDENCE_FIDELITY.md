# Alpha3 — Evidence Fidelity

## Milestone purpose

Alpha3 must establish that Medical AI can construct the **correct evidence state** for a medical question before meaningful free-form medical synthesis is allowed into the answer path.

Retrieving a relevant document is necessary but insufficient.

The milestone must demonstrate the chain:

`Question -> claim/intention classification -> authoritative retrieval -> authority selection -> source admissibility/rejection -> evidence extraction -> ClaimRecord -> claim/evidence verification -> applicability/conflict/freshness checks -> safety gate -> supported/qualified/abstained state`

## Why this milestone exists

A retrieval system can achieve good recall while still exposing unsafe evidence state. For example, it may retrieve the right regulator or guideline alongside a superseded recommendation, retracted paper, irrelevant population, wrong jurisdiction or registry narrative and still count the case as a retrieval success.

Alpha3 therefore evaluates whether the system correctly decides **what may influence a claim and why**, not merely whether a relevant source appeared somewhere in the result set.

## Scope

Alpha3 covers evidence-state construction and gating for the validated research/education scope.

It includes:

- natural-language query normalization/planning;
- claim/intention classification sufficient for authority selection;
- authoritative retrieval;
- source-class and jurisdiction handling;
- source admissibility and explicit rejection;
- provenance-preserving evidence extraction;
- ClaimRecord construction;
- claim-to-evidence verification;
- freshness, supersession and retraction handling;
- population/applicability handling;
- evidence conflict representation;
- high-consequence fail-closed routing;
- abstention/failure taxonomy;
- revision-bound evaluation evidence;
- controlled live-source verification for approved external sources.

## Explicit non-goals

Alpha3 does not establish:

- public/commercial medical release readiness;
- patient-specific clinical decision support;
- autonomous diagnosis or treatment recommendation;
- prescribing;
- autonomous emergency triage;
- medical-device authorization;
- a patient/public product mode;
- EHR write-back;
- broad generative medical synthesis before evidence-state gates are demonstrated.

## Benchmark case contract

A gold case should record, as applicable:

- question text;
- intended claim type(s);
- expected authoritative source class;
- expected authoritative source(s) or acceptable source set where appropriate;
- jurisdiction expectation;
- population/applicability expectation;
- freshness/supersession requirement;
- expected admissible evidence;
- known inadmissible or misleading evidence classes;
- expected high-consequence classification;
- expected conflict state;
- expected terminal influence state (`supported`, `qualified`, `abstained`, `rejected`);
- expected failure code(s) when not supported;
- reviewer identity/role and review date where human review is required.

A benchmark must not silently encode one publication identifier as the only acceptable answer where multiple authoritative sources are valid.

## Core evaluation dimensions

### Retrieval

- authoritative-source recall@k;
- rank of first authoritative source;
- natural-language query translation/normalization behavior;
- live-source availability and failure handling.

Current engineering target remains approximately **>=98% authoritative-source recall@k** on an appropriate curated benchmark where an authoritative source exists. This is an engineering acceptance target, not a regulatory threshold.

### Authority and admissibility

Measure whether the system:

- selects the correct authority for the claim type;
- avoids using a source outside its legitimate claim class;
- rejects inadmissible retrieved material;
- distinguishes discovery material from evidence allowed to support a claim.

Candidate metrics include:

- authority-selection correctness;
- authority-weighted precision;
- inadmissible-source contamination rate;
- rejected-source correctness.

### Evidence extraction and provenance

Measure whether the system:

- extracts the passage/section that actually supports the claim;
- preserves material qualifications;
- retains stable identifiers and version/effective-date information;
- can reconstruct claim -> evidence provenance.

Candidate metrics include:

- extraction fidelity;
- provenance completeness;
- citation correctness / claim-to-passage entailment.

Current engineering targets remain:

- >=99% citation correctness for ordinary factual claims in the applicable evaluation suite;
- 100% observed citation correctness for high-consequence release-suite claims.

### Freshness, retraction and supersession

Measure whether the system prevents invalid current support from:

- retracted publications;
- superseded guidelines;
- outdated regulatory information where freshness is material.

Candidate metrics include:

- retracted-source escape rate;
- superseded-source escape rate;
- freshness classification correctness.

### Jurisdiction and applicability

Measure:

- jurisdiction correctness;
- population/applicability correctness;
- refusal to silently generalize across mismatched populations or jurisdictions.

### Conflict

Measure whether materially conflicting authoritative evidence is represented explicitly rather than merged into an invented compromise or silently resolved by the model.

### Abstention and safety

Measure whether the workflow emits the correct explicit state when evidence requirements fail.

Important states include:

- `EVIDENCE_INSUFFICIENT`;
- `EVIDENCE_CONFLICTING`;
- `SOURCE_OUTDATED`;
- `POPULATION_MISMATCH`;
- `NO_AUTHORITATIVE_SOURCE`;
- `JURISDICTION_UNCLEAR`;
- `PROVENANCE_INCOMPLETE`;
- `HIGH_CONSEQUENCE_VERIFICATION_FAILED`;
- `OUTSIDE_VALIDATED_CAPABILITY`;
- `SOURCE_UNAVAILABLE`.

Candidate metrics include:

- abstention correctness;
- false-support rate;
- high-consequence gate bypass rate;
- unsupported-claim escape rate.

The release suite target remains **zero observed catastrophic/critical clinical-safety failures**. This does not imply zero underlying real-world risk.

## Live-source verification

Alpha3 should include revision-bound live tests for approved sources where network behavior is part of the claim being validated.

At minimum, the current planned live paths include:

- PubMed;
- ClinicalTrials.gov.

Live-source tests must remain distinguishable from deterministic regression tests so transient external/network failure is not misreported as deterministic application failure.

Each live result must record enough identity to reconstruct:

- repository commit;
- configuration/model versions where relevant;
- source/query;
- retrieval timestamp;
- observed result;
- assertion/postcondition;
- unavailable/blocked conditions.

## Required evidence before milestone completion

Alpha3 is not complete merely because benchmark code exists or a test command exits successfully.

Completion requires evidence that, for the accepted benchmark and exact revision:

1. the benchmark has appropriate clinical/research review for its intended claims;
2. retrieval performance has been measured rather than assumed;
3. claim-specific authority/admissibility behavior is exercised;
4. provenance and extraction fidelity are exercised;
5. retraction/supersession/freshness negative cases are exercised;
6. jurisdiction and population/applicability negative cases are exercised;
7. conflict and abstention behavior are exercised;
8. high-consequence gates fail closed under negative tests;
9. unsupported claims cannot reach user-visible influence in the validated path;
10. live external-source checks required by scope are bound to the exact revision/configuration;
11. failures and blocked checks remain visible rather than being averaged into a single score.

## Relationship to generative synthesis

Meaningful free-form medical synthesis should remain behind the ClaimRecord/evidence-verification boundary until this milestone has established the evidence-state behavior for the intended scope.

Passing deterministic unit tests alone does not authorize synthesis. Passing retrieval recall alone does not authorize synthesis.

## Change control

Changes to Alpha3 acceptance criteria, benchmark semantics or ClaimRecord requirements are consequential project changes. Update the canonical contract first, then update implementation/tests. Do not weaken the benchmark solely to obtain a green result.
