#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kaoyan-elena.duckdns.org 自动接线 (auto-wire).

背景: 阿里云广州网关对所有 *.duckdns.org 的 SNI 注入 TCP RST (含从未配置的随机子域, 实测),
所以 DuckDNS 的 A 记录不能指向 elena(8.163.29.42), 必须指向香港边缘 CVM(43.160.227.166)。
本脚本等公共 DNS 指向边缘后: 备份并追加 CVM Caddy 站点 -> validate -> reload(不重启容器) -> 验证 HTTPS。
幂等; 不含任何 DuckDNS token; --dry-run 只判定不改动。
"""
import argparse
import datetime
import subprocess
import sys
import time

DOMAIN = "kaoyan-elena.duckdns.org"
EDGE = "43.160.227.166"
ORIGIN = "8.163.29.42:3389"
LOG = "/Users/liuzengyu/Library/Logs/kaoyan_duckdns_autowire.log"

REMOTE = r'''
import pathlib, shutil, time, subprocess, sys
p = pathlib.Path("/opt/ihg_hotel/10_deploy/Caddyfile")
s = p.read_text()
if "kaoyan-elena.duckdns.org {" in s:
    print("ALREADY_PRESENT")
else:
    shutil.copy(p, str(p) + ".bak." + str(int(time.time())))
    block = """
# [kaoyan-elena.duckdns.org] 广州ECS对 *.duckdns.org 注入RST -> 经香港边缘(免备案)回源 elena:3389, 强制 Host=127.0.0.1
kaoyan-elena.duckdns.org {
	encode gzip
	header {
		Cache-Control "no-cache, no-store, must-revalidate"
		X-Content-Type-Options "nosniff"
		X-Frame-Options "SAMEORIGIN"
	}
	handle {
		reverse_proxy 8.163.29.42:3389 {
			header_up Host 127.0.0.1
			header_up X-Real-IP {remote_host}
		}
	}
}
"""
    p.write_text(s.rstrip("\n") + "\n" + block)
    print("APPENDED")
v = subprocess.run(["docker", "exec", "caddy-proxy", "caddy", "validate", "--config", "/etc/caddy/Caddyfile"], capture_output=True, text=True)
if "Valid configuration" not in (v.stdout + v.stderr):
    print("VALIDATE_FAILED", (v.stdout + v.stderr)[-300:]); sys.exit(2)
r = subprocess.run(["docker", "exec", "caddy-proxy", "caddy", "reload", "--config", "/etc/caddy/Caddyfile"], capture_output=True, text=True)
print("RELOAD_RC", r.returncode)
sys.exit(r.returncode)
'''


def log(msg):
    line = f"[{datetime.datetime.now().isoformat()}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def sh(cmd, timeout=40, stdin=None):
    try:
        p = subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True, text=True, timeout=timeout, input=stdin)
        return (p.stdout + p.stderr).strip()
    except subprocess.TimeoutExpired:
        return "TIMEOUT"


def dns_points_to_edge():
    out = sh(f"ssh -o BatchMode=yes -o ConnectTimeout=8 elena 'dig @8.8.8.8 {DOMAIN} +short; dig @223.5.5.5 {DOMAIN} +short'")
    return EDGE in out.split(), out.replace("\n", " ")


def https_code(vantage):
    cmd = f"curl -s -o /dev/null -w %{{http_code}}_%{{ssl_verify_result}} --max-time 10 https://{DOMAIN}/"
    return sh(cmd if vantage == "m4" else f"ssh -o BatchMode=yes -o ConnectTimeout=8 cvm '{cmd}'", 30)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--wait-minutes", type=int, default=15)
    a = ap.parse_args()
    deadline = time.time() + a.wait_minutes * 60
    while True:
        ok, seen = dns_points_to_edge()
        if ok:
            break
        log(f"WAITING: DuckDNS A not {EDGE} yet (seen: {seen or 'empty'}); 请在 duckdns.org 把 {DOMAIN} 的 IP 改为 {EDGE}")
        if a.dry_run or time.time() > deadline:
            return 0
        time.sleep(15)
    log(f"DNS points to edge ({seen}); wiring CVM Caddy")
    if a.dry_run:
        return 0
    out = sh("ssh -o BatchMode=yes -o ConnectTimeout=8 cvm python3 -", 60, stdin=REMOTE)
    log("CVM: " + out.replace("\n", " | ")[-300:])
    end = time.time() + 240
    while time.time() < end:
        m4, cvm = https_code("m4"), https_code("cvm")
        log(f"verify m4={m4} cvm={cvm}")
        if m4 == "200_0" and cvm == "200_0":
            log("OK: https://%s 已上线" % DOMAIN)
            sh(f"osascript -e 'display notification \"https://{DOMAIN} 已上线\" with title \"kaoyan duckdns\"'")
            return 0
        time.sleep(15)
    log("FAIL: 4 分钟内未得到 200_0 (证书可能仍在签发; 可再次运行本脚本)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
