# Pilot operating boundary and professional review brief

**Decision record date:** 6 October 2026, Australia/Darwin

**Status:** operating decisions recorded; hosting implementation and professional
engagement incomplete. External pilot, public and commercial release remain **NO-GO**.

Related: [Issue #5](https://github.com/Subzteveo/Medical-AI/issues/5),
[release-readiness owner](RELEASE_READINESS.md),
[historical candidate assessment](PILOT_CANDIDATE_ASSESSMENT.md),
[intended-use owner](INTENDED_USE.md).

## Decisions supplied by Steven Lees

The following answers were supplied in this session on 6 October 2026. They define
planning scope, not permission to start the pilot or a legal determination.

| Boundary | Recorded decision | Remaining limit |
| --- | --- | --- |
| Operator | Steven Lees personally, as individual operator | Reviewer to assess operator/manufacturer/sponsor roles, liability and suitability; no company or university operator inferred |
| Hosting | Australian hosting for the proposed application and storage | Provider, exact regions, backups, telemetry, identity/secret services and support access not selected or verified |
| Participants | Invited adults in Australia | No patient-facing access, public registration, overseas participants or minors in this pilot plan |
| Audience | Medical students, GPs, health professionals, universities and researchers | Universities are participating institutions; accounts belong to named individuals, with institutional responsibilities still to be agreed |
| Activity | General education and research within existing intended use | No patient-specific care or patient-identifying data; no diagnosis, treatment selection, prescribing or triage expansion |
| Access | Invitation-only, using the implemented application gate | Deployment-bound enforcement, enrolment/offboarding, identity/age/location checks and credential custody remain unverified |
| Target | 1 November 2026 | Conditional target only; pilot duration, participant cap and final approval unresolved |

Australian hosting does **not** establish all-Australian processing. The current
connectors send normalised evidence-search queries to NCBI/PubMed and
ClinicalTrials.gov. API documentation also loads external Swagger assets by default.
Overseas processing, browser requests, logging and support access need an explicit
inventory and privacy review. No patient-identifying text is permitted; the heuristic
detector is not a guarantee that prohibited input cannot escape.

## Candidate and evidence handed to the reviewer

- Current source candidate: [`a12567dedb5fa70c11ff757f7ff7bd0a74aa059b`](https://github.com/Subzteveo/Medical-AI/tree/a12567dedb5fa70c11ff757f7ff7bd0a74aa059b).
- Git tree: `0ae57f90fc9b54b544278cf74660af3af81a739f`.
- This merge has the same tracked tree as reviewed access head
  `ec2a7b715f5e50fe0bce225489db0e9be9531291`; no runtime difference found.
- [PR #18](https://github.com/Subzteveo/Medical-AI/pull/18) and
  [exact-head CI](https://github.com/Subzteveo/Medical-AI/actions/runs/37407285666):
  135 deterministic tests passed, 81 checksums and 101 hygiene checks, compile/policy
  checks passed. Engineering evidence only.
- [API and access implementation](https://github.com/Subzteveo/Medical-AI/tree/a12567dedb5fa70c11ff757f7ff7bd0a74aa059b/src/medical_ai),
  [privacy architecture](PRIVACY_ARCHITECTURE.md),
  [harness limitations](ALPHA3_ENGINEERING_HARNESS.md).
- Historical assessment at `197134ba22510f902c033f55d39ed33c5af22857` predates access
  control and must not be presented as a final assessment of the new candidate.
  Conflict and population-mismatch handling remain blocked; live fidelity and
  clinical entailment remain unproven.
- No final package/container hash or deployment configuration exists in this brief.
  Freeze and review them before any release disposition. Later runtime changes
  require reconciliation of the affected advice and evidence.

## Proposed operating controls to be confirmed before implementation

Steven Lees is the accountable operator. The procedures below are proposals for
review, not evidence that operations are implemented or someone else appointed.

| Work item | Required record and acceptance evidence |
| --- | --- |
| Enrolment | Named participant, adult/Australian participation confirmation, agreed education/research purpose and notice/terms acknowledgement; keep identity records outside GitHub |
| Invitations | Secret-managed high-entropy tokens, named issuance custodian, expiry, participant/credential IDs and minimum necessary identity mapping |
| Offboarding | Revocation and credential rotation procedures; test both old Bearer token and existing browser session after change; institutional participant removal process |
| Hosting | Selected provider and Australian application/database/backup regions; complete processor/subprocessor and overseas-access inventory; TLS/origin/route tests |
| Data and retention | Inventory invitation/account records, queries, traces, network/proxy/security logs, cookies and support data; approve purpose, access, retention periods and deletion for each class |
| Accidental prohibited data | Approved no-PHI notice, intake/egress tests and incident/quarantine/deletion process; review infrastructure logging independently of SQLite trace behaviour |
| Operations | Named support/incident contact, suspension and rollback authority, quota/abuse controls, backups and recovery evidence |
| Institutional boundary | Decide individual-only pilot versus institution-specific segregation; selecting a view is not professional credential or tenancy verification |
| Commercial and study terms | Decide fees/free access, participant cap, duration and research/ethics arrangements; none inferred from invitation-only access |

## Scope for qualified Australian review

Legal research intake fields: **Australia**, including relevant NT and participant
state/territory rules; **question** lawful supply and privacy boundary for this exact
education/research pilot; **facts** candidate and recorded decisions above;
**date boundary** proposed use from 1 November 2026, assessment prepared 6 October;
**source limits** public repository/primary sources now, confidential operational
facts and advice supplied privately after engagement. This brief requests review;
it does not perform or complete professional legal assessment.

Request two signed workstreams, which may be provided by one coordinated team:

1. **Software regulatory:** reconcile actual capabilities, foreseeable clinical use,
   intended purpose and all claims; determine medical-device status, any applicable
   exclusion or exemption, November CDSS criteria/application, manufacturer/sponsor
   responsibility and lawful supply pathway. Identify clinical evidence, ethics/trial,
   advertising and ongoing obligations where applicable, with primary-source reasoning.
2. **Privacy/legal:** determine entity coverage and relevant Commonwealth/NT/other
   state or institutional obligations; assess the data-flow and hosting/vendor model,
   overseas processing, accounts and sensitive-data risks; specify notices, terms,
   retention, security, incident response, individual rights and operator liability.

Ask the reviewers to separate verified facts, assumptions, conditional conclusions
and outstanding evidence. Request a dated revision-bound opinion, named responsible
reviewers, qualifications, conflicts/independence disclosure, conditions, and a clear
statement of what must change before the proposed pilot. Their advice is not the
operator's release approval and does not establish clinical safety.

## Engagement readiness and candidate providers

Public first-party service descriptions were inspected on 6 October 2026. These
support a shortlist, not independent verification of an assigned professional's
practising status, availability, price or suitability. Verify the named solicitor's
current practising status through the relevant regulator before legal engagement,
and obtain specific SaMD/CDSS experience for the assigned regulatory reviewer.

| Candidate | Inspected fit | Contact and limit |
| --- | --- | --- |
| Johnson Winter Slattery | [Healthcare & Life Sciences](https://jws.com.au/what-we-do/healthcare/) describes medical-device/software, privacy and health-record advice | [Official contact](https://jws.com.au/contact/); suggested first quote for combined regulatory/privacy legal scope. No named reviewer, quote or appointment yet |
| KD&A | [SaMD service](https://kdas.com.au/services/software-as-a-medical-device-samd/) describes software regulatory strategy/classification and customised quotes | Official page lists `kdent@kdas.com.au`; alternative regulatory specialist, with separate qualified privacy/legal coverage required. No appointment yet |

No outreach has been sent, no fee/budget approved and no professional engaged.
The next engagement action is a **quote and availability enquiry**, not acceptance
of paid work. Obtain conflict clearance, named reviewers, written scope/exclusions,
fee cap/GST, evidence needed and an achievable timetable. Request completion with
time for corrections before 1 November; if that is not achievable, keep NO-GO and
move the target rather than treating the date as approval.

### Ready-to-send enquiry

Subject: Quote request: Australian software regulatory and privacy review for Medical AI pilot

Hello,

I am Steven Lees in Darwin, the proposed individual operator of Medical AI. I am
seeking a scoped quote and availability for Australian software regulatory and
privacy/legal review before a proposed invitation-only pilot on 1 November 2026.

The proposed participants are invited adults in Australia: medical students, GPs,
health professionals and researchers, including people participating through
universities. The purpose is general education and research. Patient-identifying
data, patient-specific care, diagnosis, prescribing and treatment decisions are
outside the proposed scope. Application/storage hosting is proposed in Australia;
the provider is not selected and overseas evidence-query processing requires review.

The public source candidate is `a12567dedb5fa70c11ff757f7ff7bd0a74aa059b` in
https://github.com/Subzteveo/Medical-AI. The release assessment and operating brief
are repository documents; access-control tests are engineering evidence only.
External pilot/public/commercial release remains NO-GO pending assessment and approval.

Please identify the responsible reviewers, relevant SaMD/CDSS and privacy experience,
conflict-check process, proposed deliverables/exclusions, evidence you need, quote
including GST and fee cap, and earliest completion date. We need assessment of the
1 November 2026 CDSS boundary where applicable, operator/manufacturer/sponsor roles,
privacy coverage and the eventual hosting/data flows, plus conditions required before
lawful supply. Please tell me if you can cover both workstreams or need a separate specialist.

This is a request for a quote and availability, not authority to start billable work.
Confidential information can be supplied through your agreed secure process after
scope and engagement are settled.

Regards,
Steven Lees

## Closure and confidentiality

Store engagement documents, personal participant records, confidential advice and
operational secrets privately. Public repository records should contain only approved
non-confidential conclusions, candidate identity, reviewer role/date, conditions and
an evidence pointer. Do not assume legal privilege for this public brief.

Issue #5 stays open. Provider appointment, professional assessment, final hosting
configuration, notices/claims comparison and Steven Lees's dated release disposition
remain outstanding. Nothing in this record authorises invitations or deployment.
