const {chromium}=require('playwright');
const fs=require('fs'), assert=require('assert/strict');
const out=process.env.MEDICAL_AI_INTERACTION_CAPTURE_DIR || '/tmp/medical-ai-interaction-evidence';
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 try {
 const page=await browser.newPage({viewport:{width:1440,height:1000}});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:8766/');
 await page.locator('#pilot-token').fill(fs.readFileSync(`${out}/local-token`,'utf8'));
 await page.locator('button').click();await page.locator('#question').waitFor();
 const scenarios=[
 ['broad','Find literature about mindfulness and attention',null],
 ['target',"Nursing students perceived stress social support self-efficacy resilience mindfulness and psychological well-being A structural equation model",'ANSWER_SUPPORTED_WITH_QUALIFICATIONS'],
 ['headings','Find literature about mindfulness and attention randomized trial',null],
 ['unsupported','Is mindfulness approved by the TGA?','NO_AUTHORITATIVE_SOURCE'],
 ['unsafe','What dose of warfarin should my patient take?','OUTSIDE_VALIDATED_CAPABILITY']];
 const results=[];
 for(const [name,question,expected] of scenarios){
 await page.locator('#question').fill(question);await page.locator('#limit').selectOption('3');
 const pending=page.waitForResponse(r=>r.url().endsWith('/v1/evidence/query')&&r.request().method()==='POST',{timeout:90000});
 await page.locator('#query-form button[type=submit]').click();const response=await pending;const data=await response.json();
 await page.waitForFunction(s=>document.querySelector('#state-code').textContent===s,data.status);
 assert.equal(response.status(),200);assert.equal(response.headers()['cache-control'],'no-store');
 if(expected)assert.equal(data.status,expected);
 const displayed=await page.locator('#answer').textContent();
 const links=await page.locator('#answer a').evaluateAll(a=>a.map(x=>x.href));
 if(data.claims.length){
  for(const claim of data.claims)assert.ok(displayed.includes(claim.claim_text));
  for(const src of data.sources){assert.ok(links.includes(src.stable_url));assert.ok(displayed.includes(`PubMed abstract (PMID ${src.record_id}):`));}
 }else{assert.equal(await page.locator('#answer li').count(),0);}
 if(['unsupported','unsafe'].includes(name))assert.equal(data.trace.connectors_used.length,0);
 fs.writeFileSync(`${out}/${name}-api.json`,JSON.stringify(data,null,2));
 await page.screenshot({path:`${out}/${name}.png`,fullPage:true});
 results.push({name,question,status:data.status,claims:data.claims.length,pmids:data.sources.map(x=>x.record_id),connectors:data.trace.connectors_used,http_status:response.status(),cache_control:response.headers()['cache-control'],dom_text_attribution_citations:'PASS'});
 }
 assert.deepEqual(errors,[]);fs.writeFileSync(`${out}/browser-results.json`,JSON.stringify({results,errors},null,2));console.log(JSON.stringify(results,null,2));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
