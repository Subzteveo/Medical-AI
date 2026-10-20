/* Exact-source visual QA with synthetic nonclinical API responses. */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const { chromium } = require('playwright');
const { fixtures, supportedFixture, mutations } = require('./provenance_test_cases.cjs');

const HTML = fs.readFileSync(path.join(__dirname, '..', 'src/medical_ai/static/index.html'), 'utf8');
const OUT = '/tmp/medical-ai-evidence-atlas-screenshots';
fs.mkdirSync(OUT, { recursive: true });

const fixtureTrace = {
  trace_id: 'synthetic-visual-fixture',
  query_plan: { consequence_level: 'LOW', required_source_classes: ['biomedical_literature'] },
  connectors_used: ['fixture-only'],
  source_ids: [],
  safety_flags: [],
  authorization_decision_ids: [],
};
const forbidden = 'UNAUTHORIZED_SENTINEL_NOT_FOR_DISPLAY';
const server = http.createServer((req, res) => {
  if (req.method === 'GET' && req.url === '/') {
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' });
    res.end(HTML);
    return;
  }
  if (req.method === 'POST' && req.url === '/v1/evidence/query') {
    let body = '';
    req.on('data', part => { body += part; });
    req.on('end', () => {
      const payload = JSON.parse(body);
      assert.equal(typeof payload.question, 'string');
      assert.equal(payload.jurisdiction, 'AU');
      assert.ok(['student', 'clinician', 'researcher'].includes(payload.user_mode));
      if (payload.question.startsWith('boundary ')) {
        const data = fixtures[payload.question.slice('boundary '.length)];
        assert.ok(data);
        res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
        res.end(JSON.stringify(data));
        return;
      }
      if (payload.question.startsWith('integrity ')) {
        const caseName = payload.question.slice('integrity '.length);
        const data = structuredClone(supportedFixture);
        if (mutations[caseName]) mutations[caseName](data);
        res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
        res.end(JSON.stringify(data));
        return;
      }
      const blocked = payload.question.includes('blocked');
      const result = blocked ? {
        status: 'INFLUENCE_DENIED',
        answer_markdown: forbidden,
        claims: [{ claim_id: 'not-admitted', claim_text: forbidden, verification_status: 'PASS', source_ids: ['source1'] }],
        sources: [],
        trace: { ...fixtureTrace, safety_flags: ['FIXTURE_DENIED'] },
        influence_decisions: [{ status: 'DENY', reasons: ['EVIDENCE_AUTHORITY_DENIED'] }],
      } : {
        status: 'EVIDENCE_INSUFFICIENT',
        answer_markdown: 'No source supported an answer',
        claims: [],
        sources: [],
        trace: fixtureTrace,
        influence_decisions: [],
      };
      res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
      res.end(JSON.stringify(result));
    });
    return;
  }
  if (req.method === 'POST' && req.url === '/access/logout') {
    res.writeHead(200, { 'Content-Type': 'application/json' }); res.end('{"status":"signed_out"}'); return;
  }
  res.writeHead(404); res.end();
});

async function run() {
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const port = server.address().port;
  let browser;
  try {
    browser = await chromium.launch({ headless: true, executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE, args: ['--no-sandbox'] });
    const desktop = await browser.newPage({ viewport: { width: 1450, height: 930 }, deviceScaleFactor: 1 });
    const browserErrors = [];
    desktop.on('pageerror', e => browserErrors.push(e.message));
    await desktop.goto('http://127.0.0.1:' + port + '/', { waitUntil: 'networkidle' });
    assert.equal(await desktop.locator('#query-form').count(), 1);
    assert.equal(await desktop.getByRole('tab').count(), 3);
    await desktop.screenshot({ path: path.join(OUT, 'desktop-search.png'), fullPage: true });
    await desktop.getByRole('tab', { name: /Inside Medical AI/ }).click();
    assert.equal(await desktop.locator('#view-map').isVisible(), true);
    assert.equal(await desktop.locator('.column').count(), 5);
    await desktop.screenshot({ path: path.join(OUT, 'desktop-system-map.png'), fullPage: true });
    await desktop.getByRole('tab', { name: /Source directory/ }).click();
    assert.equal(await desktop.locator('#view-directory').isVisible(), true);
    await desktop.screenshot({ path: path.join(OUT, 'desktop-source-directory.png'), fullPage: true });
    await desktop.getByRole('tab', { name: /Search evidence/ }).click();
    await desktop.locator('#question').fill('blocked fixture question');
    await desktop.locator('#submit').click();
    await desktop.locator('#result').waitFor({ state: 'visible' });
    assert.match(await desktop.locator('#status').innerText(), /PROVENANCE_INCOMPLETE/);
    assert.equal((await desktop.locator('#answer').innerText()).includes(forbidden), false);
    assert.equal(await desktop.locator('#answer li').count(), 0);
    const failures = [];
    for (const caseName of ['positive', ...Object.keys(mutations)]) {
      await desktop.locator('#question').fill('integrity ' + caseName);
      await desktop.locator('#submit').click();
      await desktop.waitForFunction(() => !document.getElementById('submit').disabled);
      try {
        assert.equal(await desktop.locator('#result').isVisible(), true);
        const text = await desktop.locator('#answer').innerText();
        const state = await desktop.locator('#state-code').innerText();
        if (caseName === 'positive') {
          assert.ok(text.includes(supportedFixture.claims[0].claim_text));
          assert.equal(state, 'ANSWER_SUPPORTED_WITH_QUALIFICATIONS');
          assert.ok(await desktop.locator('#sources a').count() > 0);
          assert.equal(await desktop.locator('.passport').count(), supportedFixture.claims.length);
          const passport = desktop.locator('.passport').first();
          await passport.locator('summary').focus();
          await desktop.keyboard.press('Enter');
          assert.equal(await passport.evaluate(element => element.open), true);
          assert.equal(await passport.locator('mark').first().innerText(), supportedFixture.claims[0].claim_text);
          assert.ok((await passport.innerText()).includes(supportedFixture.citation_mappings[0].mapping_id));
          assert.ok((await passport.innerText()).includes('Policy digest: Not supplied'));
          await desktop.screenshot({ path: path.join(OUT, 'desktop-evidence-passport.png'), fullPage: true });
        } else {
          assert.equal(text.includes(supportedFixture.claims[0].claim_text), false, 'Invalid claim disclosed');
          assert.equal(state, 'PROVENANCE_INCOMPLETE', 'Inconsistent response was not withheld');
          assert.equal(await desktop.locator('#sources a').count(), 0);
          assert.equal(await desktop.locator('.passport').count(), 0);
          assert.ok(await desktop.locator('[data-boundary-state="failed"]').count() > 0);
        }
        const unsafe = await desktop.locator('#result a').evaluateAll(links => links.some(link => new URL(link.href).protocol !== 'https:'));
        assert.equal(unsafe, false, 'Unsafe source link retained');
      } catch (error) { failures.push(caseName + ': ' + error.message); }
    }
    assert.deepEqual(failures, [], 'Provenance browser regressions');
    for (const name of ['insufficient', 'high', 'regulator']) {
      await desktop.locator('#question').fill('boundary ' + name);
      await desktop.locator('#submit').click();
      await desktop.waitForFunction(() => !document.getElementById('submit').disabled);
      assert.equal(await desktop.locator('#state-code').innerText(), fixtures[name].status);
      for (const state of ['failed', 'unknown', 'not-implemented']) assert.ok(await desktop.locator(`[data-boundary-state="${state}"]`).count() > 0);
    }
    assert.deepEqual(browserErrors, []);
    const mobile = await browser.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1 });
    const mobileErrors = [];
    mobile.on('pageerror', e => mobileErrors.push(e.message));
    await mobile.goto('http://127.0.0.1:' + port + '/', { waitUntil: 'networkidle' });
    assert.equal(await mobile.locator('#query-form').isVisible(), true);
    const overflow = await mobile.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 2);
    assert.equal(overflow, false, 'Mobile horizontal overflow detected');
    await mobile.screenshot({ path: path.join(OUT, 'mobile-search.png'), fullPage: true });
    await mobile.locator('#question').fill('integrity positive');
    await mobile.locator('#submit').click();
    await mobile.waitForFunction(() => !document.getElementById('submit').disabled);
    await mobile.locator('.passport summary').first().click();
    assert.equal(await mobile.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 2), false, 'Mobile passport overflow detected');
    await mobile.screenshot({ path: path.join(OUT, 'mobile-evidence-passport.png'), fullPage: true });
    await mobile.getByRole('tab', { name: /Inside Medical AI/ }).click();
    const mapOverflow = await mobile.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 2);
    assert.equal(mapOverflow, false, 'Mobile architecture map overflow detected');
    await mobile.screenshot({ path: path.join(OUT, 'mobile-system-map.png'), fullPage: true });
    assert.deepEqual(mobileErrors, []);
    console.log('Visual QA passed: desktop/mobile layout, keyboard Passport inspection, boundaries and provenance regressions.');
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
}

run().catch(e => { console.error(e); process.exitCode = 1; server.close(); });
