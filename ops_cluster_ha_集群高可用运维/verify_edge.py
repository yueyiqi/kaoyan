"""Verify public TLS, exact static bytes, API routing and source-file exclusion."""
import json
from remote import BASE, python_remote

release = json.loads((BASE/'edge_release.json').read_text())
code = """import hashlib,json,urllib.request,urllib.error
base='https://kaoyan-elena.duckdns.org'
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
checks=[]
for name,digest in HASHES.items():
 with opener.open(base+('/' if name=='index.html' else '/'+name),timeout=60) as r:
  assert r.status==200
  assert r.headers.get('X-Kaoyan-Frontend')=='ecs-static'
  assert hashlib.sha256(r.read()).hexdigest()==digest,name
  checks.append('ecs_static_hash_'+name)
with opener.open(base+'/api/health',timeout=60) as r:
 state=json.load(r);assert state['db_engine']=='portable_sqlite' and state['replicas_confirmed']>=2
 checks.append('api_routes_to_live_cluster')
try:opener.open(base+'/api/admin/db/drilldown',timeout=60)
except urllib.error.HTTPError as e:assert e.code==401;checks.append('admin_requires_login')
else:raise AssertionError('admin endpoint exposed')
with opener.open(base+'/kaoyan_runtime.py',timeout=60) as r:
 assert r.geturl()==base+'/'
 assert hashlib.sha256(r.read()).hexdigest()==HASHES['index.html']
 checks.append('python_source_not_served')
print(json.dumps({'status':'PASS','checks':checks,'health':state}))
""".replace('HASHES', repr(release['files']))
result = json.loads(python_remote('hp', code))
(BASE/'edge_acceptance.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result))
