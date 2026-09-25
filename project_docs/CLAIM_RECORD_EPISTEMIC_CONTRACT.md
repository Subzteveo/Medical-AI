# ClaimRecord Epistemic Contract

## Purpose

A `ClaimRecord` is the minimum auditable evidence state required before a substantive medical claim may influence a user-visible answer.

The contract exists to enforce the governing principle:

> **A model is never evidence.**

A language model may help retrieve, classify, extract, compare, explain or synthesize evidence, but it must not be allowed to create an unsupported medical fact by assertion.

## Influence rule

A medical claim may influence a user-visible answer only when the system can establish all required elements for that claim class:

`Evidence AND Provenance AND Applicability AND Verification AND Safety`

Where operational release policy additionally requires validated components, monitored versions and approved data routes, those gates remain separate mandatory controls.

Failure of a mandatory gate must produce a qualified or abstained state rather than silent completion from model memory.

## Mandatory claim state

Every substantive medical `ClaimRecord` must be able to represent:

- `claim_id` — stable identifier for the claim within the execution;
- `claim_text` — the exact normalized proposition being evaluated;
- `claim_type` — e.g. regulatory status, contraindication, recommendation, efficacy, safety signal, terminology, trial-registration fact;
- `consequence_class` — ordinary or applicable high-consequence category;
- `jurisdiction` — explicit where jurisdiction affects authority or applicability;
- `population` / `applicability` — direct, partial, indirect, mismatch or unknown as appropriate;
- `source_authority_requirement` — the evidence/source class required for this claim type;
- `evidence_refs` — identifiers for the evidence objects allowed to support the claim;
- `source_passages` — recoverable passages/sections supporting the claim where available;
- `source_versions` / effective dates — sufficient to assess currency and supersession;
- `retrieval_timestamp` — when the evidence was obtained;
- `freshness_status` — current, potentially outdated, superseded, unknown or equivalent explicit state;
- `conflict_status` — concordant, mixed, conflicting, unknown or not applicable;
- `verification_status` — whether claim-to-evidence support has passed the required verification path;
- `safety_gate_status` — including independent high-consequence verification where required;
- `influence_status` — supported, qualified, abstained or rejected;
- `failure_reasons` — explicit machine-readable reason(s) when influence is denied or qualified;
- `trace_ref` — link to the relevant execution/provenance trace.

The persisted implementation schema may evolve, but these epistemic meanings must remain reconstructable.

## Source authority is claim-specific

There is no universal source ranking.

The system must determine admissible source classes from the claim being evaluated. Examples:

- Australian regulatory status or current product information -> applicable TGA authority;
- Australian medicine subsidy -> PBS;
- clinical recommendation -> applicable current recognised guideline;
- treatment efficacy -> appropriate guideline/systematic review/primary evidence according to the question;
- trial-registration facts -> trial registry;
- terminology -> applicable terminology authority.

A source suitable for one claim class must not automatically receive authority for another.

In particular:

- a ClinicalTrials.gov record does not by itself establish treatment efficacy;
- a patient record does not become generalisable medical evidence;
- a search result, model answer or snippet may assist discovery but does not establish a medical fact.

## Evidence admissibility and rejection

The system must retain enough state to explain not only why evidence was accepted, but why retrieved material was prevented from influencing a claim.

Rejection/qualification reasons include at least:

- `NO_AUTHORITATIVE_SOURCE`;
- `SOURCE_OUTDATED`;
- retracted source;
- superseded source;
- inappropriate evidence class;
- `POPULATION_MISMATCH`;
- `JURISDICTION_UNCLEAR` or jurisdiction mismatch;
- `PROVENANCE_INCOMPLETE`;
- material evidence conflict;
- source unavailable;
- high-consequence verification failure;
- outside validated capability.

The implementation may use a broader taxonomy, but these meanings must not be collapsed into a generic low-confidence state.

## High-consequence claims

Claims involving areas such as dose, contraindications, interactions, pregnancy, paediatrics, renal/hepatic adjustment, anticoagulation, allergy, emergency care, toxicology, diagnostic exclusion, treatment initiation/discontinuation and cancer therapy require their dedicated fail-closed verification path.

A high-consequence claim must not receive `supported` influence status unless all required evidence and independent verification conditions for that claim class have passed.

Failure must produce an explicit abstention/failure state such as `HIGH_CONSEQUENCE_VERIFICATION_FAILED` rather than a best-effort model completion.

## Model authority boundaries

A model may propose or derive fields for subsequent verification, but it must never be treated as the truth source for:

- whether the underlying medical fact is true;
- whether a source is current when that requires authoritative version/supersession data;
- whether the source is authoritative for the claim unless policy rules verify that classification;
- regulatory or subsidy status;
- citation support/entailment without verification;
- jurisdictional applicability without verified source metadata/rules;
- high-consequence approval state;
- final evidence certainty solely from model self-confidence.

Model-generated classifications must be distinguishable from source-derived or deterministically verified state.

## Verification expectations

The system must be able to test at least:

1. the expected authoritative source was retrieved when one exists;
2. the source class is admissible for the claim;
3. the extracted passage actually supports the proposition;
4. material qualifications were preserved;
5. jurisdiction and population applicability were not silently broadened;
6. retracted or superseded evidence cannot provide current support;
7. conflicting authoritative evidence is represented rather than averaged away;
8. high-consequence verification cannot be bypassed;
9. an unsupported claim cannot escape into user-visible output.

## User-facing relationship

`ClaimRecord` is mandatory internal infrastructure but should be progressively disclosed rather than dumped into every answer.

Intended product layers:

1. **Answer** — concise, readable and appropriately qualified.
2. **Evidence inspection** — claims, citations, authority, jurisdiction, applicability, freshness, disagreement and verification state.
3. **Audit trail** — exact passages, rejected sources, retrieval path, component/configuration versions, verifier outcomes and `ExecutionTrace`.

## Change control

Changes to this contract are consequential architecture/safety changes. They require coordinated updates to affected schemas, policies, tests, evaluation benchmarks and user-visible semantics.

Do not weaken a ClaimRecord requirement merely to make a failing implementation or benchmark pass. Change the accepted contract first, document why, then update verification.
