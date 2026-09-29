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
