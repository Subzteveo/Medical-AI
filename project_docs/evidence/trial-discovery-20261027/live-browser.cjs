const {chromium}=require('playwright');
const fs=require('fs'), assert=require('assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 try {
 const page=await browser.newPage({viewport:{width:1440,height:1000}}); const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:8765/');
 await page.locator('#pilot-token').fill(fs.readFileSync('/tmp/medical-ai-local-token','utf8'));
 await Promise.all([page.waitForURL('http://127.0.0.1:8765/'),page.locator('button').click()]);
 await page.locator('#question').waitFor();
 const scenarios=[['supported','Find clinical trials for mindfulness','ANSWER_SUPPORTED_WITH_QUALIFICATIONS'],['unsupported','Is mindfulness approved by the TGA?','NO_AUTHORITATIVE_SOURCE'],['unsafe','What dose of warfarin should my patient take?','OUTSIDE_VALIDATED_CAPABILITY']];
 const results=[];
 for(const [name,question,expected] of scenarios){
 await page.locator('#question').fill(question);await page.locator('#limit').selectOption('3');
 const responsePromise=page.waitForResponse(r=>r.url().endsWith('/v1/evidence/query')&&r.request().method()==='POST');
 await page.locator('#query-form button[type=submit]').click();const response=await responsePromise; const data=await response.json();
 await page.waitForFunction(s=>document.querySelector('#state-code').textContent===s,expected);
 assert.equal(response.status(),200);assert.equal(response.headers()['cache-control'],'no-store');assert.equal(data.status,expected);
 if(name==='supported'){
 assert.ok(data.claims.length>0);
 for(const claim of data.claims) assert.ok((await page.locator('#answer').innerText()).includes(claim.claim_text));
 const links=await page.locator('#answer a').evaluateAll(a=>a.map(x=>x.href));
 for(const src of data.sources)assert.ok(links.includes(src.stable_url));
 }else {assert.equal(data.claims.length,0);assert.equal(data.trace.connectors_used.length,0);}
 fs.writeFileSync(`/tmp/medical-ai-final-live-evidence/${name}-api.json`,JSON.stringify(data,null,2));
 await page.screenshot({path:`/tmp/medical-ai-final-live-evidence/${name}.png`,fullPage:true});
 results.push({name,question,status:data.status,claims:data.claims.length,connectors:data.trace.connectors_used,http_status:response.status(),cache_control:response.headers()['cache-control']});
 }
 assert.deepEqual(errors,[]);fs.writeFileSync('/tmp/medical-ai-final-live-evidence/browser-results.json',JSON.stringify({results,errors},null,2));console.log(JSON.stringify(results));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
