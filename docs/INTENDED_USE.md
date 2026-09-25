# Intended Use — remediation candidate

## Developer-stated intended purpose

Medical AI is an engineering-alpha evidence workbench intended to help **medical students, clinicians and researchers** retrieve and inspect general medical literature and trial-registry information with claim-level provenance.

The current build is intended for:
- medical education and concept review;
- general evidence retrieval;
- literature and trial discovery;
- research support; and
- clinician-facing inspection of source provenance.

The current build is **not intended** to:
- make a clinical diagnosis;
- make or specify a treatment decision for a patient;
- prescribe, select, initiate, stop or dose treatment for a patient;
- replace the clinical judgement of a health professional;
- perform autonomous emergency triage; or
- process patient-identifying information through public evidence connectors.

The renderer may expose only claims that pass the runtime evidence gates. PubMed supports admitted literature claims. ClinicalTrials.gov supports trial discovery and registered-study facts only; sponsor/investigator narrative is not admitted as treatment-efficacy or safety evidence. High-consequence claims remain fail-closed because the required authoritative-source and independent second-verifier path is not implemented.

## Australian regulatory position — release gate, not a legal determination

No final TGA classification or exemption determination has been made for this product. That determination depends on the product's actual intended purpose, claims, users, functions and distribution at release time.

Primary-source review performed 25 September 2026 found:
- TGA guidance states that whether software is a medical device depends on its intended purpose and that CDSS intended to support clinical decisions is subject to the applicable medical-device framework unless excluded or exempt.
- Therapeutic Goods Legislation Amendment (2026 Measures No. 1) Regulations 2026 (F2026L01167) contains amendments commencing **1 November 2026**. The amended CDSS exemption remains framed around recommendations to a health professional, not replacing clinical judgement or making diagnosis/treatment decisions, and adds a condition that the software display the clinical practice guidelines, calculations or logic used so a health professional can readily interpret and verify recommendations.

Sources checked:
- TGA, *Understanding clinical decision support system software regulation*.
- TGA, *Clinical decision support system exemption amendments*, 8 September 2026.
- Federal Register of Legislation, F2026L01167, Schedule 1 Part 3.

Before any public or commercial launch, obtain a product-specific regulatory assessment based on the then-current intended purpose and actual release functionality. This document is an engineering statement of intended purpose, not legal advice or a TGA determination.
