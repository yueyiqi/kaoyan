#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""07 只读状态探针: ① 刀刃路由档位一致性 (ADR-0710)  ② kaoyan.elenalyl.top 上线阻塞项现状。
退出码恒为 0 (这是状态播报, 不是闸口); 用 JSON 里的 go_live 字段判断。不修改任何文件。
"""
import glob
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ADR_CHECK = glob.glob(str(ROOT / ".adr/701-800/701-710/adr_0710_*/adr_0710_*.py"))


def sh(cmd, timeout=40):
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return (p.stdout + p.stderr).strip()
    except subprocess.TimeoutExpired:
        return "TIMEOUT"


def main():
    r = {}
    adr = sh(f'/usr/bin/python3 "{ADR_CHECK[0]}"') if ADR_CHECK else "{}"
    try:
        r["blade_tier_consistent"] = json.loads(adr).get("consistent")
    except ValueError:
        r["blade_tier_consistent"] = None
    r["registry_status"] = sh(
        "curl -s --max-time 10 https://rdap.zdnsgtld.com/top/domain/elenalyl.top | "
        "python3 -c \"import sys,json;print(json.load(sys.stdin).get('status'))\"")
    r["dns_from_elena"] = sh(
        "ssh -o BatchMode=yes -o ConnectTimeout=8 elena "
        "'echo hichina=$(dig @dns1.hichina.com kaoyan.elenalyl.top +short) "
        "pub223=$(dig @223.5.5.5 kaoyan.elenalyl.top +short) pub88=$(dig @8.8.8.8 kaoyan.elenalyl.top +short) "
        "edge80=$(curl -s -o /dev/null -w %{http_code} --max-time 8 --resolve kaoyan.elenalyl.top:80:43.160.227.166 http://kaoyan.elenalyl.top/)'")
    r["watcher_last_log"] = sh("tail -n 1 ~/Library/Logs/kaoyan_elenalyl_watch.log | cut -c1-140")
    r["watcher_launchd"] = sh("launchctl print gui/$(id -u)/top.elenalyl.kaoyan.watch 2>&1 | grep -E 'run interval|last exit code' | tr -s '\\t ' ' ' | tr '\\n' ';'")
    r["go_live"] = "client hold" not in r["registry_status"] and "43.160.227.166" in r["dns_from_elena"].split("pub223=")[-1]
    print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
