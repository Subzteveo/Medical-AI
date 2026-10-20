# Evidence Atlas — UI implementation contract

**State:** Engineering-alpha branch candidate, based on `main` at `9aaf79627acf2bdc85940764aebd4eb2737e8203`. The provenance repair is local commit `ac804d3fc3942619a180033bbb72c211271b7d69`; the inspection-surface follow-up is prepared for review. Neither establishes merge, deployment, clinical validation or public/commercial release approval.

## Views
- Search Evidence: existing authenticated root route, same POST `/v1/evidence/query` request schema and trusted server output. The user sees actual status, authorized claims, admitted sources, and execution trace.
- Inside Medical AI: explanatory five-column system map, not a live monitor.
- Source Directory: existing PubMed and ClinicalTrials.gov alpha adapters versus planned TGA/PBS/SNOMED CT-AU/AMT/NCTS; explicit evidence, terminology, clinical and research plane separation.

## Security, epistemic authority and accessibility
The backend's v0.2 influence controller alone grants claim capabilities. The renderer rechecks those capabilities and the complete delivered claim/evidence/passage/source/citation graph. `EvidenceAnswer` checks references, supported status, trace records and recorded decisions. The API reparses a detached response, checks the issuing controller's current decision/capability and regenerates Markdown from authorised views. A supplied `PASS` or `ALLOW` flag alone cannot enter that path.

The browser checks graph closure and recorded outcome consistency before displaying any claim. Missing or duplicate IDs, unresolved/mismatched references, unsafe links and contradictory supported responses produce a provenance hold. Every source-link surface uses `appendSourceLink` and `safeSourceUrl`. HTTPS permits a link scheme; it establishes no medical evidence authority. Text uses `textContent`, never `innerHTML`.

The pilot authentication shell, protected API, signed-in session boundary, PHI restrictions and evidence-source approvals are unchanged. Tabs support keyboard arrows, Home and End; controls retain labels and visible focus. A browser keyboard walkthrough, screen-reader test, zoom/reflow testing and independent accessibility review are still necessary.

## Evidence Passport and deterministic boundary panel

The branch implements a limited inspection view of the returned server snapshot. Each Passport shows actual retrieved passages with exact claim text highlighted, source/evidence/passage/mapping IDs, locators, recorded verifier outcomes, controller decision and authorization IDs, policy versions and timestamps. Absent optional metadata is labelled **Not supplied**. Policy digests and source-admission rule/tier records are absent from the existing contract, so no hash, tier, trust badge or clinical certainty is generated for them.

The boundary panel distinguishes **Failed**, **Unknown** and **Not implemented**. Failed rows derive from returned outcomes or recorded failed decisions. Missing gate records remain unknown. Fixed capability limits identify absent TGA/PBS connectors and independent high-consequence verification. Extractive support does not establish GRADE certainty, comprehensive freshness/conflict review, patient applicability or ongoing monitoring.

This is not a signed export, persistent replay authority or continuous revocation monitor. The browser cannot establish current controller state after response delivery. The fuller Passport contract, Influence X-ray, validated Australian jurisdiction lens and evidence history remain future work. No A1 authority model or verbatim Tranche A contract is reconstructed here.

## Bounded verification

Repair regressions use real engine, renderer, response-schema and authenticated FastAPI interfaces with synthetic records. On the unchanged baseline, 47 of 50 new checks failed; three positive/revocation controls passed. After repair, the full Python suite passed 203 tests. DOM execution withheld 43 malformed responses and preserved a valid control. Further DOM checks inspect Passport passages/mappings/decisions, missing optional fields and three terminal outcomes.

The Alpha3 fixture harness still records four required cases passing, two blocked conflict/population cases and three unproven live/clinical checks. The limitations panel explicitly identifies the missing dedicated conflict/population gates; this build does not repair or close those broader evaluation gaps.

Playwright checks use the same real-engine synthetic fixtures, including keyboard disclosure, source links and mobile overflow. Local Chromium execution is **blocked** by the environment's socket restriction. Screenshots and browser layout/accessibility outcomes are not claimed. Exact-head CI, CodeQL, browser execution and human review remain required before merge. Fixture tests are not live-source or clinical validation.

## Remaining limitations
Alpha supports PubMed literature and ClinicalTrials.gov trial discovery. It does not validate clinical recommendations, perform GRADE appraisal or support patient-specific treatment. Live sources, real-world retrieval fidelity, release-scale citation entailment, complete PHI boundary, Australian regulator/terminology integration, mobile/assistive-technology verification, clinical safety and final regulation status remain unproven. This follow-up changes existing output checks and presentation; it adds no endpoint, patient-data workflow, connector, model or release permission.
