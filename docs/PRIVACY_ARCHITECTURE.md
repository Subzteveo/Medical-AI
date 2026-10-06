# Privacy Architecture — alpha2.1 remediation candidate

- This candidate does not claim PHI approval.
- PubMed and ClinicalTrials.gov connectors are explicitly `phi_approved = false`.
- Deterministic patient/identifier detection runs before public connector invocation.
- The detector now covers the five realistic bypass examples reproduced by the 25 September 2026 ultrareview, but it remains heuristic and is **not** a guarantee that all PHI/identifiers are detected. Users must not enter identifying patient information.
- Persisted SQLite ExecutionTrace metadata stores keyed HMAC query digests and non-content identifiers/statuses, not raw user questions or retrieved source passages.
- Default trace storage is anchored to an absolute user-home path rather than the launch working directory; it can be overridden with `MEDICAL_AI_TRACE_DB`.
- Future production design requires separate `evidence_approved` and `phi_approved` states, operational access controls, retention/deletion, encryption, vendor/processor review, incident response and jurisdiction-specific privacy assessment.
- No HIPAA, Australian Privacy Act/APP, state health-record, or other compliance claim is made by this artifact.

## Invitation-only pilot access engineering candidate — 6 October 2026

Application-level identity/access control is implemented in engineering candidate
`523ab64fd180ab7550c8565dae1cb366c506f159` without changing the current no-PHI and no-release posture.

- Participant configuration is external to the repository and uses a stable
  `participant_id`, rotatable `credential_id`, SHA-256 invite-token digest,
  timezone-aware expiry and revocation flag.
- Raw invite tokens are accepted only in the JSON credential exchange body or
  `Authorization: Bearer` header. They are not placed in URLs and are not passed to
  the evidence engine or SQLite execution trace.
- Browser sessions are HMAC-signed and stored in an HTTP-only,
  `SameSite=Strict` cookie. `Secure` defaults to true. The signed payload contains
  participant ID, credential ID and session expiry; it does not contain the raw invite
  token.
- Expiry, revocation and credential ID are rechecked against the current allowlist on
  every protected request. Changing those values therefore invalidates an existing
  session rather than waiting only for cookie expiry.
- The active participant ID exists in request state for authorization. It is not
  currently persisted in the medical execution-trace database. That avoids silently
  expanding audit-data retention before operator/retention decisions are approved.
- `/v1/evidence/query`, `/docs` and `/openapi.json` are protected. The root route
  serves only a login shell before authentication. `/health` is intentionally public
  and returns bounded liveness/version metadata.
- Presentation mode remains separate from identity. Selecting a clinician view does
  not establish that the participant is a GP or other health professional.

Remaining privacy/security work includes deployment secret custody, HTTPS and
direct-origin verification, infrastructure/proxy log review, operator identity,
participant notice/terms, retention/deletion, incident response, hosting/processor
assessment, account lifecycle operations and any required tenancy/rate-limit controls.

No Australian Privacy Act/APP, health-record, HIPAA, clinical-safety or regulatory
compliance claim is made by this engineering candidate.

