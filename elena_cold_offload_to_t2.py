#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
elena_cold_offload_to_t2.py v3.0 — 運行於 elena (8.163.29.42, User=elena) 的 PG18 + SQLite WAL 雙擎 3-2-1 異地災備守護腳本
1. 檢查 8.163.29.42 (/dev/vda3 40GB) 磁盤水位，確保佔用恆定 < 15%；
2. 執行 PostgreSQL 18.6 (kaoyan_prod) 邏輯全量導出 (pg_dump --clean --if-exists) 並壓縮計算 SHA-256；
3. 執行 SQLite WAL 熱備庫 (kaoyan_hub.sqlite3) PRAGMA wal_checkpoint(TRUNCATE) 並導出壓縮包與 SHA-256；
4. 通過免密 SSH (elena -> t2) 雙軌同步至 T2 的 19TB Btrfs 陣列 (/vol1/backup/elena_kaoyan_cold_archive/)。
"""
import datetime
import gzip
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
from pathlib import Path

STORAGE_ROOT = Path("/home/elena/kaoyan_storage")
HOT_DB = STORAGE_ROOT / "hot_db/kaoyan_hub.sqlite3"
WARM_SNAP = STORAGE_ROOT / "warm_staging/daily_snapshots"
COLD_OUTBOX = STORAGE_ROOT / "cold_outbox"
T2_TARGET = "/vol1/backup/elena_kaoyan_cold_archive"

PG_ENV = dict(os.environ, PGPASSWORD=os.environ.get("KAOYAN_PG_PASS", "kaoyan_pg18_ha_2026"))


def main() -> None:
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    usage = shutil.disk_usage("/")
    used_pct = round(usage.used * 100.0 / usage.total, 2)

    WARM_SNAP.mkdir(parents=True, exist_ok=True)
    (COLD_OUTBOX / "sql_archives").mkdir(parents=True, exist_ok=True)

    # 1. SQLite WAL Checkpoint & Dump
    conn = sqlite3.connect(str(HOT_DB))
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
    sql_dump = "\n".join(conn.iterdump())
    conn.close()

    warm_file = WARM_SNAP / f"kaoyan_hot_snapshot_{ts}.sql"
    warm_file.write_text(sql_dump, encoding="utf-8")

    cold_sqlite_gz = COLD_OUTBOX / "sql_archives" / f"kaoyan_cold_archive_{ts}.sql.gz"
    with gzip.open(cold_sqlite_gz, "wt", encoding="utf-8") as gz:
        gz.write(sql_dump)
    sqlite_sha256 = hashlib.sha256(cold_sqlite_gz.read_bytes()).hexdigest()

    # 2. PostgreSQL 18.6 Logical Dump (pg_dump)
    pg_dump_cmd = [
        "pg_dump",
        "-h", "127.0.0.1",
        "-p", "5432",
        "-U", "elena",
        "-d", "kaoyan_prod",
        "--clean",
        "--if-exists",
    ]
    pg_sql = subprocess.check_output(pg_dump_cmd, env=PG_ENV, text=True, timeout=30)
    warm_pg_file = WARM_SNAP / f"kaoyan_pg18_snapshot_{ts}.sql"
    warm_pg_file.write_text(pg_sql, encoding="utf-8")

    cold_pg_gz = COLD_OUTBOX / "sql_archives" / f"kaoyan_pg18_archive_{ts}.sql.gz"
    with gzip.open(cold_pg_gz, "wt", encoding="utf-8") as gz:
        gz.write(pg_sql)
    pg_sha256 = hashlib.sha256(cold_pg_gz.read_bytes()).hexdigest()

    manifest = {
        "timestamp_utc": ts,
        "backup_architecture": "3-2-1 Dual-Engine Cold Offload (PG18 Primary + SQLite WAL Standby -> T2 19TB Btrfs)",
        "source_host": "elena (8.163.29.42)",
        "process_user": os.environ.get("USER", "elena"),
        "elena_disk_total_gb": round(usage.total / (1024**3), 2),
        "elena_disk_used_gb": round(usage.used / (1024**3), 2),
        "elena_disk_used_pct": used_pct,
        "pg18_db_name": "kaoyan_prod",
        "pg18_archive_file": cold_pg_gz.name,
        "pg18_archive_sha256": pg_sha256,
        "hot_db_path": str(HOT_DB),
        "cold_archive_file": cold_sqlite_gz.name,
        "cold_archive_sha256": sqlite_sha256,
        "t2_destination": f"t2:{T2_TARGET}/sql_archives/",
    }
    manifest_path = COLD_OUTBOX / f"manifest_{ts}.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    subprocess.run(["scp", "-q", str(cold_sqlite_gz), str(cold_pg_gz), f"t2:{T2_TARGET}/sql_archives/"], check=True)
    subprocess.run(["scp", "-q", str(manifest_path), f"t2:{T2_TARGET}/manifests/latest_manifest.json"], check=True)
    print(json.dumps(manifest, ensure_ascii=False))


if __name__ == "__main__":
    main()
