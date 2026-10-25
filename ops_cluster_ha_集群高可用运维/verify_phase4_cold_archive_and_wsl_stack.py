#!/usr/bin/env python3
"""Phase 4 (D03/D05/D06): Edge LRU Pruning, 3-Host Cold-Archive Vault + T2 Spool, and WSL2 Stack Cold-Restart."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys
import time

from remote import BASE, copy, python_remote, run, ssh, win, wsl


def verify_edge_lru() -> dict:
    subprocess.run([sys.executable, str(BASE / 'deploy_edge.py')], check=True)
    subprocess.run([sys.executable, str(BASE / 'verify_edge.py')], check=True)
    edge_probe = """from pathlib import Path
import json
root = Path('/srv/kaoyan-edge/releases')
dirs = sorted([d.name for d in root.iterdir() if d.is_dir()])
total_bytes = sum(f.stat().st_size for f in root.rglob('*') if f.is_file())
assert len(dirs) <= 5, dirs
assert total_bytes < 16 * 1024 * 1024, total_bytes
print(json.dumps({'release_count': len(dirs), 'releases': dirs, 'total_bytes': total_bytes, 'budget_bytes': 16 * 1024 * 1024}))
"""
    return json.loads(python_remote('elena', edge_probe))


def verify_cold_archive_vault_3hosts() -> dict:
    # 1. Create verified cold snapshot of current production.sqlite3 on HP and export legacy archives from W1
    staged = json.loads((BASE / 'staged_runtime.json').read_text())['linux_staging']
    w1_export = f"""from pathlib import Path
import hashlib, json, shutil, sqlite3
arch = Path('/srv/kaoyan-docker/legacy-edge-archive')
stage = Path({staged!r})
stage.mkdir(parents=True, exist_ok=True)
prod_src = Path('/srv/kaoyan-docker/worker/production.sqlite3')
prod_cold = arch / 'production-cold-20261024.sqlite3'
with sqlite3.connect(prod_src) as s, sqlite3.connect(prod_cold) as d:
    s.backup(d)
    d.execute('PRAGMA journal_mode=DELETE')
with sqlite3.connect(prod_cold) as d:
    assert d.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
prod_cold.chmod(0o600)
names = ['legacy-kaoyan.sqlite3', 'legacy-kaoyan.pgbackup', 'production-cold-20261024.sqlite3']
manifest = {{}}
for n in names:
    p = arch / n
    assert p.exists(), n
    if n.endswith('.sqlite3'):
        with sqlite3.connect(p) as db:
            assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    shutil.copy2(p, stage / n)
    manifest[n] = {{'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}}
(arch / 'manifest.json').write_text(json.dumps(manifest, indent=2))
print(json.dumps(manifest))
"""
    manifest = json.loads(wsl('python3 -c ' + shlex.quote(w1_export)))
    scratch = BASE / 'scratchpad' / 'cold_archive_vault'
    scratch.mkdir(parents=True, exist_ok=True)
    for name, meta in manifest.items():
        local_f = scratch / name
        run(['scp', '-q', f'w1:kaoyan_docker_20261024/{name}', str(local_f)], timeout=60)
        local_f.chmod(0o600)
        assert hashlib.sha256(local_f.read_bytes()).hexdigest() == meta['sha256'], name

    # 2. Replicate and verify across HP and S1 cold_archive_vault
    host_verifications = {'W1': '/srv/kaoyan-docker/legacy-edge-archive'}
    for host in ('hp', 's1'):
        ssh(host, 'mkdir -p ~/kaoyan_live_20261024/cold_archive_vault && chmod 700 ~/kaoyan_live_20261024/cold_archive_vault')
        for name in manifest:
            copy(host, scratch / name, f'kaoyan_live_20261024/cold_archive_vault/{name}')
        verify_code = f"""from pathlib import Path
import hashlib, json, sqlite3
v = Path.home() / 'kaoyan_live_20261024/cold_archive_vault'
expected = {manifest!r}
for n, m in expected.items():
    p = v / n
    p.chmod(0o600)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == m['sha256'], n
    if n.endswith('.sqlite3'):
        with sqlite3.connect(p) as db:
            assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
(v / 'manifest.json').write_text(json.dumps(expected, indent=2))
print(str(v))
"""
        host_verifications[host.upper()] = python_remote(host, verify_code).strip()

    # 3. Probe T2 reachability from HP and persist deterministic T2 outbox spool manifest
    t2_probe = """from pathlib import Path
import json, subprocess
v = Path.home() / 'kaoyan_live_20261024/cold_archive_vault'
r = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=4', 't2', 'true'], capture_output=True, text=True)
t2_state = 'ONLINE_SYNCED' if r.returncode == 0 else 'CROSS_SUBNET_OFFLINE_QUEUED_ON_3HOSTS'
spool = {
    'target_node': 'T2',
    't2_state': t2_state,
    'verified_online_vault_hosts': ['W1', 'HP', 'S1'],
    'files': json.loads((v / 'manifest.json').read_text()),
}
(v / 't2_cold_offload_spool.json').write_text(json.dumps(spool, indent=2))
print(json.dumps(spool))
"""
    t2_spool = json.loads(python_remote('hp', t2_probe))
    edge_ret = {
        'status': 'PASS',
        'archive_on': 'W1 + HP + S1 3-Host Verified Cold Vault',
        'vault_paths': host_verifications,
        'archives': manifest,
        'deleted_databases': False,
        't2_offload_spool': t2_spool,
    }
    (BASE / 'edge_retirement.json').write_text(json.dumps(edge_ret, indent=2) + '\n')
    return edge_ret


def verify_wsl_systemd_stack_cold_restart() -> dict:
    t0 = time.monotonic()
    task_info = json.loads(
        win("Get-ScheduledTask 'KaoyanDockerWSL' | Select-Object TaskName,@{Name='State';Expression={$_.State.ToString()}} | ConvertTo-Json -Compress")
    )
    assert task_info['State'] == 'Running', task_info
    wsl('systemctl restart kaoyan-replica-tunnels kaoyan-containers', timeout=90)
    time.sleep(3.0)
    ssh('hp', 'sudo -n systemctl restart kaoyan-live-w1-tunnel && sudo -n systemctl restart kaoyan-w1-gateway-relay')
    time.sleep(2.0)
    subprocess.run([sys.executable, str(BASE / 'test_runtime_restart.py')], check=True)
    restart_res = json.loads((BASE / 'restart_result.json').read_text())
    return {
        'scheduled_task': task_info,
        'wsl_stack_cold_restart_seconds': round(time.monotonic() - t0, 3),
        'container_restart_checks': restart_res['checks'],
        'negative_health_control': restart_res['negative_health_control'],
    }


def main() -> None:
    edge_lru = verify_edge_lru()
    cold_vault = verify_cold_archive_vault_3hosts()
    wsl_restart = verify_wsl_systemd_stack_cold_restart()
    summary = {
        'status': 'PASS',
        'edge_lru': edge_lru,
        'cold_vault_3hosts': cold_vault,
        'wsl_stack_cold_restart': wsl_restart,
    }
    (BASE / 'phase4_cold_archive_and_wsl_stack.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
