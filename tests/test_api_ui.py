from fastapi.testclient import TestClient
from medical_ai.api import app


def test_root_serves_accessible_workbench_shell():
    response = TestClient(app).get("/")
    assert response.status_code == 200
    assert "Medical AI Evidence Workbench" in response.text
    assert 'label for="question"' in response.text
    assert 'aria-live="polite"' in response.text
    assert "do not enter identifying patient information" in response.text


def test_health_reports_alpha2():
    response = TestClient(app).get("/health")
    assert response.json()["version"] == "0.1.0-alpha2.1-remediation"
