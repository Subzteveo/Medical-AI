# Security and Privacy — remediation candidate

## Relevant data flow

User question → FastAPI validation → deterministic policy-bound planner → privacy/consequence gate → approved public evidence connector → normalized source data → evidence/claim verification → answer response.

A minimal audit record is written locally after processing. It contains a **keyed HMAC query digest**, classification/status, connector/source/evidence/claim identifiers and component versions. It deliberately excludes raw question text and source passages.

## Trust boundaries

1. **Browser input is untrusted.** Backend validation and policy gates are authoritative.
2. **Retrieved source text is untrusted content.** It can supply evidence, but instruction-like source text is not permitted to control the system.
3. **Public connectors are non-PHI routes.** `phi_approved=false` is explicit connector metadata.
4. **Local trace storage is not designed as a PHI repository.** This does not establish legal/compliance status.
5. **No authentication exists in this candidate.** It remains an internal/local engineering artifact, not an approved public multi-user service.

## Current controls

- deterministic patient/identifier patterns run before connector invocation;
- five reproduced realistic patient/identifier inputs are regression-tested;
- the UI explicitly says the detector is heuristic and tells users not to enter identifiers;
- raw questions and retrieved passages are excluded from persisted trace payloads;
- query digests use keyed HMAC rather than unsalted SHA-256;
- connector failure has no model-memory fallback;
- external text is rendered with DOM text nodes/structured links rather than trusted source HTML;
- regulatory and high-consequence paths fail closed;
- claim-level consequence classification prevents a moderate question from laundering a high-consequence extracted claim;
- retracted PubMed records are marked superseded and rejected;
- ClinicalTrials.gov narrative descriptions are retained for provenance but are not promoted to efficacy/safety claims;
- packaged policy files are loaded by the runtime rather than existing only as documentation.

## Limits

The patient/identifier detector remains heuristic. It cannot prove absence of PHI or guarantee de-identification. A future PHI-capable workflow requires separate intake, data minimisation, processor/vendor approval, access control, retention/deletion, logging, encryption, incident response, applicable Australian privacy/legal review and runtime verification.

No HIPAA, Privacy Act, APP, medical-device, ISO, SOC, WCAG or other compliance/certification claim is made.
