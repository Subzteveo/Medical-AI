from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path

import pytest
from medical_ai.schemas import (
    FreshnessAssessment,
    FreshnessState,
    InformationClass,
    Passage,
    PHIClassification,
    SourceRecord,
    SourceVersionRecord,
    source_version_content_sha256,
)
from medical_ai.engine import EvidenceEngine
from medical_ai.authority_resolver import AuthorityResolver


def _home_state_snapshot() -> dict[str, int]:
    root = Path.home() / ".medical_ai"
    if not root.exists():
        return {}
    return {str(p): p.stat().st_mtime_ns for p in [root, *sorted(root.rglob("*"))]}


@pytest.fixture(scope="session", autouse=True)
def home_state_untouched():
    """The suite must never create or modify the operator's real state directory."""
    before = _home_state_snapshot()
    yield
    assert _home_state_snapshot() == before, "tests wrote to ~/.medical_ai"


@pytest.fixture(autouse=True)
def isolated_state_dirs(monkeypatch, tmp_path):
    """Point the session and trace stores at a per-test temporary directory."""
    import medical_ai.api as api

    monkeypatch.setenv("MEDICAL_AI_PILOT_SESSION_DB", str(tmp_path / "pilot_sessions.sqlite3"))
    monkeypatch.setenv("MEDICAL_AI_TRACE_DB", str(tmp_path / "medical_ai_traces.sqlite3"))
    monkeypatch.setattr(api, "TRACE_DB", str(tmp_path / "medical_ai_traces.sqlite3"))


def synthetic_version_record(
    *, source_id: str, record_id: str, upstream_version: str, connector_name: str, connector_version: str
) -> SourceVersionRecord:
    """A clearly-synthetic, digest-valid source-version record for supported-path fixtures."""
    return SourceVersionRecord(
        source_id=source_id,
        upstream_record_id=record_id,
        upstream_version=upstream_version,
        retrieved_at=datetime.now(timezone.utc),
        connector_name=connector_name,
        connector_version=connector_version,
        content_sha256=source_version_content_sha256(
            source_id=source_id, upstream_record_id=record_id, upstream_version=upstream_version
        ),
    )


def synthetic_current_freshness() -> FreshnessAssessment:
    return FreshnessAssessment(
        state=FreshnessState.CURRENT, basis="synthetic-fixture", assessed_at=datetime.now(timezone.utc)
    )


def make_engine(connectors, **kwargs):
    """Construct an engine with the trusted A2 authority resolver wired in.

    Supported-path tests use this so claims can be independently authorised. Tests
    that assert the fail-closed default (no authority) construct EvidenceEngine
    directly without a resolver.
    """
    if "authority_resolver" not in kwargs:
        kwargs["authority_resolver"] = AuthorityResolver()
    return EvidenceEngine(connectors, **kwargs)


class FakePubMedConnector:
    name = "fake-pubmed"
    version = "fixture-2"
    source_class = "biomedical_literature"
    evidence_approved = True
    phi_approved = False

    def __init__(self, sources=None, passages=None):
        self.called = False
        self.sources = sources if sources is not None else [SourceRecord(
            source_id="pubmed:123",
            authority="NLM/NCBI PubMed",
            publisher="Example Journal",
            source_type="indexed_biomedical_literature",
            title="Evidence about treatment X",
            record_id="123",
            stable_url="https://pubmed.ncbi.nlm.nih.gov/123/",
            identifiers={"PMID":"123"},
            publication_date="2026",
            version_record=synthetic_version_record(
                source_id="pubmed:123", record_id="123", upstream_version="123.1",
                connector_name="fake-pubmed", connector_version="fixture-2",
            ),
            freshness=synthetic_current_freshness(),
            phi_classification=PHIClassification(
                classification_id="public:pubmed:123",
                object_id="pubmed:123",
                information_class=InformationClass.PUBLIC,
                contains_phi=False,
            ),
        )]
        self.passages = passages if passages is not None else [Passage(
            passage_id="p1", source_id="pubmed:123", section="RESULTS",
            text="Treatment X reduced symptom scores compared with placebo in the studied adult population. The study did not evaluate other populations.",
            locator="AbstractText[0]"
        )]

    async def search_and_fetch(self, query: str, limit: int = 5):
        self.called = True
        return self.sources, self.passages


class FakeTrialConnector:
    name = "fake-clinicaltrials"
    version = "fixture-2"
    source_class = "clinical_trial_registry"
    evidence_approved = True
    phi_approved = False

    def __init__(self):
        self.called = False
        self.sources = [SourceRecord(
            source_id="ctgov:NCT00000001",
            authority="ClinicalTrials.gov / U.S. National Library of Medicine",
            publisher="Example Sponsor",
            source_type="clinical_trial_registry",
            title="Study of treatment X in hypertension",
            record_id="NCT00000001",
            stable_url="https://clinicaltrials.gov/study/NCT00000001",
            identifiers={"NCT":"NCT00000001"},
            evidence_class="trial_registry_record",
            version_record=synthetic_version_record(
                source_id="ctgov:NCT00000001", record_id="NCT00000001",
                upstream_version="NCT00000001@2026-01-01", connector_name="fake-clinicaltrials",
                connector_version="fixture-2",
            ),
            freshness=synthetic_current_freshness(),
            phi_classification=PHIClassification(
                classification_id="public:ctgov:NCT00000001",
                object_id="ctgov:NCT00000001",
                information_class=InformationClass.PUBLIC,
                contains_phi=False,
            ),
        )]
        self.passages = [Passage(
            passage_id="tp1", source_id="ctgov:NCT00000001", section="REGISTRY_FACT",
            text="The registry status for NCT00000001 is RECRUITING.", locator="protocolSection.fact[1]"
        )]

    async def search_and_fetch(self, query: str, limit: int = 5):
        self.called = True
        return self.sources, self.passages


@pytest.fixture
def fake_connector():
    return FakePubMedConnector()


@pytest.fixture
def fake_registry(fake_connector):
    return {
        "biomedical_literature": fake_connector,
        "clinical_trial_registry": FakeTrialConnector(),
    }
