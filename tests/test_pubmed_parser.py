from medical_ai.connectors.pubmed import PubMedConnector

XML = '''<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>999</PMID><Article><Journal><JournalIssue><PubDate><Year>2026</Year></PubDate></JournalIssue><Title>Journal X</Title></Journal><ArticleTitle>Example title</ArticleTitle><Abstract><AbstractText Label="RESULTS">Example result sentence.</AbstractText></Abstract></Article></MedlineCitation><PubmedData><ArticleIdList><ArticleId IdType="pubmed">999</ArticleId><ArticleId IdType="doi">10.1/example</ArticleId><ArticleId IdType="pmc">PMC999</ArticleId></ArticleIdList></PubmedData></PubmedArticle></PubmedArticleSet>'''

def test_pubmed_xml_maps_to_source_and_passage():
    sources, passages = PubMedConnector._parse_pubmed_xml(XML)
    assert sources[0].identifiers["DOI"] == "10.1/example"
    assert sources[0].identifiers["PMC"] == "PMC999"
    assert any(p.text == "Example result sentence." for p in passages)
