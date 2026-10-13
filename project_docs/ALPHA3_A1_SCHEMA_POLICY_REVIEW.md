# Alpha3 A1 — Canonical Schemas, Authority Policies and Status Claims (Review Contract)

**Authoring date:** 11 October 2026 (Australia/Darwin)  
**Baseline:** `13fadd41e628ff60de2cdfff933b3e2be19f1327` (immutable `main` inspection revision)  
**Disposition:** **DOCUMENTED / CANDIDATE FOR HUMAN REVIEW**, NOT IMPLEMENTED, NOT TESTED, NOT VALIDATED, NOT APPROVED FOR MEDICAL INFLUENCE.  
**Gate:** G0 required-PR and required-check enforcement must be observed before application/runtime A1 files change.  
**Upstream contract:** Owner-approved *Medical AI — Alpha3 Tranche A Implementation Contract*, 11 October 2026. This file refines A1 only; it does not supersede the full Tranche A contract.

## 1. Non-negotiable scope

The existing v0.2 influence kernel and PR #21 type-safety protections are the foundation, not a replacement target. **A model is never evidence.** Passing verification and a declared `APPROVED` flag do not authorize an object to influence a medical proposition. Every production-capable influence path must resolve independently sourced, current authority.

Separate dimensions:

1. **EVIDENCE_AUTHORITY**: admissibility for exact evidence object × claim × context and operation.
2. **INFORMATION_HANDLING**: component × information classification × operation × purpose × environment.
3. **DATA_PLANE_TRANSITION**: source plane × target plane × information classification × operation × purpose × component.
4. **STATUS_AUTHORITY**: subject × status × scope × exact revision, using the evidence appropriate to that status.

Status authority is independent; it is only a medical-influence dependency where validated component/approval/release status is actually required by an immutable policy path. A user caller cannot omit mandatory dimensions.

In this PR **there are no modifications to `src/`, `policies/`, `tests/`, CI, API, renderer, connectors or active policy**. Candidate examples live in `project_docs/` only and must be compiled into validated, enforced runtime policy in a future authorized A1 implementation PR.

## 2. Observed starting structures

At baseline: `src/medical_ai/schemas.py` defines `SourceRecord`, `Passage`, `EvidenceUnit`, `ClaimRecord`, `InfluenceSubject`, `DataPlaneTransition`, `InfluenceRequest`, `InfluenceAuthorization`, `InfluenceDecision`, `DependencyEdge`, `AuthorizedClaimView`, and `ExecutionTrace`. `src/medical_ai/influence.py` owns the influence capability; `renderer.py` validates it. `source_policy.py` remains source/query-class oriented; `policy_loader.py` returns untyped dicts; `engine.py` currently materializes broad evidence-authority and validation flags. `pyproject.toml` pins strict Pyright for the existing influence path.

**Preserve all existing evidence and pilot routing limits during A1.** A1 contracts must not change public clinical scope or permit unverified medical claims.

## 3. Closed canonical types

All below are schema **requirements**, not executable Python. Use Pydantic v2 with `extra="forbid"`, closed enums, checked nonblank IDs, timezone-aware timestamps, immutable decision/event payloads (`frozen=True`), and exhaustive parsing at trust boundaries. Runtime snapshots are never trusted merely because they deserialize.

| Canonical type | Minimum required fields | Contract check |
|---|---|---|
| `SourceVersion` | `source_version_id`, `source_id`, `record_id`, `content_or_version_digest`, `retrieved_at`, `jurisdiction`, `retraction_state`, `provenance_ref`, `trace_ref`; optional effective/supersession refs | Version is immutable and resolvable; unknown retraction/supersession blocks freshness-dependent permission |
| `ClaimEvidenceLink` | `link_id`, `claim_id`, `evidence_id`, `source_version_id`, nonempty `passage_refs`, closed `claim_type`, `jurisdiction`, `population_context`, `required_authority_class`, `applicability`, `verification_ref`, `evidence_authority_decision_ref`, `dependency_refs`, `result`, `trace_ref` | No link authority without version, passage, context and independently resolved decision |
| `TypedJudgment` | `judgment_id`, `judgment_type`, `subject_refs`, `input_state_hash`, bounded result, `method_id`, `created_at`, `trace_ref` | Semantic evidence input only; confidence cannot grant permission |
| `EvidenceAuthorityDecision` | shared decision envelope + `claim_evidence_link_ref`, `source_version_ref`, `claim_type`, `context_ref`, `permitted_operations` | Claim-specific, not a global source trust bit |
| `InformationHandlingDecision` | envelope + `component_ref`, `information_class`, `operation`, `purpose`, `environment` | Evidence admission cannot grant information access |
| `DataPlaneTransitionDecision` | envelope + `from_plane`, `to_plane`, `information_class`, `operation`, `purpose`, `component_ref` | Same-plane operations also require explicit policy; clinical/research → evidence denied in Tranche A |
| `StatusClaimRecord` | `status_claim_id`, `subject_ref`, `status`, `scope`, `revision_ref`, `authority_type`, `authority_ref`, `evidence_refs`, `asserted_at`, `observed_at`, `result`, `reason_codes`, `trace_ref`; optional recheck expiry | Subject, scope and revision must match external authority; model/issue narrative alone insufficient |
| `AuthorityPolicyBundle` | `schema_version`, `policy_id`, `revision`, `effective_at`, `default_decision=DENY`, `rules`, `policy_digest` computed over canonical content | Unknown key/type/enum, ambiguous overlap, duplicate rule IDs, missing digest or unsupported policy version → DENY / reject load |

### Shared immutable decision envelope

Require: `decision_id`, `subject_ref`, `scope`, `policy_ref`, `policy_digest`, `input_state_hash`, `authority_source_ref`, `evidence_refs[]`, `observed_at`, `result (ALLOW|DENY)`, `reason_codes[]`, `trace_ref`. A result of `ALLOW` must have an independently verifiable authority source and all policy-required evidence. Never construct `ALLOW` from a prefilled model attribute or an empty reasons list.

`UNASSESSED → ALLOW|DENY`; previous `ALLOW → STALE|REVOKED`. Do not edit a denied/stale/revoked record back to ALLOW. Re-evaluate under a new decision ID. Historical records remain append-only.

### Classification migration is denial-preserving

New `InformationClassification` (closed): `PUBLIC_EVIDENCE`, `IDENTIFIABLE_HEALTH_INFORMATION`, `DEIDENTIFIED_HEALTH_INFORMATION`, `RESTRICTED_RESEARCH_DATA`, `UNKNOWN`. Map legacy `PUBLIC` and `PHI` only through verified boundary adapters; legacy `SENSITIVE` has no assumed safe mapping and becomes `UNKNOWN` → deny. De-identification requires separately authorized evaluation; absence of obvious identifiers is not proof. Preserve the old types at existing public boundaries until a tested migration can be shipped.

`DataPlane` remains the closed four-value `EVIDENCE`, `TERMINOLOGY`, `CLINICAL`, `RESEARCH` enum; do not turn it into a mutable authority object.

### Status vocabulary is explicit

`DOCUMENTED`, `IMPLEMENTED`, `TESTED`, `PASSED`, `VALIDATED`, `VERIFIED`, `APPROVED`, `MERGED`, `RELEASE_BLOCKED`, `RELEASE_READY`, `DEFERRED`, `SUPERSEDED`, `DEPRECATED`, optionally `PROPOSED`. No status implies any other. `UNAUTHORIZED` and `STALE` are **evaluation outcomes**, not evidence of an approved new status.

## 4. Executable policy contract for subsequent gated implementation

Proposed packaged policy files (none created in this documentation-only PR):

- `src/medical_ai/policies/evidence-authority-v0.2.yaml`
- `src/medical_ai/policies/information-handling-v0.2.yaml`
- `src/medical_ai/policies/data-plane-transitions-v0.2.yaml`
- `src/medical_ai/policies/status-claims-v0.1.yaml`
- `src/medical_ai/policies/influence-aggregation-v0.2.yaml`

Mirror exact bytes under `policies/` and verify parity and source hashes. Parse with an explicitly versioned closed schema in `authority_policy.py` or `policy_loader.py`: **YAML decode → strict schema validation → immutable compiled rule registry → matching scoped decision**. Never pass `dict[str, Any]` into the influence core. Each rule needs nonempty `rule_id`, complete scope tuple, explicit ALLOW/DENY and evidence requirement. A wildcard must not silently override a narrower prohibition; define collisions as DENY rather than sort-dependent allow. Unknown policy or operation is DENY.

Candidate non-runtime policy review cases live in [A1 policy cases](ALPHA3_A1_POLICY_REVIEW_CASES.md); that document is **not a loaded policy** and cannot authorize any medical output.

### Evidence authority

Match `claim_type × jurisdiction × population × source_class × source_version × freshness/retraction × operation × consequence`. For Tranche A, current PubMed extractive literature and ClinicalTrials registry **registration facts** are only candidates; no source class alone grants ALLOW. A trial registry sponsor narrative is DENY for treatment efficacy, and PubMed cannot establish Australian drug approval. Retraction/supersession/unknown required freshness blocks current-effect claims. High-consequence synthesis remains disabled.

### Information handling

Match `component × information_class × operation × purpose × environment`. Public evidence can be processed only by named, authorized connector/workflow operations; every identifiable/deidentified/restricted clinical/research class is deny-by-default until separately authorized. Authorization to retrieve PUBLIC_EVIDENCE never authorizes handling an identifiable patient query on a public connector.

### Data-plane transitions

Match `from_plane × to_plane × information_class × operation × purpose × component`. Default DENY, including same-plane unknown operations. Explicitly considered, bounded `EVIDENCE → EVIDENCE` public retrieval/render may pass only when its operation is in the policy and all other required gates pass. `CLINICAL/RESEARCH → EVIDENCE` is DENY for efficacy/recommendation promotion. Cross-plane admission cannot be added by a model.

### Influence aggregation

Trusted immutable policy, not the caller, resolves each required authority dimension. `ACTIVE` authorization requires current matching decision refs, exact claim/link snapshots, mandatory verification, provenance, status/revision dependencies where applicable, validation, safety, monitoring, and no blocking invalidation. A missing optional dimension only stays optional if immutable policy establishes that fact. Rendering and API JSON must derive from the same authorized projection.

## 5. Status-claim authority rules

| Claim | Required evidence | Explicitly insufficient |
|---|---|---|
| `DOCUMENTED` | identified current document/spec and version | model assertion |
| `IMPLEMENTED` | inspected code/executable artefact at exact revision | project spec, issue closure |
| `TESTED` | test execution evidence bound to revision/configuration | presence of test files |
| `PASSED` | successful check run for exact commit/configuration | a run on prior commit |
| `VALIDATED` | protocol + criteria + executed appropriate validation and passing result | successful unit tests alone |
| `VERIFIED` | object-appropriate independent verification event | chat summary |
| `APPROVED` | designated human/policy authority event, exact scope/revision | assistant advice, merged PR |
| `MERGED` | repository merge event and merge-commit ref | a PR described as complete |
| `RELEASE_READY` | every current mandatory release gate + required designated authority | passing CI |
| `RELEASE_BLOCKED` | at least one verified current required release gate unresolved/denied | unevidenced blocker narrative |
| `DEFERRED` | explicit recorded scope/roadmap decision | feature missing |
| `SUPERSEDED` | identified successor/explicit supersession event | newer date alone |
| `DEPRECATED` | authorized deprecation scope/date | unverified document text |

Approval is by a designated human or policy role and bound to the **specific action/scope**; an approval to proceed with engineering work is not a medical/clinical release approval. Historical `PASSED` for commit A is retained when B appears, but never becomes `PASSED` for B. Status validity is computed from underlying evidence; never from an autonomous status label. Contradictory active records trigger stale/unauthorized reconciliation, not “latest wins.” Store append-only status events and reconstruct projection in later A2/A3 work.

## 6. Schema and policy merge prerequisites

1. G0 read-back shows **required PR + required exact-head `source-and-tests`** and no force-push/deletion bypass; designated human reviewer remains effective. This is **not satisfied at authoring**.
2. Full, reviewed Tranche A contract is available as a revisioned repository document; this A1 review spec cannot substitute for it.
3. Every A1 runtime enum/schema has strict `extra=forbid`, immutable decision semantics, explicit serialization and denial-preserving migration.
4. Policy unit tests reject missing/invalid fields, duplicate/ambiguous rules, unknown information classes/purposes/operations, absent source version, bad actor/authority refs, stale revision, and malformed timestamps.
5. No test or application call can grant authority through a direct `InfluenceSubject(APPROVED)` absent independently referenced evaluation.
6. No runtime default `ALLOW`; a policy compile/parse error fails closed; check policy hash and mirrored policy parity in CI.
7. The existing PR #21 type-safety source guard, `AuthorizedClaimView` restriction, API behavior, existing deterministic suite and the blocked Alpha3 fixture outcomes must be preserved.
8. Exactly scoped PR-head CI evidence and human review before merge. A1 alone is neither `IMPLEMENTED` nor `VALIDATED` for the full four-authority kernel.

## 7. Explicitly deferred to A2–A4

A1 does not independently resolve authority in `engine.py`, modify the renderer, persist revocations, add graph traversals, install TypeSafe/Jev, validate real clinical safety, broaden patient-specific functionality, or authorize deployment. A2 wires claim-specific decisions and status policy, A3 adds transactional audit/revocation plus full API projection, and A4 supplies adversarial assurance.

**Reviewer decision requested:** approve or request changes on this exact typed-contract/policy matrix only. Do not mark code IMPLEMENTED, policy ENFORCED or feature APPROVED from this document.
