"""ToxSec DES-03 red regressions: bounded influence state without unsafe eviction."""
from __future__ import annotations

import pytest

from medical_ai.engine import EvidenceEngine
from medical_ai.influence import InfluenceCapacityExceeded, InfluenceController
from medical_ai.schemas import (
    AnswerStatus, DataPlane, DataPlaneTransition, EvidenceAuthorityState,
    InfluenceObjectType, InfluenceRequest, InfluenceSubject, InformationClass,
    InformationHandlingAuthorityState,
)
from conftest import FakePubMedConnector


def _request(identifier: str) -> InfluenceRequest:
    source = InfluenceSubject(
        object_id=identifier,
        object_type=InfluenceObjectType.EVIDENCE_OBJECT,
        data_plane=DataPlane.EVIDENCE,
        evidence_authority=EvidenceAuthorityState.APPROVED,
        information_handling_authority=InformationHandlingAuthorityState.APPROVED,
        provenance_complete=True, validation_passed=True,
        safety_passed=True, monitoring_enabled=True,
        version="synthetic-v1",
    )
    return InfluenceRequest(
        subject=source,
        proposition_id=f"claim:{identifier}",
        transition=DataPlaneTransition(
            source_plane=DataPlane.EVIDENCE,
            target_plane=DataPlane.EVIDENCE,
            information_class=InformationClass.PUBLIC,
        ),
    )


def test_capacity_denies_new_authorization_without_eviction_of_old_capability():
    controller = InfluenceController(max_decisions=1)
    first = controller.authorize(_request("evidence:1"))
    assert first.allowed and first.authorization is not None

    with pytest.raises(InfluenceCapacityExceeded):
        controller.authorize(_request("evidence:2"))

    assert len(controller.decisions) == 1
    assert controller.get_subject("evidence:2") is None
    assert controller.get_authorization(first.authorization.authorization_id) is not None


@pytest.mark.asyncio
async def test_engine_exhausted_controller_withholds_without_fabricating_claim():
    controller = InfluenceController(max_decisions=1)
    engine = EvidenceEngine(FakePubMedConnector(), influence_controller=controller)
    await engine.answer("What evidence shows treatment X reduces symptom scores?")
    assert len(controller.decisions) == 1

    result = await engine.answer("What evidence shows treatment X reduces symptom scores?")
    assert result.status == AnswerStatus.INFLUENCE_DENIED
    assert result.claims == []
    assert "INFLUENCE_CAPACITY_EXCEEDED" in result.trace.safety_flags
    assert len(controller.decisions) == 1


@pytest.mark.parametrize("budget", [0, -1, 1000001])
def test_unbounded_or_nonpositive_budget_is_rejected(budget):
    with pytest.raises(ValueError):
        InfluenceController(max_decisions=budget)
