"""Offline cutover tools; complete SQLite snapshots, never raw live-file copies.

[IoC_Skill_Telemetry] Status: TAIL_PENDING; Author: Codex/OpenAI.
Export is a point-in-time backup. Stop application writes before final cutover.
Restore requires a NEW target file; existing databases are never overwritten.
"""
import argparse
import base64
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import sqlite3
import tempfile
import time
import uuid

from kaoyan_schema import ensure_schema, inspect_schema, quote


def connect(path, readonly=False):
    path = Path(path).expanduser().resolve()
    if readonly:
        return sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=10)
    return sqlite3.connect(path, timeout=10)


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inventory(conn):
    result = {}
    for (table,) in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
        columns = sorted(row[1] for row in conn.execute(f"PRAGMA table_info({quote(table)})"))
        selection = ",".join(map(quote, columns))
        digest, count = hashlib.sha256(), 0
        digest.update(json.dumps(columns).encode())
        for row in conn.execute(f"SELECT {selection} FROM {quote(table)} ORDER BY {selection}"):
            values = [{"bytes": base64.b64encode(v).decode()} if isinstance(v, bytes) else v for v in row]
            digest.update(json.dumps(values, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8") + b"\n")
            count += 1
        result[table] = {"rows": count, "sha256": digest.hexdigest(), "columns": columns}
    return result


def validate(conn):
    check = conn.execute("PRAGMA integrity_check").fetchall()
    if check != [("ok",)]:
        raise RuntimeError("SQLite integrity check failed")
    status = inspect_schema(conn)
    if not status["ready"]:
        raise RuntimeError("Incomplete schema: " + json.dumps(status))
    return status


def backup(source, destination):
    deadline = time.monotonic() + 30
    def progress(*_):
        if time.monotonic() > deadline:
            raise TimeoutError("Snapshot exceeded 30 seconds; quiesce writes and retry")
    with closing(connect(destination)) as target:
        source.backup(target, pages=256, progress=progress, sleep=0.05)
        # A portable snapshot must not depend on WAL/SHM sidecars. Normalize
        # only this private completed backup, never the live source database.
        if target.execute("PRAGMA journal_mode=DELETE").fetchone()[0] != "delete":
            raise RuntimeError("Snapshot could not leave WAL mode")


def export_snapshot(database, package):
    package = Path(package).resolve()
    package.mkdir(mode=0o700, parents=True, exist_ok=False)
    # The manifest is published last; incomplete packages cannot be restored.
    with closing(connect(database, readonly=True)) as source:
        backup(source, package / "database.sqlite3")
    with closing(connect(package / "database.sqlite3", readonly=True)) as snapshot:
        schema = validate(snapshot)
        tables = inventory(snapshot)
    manifest = {"format": "kaoyan-sqlite-snapshot-v1", "schema": schema,
                "source_os": platform.system(), "source_machine": platform.machine(),
                "database_sha256": file_hash(package / "database.sqlite3"), "tables": tables}
    (package / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def restore_snapshot(package, database):
    package, database = Path(package).resolve(), Path(database).expanduser().resolve()
    if database.exists() or any(Path(str(database) + ext).exists() for ext in ("-wal", "-shm")):
        raise FileExistsError("Restore requires a new, inactive target database")
    manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("format") != "kaoyan-sqlite-snapshot-v1":
        raise ValueError("Unsupported snapshot format")
    source_path = package / "database.sqlite3"
    if file_hash(source_path) != manifest["database_sha256"]:
        raise ValueError("Snapshot file checksum mismatch")
    database.parent.mkdir(parents=True, exist_ok=True)
    stage = database.with_name(database.name + ".restore-" + uuid.uuid4().hex)
    try:
        # This is a completed immutable backup package, never the live source DB.
        # Re-running Backup API across SQLite versions can change header bytes.
        with source_path.open("rb") as source, stage.open("xb") as target:
            shutil.copyfileobj(source, target)
            target.flush()
            os.fsync(target.fileno())
        # Validate the exact copied bytes, including source-change races.
        if file_hash(stage) != manifest["database_sha256"]:
            raise ValueError("Snapshot changed during restore")
        with closing(connect(stage, readonly=True)) as restored:
            schema = validate(restored)
            if schema["schema_sha256"] != manifest["schema"]["schema_sha256"]:
                raise ValueError("Snapshot schema version mismatch")
            if inventory(restored) != manifest["tables"]:
                raise ValueError("Snapshot table inventory mismatch")
        # Atomic no-clobber publication on Windows NTFS, Linux and macOS.
        os.link(stage, database)
    finally:
        stage.unlink(missing_ok=True)
    return {"ready": True, "tables": len(manifest["tables"]), "target_os": platform.system()}


def repair(database):
    database = Path(database).expanduser().resolve()
    database.parent.mkdir(parents=True, exist_ok=True)
    backup_path = None
    if database.exists():
        backup_path = database.with_name(database.name + ".before-schema-" + uuid.uuid4().hex + ".sqlite3")
        with closing(connect(database, readonly=True)) as source:
            backup(source, backup_path)
    with closing(connect(database)) as conn:
        result = ensure_schema(conn)
        validate(conn)
    return {**result, "backup": str(backup_path) if backup_path else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["inspect", "repair", "export", "restore"])
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--package", type=Path)
    args = parser.parse_args()
    if args.operation == "inspect":
        with closing(connect(args.database, readonly=True)) as conn:
            result = {"schema": inspect_schema(conn), "tables": inventory(conn), "os": platform.system()}
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result["schema"]["ready"] else 1
    if args.operation == "repair":
        result = repair(args.database)
    else:
        if args.package is None:
            parser.error("--package is required for export/restore")
        result = (export_snapshot(args.database, args.package) if args.operation == "export"
                  else restore_snapshot(args.package, args.database))
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# [IoC_Revision_v1] Status: IMPLEMENTED; schema/snapshot regression ev:ev-0009, ev:ev-0010, ev:ev-0012; cross-host ev:ev-0011.
