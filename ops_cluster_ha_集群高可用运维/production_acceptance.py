"""Run on HP against the requested HTTPS URL; test accounts are disabled afterward."""
from contextlib import closing
import base64
import json
from pathlib import Path
import secrets
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid

BASE=Path.home()/'kaoyan_live_20261024'
sys.path.insert(0,str(BASE/'app'))
from kaoyan_cluster_common import rpc
from kaoyan_portable import inventory
CFG=json.loads((BASE/'gateway.json').read_text())
PUBLIC='https://kaoyan-elena.duckdns.org'
checks=[];switches=[];latencies=[]
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))

def check(label,value):
    assert value,label
    checks.append(label)

def request(base,path,data=None,token=None,key=None):
    headers={'Content-Type':'application/json'}
    if token:headers['Authorization']='Bearer '+token
    if key:headers['X-Idempotency-Key']=key
    req=urllib.request.Request(base+path,data=json.dumps(data,ensure_ascii=False).encode() if data is not None else None,headers=headers)
    start=time.monotonic()
    try:r=opener.open(req,timeout=90)
    except urllib.error.HTTPError as e:r=e
    with r:body=r.read();status=r.status
    latencies.append(round((time.monotonic()-start)*1000,2))
    return status,json.loads(body)

def control(op,**kwargs):
    status,data=request('http://127.0.0.1:'+str(CFG['port']),'/_cluster/control',{'op':op,**kwargs},CFG['token'])
    assert status==200,(op,status)
    return data

def main():
    code,health=request(PUBLIC,'/api/health')
    check('HTTPS_live_cluster',code==200 and health['db_engine']=='portable_sqlite' and health['replicas_confirmed']==3)
    check('default_W1',control('status')['primary']=='W1')
    with closing(sqlite3.connect(BASE/'data/production.sqlite3')) as conn:
        admin=conn.execute("SELECT token_secret FROM sys_users WHERE role='ADMIN' AND account_status='ACTIVE' LIMIT 1").fetchone()[0]
    user='docker_accept_'+uuid.uuid4().hex[:8];password=secrets.token_urlsafe(20)
    created=False
    try:
        code,_=request(PUBLIC,'/api/admin/users',{'username':user,'passcode':password,'display_name':'容器部署验收临时账号'},admin,'create-'+user)
        check('public_account_write',code==200);created=True
        code,login=request(PUBLIC,'/api/auth/login',{'username':user,'passcode':password},key='login-'+user)
        check('public_login',code==200);token=login['token']
        check('guest_admin_denied',request(PUBLIC,'/api/admin/db/drilldown')[0]==401)
        check('scholar_admin_denied',request(PUBLIC,'/api/admin/db/drilldown',token=token)[0]==403)
        subprocess.run(['sudo','-n','systemctl','stop','kaoyan-live-s1-tunnel'],check=True)
        try:
            code,data=request(PUBLIC,'/api/vocab/lookup',{'lemma':'docker-partition'},token,'partition-'+user)
            check('write_during_real_replica_link_loss',code==200 and data['lookup_count']==1)
            code,health=request(PUBLIC,'/api/health')
            check('degraded_status_truthful',code==200 and health['replicas_confirmed']==2)
        finally:
            subprocess.run(['sudo','-n','systemctl','start','kaoyan-live-s1-tunnel'],check=True)
        for _ in range(20):
            state=control('recover')
            if all(v['ok'] for v in state['acks'].values()):break
            time.sleep(.5)
        check('replica_reconnected_and_caught_up',all(v['ok'] for v in state['acks'].values()))
        for i,node in enumerate(['S1','HP','W1']):
            state=control('switch',target=node)
            switches.append({'node':node,'ms':state['switch_ms'],'epoch':state['epoch']})
            check('primary_selected_'+node,state['primary']==node)
            payload={'lemma':'docker-acceptance','contextual_meaning':'跨平台容器验收 /ə/'}
            code,data=request(PUBLIC,'/api/vocab/lookup',payload,token,'write-'+user+'-'+node)
            check('public_write_'+node,code==200 and data['lookup_count']==i+1)
            code,replay=request(PUBLIC,'/api/vocab/lookup',payload,token,'write-'+user+'-'+node)
            check('idempotent_replay_'+node,code==200 and replay==data)
            actual=rpc(CFG['workers'][node],CFG['token'],{'op':'status'})
            check('real_worker_os_'+node,actual['os']=={'HP':'Linux','W1':'Linux','S1':'Darwin'}[node])
            check('production_path_'+node,'production.sqlite3' in actual['database'] and actual['role']=='leader')
            if node=='W1':check('container_volume_path',actual['database']=='/data/production.sqlite3')
    finally:
        # Restore the requested default primary even if a later assertion fails.
        control('switch',target='W1')
        if created:
            code,_=request(PUBLIC,'/api/admin/users/role_status',{'target_user_id':user,'account_status':'DISABLED'},admin,'disable-'+user)
            check('temporary_account_disabled',code==200)
    state=control('recover')
    workers={n:rpc(u,CFG['token'],{'op':'status'}) for n,u in CFG['workers'].items()}
    check('complete_table_values_match',all(s['tables']==state['tables'] for s in workers.values()))
    check('complete_DDL_matches',len({s['schema_sha256'] for s in workers.values()})==1)
    package=rpc(CFG['workers']['W1'],CFG['token'],{'op':'snapshot','epoch':state['epoch']})
    dest=BASE/'docker-accepted.sqlite3';dest.write_bytes(base64.b64decode(package['database']));dest.chmod(0o600)
    source=BASE/'docker-cutover-backup/production.sqlite3'
    with closing(sqlite3.connect(source)) as before,closing(sqlite3.connect(dest)) as after:
        check('all_source_tables_preserved',set(inventory(before))==set(inventory(after)))
        for table in inventory(before):
            if table=='ha_cluster_meta':continue  # The protocol version must advance.
            cols=[r[1] for r in before.execute('PRAGMA table_info("'+table+'")')]
            quoted=','.join('"'+c+'"' for c in cols)
            old=set(before.execute('SELECT '+quoted+' FROM "'+table+'"'))
            new=set(after.execute('SELECT '+quoted+' FROM "'+table+'"'))
            check('historical_rows_'+table,old<=new)
    result={'status':'PASS','checks':checks,'assertions':len(checks),'switches':switches,'latencies_ms':latencies,
            'tables':len(state['tables']),'final_primary':state['primary'],'final_version':state['version'],
            'workers':{n:{k:s[k] for k in ['os','machine','python','sqlite','database','role','epoch','version']} for n,s in workers.items()}}
    (BASE/'docker-production-acceptance.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
