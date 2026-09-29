from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .connectors.pubmed import PubMedConnector
from .connectors.clinical_trials import ClinicalTrialsConnector
from .engine import EvidenceEngine
from .trace_store import SQLiteTraceStore

VERSION = "0.1.0-alpha2.1-remediation"
STATIC_DIR = Path(__file__).parent / "static"
_default_trace_db = Path.home() / ".medical_ai" / "medical_ai_traces.sqlite3"
TRACE_DB = str(Path(os.getenv("MEDICAL_AI_TRACE_DB", str(_default_trace_db))).expanduser().resolve())

app = FastAPI(title="Medical AI Evidence Workbench", version=VERSION)


class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=4000)
    user_mode: str = Field(default="clinician", pattern="^(student|clinician|researcher)$")
    jurisdiction: str = Field(default="AU", max_length=40)
    limit: int = Field(default=5, ge=1, le=20)


def build_engine() -> EvidenceEngine:
    connectors = {
        "biomedical_literature": PubMedConnector(email=os.getenv("NCBI_EMAIL"), api_key=os.getenv("NCBI_API_KEY")),
        "clinical_trial_registry": ClinicalTrialsConnector(),
    }
    return EvidenceEngine(connectors, trace_store=SQLiteTraceStore(TRACE_DB))


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health():
    return {"status": "ok", "version": VERSION}


@app.post("/v1/evidence/query")
async def query(req: QueryRequest):
    engine = build_engine()
    return await engine.answer(req.question, user_mode=req.user_mode, jurisdiction=req.jurisdiction, limit=req.limit)
