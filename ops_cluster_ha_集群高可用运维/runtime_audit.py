"""Read-only runtime audit: observe processes, durable state and routing, no secrets."""
import concurrent.futures, json, shlex
from remote import BASE, PROJECT, ssh, win, wsl, python_remote

def hp():
 code="""from pathlib import Path
import json,sys
p=Path.home()/'kaoyan_live_20261024';sys.path.insert(0,str(p/'app'))
from kaoyan_cluster_common import rpc
cfg=json.loads((p/'gateway.json').read_text())
import urllib.request
req=urllib.request.Request('http://127.0.0.1:'+str(cfg['port'])+'/_cluster/control',data=b'{"op":"status"}',headers={'Authorization':'Bearer '+cfg['token']})
with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req,timeout=60) as r: state=json.load(r)
workers={n:rpc(u,cfg['token'],{'op':'status'}) for n,u in cfg['workers'].items()}
print(json.dumps({'state':state,'workers':workers,'hp_standby_coordinator_bytes':Path(cfg['state']).stat().st_size}))
"""
 return json.loads(python_remote('hp',code))
def w1_docker():
 code="""from pathlib import Path
import json,subprocess
coord=Path('/srv/kaoyan-docker/gateway/production_coordinator.sqlite3')
worker_db=Path('/srv/kaoyan-docker/worker/production.sqlite3')
containers=subprocess.check_output(['docker','inspect','--format','{{.Name}} {{.State.Status}} {{.State.Health.Status}}','kaoyan-w1-worker','kaoyan-w1-gateway'],text=True).splitlines()
print(json.dumps({'w1_coordinator_bytes':coord.stat().st_size if coord.exists() else 0,'w1_worker_db_bytes':worker_db.stat().st_size if worker_db.exists() else 0,'containers':containers}))
"""
 return json.loads(wsl('python3 -c '+shlex.quote(code)))
def elena():
 code="""from pathlib import Path
import json,subprocess
cfg=subprocess.check_output(['sudo','-n','cat','/etc/caddy/Caddyfile'],text=True)
print(json.dumps({'caddy':cfg,'memory':Path('/proc/meminfo').read_text().splitlines()[:3],'pg_running':subprocess.call(['systemctl','is-active','--quiet','postgresql@18-main'])==0}))
"""
 return json.loads(python_remote('elena',code))
def main():
 result={}
 with concurrent.futures.ThreadPoolExecutor(3) as pool:
  futures={pool.submit(f):n for n,f in [('cluster',hp),('w1_docker',w1_docker),('edge',elena)]}
  for f,n in futures.items(): result[n]=f.result()
 result['frontend_framework_imports']=[l.strip() for l in (PROJECT/'index.html').read_text().splitlines() if '<script src=' in l]
 (BASE/'runtime_baseline.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
 c=result['cluster'];w=result['w1_docker']
 print(json.dumps({'primary':c['state']['primary'],'version':c['state']['version'],'tables':len(c['state']['tables']),'w1_coordinator_bytes':w['w1_coordinator_bytes'],'w1_containers':w['containers'],'workers':{n:{k:x[k] for k in ['os','database','ready','role']} for n,x in c['workers'].items()},'edge_static': 'file_server' in result['edge']['caddy']},ensure_ascii=False))
if __name__=='__main__':main()
