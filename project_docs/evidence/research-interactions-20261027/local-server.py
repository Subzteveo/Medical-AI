import os,json,secrets,hashlib
from pathlib import Path
from datetime import datetime,timedelta,timezone
for k in list(os.environ):
 if k.lower().endswith('proxy') and k.lower() not in {'http_proxy','https_proxy','no_proxy'}: os.environ.pop(k)
os.environ['SSL_CERT_FILE']='/etc/ssl/certs/ca-certificates.crt'
out=Path(os.environ.get('MEDICAL_AI_INTERACTION_CAPTURE_DIR', '/tmp/medical-ai-interaction-evidence')); out.mkdir(exist_ok=True)
token=secrets.token_urlsafe(32)
(out/'local-token').write_text(token)
os.environ['MEDICAL_AI_PILOT_ACCESS_JSON']=json.dumps({'participants':[{'participant_id':'local-engineering-validation','credential_id':'ephemeral-test','token_sha256':hashlib.sha256(token.encode()).hexdigest(),'expires_at':(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat(),'revoked':False}]})
os.environ['MEDICAL_AI_PILOT_SESSION_SECRET']=secrets.token_urlsafe(48)
os.environ['MEDICAL_AI_PILOT_COOKIE_SECURE']='false'
os.environ['MEDICAL_AI_TRACE_DB']=str(out/'traces.sqlite3')
import httpx
original=httpx.AsyncClient.send
async def capture(self,request,*args,**kwargs):
 response=await original(self,request,*args,**kwargs)
 if request.url.host=='eutils.ncbi.nlm.nih.gov':
  await response.aread()
  filename=out/f'original-response-{len(list(out.glob("original-response-*")))}.json'
  filename.write_text(json.dumps({'url':str(request.url),'status':response.status_code,'retrieved_at':datetime.now(timezone.utc).isoformat(),'body':response.text},indent=2))
 return response
httpx.AsyncClient.send=capture
import uvicorn
from medical_ai.api import app
uvicorn.run(app,host='127.0.0.1',port=8766,log_level='warning',access_log=False)
