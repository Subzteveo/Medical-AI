# Product Foundation — Medical AI Evidence Workbench

## Objective

Provide medical students, clinicians and researchers with a transparent evidence-retrieval workbench whose substantive medical claims are traceable to admitted source passages and whose unsupported/high-consequence outputs fail closed.

## Primary users

- **Primary v1:** medical students and clinicians.
- **Secondary:** researchers.
- **Deferred:** patient/public experience using the same evidence infrastructure but separate presentation, safety, readability and escalation layers.

## Intended use

Education, evidence retrieval, literature/trial discovery and research support. The current product is not validated for autonomous diagnosis, prescribing, treatment selection, emergency triage or patient-specific clinical decision support.

## MVP requirements and acceptance

| Requirement | Observable acceptance |
|---|---|
| **REQ-001 Evidence-bound claims** — substantive medical claims must come from admitted evidence, not model memory | **AC-001:** every rendered claim has a ClaimRecord → EvidenceUnit → Passage → SourceRecord path and an exact-passage verification result |
| **REQ-002 Browser evidence workflow** | **AC-002:** a user can submit a general evidence question and inspect answer state, sources and trace from one accessible browser surface |
| **REQ-003 Claim-specific source routing** | **AC-003:** literature queries route to PubMed; explicit trial-discovery queries route to ClinicalTrials.gov; regulatory questions do not use either as a substitute regulator |
| **REQ-004 Patient-specific public-route block** | **AC-004:** detected patient-specific wording returns `OUTSIDE_VALIDATED_CAPABILITY` before a non-PHI-approved connector is called |
| **REQ-005 AU regulatory fail-closed** | **AC-005:** TGA/PBS/approval queries return `NO_AUTHORITATIVE_SOURCE` until an appropriate Australian authority adapter exists |
| **REQ-006 High-consequence fail-closed** | **AC-006:** dose/contraindication/interactions/pregnancy/paediatric/etc. claims cannot reach PASS through PubMed/trial-registry evidence alone |
| **REQ-007 Provenance and traceability** | **AC-007:** each answer exposes source IDs, evidence IDs, claim IDs, verifier state and component versions |
| **REQ-008 Minimal durable audit trail** | **AC-008:** local trace persistence survives process-level use without storing the raw user question or retrieved passages |
| **REQ-009 Safe dependency failure** | **AC-009:** source outage yields `SOURCE_UNAVAILABLE` and no model-memory fallback |
| **REQ-010 Accessible interaction states** | **AC-010:** native labelled form controls, keyboard-visible focus, status live region, responsive layout and text-based result states are present; deeper browser/AT testing remains separately evidenced |
| **REQ-011 Retrieval evaluation path** | **AC-011:** recall@k can be calculated from a gold fixture; production authoritative-source recall remains unestablished until a reviewed gold set and live runs exist |

## Explicit alpha2 non-goals

- Generative medical synthesis.
- GRADE/systematic-review certainty calculation.
- TGA/PBS/SNOMED CT-AU/AMT integration.
- Drug-interaction authority.
- EHR/FHIR/SMART or OMOP patient/research-data workflows.
- Authentication/multi-user tenancy.
- PHI-approved production processing.
- Public medical deployment.
- Autonomous clinical decision support.

## Candidate acceptance addition: context continuity → verified research outcome → commercial decision

**Status: proposed, not implemented or approved for release.** This supplements AC-001–AC-011, without lowering any existing requirement or intended-use boundary. Exact code baseline for the proposal: merged main `c5edb081dfefef022a3b8f7c25095930e83f1177` (27 October 2026). See [architecture mapping](ARCHITECTURE_AND_CONTRACTS.md#context--loop--harness--graph-evidence-bound-integration-candidate-28-october-2026).

### User result and controlled scope

For a medical student or researcher asking a **general, non-patient-specific** literature or trial-discovery question, the intended result is to find and inspect the correct original publication abstract/registered study facts, preserve qualifiers and attribution, understand why anything was withheld, and complete a genuine research-inspection task without relying on unsupported AI medical claims. This is distinct from proving efficacy, clinical applicability or correctness. User-facing browser inspectability and clarity must be measured with real people, not inferred from unit tests.

The candidate context-to-outcome loop reuses `QueryPlan` → original source → `Passage` → `EvidenceUnit` → `ClaimRecord` → `CitationMapping` → `ExecutionTrace` → existing influence controller. A presentation-only graph may link delivered, currently authorised IDs; it is never a second source of truth, authorisation system or medical recommendation engine. Development agents may propose fixes off-line, not issue medical answers without controller approval. No new graph/orchestration store is approved.

### Proposed outcome acceptance register (not a claim of achievement)

| ID | Observable acceptance / independent oracle | Current evidence and gap |
|---|---|---|
| AC-012 — Context continuity | On a frozen corpus containing the PR #32 metadata-punctuation, #33 cross-section context and #34 research-variable/unknown-medicine cases, a reviewer can follow every **displayed** claim through `ClaimRecord → EvidenceUnit → Passage → SourceRecord` plus current influence authorisation. No unsupported standalone efficacy claim, dropped abstract qualification or risk-downgraded unknown interaction survives. | Source-diff and original-field checks are recorded in the three PR evidence directories; repeat on each candidate SHA and have a reviewer inspect newly introduced graph presentation. Not independently established for a future candidate. |
| AC-013 — Bounded failure/recovery loop | A baseline trace, precise earliest deviation, changed revision, failing pre-fix case, passing post-fix case and retained adverse control can be recovered for each of #32–#34. Any missing transition is labelled UNKNOWN. Withheld results never generate silent fallback claims or automatic weak-source retries. | Individual PR records preserve many inputs and results; cross-revision independently checked continuity has **not** run as one acceptance test. |
| AC-014 — Demonstrable task value | **Proposed study, not results:** at least 5 consented users complete 20 predefined general research-inspection tasks, with a blinded or independent assessor comparing against an established manual/source-first baseline. Record task completion, source/context identification, errors, abstention comprehension and time-to-correct-source. Candidate thresholds: ≥80% correct task completion, zero uncorrected source-attribution errors in the reviewed set, and no deterioration in correct-source time or abstention understanding against the baseline. Record failures and confidence limits; small n does not validate clinical reliability. | NOT RUN: user studies, independently adjudicated source/task gold set, comparator and consent/privacy plan are absent. |
| AC-015 — No new medical influence | PR, unit, browser and adversarial tests show no added user-visible medical influence without existing authority; blocked PHI, Australian regulatory questions, high-consequence evidence, tampered citations and unknown medicine terms continue to withhold. | Existing engineering regressions passed on PR #34's exact head; must be rerun for any modified code and independently checked before further product claims. |
| AC-016 — Commercial release boundary | The owner approves a specific audience, claim set, data handling route, distribution method, source rights, privacy/security review, operational controls and product-specific Australian regulatory assessment. If clinical or patient-specific purpose is proposed, require its distinct clinical validation/authorisation. Commercial supply cannot be inferred from AC-012–AC-015. | NOT ESTABLISHED; the repository does not authorise public/commercial medical release, clinical pilot or deployment. |

### Candidate Outcome Alignment handoff

- **Outcome ID:** `medical-ai/research-evidence-context-continuity/v0.1-candidate`.
- **Actor:** research/education user and separately named independent evaluator; human product owner approves scope and release.
- **Baseline:** main commit `c5edb081dfefef022a3b8f7c25095930e83f1177` and its PR #32/#33/#34 evidence records. This is a proposed next-revision comparison, not retrospective proof of customer value.
- **Hard constraints:** `A model is never evidence`; no patient data; evidence-authority separate from information-handling authority; fail-closed high-consequence handling; no unsupported Australian regulator substitution; no new unreviewed clinical intended purpose; source licensing respected.
- **Measured checks:** AC-012–AC-015 plus independent human research-task observations in AC-014. Review same original task against manual comparator; retain errors and unverified outcomes.
- **Decision:** `NOT_ESTABLISHED` for commercial readiness until AC-014 and AC-016 have trustworthy independent evidence; engineering tests cannot override a hard constraint. Report `PARTIAL` only for demonstrably completed technical acceptance checks, identifying exact revision and scope. OA does not itself grant release.
- **One correction at a time:** failing objective → original evidence and first divergence → minimal controlled correction → exact-head regressions/browser/source comparison → independent check → human decision → next iteration. Stop on an unresolved authority, evidence or regulatory gap.

### Commercial interpretation

An owner-reviewed, accurate **engineering case study** of PRs #32–#34 may be used to explain the project's research method with explicit development-stage limitations and no patient-care or efficacy claims. This is not equivalent to selling or providing the Medical-AI software, inviting live clinical users, or representing the product as validated. Before external product access, pilot or paid software supply, establish the actual intended purpose, access/PHI and data controls, source licensing, legal/regulatory position, operational readiness and approval. The [TGA's 16 October 2026 CDSS guidance](https://www.tga.gov.au/resources/guidance/understanding-clinical-decision-support-system-software-regulation) was under review for [1 November 2026 amendments](https://www.tga.gov.au/news/news-articles/clinical-decision-support-system-exemption-amendments); this proposal is not a TGA classification.

**Smallest next verification:** reproduce the three original failures and the adverse PR #34 suffix case using the archived, revision-bound fixtures on a review candidate, confirm graph traversal through the existing provenance mappings and withheld-state non-disclosure, then request independent inspection. No paid product trial or public deployment is authorised by this section.
