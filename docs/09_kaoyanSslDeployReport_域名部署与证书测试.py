#!/usr/bin/env python3
"""09_kaoyanSslDeployReport_域名部署与证书测试.py

Full-chain deployment, DNS, TLS certificate issuance, and P1/P2/P3 functional probe suite
for kaoyan.elenalyl.top and its underlying elena (8.163.29.42) + CVM (43.160.227.166) topology.
"""

from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def run_cmd(cmd: str, timeout: int = 15) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "rc": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except Exception as exc:
        return {"rc": -1, "stdout": "", "stderr": str(exc)}


def collect_probe_matrix() -> dict[str, Any]:
    now_utc = dt.datetime.now(dt.timezone.utc).isoformat()
    results: dict[str, Any] = {"timestamp_utc": now_utc, "layers": {}}

    # Layer 1: Registry & Registrar RDAP + Authoritative / TLD / Recursive DNS
    rdap_top = run_cmd("curl -sS -m 8 https://rdap.zdnsgtld.com/top/domain/elenalyl.top")
    rdap_status = []
    rdap_events = []
    if rdap_top["rc"] == 0 and rdap_top["stdout"]:
        try:
            payload = json.loads(rdap_top["stdout"])
            rdap_status = payload.get("status", [])
            rdap_events = payload.get("events", [])
        except Exception:
            pass

    dns_elena = run_cmd(
        'ssh -o ConnectTimeout=6 elena "'
        "dig @dns1.hichina.com kaoyan.elenalyl.top A +short; echo ---; "
        "dig @a.zdnscloud.com elenalyl.top NS +noall +comments; echo ---; "
        'dig @223.5.5.5 kaoyan.elenalyl.top A +noall +comments"'
    )
    dns_cvm = run_cmd(
        'ssh -o ConnectTimeout=6 cvm "'
        "dig @8.8.8.8 kaoyan.elenalyl.top A +noall +comments; echo ---; "
        'dig @1.1.1.1 kaoyan.elenalyl.top A +noall +comments"'
    )

    results["layers"]["L1_dns_and_registry"] = {
        "rdap_status": rdap_status,
        "rdap_events": rdap_events,
        "client_hold_active": any("client hold" in s.lower() for s in rdap_status),
        "elena_dns_probe": dns_elena["stdout"],
        "cvm_dns_probe": dns_cvm["stdout"],
    }

    # Layer 2: Edge Gateway (CVM 43.160.227.166) Caddy Config & ACME Certificate State
    cvm_caddy = run_cmd(
        'ssh -o ConnectTimeout=6 cvm "'
        "grep -n -A 15 'kaoyan.elenalyl.top {' /opt/ihg_hotel/10_deploy/Caddyfile || true; echo ---; "
        "docker exec caddy-proxy find /data/caddy -name '*elenalyl*' -o -name '*kaoyan*' 2>/dev/null || true; echo ---; "
        "docker logs caddy-proxy 2>&1 | grep -i 'kaoyan.elenalyl.top' | tail -n 6 || true\""
    )
    cvm_http80 = run_cmd(
        'ssh -o ConnectTimeout=6 cvm "'
        'curl -sI -m 5 --resolve kaoyan.elenalyl.top:80:127.0.0.1 http://kaoyan.elenalyl.top/ | head -n 5"'
    )
    cvm_tls443 = run_cmd(
        'ssh -o ConnectTimeout=6 cvm "'
        'curl -vI -m 5 --resolve kaoyan.elenalyl.top:443:127.0.0.1 https://kaoyan.elenalyl.top/ 2>&1 | tail -n 8"'
    )
    results["layers"]["L2_cvm_edge_and_acme"] = {
        "cvm_caddy_state": cvm_caddy["stdout"],
        "cvm_http80_redirect": cvm_http80["stdout"],
        "cvm_tls443_handshake": cvm_tls443["stdout"],
    }

    # Layer 3: Origin Host elena (8.163.29.42) Non-Root Service, Storage & Backhaul
    elena_runtime = run_cmd(
        'ssh -o ConnectTimeout=6 elena "'
        "systemctl is-active kaoyan-english-hub caddy; "
        "ps -o user:12,pid,comm,args -C python3 | grep kaoyan_hub_server || true; "
        'ls -lh /home/elena/kaoyan_storage/hot_db/kaoyan_hub.sqlite3*"'
    )
    cvm_to_elena = run_cmd(
        'ssh -o ConnectTimeout=6 cvm "'
        'curl -sS -m 6 -H Host:127.0.0.1 -w \\" HTTP_CODE=%{http_code} TIME=%{time_total}s\\" http://8.163.29.42:3389/api/health"'
    )
    results["layers"]["L3_elena_origin_and_backhaul"] = {
        "elena_runtime": elena_runtime["stdout"],
        "cvm_to_elena_backhaul": cvm_to_elena["stdout"],
    }

    # Layer 4: P1/P2/P3 Functional Probes across all deployed Kaoyan HTTPS endpoints
    endpoints = {
        "kaoyan_elenalyl_top": "https://kaoyan.elenalyl.top",
        "kaoyan_elena_nip_io": "https://kaoyan.8.163.29.42.nip.io",
        "kaoyan_cvm_nip_io": "https://kaoyan.43.160.227.166.nip.io",
        "kaoyan_liuzengyu_top": "https://kaoyan.liuzengyu.top",
    }
    ep_probes: dict[str, Any] = {}
    for name, base_url in endpoints.items():
        probe = run_cmd(
            f'curl -sS -m 6 -o /tmp/ep_{name}.out -w "HTTP=%{{http_code}} SSL=%{{ssl_verify_result}} TIME=%{{time_total}}s SIZE=%{{size_download}}" {base_url}/api/health 2>&1'
        )
        ep_probes[name] = {
            "url": base_url,
            "rc": probe["rc"],
            "metrics": probe["stdout"],
            "err": probe["stderr"],
        }

    # Deep API functional test on the live elena instance via https://kaoyan.8.163.29.42.nip.io
    api_checks = {}
    for route in ["/", "/api/health", "/api/state"]:
        r = run_cmd(
            f'curl -sS -m 6 -o /tmp/kaoyan_route.out -w "HTTP=%{{http_code}} SSL=%{{ssl_verify_result}} SIZE=%{{size_download}} TIME=%{{time_total}}s" "https://kaoyan.8.163.29.42.nip.io{route}"'
        )
        api_checks[f"GET {route}"] = r["stdout"]

    for route, payload in [
        ("/api/progress/anchor", '{"passage_id":"2010-T1","paragraph_idx":2,"sentence_idx":1,"scroll_pct":42}'),
        ("/api/vocab/lookup", '{"word":"intellectual"}'),
    ]:
        r = run_cmd(
            f'curl -sS -m 6 -X POST -H "Content-Type: application/json" -d \'{payload}\' -o /tmp/kaoyan_post.out -w "HTTP=%{{http_code}} SSL=%{{ssl_verify_result}} SIZE=%{{size_download}} TIME=%{{time_total}}s" "https://kaoyan.8.163.29.42.nip.io{route}"'
        )
        api_checks[f"POST {route}"] = r["stdout"]

    # Watcher daemon status on M4
    watcher_state = run_cmd("launchctl list | grep top.elenalyl.kaoyan.watch || true")
    results["layers"]["L4_endpoints_and_functional_matrix"] = {
        "endpoints": ep_probes,
        "elena_functional_routes": api_checks,
        "m4_watcher_daemon": watcher_state["stdout"],
    }
    return results


def main() -> int:
    matrix = collect_probe_matrix()
    out_json = Path("/tmp/09_kaoyan_elenalyl_top_test_report.json")
    out_json.write_text(json.dumps(matrix, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] Probe matrix written to {out_json}")
    l1 = matrix["layers"]["L1_dns_and_registry"]
    l3 = matrix["layers"]["L3_elena_origin_and_backhaul"]
    l4 = matrix["layers"]["L4_endpoints_and_functional_matrix"]
    print(f"  - elenalyl.top RDAP status: {l1['rdap_status']}")
    print(f"  - clientHold active: {l1['client_hold_active']}")
    print(f"  - CVM->elena:3389 backhaul: {l3['cvm_to_elena_backhaul'][:120]}...")
    for k, v in l4["endpoints"].items():
        print(f"  - Endpoint {k} ({v['url']}): rc={v['rc']} | {v['metrics']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
