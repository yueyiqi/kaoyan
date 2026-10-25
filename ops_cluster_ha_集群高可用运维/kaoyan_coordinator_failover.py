#!/usr/bin/env python3
"""Phase 3 (D04/B05): Epoch-fenced Standby Coordinator Failover (W1 -> HP) & Failback (HP -> W1)."""
from __future__ import annotations
import json
from pathlib import Path
import shlex
import time

from remote import BASE, copy, python_remote, run, ssh, wsl


def control(op: str, target: str | None = None) -> dict:
    suffix = f' {target}' if target else ''
    return json.loads(
        ssh('hp', f'python3 ~/kaoyan_live_20261024/app/kaoyan_cluster_admin.py --include-tables {op}{suffix}', timeout=45)
    )


def seed_hp_standby_from_local_replica(next_epoch: int) -> dict:
    code = f"""from pathlib import Path
import json, sqlite3, sys
base = Path.home() / 'kaoyan_live_20261024'
sys.path.insert(0, str(base / 'app'))
from kaoyan_cluster_common import snapshot as export_snapshot
cfg = json.loads((base / 'gateway.json').read_text())
worker_cfg = json.loads((base / 'worker.json').read_text())
db_path = Path(worker_cfg['database'])
fence_path = db_path.with_suffix('.fence.json')
fence = json.loads(fence_path.read_text()) if fence_path.exists() else {{'epoch': 0}}
assert {next_epoch} > int(fence.get('epoch', 0)), (fence, {next_epoch})
snap = export_snapshot(db_path)
state_obj = {{
    'primary': 'HP',
    'epoch': {next_epoch},
    'snapshot': snap,
    'pending': None,
}}
state_path = Path(cfg['state'])
state_path.parent.mkdir(parents=True, exist_ok=True)
with sqlite3.connect(state_path) as db:
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('PRAGMA synchronous=FULL')
    db.execute('CREATE TABLE IF NOT EXISTS coordinator (singleton INTEGER PRIMARY KEY CHECK(singleton=1), state TEXT NOT NULL)')
    db.execute('INSERT OR REPLACE INTO coordinator VALUES (1, ?)', (json.dumps(state_obj),))
    assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
print(json.dumps({{'seeded_primary': 'HP', 'seeded_epoch': {next_epoch}, 'version': snap['version'], 'tables': len(snap['tables'])}}))
"""
    return json.loads(python_remote('hp', code))


def probe_public_https(expected_replicas: int) -> dict:
    code = f"""import json, time, urllib.request
opener = urllib.request.build_opener(urllib.request.ProxyHandler({{}}))
t0 = time.monotonic()
with opener.open('https://kaoyan-elena.duckdns.org/api/health', timeout=30) as r:
    health = json.load(r)
health_ms = round((time.monotonic() - t0) * 1000, 2)
assert health['status'] == 'ok' and health['replicas_confirmed'] == {expected_replicas}, health
t1 = time.monotonic()
with opener.open('https://kaoyan-elena.duckdns.org/api/passages', timeout=30) as r:
    assert r.status == 200
    body = r.read()
read_ms = round((time.monotonic() - t1) * 1000, 2)
print(json.dumps({{'health': health, 'health_ms': health_ms, 'read_ms': read_ms, 'passages_bytes': len(body)}}))
"""
    return json.loads(python_remote('hp', code))


def export_hp_state_to_w1() -> None:
    hp_export = """from pathlib import Path
import json, sqlite3
base = Path.home() / 'kaoyan_live_20261024'
cfg = json.loads((base / 'gateway.json').read_text())
out = base / 'failback_state.sqlite3'
with sqlite3.connect(cfg['state']) as src, sqlite3.connect(out) as dst:
    src.backup(dst)
out.chmod(0o600)
print('HP_STATE_EXPORTED')
"""
    assert 'HP_STATE_EXPORTED' in python_remote('hp', hp_export)
    scratch = BASE / 'scratchpad'
    scratch.mkdir(exist_ok=True)
    local_state = scratch / 'failback_state.sqlite3'
    run(['scp', '-q', 'hp:kaoyan_live_20261024/failback_state.sqlite3', str(local_state)], timeout=60)
    local_state.chmod(0o600)
    copy('w1', local_state, 'kaoyan_docker_20261024/failback_state.sqlite3')
    staged = json.loads((BASE / 'staged_runtime.json').read_text())['linux_staging']
    w1_install = f"""from pathlib import Path
import os, sqlite3
src_path = Path({staged!r}) / 'failback_state.sqlite3'
dst_path = Path('/srv/kaoyan-docker/gateway/production_coordinator.sqlite3')
with sqlite3.connect(src_path) as src, sqlite3.connect(dst_path) as dst:
    src.backup(dst)
dst_path.chmod(0o600)
os.chown(dst_path, 1000, 1000)
with sqlite3.connect(dst_path) as db:
    assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
src_path.unlink(missing_ok=True)
print('W1_STATE_INSTALLED')
"""
    assert 'W1_STATE_INSTALLED' in wsl('python3 -c ' + shlex.quote(w1_install))


def main() -> None:
    before = control('recover')
    assert before['primary'] == 'W1' and all(v['ok'] for v in before['acks'].values()), before
    initial_epoch = int(before['epoch'])
    initial_version = int(before['version'])
    initial_tables = before['tables']

    t_failover_start = time.monotonic()
    try:
        # 1. Simulate W1 container stack outage (stop both gateway & worker on W1)
        wsl('systemctl stop kaoyan-containers', timeout=60)
        running_during_outage = wsl("docker ps --format '{{.Names}}'").strip().splitlines()
        assert not {'kaoyan-w1-gateway', 'kaoyan-w1-worker'} & set(running_during_outage), running_during_outage

        # 2. Activate HP standby coordinator fenced at epoch + 1 from HP local replica
        ssh('hp', 'sudo -n systemctl stop kaoyan-w1-gateway-relay')
        seeded = seed_hp_standby_from_local_replica(initial_epoch + 1)
        ssh('hp', 'sudo -n systemctl start kaoyan-live-gateway')
        standby_state = control('recover')
        failover_seconds = round(time.monotonic() - t_failover_start, 3)

        assert standby_state['primary'] == 'HP', standby_state
        assert standby_state['epoch'] == initial_epoch + 1, standby_state
        assert standby_state['acks']['HP']['ok'] and standby_state['acks']['S1']['ok'], standby_state
        assert not standby_state['acks']['W1']['ok'], standby_state
        assert standby_state['tables'] == initial_tables

        # Verify public HTTPS serves traffic with 2/3 quorum while W1 is completely stopped
        failover_https = probe_public_https(expected_replicas=2)

        # 3. Failback to W1 Docker authority at epoch + 2
        t_failback_start = time.monotonic()
        ssh('hp', 'sudo -n systemctl stop kaoyan-live-gateway')
        export_hp_state_to_w1()
        wsl('systemctl start kaoyan-containers', timeout=90)
        ssh('hp', 'sudo -n systemctl restart kaoyan-live-w1-tunnel && sudo -n systemctl start kaoyan-w1-gateway-relay')

        for attempt in range(8):
            try:
                rec = control('recover')
                if all(v['ok'] for v in rec['acks'].values()):
                    break
            except Exception:
                if attempt == 7:
                    raise
            time.sleep(1.5)
        else:
            raise RuntimeError('W1 failback did not regain 3/3 worker acknowledgements')

        restored = control('switch', 'W1')
        failback_seconds = round(time.monotonic() - t_failback_start, 3)
        assert restored['primary'] == 'W1' and restored['epoch'] == initial_epoch + 2, restored
        assert all(v['ok'] for v in restored['acks'].values()), restored
        assert restored['tables'] == initial_tables

        failback_https = probe_public_https(expected_replicas=3)
    except Exception:
        # Emergency self-heal: ensure W1 containers and HP relay are running
        wsl('systemctl start kaoyan-containers || true', timeout=90)
        ssh('hp', 'sudo -n systemctl stop kaoyan-live-gateway || true; sudo -n systemctl restart kaoyan-live-w1-tunnel || true; sudo -n systemctl start kaoyan-w1-gateway-relay || true')
        raise

    summary = {
        'status': 'PASS',
        'initial': {'primary': 'W1', 'epoch': initial_epoch, 'version': initial_version},
        'failover_to_hp': {
            'w1_containers_stopped': True,
            'seeded': seeded,
            'primary': standby_state['primary'],
            'epoch': standby_state['epoch'],
            'acks': standby_state['acks'],
            'failover_seconds': failover_seconds,
            'public_https': failover_https,
        },
        'failback_to_w1': {
            'primary': restored['primary'],
            'epoch': restored['epoch'],
            'version': restored['version'],
            'acks': restored['acks'],
            'switch_ms': restored['switch_ms'],
            'failback_seconds': failback_seconds,
            'public_https': failback_https,
        },
        'table_hashes_preserved': restored['tables'] == initial_tables,
    }
    (BASE / 'coordinator_failover_result.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
