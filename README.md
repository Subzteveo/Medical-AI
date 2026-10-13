# Medical AI

An **Australian-first, globally extensible, evidence-bound medical learning and research platform** built around authoritative sources, explicit provenance, controlled influence, and fail-closed safety boundaries.

The product north star is simple on the surface and rigorous underneath: **Google-simple on the surface; medical-evidence infrastructure underneath.** See [`project_docs/NORTH_STAR.md`](project_docs/NORTH_STAR.md).

Developed by Oli and Stevie.

## Current status

**Engineering alpha / pre-release development. Not approved for clinical use, diagnosis, prescribing, patient-specific treatment decisions, or public/commercial medical release.**

The exact alpha2.1 remediation source has been imported and merged. Medical AI v0.2 now includes a machine-enforced evidence-influence control core with independent evidence-authority and information-handling/PHI authority dimensions, typed data planes, authorization artefacts, dependency tracking, selective revocation, and fail-closed rendering integration. PR #10 merged this control core; deterministic CI at its final PR head passed with **85 tests**.

Those engineering results establish only the tested implementation behavior. They do **not** establish clinical safety, production readiness, Australian privacy or medical-device compliance, validated real-world retrieval accuracy, release-scale citation correctness, complete PHI protection, independent high-consequence verification, or live external-source validation.

See [`project_docs/NORTH_STAR.md`](project_docs/NORTH_STAR.md) for the canonical long-term product direction, [`project_docs/PROJECT_INDEX.md`](project_docs/PROJECT_INDEX.md) for the source-of-truth map, [`project_docs/STATUS.md`](project_docs/STATUS.md) for the current development checkpoint, and [`docs/INTENDED_USE.md`](docs/INTENDED_USE.md) for the current intended-use boundary.


> **11 October 2026 governance addendum:** At observed `main` revision `13fadd41e628ff60de2cdfff933b3e2be19f1327`, PR #21's typed influence-control hardening is merged and exact-revision deterministic CI completed successfully. Those outcomes are revision-bound engineering evidence only. The approved Alpha3 Tranche A **engineering contract** has not yet been implemented. Required PR and required CI merge enforcement are not demonstrated in the active branch ruleset; see [G0 governance checkpoint](project_docs/ALPHA3_TRANCHE_A_G0_CHECKPOINT.md). No status of clinical validation, release authorization or production readiness is implied.

## Engineering principles

- A model is never evidence.
- No user-visible medical factual claim without recoverable provenance.
- Source authority is claim-specific and jurisdiction-aware.
- Australian sources, terminology and jurisdiction are first-class where relevant.
- Known, unknown, inferred, and source-supported information remain distinct.
- High-consequence medical claims fail closed.
- Conflict and abstention are legitimate outputs.
- PHI approval and evidence approval are separate.
- Evidence, terminology, clinical-data and research-data planes remain explicitly separated.
- Generated prose is a view over verified state; generation must not create medical truth.
- Passing engineering tests does not by itself establish clinical safety or release readiness.

## Git workflow

`main` is the stable integration branch. Development happens on short-lived branches and enters `main` through reviewed pull requests. Do not push feature work directly to `main`.

## Alpha3 deterministic harness (engineering fixtures)

Run the bounded Alpha3 evidence-fidelity engineering harness:

```bash
python -m medical_ai.evals.alpha3_evidence_fidelity --json-out /tmp/alpha3-evidence-fidelity.json
```

The default evaluation requires all six cases to execute and four fixed cases to pass;
conflict and population mismatch remain **BLOCKED**, never counted as passes.
`--required-case-id` only adds execution requirements. Case-set policy cannot remove
baseline cases or downgrade required tiers. Invalid policy exits non-zero.

Recall and first-authoritative rank describe synthetic fixture source order after
pipeline admission (`trace.source_ids`), not measured live retrieval/ranking.
Normalization is observed in the fixture connector. Current-pipeline live recall,
clinical entailment and live-source ranking remain unproven.

See [the coverage map](docs/ALPHA3_ENGINEERING_HARNESS.md) for remaining Issue #4 gaps.

Run focused harness tests:

```bash
python -m pytest tests/test_alpha3_evidence_fidelity_eval.py -q
```


## Invitation-only pilot access gate — engineering candidate

Branch candidate revision `523ab64fd180ab7550c8565dae1cb366c506f159` adds an application-level, deny-by-default
access boundary for the proposed invitation-only pilot. This is engineering work only;
it does not authorize deployment, pilot invitations, clinical use, public release or
commercial release.

Runtime configuration is external to the repository:

- `MEDICAL_AI_PILOT_ACCESS_JSON` contains the explicit participant allowlist. Each
  participant has a stable `participant_id`, rotatable `credential_id`, SHA-256 digest
  of a high-entropy invite token, timezone-aware expiry and revocation flag.
- `MEDICAL_AI_PILOT_SESSION_SECRET` is an out-of-repository secret used to HMAC-sign
  browser sessions and must contain at least 32 bytes.
- `MEDICAL_AI_PILOT_SESSION_TTL_SECONDS` is optional, defaults to 28,800 seconds
  (8 hours), and is bounded to 300-43,200 seconds.
- `MEDICAL_AI_PILOT_COOKIE_SECURE` defaults to `true`. Setting it to `false` is
  for controlled local/test HTTP only, not an external pilot.

Allowlist JSON has exactly one top-level field, `participants`. Every entry must
contain exactly `participant_id`, `credential_id`, `token_sha256`, `expires_at` and
an explicit boolean `revoked`. Missing, unexpected or duplicate fields fail closed.
Invite credentials must be 20-512 characters on both Bearer and browser paths;
operators must generate high-entropy values, since length alone does not prove entropy.
Rotate both the token digest and `credential_id` to invalidate previous invitations
and their existing sessions. Credential-validation errors never echo submitted input.

Do not commit invite tokens, session secrets or environment files. Generate and deliver
invite tokens out of band; only token digests belong in the runtime allowlist. Expiry
and revocation are checked on every protected request, including already-issued
browser sessions.

Route boundary in this candidate:

- `/` is a public access shell until a valid session exists; the workbench itself is
  served only after authentication.
- `/access/session` is the credential exchange endpoint and never places credentials
  in the URL.
- `/v1/evidence/query`, `/docs` and `/openapi.json` require an active participant.
- Direct API clients may use the invite token as a Bearer credential; the same
  allowlist, expiry and revocation checks apply.
- `/health` remains intentionally public for liveness/version checks and exposes no
  participant or medical query data.

The `student`, `clinician` and `researcher` values remain presentation modes.
They are not identity proof, professional credential verification or authorization
roles. The authenticated participant ID is attached to request state for the active
request; it is not currently written into the medical execution trace.

Regression tests are included for fail-closed configuration, unauthenticated and
invalid access, valid direct API access, expiry, revocation, existing-session
invalidation, browser entry, protected API documentation, request-body identity
override attempts and raw credential echo/logging. PR/CI evidence remains the
authority for whether those tests actually pass at the final head.

## Privacy

Do **not** place real patient identifiers, Medicare numbers, medical-record data, secrets, access tokens, or other sensitive information in issues, pull requests, commits, fixtures, screenshots, logs, or CI artifacts.

## Licensing

Do not copy proprietary medical content into the repository unless the project has explicit rights to store and redistribute it. Source adapters must preserve licensing/access constraints.
