"""Alpha3 A1 — status-claim contract tests.

Status authority is independent and revision-bound. A status label is admissible
only with the evidence its policy requires, and no status label implies any other.
These tests exercise the schema contract and the status-claims policy mapping for
the A1-STA candidate cases; projection/reconciliation over append-only events is
explicitly deferred to A2/A3.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from medical_ai.authority import StatusClaimRecord, StatusResult, StatusValue
from medical_ai.authority_policy import (
    DecisionResult,
    RuleScope,
    compile_authority_policy,
    evaluate_scope,
)

AWARE = datetime(2026, 11, 5, 0, 0, tzinfo=timezone.utc)


def _record(**kw: object) -> StatusClaimRecord:
    base: dict[str, object] = dict(
        status_claim_id="sc-1", subject_ref="subject-1", status=StatusValue.DOCUMENTED, scope="scope-1",
        revision_ref="rev-abc", authority_type="repository-document", authority_ref="doc-at-rev-abc",
        evidence_refs=("doc-1",), asserted_at=AWARE, observed_at=AWARE, result=StatusResult.AUTHORIZED, trace_ref="t",
    )
    base.update(kw)
    return StatusClaimRecord(**base)


def test_documented_authorized_requires_document_evidence() -> None:
    # A1-STA-001 current document at exact revision -> DOCUMENTED AUTHORIZED
    assert _record().result is StatusResult.AUTHORIZED
    # A1-STA-002 docs claim implemented without artefact -> IMPLEMENTED UNAUTHORIZED
    unauth = _record(
        status=StatusValue.IMPLEMENTED, result=StatusResult.UNAUTHORIZED, authority_ref=None,
        evidence_refs=(), reason_codes=("NO_INSPECTED_ARTEFACT",))
    assert unauth.result is StatusResult.UNAUTHORIZED


def test_tested_without_run_is_unauthorized() -> None:
    # A1-STA-003 test files present, no run event
    rec = _record(status=StatusValue.TESTED, result=StatusResult.UNAUTHORIZED, authority_ref=None,
                  evidence_refs=(), reason_codes=("NO_TEST_EXECUTION_EVENT",))
    assert rec.status is StatusValue.TESTED
    assert rec.result is StatusResult.UNAUTHORIZED


def test_passed_is_revision_bound() -> None:
    # A1-STA-004 CI passed at commit A, assertion concerns commit B
    rec = _record(status=StatusValue.PASSED, revision_ref="commit-B", result=StatusResult.UNAUTHORIZED,
                  authority_ref=None, evidence_refs=(), reason_codes=("CHECK_RUN_BOUND_TO_DIFFERENT_COMMIT",))
    assert rec.result is StatusResult.UNAUTHORIZED


def test_merged_authorized_needs_merge_event() -> None:
    # A1-STA-007 merged at exact revision with merge event -> MERGED AUTHORIZED
    rec = _record(status=StatusValue.MERGED, authority_type="github-merge", authority_ref="merge-commit-x",
                  evidence_refs=("merge-event-x",))
    assert rec.result is StatusResult.AUTHORIZED
    # ...but cannot be constructed AUTHORIZED without the evidence.
    with pytest.raises(ValidationError):
        _record(status=StatusValue.MERGED, authority_ref=None, evidence_refs=())


def test_stale_requires_reason() -> None:
    # A1-STA-009 expired/withdrawn -> STALE with a reason
    rec = _record(result=StatusResult.STALE, authority_ref=None, evidence_refs=(), reason_codes=("UPSTREAM_WITHDRAWN",))
    assert rec.result is StatusResult.STALE
    with pytest.raises(ValidationError):
        _record(result=StatusResult.STALE, authority_ref=None, evidence_refs=(), reason_codes=())


def test_status_vocabulary_is_closed() -> None:
    with pytest.raises(ValidationError):
        _record(status="NOT_A_STATUS")


def test_status_policy_maps_each_status_to_required_evidence() -> None:
    policy = compile_authority_policy("status-claims-v0.1.yaml")
    release_ready = evaluate_scope(policy, RuleScope(subject_status=StatusValue.RELEASE_READY))
    assert release_ready.result is DecisionResult.ALLOW
    assert "ALL_MANDATORY_RELEASE_GATES" in release_ready.evidence_requirements
    assert "DESIGNATED_RELEASE_AUTHORITY" in release_ready.evidence_requirements
    approved = evaluate_scope(policy, RuleScope(subject_status=StatusValue.APPROVED))
    assert approved.evidence_requirements == ("DESIGNATED_AUTHORITY_EVENT_WITH_SCOPE",)
    # Every closed status value is mapped by the policy (no permissive fall-through).
    for status in StatusValue:
        assert evaluate_scope(policy, RuleScope(subject_status=status)).result is DecisionResult.ALLOW
