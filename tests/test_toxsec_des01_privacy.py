"""ToxSec DES-01 red regressions: use synthetic identifiers only.

These tests assert the connector/storage boundary, not a guarantee that all PHI
can be identified by deterministic detection.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

import medical_ai.api as api
from medical_ai.engine import EvidenceEngine
from medical_ai.schemas import AnswerStatus
from medical_ai.trace_store import SQLiteTraceStore
from conftest import FakePubMedConnector


class RecordingConnector(FakePubMedConnector):
    def __init__(self):
        super().__init__()
        self.queries: list[str] = []

    async def search_and_fetch(self, query: str, limit: int = 5):
        self.queries.append(query)
        return await super().search_and_fetch(query, limit=limit)


@pytest.mark.asyncio
@pytest.mark.parametrize("question", [
    "Find studies relevant to Casey Example and hypertension.",
    "What research relates to synthetic.case@example.invalid and hypertension?",
    "Research on 0400 000 000 and blood pressure.",
    "Does 99 Fictional Street have relevant medical research?",
])
async def test_synthetic_identifiers_never_reach_provider_or_trace(tmp_path, question):
    connector = RecordingConnector()
    db_path = tmp_path / "audit.sqlite3"
    engine = EvidenceEngine(connector, trace_store=SQLiteTraceStore(db_path))
    answer = await engine.answer(question)

    assert answer.status == AnswerStatus.OUTSIDE_VALIDATED_CAPABILITY
    assert "PHI_ROUTE_BLOCKED" in answer.trace.safety_flags
    assert connector.queries == []
    assert question not in db_path.read_bytes().decode("utf-8")


@pytest.mark.asyncio
async def test_ordinary_research_query_still_reaches_approved_mock():
    connector = RecordingConnector()
    await EvidenceEngine(connector).answer("What evidence exists for exercise reducing blood pressure?")
    assert connector.queries == ["What evidence exists for exercise reducing blood pressure?"]


def test_free_text_jurisdiction_is_rejected_before_connector(monkeypatch):
    token = "test-invite-" + "K" * 40
    secret = "test-secret-" + "Q" * 40
    config = {"participants": [{
        "participant_id": "synthetic-001",
        "credential_id": "synthetic-credential",
        "token_sha256": hashlib.sha256(token.encode()).hexdigest(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
        "revoked": False,
    }]}
    monkeypatch.setenv("MEDICAL_AI_PILOT_ACCESS_JSON", json.dumps(config))
    monkeypatch.setenv("MEDICAL_AI_PILOT_SESSION_SECRET", secret)
    connector = RecordingConnector()
    monkeypatch.setattr(api, "build_engine", lambda: EvidenceEngine(connector))
    response = TestClient(api.app).post(
        "/v1/evidence/query",
        json={
            "question": "What evidence exists for exercise reducing blood pressure?",
            "jurisdiction": "AU synthetic.case@example.invalid",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
    assert "synthetic.case@example.invalid" not in response.text
    assert connector.queries == []
