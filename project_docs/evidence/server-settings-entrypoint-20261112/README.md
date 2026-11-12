# C1 — settings module, `medical-ai-serve` entry point, test isolation — 12 November 2026

**Plan:** [full application build plan](../../plans/2026-11-11-full-app-build-plan.md), chunk C1
**Base `main`:** `8a326342343c797e113e58967b712a4b7b86b4ab`
**Recorded:** 12 November 2026, Australia/Darwin
**Disposition:** **generated + executed + passed locally.** Not verified, not audited, not merged, not deployed. Clinical, privacy and release posture unchanged (**NO-GO**).

Engineering evidence only. The head SHA and exact-head CI are read from the pull request, not from this file.

## 1. Preconditions and the gap C1 closes

At the base revision the application had no launcher: no `[project.scripts]` entry, no `__main__`, no `uvicorn.run` under `src/`, and no settings module. Environment variables were read ad hoc. The pilot allowlist could only be supplied inline in `MEDICAL_AI_PILOT_ACCESS_JSON`. The test suite wrote session and trace databases into the real `~/.medical_ai` directory.

## 2. What was implemented

- `src/medical_ai/settings.py` — frozen, strictly typed settings (`ServerSettings`, `StorageSettings`, `ConnectorSettings`, `RateLimitSettings`, `Settings`), read from the environment on every call and never cached. Validation errors name the variable and never echo its value. `MEDICAL_AI_WORKERS` must be 1, because influence revocation state is per-process until the A3 persistent ledger exists. `RateLimitSettings` is parsed only; nothing enforces it until chunk C6.
- `src/medical_ai/server.py` — `medical-ai-serve`. Runs start-up checks (settings, trace HMAC key of at least 32 bytes, access configuration, session store, trace store, digest-bound authority policies) and refuses to start if any fails. `--check-config` prints a redacted JSON report (names, counts, booleans) and exits 0 or 1. The server runs one uvicorn worker with request access logs off and forwarded headers untrusted.
- `src/medical_ai/access.py` — `MEDICAL_AI_PILOT_ACCESS_FILE` as an alternative to the inline JSON. Exactly one source may be set. The file is opened without following a final symlink, must be a regular file with no group/other permission bits, and is limited to 1 MiB; any deviation fails closed (HTTP 503 on protected routes). It is re-read per request, so allowlist edits apply without a restart. `parse_access_document` validates a document without reading the environment.
- `src/medical_ai/api.py` — `TRACE_DB` comes from `settings.trace_db_path` (still absolute, still resolved at import, never raises). `build_engine()` reads NCBI values and the new `MEDICAL_AI_HTTP_TIMEOUT_SECONDS` from settings.
- `pyproject.toml` — `[project.scripts] medical-ai-serve`; both new modules added to the strict Pyright include.
- `tests/conftest.py` — autouse `isolated_state_dirs` (per-test temporary session and trace databases) and a session guard that fails the run if `~/.medical_ai` is created or modified.
- Tests: `tests/test_settings.py`, `tests/test_server_entrypoint.py`, eight additions to `tests/test_pilot_access.py`.

Not changed: `engine.py`, `renderer.py`, `influence.py`, connectors, `authority.py`, `authority_policy.py`, `authority_resolver.py`, every policy file, the UI. No route was added or removed. The engine's random per-process fallback for the trace HMAC key remains for tests; only the server entry point requires the key.

## 3. Behaviour exercised

Red before implementation: `tests/test_settings.py` and `tests/test_server_entrypoint.py` failed at collection (modules absent); four of the new `tests/test_pilot_access.py` cases failed.

Deterministic tests after implementation cover: defaults; every range and enum rejection; workers other than 1 rejected; conflicting allowlist sources; errors not echoing rejected values; per-call environment reads; uvicorn options passed (`workers=1`, `access_log=False`, `proxy_headers=False`, `server_header=False`); refusal to start without the HMAC key, with invalid settings, or without access configuration; `--check-config` output containing none of the synthetic secrets or the token digest; allowlist file happy path, live revocation by file edit, broad permissions, symlink, missing path, directory, oversize and dual-source cases all failing closed; importing `medical_ai.api` in a clean subprocess with a malformed port and an empty home directory.

Manual smoke on the working tree with synthetic values only: `medical-ai-serve --check-config` returned `status: ok`; the server started on a loopback port; `GET /health` returned 200; unauthenticated `POST /v1/evidence/query` returned 401; `POST /access/session` with the synthetic token returned 200; an authenticated Australian regulatory question returned 200 (abstention path, no external call); the server log contained zero occurrences of the token; starting without the HMAC key exited 1 with a message naming the variable.

## 4. Local check results at the working tree (pre-merge)

Clean exact-pinned `.[dev]` environment, Python 3.13 locally (CI uses 3.12):

- source checksum manifest: **passed** (123 entries; was 118);
- repository hygiene: **passed**;
- strict Pyright including the two new modules: **0 errors, 0 warnings**;
- influence-boundary source guard: **passed** (8 authoritative files, list unchanged);
- deterministic pytest suite: **442 passed, 1 warning** (was 400; +42);
- Alpha3 engineering harness CLI: ran to completion, exit 0 (blocked and unproven cases unchanged);
- compile, import smoke, package policy parity: **passed**.

## 5. Not done / still gated

- No container, TLS edge, readiness endpoint, structured logging, security headers or rate limiting: chunks C3 to C7. uvicorn's own start-up lines still use its default log format.
- No live PubMed or ClinicalTrials.gov call was made in this chunk.
- Kilo Claw audit and owner review are outstanding. Exact-head CI is read from the pull request.
- Deployment to any host, pilot invitations, pen testing and release remain separately owner-gated. **NO-GO unchanged.**
