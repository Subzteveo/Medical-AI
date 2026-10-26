"""Compare an answer with original EFetch XML without importing runtime code.

Inputs remain local request-time captures. Output contains identifiers/digests,
not redistributed publisher abstracts. This checks literal fidelity, not medicine.
Usage: python scripts/check_pubmed_discovery_evidence.py ORIGINAL.xml ANSWER.json
"""
from __future__ import annotations

import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def check(xml_text: str, answer: dict) -> dict:
    articles = {}
    for article in ET.fromstring(xml_text).findall('./PubmedArticle'):
        pmid = article.findtext('MedlineCitation/PMID')
        nodes = article.findall('MedlineCitation/Article/Abstract/AbstractText')
        sections = []
        for node in nodes:
            text = ''.join(node.itertext()).strip()
            label = node.get('Label') or node.get('NlmCategory')
            if text:
                sections.append(f'{label}: {text}' if label else text)
        articles[pmid] = '\n\n'.join(s for s in sections if s)
    assert answer['status'] == 'ANSWER_SUPPORTED_WITH_QUALIFICATIONS'
    sources = {s['source_id']: s for s in answer['sources']}
    units = {u['evidence_id']: u for u in answer['evidence_objects']}
    passages = {p['passage_id']: p for p in answer['passages']}
    results = []
    for claim in answer['claims']:
        assert len(claim['evidence_ids']) == len(claim['source_ids']) == 1
        unit = units[claim['evidence_ids'][0]]
        source = sources[claim['source_ids'][0]]
        assert len(unit['passage_ids']) == 1
        passage = passages[unit['passage_ids'][0]]
        pmid = source['record_id']
        expected = articles[pmid]
        assert expected
        assert claim['claim_text'] == unit['proposition'] == passage['text'] == expected
        assert unit['source_id'] == passage['source_id'] == source['source_id']
        assert passage['locator'] == 'Article/Abstract'
        assert source['stable_url'] == f'https://pubmed.ncbi.nlm.nih.gov/{pmid}/'
        assert any(m['claim_id'] == claim['claim_id'] and m['evidence_id'] == unit['evidence_id'] and m['source_id'] == source['source_id'] and m['passage_ids'] == [passage['passage_id']] for m in answer['citation_mappings'])
        results.append({'pmid': pmid, 'citation': source['stable_url'], 'characters': len(expected), 'abstract_sha256': hashlib.sha256(expected.encode()).hexdigest()})
    assert results
    return {'result': 'PASS', 'scope': 'Complete original abstract text and citation identity; not clinical correctness or retrieval completeness', 'xml_sha256': hashlib.sha256(xml_text.encode()).hexdigest(), 'checked_abstracts': results}


if __name__ == '__main__':
    print(json.dumps(check(Path(sys.argv[1]).read_text(), json.loads(Path(sys.argv[2]).read_text())), indent=2))
