# Evidence Atlas — UI implementation contract

**State:** Engineering-alpha interface tranche. Not deployed, clinically validated or authorized for public/commercial use.

## Views
- Search Evidence: existing authenticated root route, same POST `/v1/evidence/query` request schema and trusted server output. The user sees actual status, authorized claims, admitted sources, and execution trace.
- Inside Medical AI: explanatory five-column system map, not a live monitor.
- Source Directory: existing PubMed and ClinicalTrials.gov alpha adapters versus planned TGA/PBS/SNOMED CT-AU/AMT/NCTS; explicit evidence, terminology, clinical and research plane separation.

## Security, epistemic authority and accessibility
The backend's v0.2 influence controller alone admits `EvidenceAnswer.claims`. This UI never turns unverified candidates into evidence, and only shows PASS claims for server-supported states. For blocked, conflicting, outdated, unproven or unavailable states, it renders fixed nonclinical text instead of raw backend prose. Citations require an admitted source and HTTPS link; source text is inserted with `textContent`, never `innerHTML`.

The pilot authentication shell, protected API, signed-in session boundary, PHI restrictions and evidence-source approvals are unchanged. Tabs support keyboard arrows, Home and End; controls retain labels and visible focus. A browser keyboard walkthrough, screen-reader test, zoom/reflow testing and independent accessibility review are still necessary.

## Future contracts, not shipped features
Evidence Passport requires signed or reconstructible claim/authorization snapshots and exact passages. Influence X-ray requires authoritative decision/revocation records. Jurisdiction Lens requires independent validated Australian authority (cannot treat US authority as AU). Evidence history requires source version snapshots. Negative Space may only expose backend evidence gaps, not infer clinical conclusions.

## Remaining limitations
Alpha supports PubMed literature and ClinicalTrials.gov trial discovery. It does not validate clinical recommendations, perform GRADE appraisal or support patient-specific treatment. Live sources, real-world retrieval fidelity, release-scale citation entailment, complete PHI boundary, Australian regulator/terminology integration, mobile/assistive-technology verification, clinical safety and final regulation status remain unproven. No new routes, backend logic, patient-data features, connectors or models are introduced by this UI tranche.
