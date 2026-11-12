# C2 — `medical-ai-admin` invitation tool — 12 November 2026

**Plan:** [full application build plan](../../plans/2026-11-11-full-app-build-plan.md), chunk C2
**Base `main`:** `bec3a066ae7d796d03c1ef7f8d2339d5ffedc78d` (C1 merged via PR #59)
**Recorded:** 12 November 2026, Australia/Darwin
**Disposition:** **generated + executed + passed locally.** Not verified, not audited, not merged, not deployed. Clinical, privacy and release posture unchanged (**NO-GO**).

Engineering evidence only. The head SHA and exact-head CI are read from the pull request, not from this file. No Kilo Claw audit record exists for C1 or for this chunk at the time of writing.

## 1. Preconditions and the gap C2 closes

C1 let the server read the pilot allowlist from an owner-only file, re-read on every request. There was no tool to maintain that file: an operator had to generate a token, compute its SHA-256 digest and hand-edit JSON, with nothing preventing a broadly readable file, a duplicate credential or a token left in shell history or the file itself.

## 2. What was implemented

- `src/medical_ai/admin_cli.py` — `medical-ai-admin`, strictly typed. Every command requires `--allowlist PATH`; there is no default path.
  - `invite` adds a participant and prints a new 256-bit token once on standard output. A JSON summary (participant id, credential id, expiry, digest) goes to standard error. The token is never written to the file, to standard error or into an error message.
  - `revoke` marks a participant revoked (exit 1 if unknown; idempotent).
  - `rotate` replaces the credential id and digest, clears the revoked flag, keeps the expiry unless a new one is given, and requires a credential id different from the current one, because existing browser sessions are bound to the credential id.
  - `list` shows participant id, credential id, expiry, state and the first 8 hex characters of the digest.
  - `check` validates the file and exits 0 or 1.
- Reads reuse the C1 fail-closed reader (no symlink, regular file, owner-only, at most 1 MiB). A dangling symlink is refused instead of written through. Every write is validated with `parse_access_document` first and then replaces the file atomically: a mode 0600 temporary file in the same directory, `fsync`, `os.replace`.
- `src/medical_ai/access.py` — two thin public wrappers, `read_access_file` and `parse_expiry`, over existing private helpers. No behaviour change.
- `pyproject.toml` — `[project.scripts] medical-ai-admin`; the module added to the strict Pyright include.
- `tests/test_admin_cli.py` — 27 cases. `tests/test_server_entrypoint.py` — the subprocess snippet now lives in a named variable (readability finding from the code-quality bot on PR #59; no behaviour change).

Not changed: engine, renderer, influence controller, connectors, `authority.py`, `authority_policy.py`, `authority_resolver.py`, every policy file, the API routes, the UI.

## 3. Behaviour exercised

Red before implementation: `tests/test_admin_cli.py` failed at collection (module absent).

Deterministic tests after implementation cover: token on standard output exactly once and absent from standard error and the file; file mode 0600 after every write; an issued token authenticating through `load_access_config()` and through the API with a Bearer header; appending a second participant; explicit expiry recorded; offset-less, unparseable and out-of-range expiry rejected without creating the file; duplicate participant, duplicate credential and malformed ids leaving the file byte-identical; revoke blocking the token without a restart; unknown participant exit 1; rotate invalidating the old token, accepting the new one, restoring a revoked participant and keeping the expiry; rotate refusing the same credential id; `list` showing no token and no full digest; `check` exit codes; symlinked, dangling-symlink and group-readable allowlists refused; missing parent directory failing cleanly; no temporary files left behind; missing `--allowlist` exiting 2.

Manual smoke on the working tree with synthetic values only, against a running `medical-ai-serve` using the same file: invite produced a mode 600 file; session exchange with the token returned 200; after `revoke` the same token returned 401 with no restart; after `rotate` the old token returned 401 and the new token 200; neither token appeared in the server log or the allowlist file.

## 4. Local check results at the working tree (pre-merge)

Clean exact-pinned `.[dev]` environment, Python 3.13 locally (CI uses 3.12):

- source checksum manifest: **passed** (126 entries; was 123);
- repository hygiene: **passed**;
- strict Pyright including `admin_cli.py`: **0 errors, 0 warnings**;
- influence-boundary source guard: **passed** (8 authoritative files, list unchanged);
- deterministic pytest suite: **469 passed, 1 warning** (was 442; +27);
- Alpha3 engineering harness CLI: ran to completion, exit 0 (blocked and unproven cases unchanged);
- compile, import smoke, package policy parity: **passed**.

## 5. Not done / still gated

- The tool manages a file; it does not deliver tokens to participants, record enrolment or consent, or verify identity, age or location. Those operating procedures remain unresolved in `docs/PILOT_OPERATING_BOUNDARY_AND_REVIEW_BRIEF.md`.
- Concurrent runs of the tool are not locked against each other; the last atomic replace wins. One operator at a time.
- Backup, restore and trace retention commands are chunk C14.
- Kilo Claw audit and owner review are outstanding for C1 and C2. Exact-head CI is read from the pull request.
- Issuing real invitations, deployment, pen testing and release remain separately owner-gated. **NO-GO unchanged.**
