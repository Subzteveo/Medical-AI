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

## Invitation lifecycle tooling — 12 November 2026 candidate

Engineering tooling only. It does not authorize issuing invitations, a pilot or deployment.

`medical-ai-admin` edits the allowlist file the server reads through `MEDICAL_AI_PILOT_ACCESS_FILE`. The server re-reads that file on every request, so changes apply without a restart.

| Step | Command | Effect |
| --- | --- | --- |
| Issue | `medical-ai-admin invite --allowlist PATH --participant-id ID --credential-id ID --ttl-days N` | Prints the token once on standard output. Deliver it out of band; it cannot be recovered later. |
| Revoke | `medical-ai-admin revoke --allowlist PATH --participant-id ID` | The token and any existing browser session stop working on the next request. |
| Rotate | `medical-ai-admin rotate --allowlist PATH --participant-id ID --credential-id NEWID` | Old token and old sessions stop working; a new token is printed once. |
| Review | `medical-ai-admin list --allowlist PATH` / `check` | Shows state without tokens or full digests; validates the file. |

The file must be a regular, non-symlinked file readable only by its owner. One operator edits it at a time: concurrent runs are not locked. Enrolment records, consent, identity checks, token delivery and retention are not handled by this tool and remain unresolved operating decisions.

