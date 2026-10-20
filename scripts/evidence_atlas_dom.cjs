/* DOM execution complements browser QA; it does not establish visual/accessibility compliance. */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { JSDOM, VirtualConsole } = require('jsdom');
const { supportedFixture, mutations, unsafeUrls } = require('./provenance_test_cases.cjs');
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
        assert.equal(state, 'ANSWER_SUPPORTED_WITH_QUALIFICATIONS');
        assert.ok(document.querySelectorAll('#sources a').length > 0);
      } else {
        assert.equal(answer.includes(supportedFixture.claims[0].claim_text), false, 'Invalid claim disclosed');
        assert.equal(state, 'PROVENANCE_INCOMPLETE');
        assert.equal(document.querySelectorAll('#sources a').length, 0);
      }
      assert.ok([...document.querySelectorAll('#result a')].every(link => new URL(link.href).protocol === 'https:'));
    } catch (error) { failures.push(name + ': ' + error.message); }
  }
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
