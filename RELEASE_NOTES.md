# Release Notes — Medical AI v0.1.0-alpha2.1-remediation

Internal remediation candidate derived from the canonical `v0.1.0-alpha2` artifact after the 25 September 2026 ultrareview reproduced critical safety defects. **Not approved for public or clinical deployment.**

## Safety remediation

- runtime consequence categories now mirror the 13-category policy and cover reproduced inflected/missing phrasings;
- each extracted claim is consequence-classified independently of the original query;
- retracted PubMed publications are marked superseded and excluded;
- PubMed publication types are captured;
- ClinicalTrials.gov sponsor/investigator narrative cannot establish efficacy/safety claims;
- patient/identifier detection covers the five reproduced bypass inputs, while the UI explicitly retains the heuristic/no-guarantee warning;
- overlapping source prompt-injection instructions are filtered from EvidenceUnits;
- regulatory routing false positives were narrowed and refusal wording now respects requested jurisdiction;
- empty retrieval results no longer falsely imply that no authoritative source exists;
- plain-English source queries are normalized before search;
- sentence splitting protects common abbreviations such as `vs.` and `i.e.`;
- trace query digests use keyed HMAC rather than unsalted SHA-256;
- default trace path is stable rather than current-working-directory dependent.

## Release integrity and reproducibility

- runtime/development dependencies are exact-pinned;
- checksum verification checks the existing manifest; generation is a separate explicit script;
- all four packaged policy files are loaded by the runtime path;
- worker prompts now include structured output contracts/examples;
- unrelated Make AI do Good plugin audit removed from the medical app package;
- full Medical Evidence Influence Policy is included under its canonical name;
- raw chat citation markers removed from packaged research material.

## Evidence

- Red checkpoint after adding ultrareview regressions: **34 failed, 29 passed**.
- Green checkpoint after remediation: **63 passed** in the current container.
- Secret-pattern scan: no target secrets found.
- Editable install with `--no-build-isolation`: passed in the provisioned environment.
- Standard build-isolated wheel: blocked here by DNS/package-index access, not established on this candidate.
- Live PubMed/ClinicalTrials smoke tests: attempted but blocked here by outbound network/DNS.

## Still blocked for public release

Clinically reviewed retrieval benchmarks, release-scale citation correctness, genuinely independent high-consequence verification, complete PHI/privacy operations, TGA/PBS authority integration, product-specific Australian regulatory determination, real browser/assistive-tech verification, authentication, production monitoring/rollback, and live-source verification on the exact artifact.
