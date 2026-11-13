"""Static checks on the container and deployment assets (chunk C3).

These tests read files only. They prove the shipped assets keep their security
shape; they do not build or run an image. Image build and the running-container
smoke are exercised by the ``container-smoke`` CI job.
"""

from __future__ import annotations

import importlib.util
import re
import tomllib
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE = ROOT / "Dockerfile"
DOCKERIGNORE = ROOT / ".dockerignore"
COMPOSE = ROOT / "deploy" / "docker-compose.yml"
LOCK = ROOT / "deploy" / "requirements.lock.txt"
ENV_EXAMPLE = ROOT / "deploy" / "medical-ai.env.example"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
GITIGNORE = ROOT / ".gitignore"

PIN = re.compile(r"^(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)==(?P<version>[0-9][A-Za-z0-9._+!-]*)$")


def _normalise(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _dockerfile_instructions() -> list[str]:
    """Logical Dockerfile instructions with continuations joined and comments dropped."""
    logical: list[str] = []
    pending = ""
    for raw in DOCKERFILE.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if not pending and (not line.strip() or line.lstrip().startswith("#")):
            continue
        if line.endswith("\\"):
            pending += line[:-1] + " "
            continue
        logical.append((pending + line).strip())
        pending = ""
    return logical


def _compose_app() -> dict:
    document = yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))
    assert isinstance(document, dict)
    app = document["services"]["app"]
    assert isinstance(app, dict)
    return app


# ---------------------------------------------------------------- Dockerfile


def test_dockerfile_runs_as_pinned_non_root_user():
    instructions = _dockerfile_instructions()
    users = [line.split(None, 1)[1] for line in instructions if line.upper().startswith("USER ")]
    assert users, "Dockerfile must set a USER"
    assert users[-1].split(":")[0] == "10001"


def test_dockerfile_base_image_is_digest_pinned():
    text = DOCKERFILE.read_text(encoding="utf-8")
    assert re.search(r"python:3\.12-slim-bookworm@sha256:[0-9a-f]{64}", text)
    for instruction in _dockerfile_instructions():
        if instruction.upper().startswith("FROM "):
            image = instruction.split()[1]
            assert image.startswith("${") or "@sha256:" in image or image in {"build", "runtime"}, (
                f"unpinned base image: {image}"
            )


def test_dockerfile_has_healthcheck_entrypoint_and_state_volume():
    instructions = _dockerfile_instructions()
    upper = [line.upper() for line in instructions]
    assert any(line.startswith("HEALTHCHECK ") for line in upper)
    assert 'ENTRYPOINT ["medical-ai-serve"]' in instructions
    assert any(line.startswith("VOLUME ") and "/var/lib/medical-ai" in line for line in instructions)
    assert any("/health" in line for line in instructions if line.upper().startswith("HEALTHCHECK "))


def test_dockerfile_never_uses_add_or_remote_install_shortcuts():
    for instruction in _dockerfile_instructions():
        verb = instruction.split(None, 1)[0].upper()
        assert verb != "ADD", instruction
        assert "curl " not in instruction and "wget " not in instruction, instruction
        assert "| sh" not in instruction and "| bash" not in instruction, instruction


def test_dockerfile_installs_locked_dependencies_then_package_without_dependencies():
    runs = [line for line in _dockerfile_instructions() if line.upper().startswith("RUN ")]
    joined = "\n".join(runs)
    assert "-r deploy/requirements.lock.txt" in joined
    assert "pip install --no-deps ." in joined
    assert joined.index("-r deploy/requirements.lock.txt") < joined.index("pip install --no-deps .")


def test_dockerfile_sets_state_locations_and_listens_on_all_interfaces_inside_container_only():
    envs = " ".join(line for line in _dockerfile_instructions() if line.upper().startswith("ENV "))
    assert "MEDICAL_AI_HOST=0.0.0.0" in envs
    assert "MEDICAL_AI_PORT=8000" in envs
    assert "MEDICAL_AI_TRACE_DB=/var/lib/medical-ai/medical_ai_traces.sqlite3" in envs
    assert "MEDICAL_AI_PILOT_SESSION_DB=/var/lib/medical-ai/pilot_sessions.sqlite3" in envs
    # No secret may be baked into an image layer.
    for name in ("HMAC_KEY", "SESSION_SECRET", "API_KEY", "ACCESS_JSON", "TOKEN"):
        assert name not in envs


def test_dockerfile_never_copies_tests_docs_or_secrets_into_the_image():
    copies = [line for line in _dockerfile_instructions() if line.upper().startswith("COPY ")]
    for line in copies:
        assert not re.search(r"\b(tests|project_docs|docs|\.git|\.env)\b", line), line
    ignore = DOCKERIGNORE.read_text(encoding="utf-8").splitlines()
    assert "**" in ignore or "*" in ignore, ".dockerignore must default-deny the build context"
    for allowed in ("!src", "!pyproject.toml", "!README.md", "!deploy/requirements.lock.txt"):
        assert allowed in ignore


# ------------------------------------------------------------------- compose


def test_compose_app_has_no_published_host_port():
    app = _compose_app()
    assert "ports" not in app


def test_compose_app_is_hardened():
    app = _compose_app()
    assert app["read_only"] is True
    assert "/tmp" in app["tmpfs"]
    assert app["cap_drop"] == ["ALL"]
    assert "no-new-privileges:true" in app["security_opt"]
    assert str(app["user"]) == "10001:10001"
    assert app.get("privileged") is not True
    assert "cap_add" not in app
    assert app.get("network_mode") != "host"


def test_compose_app_reads_secrets_from_an_out_of_repository_env_file_and_mounts_state():
    app = _compose_app()
    assert app["env_file"] == "/etc/medical-ai/medical-ai.env" or app["env_file"] == [
        "/etc/medical-ai/medical-ai.env"
    ]
    assert any(str(volume).endswith(":/var/lib/medical-ai") for volume in app["volumes"])
    for volume in app["volumes"]:
        assert "docker.sock" not in str(volume)
    text = COMPOSE.read_text(encoding="utf-8")
    for secret_name in ("HMAC_KEY", "SESSION_SECRET", "API_KEY"):
        assert not re.search(rf"{secret_name}\s*[:=]\s*\S", text), secret_name


# ----------------------------------------------------------------- lock file


def _lock_pins() -> dict[str, str]:
    pins: dict[str, str] = {}
    for number, raw in enumerate(LOCK.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = PIN.fullmatch(line)
        assert match, f"lock line {number} is not an exact name==version pin: {line!r}"
        name = _normalise(match["name"])
        assert name not in pins, f"duplicate lock entry: {name}"
        pins[name] = match["version"]
    return pins


def test_lock_file_is_exact_pins_only_and_covers_direct_dependencies():
    pins = _lock_pins()
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    for requirement in project["dependencies"]:
        match = PIN.fullmatch(requirement)
        assert match, f"direct dependency is not exact-pinned: {requirement}"
        assert pins[_normalise(match["name"])] == match["version"], requirement
    # Transitive pins are what make the image reproducible.
    for transitive in ("starlette", "pydantic-core", "anyio", "h11", "click"):
        assert transitive in pins


def test_lock_file_excludes_development_and_project_packages():
    pins = _lock_pins()
    for name in ("pytest", "pytest-asyncio", "pyright", "medical-ai-evidence-workbench"):
        assert name not in pins


# --------------------------------------------------------------- env example


def _env_example_assignments() -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in ENV_EXAMPLE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        name, _, value = line.partition("=")
        values[name.strip()] = value.strip()
    return values


def test_env_example_has_the_expected_name_and_no_secret_values():
    assert ENV_EXAMPLE.name == "medical-ai.env.example"
    assert not (ROOT / "deploy" / ".env.example").exists()
    values = _env_example_assignments()
    for secret_name in (
        "MEDICAL_AI_TRACE_HMAC_KEY",
        "MEDICAL_AI_PILOT_SESSION_SECRET",
    ):
        assert values[secret_name] == "", f"{secret_name} must be empty in the example"
    for optional_secret in ("NCBI_API_KEY", "NCBI_EMAIL"):
        assert values.get(optional_secret, "") == ""
    assert "MEDICAL_AI_PILOT_ACCESS_JSON" not in values, "invitations belong in the allowlist file"


def test_env_example_names_are_all_known_settings():
    from medical_ai import access, settings

    known = {
        value
        for module in (settings, access)
        for name, value in vars(module).items()
        if name.endswith("_ENV") and isinstance(value, str)
    }
    known |= {"NCBI_EMAIL", "NCBI_API_KEY"}
    unknown = set(_env_example_assignments()) - known
    assert not unknown, f"env example names not read by the application: {sorted(unknown)}"


def test_env_example_points_state_and_allowlist_at_the_container_volume():
    values = _env_example_assignments()
    assert values["MEDICAL_AI_PILOT_ACCESS_FILE"].startswith("/var/lib/medical-ai/")
    assert values["MEDICAL_AI_WORKERS"] == "1"
    assert values["MEDICAL_AI_PILOT_COOKIE_SECURE"] == "true"


# ------------------------------------------------------------------- hygiene


def _load_hygiene_module():
    spec = importlib.util.spec_from_file_location(
        "check_repo_hygiene", ROOT / "scripts" / "check_repo_hygiene.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("name", ["deploy/medical-ai.env", "deploy/prod.env", "secrets/x.env"])
def test_hygiene_rejects_tracked_env_files(name, monkeypatch, capsys):
    hygiene = _load_hygiene_module()
    monkeypatch.setattr(hygiene, "tracked_paths", lambda: [name])
    assert hygiene.main() == 1
    assert "Forbidden tracked artifact" in capsys.readouterr().err


def test_hygiene_accepts_the_env_example_name(monkeypatch, capsys):
    hygiene = _load_hygiene_module()
    monkeypatch.setattr(hygiene, "tracked_paths", lambda: ["deploy/medical-ai.env.example"])
    assert hygiene.main() == 0


def test_gitignore_blocks_deploy_env_files_but_not_the_example():
    lines = GITIGNORE.read_text(encoding="utf-8").splitlines()
    assert "deploy/*.env" in lines


# ------------------------------------------------------------------------ CI


def test_ci_has_a_container_smoke_job_that_is_independent_of_the_main_job():
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    jobs = workflow["jobs"]
    assert "source-and-tests" in jobs
    smoke = jobs["container-smoke"]
    assert "needs" not in smoke
    text = CI_WORKFLOW.read_text(encoding="utf-8")
    # Synthetic secrets are generated at run time and never written into the workflow.
    assert "openssl rand" in text
    assert "docker compose" in text
