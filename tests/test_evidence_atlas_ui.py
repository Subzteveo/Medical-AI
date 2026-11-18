"""Evidence Atlas static contract and safety invariants."""
from pathlib import Path
from fastapi.testclient import TestClient
from medical_ai.api import app

PAGE = Path(__file__).resolve().parents[1] / "src/medical_ai/static/index.html"

def test_evidence_atlas_navigation_and_accessibility_structure():
    html = PAGE.read_text(encoding="utf-8")
    assert "Evidence Atlas" in html
    for key in ("view-search", "view-map", "view-directory", "tab-search", "tab-map", "tab-directory"):
        assert f'id="{key}"' in html
    assert 'role="tablist"' in html and 'role="tabpanel"' in html
    assert 'id="answer-heading" tabindex="-1"' in html
    assert 'aria-live="polite"' in html and 'label for="question"' in html
    assert "ArrowRight" in html and "ArrowLeft" in html
    assert ":focus-visible" in html and "@media(max-width:760px)" in html

def test_evidence_atlas_safe_claim_rendering_contract():
    html = PAGE.read_text(encoding="utf-8")
    assert "validateResponse(data)" in html
    assert "integrity && supportedStates.has(data.status) ? data.claims : []" in html
    assert "No supported finding could be shown" in html
    assert "descriptions[displayStatus]" in html
    assert "new URL(value)" in html and "url.protocol === 'https:'" in html
    assert "textContent" in html and "innerHTML" not in html
    assert "data.answer_markdown.replace" not in html

def test_evidence_atlas_preserves_pilot_access_and_authority_boundaries():
    html = PAGE.read_text(encoding="utf-8")
    assert "/v1/evidence/query" in html
    assert "Do not enter anyone\'s personal medical details." in html
    assert "Do not enter personal patient details" in html
    assert "Australian medicines information" in html and "Not available yet" in html
    assert "ClinicalTrials.gov" in html
    anon = TestClient(app).get("/")
    # Without pilot configuration the existing gate fails closed (503).
    # With configuration an anonymous visitor sees the access shell (200).
    assert anon.status_code in (200, 503)
    assert 'id="query-form"' not in anon.text
    if anon.status_code == 200:
        assert "Welcome to Medical AI" in anon.text

def test_plain_language_interface_keeps_existing_checks():
    html = PAGE.read_text(encoding="utf-8")
    assert "What would you like to research?" in html
    assert "Search research" in html
    assert "Read the supporting passage" in html
    assert "statusTitles[displayStatus]" in html
    assert "validateResponse(data)" in html
    assert "integrity && supportedStates.has(data.status) ? data.claims : []" in html
    for retired_label in ("Backend result state", "Evidence Passport", "Engineering alpha", "Admitted sources", "PHI approval"):
        assert retired_label not in html
    assert "Not for treatment decisions" in html
    assert "Study quality not assessed" in html
