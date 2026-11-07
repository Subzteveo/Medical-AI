/* DOM execution complements browser QA; it does not establish visual/accessibility compliance. */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { JSDOM, VirtualConsole } = require('jsdom');
const { fixtures, supportedFixture, mutations, unsafeUrls } = require('./provenance_test_cases.cjs');
const html = fs.readFileSync(process.env.MEDICAL_AI_HTML_PATH || path.join(__dirname, '../src/medical_ai/static/index.html'), 'utf8');

async function run() {
  const failures = [], errors = [];
  const virtualConsole = new VirtualConsole();
  virtualConsole.on('jsdomError', error => errors.push(error.message));
  let payload;
  const dom = new JSDOM(html, { url: 'https://fixture.invalid/', runScripts: 'dangerously', virtualConsole,
    beforeParse(window) { window.fetch = async () => ({ ok: true, json: async () => structuredClone(payload) }); },
  });
  const { window } = dom, document = window.document;
  for (const name of ['positive', ...Object.keys(mutations)]) {
    payload = structuredClone(supportedFixture);
    if (mutations[name]) mutations[name](payload);
    document.getElementById('question').value = 'Synthetic integrity fixture';
    document.getElementById('query-form').dispatchEvent(new window.Event('submit', { cancelable: true }));
    await new Promise(resolve => setImmediate(resolve));
    try {
      assert.equal(document.getElementById('submit').disabled, false);
      assert.equal(document.getElementById('result').hidden, false);
      const answer = document.getElementById('answer').textContent;
      const state = document.getElementById('state-code').textContent;
      if (name === 'positive') {
        assert.ok(answer.includes(supportedFixture.claims[0].claim_text));
        assert.equal(state, 'Research found, with important limits');
        assert.ok(document.querySelectorAll('#sources a').length > 0);
        assert.equal(document.querySelectorAll('.passport').length, payload.claims.length);
        assert.ok(document.querySelector('.passport blockquote').textContent.includes(payload.passages[0].text));
        assert.equal(document.querySelector('.passport mark').textContent, payload.claims[0].claim_text);
        assert.ok(document.querySelector('.passport').textContent.includes('Original source'));
        assert.ok(document.querySelector('.passport a').href.startsWith('https://'));
        assert.equal(document.querySelector('.passport').textContent.includes('Policy digest'), false);
        assert.ok(document.getElementById('boundaries').textContent.includes('Study quality not assessed'));
        assert.ok(document.getElementById('boundaries').textContent.includes('Australian medicine rules not checked'));
        assert.ok(document.getElementById('boundaries').textContent.includes('Not a complete comparison of studies'));
      } else {
        assert.equal(answer.includes(supportedFixture.claims[0].claim_text), false, 'Invalid claim disclosed');
        assert.equal(state, 'We could not check the source details');
        assert.equal(document.querySelectorAll('#sources a').length, 0);
        assert.equal(document.querySelectorAll('.passport').length, 0);
        assert.ok(document.getElementById('boundaries').textContent.includes('Source details could not be checked'));
      }
      assert.ok([...document.querySelectorAll('#result a')].every(link => new URL(link.href).protocol === 'https:'));
    } catch (error) { failures.push(name + ': ' + error.message); }
  }
  for (const name of ['insufficient', 'high', 'regulator']) {
    payload = fixtures[name];
    document.getElementById('query-form').dispatchEvent(new window.Event('submit', { cancelable: true }));
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(document.getElementById('state-code').textContent, ({ ANSWER_SUPPORTED_WITH_QUALIFICATIONS: 'Research found, with important limits', EVIDENCE_INSUFFICIENT: 'Not enough information to answer', HIGH_CONSEQUENCE_VERIFICATION_FAILED: 'We cannot verify this safety-related question', NO_AUTHORITATIVE_SOURCE: 'We could not find a suitable source' })[payload.status]);
    assert.equal(document.querySelectorAll('.passport').length, 0);
    assert.ok(document.getElementById('boundaries').textContent.includes('Study quality not assessed'), `${name}: missing study-quality limitation`);
    assert.ok(document.getElementById('boundaries').textContent.includes('Australian medicine rules not checked'), `${name}: missing source limitation`);
  }
  payload = structuredClone(supportedFixture);
  delete payload.claims[0].evidence_certainty;
  delete payload.sources[0].version;
  document.getElementById('query-form').dispatchEvent(new window.Event('submit', { cancelable: true }));
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(document.getElementById('state-code').textContent, ({ ANSWER_SUPPORTED_WITH_QUALIFICATIONS: 'Research found, with important limits', EVIDENCE_INSUFFICIENT: 'Not enough information to answer', HIGH_CONSEQUENCE_VERIFICATION_FAILED: 'We cannot verify this safety-related question', NO_AUTHORITATIVE_SOURCE: 'We could not find a suitable source' })[payload.status]);
  assert.ok(document.querySelector('.passport').textContent.includes('Read the supporting passage'));
  assert.equal(document.querySelector('.passport').textContent.includes('Evidence certainty:'), false);
  for (const url of unsafeUrls) assert.equal(window.safeSourceUrl(url), null, url);
  for (const url of ['https://pubmed.ncbi.nlm.nih.gov/123/', 'HTTPS://example.org/article?q=a#span', 'https://example.org:8443/']) {
    assert.ok(window.safeSourceUrl(url), 'Permitted HTTPS link rejected');
  }
  dom.window.close();
  assert.deepEqual(errors, [], 'Unhandled page errors');
  assert.deepEqual(failures, [], 'DOM provenance regressions');
  console.log(`DOM QA passed: ${Object.keys(mutations).length} invalid responses withheld, valid positive control, ${unsafeUrls.length} unsafe-link controls.`);
}
run().catch(error => { console.error(error); process.exitCode = 1; });
