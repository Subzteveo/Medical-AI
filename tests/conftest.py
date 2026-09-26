from __future__ import annotations
import pytest
from medical_ai.schemas import Passage, SourceRecord


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
        )]
        self.passages = passages if passages is not None else [Passage(
            passage_id="p1", source_id="pubmed:123", section="RESULTS",
            text="Treatment X reduced symptom scores compared with placebo in the studied adult population. The study did not evaluate children.",
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
