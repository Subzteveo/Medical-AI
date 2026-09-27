# Release and Operations — remediation candidate

## Current release boundary

This directory is a **remediation source candidate derived from the canonical alpha2 baseline**. Packaging, publication, installation, deployment and observed operation remain separate events.

## D6 readiness status

| Gate | State |
|---|---|
| Ultrareview-derived regression suite | Satisfied in current container: 63/63 total tests pass after remediation |
| Original alpha2 safety evidence | Superseded/contradicted where documented; retained in remediation history |
| Static/package syntax | Must be rerun on exact final candidate |
| Live PubMed contract | Must be rerun on exact remediation artifact |
| Live ClinicalTrials.gov contract | Must be rerun on exact remediation artifact |
| Clinically reviewed retrieval benchmark | Unsatisfied / not yet built |
| High-consequence independent verification | Unsatisfied; deterministic blocking is not an independent clinical verifier |
| TGA/PBS authority path | Unsatisfied |
| TGA intended-purpose/classification determination | Unverified; required before public/commercial launch |
| PHI/privacy production route | Unsatisfied |
| Browser accessibility runtime checks | Unverified |
| GitHub/revision provenance | Conditional and fail-closed: treat as verified only when both pull-request and push CI runs succeed for the exact PR head SHA. Last verified SHA: `e17f8b2656204f76e0a353f833e9494fbfa70311` (PR run `36159636815`, push run `36159603463`). Any newer SHA is unverified until matching CI evidence is recorded. |
| Public deployment rollback/monitoring | Not applicable yet / not designed for deployment |

**Public/external medical release: NO-GO.**

## Distribution and pricing

No public price, subscription tier or "anyone can buy" access model is approved in this foundation. Distribution remains internal/development-only until regulatory, privacy, safety and release gates are explicitly resolved.

## Deployment

No D7 deployment is authorized by remediation packaging. A future deployment must identify its target, users, intended purpose, data path, authentication/exposure, secrets, monitoring, recovery/rollback and actual post-deployment observation before `Installed/Deployed` or `Observed operational` can be claimed.
