# Medical AI — Full Application Build Plan (chunked, auditable)

**Recorded:** 11 November 2026
**Status:** **proposed** coordination plan. Nothing in this document is implemented, executed or verified. It is not a substitute for `STATUS.md`, approved requirements, GitHub enforcement or release authority. **Public, pilot, commercial and clinical release remain NO-GO.**
**Base `main` when written:** `eb1dcd7`

> **For agentic workers:** execute this plan task-by-task, one chunk per branch and pull request. Steps use checkbox (`- [ ]`) syntax for tracking. Kilo Claw audits each chunk before the next starts; see [`KILO_CLAW_AUDIT_PROTOCOL.md`](KILO_CLAW_AUDIT_PROTOCOL.md).

## Context

The repository is a bounded engineering alpha: one FastAPI module (`src/medical_ai/api.py`), PubMed and ClinicalTrials.gov connectors, an extractive evidence pipeline, the v0.2 influence-control core with the A1/A2 authority kernel, a static Evidence Atlas page, SQLite trace and session stores, and an invite-only access gate. It has no launcher, settings module, container, TLS edge, rate limiting, admin tooling, TGA/PBS adapters, readiness or observability, or runbook.

Owner decisions recorded on 11 November 2026 for this plan:

- **Server shape:** self-hosted container (Dockerfile, compose, Caddy TLS reverse proxy, systemd unit), provider-agnostic Australian VPS, SQLite on a mounted volume. Deployment itself remains a separate owner gate.
- **Australian sources:** build TGA (ARTG) and PBS adapters behind the existing fail-closed gates, disabled by default. SNOMED CT-AU/AMT/NCTS is deferred pending licence.
- **Audit:** Kilo Claw audits each chunk after the coding agent finishes it.

Hard boundaries (from `AGENTS.md` and the 4 November handoff): a model is never evidence; the A1 kernel (`authority.py`, digest-bound policies, resolver mappings) is owner-gated; deployment, pilot invitations, pen test, A3/A4, SNOMED and release each need separate owner approval. This plan builds up to those gates and marks the gated steps.

**Spec:** this document, arguing from `project_docs/NORTH_STAR.md`, `project_docs/PRODUCT_FOUNDATION.md` (REQ-001..011), `docs/INTENDED_USE.md`, `docs/RELEASE_READINESS.md` and `docs/PILOT_OPERATING_BOUNDARY_AND_REVIEW_BRIEF.md`.

**Goal:** Turn the engineering alpha into a self-hosted, operable, Australian-first evidence product with its own server, built in 20 independently mergeable chunks that each leave `main` green and are each audited by Kilo Claw.

**Architecture:** Keep the single FastAPI process and the fail-closed pipeline unchanged in shape. Add a typed settings layer and a console entry point around it, wrap it in a non-root container behind Caddy, add TGA/PBS connectors that route through the existing admission gate and fail closed at the authority resolver until an owner-approved kernel PR maps them, and grow the Evidence Atlas into a mode-aware, progressively inspectable surface fed by new read-only endpoints. Operations (admin CLI, backups, retention, runbook, live smoke) complete the lifecycle.

**Tech stack:** Python 3.12, FastAPI 0.128.2, uvicorn 0.48.0, httpx 0.28.1, pydantic 2.13.4, PyYAML 6.0.3, SQLite; pytest 9.0.2, pyright 1.1.414 strict; Docker, Caddy 2.x, systemd; Playwright 1.56.1 + jsdom for UI checks. No new runtime dependencies.

## Global constraints (apply to every chunk)

- Branch names `feat/…`, `fix/…`, `docs/…`, `chore/…`; one chunk per PR; PR body follows `.github/PULL_REQUEST_TEMPLATE.md`.
- `provenance/SOURCE_SHA256SUMS` must list every tracked file under `src/`, `tests/`, `policies/`, `prompts/`, `evals/` and `pyproject.toml`; update by hand with `sha256sum`, keep `LC_ALL=C` sort; **never add a generator**. Bind new security-relevant docs too.
- Every `policies/*.yaml` is byte-identical in `src/medical_ai/policies/`; v0.2 policies carry a recomputed `policy_digest`.
- New modules that construct capabilities/output go into `[tool.pyright] include` (strict) and, if they build `InfluenceAuthorization`/`EvidenceAnswer`/call `render_answer`, into `scripts/verify_influence_boundary.py` lists. No `Any`, `cast`, `# type: ignore` in guarded files.
- `scripts/check_repo_hygiene.py` rejects binaries, `.env*`, `*.db`, keys: the env example is `deploy/medical-ai.env.example`, never `.env.example`.
- Tests set env with `monkeypatch` after import and `load_access_config()` runs per request: all settings are read lazily per call, never cached at import; `import medical_ai.api` must succeed with no env.
- Evidence vocabulary only: `proposed, generated, inspected, executed, passed, verified, blocked, unproven`. Never call generated code executed, a green run verification, or an image deployed.
- No PHI, tokens, secrets, real participant data in code, fixtures, logs, CI artifacts or PR text. Synthetic fixtures only.
- Logs never contain question text, answer text, cookies, tokens, or `Authorization` values.
- Do not edit `authority.py`, `authority_policy.py`, `authority_resolver.py` mapping dicts, or any `*-v0.2.yaml` outside chunk C9, and C9 only after written owner approval.
- Each chunk ends with `project_docs/evidence/<topic>-<YYYYMMDD>/README.md` (headings: 1 defect/preconditions, 2 what was implemented, 3 behaviour exercised, 4 local check results, 5 not done / still gated) and a dated STATUS.md banner line. Public/pilot/clinical release remains NO-GO in every record.

## Standard chunk check sequence (run before every push)

```bash
python scripts/verify_source_checksums.py
python scripts/check_repo_hygiene.py
python -m pip install -e '.[dev]'
python scripts/run_type_safety_gate.py --json-out /tmp/type-safety.json
python -m pytest
python -m medical_ai.evals.alpha3_evidence_fidelity --json-out /tmp/alpha3.json
python -m compileall -q src && python -c 'import medical_ai.api, medical_ai.engine, medical_ai.schemas'
python scripts/verify_package_policies.py
```
Expected: all exit 0; pytest count ≥ previous chunk's count (record both numbers in the evidence README).

## Kilo Claw audit protocol (one audit per chunk)

Auditor reads the chunk's PR, exact head SHA, CI run, evidence README. Records `project_docs/evidence/<topic>-<date>/AUDIT.md` with: head SHA audited; checks re-executed locally (commands + pass/fail counts); invariant checklist (A model is never evidence; fail-closed on missing authority; evidence/PHI authority separation; no PHI/secrets in repo/logs; no overclaiming words "verified/validated/deployed" without evidence; manifest/policy parity intact; kernel files untouched unless C9); findings (severity, file:line, reproduction); verdict **PASS / FAIL / BLOCKED / UNVERIFIED**; owner decisions required. A FAIL opens a `fix/…` chunk before the next chunk starts. Audits never modify code.

## Chunk map

| # | Chunk | Branch | Depends on | Owner gate |
|---|---|---|---|---|
| C1 | Settings module + `medical-ai-serve` + test isolation | `feat/server-settings-entrypoint` | — | no |
| C2 | `medical-ai-admin` invite/revoke/rotate/list/check | `feat/admin-cli` | C1 | no |
| C3 | Dockerfile + compose (app) + dependency lock + CI container smoke | `feat/container-image` | C1 | no |
| C4 | Readiness endpoint + structured no-content logging + request id | `feat/observability-core` | C1 | no |
| C5 | Security headers middleware | `feat/security-headers` | C4 | no |
| C6 | Rate limiting | `feat/rate-limiting` | C1, C4 | no |
| C7 | Caddy TLS proxy + systemd unit + deploy README | `feat/edge-proxy-systemd` | C3, C6 | no (deployment itself stays gated) |
| C8 | AU source-contract spike (TGA ARTG, PBS) + fixtures | `docs/au-source-contracts` | — | no |
| C9a | AU routing split + fail-closed RED tests + CODEOWNERS | `feat/au-routing-fail-closed` | C8 | no |
| C9b | PBSConnector (disabled by default) | `feat/pbs-connector` | C9a | no |
| C9c | TGAConnector (disabled by default) | `feat/tga-connector` | C9a | no |
| C9 | **Kernel enablement for AU authority** | `feat/au-authority-kernel` | C9a–c | **YES** |
| C10 | `GET /v1/sources` + live Source Directory | `feat/source-directory-endpoint` | C9a | no |
| C11a | Answer-state catalogue endpoint + evidence-dimension summary | `feat/answer-states` | C10 | no |
| C11b | Mode-aware presentation (student/clinician/researcher) | `feat/mode-presentation` | C11a | no |
| C12 | `GET /v1/evidence/trace/{id}` + researcher JSON export | `feat/trace-endpoint-export` | C11a | no |
| C13 | Accessibility automation (axe + keyboard walkthrough) | `test/a11y-automation` | C11b | no |
| C14 | Backup/restore + trace retention + trace DB hardening | `feat/backup-retention` | C2 | no |
| C15 | Manual live-source smoke workflow | `test/live-source-smoke` | C9b, C9c | no |
| C16 | Runbook + pilot data inventory + docs truth sweep | `docs/runbook-and-truth-sweep` | all above | no |
| P5 | A3 persistent revocation, A4 adversarial suite, SNOMED/NCTS, native mobile, pen test, deployment, pilot invites, release | separate plans | — | **YES each** |

Recommended execution order: C1 → C2 → C3 → C4 → C5 → C6 → C7 → C8 → C9a → C9b → C9c → (C9 when approved) → C10 → C11a → C11b → C12 → C13 → C14 → C15 → C16.

---

## C1 — Settings module, server entry point, test isolation

**Files:** Create `src/medical_ai/settings.py`, `src/medical_ai/server.py`, `tests/test_settings.py`, `tests/test_server_entrypoint.py`. Modify `src/medical_ai/api.py` (`TRACE_DB`, `build_engine`), `src/medical_ai/access.py` (add `MEDICAL_AI_PILOT_ACCESS_FILE`, extract `parse_access_document`), `tests/conftest.py` (autouse `isolated_state_dirs`), `tests/test_pilot_access.py`, `pyproject.toml` (`[project.scripts]`, pyright include).

**Interfaces produced:**
```python
# settings.py (frozen dataclasses; strict typed)
class SettingsError(ValueError): ...
@dataclass(frozen=True) class ServerSettings: host: str="127.0.0.1"; port: int=8000; workers: int=1; log_level: str="info"; trusted_proxy_count: int=0
@dataclass(frozen=True) class StorageSettings: trace_db: Path; session_db: Path
@dataclass(frozen=True) class ConnectorSettings: ncbi_email: str|None; ncbi_api_key: str|None; http_timeout_seconds: float=20.0
@dataclass(frozen=True) class RateLimitSettings: enabled: bool=True; access_per_minute: int=10; query_per_minute: int=30   # consumed in C6
@dataclass(frozen=True) class Settings: server; storage; connectors; rate_limits; trace_hmac_key_configured: bool; access_source: Literal["json","file","missing"]
def trace_db_path(environ: Mapping[str,str]) -> Path          # never raises; used at api import
def load_settings(environ: Mapping[str,str]|None=None) -> Settings   # reads env each call; no cache
# server.py
def main(argv: Sequence[str]|None=None) -> int   # flags: --check-config ; runs uvicorn.run("medical_ai.api:app", host, port, workers=1, proxy_headers=False, server_header=False, access_log=False, log_config=None)
# access.py
def parse_access_document(document: object) -> tuple[PilotParticipant, ...]
```
Env names: `MEDICAL_AI_HOST`, `MEDICAL_AI_PORT` (1..65535), `MEDICAL_AI_WORKERS` (must be 1 until A3; otherwise `SettingsError`), `MEDICAL_AI_LOG_LEVEL` {debug,info,warning,error}, `MEDICAL_AI_TRUSTED_PROXY_COUNT` (0..2), `MEDICAL_AI_HTTP_TIMEOUT_SECONDS` (1..60), `MEDICAL_AI_PILOT_ACCESS_FILE` (exactly one of `_JSON`/`_FILE`; regular file, `O_NOFOLLOW`, no group/other bits, ≤ 1 MiB). Existing names unchanged. Server refuses to start when `MEDICAL_AI_TRACE_HMAC_KEY` is absent or < 32 bytes (engine's random fallback remains for tests only).

**Steps**
- [ ] Write failing tests: `test_settings.py` (defaults; each range/enum error; `workers=2` rejected; `_JSON`+`_FILE` conflict; `trace_db_path` absolute); `test_server_entrypoint.py` (monkeypatched `uvicorn.run` recorder receives host/port/workers=1/access_log=False; refuses without HMAC key, exit 1; `--check-config` prints redacted JSON (names/booleans only) and exit 0/1; stdout never contains the secret strings); `test_pilot_access.py` additions (`_FILE` happy path; too-broad perms → 503; symlink → 503).
- [ ] Run `python -m pytest tests/test_settings.py tests/test_server_entrypoint.py -q` → FAIL (ImportError).
- [ ] Implement `settings.py`, `server.py`, `access.py` changes, `api.py` (`TRACE_DB = str(trace_db_path(os.environ))`; `build_engine()` reads `load_settings().connectors`), `pyproject.toml` `[project.scripts] medical-ai-serve = "medical_ai.server:main"`, pyright include += `settings.py`, `server.py`.
- [ ] Add autouse fixture `isolated_state_dirs` in `tests/conftest.py`: sets `MEDICAL_AI_PILOT_SESSION_DB` to `tmp_path` and `monkeypatch.setattr(api, "TRACE_DB", str(tmp_path/"traces.sqlite3"))`; add assertion fixture that `~/.medical_ai` mtime is unchanged across the session.
- [ ] Run focused tests → PASS; run standard check sequence → all green; update manifest; write evidence README; commit per logical unit (`feat(C1): …`, `chore(C1): bind manifest`).

**Audit checklist:** `import medical_ai.api` with empty env succeeds; `medical-ai-serve --check-config` output contains no secret; `tests/test_ultrareview_regressions.py::…TRACE_DB absolute` still passes; `~/.medical_ai` untouched by the suite.

## C2 — Admin CLI

**Files:** Create `src/medical_ai/admin_cli.py`, `tests/test_admin_cli.py`. Modify `pyproject.toml` (`medical-ai-admin = "medical_ai.admin_cli:main"`, pyright include), `project_docs/RELEASE_AND_OPERATIONS.md`.

**Interfaces:** `main(argv) -> int`; every command requires `--allowlist PATH` (no default). `invite --participant-id ID --credential-id ID (--expires-at ISO8601+offset | --ttl-days N)` prints the raw token **once on stdout only**, JSON summary `{participant_id, credential_id, expires_at, token_sha256}` on stderr, appends the entry, validates via `parse_access_document`, atomic write (temp 0600 same dir, fsync, `os.replace`). `revoke --participant-id ID` (exit 1 if unknown). `rotate --participant-id ID --credential-id NEWID [--expires-at]` replaces credential_id + digest, prints new token. `list` (first 8 hex of digest only). `check` (exit 0/1). Takes effect without restart when server uses `MEDICAL_AI_PILOT_ACCESS_FILE`.

**Steps:** failing tests in `tmp_path` + `capsys` (token on stdout exactly once, absent from file and stderr; file mode 0600; after `revoke`, `authenticate_invite_token(token, load_access_config())` is `None` with `_FILE` pointing at the file; `rotate` invalidates old token; bad expiry rejected; symlinked allowlist refused) → run FAIL → implement → PASS → standard sequence → manifest → evidence README → commit.

## C3 — Container image, dependency lock, CI smoke

**Files:** Create `Dockerfile`, `deploy/docker-compose.yml` (app service only), `deploy/requirements.lock.txt`, `deploy/medical-ai.env.example`, `tests/test_deploy_assets.py`. Modify `.gitignore` (`deploy/*.env`), `scripts/check_repo_hygiene.py` (add `.env` to banned suffixes), `.github/workflows/ci.yml` (new job `container-smoke`, not required until owner adds it), `sbom/README.md`.

**Design:** multi-stage `python:3.12-slim-bookworm@sha256:<digest pinned at build time>`; `pip install -r deploy/requirements.lock.txt` then `pip install --no-deps .`; runtime user uid/gid 10001; `ENV MEDICAL_AI_HOST=0.0.0.0 MEDICAL_AI_PORT=8000 MEDICAL_AI_TRACE_DB=/var/lib/medical-ai/medical_ai_traces.sqlite3 MEDICAL_AI_PILOT_SESSION_DB=/var/lib/medical-ai/pilot_sessions.sqlite3`; `VOLUME /var/lib/medical-ai`; stdlib `HEALTHCHECK` on `/health`; `ENTRYPOINT ["medical-ai-serve"]`. Compose `app`: `read_only: true`, `tmpfs: [/tmp]`, `cap_drop: [ALL]`, `no-new-privileges`, bind mount state dir, **no host port**, `env_file` `/etc/medical-ai/medical-ai.env`. Lock file generated by `pip freeze` from a clean exact install (records transitive pins: starlette, pydantic-core, anyio, h11, click…).

**Steps:** write `test_deploy_assets.py` (Dockerfile has `USER 10001`, `HEALTHCHECK`, no `ADD`; compose app has no `ports`; hygiene rejects a tracked `deploy/x.env`) → FAIL → create assets → PASS → `docker build` locally → CI job: build; `compose config` with dummy env; run with synthetic secrets and `chown 10001` state dir; poll `/health` ≤ 30 s; unauth query → 401; `/access/session` with synthetic token → 200 (proves volume perms); `id -u` → 10001; health status healthy; `docker logs` must not contain any synthetic secret → manifest/docs → evidence README (record image digest) → commit.

## C4 — Readiness, structured logging, request id

**Files:** Create `src/medical_ai/logging_config.py`, `tests/test_observability.py`. Modify `api.py` (`GET /health/ready`, request-id middleware), `server.py` (`configure_logging()` before uvicorn), `docs/PRIVACY_ARCHITECTURE.md` (log field inventory), `project_docs/ARCHITECTURE_AND_CONTRACTS.md` (routes).

**Interfaces:** `configure_logging(level: str) -> None` (JSON lines to stderr: `ts, level, logger, event, request_id, method, path, status, duration_ms`; **never** query string, body, cookie, authorization, answer). `GET /health/ready` (public, no participant data): `{status: "ready"|"not_ready", checks: {access_config: bool, session_store: bool, trace_store: bool, policies: bool}}`, 503 when not ready. Request id: honour inbound `X-Request-ID` only when `trusted_proxy_count > 0`, else generate uuid4; echo in response header.

**Steps:** failing tests (ready → 200 when env configured, 503 and which check failed otherwise, body contains no paths; `test_logs_never_contain_request_content`: perform `/access/session` with token and a query containing synthetic identifier text, capture all `medical_ai.*` and `uvicorn*` records, assert none contains token/cookie/question/answer; request id echoed; inbound id ignored when proxy count 0) → FAIL → implement → PASS → standard sequence → manifest, pyright include += `logging_config.py` → evidence README → commit.

## C5 — Security headers

**Files:** Modify `api.py` (middleware), `tests/test_evidence_atlas_ui.py`; create `tests/test_security_headers.py`; update `project_docs/SECURITY_PRIVACY.md`.

**Design:** `Content-Security-Policy: default-src 'none'; script-src 'sha256-<hash of inline script>'; style-src 'sha256-<hash of inline style>'; connect-src 'self'; img-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'`; `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `X-Frame-Options: DENY`, `Permissions-Policy: camera=(), microphone=(), geolocation=()`; HSTS only when `trusted_proxy_count > 0` (behind TLS). Hashes computed at import from `static/index.html` and `ACCESS_PAGE` so edits never silently break CSP. `/docs` Swagger page gets its own relaxed policy (loads external assets; document that in PRIVACY_ARCHITECTURE egress inventory).

**Steps:** failing tests (headers present on `/`, `/access/session`, `/v1/evidence/query`, `/health`; CSP hash equals sha256 of current inline blocks; HSTS absent when proxy count 0) → implement → PASS → DOM script still passes → evidence → commit.

## C6 — Rate limiting

**Files:** Create `src/medical_ai/ratelimit.py`, `tests/test_ratelimit.py`. Modify `settings.py` (`RateLimitSettings` env: `MEDICAL_AI_RATE_LIMIT_ENABLED`, `_ACCESS_PER_MINUTE`, `_QUERY_PER_MINUTE`), `api.py`, `tests/conftest.py` (autouse clear of limiter caches), `deploy/medical-ai.env.example`.

**Interfaces:**
```python
@dataclass(frozen=True) class RateLimitPolicy: capacity: int; refill_per_second: float
@dataclass(frozen=True) class RateLimitDecision: allowed: bool; retry_after_seconds: int
class TokenBucketLimiter:
    def __init__(self, policy, *, clock: Callable[[], float]=time.monotonic, max_keys: int=10_000) -> None
    def acquire(self, key: str) -> RateLimitDecision     # Lock + LRU; evict full idle buckets first
def client_ip_key(request: Request, trusted_proxy_count: int) -> str   # count 0 → request.client.host; else XFF[-count], validated with ipaddress; fallback to client.host; "ip:"+sha256[:32]
def participant_key(request: Request) -> str                           # "participant:"+request.state.pilot_participant_id
```
Wiring: `/access/session` keyed by IP (capacity 10, refill 10/60); `/v1/evidence/query` keyed by participant **after** `require_pilot_participant` (capacity 10, refill 30/60). Denial: 429, body exactly `{"detail": "Too many requests"}`, headers `Retry-After`, `Cache-Control: no-store`.

**Steps:** failing tests (fake clock: capacity 3 → 4th denied, refill restores; XFF spoof ignored when count 0; count 1/2 selection; invalid IP fallback; eviction bound; API: 11th `/access/session` → 429 constant body with no token/host echo; participant A exhausted while B 200; unauthenticated query → 401 never 429; disabled flag bypass) → implement → PASS → standard sequence → manifest, pyright include += `ratelimit.py` → evidence → commit.

## C7 — Caddy TLS edge, systemd, deploy README

**Files:** Create `deploy/Caddyfile`, `deploy/medical-ai.service`, `deploy/README.md`. Modify `deploy/docker-compose.yml` (add `caddy` service: pinned `caddy:2.x` tag, ports 80/443/443udp, volumes `caddy_data`, `caddy_config`, Caddyfile ro, env `MEDICAL_AI_DOMAIN`, `MEDICAL_AI_ACME_EMAIL`), `tests/test_deploy_assets.py`, `project_docs/RELEASE_AND_OPERATIONS.md`.

**Caddyfile invariants (tested as text):** `reverse_proxy app:8000` with `header_up X-Forwarded-For {http.request.remote.host}` (overwrites client XFF), `header_up X-Request-ID {http.request.uuid}`; `request_body max_size 64KB`; HSTS header; `-Server`; access log `format filter` deleting `request>headers>Cookie`, `Authorization`, `X-Request-ID`. App env sets `MEDICAL_AI_TRUSTED_PROXY_COUNT=1`. systemd: `Type=oneshot`, `RemainAfterExit=yes`, `EnvironmentFile=/etc/medical-ai/medical-ai.env`, `ExecStartPre=/usr/bin/install -d -o 10001 -g 10001 -m 0700 /var/lib/medical-ai`, `ExecStart=docker compose … up -d --remove-orphans`, `ExecStop=… down`, `After=docker.service network-online.target`.

**Steps:** failing asset tests → create files → PASS → local `docker compose config` → README covers: host prerequisites, env file custody (root:root 0600), first start, invite issuance via C2, log locations, what is NOT authorised (no public exposure until owner deployment decision) → evidence → commit. **Deployment to a real host is not part of this chunk.**

## C8 — AU source-contract spike (docs + fixtures only)

**Files:** Create `project_docs/evidence/au-source-contract-<date>/README.md`, `tests/fixtures/au/pbs_item_sample.json`, `tests/fixtures/au/artg_entry_sample.json` (public, non-PHI, small). Modify `docs/SOURCE_MAP.md`, `docs/LICENCE_REGISTER.md`.

**Must establish, with primary-source links and access dates:** for PBS: the public PBS data API base URL, auth model (subscription key or none), schedule versioning (effective date), rate limits, licence/terms; for TGA: whether a stable machine-readable ARTG endpoint exists, or whether the adapter must consume a versioned public dataset snapshot (data.gov.au style); record ID forms (ARTG number; PBS item code), cancellation/delisting representation, and what fields are **facts** vs **narrative** (indications, restrictions are narrative → never propositions). **Do not assume a JSON API exists.** Output: a contract table per source and a go/no-go per adapter; if TGA has no stable endpoint, C9c builds against the snapshot format.

**Steps:** research → write README + fixtures → update SOURCE_MAP (status column: planned → contract recorded) → manifest (fixtures under `tests/` are mandatory) → commit. No code.

## C9a — AU routing split, fail-closed RED tests, CODEOWNERS

**Files:** Modify `planner.py`, `engine.py` (line ~110 block), `source_policy.py`, `extractor.py`, `policies/source-policy-v0.1.yaml` + mirror, `tests/conftest.py` (`FakeTGAConnector`, `FakePBSConnector`), `tests/test_planner.py`. Create `tests/test_au_routing_red.py`, `.github/CODEOWNERS` (owner on `src/medical_ai/authority*.py`, `policies/`, `src/medical_ai/policies/`). `api.build_engine` is **not** changed (runtime behaviour identical).

**Interfaces:** source-class strings `au_regulator`, `au_subsidy` (generic `regulator`, `subsidy` keep abstaining); planner: remove `pbs` from `REGULATORY_CUES`; add `AU_SUBSIDY_CUES` (pbs, pharmaceutical benefits scheme, rpbs, subsidised/co-payment/authority required/restricted benefit near medicine/listing, listed near pbs/scheme); required classes: regulatory → `["au_regulator"]` if jurisdiction AU else `["regulator"]`; subsidy likewise; both → both; intent `SUBSIDY_QUERY`, flag `AU_SUBSIDY_SOURCE_REQUIRED`; `jurisdiction_material = regulatory or subsidy`. Engine: generic class → existing `NO_AUTHORITATIVE_SOURCE` wording (keep the substring `test_vertical_slice` asserts); two AU classes → abstain "one authority per query"; AU class with no configured connector → abstain with the existing sentence (PBS variant "…for the required subsidy authority"); otherwise fall through to the connector path. `source_policy`: `au_regulator` admitted iff policy `au_regulatory_status.alpha3_allowed_sources` contains `tga_artg_register` and `source.source_type == "au_regulatory_register"` and `source.jurisdiction == "AU"`; `au_subsidy` ↔ `pbs_schedule` / `au_subsidy_schedule`. Extractor: fact sections `REGISTRY_FACT | REGISTER_FACT | SCHEDULE_FACT` only; `evidence_type` `regulatory_register_fact` / `subsidy_schedule_fact`; limitation text "registration/listing does not establish efficacy, safety or clinical suitability".

**RED tests (must stay red until C9):** `test_tga_claim_never_renders_before_kernel_mapping` (engine with FakeTGA → `INFLUENCE_DENIED`, `claims == []`, verifier `PASS` present in trace, every decision has `EVIDENCE_AUTHORITY_UNKNOWN` + `INFORMATION_HANDLING_AUTHORITY_UNKNOWN`); `test_resolver_leaves_au_classes_unmapped`; `test_no_au_connector_keeps_abstention`; `test_us_jurisdiction_never_routes_to_au_connector`; `test_two_authorities_abstain`; `test_pbs_source_rejected_for_regulatory_plan`; `test_indication_text_is_never_a_proposition`.

**Steps:** write tests → FAIL → implement → PASS (the "never renders" tests pass *because* the kernel denies) → standard sequence → manifest/mirror → SOURCE_MAP → evidence README → commit. PR text must state: "AU claims fail closed at the authority gate by design; enabling requires owner-approved C9."

## C9b — PBSConnector (disabled by default)

**Files:** Create `src/medical_ai/connectors/pbs.py`, `tests/test_pbs_connector.py`. Modify `settings.py` (`MEDICAL_AI_CONNECTOR_PBS_ENABLED=false`, `MEDICAL_AI_PBS_BASE_URL`, `MEDICAL_AI_PBS_SUBSCRIPTION_KEY` presence flag only), `api.py` (`build_engine` registers `au_subsidy` only when enabled), `docs/SOURCE_MAP.md`, `docs/PRIVACY_ARCHITECTURE.md` (egress host), `docs/LICENCE_REGISTER.md`, `deploy/medical-ai.env.example`.

**Interface:** `class PBSConnector: name="pbs-data-api"; version; source_class="au_subsidy"; evidence_approved=True; phi_approved=False; __init__(*, base_url, subscription_key: str|None, timeout)`; `search_and_fetch(query, limit)` → `SourceRecord(source_type="au_subsidy_schedule", jurisdiction="AU", authority="Pharmaceutical Benefits Scheme / Australian Government Department of Health", identifiers={"PBS_ITEM": code}, version_record keyed by schedule effective date (absent → `FreshnessState.UNKNOWN`), PHI PUBLIC)`; passages: `SCHEDULE_FACT` templated facts with `locator` (item code, listing status, schedule effective date, restriction *category* only); restriction/indication narrative stored as `RESTRICTION_TEXT` passage, never a fact. Delisted items → `superseded=True`. Query normalisation via `normalize_search_query`; the subscription key goes in a header, never in URL or logs.

**Steps:** failing parser tests against `tests/fixtures/au/pbs_item_sample.json` (fields, locator, version record digest, UNKNOWN without date, delisted → superseded, narrative not in facts; mocked httpx: key only in header; network error surfaces as exception so engine yields `SOURCE_UNAVAILABLE`) → implement → PASS → `test_au_routing_red` still red-by-design → standard sequence → manifest/docs → evidence → commit.

## C9c — TGAConnector (disabled by default)

Same shape as C9b against the C8-established contract: `connectors/tga.py`, `class TGAConnector: source_class="au_regulator"`, `source_type="au_regulatory_register"`, `identifiers={"ARTG": number}`, `REGISTER_FACT` passages (ARTG number, entry status, sponsor name, start date, product category), `INDICATION_TEXT` narrative never a fact, cancelled entries → `superseded=True`, version record keyed by the register snapshot/last-updated date. Env `MEDICAL_AI_CONNECTOR_TGA_ENABLED=false`, base URL/snapshot path. Tests in `tests/test_tga_connector.py` against `tests/fixtures/au/artg_entry_sample.json`.

## C9 — Kernel enablement for AU authority (**OWNER-GATED**)

**Precondition:** written owner approval on the PR + CODEOWNERS review; must reference the Tranche A contract pin in `project_docs/evidence/tranche-a-contract-20261105/`.

**Files:** Modify `src/medical_ai/authority.py` (`AuthorityPurpose += AU_REGULATORY_STATUS_LOOKUP, AU_SUBSIDY_STATUS_LOOKUP`), `authority_resolver.py` (`_SOURCE_CLASS["au_regulator"]=SourceClass.TGA`, `["au_subsidy"]=SourceClass.PBS`; `_CLAIM_TYPE` → `AU_REGULATORY_APPROVAL` / `AU_SUBSIDY_STATUS`; `_COMPONENT` → `tga_artg_public_connector` / `pbs_public_connector`; `_PURPOSE` → the two new purposes), `policies/evidence-authority-v0.2.yaml` (revision 2: ALLOW `ea-tga-artg-status-retrieve` {AU_REGULATORY_APPROVAL, TGA, jurisdiction AU, RETRIEVE_PUBLIC_EVIDENCE, CURRENT; [PROVENANCE, SOURCE_VERSION, REGISTER_FIELD_PRESENT]}, ALLOW `ea-pbs-subsidy-status-retrieve`; DENY `ea-tga-not-efficacy`, `ea-pbs-not-efficacy`, `ea-pbs-not-regulatory`, `ea-tga-not-subsidy`, `ea-pubmed-not-subsidy`, `ea-ctgov-not-subsidy`; existing HIGH/retracted/superseded/unknown DENY rules untouched), `information-handling-v0.2.yaml` (ALLOW `ih-tga-public-register`, `ih-pbs-public-schedule`), `data-plane-transitions-v0.2.yaml` (ALLOW `dp-evidence-retrieve-au-regulatory`, `dp-evidence-retrieve-au-subsidy`), mirrors, `renderer.py` (citation labels `ARTG <n>` / `PBS item <code>`, AU limitation footer; new kw-only `au_authority: bool`, still only called from engine), `tests/test_au_routing_red.py` → flip to `tests/test_au_authority_enablement.py`, `tests/test_authority_resolver.py`, `tests/test_authority_policy_compile.py`, `project_docs/ALPHA3_A1_POLICY_REVIEW_CASES.md`, `static/index.html` directory text, STATUS, SOURCE_MAP, KNOWN_LIMITATIONS.

**Digest recompute:** same method as `tests/test_authority_policy_compile.py::_digest_for`; paste; mirror bytes; manifest both copies.

**Tests:** positive control (`ANSWER_SUPPORTED_WITH_QUALIFICATIONS`, decision evidence authority `APPROVED` from resolver); negatives: PBS source for regulatory plan denied (`WRONG_REGULATOR_FOR_CLAIM`), TGA claim with jurisdiction US → no rule → UNKNOWN → denied, cancelled entry → `SOURCE_OUTDATED`, dose question → `HIGH_CONSEQUENCE_VERIFICATION_FAILED`, missing freshness → denied; all A1 digests verify.

## C10 — Source directory endpoint

**Files:** Create `src/medical_ai/api_models.py`, `src/medical_ai/source_directory.py`, `tests/test_source_directory.py`. Modify `authority_resolver.py` (**read-only accessor only** `mapped_source_classes() -> frozenset[str]`; no mapping change), `api.py` (`GET /v1/sources`, protected), `static/index.html` (directory tab fetches `/v1/sources`, validates `Array.isArray(data.entries)`, falls back to static cards; keep "TGA and PBS"/"Not connected" fallback text), `scripts/evidence_atlas_dom.cjs`, `project_docs/UI_UX_AND_ROUTES.md`.

**Schema:** `SourceDirectoryEntry{source_class, connector_name, connector_version, authority, plane: "EVIDENCE", jurisdiction, evidence_approved, phi_approved, configured, authority_mapped, status: "live"|"configured_fail_closed"|"not_connected", licence_class, limitation}`; `PlannedSourceEntry{name, plane, note}`; `SourceDirectory{generated_at, engine_version, influence_policy_version, authority_policy_digests: dict[str,str], entries, planned}`. `status` is computed, never asserted: `live` iff configured **and** mapped.

**Steps:** failing tests (FakeTGA configured before C9 → `configured_fail_closed`; PubMed → `live`; unauth → 401; digests equal `compile_authority_policy(...).policy_digest`) → implement → PASS → DOM test for fallback → standard sequence → manifest, pyright include += `api_models.py`, `source_directory.py` → evidence → commit.

## C11a — Answer-state catalogue + evidence-dimension summary

**Files:** Create `src/medical_ai/answer_states.py`, `tests/test_answer_states.py`. Modify `api.py` (`GET /v1/answer-states`, protected), `static/index.html` (state banner shows headline/explanation/next_action; evidence-dimension panel over existing fields: authority, jurisdiction vs requested, evidence type, freshness, verification + entailment, authorization), `scripts/evidence_atlas_dom.cjs`, `project_docs/EVIDENCE_ATLAS_UI.md`.

**Schema:** `AnswerStateExplanation{status: AnswerStatus, headline, explanation, next_action, supported: bool}`; `AnswerStateCatalogue{version, entries}`. Test: every `AnswerStatus` member has an entry; no entry text contains "verified", "validated", "approved for clinical", "safe". Copy must satisfy North Star questions 1, 2 and 6 (what is shown, what evidence says, next safe action).

## C11b — Mode-aware presentation

Modify `static/index.html` + DOM script: student mode leads with "why this is supported" (claim → passage → source), clinician mode leads with jurisdiction + freshness + applicability rows, researcher mode leads with identifiers + export (C12). **Invariant test:** the set of rendered `claim_text` is identical across the three modes; modes never add or remove claims. Update `EVIDENCE_ATLAS_UI.md`, `UI_UX_AND_ROUTES.md`.

## C12 — Trace endpoint + researcher export

**Files:** Modify `api.py` (`GET /v1/evidence/trace/{trace_id}`, protected, uuid path regex, reuse `SQLiteTraceStore(TRACE_DB).get`), `api_models.py` (`TraceRecordView` with exactly the 21 keys `SQLiteTraceStore.save` persists; parity test against `save`'s payload keys), `static/index.html` (researcher export: Blob of the validated response + `{exported_at, ui_version}`, filename `medical-ai-answer-<trace_id>.json`), DOM script (export deep-equals response; `use_notice` present), `project_docs/ARCHITECTURE_AND_CONTRACTS.md`. Create `tests/test_trace_endpoint.py` (404 constant body; `no-store`; unauth 401; returned payload contains no question text).

## C13 — Accessibility automation

**Files:** Create `scripts/evidence_atlas_a11y.cjs` (axe-core pinned version over access page + workbench in both colour schemes; keyboard walkthrough: tab order through tabs → form → submit → Passport → sign out; focus visible assertions; zoom 200% no horizontal scroll). Modify `.github/workflows/evidence-atlas-visual.yml` (run it; upload report). Evidence README records violations found/fixed; **no WCAG conformance claim**; real AT testing stays unproven.

## C14 — Backup, retention, trace DB hardening

**Files:** Modify `admin_cli.py` (`backup --state-dir DIR --out FILE` uses `sqlite3.Connection.backup` for both DBs into a tar with 0600; `restore`; `purge-traces --older-than-days N` ), `trace_store.py` (`delete_older_than(cutoff: datetime) -> int`; create file 0600 with `O_NOFOLLOW` like session store), tests. Create `deploy/medical-ai-purge.service` + `.timer`. Update `RELEASE_AND_OPERATIONS.md`, `PRIVACY_ARCHITECTURE.md` (retention default: traces 90 days, documented as proposal pending owner decision).

## C15 — Live-source smoke workflow (manual dispatch)

**Files:** Create `src/medical_ai/evals/live_source_smoke.py` (CLI; synthetic non-PHI queries per configured connector; emits JSON `{connector, status, http_status_class, record_count, elapsed_ms}`; never prints passages), `evals/live/smoke-cases-v0.1.json`, `.github/workflows/live-source-smoke.yml` (`workflow_dispatch` only; secrets from repo env; artifact upload), tests for the CLI with mocked connectors. Not a required check. Records go to evidence READMEs as `executed` live evidence, never as validation.

## C16 — Runbook, pilot data inventory, truth sweep

**Files:** Create `project_docs/RUNBOOK.md` (start/stop, upgrade with image digest, rollback to previous digest, secret rotation, invite lifecycle, incident + quarantine of accidental PHI, backup/restore drill), `docs/PILOT_DATA_INVENTORY.md` (per data class from the pilot brief: purpose, location, access, retention, deletion). Update `SOURCE_MAP.md`, `KNOWN_LIMITATIONS.md`, `PRIVACY_ARCHITECTURE.md` (egress inventory now: NCBI, ClinicalTrials.gov, PBS host, TGA host, Swagger CDN), `ARCHITECTURE_AND_CONTRACTS.md` (full API surface), `STATUS.md`, `PROJECT_INDEX.md`, manifest. Every statement classified with the evidence vocabulary.

## Phase 5 — owner-gated follow-ons (not in this plan's build scope)

A3 persistent/transactional revocation ledger (needed before `MEDICAL_AI_WORKERS>1`); A4 adversarial assurance suite; SNOMED CT-AU/AMT via NCTS (licence first); native iOS/Android; independent pen test (isolated synthetic environment + rules of engagement); Australian hosting selection + deployment of a pinned digest; pilot invitations; clinically reviewed evidence-fidelity benchmarks; regulatory/privacy professional review; release decision. Each gets its own plan and owner decision record in `docs/RELEASE_READINESS.md`.

## Review focus (failure modes no single chunk's tests cover; each pinned to its owner)

1. **Request content reaches logs or the edge** (C4, C7) → `tests/test_observability.py::test_logs_never_contain_request_content`; `tests/test_deploy_assets.py::test_caddyfile_deletes_cookie_and_authorization_headers`.
2. **An AU claim renders before owner-approved C9** (C9a–c) → `tests/test_au_routing_red.py::test_tga_claim_never_renders_before_kernel_mapping`, `::test_resolver_leaves_au_classes_unmapped`; CODEOWNERS; policy digest tests.
3. **Wrong authority or jurisdiction leakage after C9** → `tests/test_au_authority_enablement.py::test_pbs_source_denied_for_regulatory_claim`, `::test_tga_claim_denied_outside_au_jurisdiction`, `::test_indication_text_is_never_a_proposition`, `::test_cancelled_artg_entry_is_source_outdated`.
4. **Proxy-trust / rate-limit misconfiguration** (C6, C7) → `tests/test_ratelimit.py::test_spoofed_forwarded_for_ignored_without_trusted_proxy`, `::test_unauthenticated_query_is_401_not_429`, `::test_429_body_is_constant_and_echoes_nothing`; `tests/test_settings.py::test_workers_above_one_rejected`.
5. **UI or directory overstating capability** (C10–C12) → `tests/test_source_directory.py::test_status_derives_from_resolver_mapping`; `tests/test_answer_states.py::test_every_status_has_entry_and_no_overclaiming_words`; DOM tests: export deep-equals response; claims identical across modes.

---

## Follow-up prompt for the coding agent

> You are the Medical AI coding agent for `Subzteveo/Medical-AI`. Read, in order: `AGENTS.md`, `README.md`, `project_docs/NORTH_STAR.md`, `project_docs/PROJECT_INDEX.md`, `project_docs/STATUS.md`, `project_docs/DEVELOPMENT_WORKFLOW.md`, `docs/INTENDED_USE.md`, then the build plan `project_docs/plans/2026-11-11-full-app-build-plan.md` and `project_docs/plans/KILO_CLAW_AUDIT_PROTOCOL.md`.
>
> Execute the plan **one chunk at a time, in the recommended order, starting with C1**. For each chunk: create the named branch from the latest `main`; follow the chunk's Files, Interfaces and Steps exactly; write the failing test first and show it failing; implement the narrowest code that makes it pass; run the standard check sequence from the plan and paste the real pass/fail counts; update the checksum manifest and policy mirrors by hand; write the chunk's `project_docs/evidence/<topic>-<YYYYMMDD>/README.md` with the five headings and the evidence vocabulary; add the dated STATUS.md banner line; open a **draft PR** using the repository template with exact head SHA, checks run, checks not run, safety/privacy impact. Then **stop and report**: base/head SHA, work done, checks with counts, blockers, gate classification (PASS / FAIL / BLOCKED / UNVERIFIED), "awaiting Kilo Claw audit and owner review". Do not start the next chunk until the audit verdict and merge are recorded.
>
> Binding rules: a model is never evidence; never fill missing facts from memory; preserve fail-closed behaviour and the evidence/PHI authority split; never edit `src/medical_ai/authority.py`, `authority_policy.py`, the resolver mapping dicts or any `*-v0.2.yaml` outside chunk C9, and start C9 only with written owner approval on its PR; never weaken or skip a test to go green; never commit `.env*`, keys, databases, binaries, real tokens or any patient-identifying text; logs and error bodies must never contain question text, tokens, cookies or answers; use only the evidence words proposed/generated/inspected/executed/passed/verified/blocked/unproven and never describe generated code as executed, a passing run as validation, or an image as deployed. Deployment to a host, pilot invitations, pen testing, SNOMED, A3/A4 and release are outside your authority: list them as gated when relevant and stop.
>
> If a chunk's precondition is missing (an endpoint contract from C8 is unresolved, a required file differs from the plan, CI is red on `main`), do not improvise: record it as BLOCKED with the exact evidence and stop at that decision gate.
