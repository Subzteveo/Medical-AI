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
- authentication/access controls for any shared/public service;
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

### Missing decisions

The audience, access model and target date supplied by Steven Lees on 6 October
2026 are recorded in the [frozen candidate assessment](PILOT_CANDIDATE_ASSESSMENT.md).
That assessment binds source revision, capability mapping and preliminary regulatory
findings; it is not final professional sign-off. Every remaining unresolved field
below remains **UNRESOLVED**. Proposed action owners are
coordination suggestions, not evidence that someone has accepted the task.

| Decision | Current evidence/state | Evidence required before disposition | Proposed action owner |
| --- | --- | --- | --- |
| Assessed release identity | Source candidate `197134ba22510f902c033f55d39ed33c5af22857` assessed; final artifact/configuration and release approval absent | Exact commit, package identity/hash where applicable, assessed feature list and evidence links | Maintainer prepares; Steven Lees confirms scope |
| Purpose versus actual capabilities | Developer statement mapped to frozen source candidate in linked assessment; operational/clinical validation incomplete | Link each intended function and excluded use to actual UI/API behavior and limitations at the assessed revision | Maintainer prepares; Steven Lees reviews |
| Audience and distribution | Proposed medical students, GPs, health professionals, universities and researchers; invitation-only pilot; geography, patient/public boundary approval and terms unresolved | Explicit users, patient/public-access inclusion or exclusion, access controls, geography, distribution channel and pricing/public-access decision | Steven Lees |
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

Steven Lees resolves the remaining participant/operator/hosting boundaries and
arranges qualified Australian review of the [frozen candidate assessment](PILOT_CANDIDATE_ASSESSMENT.md).
The maintainer supplies an enforceable invitation/access design and its evidence.
No external pilot, public/commercial release or deployment is authorised.
