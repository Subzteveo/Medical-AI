# Dependency / SBOM note — alpha2

`pyproject.toml` is the authoritative direct dependency declaration for this engineering alpha. A formal machine-generated SBOM for the exact distributable has not yet been produced, signed or independently verified.

Direct runtime dependency ranges:
- FastAPI >=0.128,<1
- httpx >=0.28,<1
- Pydantic >=2.13,<3
- Uvicorn >=0.35,<1

Development dependency ranges:
- pytest >=9,<10
- pytest-asyncio >=1,<2

A release-grade SBOM should be generated from the frozen build environment/artifact before any external distribution. This note must not be treated as a software-composition or vulnerability scan.

## Container dependency lock (C3, 13 November 2026)

`deploy/requirements.lock.txt` pins the 17 runtime packages (direct and transitive) with exact versions for the container build. It is a hand-curated pin list taken from a clean `pip install -e .` resolution; it carries no hashes, was not produced by a lock generator and has not been scanned for vulnerabilities. The container base image is pinned by digest in the `Dockerfile` (`PYTHON_IMAGE`). Neither is a signed or independently verified SBOM, and no image has been built from them yet outside CI.
