# Privacy Architecture — alpha2.1 remediation candidate

- This candidate does not claim PHI approval.
- PubMed and ClinicalTrials.gov connectors are explicitly `phi_approved = false`.
- Deterministic patient/identifier detection runs before public connector invocation.
- The detector now covers the five realistic bypass examples reproduced by the 25 September 2026 ultrareview, but it remains heuristic and is **not** a guarantee that all PHI/identifiers are detected. Users must not enter identifying patient information.
- Persisted SQLite ExecutionTrace metadata stores keyed HMAC query digests and non-content identifiers/statuses, not raw user questions or retrieved source passages.
- Default trace storage is anchored to an absolute user-home path rather than the launch working directory; it can be overridden with `MEDICAL_AI_TRACE_DB`.
- Future production design requires separate `evidence_approved` and `phi_approved` states, operational access controls, retention/deletion, encryption, vendor/processor review, incident response and jurisdiction-specific privacy assessment.
- No HIPAA, Australian Privacy Act/APP, state health-record, or other compliance claim is made by this artifact.
