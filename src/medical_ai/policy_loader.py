from __future__ import annotations

from functools import lru_cache
from importlib.resources import files
from typing import Any

import yaml


@lru_cache(maxsize=None)
def load_policy(name: str) -> dict[str, Any]:
    resource = files("medical_ai.policies").joinpath(name)
    with resource.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise RuntimeError(f"Policy {name} did not parse to a mapping")
    return data


def consequence_policy() -> dict[str, Any]:
    return load_policy("consequence-policy-v0.1.yaml")


def source_policy() -> dict[str, Any]:
    return load_policy("source-policy-v0.1.yaml")


def phi_routing_policy() -> dict[str, Any]:
    return load_policy("phi-routing-v0.1.yaml")


def evidence_influence_policy() -> dict[str, Any]:
    return load_policy("evidence-influence-v0.1.yaml")
