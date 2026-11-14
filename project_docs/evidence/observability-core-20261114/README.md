# C4 — readiness endpoint, structured no-content logging, request id — 14 November 2026

**Plan:** [full application build plan](../../plans/2026-11-11-full-app-build-plan.md), chunk C4
**Base `main`:** `7f5dcd18015cc00e5203ba869ae27c6fa1439b84` (C3 merged via PR #61)
**Recorded:** 14 November 2026
**Disposition:** **generated + executed + passed locally.** Not verified, not audited, not merged, not deployed. Clinical, privacy and release posture unchanged (**NO-GO**).

Engineering evidence only. The head SHA and exact-head CI are read from the pull request, not from this file. No Kilo Claw audit record exists for C1–C4.

## 1. Preconditions and the gap C4 closes

The server had liveness (`/health`) but no readiness signal an orchestrator or operator could poll, no application log format, and no request correlation. uvicorn's access log was already off (C1), so nothing recorded what the application did; and the connectors use `httpx`, whose default INFO line prints the full request URL including search terms.

## 2. What was implemented

- `src/medical_ai/logging_config.py` — `configure_logging(level, stream=None)` installs one JSON-lines handler on the root logger (idempotent) and holds `httpx`/`httpcore` at WARNING. `JsonLogFormatter` serialises an allowlist of fields only (`ts, level, logger, event, request_id, method, path, status, duration_ms`) plus `error_type` (exception class name). Exception text, tracebacks and non-allowlisted `extra` values are never serialised.
- `src/medical_ai/readiness.py` — the four start-up checks moved out of `server.py` and shared; `readiness_checks()` returns booleans (`access_config`, `session_store`, `trace_store`, `policies`). Policy compilation is cached per process. Unreadable settings fail the two store checks closed.
- `src/medical_ai/api.py` — `GET /health/ready` (public, 200/503, `no-store`) and a `request_context` middleware: request id (uuid4; an inbound `X-Request-ID` is honoured only when `MEDICAL_AI_TRUSTED_PROXY_COUNT` > 0 and the value matches `[A-Za-z0-9._-]{8,64}`), echoed in the response header, and one `request.completed` log line per request with the matched route template (the literal `unmatched` for unknown paths) — never the client path, query string, body, cookie or token. Unhandled exceptions are logged with status 500 and class name only, then re-raised.
- `src/medical_ai/server.py` — calls `configure_logging` before `uvicorn.run` and passes `log_config=None`. `--check-config` does not reconfigure logging.
- `pyproject.toml` — both new modules added to the strict Pyright include.
- `docs/PRIVACY_ARCHITECTURE.md` — log field inventory and limits; `project_docs/ARCHITECTURE_AND_CONTRACTS.md` — route and request-id contract.

Not changed: engine, renderer, influence controller, connectors, `authority*.py`, every policy file, the existing routes' behaviour, the UI, the container assets.

## 3. Behaviour exercised

Red before implementation: `tests/test_observability.py` failed at collection (module absent).

30 deterministic tests cover: readiness 200 with all four checks; 503 naming the failed check (no access configuration; unusable session store; invalid settings); readiness body free of paths, secrets, participant ids and "sqlite"; request id generated as uuid4, echoed on success, 401, 422 and 404; inbound id ignored at proxy count 0, honoured at 1, malformed ids replaced; log lines contain only allowlisted fields; `test_logs_never_contain_request_content` — a synthetic invitation token, session cookie value, session secret, question text, query-string marker and participant id never appear in any rendered log line across a session exchange, an answered query, a rejected query and an unauthenticated query; unknown paths logged as `unmatched`; error statuses logged; an unhandled exception whose message contains the synthetic question logs only status 500 and the class name; the formatter drops unallowlisted extras and tracebacks; `configure_logging` writes JSON to stderr, is idempotent, honours level, rejects unknown levels, covers `uvicorn.*` loggers and holds `httpx`/`httpcore` at WARNING; `server.main` configures logging and passes `log_config=None`; hostile route metadata yields `unmatched` rather than an error.

**The log-content tests can fail for the defects they guard.** Mutation checks on the working tree: logging the full request URL as `path` failed 3 tests; removing the `httpx`/`httpcore` quieting failed 3 tests; both were restored and the suite returned to 29 passed (before the route-metadata test was added). The capture helper configures logging as `medical-ai-serve` does, because the in-process test client is itself built on `httpx` and would otherwise log URLs and measure the test client rather than the server.

**A real defect was found and fixed by the existing suite.** On first full run, two existing tests in `tests/test_toxsec_eax001_redaction.py` (`property_error` cases) failed because the new middleware read `request.scope["route"].path` outside a guard, and that test injects a route whose `path` raises. Root cause: `getattr(..., None)` only absorbs `AttributeError`. Fix: `_route_template` treats any error as `unmatched`; the existing tests were not changed, and `test_failing_route_metadata_does_not_break_the_request_or_the_log` pins the behaviour. Baseline on `main` passed 20/20 in that file before the change.

## 4. Local check results at the working tree (pre-merge)

Clean editable install at this working tree, Python 3.13 locally (CI uses 3.12). See the pull request for the exact-head CI runs.

- Focused: `tests/test_observability.py` **30 passed**.
- Full suite **554 passed** (524 on `main` + 30 new), Alpha3 harness exit 0, MEDAI-EVAL-002 harness exit 0, strict Pyright gate and influence-boundary guard passed, source checksums verified, repo hygiene passed, compileall + import smoke passed, installed policies match. Exit codes and counts only; CI is authoritative for the exact head.

## 5. Not done / still gated

- **Not exercised under a real server:** the tests use the in-process client and a recorded `uvicorn.run`. No log line was captured from a running `medical-ai-serve` or container; that is a CI/operator check, not claimed here.
- Framework and third-party loggers other than `httpx`/`httpcore` emit their own message text and were not audited. Reverse-proxy and host logs are C7. Log retention, shipping and access control are undecided.
- The readiness endpoint reports configuration and store reachability, not upstream connector availability.
- Rate limiting and the 429 path are C6; security headers are C5.
- Kilo Claw audit and owner review outstanding. **NO-GO unchanged.**
