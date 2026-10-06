# Release Readiness — remediation candidate

## Decision

- Internal engineering development: **GO**
- Public/external medical release: **NO-GO**
- Commercial/public sale: **not authorised; pricing and public-access plan deferred**
- Deployment/distribution: **not authorised / not performed**

## Why the canonical alpha2 evidence was reopened

The 25 September 2026 ultrareview reproduced critical failures in high-consequence gating, claim-level gating, retraction handling, registry-efficacy handling and patient/identifier detection. The original alpha2 `22/22` suite therefore did not establish the safety claims it was being used to support.

A remediation regression suite has since been added and passes in the current working environment, but this does not itself establish release safety.

## Still blocking later release

- live network validation of the exact remediation candidate;
- clinically reviewed retrieval benchmark and ≥98% authoritative-source recall@k target;
- release-scale citation-entailment benchmark;
- broad medical safety suite and zero observed critical-failure evidence;
- high-consequence authoritative source path + genuinely independent second verifier;
- TGA/PBS and Australian terminology integrations where applicable;
- product-specific TGA/intended-purpose assessment before public/commercial distribution;
- robust PHI intake/routing + privacy operational validation;
- deployment-bound verification of the invitation access configuration, secret custody, TLS/origin exposure and account lifecycle; application-level access control is implemented in engineering candidate `523ab64fd180ab7550c8565dae1cb366c506f159` but is not deployed or release-approved;
- real browser/accessibility verification;
- production monitoring/rollback exercises;
- verified GitHub/revision provenance and fresh-environment install evidence.

## Issue #5: release assessment and decision record

**Record date:** 6 October 2026, Australia/Darwin
**Status:** assessment and approval incomplete; public/commercial release **NO-GO**
**Related issue:** [Issue #5](https://github.com/Subzteveo/Medical-AI/issues/5)

This section records decisions, unresolved conditions and the evidence needed to resolve them.
It does not perform a legal assessment, appoint an adviser, grant release approval or
change the intended purpose. Merging this documentation does not authorize release.
The decision above remains in force until the assessment and approval are complete.

### Existing evidence and document owners

| Record | What it owns | Limit |
| --- | --- | --- |
| [Intended use](INTENDED_USE.md) | Developer-stated purpose, users and excluded uses | Not an approved assessment of a specific release |
| [Product north star](../project_docs/NORTH_STAR.md) | Long-term direction and user modes | Future ambition does not expand current scope |
| [README](../README.md) | Project identity and engineering/release boundary | Passing engineering checks is not release approval |
| [Project status](../project_docs/STATUS.md) | Development checkpoint and remaining evidence gaps | Checkpoint is not a release assessment |
| [Known limitations](KNOWN_LIMITATIONS.md) | Bounded capability and verification limitations | Historical candidate statements need release-revision reconciliation |
| [Privacy architecture](PRIVACY_ARCHITECTURE.md) | Engineering privacy design | Not a user-facing privacy notice or proof of operational compliance |
| [UI source](../src/medical_ai/static/index.html) | Current user-facing wording and available controls | Static inspection does not verify deployed behavior |
| [Release notes](../RELEASE_NOTES.md) | Historical remediation candidate changes | Not current release authorization |
| [Validation plan](VALIDATION_PLAN.md) | Planned validation | Planned checks are not executed evidence |

`INTENDED_USE.md` retains ownership of the purpose statement. This release-readiness
record owns the assessment references, unresolved conditions and final disposition.
Do not create a second competing intended-purpose statement here.

### Operating boundary decisions — 6 October 2026

Steven Lees has supplied: individual operator **Steven Lees**, proposed **Australian
hosting**, and **invited adults in Australia**, for general education/research with
no patient-identifying data or patient-specific care. The five audience groups,
invitation-only access and 1 November target remain as recorded. These decisions
are planning scope, not release approval or evidence of configured hosting.

The [operating boundary and professional review brief](PILOT_OPERATING_BOUNDARY_AND_REVIEW_BRIEF.md)
records those answers, binds the updated source candidate to `a12567dedb5fa70c11ff757f7ff7bd0a74aa059b`,
identifies operational gaps and prepares a quote enquiry for qualified Australian
review. Provider selection, overseas data-flow review, appointment, fees, professional
findings and release disposition remain unresolved. No outreach or paid engagement
has been performed by this documentation change.

### Missing decisions

The audience, access model and target date supplied by Steven Lees on 6 October
2026 are recorded in the [frozen candidate assessment](PILOT_CANDIDATE_ASSESSMENT.md).
That assessment binds source revision, capability mapping and preliminary regulatory
findings; it is not final professional sign-off. Every remaining unresolved field
below remains **UNRESOLVED**. Proposed action owners are
coordination suggestions, not evidence that someone has accepted the task.

| Decision | Current evidence/state | Evidence required before disposition | Proposed action owner |
| --- | --- | --- | --- |
| Assessed release identity | Historical assessment at `197134ba22510f902c033f55d39ed33c5af22857`; updated review brief binds `a12567dedb5fa70c11ff757f7ff7bd0a74aa059b`; final artifact/configuration and approval absent | Exact commit, package identity/hash where applicable, assessed feature list and evidence links | Maintainer prepares; Steven Lees confirms scope |
| Purpose versus actual capabilities | Developer statement mapped to frozen source candidate in linked assessment; operational/clinical validation incomplete | Link each intended function and excluded use to actual UI/API behavior and limitations at the assessed revision | Maintainer prepares; Steven Lees reviews |
| Audience and distribution | Five audience groups; invitation-only adults in Australia, general education/research, no patient-identifying data or patient-specific care; operator Steven Lees; terms/duration/cap and implementation evidence unresolved | Explicit users, patient/public-access inclusion or exclusion, access controls, geography, distribution channel and pricing/public-access decision | Steven Lees |
| Assessment date boundary | Target pilot date 1 November 2026; preliminary assessment 6 October 2026; pre-supply refresh and approval required | Planned release date/window, assessment date and rules effective on that date; refresh trigger if date or scope changes | Steven Lees supplies dates; assessor reviews |
| Australian regulatory position | Fresh primary-source preliminary assessment linked above; final qualified product-specific determination unresolved | Dated product-specific assessment, primary-source links/access dates, reasoning, reviewer identity/role and unresolved conditions | Steven Lees arranges appropriately qualified review |
| November amendment applicability | Authorised instrument commencement, amended criteria and earlier-build application inspected in linked assessment; product exemption not established | Verify the cited instrument/current guidance and explain applicability to the assessed purpose and release date; record pre/post-commencement treatment if relevant | Assessor, once appointed |
| Advice required | Product-specific advice recommended; engagement and questions unresolved | Advice questions, appointed adviser/reviewer, evidence location, outcomes and conditions; keep confidential advice out of public repository text | Steven Lees |
| Claims and notice alignment | Core documents broadly agree; UI contains historical “Alpha2” wording; no completed surface comparison established | Compare UI, README, intended use, release notes, privacy notice and proposed marketing against the determined boundary; link fixes or explicitly mark absent surfaces | Maintainer prepares; Steven Lees approves wording |
| Final disposition | Public/commercial release NO-GO; no release approval recorded | Dated Steven Lees approval or continued NO-GO, exact assessed revision, permitted audience/distribution, evidence references and all remaining conditions | Steven Lees |

The legal statements in the existing intended-use document remain historical
repository material. Fresh primary-source findings and their limits are recorded
in the linked candidate assessment; neither record establishes an exemption or
final regulatory classification.


### Engineering delta: application-level invitation gate

Engineering candidate `523ab64fd180ab7550c8565dae1cb366c506f159` implements the server-side access boundary that
was absent from the frozen Issue #5 candidate. The implementation is revision-bound
to that code candidate and is not retroactive evidence for the earlier assessed SHA.

Implemented/inspected in that candidate:

- deny-by-default protected evidence API when pilot access configuration is missing;
- explicit participant allowlist with stable participant ID, credential ID, token
  digest, expiry and revocation state;
- HMAC-signed HTTP-only browser sessions with bounded lifetime and secure-cookie
  default;
- per-request expiry/revocation re-evaluation, so an existing session is invalidated
  when its participant becomes inactive;
- direct evidence API and API-documentation protection independent of the browser UI;
- request models reject extra fields so a client cannot inject or override participant
  identity through the evidence-query body;
- `student`, `clinician` and `researcher` remain presentation modes, not verified
  professional identities; and
- raw invite tokens are not passed into the evidence engine or SQLite execution trace.

Still unresolved before any external pilot: deploy the exact candidate behind TLS;
supply runtime secrets/allowlist through an approved secret-management path; verify
direct-origin exposure and all configured routes in the deployed environment; define
invite issuance/offboarding ownership and retention; review infrastructure/proxy logs
for credential or query leakage; decide whether tenancy/rate limiting are required;
and complete all separate regulatory, privacy, claims, live-source, clinical and
release-approval gates.

A passing engineering suite may support this access-control delta only. It cannot
change the current **NO-GO** disposition by itself.

### Closure rule

Issue #5 remains open. A documentation PR or a green test run cannot close it.
Before proposing closure, record:

1. The exact assessed revision and capability/purpose mapping.
2. The approved audience and distribution boundary, including patient/public access.
3. A dated assessment with primary-source references, reviewer identity/role, applicable
   release-date rules and treatment of the November amendment where relevant.
4. Any required professional advice, its outcome and outstanding conditions.
5. A completed claims/notice comparison, with corrections linked to the assessed revision.
6. Steven Lees's dated disposition and the evidence supporting it.

Keep engineering results separate from clinical, privacy and regulatory findings.
If any required assessment or approval remains incomplete, public/commercial release
stays **NO-GO**. Do not treat an empty field, unavailable advice, or an unexecuted
check as a pass. Scope, revision, audience or release-date changes require review
of the affected assessment and claims before any release decision.

Issue #5 resolution is only one release gate. Other blockers above still require
separate evidence and authorization; closing this issue alone cannot authorize launch.

### Smallest next action

Select a reviewer and request a scoped quote using the
[professional review brief](PILOT_OPERATING_BOUNDARY_AND_REVIEW_BRIEF.md).
Supply the selected hosting/data-flow configuration for review before any external
pilot; the source candidate has an access gate but no observed deployment.

No external pilot, public/commercial release or deployment is authorised.
