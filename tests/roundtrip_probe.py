"""Synthetic all-table fixture for transfer between actual operating systems."""
import argparse
from contextlib import closing
import json
from pathlib import Path
import platform
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kaoyan_schema import ensure_schema, quote
from kaoyan_portable import export_snapshot, restore_snapshot, inventory

parser = argparse.ArgumentParser()
parser.add_argument("mode", choices=["create", "receive"])
parser.add_argument("workspace", type=Path)
parser.add_argument("--package", type=Path)
args = parser.parse_args()
args.workspace.mkdir(parents=True, exist_ok=False)
database = args.workspace / "roundtrip.db"
if args.mode == "create":
    with closing(sqlite3.connect(database)) as conn:
        ensure_schema(conn)
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        for table in tables:
            if table == "schema_migrations":
                continue
            fields = list(conn.execute(f"PRAGMA table_info({quote(table)})"))
            columns = [r[1] for r in fields]
            values = [7 if 'INT' in r[2].upper() else 0.75 if r[2] == 'REAL'
                      else '跨系统 /ə/\r\nC:\\学习\\' + r[1] for r in fields]
            conn.execute(f"INSERT INTO {quote(table)} ({','.join(map(quote,columns))}) VALUES ({','.join('?' for _ in columns)})", values)
        conn.execute("CREATE TABLE future_extension (id INTEGER PRIMARY KEY, payload BLOB)")
        conn.execute("INSERT INTO future_extension VALUES (1, ?)", (b'\x00\xff',))
        conn.commit()
else:
    if args.package is None:
        parser.error("--package required")
    restore_snapshot(args.package, database)
manifest = export_snapshot(database, args.workspace / "package")
print(json.dumps({"actual_os": platform.system(), "machine": platform.machine(),
                  "tables": manifest["tables"], "schema": manifest["schema"]}, ensure_ascii=False))
