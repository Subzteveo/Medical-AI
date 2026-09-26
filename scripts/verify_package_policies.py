"""Verify installed policy resources match the repository policy files."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from medical_ai import policy_loader


root = Path(__file__).resolve().parents[1]
policy_dir = root / "policies"
for policy_file in sorted(policy_dir.glob("*.yaml")):
    name = policy_file.name
    packaged = files("medical_ai.policies").joinpath(name).read_bytes()
    if policy_file.read_bytes() != packaged:
        raise RuntimeError(f"Policy resource drift: {name}")
    if not isinstance(policy_loader.load_policy(name), dict):
        raise RuntimeError(f"Policy load failure: {name}")
print("Installed policies match the repository policies and parse successfully.")
