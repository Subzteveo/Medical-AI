from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from .schemas import ExecutionTrace


class SQLiteTraceStore:
    """Minimal local audit store that deliberately excludes raw user queries and source text."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS execution_traces (
                    trace_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    final_status TEXT NOT NULL,
                    query_digest TEXT,
                    payload_json TEXT NOT NULL
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def save(self, trace: ExecutionTrace) -> None:
        # Persist only non-content audit fields. Do not persist retrieval_questions,
        # known_user_facts, unknown_material_facts, source passages, or user text.
        plan = trace.query_plan
        payload = {
            "trace_id": trace.trace_id,
            "timestamp": trace.timestamp.isoformat(),
            "intent": plan.intent,
            "user_mode": plan.user_mode,
            "patient_specific": plan.patient_specific,
            "jurisdiction": plan.jurisdiction,
            "jurisdiction_material": plan.jurisdiction_material,
            "temporal_sensitivity": plan.temporal_sensitivity,
            "consequence_level": plan.consequence_level.value,
            "required_source_classes": plan.required_source_classes,
            "required_second_pass": plan.required_second_pass,
            "retrieval_query_digests": trace.retrieval_query_digests,
            "connectors_used": trace.connectors_used,
            "source_ids": trace.source_ids,
            "evidence_ids": trace.evidence_ids,
            "candidate_claim_ids": trace.candidate_claim_ids,
            "verification_results": trace.verification_results,
            "safety_flags": trace.safety_flags,
            "component_versions": trace.component_versions,
            "final_status": trace.final_status.value,
        }
        query_digest = trace.retrieval_query_digests[0] if trace.retrieval_query_digests else None
        with self._connect() as db:
            db.execute(
                "INSERT OR REPLACE INTO execution_traces(trace_id,timestamp,final_status,query_digest,payload_json) VALUES(?,?,?,?,?)",
                (trace.trace_id, trace.timestamp.isoformat(), trace.final_status.value, query_digest, json.dumps(payload, sort_keys=True)),
            )

    def get(self, trace_id: str) -> dict | None:
        with self._connect() as db:
            row = db.execute("SELECT payload_json FROM execution_traces WHERE trace_id = ?", (trace_id,)).fetchone()
        return json.loads(row[0]) if row else None
