# Medical AI — Product North Star

**Status:** Canonical long-term product direction. This document defines where Medical AI is going; it does **not** by itself expand the current validated capability, intended use, regulatory position, or release status.

## North star

Medical AI is an **Australian-first, globally extensible, evidence-bound medical learning and research platform** that feels exceptionally simple to use while remaining rigorous underneath.

It should serve primarily:

- medical students;
- Australian GPs and other clinicians using the product for evidence retrieval and professional research within validated scope; and
- medical and health researchers.

The product should be clear enough that a first-time user can immediately understand:

1. what the system is showing;
2. what the evidence says;
3. where that evidence came from;
4. how strong, current, applicable and jurisdictionally relevant it is; and
5. what the user can do next within the product's validated scope.

The product goal is:

> **Turn authoritative medical, regulatory, legal and public-health information into a fast, understandable, traceable evidence experience—without allowing an AI model to become the source of medical truth.**

The usability target is:

> **Google-simple on the surface; medical-evidence infrastructure underneath.**

## Governing architecture

The governing information path is:

> **Authoritative data → admissible evidence → provenance → verification → safety → understandable output**

The controlling rule remains:

> **A model is never evidence.**

Models may retrieve, classify, extract, compare, translate, explain, synthesise or communicate evidence only inside machine-enforced evidence and information-handling boundaries. Availability to the system never grants an object authority to influence medical truth.

Production influence remains governed by the Medical Evidence Influence Policy and the v0.2 influence-control architecture. Evidence authority and information-handling/PHI authority are separate dimensions and must remain independently enforceable.

## Australian-first, globally extensible

Australia is not a localization layer added after a US-first product. Australian evidence, terminology, jurisdiction and obligations are first-class product infrastructure.

Priority Australian authority and infrastructure includes, where licensing and intended use permit:

- Therapeutic Goods Administration (TGA);
- Pharmaceutical Benefits Scheme (PBS);
- SNOMED CT-AU and Australian Medicines Terminology (AMT);
- National Clinical Terminology Service (NCTS) and appropriate terminology infrastructure;
- Australian clinical guidelines and public-health authorities;
- Australian Government and state/territory health datasets where appropriate;
- Australian privacy, health-record, consumer, professional and medical-device obligations relevant to the actual product and intended purpose.

The architecture must remain globally extensible to trusted international evidence and regulators, including sources such as PubMed/PMC, ClinicalTrials.gov, WHO, FDA, EMA and comparable authoritative bodies.

Jurisdiction must remain explicit. International evidence may inform an Australian user, but foreign regulatory status, labelling, recommendations or policy must never be silently presented as Australian authority.

## Product, not chatbot

Medical AI is the whole evidence product, not a chat interface wrapped around retrieval.

The long-term product surface includes:

- web application;
- iOS and Android experiences;
- information architecture and design system;
- evidence search and discovery;
- study and revision workflows;
- GP/professional research workflows;
- source, citation and provenance inspection;
- Australian jurisdiction handling;
- terminology search, normalization and mapping;
- regulatory, legal and public-health corpus access within licensed scope;
- backend APIs and databases;
- retrieval and indexing infrastructure;
- influence-control state machine and dependency/revocation semantics;
- evidence/clinical/research data-plane separation and privacy firewall;
- authentication and authorization;
- auditability and reproducibility;
- monitoring, rollback and change control;
- automated and human-reviewed evaluation;
- accessibility;
- privacy-respecting analytics;
- deployment and operations;
- onboarding;
- market positioning;
- pricing assumptions; and
- product copy.

These are product responsibilities, not a declaration that every item is currently implemented or validated.

## Core user experience

The interface should reveal complexity progressively rather than hiding evidence behind prose.

A user should be able to move naturally between:

> **Question or search → concise evidence state → supporting claims → exact sources/passages → provenance and qualifications → next product action**

The default view should be simple. Deeper inspection should expose the system's evidence state without requiring the user to trust an opaque confidence score.

Prefer meaningful dimensions such as:

- source authority;
- jurisdiction;
- evidence type;
- evidence certainty where supported;
- applicability/population;
- freshness/supersession state;
- agreement/conflict;
- claim-to-source verification state; and
- current capability or safety boundary.

The product should never use fluent language, visual polish or model confidence to obscure weak, missing, conflicting, outdated, indirect or jurisdictionally mismatched evidence.

## User modes on one evidence foundation

The platform may support different presentation and workflow modes, but they should share the same evidence-control foundation.

### Medical student mode

Optimize for learning, retrieval, concept inspection, source literacy, revision and understanding why an answer is supported.

### GP / clinician research mode

Optimize for fast professional evidence retrieval, Australian jurisdiction, source recency, applicability, conflict inspection and traceability. This mode does not by itself authorize patient-specific clinical decision support.

### Research mode

Optimize for literature/trial discovery, structured evidence extraction, comparison, provenance, reproducibility and exportable research workflows within licensing and privacy constraints.

Patient/public experiences, patient-specific CDS and autonomous diagnosis/treatment remain separate future capability classes requiring their own product, safety, clinical, privacy and regulatory validation.

## Evidence and data-plane discipline

The architecture must preserve explicit separation between:

- **evidence plane** — literature, guidelines, regulators, trials and other admissible evidence sources;
- **terminology plane** — SNOMED CT-AU, AMT, ICD, LOINC, UMLS and related terminology services;
- **clinical data plane** — patient/EHR information and interoperability such as FHIR/SMART where eventually approved;
- **research data plane** — cohorts, observational datasets and research infrastructure such as OMOP where eventually approved.

Information from a patient record, research dataset, model, connector or retrieved document must not become medical evidence merely because it is available.

Permission to process information and permission to influence a medical proposition remain distinct.

## Release boundary

Medical AI begins as an **education, evidence-retrieval and professional research system**.

It is not, by default:

- an autonomous diagnostic system;
- a prescribing system;
- an autonomous treatment-selection system;
- an emergency triage system;
- a substitute for clinician judgement; or
- a patient-specific clinical decision-support product.

Any movement across those boundaries requires explicit intended-purpose change control plus the corresponding clinical, safety, privacy, regulatory, human-factors and operational evidence.

Passing engineering tests does not establish clinical safety, regulatory compliance, retrieval accuracy in the real world, or production readiness.

## Product decision test

A proposed feature, model, connector, workflow or commercial decision should be challenged against these questions:

1. **Does it make authoritative evidence faster or easier to understand without weakening traceability?**
2. **Can the system show exactly what source and evidence state support the user-visible medical proposition?**
3. **Does it preserve `A model is never evidence` and the independent evidence/PHI authority boundaries?**
4. **Is Australian jurisdiction handled explicitly where relevant?**
5. **Does it remain inside the current validated/intended scope, or does it trigger a deliberate scope-change gate?**
6. **Can a first-time user understand the result, its limitations and the next safe product action?**
7. **Can the behavior be tested, audited, monitored, revoked and rolled back?**

If the answer to a required question is no, the feature should not acquire production influence merely because it is technically possible or commercially attractive.

## Relationship to current implementation contracts

This north star is the long-term product direction.

Current milestone documents remain authoritative for what is actually implemented, tested or allowed now, including:

- `docs/INTENDED_USE.md` for the current intended-use boundary;
- `project_docs/PRODUCT_FOUNDATION.md` for the current bounded product/MVP contract;
- `docs/MEDICAL_EVIDENCE_INFLUENCE_POLICY_v0.1.md` for evidence-influence rules;
- `docs/INFLUENCE_CONTROL_CORE_v0.2.md` and implementation code for the current machine-enforced influence-control mechanism;
- `project_docs/STATUS.md` for current project state; and
- validation/release documents for what has and has not been demonstrated.

When a milestone implements only part of this north star, the milestone may narrow scope but must not silently weaken the governing evidence, provenance, privacy, jurisdiction or release boundaries.
