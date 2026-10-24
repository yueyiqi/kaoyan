#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""06 · elenalyl.top 域名解封自动上线守护脚本

功能：
1. 检查 ~/Library/Application Support/kaoyan_elenalyl_watch/DONE，存在则直接 exit 0
2. 通过 ssh elena 探测公共 DNS (223.5.5.5 / 8.8.8.8) kaoyan.elenalyl.top A 记录是否解析为 43.160.227.166
   未解析则记录 WAITING 日志后 exit 0 (同时记录 RDAP 状态)
3. 放行后执行 ssh cvm "docker exec caddy-proxy caddy reload --config /etc/caddy/Caddyfile --force" 重置退避
4. 每 20 秒探测一次 (最多 10 分钟): ssh elena "curl -s -o /dev/null -w %{http_code}_%{ssl_verify_result} --max-time 10 https://kaoyan.elenalyl.top/"
   得到 200_0 即成功
5. 成功后通过 Unix Domain Socket 清除 M4 本机 mihomo DNS/Fake-IP 缓存，写入 DONE 标记，发送 macOS 桌面通知
6. 超时未成功则记录 FAIL 及最后一次探测值，不写 DONE 等下次重试
支持 --dry-run 参数：仅执行第 2 步判定与打印，不触发 reload 与 flush
"""

import sys
import os
import time
import subprocess
import json
import socket
from datetime import datetime

LOG_PATH = os.path.expanduser("~/Library/Logs/kaoyan_elenalyl_watch.log")
DONE_DIR = os.path.expanduser("~/Library/Application Support/kaoyan_elenalyl_watch")
DONE_PATH = os.path.join(DONE_DIR, "DONE")
SOCKET_PATH = "/var/run/clash-verge-service/users/502/verge-mihomo.sock"
TARGET_IP = "43.160.227.166"
DOMAIN = "kaoyan.elenalyl.top"
RDAP_URL = "https://rdap.zdnsgtld.com/top/domain/elenalyl.top"

def log(msg, to_stdout=False):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    ts = datetime.now().isoformat()
    line = f"[{ts}] {msg}"
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    if to_stdout:
        print(line)

def run_ssh(host, cmd, timeout=15):
    full_cmd = [
        "ssh",
        "-o", "BatchMode=yes",
        "-o", "ConnectTimeout=8",
        host,
        cmd
    ]
    res = subprocess.run(full_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)
    return res.returncode, res.stdout.strip(), res.stderr.strip()

def get_rdap_status():
    try:
        import urllib.request
        req = urllib.request.Request(
            RDAP_URL,
            headers={"User-Agent": "curl/8.7.1", "Accept": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("status", [])
    except Exception:
        try:
            req_cmd = ["curl", "-s", "--max-time", "10", RDAP_URL]
            res = subprocess.run(req_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=12)
            if res.returncode == 0 and res.stdout:
                data = json.loads(res.stdout)
                return data.get("status", [])
        except Exception as e:
            return [f"error: {e}"]
    return ["unknown"]

def flush_mihomo_socket(endpoint):
    try:
        if not os.path.exists(SOCKET_PATH):
            return False, f"socket {SOCKET_PATH} not found"
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect(SOCKET_PATH)
        req = f"POST {endpoint} HTTP/1.1\r\nHost: localhost\r\nContent-Length: 0\r\n\r\n"
        s.sendall(req.encode("utf-8"))
        res = s.recv(1024)
        s.close()
        status_line = res.decode("utf-8", errors="replace").splitlines()[0] if res else "empty"
        return True, status_line
    except Exception as e:
        return False, str(e)

def main():
    dry_run = "--dry-run" in sys.argv

    # 1) 检查标记文件
    if os.path.exists(DONE_PATH):
        if dry_run:
            print("ALREADY_DONE: DONE flag exists")
        sys.exit(0)

    # 2) 经 ssh elena 查询公共 DNS
    dns_cmd = 'dig @223.5.5.5 kaoyan.elenalyl.top A +short; dig @8.8.8.8 kaoyan.elenalyl.top A +short'
    try:
        ret, stdout, stderr = run_ssh("elena", dns_cmd, timeout=20)
    except Exception as e:
        ret, stdout, stderr = 1, "", str(e)

    dns_ips = [line.strip() for line in stdout.splitlines() if line.strip()]
    rdap_status = get_rdap_status()
    is_propagated = any(ip == TARGET_IP for ip in dns_ips)

    if not is_propagated:
        msg = f"WAITING: DNS not propagated (resolved: {dns_ips}, target: {TARGET_IP}), RDAP status: {rdap_status}"
        log(msg, to_stdout=True)
        sys.exit(0)

    log(f"DNS_RESOLVED: {dns_ips} matched target {TARGET_IP}, RDAP: {rdap_status}", to_stdout=True)

    if dry_run:
        print("DRY_RUN: DNS resolved. Skipping Caddy reload, probing and cache flushing.")
        sys.exit(0)

    # 3) 放行后执行 CVM Caddy reload 重置退避
    log("RELOAD_CADDY: Triggering caddy reload on cvm...", to_stdout=True)
    caddy_cmd = 'docker exec caddy-proxy caddy reload --config /etc/caddy/Caddyfile --force'
    try:
        c_ret, c_out, c_err = run_ssh("cvm", caddy_cmd, timeout=30)
        log(f"RELOAD_CADDY_RESULT: ret={c_ret}, out={c_out}, err={c_err}", to_stdout=True)
    except Exception as e:
        log(f"RELOAD_CADDY_ERROR: {e}", to_stdout=True)

    # 4) 每 20 秒探测一次，最多 10 分钟 (30 次)
    probe_cmd = 'curl -s -o /dev/null -w %{http_code}_%{ssl_verify_result} --max-time 10 https://kaoyan.elenalyl.top/'
    max_attempts = 30
    success = False
    last_res = "none"

    log("START_PROBING: Probing https://kaoyan.elenalyl.top/ via elena every 20s (max 10m)...", to_stdout=True)
    for attempt in range(1, max_attempts + 1):
        try:
            p_ret, p_out, p_err = run_ssh("elena", probe_cmd, timeout=15)
            last_res = p_out
            log(f"PROBE #{attempt}: {last_res}", to_stdout=True)
            if last_res == "200_0":
                success = True
                break
        except Exception as e:
            last_res = f"exception: {e}"
            log(f"PROBE #{attempt} failed with {e}", to_stdout=True)

        if attempt < max_attempts:
            time.sleep(20)

    # 5) 成功处理
    if success:
        log("SUCCESS: https://kaoyan.elenalyl.top/ returned 200_0", to_stdout=True)
        # 清除 M4 本机 mihomo 缓存
        ok1, res1 = flush_mihomo_socket("/cache/dns/flush")
        ok2, res2 = flush_mihomo_socket("/cache/fakeip/flush")
        log(f"FLUSH_CACHE: dns={ok1}({res1}), fakeip={ok2}({res2})", to_stdout=True)

        # 写入 DONE 标记
        os.makedirs(DONE_DIR, exist_ok=True)
        with open(DONE_PATH, "w", encoding="utf-8") as f:
            f.write(f"DONE at {datetime.now().isoformat()}\n")

        # macOS 桌面通知
        notify_cmd = ['osascript', '-e', 'display notification "https://kaoyan.elenalyl.top 已上线" with title "kaoyan watcher"']
        try:
            subprocess.run(notify_cmd, timeout=5)
        except Exception as e:
            log(f"NOTIFY_ERROR: {e}", to_stdout=True)

        sys.exit(0)
    else:
        # 6) 失败记录
        log(f"FAIL: 10 minutes elapsed, final probe result: {last_res}", to_stdout=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
