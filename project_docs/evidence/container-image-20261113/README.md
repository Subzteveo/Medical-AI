# C3 — container image, dependency lock and CI smoke — 13 November 2026

**Plan:** [full application build plan](../../plans/2026-11-11-full-app-build-plan.md), chunk C3
**Base `main`:** `f292523` (C2 merged via PR #60)
**Recorded:** 13 November 2026
**Disposition:** **generated + statically tested locally.** The image build and container run are **unproven** until the `container-smoke` CI job executes them. Not verified, not audited, not merged, not deployed. Clinical, privacy and release posture unchanged (**NO-GO**).

Engineering evidence only. The head SHA and exact-head CI are read from the pull request, not from this file. No Kilo Claw audit record exists for C1, C2 or this chunk.

## 1. Preconditions and the gap C3 closes

C1 gave the server a start command and C2 an invitation tool, but there was no reproducible way to package and run the application: no image, no pinned dependency set, no hardened runtime definition, and nothing in CI that actually started the service.

## 2. What was implemented

- `Dockerfile` — two-stage build. Base image `python:3.12-slim-bookworm` pinned by digest `sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df` (digest read from the registry on 13 Nov 2026). The build stage installs `deploy/requirements.lock.txt`, then the project with `--no-deps`. The runtime stage runs as uid/gid 10001, declares `/var/lib/medical-ai` as the state volume, has a `/health` HEALTHCHECK and `ENTRYPOINT ["medical-ai-serve"]`. No `ADD`, no network fetch beyond the lock install, no secrets in `ENV`.
- `.dockerignore` — default-deny; only `src`, `pyproject.toml`, `README.md` and the lock enter the build context (no tests, docs, `.git`, `.env`, policies outside the package).
- `deploy/requirements.lock.txt` — 17 exact pins (direct dependencies equal `pyproject.toml`; transitive pins included; no dev packages).
- `deploy/docker-compose.yml` — single service, no published host ports, read-only root filesystem, tmpfs `/tmp`, all capabilities dropped, `no-new-privileges`, user 10001, environment from `/etc/medical-ai/medical-ai.env`, state volume bind. The reverse proxy and systemd unit arrive in C7.
- `deploy/medical-ai.env.example` — documented variable list with empty secret values. Named so it cannot be mistaken for a real `.env`.
- `scripts/check_repo_hygiene.py` and `.gitignore` — any tracked `*.env` file other than the `.example` is now rejected; `deploy/*.env` is ignored.
- `.github/workflows/ci.yml` — independent job `container-smoke` (not a dependency of the existing job). It generates synthetic secrets at run time (masked), mirrors the host layout, builds the image, starts the container and checks: `/health` responds; an unauthenticated query returns 401; an invitation token exchanges for a session (200); the process uid is 10001; the root filesystem is not writable; no host port is published; the container reports `healthy`; no synthetic secret appears in the container logs. Teardown always runs.
- `tests/test_deploy_assets.py` — 21 static tests over all of the above.

Not changed: engine, renderer, influence controller, connectors, `authority*.py`, every policy file, API routes, the UI.

## 3. Behaviour exercised

Red before implementation: all 21 asset tests failed while the files were absent. After implementation they pass. They are static checks; they prove the files say what is required, not that the image builds or the container behaves.

The embedded smoke script was syntax-checked with `bash -n` and both of its Python heredocs were compiled. One defect was found and fixed during that review: the invitation token was exported to the container with a bare `-e INVITE_TOKEN`, which would have passed nothing from a non-exported shell variable; it is now passed explicitly.

## 4. Local check results at the working tree (pre-merge)

Python 3.13 locally (CI uses 3.12). See the pull request for the exact-head runs.

- C3 asset tests: **21 passed**.
- Full results of the standard check sequence are recorded in the pull request description.

## 5. Not done / still gated

- **Image build and container run: unproven.** No Docker daemon was available in the authoring environment. The first execution is the `container-smoke` CI job; if it fails, the failure is the next unresolved item, not a reason to weaken the check.
- The lock is hand-curated, has no hashes and is not vulnerability-scanned; no signed SBOM, no image signing, no registry push.
- Local Python 3.13 versus image Python 3.12: the lock was resolved on 3.13; any 3.12-only resolution difference would appear in the CI build.
- TLS, reverse proxy, systemd, host hardening: C7. Backup and retention: C14. Deployment itself is owner-gated.
- Kilo Claw audit and owner review outstanding. **NO-GO unchanged.**
