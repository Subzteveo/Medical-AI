# Release Readiness — remediation candidate

## Decision

- Internal engineering development: **GO**
- Public/external medical release: **NO-GO**
- Commercial/public sale: **not authorised; pricing and public-access plan deferred**
- Deployment/distribution: **not authorised / not performed**

## Why the canonical alpha2 evidence was reopened

The 25 September 2026 ultrareview reproduced critical failures in high-consequence gating, claim-level gating, retraction handling, registry-efficacy handling and patient/identifier detection. The original alpha2 `22/22` suite therefore did not establish the safety claims it was being used to support.

A remediation regression suite has since been added and passes in the current working environment, but this does not itself establish release safety.

## Still blocking later release

- live network validation of the exact remediation candidate;
- clinically reviewed retrieval benchmark and ≥98% authoritative-source recall@k target;
- release-scale citation-entailment benchmark;
- broad medical safety suite and zero observed critical-failure evidence;
- high-consequence authoritative source path + genuinely independent second verifier;
- TGA/PBS and Australian terminology integrations where applicable;
- product-specific TGA/intended-purpose assessment before public/commercial distribution;
- robust PHI intake/routing + privacy operational validation;
- authentication/access controls for any shared/public service;
- real browser/accessibility verification;
- production monitoring/rollback exercises;
- verified GitHub/revision provenance and fresh-environment install evidence.
