# Validation Plan — alpha2.1 remediation candidate

Canonical REQ→AC→VAL mapping and observed run evidence live in `project_docs/VALIDATION_AND_EVIDENCE.md`.

Automated coverage now includes:
- end-to-end SourceRecord → Passage → EvidenceUnit → ClaimRecord → verification → trace;
- unsupported claim rejection;
- 18 policy-derived high-consequence query phrasings;
- claim-level high-consequence classification independent of query level;
- retracted PubMed publication parsing/supersession;
- ClinicalTrials.gov narrative efficacy blocking;
- five realistic patient/identifier pre-connector blocks;
- plain-English retrieval-query normalization contract;
- empty-result vs missing-authority status distinction;
- prompt-injection overlap filtering;
- abbreviation-safe sentence splitting for `vs.` and related forms;
- keyed-HMAC query digests;
- regulatory false-positive/routing checks;
- jurisdiction-aware regulatory refusal wording;
- stable trace database path;
- publication-type capture;
- structured browser rendering rather than literal Markdown;
- exact dependency pinning;
- checksum verification that does not regenerate the manifest;
- packaged-policy/runtime category binding;
- upstream source outage safe degradation without model fallback;
- content-minimised SQLite trace persistence;
- browser shell/health endpoints;
- recall@k metric plumbing.

Observed remediation sequence in this container:

- red checkpoint after adding ultrareview regressions: `34 failed, 29 passed`;
- green checkpoint after fixes: `63 passed`.

Still not established: live source behavior on this remediation candidate in a network-capable runtime, clinically reviewed retrieval recall, release-scale citation correctness, broad critical clinical safety suite, subgroup performance, complete PHI detection, accessibility runtime conformance, production monitoring/rollback, or TGA/PBS/SNOMED CT-AU/AMT integration.
