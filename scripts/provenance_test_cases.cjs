'use strict';
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const supportedFixture = JSON.parse(execFileSync(process.env.PYTHON || 'python', [path.join(__dirname, '../tests/browser_fixture.py')], { encoding: 'utf8' }));
const mutations = {
  unsafe: d => { d.sources[0].stable_url = 'javascript:alert(1)'; },
  http: d => { d.sources[0].stable_url = 'http://example.org/'; },
  orphan: d => { d.sources = []; },
  duplicate: d => { d.sources.push(structuredClone(d.sources[0])); },
  blank: d => { d.sources[0].source_id = ''; },
  reference: d => { d.claims[0].source_ids = ['absent']; },
  duplicateReference: d => { d.claims[0].source_ids.push(d.claims[0].source_ids[0]); },
  noEvidence: d => { d.evidence_objects = []; },
  duplicateEvidence: d => { d.evidence_objects.push(structuredClone(d.evidence_objects[0])); },
  evidence: d => { d.evidence_objects[0].source_id = 'absent'; },
  proposition: d => { d.evidence_objects[0].proposition = 'Unrelated claim.'; },
  passage: d => { d.passages[0].source_id = 'absent'; },
  noPassage: d => { d.passages = []; },
  duplicatePassage: d => { d.passages.push(structuredClone(d.passages[0])); },
  text: d => { d.passages[0].text = 'Unrelated text.'; },
  noMapping: d => { d.citation_mappings = []; },
  duplicateMapping: d => { d.citation_mappings.push(structuredClone(d.citation_mappings[0])); },
  mapping: d => { d.citation_mappings[0].passage_ids = ['absent']; },
  mappingSource: d => { d.citation_mappings[0].source_id = 'absent'; },
  mappingVerification: d => { d.citation_mappings[0].verified = false; },
  empty: d => { d.claims = []; },
  status: d => { d.trace.final_status = 'EVIDENCE_INSUFFICIENT'; },
  unsupportedClaims: d => { d.status = d.trace.final_status = 'EVIDENCE_INSUFFICIENT'; },
  traceClaim: d => { d.trace.candidate_claim_ids = []; },
  decision: d => { d.influence_decisions = []; },
  duplicateDecision: d => { d.influence_decisions.push(structuredClone(d.influence_decisions[0])); },
  revoked: d => { d.influence_decisions[0].authorization.state = 'REVOKED'; },
  wrongDecision: d => { d.influence_decisions[0].object_id = 'absent'; },
};
const unsafeUrls = ['javascript:alert(1)', 'data:text/html,unsafe', 'http://example.org/', '//example.org/',
  'https:example.org', 'https://', 'https://user@example.org/', 'https://@example.org/', 'https:///example.org/',
  'https://example.org:bad/', 'https://example.org:0/', 'https://example.org\\@evil.test/',
  'https://exam\nple.org/', ' https://example.org/', 'https://%65xample.org/'];
unsafeUrls.forEach((url, i) => { mutations['url' + i] = d => { d.sources[0].stable_url = url; }; });
module.exports = { supportedFixture, mutations, unsafeUrls };
