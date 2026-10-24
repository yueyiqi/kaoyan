"""Additive, transactional schema reconciliation shared by every launch path.

[IoC_Skill_Telemetry] Status: TAIL_PENDING; Author: Codex/OpenAI.
"""
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import sqlite3

VERSION = "V005"
FILENAME = "V005__complete_portable_schema.sql"
ROOT = Path(__file__).resolve().parent


def schema_source():
    directory = Path(os.environ.get("KAOYAN_MIGRATIONS_DIR", ROOT / "db_migrations"))
    path = directory / FILENAME
    if not path.is_file():
        raise RuntimeError(f"Required schema asset missing: {path}")
    sql = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    return sql, hashlib.sha256(sql.encode("utf-8")).hexdigest()


def quote(name):
    return '"' + name.replace('"', '""') + '"'


def reference_schema():
    sql, checksum = schema_source()
    with closing(sqlite3.connect(":memory:")) as ref:
        ref.executescript(sql)
        tables = {}
        for name, create in ref.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
            tables[name] = (create, list(ref.execute(f"PRAGMA table_info({quote(name)})")))
        indexes = [r[0] for r in ref.execute("SELECT sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL")]
    return tables, indexes, checksum


def inspect_schema(conn):
    tables, _, checksum = reference_schema()
    missing_tables, missing_columns = [], {}
    for name, (_, expected) in tables.items():
        actual = {r[1]: r for r in conn.execute(f"PRAGMA table_info({quote(name)})")}
        if not actual:
            missing_tables.append(name)
        else:
            missing = [r[1] for r in expected if r[1] not in actual]
            if missing:
                missing_columns[name] = missing
    return {"ready": not (missing_tables or missing_columns), "missing_tables": missing_tables,
            "missing_columns": missing_columns, "expected_tables": len(tables), "schema_sha256": checksum}


def ensure_schema(conn):
    """Repair structure, never invent lost rows or silently accept failed DDL."""
    tables, indexes, checksum = reference_schema()
    changes = []
    conn.execute("BEGIN IMMEDIATE")
    try:
        for name, (create, expected) in tables.items():
            actual = {r[1]: r for r in conn.execute(f"PRAGMA table_info({quote(name)})")}
            if not actual:
                conn.execute(create)
                changes.append(f"create:{name}")
                continue
            for _, column, kind, required, default, pk in expected:
                if column in actual:
                    if actual[column][5] != pk:
                        raise RuntimeError(f"Incompatible primary key: {name}.{column}")
                    continue
                if pk or (required and default is None):
                    raise RuntimeError(f"Unsafe missing column requires explicit migration: {name}.{column}")
                declaration = f"{quote(column)} {kind}" + (" NOT NULL" if required else "")
                if default is not None:
                    declaration += " DEFAULT " + default
                conn.execute(f"ALTER TABLE {quote(name)} ADD COLUMN {declaration}")
                changes.append(f"add:{name}.{column}")
        row = conn.execute("SELECT checksum_sha256 FROM schema_migrations WHERE version_id=?", (VERSION,)).fetchone()
        if row and row[0] != checksum:
            raise RuntimeError("Applied schema checksum differs from packaged V005")
        for statement in indexes:
            conn.execute(statement.replace("CREATE UNIQUE INDEX ", "CREATE UNIQUE INDEX IF NOT EXISTS ")
                         .replace("CREATE INDEX ", "CREATE INDEX IF NOT EXISTS "))
        conn.execute("INSERT OR IGNORE INTO schema_migrations (version_id,script_name,checksum_sha256,engine_target,applied_at) VALUES (?,?,?,?,?)",
                     (VERSION, FILENAME, checksum, "SQLITE_PORTABLE", datetime.now(timezone.utc).isoformat()))
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    return {**inspect_schema(conn), "changes": changes}


def ensure_pg_schema(conn):
    """Use the same columns for PostgreSQL without executing SQLite PRAGMAs."""
    tables, indexes, checksum = reference_schema()
    with conn.cursor() as cur:
        # Serialize simultaneous startups for this database without a host lock.
        cur.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", ("kaoyan-schema-v005",))
        for name, (create, expected) in tables.items():
            create = create.replace("CREATE TABLE ", "CREATE TABLE IF NOT EXISTS ")
            create = create.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "BIGSERIAL PRIMARY KEY")
            cur.execute(create)
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema=current_schema() AND table_name=%s", (name,))
            actual = {r[0] for r in cur.fetchall()}
            for _, column, kind, required, default, pk in expected:
                if column in actual:
                    continue
                if pk or (required and default is None):
                    raise RuntimeError(f"Unsafe missing PG column: {name}.{column}")
                declaration = f"{quote(column)} {kind}" + (" NOT NULL" if required else "")
                if default is not None:
                    declaration += " DEFAULT " + default
                cur.execute(f"ALTER TABLE {quote(name)} ADD COLUMN {declaration}")
        cur.execute("SELECT checksum_sha256 FROM schema_migrations WHERE version_id=%s", (VERSION,))
        previous = cur.fetchone()
        if previous and previous[0] != checksum:
            raise RuntimeError("Applied PG schema checksum differs from packaged V005")
        for statement in indexes:
            cur.execute(statement.replace("CREATE UNIQUE INDEX ", "CREATE UNIQUE INDEX IF NOT EXISTS ")
                        .replace("CREATE INDEX ", "CREATE INDEX IF NOT EXISTS "))
        cur.execute("INSERT INTO schema_migrations (version_id,script_name,checksum_sha256,engine_target,applied_at) VALUES (%s,%s,%s,%s,%s) ON CONFLICT (version_id) DO NOTHING",
                    (VERSION, FILENAME, checksum, "POSTGRESQL", datetime.now(timezone.utc).isoformat()))

# [IoC_Revision_v1] Status: IMPLEMENTED; schema/snapshot regression ev:ev-0009, ev:ev-0010, ev:ev-0012; cross-host ev:ev-0011.
