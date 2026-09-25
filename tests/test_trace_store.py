from pathlib import Path
import json
import sqlite3
import pytest
from medical_ai.engine import EvidenceEngine
from medical_ai.trace_store import SQLiteTraceStore
from conftest import FakePubMedConnector


@pytest.mark.asyncio
async def test_trace_store_does_not_persist_raw_question(tmp_path: Path):
    db_path = tmp_path / "traces.sqlite3"
    store = SQLiteTraceStore(db_path)
    question = "What evidence shows treatment X reduces symptom scores?"
    out = await EvidenceEngine(FakePubMedConnector(), trace_store=store).answer(question)
    stored = store.get(out.trace.trace_id)
    assert stored is not None
    assert question not in json.dumps(stored)
    assert stored["retrieval_query_digests"][0].startswith("hmac-sha256:")
    with sqlite3.connect(db_path) as db:
        raw = db.execute("select payload_json from execution_traces").fetchone()[0]
    assert question not in raw
