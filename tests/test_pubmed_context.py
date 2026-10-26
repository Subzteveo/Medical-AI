"""Synthetic abstracts test context fidelity, not clinical truth."""
from xml.sax.saxutils import escape

from medical_ai.connectors.pubmed import PubMedConnector
from medical_ai.engine import EvidenceEngine
from medical_ai.schemas import AnswerStatus


def xml_abstract(*sections):
    body = ''
    for label, text in sections:
        attribute = f' Label="{label}"' if label else ''
        body += f'<AbstractText{attribute}>{escape(text)}</AbstractText>' 
    return f'<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>999</PMID><Article><ArticleTitle>Context test</ArticleTitle><Abstract>{body}</Abstract></Article></MedlineCitation></PubmedArticle></PubmedArticleSet>'


class FixtureConnector(PubMedConnector):
    def __init__(self, xml):
        super().__init__()
        self.xml = xml

    async def search_and_fetch(self, query, limit=5):
        return self._parse_pubmed_xml(self.xml)


async def test_whole_abstract_keeps_design_population_and_qualification():
    text = ('This cross-sectional study sampled 30 university students. '
            'Mindfulness was associated with attention. '
            'This association does not establish causation or generalise to other populations.')
    answer = await EvidenceEngine(FixtureConnector(xml_abstract(('', text)))).answer('Find literature about mindfulness and attention')
    assert answer.status == AnswerStatus.ANSWER_SUPPORTED_WITH_QUALIFICATIONS
    assert [c.claim_text for c in answer.claims] == [text]
    assert r'PubMed abstract \(PMID 999\)' in answer.answer_markdown


async def test_structured_abstract_keeps_qualifier_in_separate_section():
    methods = 'We surveyed 30 university students at one time point.'
    results = 'Mindfulness was associated with attention.'
    conclusion = 'Causal effects cannot be inferred from this design.'
    answer = await EvidenceEngine(FixtureConnector(xml_abstract(('METHODS', methods), ('RESULTS', results), ('CONCLUSIONS', conclusion)))).answer('Find literature about mindfulness and attention')
    assert [c.claim_text for c in answer.claims] == [f'METHODS: {methods}\n\nRESULTS: {results}\n\nCONCLUSIONS: {conclusion}']
    assert answer.passages[0].locator == 'Article/Abstract'
    assert answer.sources[0].raw_metadata['abstract_labels'] == ['METHODS', 'RESULTS', 'CONCLUSIONS']


async def test_abstract_without_query_overlap_is_not_supported():
    answer = await EvidenceEngine(FixtureConnector(xml_abstract(('', 'A survey measured commuter bicycle use in a city.')))).answer('Find literature about mindfulness and attention')
    assert answer.status == AnswerStatus.EVIDENCE_INSUFFICIENT
    assert not answer.claims


async def test_high_consequence_context_cannot_be_dropped_for_matching_sentence():
    text = 'Mindfulness was associated with attention. Warfarin dose adjustment is discussed elsewhere.'
    answer = await EvidenceEngine(FixtureConnector(xml_abstract(('', text)))).answer('Find literature about mindfulness and attention')
    assert answer.status == AnswerStatus.HIGH_CONSEQUENCE_VERIFICATION_FAILED
    assert not answer.claims


async def test_original_shared_fixture_pediatric_qualification_is_now_retained_and_held():
    # The former generic positive fixture silently discarded this second sentence.
    # Keep that exact safety case here, separate from low-consequence UI fixtures.
    text = 'Treatment X reduced symptom scores compared with placebo in the studied adult population. The study did not evaluate children.'
    answer = await EvidenceEngine(FixtureConnector(xml_abstract(('RESULTS', text)))).answer('What evidence shows treatment X reduced symptom scores?')
    assert answer.status == AnswerStatus.HIGH_CONSEQUENCE_VERIFICATION_FAILED
    assert not answer.claims
