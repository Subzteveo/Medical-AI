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
  and returns bounded liveness/version metadata. `/health/ready` is also public and returns
  one boolean per dependency (access configuration, session store, trace store, policy
  digests); it returns no path, secret, participant identifier or exception text.
- Presentation mode remains separate from identity. Selecting a clinician view does
  not establish that the participant is a GP or other health professional.

Remaining privacy/security work includes deployment secret custody, HTTPS and
direct-origin verification, infrastructure/proxy log review, operator identity,
participant notice/terms, retention/deletion, incident response, hosting/processor
assessment, account lifecycle operations and any required tenancy/rate-limit controls.

No Australian Privacy Act/APP, health-record, HIPAA, clinical-safety or regulatory
compliance claim is made by this engineering candidate.


## ToxSec DES-01 candidate — 7 November 2026

ToxSec's source-based review at `fad2ca97207a30d3c5c9f07d341b9e853b118df2` found that permitted research text could carry identifiers through query normalization into third-party provider requests. The synthetic helper check did not exercise live egress.

This branch adds conservative input rejection for common email, Australian mobile, address, numeric and name-shaped patterns before invoking a public provider. It also restricts HTTP jurisdiction metadata to values supported by the current UI (`AU`, `US`, `INTERNATIONAL`). The added regression tests inspect mocked connector calls and local trace storage for synthetic input. There is no claim that the detector reliably de-identifies arbitrary text: false negatives, indirect identifiers, uncommon formats and legitimate queries rejected as names remain possible.

**Pilot boundary remains blocked.** No real patient data may be entered. An independently reviewed permitted-input contract, a provider egress inventory, synthetic end-to-end privacy tests, operational log checks and an Australian privacy assessment remain required before considering invited use. This patch does not authorize PHI handling, deployment or release.

## Application log field inventory — 14 November 2026 candidate

`medical-ai-serve` writes one JSON object per line to standard error. A record may contain only these fields:

| Field | Content |
| --- | --- |
| `ts` | UTC time, millisecond precision |
| `level` | `debug`, `info`, `warning` or `error` |
| `logger` | Python logger name |
| `event` | Fixed event name (`request.completed`) or the message of a framework logger |
| `request_id` | uuid4, or a validated token from a trusted proxy |
| `method` | HTTP method |
| `path` | Matched route template, or the literal `unmatched`; never the client-supplied path |
| `status` | HTTP status code |
| `duration_ms` | Server-side handling time |
| `error_type` | Exception class name only, on unhandled errors |

Never logged by application code: query strings, request bodies, questions, answers, cookies, authorization values, invitation tokens, participant identifiers, exception messages or tracebacks. uvicorn's access log stays off. The `httpx` and `httpcore` loggers are held at WARNING because connector requests carry search terms in their URLs.

**Limits (unproven or out of scope):** framework and third-party loggers other than the two above write their own message text, which this change does not audit; reverse-proxy and host logs are not covered until C7; log retention, shipping and access are undecided; no PHI-bearing log has been tested against a real deployment. This is an engineering control, not a privacy-compliance claim.
