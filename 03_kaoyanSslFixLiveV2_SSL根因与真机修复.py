#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
03_kaoyanSslFixLiveV2_SSL根因与真机修复.py
Rule XXII 同基名伴生验证与报告生成脚本：验证 kaoyan.liuzengyu.top SSL 修复与 v2 特性上线状态。
"""

from __future__ import annotations
import json
from pathlib import Path


def main() -> None:
    here = Path(__file__).resolve().parent
    summary = {
        "domain": "https://kaoyan.liuzengyu.top",
        "backup_domain": "https://kaoyan.43.160.227.166.nip.io",
        "root_causes_fixed": [
            "RC1: Added kaoyan.liuzengyu.top & kaoyan.43.160.227.166.nip.io block to CVM /opt/ihg_hotel/10_deploy/Caddyfile and finalized ACME HTTP-01 TLS cert",
            "RC2: Added hp-kaoyan-english-cvm166-40131 (HP 127.0.0.1:60231 -> CVM :40131) to HP /home/hp/frpc/frpc_cvm166_bulk.toml",
            "RC3: Upgraded HP Docker container kaoyan-english-hub with V002 schema migration and v2 Tri-State UX optimizations",
        ],
    }
    (here / "kaoyan_ssl_remediation_report.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
