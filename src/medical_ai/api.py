from __future__ import annotations

import os
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from .access import (
    SESSION_COOKIE_NAME,
    AccessConfigurationError,
    authenticate_invite_token,
    create_session_token,
    load_access_config,
    optional_pilot_participant,
    require_pilot_participant,
)
from .connectors.pubmed import PubMedConnector
from .connectors.clinical_trials import ClinicalTrialsConnector
from .engine import EvidenceEngine
from .trace_store import SQLiteTraceStore

VERSION = "0.1.0-alpha2.1-remediation"
STATIC_DIR = Path(__file__).parent / "static"
_default_trace_db = Path.home() / ".medical_ai" / "medical_ai_traces.sqlite3"
TRACE_DB = str(Path(os.getenv("MEDICAL_AI_TRACE_DB", str(_default_trace_db))).expanduser().resolve())

app = FastAPI(
    title="Medical AI Evidence Workbench",
    version=VERSION,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

@app.exception_handler(RequestValidationError)
async def credential_validation_error(request: Request, exc: RequestValidationError):
    # Default validation responses include rejected input values, which can be credentials.
    if request.url.path == "/access/session":
        return JSONResponse(
            status_code=422,
            content={"detail": "Invalid pilot credential request"},
            headers={"Cache-Control": "no-store"},
        )
    return await request_validation_exception_handler(request, exc)


ACCESS_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Medical AI Pilot Access</title>
</head>
<body>
<main>
  <h1>Medical AI Pilot</h1>
  <p>This engineering pilot is invitation-only. Enter the pilot credential supplied to you.</p>
  <p>Do not enter patient-identifying information. Access does not expand the product's intended-use boundary.</p>
  <form id="access-form">
    <label for="pilot-token">Pilot credential</label>
    <input id="pilot-token" name="pilot-token" type="password" required minlength="20" autocomplete="off">
    <button type="submit">Enter pilot</button>
  </form>
  <p id="access-status" role="status" aria-live="polite"></p>
</main>
<script>
const form = document.getElementById('access-form');
const statusEl = document.getElementById('access-status');
form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const token = document.getElementById('pilot-token').value;
  statusEl.textContent = 'Checking invitation…';
  try {
    const response = await fetch('/access/session', {
      method: 'POST',
      headers: {'content-type': 'application/json'},
      body: JSON.stringify({token})
    });
    if (!response.ok) {
      statusEl.textContent = response.status === 401 ? 'Invitation not accepted.' : 'Pilot access is unavailable.';
      return;
    }
    document.getElementById('pilot-token').value = '';
    window.location.replace('/');
  } catch (error) {
    statusEl.textContent = 'Unable to check invitation.';
  }
});
</script>
</body>
</html>
"""


class AccessRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=20, max_length=512)


class QueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
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
def index(request: Request):
    participant = optional_pilot_participant(request)
    if participant is None:
        return HTMLResponse(ACCESS_PAGE, headers={"Cache-Control": "no-store"})
    return FileResponse(STATIC_DIR / "index.html", headers={"Cache-Control": "no-store"})


@app.post("/access/session", include_in_schema=False)
def create_access_session(req: AccessRequest, response: Response):
    try:
        config = load_access_config()
    except AccessConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Pilot access is not configured",
        ) from exc
    participant = authenticate_invite_token(req.token, config)
    if participant is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive pilot credential",
        )
    session_token, max_age = create_session_token(participant, config)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        max_age=max_age,
        httponly=True,
        secure=config.cookie_secure,
        samesite="strict",
        path="/",
    )
    response.headers["Cache-Control"] = "no-store"
    return {
        "status": "ok",
        "participant_id": participant.participant_id,
        "expires_at": participant.expires_at.isoformat(),
    }


@app.post("/access/logout", include_in_schema=False)
def logout(response: Response):
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
    response.headers["Cache-Control"] = "no-store"
    return {"status": "signed_out"}


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok", "version": VERSION}


@app.get("/openapi.json", include_in_schema=False)
def protected_openapi(_participant=Depends(require_pilot_participant)):
    return JSONResponse(app.openapi())


@app.get("/docs", include_in_schema=False)
def protected_docs(_participant=Depends(require_pilot_participant)):
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=f"{app.title} - API docs",
    )


@app.post("/v1/evidence/query")
async def query(
    req: QueryRequest,
    _participant=Depends(require_pilot_participant),
):
    engine = build_engine()
    return await engine.answer(req.question, user_mode=req.user_mode, jurisdiction=req.jurisdiction, limit=req.limit)
