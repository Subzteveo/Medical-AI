"""Inspect local request-time captures; publish digests and decisions, not abstracts."""
import copy
import hashlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from medical_ai.connectors.pubmed import PubMedConnector
from medical_ai.planner import classify_consequence, plan_query
from medical_ai.extractor import extract_evidence
from medical_ai.claims import build_claims
from medical_ai.verifier import verify_claims
from medical_ai.source_policy import qualify_source

# Independent field checker imports none of the runtime processing functions.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from scripts.check_pubmed_discovery_evidence import check

capture = Path(sys.argv[1])
output = Path(sys.argv[2])
revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
report = {'revision': revision, 'cases': [], 'scope': 'Literal fidelity and deterministic routing; not clinical correctness'}
for name, response_number in [('broad', 1), ('target', 3), ('headings', 5)]:
    raw = json.loads((capture/f'original-response-{response_number}.json').read_text())
    xml = raw['body']
    answer = json.loads((capture/f'{name}-api.json').read_text())
    root = ET.fromstring(xml)
    item = {'name': name, 'xml_sha256': hashlib.sha256(xml.encode()).hexdigest(), 'url': raw['url'], 'retrieved_at': raw['retrieved_at'], 'trace': answer['trace']}
    if answer['claims']:
        item['fidelity'] = check(xml, answer)
        source_fields = []
        for source in answer['sources']:
            node = next(n for n in root.findall('./PubmedArticle') if n.findtext('MedlineCitation/PMID') == source['record_id'])
            article = node.find('MedlineCitation/Article')
            assert source['title'] == ''.join(article.find('ArticleTitle').itertext()).strip()
            labels = [n.get('Label') or n.get('NlmCategory') or 'ABSTRACT' for n in article.findall('Abstract/AbstractText') if ''.join(n.itertext()).strip()]
            assert source['raw_metadata']['abstract_labels'] == labels
            source_fields.append({'pmid':source['record_id'], 'headings':labels, 'title_match':True})
        item['original_fields'] = source_fields
        tampered = copy.deepcopy(answer)
        tampered['claims'][0]['claim_text'] += ' Altered claim.'
        try: check(xml, tampered)
        except AssertionError: item['tampered_claim_negative_control'] = 'REJECTED'
        else: raise AssertionError('Tampered claim accepted')
    # Diagnostic replay explains the existing trace without altering live output.
    sources, passages = PubMedConnector._parse_pubmed_xml(xml)
    plan = plan_query(answer['trace']['query_plan']['retrieval_questions'][0])
    admitted = [s for s in sources if qualify_source(s, plan).admitted]
    passages = [p for p in passages if p.source_id in {s.source_id for s in admitted}]
    units = extract_evidence(plan.retrieval_questions[0], admitted, passages)
    claims = verify_claims(build_claims(units, plan), units, passages)
    item['candidate_diagnostics'] = [{'claim_id':c.claim_id,'sources':c.source_ids,'categories':classify_consequence(c.claim_text)[1],'consequence':c.consequence_level,'verification':c.verification_status,'entailment':c.entailment_status} for c in claims]
    assert {c.claim_id:c.verification_status.value for c in claims} == answer['trace']['verification_results']
    report['cases'].append(item)
output.write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps([{ 'case':c['name'], 'fields':c.get('original_fields'), 'categories':[d['categories'] for d in c['candidate_diagnostics']]} for c in report['cases']],indent=2))
