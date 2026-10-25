#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kaoyan.elenalyl.top 可达性根因探针 (Reachability root-cause probe).

在 M4 上 Clash fake-ip 会污染结果，因此所有"外网视角"探针一律经 CVM(香港边缘) 发起。
用法: python3 05_...py  -> 打印各层判定; 全部 PASS 后才可声明域名可用。
"""
import json
import subprocess

DOMAIN = "kaoyan.elenalyl.top"
ELENA_IP = "8.163.29.42"
EDGE_IP = "43.160.227.166"


def sh(cmd: str, timeout: int = 30) -> str:
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return (p.stdout + p.stderr).strip()
    except subprocess.TimeoutExpired:
        return "TIMEOUT"


def via_cvm(cmd: str) -> str:
    return sh(f"ssh cvm '{cmd}'", 40)


def main() -> None:
    r = {}
    # L1 注册局状态: clientHold => 公共DNS NXDOMAIN
    r["L1_registry_status"] = sh(
        "curl -s https://rdap.zdnsgtld.com/top/domain/elenalyl.top | "
        "python3 -c \"import sys,json;print(json.load(sys.stdin).get('status'))\""
    )
    # L2 公共DNS解析 (8.8.8.8 / 223.5.5.5)
    r["L2_public_dns"] = via_cvm(f"dig @8.8.8.8 {DOMAIN} +short; dig @223.5.5.5 {DOMAIN} +short") or "NXDOMAIN(empty)"
    # L3 安全组: 80/443 对外是否放行
    r["L3_sg_80"] = via_cvm(f"curl -s -o /dev/null -w %{{http_code}} --max-time 5 http://{ELENA_IP}/ || echo BLOCKED")
    r["L3_sg_443"] = via_cvm(f"curl -sk -o /dev/null -w %{{http_code}} --max-time 5 https://{ELENA_IP}/ || echo BLOCKED")
    # L4 ICP按Host拦截: 同一端口, Host不同, 结果不同 => 边缘网关按域名拦截
    r["L4_host_domain_3389"] = via_cvm(f"curl -s -o /dev/null -w %{{http_code}} --max-time 6 -H Host:{DOMAIN} http://{ELENA_IP}:3389/")
    r["L4_host_127_3389"] = via_cvm(f"curl -s -o /dev/null -w %{{http_code}} --max-time 6 -H Host:127.0.0.1 http://{ELENA_IP}:3389/")
    # L5 边缘反代: 已存在的免备案域名
    r["L5_liuzengyu_https"] = sh("curl -s -o /dev/null -w %{http_code} --max-time 10 https://kaoyan.liuzengyu.top/")
    # L6 DNS 是否已指向香港边缘 (切换后应=EDGE_IP)
    r["L6_dns_points_to_edge"] = EDGE_IP in r["L2_public_dns"]
    print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
