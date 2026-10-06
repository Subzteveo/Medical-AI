# Invitation-only pilot: candidate assessment

**Assessment date:** 6 October 2026, Australia/Darwin
**Target pilot date:** 1 November 2026, subject to approval
**Disposition:** **NO-GO for external pilot, public or commercial release**
**Related:** [Issue #5](https://github.com/Subzteveo/Medical-AI/issues/5), [release decision record](RELEASE_READINESS.md)

This is a repository and primary-source assessment prepared by Codex. It is not
professional legal advice, a TGA determination, an appointed reviewer's sign-off,
or Steven Lees's release approval. No invitation, distribution or deployment is authorised.

## Frozen scope and identity

| Field | Assessed boundary |
| --- | --- |
| Repository | `Subzteveo/Medical-AI` |
| Exact candidate commit | [`197134ba22510f902c033f55d39ed33c5af22857`](https://github.com/Subzteveo/Medical-AI/tree/197134ba22510f902c033f55d39ed33c5af22857), fetched `main` on assessment date |
| Git tree | `1eab9decd0e5e71147f3a1fcf278a0a67b9c11b9` |
| Package metadata | `medical-ai-evidence-workbench`, `0.1.0a2.post1`; metadata does not uniquely identify this commit |
| Runtime labels | API `0.1.0-alpha2.1-remediation`; engine `0.2.0-influence-control-core`; UI still says Alpha2 |
| Distribution artifact | No pilot wheel/container/deployment configuration selected or hashed; source assessment only |
| Audience supplied by Steven Lees | Medical students, GPs, health professionals, universities, researchers |
| Access model supplied by Steven Lees | Invitation-only pilot |
| Release target supplied by Steven Lees | 1 November 2026; pilot duration/end date unresolved |
| Purpose | Existing [INTENDED_USE.md](INTENDED_USE.md): general medical education, evidence retrieval, literature/trial discovery, research support and clinician provenance inspection |
| Patient/public access | No public registration or patient-facing decision support is proposed in this assessment. This is an interpretation of the supplied audience and invitation model, pending explicit final boundary approval |
| Institutions | Universities are treated as potential participating institutions; actual individual users and institutional responsibilities still need confirmation |
| Jurisdiction | Australian requirements assessed. Australia-only participation is a proposed assessment boundary, not a user-approved geography; overseas participation requires separate review |
| Commercial terms | Pricing, fees and contractual terms unresolved; no sale authority inferred |

A later documentation commit does not replace this frozen source candidate.
Any runtime, purpose, audience, access architecture or release-date change requires
an updated assessment of the affected evidence. The actual release must identify
both its source revision and final distribution artifact/configuration.

## Review question and method

Can this exact candidate support the proposed pilot and what must be resolved for
1 November 2026? Included: tracked UI/API, engine, policies, connectors, trace store,
tests, package/workflow metadata, existing purpose/privacy/release documents, and
Australian primary sources below. Excluded: unobserved infrastructure, live user
sessions, clinical validation, overseas law and confidential advice.

Legal research inputs: jurisdiction Australia; question software-device/CDSS and
privacy boundaries for the pilot; facts the frozen candidate and supplied plan;
effective date 1 November 2026; source access public TGA, Federal Register and OAIC
material retrieved on 6 October 2026. This forward assessment must be refreshed
before supply because future legal/guidance changes cannot be ruled out today.

Paths below refer to the frozen commit, not whatever `main` later contains.
`Inspected` means source inspection; `executed` means a recorded check. Passing
fixtures is not clinical verification. Stop at a documented NO-GO when approvals,
operational evidence or professional determinations are absent.

## Capability and purpose mapping

| Function/boundary | Inspected evidence at candidate | Assessment and limitation |
| --- | --- | --- |
| Education and general literature retrieval | `api.py`: POST `/v1/evidence/query`; `connectors/pubmed.py`: ESearch/EFetch; `extractor.py`, `claims.py`, `verifier.py`, `renderer.py` | Implemented extractive abstract-sentence path with source IDs/passages/citations. Exact passage matching is not study-quality assessment or clinical entailment validation |
| Trial discovery/research | `planner.py`, `connectors/clinical_trials.py`, `extractor.py` | Registry facts admitted for discovery; sponsor narrative is not efficacy/safety evidence. No patient eligibility matching or research ethics approval established |
| Inspectable evidence | `engine.py`, `schemas.py`, `static/index.html` | Structured claims, evidence, sources, safety flags and trace displayed; does not prove a user can independently verify every clinically relevant recommendation |
| Role views | `api.py`: client-selected `student`, `clinician`, `researcher`; UI select control | Presentation modes, not authenticated roles, verified GP credentials or university tenancy |
| Australian regulatory queries | `planner.py`, `engine.py` | Recognised regulator requests return `NO_AUTHORITATIVE_SOURCE`; no implemented TGA/PBS connector. AU selection does not make PubMed evidence Australian regulatory authority |
| Patient-specific/identifying requests | `planner.py` regex detector; `engine.py` early terminal branch; public connectors `phi_approved=False` | Detected requests blocked before retrieval; heuristic detection is not comprehensive PHI prevention. General free text can escape detection |
| High-consequence claims | `planner.py`, `claims.py`, `verifier.py`, `engine.py` | Recognised high-consequence claims fail closed; dedicated authority and independent second verifier unavailable. Keyword/claim patterns are not proof all diagnosis/treatment requests are blocked |
| Diagnosis, treatment selection, prescribing, triage | Existing intended-use exclusions; no validated clinical decision service | Excluded purposes remain excluded. Education wording and clinician access do not establish that foreseeable misuse is prevented |
| Evidence influence controls | `influence.py`, `engine.py` | Evidence/handling authority and revocation gates implemented; these authorise claim influence, not human access to the service |
| Live fidelity and usability | `docs/ALPHA3_ENGINEERING_HARNESS.md`, tests and current UI | Synthetic retrieval/order results do not prove live recall/ranking or clinical entailment. Deployed browser/accessibility, live-source and pilot usability evidence absent |

## Executed engineering evidence

Local Python 3.12.14 checks on the frozen application source, 6 October 2026:

- Editable install with the repository's pinned direct application/dev dependencies: passed.
  Transitive dependencies are not a complete reproducible lock; this is not a pilot artifact.
- `python -m pytest`: **103 passed**, one Starlette/AnyIO deprecation warning.
- Alpha3 CLI report records the exact candidate SHA: four required cases passed,
  two blocked cases and three unproven checks. The conflict and population-mismatch
  cases currently emit `ANSWER_SUPPORTED_WITH_QUALIFICATIONS` instead of their
  intended abstention states. These are material unresolved capability gaps,
  not successful safety checks.
- Compile and installed policy parity/parse: passed.
- Original frozen-commit manifest independently checked against Git blob bytes:
  **79 hashes matched**. Updated documentation has its own intentional manifest change.
- Local entry-control probe: no-network connector, synthetic general question,
  FastAPI TestClient, no credentials, each of the three user modes. HTTP 200 and
  `EVIDENCE_INSUFFICIENT` for each query confirms no application authentication gate.

No live PubMed/ClinicalTrials calls, clinical benchmark, deployed access gateway,
real browser/accessibility exercise or production privacy check was executed.
These results support bounded engineering findings only.

## Access and privacy assessment

**Supported conclusion: this candidate cannot itself enforce an invitation-only
shared pilot.** `api.py` has no authentication dependency/middleware, invitation
allowlist, server-side user role or tenant boundary. An executed local FastAPI TestClient check, with a no-network connector substituted,
returned HTTP 200 for unauthenticated POST requests in all three user modes, and
for GET `/`, `/docs`, `/openapi.json` and `/health`. This tests application entry
controls; it does not establish network exposure of an unobserved deployment. No deployment gateway evidence was supplied; an external
identity proxy could be proposed, but cannot be assumed to exist or protect all routes.

| Control | Candidate evidence/state | Required pilot evidence |
| --- | --- | --- |
| Invitation and identity | Absent in application; self-selected modes | Selected identity/access design; named invitees; deny uninvited, revoked and expired sessions; authorised enrolment/offboarding owner |
| Direct API protection | No authentication on query, root or default API docs | Prove all sensitive entry points are protected, including direct origin/API calls; bypass prevention, least privilege and session controls |
| Organisation isolation | No user/tenant identity in trace persistence | Decide whether tenancy is needed; test institutional/admin boundaries and prevent cross-user disclosure |
| Abuse and cost controls | Input length/result limit present; no application rate limiter | Per-user/request limits, external connector quotas, monitoring and suspension procedure |
| Query data flow | Public connectors receive normalised query text; identifiers can evade heuristic gate | No patient-identifying data policy and operational enforcement; processor/hosting/log review; test accidental PHI handling before external egress |
| Audit storage | SQLite stores HMAC digests and non-content trace metadata; no raw query/passages persisted by that store | Storage access, retention/deletion, encryption, backup, incident response and account-level audit design; infrastructure logs separately assessed |
| Notice/terms | Privacy architecture exists; no standalone user-facing privacy notice identified in tracked files | Operator identity, collection/usage/overseas processing, retention, rights/contact, acceptable use and pilot terms approved before onboarding |

A private URL, invitation email or clinician view alone is not an access control.
No PHI-approved production route or privacy compliance finding is established.

## Australian regulatory assessment for the target date

**Provisional inference:** tightly limited general education/reference/research
retrieval may sit outside the medical-device definition if the actual manufacturer
purpose and claims contain no medical-device purpose. This is not a determination:
extractive medical answers, clinical context and product claims require a
product-specific boundary review. Invitation-only or free access is not evidence
of exemption. Evaluate each function before selecting a regulatory pathway.

| Question/pathway | Primary-source finding | Candidate consequence |
| --- | --- | --- |
| Medical device first | TGA directs manufacturers to assess intended purpose under Act s41BD [R1, R4] | Qualified reviewer must reconcile actual outputs, excluded uses and all supplied/promotional claims; no classification signed off |
| Excluded goods | TGA requires all functions to meet relevant exclusion conditions [R5] | No specific excluded-goods category proven. Do not equate an education label with a statutory exclusion |
| CDSS on 1 November | F2026L01167 s2/Schedule 1 Part 3 item48 amends Schedule4 item2.15 [R2] | If relying on CDSS exemption, assess all five criteria: recommendation to health professional for specified purpose; no medical image/signal processing; no replacement of judgement; no diagnosis/treatment decision; displayed guideline/calculation/logic enabling ready interpretation/verification |
| Existing build timing | Item49 inserts reg11.90 covering earlier-manufactured devices intended for use on/after commencement [R2] | Building or inviting before November does not avoid the amended test for the target use date |
| Mixed audience | CDSS guidance limits the pathway to health-professional decision support [R1] | Students/researchers/universities are not automatically health professionals. Verify individual status and purposes if the pathway is contemplated; no blanket CDSS exemption established |
| Interpretability | Candidate shows passages/citations and trace metadata, not a verified clinical recommendation logic display | Citation presence alone does not prove amended criterion(e); clinical user interpretation/verification evidence needed if applicable |
| If exempt CDSS | TGA lists notification, Essential Principles, adverse-event and advertising duties [R1] | Exempt is not unregulated; document responsible sponsor/manufacturer and applicable compliance evidence |
| If regulated and neither excluded nor exempt | TGA requires ARTG inclusion before supply [R5, R6] | Classification, conformity/evidence and lawful supply pathway must be resolved before pilot; no ARTG inclusion asserted |
| Research/clinical trial | TGA identifies CTN/CTA pathways for clinical trials using unapproved software devices [R6] | Calling this a pilot/research project does not establish a clinical-trial pathway. Determine whether proposed activities need ethics and device-trial approvals |
| Privacy | OAIC APP guidance covers notices, security, overseas disclosure and retention for APP entities [R7]; health-service providers holding health information can be covered regardless of size [R8] | Confirm operator/entity coverage and relevant state/territory/institutional rules. Resolve actual collection, hosting and account metadata before pilot; no small-business exemption assumed |

No new AI recommendation engine is present in this extractive candidate. Adding
one would change the assessment, not inherit this provisional education boundary.
No assessment of another country's requirements is established.

### Primary-source register

All sources accessed **6 October 2026**. Legal conclusions remain provisional.

| ID | Source/version and inspected location | Evidence limit |
| --- | --- | --- |
| R1 | [TGA CDSS guidance](https://www.tga.gov.au/resources/guidance/understanding-clinical-decision-support-system-software-regulation), updated 29 January 2026; definition/exclusion/exemption and regulatory duties sections | Guidance predates commencement; use R2 for amended text |
| R2 | [F2026L01167 authorised text](https://www.legislation.gov.au/F2026L01167/asmade/2026-09-07/text/original/pdf), registered 7 September 2026; s2 and Schedule1 Part3 items48-49, printed pp13-14 | Commencement/application verified; not a product exemption determination |
| R3 | [F2026L01167 explanatory statement](https://www.legislation.gov.au/F2026L01167/asmade/2026-09-07/es/original/pdf), Part3 discussion printed pp22-23 | Explains clarification; does not substitute for instrument |
| R4 | [Therapeutic Goods Act 1989, current register](https://www.legislation.gov.au/C2004A03952/latest/text); medical-device definition referenced by R1 | Reference link; full Act not exhaustively assessed |
| R5 | [TGA software exclusions](https://www.tga.gov.au/products/medical-devices/software-and-artificial-intelligence-ai/overview/software-based-medical-device-exclusions), updated 16 March 2026; all-functions condition and supply boundary | No exclusion category claimed without instrument-level product matching |
| R6 | [TGA exempt software](https://www.tga.gov.au/products/medical-devices/software-and-artificial-intelligence-ai/overview/exempt-software-medical-device), updated 29 January 2026; supply/exemption and clinical-trial sections | Conditional pathway guidance, not permission for this pilot |
| R7 | [OAIC APP quick reference](https://www.oaic.gov.au/privacy/australian-privacy-principles/australian-privacy-principles-quick-reference), APP1/3/5/8/11/12/13 | Coverage and detailed implementation still need assessment |
| R8 | [OAIC health-service provider coverage](https://www.oaic.gov.au/privacy/your-privacy-rights/health-information/what-is-a-health-service-provider), coverage paragraph | Whether this operator supplies a health service and holds health information unresolved |

The TGA 8 September amendment announcement appeared in search results, but direct
retrieval timed out twice. The commencement conclusion is based on the inspected
authorised instrument, not that unavailable announcement. Recheck current law,
instrument status and guidance immediately before the final release disposition.

## Claims/notice reconciliation

| Surface | Candidate finding | Remaining decision |
| --- | --- | --- |
| Intended use and README | Education/research scope; clinical and public/commercial release excluded | Preserve purpose owner; approve bounded pilot wording only after assessment |
| UI and answer footer | Alpha2 language; no validated diagnosis/prescribing/patient decisions; extractive limitations | Reconcile labels with selected artifact and approved capability claims; verify real browser experience |
| API/package | Alpha2.1 metadata while engine says v0.2 | Do not use version label as release identity; align in separately tested runtime change |
| Release notes and status | Historical checkpoints describe earlier revisions | This frozen assessment does not upgrade old evidence to current verification |
| Privacy notice | Standalone notice not found | Prepare after operator/hosting/data decisions; architecture is not an onboarding notice |
| Marketing/invitations/pricing | No final pilot materials supplied for review | Claims comparison remains incomplete until actual text and terms are inspected |

## Conditions before disposition

1. Steven Lees confirms patient/public boundary, participant geography, institutions,
   operator, pilot duration, commercial terms and permitted activities. The supplied
   audience/access/date decisions are recorded, not approval to invite or deploy.
2. Maintainer implements or selects an enforceable access architecture and supplies
   tests/configuration evidence, including direct API bypass and revocation checks.
3. Appropriately qualified Australian reviewer determines device/exclusion/exemption
   pathway, November applicability, sponsor/manufacturer obligations, privacy coverage
   and any ethics/trial requirements against the actual candidate and proposed claims.
   Adviser appointment and professional advice remain unresolved; keep confidential advice private.
4. Complete pilot-relevant live-source, fidelity, safety, privacy, browser and operational
   evidence. Other [release blockers](RELEASE_READINESS.md) remain separate gates;
   any justified applicability decision must be explicit, not an omitted check.
5. Reconcile all actual onboarding/marketing/notice surfaces; freeze source/artifact
   and access configuration; refresh effective-date research; record Steven Lees's
   dated disposition with qualified review references and residual conditions.

Issue #5 remains open. External pilot and public/commercial release remain **NO-GO**.
