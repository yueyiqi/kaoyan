#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
04_elenaNonrootTieredStorage_非Root分层与T2冷备.py
Rule XXII 同基名伴生脚本：输出 elena (8.163.29.42) 非 root 部署、40GB 磁盘四区配额与 T2 (/vol1) 冷备拓扑元数据。
"""

from __future__ import annotations
import json
from pathlib import Path


def main() -> None:
    here = Path(__file__).resolve().parent
    spec = {
        "host": "elena (8.163.29.42)",
        "domain": "kaoyan.elenalyl.top",
        "service_user": "elena (uid=1000, non-root)",
        "elena_disk_zones": {
            "zone1_system_and_logs": {"path": "/var/log/journal", "cap": "200MB (SystemMaxUse=200M, SystemKeepFree=8G)"},
            "zone2_tier_hot": {"path": "/home/elena/kaoyan_storage/hot_db/kaoyan_hub.sqlite3", "cap": "4.0GB"},
            "zone3_tier_warm": {"path": "/home/elena/kaoyan_storage/warm_staging/", "cap": "2.0GB (7-day rolling)"},
            "zone4_tier_cold_outbox": {"path": "/home/elena/kaoyan_storage/cold_outbox/", "cap": "500MB"},
        },
        "t2_cold_archive": {
            "ssh_alias": "t2 (47.121.112.172:39810, user=jasper)",
            "btrfs_volume_path": "/vol1/backup/elena_kaoyan_cold_archive/",
            "free_space": "16TB on /vol1 (avoids 4.6GB / root partition)",
        },
    }
    (here / "elena_tiered_storage_and_t2_backup_report.json").write_text(
        json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
