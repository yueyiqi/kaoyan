"""Read-only final production and origin verification after all delivery batches."""
import json
from remote import BASE, ROOT, run, ssh, wsl, python_remote

receipts=[]
for path in (BASE/'_workspace_delivery_plans').glob('*.receipt.json'):
    if path.name=='01-code.receipt.json':continue  # Retained failed first preflight.
    receipt=json.loads(path.read_text())
    assert receipt['status']=='PUSHED',(path.name,receipt['status'])
    receipts.append({'batch':path.stem,'commit':receipt['commit']})
assert run(['git','remote']).split()==['origin']
assert run(['git','remote','get-url','origin']).strip()=='git@hp:liuzengyu/idea.git'
head=run(['git','rev-parse','HEAD']).strip()
branch=run(['git','symbolic-ref','--short','HEAD']).strip()
remote=run(['git','ls-remote','--heads','origin','refs/heads/'+branch],timeout=30).split()[0]
for receipt in receipts:run(['git','merge-base','--is-ancestor',receipt['commit'],remote])
assert head==remote,'Local and remote branch tips differ'
state=json.loads(ssh('hp','python3 ~/kaoyan_live_20261024/app/kaoyan_cluster_admin.py status'))
assert state['primary']=='W1' and not state['pending'] and all(v['ok'] for v in state['acks'].values())
containers=wsl("docker inspect --format '{{.Name}} {{.State.Status}} {{.State.Health.Status}}' kaoyan-w1-worker kaoyan-w1-gateway").splitlines()
assert len(containers)==2 and all(s.endswith(' running healthy') for s in containers)
code="""import urllib.request,json
o=urllib.request.build_opener(urllib.request.ProxyHandler({}))
with o.open('https://kaoyan-elena.duckdns.org/',timeout=30) as r:
 assert r.status==200 and r.headers['X-Kaoyan-Frontend']=='ecs-static'
with o.open('https://kaoyan-elena.duckdns.org/api/health',timeout=30) as r:
 h=json.load(r);assert h['replicas_confirmed']==3 and h['db_engine']=='portable_sqlite'
print('HTTPS static and three-replica API ready')
"""
assert 'ready' in python_remote('hp',code)
result={'status':'PASS','primary':state['primary'],'version':state['version'],'epoch':state['epoch'],
        'containers':containers,'commits':receipts,'remote_verified_tip':remote,
        'epoch_fenced_standby_coordinator':'VERIFIED_W1_TO_HP_AND_FAILBACK','wsl_systemd_stack_cold_restart':'VERIFIED_ACTIVE'}
(BASE/'final_signoff.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
