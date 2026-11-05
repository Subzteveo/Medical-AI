"""Alpha3 A1 — authority policy compiler and scoped decision evaluator.

Implements the executable policy contract of
``project_docs/ALPHA3_A1_SCHEMA_POLICY_REVIEW.md`` §4:

    YAML decode -> strict closed-schema validation -> immutable, digest-verified
    compiled rule registry -> scoped decision.

Fail-closed properties:

* ``default_decision`` is always ``DENY``; an unmatched request denies.
* A missing digest, a digest mismatch, a duplicate ``rule_id``, an unknown
  enum/field, or a rule whose scope keys are wrong for its dimension rejects the
  whole load — a failed policy is never cached as active.
* A broad (wildcard) ``ALLOW`` can never override a narrower ``DENY``: resolution
  is prohibition-dominant and order-independent, so overlapping/contradictory rules
  deny deterministically rather than depending on insertion order.
* A request that omits a mandatory scope key for its dimension is underspecified
  and denies; the trusted policy — not the caller — selects required dimensions.

This module is a candidate control layer. It is not imported by the engine,
renderer, API or connectors; A2 performs that integration under separate gates.
"""

from __future__ import annotations

import hashlib
import json
from enum import StrEnum
from functools import lru_cache
from importlib.resources import files

import yaml
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from .authority import (
    AuthorityDimension,
    AuthorityOperation,
    AuthorityPurpose,
    ClaimType,
    DataPlane,
    DecisionResult,
    FreshnessState,
    InformationClassification,
    NonBlankStr,
    SourceClass,
    StatusValue,
)
from .schemas import ConsequenceLevel

AUTHORITY_POLICY_SCHEMA = "medical-ai-authority-policy/1"
AGGREGATION_POLICY_SCHEMA = "medical-ai-influence-aggregation/1"


class PolicyError(RuntimeError):
    """Raised when a policy cannot be compiled; the policy is never activated."""


class ScopedDecisionReason(StrEnum):
    ALLOWED_BY_RULE = "ALLOWED_BY_RULE"
    NO_MATCHING_RULE = "NO_MATCHING_RULE"
    PROHIBITED_BY_RULE = "PROHIBITED_BY_RULE"
    UNDERSPECIFIED_REQUEST = "UNDERSPECIFIED_REQUEST"
    RULE_CONFLICT = "RULE_CONFLICT"


class _Closed(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class RuleScope(_Closed):
    """A closed, typed match scope. Every dimension uses a subset of these keys."""

    claim_type: ClaimType | None = None
    jurisdiction: NonBlankStr | None = None
    population_context: NonBlankStr | None = None
    source_class: SourceClass | None = None
    freshness: FreshnessState | None = None
    operation: AuthorityOperation | None = None
    purpose: AuthorityPurpose | None = None
    consequence: ConsequenceLevel | None = None
    information_class: InformationClassification | None = None
    component: NonBlankStr | None = None
    environment: NonBlankStr | None = None
    from_plane: DataPlane | None = None
    to_plane: DataPlane | None = None
    subject_status: StatusValue | None = None

    def set_keys(self) -> frozenset[str]:
        return frozenset(key for key, value in self.model_dump().items() if value is not None)


class AuthorityRule(_Closed):
    rule_id: NonBlankStr
    decision: DecisionResult
    match: RuleScope
    evidence_requirements: tuple[NonBlankStr, ...] = Field(default_factory=tuple)
    reason_code: NonBlankStr | None = None


class AuthorityPolicyBundle(_Closed):
    schema_version: NonBlankStr
    policy_id: NonBlankStr
    dimension: AuthorityDimension
    revision: int = Field(ge=1)
    effective_at: AwareDatetime
    default_decision: DecisionResult
    rules: tuple[AuthorityRule, ...] = Field(min_length=1)
    policy_digest: NonBlankStr


class InfluenceAggregationPolicy(_Closed):
    schema_version: NonBlankStr
    policy_id: NonBlankStr
    revision: int = Field(ge=1)
    effective_at: AwareDatetime
    required_dimensions: tuple[AuthorityDimension, ...] = Field(min_length=1)
    optional_dimensions: tuple[AuthorityDimension, ...] = Field(default_factory=tuple)
    policy_digest: NonBlankStr


class ScopedDecision(_Closed):
    result: DecisionResult
    reason: ScopedDecisionReason
    policy_id: NonBlankStr
    policy_digest: NonBlankStr
    matched_rule_ids: tuple[NonBlankStr, ...] = Field(default_factory=tuple)
    evidence_requirements: tuple[NonBlankStr, ...] = Field(default_factory=tuple)


# Keys each dimension's rules and requests must use; others must be absent.
_ALLOWED_KEYS: dict[AuthorityDimension, frozenset[str]] = {
    AuthorityDimension.EVIDENCE_AUTHORITY: frozenset(
        {"claim_type", "jurisdiction", "population_context", "source_class", "freshness", "operation", "consequence"}
    ),
    AuthorityDimension.INFORMATION_HANDLING: frozenset(
        {"component", "information_class", "operation", "purpose", "environment"}
    ),
    AuthorityDimension.DATA_PLANE_TRANSITION: frozenset(
        {"from_plane", "to_plane", "information_class", "operation", "purpose", "component"}
    ),
    AuthorityDimension.STATUS_AUTHORITY: frozenset({"subject_status"}),
}

# Keys a request (and an ALLOW rule) must specify for the dimension to be assessable.
_REQUIRED_KEYS: dict[AuthorityDimension, frozenset[str]] = {
    AuthorityDimension.EVIDENCE_AUTHORITY: frozenset({"claim_type", "source_class", "operation"}),
    AuthorityDimension.INFORMATION_HANDLING: frozenset(
        {"component", "information_class", "operation", "purpose"}
    ),
    AuthorityDimension.DATA_PLANE_TRANSITION: frozenset({"from_plane", "to_plane", "operation"}),
    AuthorityDimension.STATUS_AUTHORITY: frozenset({"subject_status"}),
}


def _canonical_digest(bundle: AuthorityPolicyBundle | InfluenceAggregationPolicy) -> str:
    payload = bundle.model_dump(mode="json", exclude={"policy_digest"})
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _load_yaml_mapping(name: str) -> object:
    resource = files("medical_ai.policies").joinpath(name)
    with resource.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _validate_rule_scopes(bundle: AuthorityPolicyBundle) -> None:
    allowed = _ALLOWED_KEYS[bundle.dimension]
    required = _REQUIRED_KEYS[bundle.dimension]
    seen: set[str] = set()
    for rule in bundle.rules:
        if rule.rule_id in seen:
            raise PolicyError(f"Duplicate rule_id in {bundle.policy_id}: {rule.rule_id}")
        seen.add(rule.rule_id)
        keys = rule.match.set_keys()
        extra = keys - allowed
        if extra:
            raise PolicyError(
                f"Rule {rule.rule_id} uses keys outside dimension {bundle.dimension}: {sorted(extra)}"
            )
        if rule.decision is DecisionResult.ALLOW and not required <= keys:
            raise PolicyError(
                f"ALLOW rule {rule.rule_id} is underspecified for {bundle.dimension}: "
                f"missing {sorted(required - keys)}"
            )


def compile_authority_bundle(raw: object) -> AuthorityPolicyBundle:
    """Validate, digest-verify and scope-check a raw authority policy mapping.

    Any failure raises :class:`PolicyError`; a rejected policy is never returned,
    so it cannot be cached or treated as active.
    """

    try:
        bundle = AuthorityPolicyBundle.model_validate(raw)
    except Exception as exc:  # pydantic validation failure -> reject load
        raise PolicyError(f"Policy failed schema validation: {exc}") from exc
    if bundle.schema_version != AUTHORITY_POLICY_SCHEMA:
        raise PolicyError(f"Policy has unsupported schema_version {bundle.schema_version!r}")
    if bundle.default_decision is not DecisionResult.DENY:
        raise PolicyError(f"Policy {bundle.policy_id} must declare default_decision DENY")
    expected = _canonical_digest(bundle)
    if bundle.policy_digest != expected:
        raise PolicyError(
            f"Policy {bundle.policy_id} digest mismatch: declared {bundle.policy_digest}, computed {expected}"
        )
    _validate_rule_scopes(bundle)
    return bundle


def compile_aggregation_bundle(raw: object) -> InfluenceAggregationPolicy:
    try:
        policy = InfluenceAggregationPolicy.model_validate(raw)
    except Exception as exc:
        raise PolicyError(f"Aggregation policy failed schema validation: {exc}") from exc
    if policy.schema_version != AGGREGATION_POLICY_SCHEMA:
        raise PolicyError(f"Aggregation policy has unsupported schema_version {policy.schema_version!r}")
    if set(policy.required_dimensions) & set(policy.optional_dimensions):
        raise PolicyError(f"Aggregation policy {policy.policy_id} lists a dimension as both required and optional")
    expected = _canonical_digest(policy)
    if policy.policy_digest != expected:
        raise PolicyError(
            f"Aggregation policy {policy.policy_id} digest mismatch: declared {policy.policy_digest}, computed {expected}"
        )
    return policy


@lru_cache(maxsize=None)
def compile_authority_policy(name: str) -> AuthorityPolicyBundle:
    return compile_authority_bundle(_load_yaml_mapping(name))


@lru_cache(maxsize=None)
def compile_aggregation_policy(name: str) -> InfluenceAggregationPolicy:
    return compile_aggregation_bundle(_load_yaml_mapping(name))


def _scope_matches(rule_scope: RuleScope, request: RuleScope) -> bool:
    request_values = request.model_dump()
    for key, value in rule_scope.model_dump().items():
        if value is None:
            continue
        if request_values[key] != value:
            return False
    return True


def evaluate_scope(bundle: AuthorityPolicyBundle, request: RuleScope) -> ScopedDecision:
    """Resolve a scoped authority decision, prohibition-dominant and fail-closed."""

    required = _REQUIRED_KEYS[bundle.dimension]
    provided = request.set_keys()
    if (provided - _ALLOWED_KEYS[bundle.dimension]) or not required <= provided:
        return ScopedDecision(
            result=DecisionResult.DENY,
            reason=ScopedDecisionReason.UNDERSPECIFIED_REQUEST,
            policy_id=bundle.policy_id,
            policy_digest=bundle.policy_digest,
        )

    deny_matches = [rule for rule in bundle.rules if rule.decision is DecisionResult.DENY and _scope_matches(rule.match, request)]
    allow_matches = [rule for rule in bundle.rules if rule.decision is DecisionResult.ALLOW and _scope_matches(rule.match, request)]

    if deny_matches:
        return ScopedDecision(
            result=DecisionResult.DENY,
            reason=ScopedDecisionReason.PROHIBITED_BY_RULE,
            policy_id=bundle.policy_id,
            policy_digest=bundle.policy_digest,
            matched_rule_ids=tuple(rule.rule_id for rule in deny_matches),
        )
    if allow_matches:
        requirements: tuple[str, ...] = tuple(
            dict.fromkeys(req for rule in allow_matches for req in rule.evidence_requirements)
        )
        return ScopedDecision(
            result=DecisionResult.ALLOW,
            reason=ScopedDecisionReason.ALLOWED_BY_RULE,
            policy_id=bundle.policy_id,
            policy_digest=bundle.policy_digest,
            matched_rule_ids=tuple(rule.rule_id for rule in allow_matches),
            evidence_requirements=requirements,
        )
    return ScopedDecision(
        result=DecisionResult.DENY,
        reason=ScopedDecisionReason.NO_MATCHING_RULE,
        policy_id=bundle.policy_id,
        policy_digest=bundle.policy_digest,
    )


def resolve_required_dimensions(
    policy: InfluenceAggregationPolicy, provided: tuple[AuthorityDimension, ...]
) -> ScopedDecision:
    """Deny when the caller omits any policy-mandated authority dimension."""

    provided_set = set(provided)
    missing = set(policy.required_dimensions) - provided_set
    if missing:
        return ScopedDecision(
            result=DecisionResult.DENY,
            reason=ScopedDecisionReason.UNDERSPECIFIED_REQUEST,
            policy_id=policy.policy_id,
            policy_digest=policy.policy_digest,
            matched_rule_ids=tuple(sorted(dimension.value for dimension in missing)),
        )
    return ScopedDecision(
        result=DecisionResult.ALLOW,
        reason=ScopedDecisionReason.ALLOWED_BY_RULE,
        policy_id=policy.policy_id,
        policy_digest=policy.policy_digest,
        evidence_requirements=tuple(dimension.value for dimension in policy.required_dimensions),
    )
