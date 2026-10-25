"""Move the single durable authority while retaining an exact rollback snapshot."""
import json
import shlex
import time
from remote import BASE, ssh, win, wsl, copy, run, python_remote

ports = json.loads((BASE/'ports.json').read_text())
staged = json.loads((BASE/'staged_runtime.json').read_text())
windows_stage = 'kaoyan_docker_20261024'
linux_stage = staged['linux_staging']

def control(op, target=None):
    suffix = ' '+target if target else ''
    return json.loads(ssh('hp', 'python3 ~/kaoyan_live_20261024/app/kaoyan_cluster_admin.py '+op+suffix,timeout=40))

def export_hp():
    code = """from pathlib import Path
import sqlite3,json,base64,zipfile,os
base=Path.home()/'kaoyan_live_20261024';cfg=json.loads((base/'gateway.json').read_text())
out=base/'docker-cutover-backup';out.mkdir(mode=448,exist_ok=True)
with sqlite3.connect(cfg['state']) as src,sqlite3.connect(out/'state.sqlite3') as dst:src.backup(dst)
with sqlite3.connect(out/'state.sqlite3') as db:state=json.loads(db.execute('SELECT state FROM coordinator').fetchone()[0])
(out/'production.sqlite3').write_bytes(base64.b64decode(state['snapshot']['database']))
with zipfile.ZipFile(out/'authority.zip','w',zipfile.ZIP_DEFLATED) as z:
 for n in ['state.sqlite3','production.sqlite3']:z.write(out/n,n)
(out/'authority.zip').chmod(384)
print(json.dumps({'primary':state['primary'],'epoch':state['epoch'],'version':state['snapshot']['version'],
 'pending':bool(state['pending']),'tables':state['snapshot']['tables'],'schema_sha256':state['snapshot']['schema_sha256']}))
"""
    meta = json.loads(python_remote('hp', code))
    (BASE/'cutover_source.json').write_text(json.dumps(meta, indent=2))
    package = BASE/'scratchpad/authority.zip'
    run(['scp','-q','hp:kaoyan_live_20261024/docker-cutover-backup/authority.zip',str(package)],timeout=120)
    package.chmod(0o600)
    copy('w1',package,windows_stage+'/authority.zip')
    return meta

def install_w1():
    code = """from pathlib import Path
import zipfile,os,sqlite3,hashlib,time,subprocess
b=Path('/srv/kaoyan-docker');z=zipfile.ZipFile(Path(STAGE)/'authority.zip')
assert set(z.namelist())=={'state.sqlite3','production.sqlite3'}
running=subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines()
assert not {'kaoyan-w1-gateway','kaoyan-w1-worker'} & set(running), 'New authority must be stopped before seed/restore'
for source,dest in [('state.sqlite3',b/'gateway/production_coordinator.sqlite3'),('production.sqlite3',b/'worker/production.sqlite3')]:
 if dest.exists():
  saved=b/'retained-failed-cutovers'/str(time.time_ns());saved.mkdir(parents=True)
  with sqlite3.connect(dest) as src,sqlite3.connect(saved/source) as dst:src.backup(dst)
 incoming=dest.with_suffix('.incoming');incoming.write_bytes(z.read(source))
 with sqlite3.connect(incoming) as src,sqlite3.connect(dest) as dst:src.backup(dst)
 incoming.unlink();dest.chmod(384);os.chown(dest,1000,1000)
 with sqlite3.connect(dest) as db:assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
(Path(STAGE)/'authority.zip').unlink()
print('authority databases installed with integrity checks')
""".replace('STAGE',repr(linux_stage))
    print(wsl('python3 -c '+shlex.quote(code)).strip(),flush=True)
    # The former native worker keeps its historical files, but cannot accept traffic.
    win("Stop-ScheduledTask 'KaoyanLiveWorker'; Disable-ScheduledTask 'KaoyanLiveWorker' | Out-Null")
    ssh('hp','sudo -n install -m 644 ~/kaoyan_live_20261024/w1-tunnel-docker.service /etc/systemd/system/kaoyan-live-w1-tunnel.service && sudo -n systemctl daemon-reload && sudo -n systemctl restart kaoyan-live-w1-tunnel')
    print(wsl('systemctl enable --now kaoyan-containers; systemctl is-active kaoyan-containers',timeout=120).strip(),flush=True)

def rollback():
    # Never revive the pre-cutover snapshot after the new coordinator has run.
    print('restoring latest authority to the previous gateway',flush=True)
    wsl('docker stop kaoyan-w1-gateway >/dev/null 2>&1 || true')
    code = """from pathlib import Path
import sqlite3,shutil
p=Path('/srv/kaoyan-docker/gateway/production_coordinator.sqlite3');target=Path(STAGE)/'rollback-state.sqlite3'
if p.exists():
 with sqlite3.connect(p) as src,sqlite3.connect(target) as dst:src.backup(dst)
 print('EXPORTED')
else:print('NO_NEW_STATE')
""".replace('STAGE',repr(linux_stage))
    exported = wsl('python3 -c '+shlex.quote(code))
    if 'EXPORTED' in exported:
        f=BASE/'scratchpad/rollback-state.sqlite3'
        run(['scp','-q','w1:'+windows_stage+'/rollback-state.sqlite3',str(f)],timeout=120);f.chmod(0o600)
        copy('hp',f,'kaoyan_live_20261024/rollback-state.sqlite3')
        python_remote('hp',"from pathlib import Path; import json,sqlite3; b=Path.home()/'kaoyan_live_20261024';c=json.loads((b/'gateway.json').read_text());s=sqlite3.connect(b/'rollback-state.sqlite3');d=sqlite3.connect(c['state']);s.backup(d);d.close();s.close()")
    ssh('hp','sudo -n systemctl disable --now kaoyan-w1-gateway-relay || true')
    wsl('systemctl disable --now kaoyan-containers || true')
    ssh('hp','sudo -n cp /etc/systemd/system/kaoyan-live-w1-tunnel.service.before-docker /etc/systemd/system/kaoyan-live-w1-tunnel.service && sudo -n systemctl daemon-reload && sudo -n systemctl restart kaoyan-live-w1-tunnel')
    win("Enable-ScheduledTask 'KaoyanLiveWorker' | Out-Null; Start-ScheduledTask 'KaoyanLiveWorker'")
    ssh('hp','sudo -n systemctl enable --now kaoyan-live-gateway')
    state=control('recover')
    (BASE/'rollback_result.json').write_text(json.dumps(state,indent=2))

def main():
    before = control('recover')
    assert all(x['ok'] for x in before['acks'].values()) and not before['pending']
    start = time.monotonic()
    ssh('hp','sudo -n systemctl stop kaoyan-live-gateway')
    try:
        meta=export_hp()
        install_w1()
        ssh('hp','sudo -n systemctl disable kaoyan-live-gateway && sudo -n systemctl enable --now kaoyan-w1-gateway-relay')
        for attempt in range(5):
            try:
                recovered=control('recover')
                if all(x['ok'] for x in recovered['acks'].values()):break
            except Exception:
                if attempt==4:raise
            time.sleep(1)
        else:raise RuntimeError('Three replicas did not rejoin')
        state=control('switch','W1')
        assert state['primary']=='W1' and all(x['ok'] for x in state['acks'].values())
        result={'status':'PASS','gateway_host':'W1','runtime':'Docker on WSL2',
                'source_version':meta['version'],'state':state,
                'maintenance_seconds':round(time.monotonic()-start,3)}
        (BASE/'cutover_result.json').write_text(json.dumps(result,indent=2))
        print(json.dumps(result),flush=True)
    except Exception:
        rollback()
        raise

if __name__=='__main__':main()
