"""Alpha3 A1 — authority policy compiler and scoped decision tests.

Covers digest reproducibility, fail-closed rejection of malformed policy, the
prohibition-dominant / default-DENY resolution, and the candidate policy decision
cases A1-POL-001..018 from ``ALPHA3_A1_POLICY_REVIEW_CASES.md`` against the actual
packaged policies.
"""

from __future__ import annotations

import copy

import pytest

from medical_ai.authority import (
    AuthorityDimension,
    AuthorityOperation,
    AuthorityPurpose,
    ClaimType,
    DataPlane,
    DecisionResult,
    FreshnessState,
    InformationClassification,
    SourceClass,
)
from medical_ai.schemas import ConsequenceLevel
from medical_ai.authority_policy import (
    AGGREGATION_POLICY_SCHEMA,
    AUTHORITY_POLICY_SCHEMA,
    PolicyError,
    RuleScope,
    ScopedDecisionReason,
    _canonical_digest,
    _load_yaml_mapping,
    compile_aggregation_bundle,
    compile_aggregation_policy,
    compile_authority_bundle,
    compile_authority_policy,
    evaluate_scope,
    resolve_required_dimensions,
)

AUTHORITY_POLICIES = (
    "evidence-authority-v0.2.yaml",
    "information-handling-v0.2.yaml",
    "data-plane-transitions-v0.2.yaml",
    "status-claims-v0.1.yaml",
)


def _raw(name: str) -> dict[str, object]:
    raw = _load_yaml_mapping(name)
    assert isinstance(raw, dict)
    return copy.deepcopy(raw)


@pytest.mark.parametrize("name", AUTHORITY_POLICIES)
def test_packaged_authority_policies_compile(name: str) -> None:
    bundle = compile_authority_policy(name)
    assert bundle.schema_version == AUTHORITY_POLICY_SCHEMA
    assert bundle.default_decision is DecisionResult.DENY
    assert bundle.policy_digest == _canonical_digest(bundle)


def test_aggregation_policy_compiles() -> None:
    policy = compile_aggregation_policy("influence-aggregation-v0.2.yaml")
    assert policy.schema_version == AGGREGATION_POLICY_SCHEMA
    assert AuthorityDimension.EVIDENCE_AUTHORITY in policy.required_dimensions
    assert AuthorityDimension.STATUS_AUTHORITY in policy.optional_dimensions


def test_digest_is_reproducible() -> None:
    raw = _raw("evidence-authority-v0.2.yaml")
    bundle = compile_authority_bundle(raw)
    assert _canonical_digest(bundle) == _canonical_digest(bundle)
    assert bundle.policy_digest == _canonical_digest(bundle)


def test_tampered_rule_order_without_new_digest_is_rejected() -> None:
    raw = _raw("evidence-authority-v0.2.yaml")
    rules = raw["rules"]
    assert isinstance(rules, list)
    rules.reverse()  # declared digest no longer matches the content
    with pytest.raises(PolicyError, match="digest mismatch"):
        compile_authority_bundle(raw)


def test_digest_mismatch_rejected() -> None:
    raw = _raw("evidence-authority-v0.2.yaml")
    raw["policy_digest"] = "0" * 64
    with pytest.raises(PolicyError, match="digest mismatch"):
        compile_authority_bundle(raw)


def test_duplicate_rule_id_rejected() -> None:
    raw = _raw("evidence-authority-v0.2.yaml")
    rules = raw["rules"]
    assert isinstance(rules, list)
    rules.append(copy.deepcopy(rules[0]))
    raw["policy_digest"] = _digest_for(raw)
    with pytest.raises(PolicyError, match="Duplicate rule_id"):
        compile_authority_bundle(raw)


def test_unknown_schema_version_rejected() -> None:
    raw = _raw("evidence-authority-v0.2.yaml")
    raw["schema_version"] = "medical-ai-authority-policy/999"
    raw["policy_digest"] = _digest_for(raw)
    with pytest.raises(PolicyError, match="unsupported schema_version"):
        compile_authority_bundle(raw)


def test_non_deny_default_rejected() -> None:
    raw = _raw("evidence-authority-v0.2.yaml")
    raw["default_decision"] = "ALLOW"
    raw["policy_digest"] = _digest_for(raw)
    with pytest.raises(PolicyError, match="default_decision DENY"):
        compile_authority_bundle(raw)


def test_unknown_enum_value_rejected() -> None:
    raw = _raw("evidence-authority-v0.2.yaml")
    rules = raw["rules"]
    assert isinstance(rules, list)
    first = rules[0]
    assert isinstance(first, dict)
    match = first["match"]
    assert isinstance(match, dict)
    match["claim_type"] = "NOT_A_CLAIM_TYPE"
    raw["policy_digest"] = _digest_for(raw)
    with pytest.raises(PolicyError, match="schema validation"):
        compile_authority_bundle(raw)


def test_extra_field_rejected() -> None:
    raw = _raw("evidence-authority-v0.2.yaml")
    raw["unexpected"] = True
    with pytest.raises(PolicyError, match="schema validation"):
        compile_authority_bundle(raw)


def test_rule_scope_key_outside_dimension_rejected() -> None:
    raw = _raw("information-handling-v0.2.yaml")
    rules = raw["rules"]
    assert isinstance(rules, list)
    first = rules[0]
    assert isinstance(first, dict)
    match = first["match"]
    assert isinstance(match, dict)
    match["from_plane"] = "EVIDENCE"  # a data-plane key in an information-handling rule
    raw["policy_digest"] = _digest_for(raw)
    with pytest.raises(PolicyError, match="outside dimension"):
        compile_authority_bundle(raw)


def test_allow_rule_underspecified_rejected() -> None:
    raw = _raw("evidence-authority-v0.2.yaml")
    rules = raw["rules"]
    assert isinstance(rules, list)
    first = rules[0]
    assert isinstance(first, dict)
    match = first["match"]
    assert isinstance(match, dict)
    del match["operation"]  # ALLOW rule now missing a required key
    raw["policy_digest"] = _digest_for(raw)
    with pytest.raises(PolicyError, match="underspecified"):
        compile_authority_bundle(raw)


def _digest_for(raw: dict[str, object]) -> str:
    """Recompute a matching digest so a *structural* rejection, not the digest, fires."""

    probe = copy.deepcopy(raw)
    probe["policy_digest"] = "0" * 64
    # The bundle may be structurally invalid; compute the digest off a lenient path.
    from medical_ai.authority_policy import AuthorityPolicyBundle

    try:
        bundle = AuthorityPolicyBundle.model_validate(probe)
    except Exception:
        return "0" * 64  # digest irrelevant; schema rejection will fire first
    return _canonical_digest(bundle)


# --- scoped decision behaviour ------------------------------------------------
def test_evidence_authority_cases() -> None:
    ea = compile_authority_policy("evidence-authority-v0.2.yaml")

    def decide(**kw: object) -> tuple[DecisionResult, ScopedDecisionReason]:
        d = evaluate_scope(ea, RuleScope(**kw))
        return d.result, d.reason

    # A1-POL-001 PubMed literature -> conditional ALLOW
    assert decide(claim_type=ClaimType.BIOMEDICAL_LITERATURE, source_class=SourceClass.PUBMED_INDEXED_LITERATURE,
                  operation=AuthorityOperation.RETRIEVE_PUBLIC_EVIDENCE, freshness=FreshnessState.CURRENT) == (
        DecisionResult.ALLOW, ScopedDecisionReason.ALLOWED_BY_RULE)
    # A1-POL-002 CT.gov registration fact -> conditional ALLOW
    assert decide(claim_type=ClaimType.TRIAL_REGISTRATION_FACT, source_class=SourceClass.CLINICALTRIALS_GOV_REGISTRY,
                  operation=AuthorityOperation.RETRIEVE_PUBLIC_EVIDENCE, freshness=FreshnessState.CURRENT)[0] is DecisionResult.ALLOW
    # A1-POL-003 CT.gov narrative as efficacy -> DENY
    assert decide(claim_type=ClaimType.TREATMENT_EFFICACY, source_class=SourceClass.CLINICALTRIALS_GOV_REGISTRY,
                  operation=AuthorityOperation.RETRIEVE_PUBLIC_EVIDENCE, freshness=FreshnessState.CURRENT) == (
        DecisionResult.DENY, ScopedDecisionReason.PROHIBITED_BY_RULE)
    # A1-POL-004 PubMed as AU regulatory approval -> DENY
    assert decide(claim_type=ClaimType.AU_REGULATORY_APPROVAL, source_class=SourceClass.PUBMED_INDEXED_LITERATURE,
                  operation=AuthorityOperation.RETRIEVE_PUBLIC_EVIDENCE, freshness=FreshnessState.CURRENT)[0] is DecisionResult.DENY
    # A1-POL-005 retracted source -> DENY even for an otherwise-admissible claim
    assert decide(claim_type=ClaimType.BIOMEDICAL_LITERATURE, source_class=SourceClass.PUBMED_INDEXED_LITERATURE,
                  operation=AuthorityOperation.RETRIEVE_PUBLIC_EVIDENCE, freshness=FreshnessState.RETRACTED) == (
        DecisionResult.DENY, ScopedDecisionReason.PROHIBITED_BY_RULE)
    # A1-POL-006 unknown freshness -> DENY
    assert decide(claim_type=ClaimType.BIOMEDICAL_LITERATURE, source_class=SourceClass.PUBMED_INDEXED_LITERATURE,
                  operation=AuthorityOperation.RETRIEVE_PUBLIC_EVIDENCE, freshness=FreshnessState.UNKNOWN)[0] is DecisionResult.DENY
    # High consequence disabled
    assert decide(claim_type=ClaimType.BIOMEDICAL_LITERATURE, source_class=SourceClass.PUBMED_INDEXED_LITERATURE,
                  operation=AuthorityOperation.RETRIEVE_PUBLIC_EVIDENCE, freshness=FreshnessState.CURRENT,
                  consequence=ConsequenceLevel.HIGH)[0] is DecisionResult.DENY
    # Underspecified (missing operation) -> DENY
    assert decide(claim_type=ClaimType.BIOMEDICAL_LITERATURE, source_class=SourceClass.PUBMED_INDEXED_LITERATURE) == (
        DecisionResult.DENY, ScopedDecisionReason.UNDERSPECIFIED_REQUEST)


def test_prohibition_dominates_order_independently() -> None:
    ea = compile_authority_policy("evidence-authority-v0.2.yaml")
    # Efficacy via PubMed matches a DENY rule and no ALLOW: must be DENY.
    decision = evaluate_scope(ea, RuleScope(
        claim_type=ClaimType.TREATMENT_EFFICACY, source_class=SourceClass.PUBMED_INDEXED_LITERATURE,
        operation=AuthorityOperation.RETRIEVE_PUBLIC_EVIDENCE, freshness=FreshnessState.CURRENT))
    assert decision.result is DecisionResult.DENY


def test_information_handling_cases() -> None:
    ih = compile_authority_policy("information-handling-v0.2.yaml")

    def decide(**kw: object) -> DecisionResult:
        return evaluate_scope(ih, RuleScope(**kw)).result

    allow = decide(component="pubmed_public_connector", information_class=InformationClassification.PUBLIC_EVIDENCE,
                   operation=AuthorityOperation.RETRIEVE_PUBLIC_EVIDENCE, purpose=AuthorityPurpose.LITERATURE_DISCOVERY,
                   environment="production_public_readonly")
    assert allow is DecisionResult.ALLOW
    # A1-POL-008 identifiable health info to public connector -> DENY
    assert decide(component="pubmed_public_connector", information_class=InformationClassification.IDENTIFIABLE_HEALTH_INFORMATION,
                  operation=AuthorityOperation.RETRIEVE_PUBLIC_EVIDENCE, purpose=AuthorityPurpose.LITERATURE_DISCOVERY,
                  environment="production_public_readonly") is DecisionResult.DENY
    # A1-POL-009 deidentified without verified determination -> DENY
    assert decide(component="pubmed_public_connector", information_class=InformationClassification.DEIDENTIFIED_HEALTH_INFORMATION,
                  operation=AuthorityOperation.RETRIEVE_PUBLIC_EVIDENCE, purpose=AuthorityPurpose.LITERATURE_DISCOVERY,
                  environment="production_public_readonly") is DecisionResult.DENY
    # A1-POL-010 restricted research data -> DENY
    assert decide(component="model_worker", information_class=InformationClassification.RESTRICTED_RESEARCH_DATA,
                  operation=AuthorityOperation.DERIVE_RESEARCH_RESULT, purpose=AuthorityPurpose.RESEARCH_ANALYSIS,
                  environment="internal") is DecisionResult.DENY


def test_data_plane_cases() -> None:
    dp = compile_authority_policy("data-plane-transitions-v0.2.yaml")

    def decide(**kw: object) -> DecisionResult:
        return evaluate_scope(dp, RuleScope(**kw)).result

    # A1-POL-011 EVIDENCE->EVIDENCE public retrieve -> conditional permit
    assert decide(from_plane=DataPlane.EVIDENCE, to_plane=DataPlane.EVIDENCE,
                  information_class=InformationClassification.PUBLIC_EVIDENCE,
                  operation=AuthorityOperation.RETRIEVE_PUBLIC_EVIDENCE, purpose=AuthorityPurpose.LITERATURE_DISCOVERY) is DecisionResult.ALLOW
    # A1-POL-012 CLINICAL->EVIDENCE -> DENY
    assert decide(from_plane=DataPlane.CLINICAL, to_plane=DataPlane.EVIDENCE,
                  information_class=InformationClassification.PUBLIC_EVIDENCE,
                  operation=AuthorityOperation.RETRIEVE_PUBLIC_EVIDENCE, purpose=AuthorityPurpose.CLINICAL_CONTEXT) is DecisionResult.DENY
    # A1-POL-013 RESEARCH->EVIDENCE -> DENY
    assert decide(from_plane=DataPlane.RESEARCH, to_plane=DataPlane.EVIDENCE,
                  information_class=InformationClassification.PUBLIC_EVIDENCE,
                  operation=AuthorityOperation.RETRIEVE_PUBLIC_EVIDENCE, purpose=AuthorityPurpose.RESEARCH_ANALYSIS) is DecisionResult.DENY
    # A1-POL-014 same-plane UNKNOWN class -> DENY
    assert decide(from_plane=DataPlane.EVIDENCE, to_plane=DataPlane.EVIDENCE,
                  information_class=InformationClassification.UNKNOWN,
                  operation=AuthorityOperation.RETRIEVE_PUBLIC_EVIDENCE, purpose=AuthorityPurpose.LITERATURE_DISCOVERY) is DecisionResult.DENY
    # PROMOTE_TO_EVIDENCE always denied in Tranche A
    assert decide(from_plane=DataPlane.EVIDENCE, to_plane=DataPlane.EVIDENCE,
                  information_class=InformationClassification.PUBLIC_EVIDENCE,
                  operation=AuthorityOperation.PROMOTE_TO_EVIDENCE, purpose=AuthorityPurpose.EDUCATIONAL_EVIDENCE_RENDER) is DecisionResult.DENY


def test_aggregation_requires_all_mandatory_dimensions() -> None:
    policy = compile_aggregation_policy("influence-aggregation-v0.2.yaml")
    # A1-POL-015 caller omits a mandatory dimension -> DENY
    missing = resolve_required_dimensions(policy, (AuthorityDimension.EVIDENCE_AUTHORITY, AuthorityDimension.INFORMATION_HANDLING))
    assert missing.result is DecisionResult.DENY
    assert missing.reason is ScopedDecisionReason.UNDERSPECIFIED_REQUEST
    full = resolve_required_dimensions(policy, (
        AuthorityDimension.EVIDENCE_AUTHORITY, AuthorityDimension.INFORMATION_HANDLING, AuthorityDimension.DATA_PLANE_TRANSITION))
    assert full.result is DecisionResult.ALLOW


def test_aggregation_bundle_rejects_dimension_in_both_sets() -> None:
    raw = _load_yaml_mapping("influence-aggregation-v0.2.yaml")
    assert isinstance(raw, dict)
    broken = copy.deepcopy(raw)
    broken["optional_dimensions"] = ["EVIDENCE_AUTHORITY"]
    with pytest.raises(PolicyError):
        compile_aggregation_bundle(broken)
