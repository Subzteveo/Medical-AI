import hashlib
import json
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from medical_ai.api import app


TOKEN = "ui-test-token-" + ("B" * 40)
SECRET = "ui-session-secret-" + ("C" * 40)


def _configure(monkeypatch):
    monkeypatch.setenv(
        "MEDICAL_AI_PILOT_ACCESS_JSON",
        json.dumps(
            {
                "participants": [
                    {
                        "participant_id": "ui-test-user",
                        "credential_id": "ui-test-credential",
                        "token_sha256": hashlib.sha256(TOKEN.encode("utf-8")).hexdigest(),
                        "expires_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
                        "revoked": False,
                    }
                ]
            }
        ),
    )
    monkeypatch.setenv("MEDICAL_AI_PILOT_SESSION_SECRET", SECRET)
    monkeypatch.setenv("MEDICAL_AI_PILOT_COOKIE_SECURE", "false")


def test_root_serves_accessible_workbench_shell_only_after_login(monkeypatch):
    _configure(monkeypatch)
    client = TestClient(app)

    anonymous = client.get("/")
    assert anonymous.status_code == 200
    assert "Medical AI Pilot" in anonymous.text
    assert 'label for="question"' not in anonymous.text

    assert client.post("/access/session", json={"token": TOKEN}).status_code == 200
    response = client.get("/")
    assert response.status_code == 200
    assert "Medical AI Evidence Workbench" in response.text
    assert 'label for="question"' in response.text
    assert 'aria-live="polite"' in response.text
    assert 'id="answer-heading" tabindex="-1"' in response.text
    assert "do not enter identifying patient information" in response.text


def test_health_reports_alpha2():
    response = TestClient(app).get("/health")
    assert response.json()["version"] == "0.1.0-alpha2.1-remediation"
