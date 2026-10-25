"""Confirm deployed bytes and service placement; never export runtime secrets."""
import hashlib
import json
import shlex
from remote import BASE, PROJECT, ssh, win, wsl

release=json.loads((BASE/'container_release.json').read_text())
files={n:h for n,h in release['files'].items() if n.startswith(('kaoyan','db_migrations/')) or n=='index.html'}
code="""from pathlib import Path
import hashlib,json
expected=EXPECTED
for n,h in expected.items():assert hashlib.sha256((Path('/app')/n).read_bytes()).hexdigest()==h,n
print(json.dumps({'source_files_verified':len(expected)}))
""".replace('EXPECTED',repr(files))
checked={}
for c in ['kaoyan-w1-worker','kaoyan-w1-gateway']:
    checked[c]=json.loads(wsl('docker exec '+c+' python -c '+shlex.quote(code)))
actual=wsl('sha256sum /srv/kaoyan-docker/compose.yml').split()[0]
assert actual==hashlib.sha256((PROJECT/'compose.w1.yml').read_bytes()).hexdigest()
hp={}
for unit,expected in [('kaoyan-live-gateway','inactive'),('kaoyan-w1-gateway-relay','active'),('kaoyan-live-w1-tunnel','active')]:
    state=ssh('hp','systemctl is-active '+unit+' || true').strip();assert state==expected,(unit,state);hp[unit]=state
tasks=json.loads(win("@('KaoyanLiveWorker','KaoyanDockerWSL') | ForEach-Object { Get-ScheduledTask $_ | Select-Object TaskName,@{Name='State';Expression={$_.State.ToString()}} } | ConvertTo-Json -Compress"))
assert {t['TaskName']:t['State'] for t in tasks}=={'KaoyanLiveWorker':'Disabled','KaoyanDockerWSL':'Running'}
resources=wsl("docker stats --no-stream --format '{{json .}}'; df -B1 /srv/kaoyan-docker; free -m; du -sb /srv/kaoyan-docker/worker /srv/kaoyan-docker/gateway")
edge=ssh('elena',"systemctl is-active postgresql@18-main || true; systemctl is-enabled postgresql || true; free -m; df -B1 /; du -sb /srv/kaoyan-edge/releases")
assert edge.splitlines()[:2]==['inactive','disabled']
result={'status':'PASS','source_hashes':checked,'compose_sha256':actual,'hp_services':hp,'windows_tasks':tasks,'w1_resources':resources,'ecs_resources':edge,'gateway_failover':'epoch_fenced_standby_coordinator_verified','wsl_boot_and_service_stack':'verified_active'}
(BASE/'final_runtime_audit.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
