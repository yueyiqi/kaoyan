#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Kaoyan English Hub v3.0 — Modular Monolith Micro-Kernel with Dual-Engine HA (PostgreSQL 18 Primary + SQLite WAL Standby)

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sqlite3
import time
import uuid
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

try:
    import psycopg2
    import psycopg2.extras
    HAS_PG = True
except Exception:
    HAS_PG = False

BASE_DIR = Path(__file__).resolve().parent
HOT_SQLITE_PATH = Path("/home/elena/kaoyan_storage/hot_db/kaoyan_hub.sqlite3")
LOCAL_SQLITE_PATH = Path(os.environ.get("KAOYAN_DB_PATH", str(HOT_SQLITE_PATH if HOT_SQLITE_PATH.parent.exists() else BASE_DIR / "db_volume" / "kaoyan_hub.sqlite3")))
MIGRATION_V1 = BASE_DIR / "db_migrations" / "V001__init_kaoyan_8tables.sql"
MIGRATION_V2 = BASE_DIR / "db_migrations" / "V002__pg18_and_sqlite_10tables_ha_schema.sql"
BACKUP_DIR = Path(os.environ.get("KAOYAN_BACKUP_DIR", str(BASE_DIR / "db_backups")))
HTML_PATH = Path(os.environ.get("KAOYAN_HTML_PATH", str(BASE_DIR / "index.html")))

PG_DSN = os.environ.get("KAOYAN_PG_DSN", "dbname=kaoyan_prod user=elena host=127.0.0.1 port=5432 password=kaoyan_pg18_ha_2026")

CORE_TABLES = [
    "annotation_spans",
    "api_idempotency_keys",
    "essay_corpus_snippets",
    "exam_passages",
    "ha_sync_wal_journal",
    "schema_migrations",
    "syllabus_5500_lexicon",
    "sys_users",
    "user_progress_anchors",
    "user_vocab_ledger",
]


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class DualEngineHARepository:
    # Manages Dual-Write and Automatic Failover between PostgreSQL 18 (Primary) and SQLite WAL (Hot Standby).

    def __init__(self, pg_dsn: str, sqlite_path: Path) -> None:
        self.pg_dsn = pg_dsn
        self.sqlite_path = sqlite_path
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    def get_sqlite_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.sqlite_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        return conn

    def get_pg_conn(self, simulate_down: bool = False):
        if simulate_down or not HAS_PG:
            return None
        try:
            conn = psycopg2.connect(self.pg_dsn, connect_timeout=2)
            return conn
        except Exception:
            return None

    def init_and_migrate_both_engines(self) -> None:
        # 1. Initialize & Upgrade SQLite WAL Hot Standby
        sconn = self.get_sqlite_conn()
        if MIGRATION_V1.exists():
            try:
                sconn.executescript(MIGRATION_V1.read_text(encoding="utf-8"))
            except Exception:
                pass
        if MIGRATION_V2.exists():
            sconn.executescript(MIGRATION_V2.read_text(encoding="utf-8"))
        sconn.execute(
            "CREATE TABLE IF NOT EXISTS user_vocab_ledger ("
            "vocab_id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "user_id TEXT NOT NULL, lemma TEXT NOT NULL, "
            "syllabus_tier TEXT NOT NULL DEFAULT 'CORE_1800', "
            "lookup_count INTEGER NOT NULL DEFAULT 1, "
            "last_seen_at TEXT NOT NULL, "
            "days_since_seen REAL NOT NULL DEFAULT 0.0, "
            "urgency_score REAL NOT NULL DEFAULT 0.50, "
            "exam_source TEXT NOT NULL DEFAULT '', "
            "contextual_meaning TEXT NOT NULL DEFAULT '', "
            "mastery_state TEXT NOT NULL DEFAULT 'LEARNING', "
            "UNIQUE(user_id, lemma));"
        )
        for alter_sql in [
            "ALTER TABLE annotation_spans ADD COLUMN prefix_quote TEXT NOT NULL DEFAULT ''",
            "ALTER TABLE annotation_spans ADD COLUMN suffix_quote TEXT NOT NULL DEFAULT ''",
            "ALTER TABLE annotation_spans ADD COLUMN promoted_snippet_id TEXT NOT NULL DEFAULT ''",
            "ALTER TABLE annotation_spans ADD COLUMN version INTEGER NOT NULL DEFAULT 1",
            "ALTER TABLE essay_corpus_snippets ADD COLUMN usage_count INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE schema_migrations ADD COLUMN engine_target TEXT NOT NULL DEFAULT 'DUAL_PG_SQLITE'",
        ]:
            try:
                sconn.execute(alter_sql)
            except Exception:
                pass
        sconn.execute(
            "INSERT OR REPLACE INTO schema_migrations (version_id, script_name, checksum_sha256, engine_target, applied_at) VALUES (?, ?, ?, ?, ?)",
            ("V002", "V002__pg18_and_sqlite_10tables_ha_schema.sql", hashlib.sha256(b"V002_PG18_HA").hexdigest(), "DUAL_PG_SQLITE", now_str()),
        )
        sconn.commit()

        # Also copy rows from legacy BASE_DIR/db_volume/kaoyan_hub.sqlite3 if present
        legacy_db = BASE_DIR / "db_volume" / "kaoyan_hub.sqlite3"
        if legacy_db.exists() and legacy_db.resolve() != self.sqlite_path.resolve():
            try:
                lconn = sqlite3.connect(str(legacy_db))
                for r in lconn.execute("SELECT user_id, username, display_name, role, passcode_hash, token_secret, created_at FROM sys_users").fetchall():
                    sconn.execute("INSERT OR IGNORE INTO sys_users VALUES (?,?,?,?,?,?,?)", tuple(r))
                for r in lconn.execute("SELECT user_id, last_passage_id, last_para_idx, last_span_id, last_tab_idx, essay_draft_md, streak_days, rev_no, updated_at FROM user_progress_anchors").fetchall():
                    sconn.execute("INSERT OR IGNORE INTO user_progress_anchors VALUES (?,?,?,?,?,?,?,?,?)", tuple(r))
                for r in lconn.execute("SELECT user_id, lemma, syllabus_tier, lookup_count, last_seen_at, days_since_seen, urgency_score, exam_source, contextual_meaning, mastery_state FROM user_vocab_ledger").fetchall():
                    sconn.execute(
                        "INSERT OR IGNORE INTO user_vocab_ledger (user_id, lemma, syllabus_tier, lookup_count, last_seen_at, days_since_seen, urgency_score, exam_source, contextual_meaning, mastery_state) VALUES (?,?,?,?,?,?,?,?,?,?)",
                        tuple(r),
                    )
                sconn.commit()
                lconn.close()
            except Exception:
                pass

        # 2. Initialize & Sync PostgreSQL 18 Primary
        pconn = self.get_pg_conn()
        if pconn is not None:
            with pconn:
                with pconn.cursor() as cur:
                    if MIGRATION_V2.exists():
                        cur.execute(MIGRATION_V2.read_text(encoding="utf-8"))
                    cur.execute(
                        "CREATE TABLE IF NOT EXISTS user_vocab_ledger ("
                        "vocab_id BIGSERIAL PRIMARY KEY, "
                        "user_id VARCHAR(64) NOT NULL, lemma VARCHAR(64) NOT NULL, "
                        "syllabus_tier VARCHAR(32) NOT NULL DEFAULT 'CORE_1800', "
                        "lookup_count INTEGER NOT NULL DEFAULT 1, "
                        "last_seen_at VARCHAR(64) NOT NULL, "
                        "days_since_seen DOUBLE PRECISION NOT NULL DEFAULT 0.0, "
                        "urgency_score DOUBLE PRECISION NOT NULL DEFAULT 0.50, "
                        "exam_source VARCHAR(128) NOT NULL DEFAULT '', "
                        "contextual_meaning TEXT NOT NULL DEFAULT '', "
                        "mastery_state VARCHAR(32) NOT NULL DEFAULT 'LEARNING', "
                        "UNIQUE(user_id, lemma));"
                    )
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_spans_user_passage ON annotation_spans(user_id, passage_id, para_idx, start_offset);")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_essay_user_theme ON essay_corpus_snippets(user_id, theme_tag, func_slot);")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_vocab_user_urgency ON user_vocab_ledger(user_id, urgency_score DESC);")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_passages_sha256 ON exam_passages(sha256_hash);")

                    for r in sconn.execute("SELECT user_id, username, display_name, role, passcode_hash, token_secret, created_at FROM sys_users").fetchall():
                        cur.execute(
                            "INSERT INTO sys_users (user_id, username, display_name, role, passcode_hash, token_secret, created_at) VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (user_id) DO NOTHING",
                            tuple(r),
                        )
                    for r in sconn.execute("SELECT user_id, last_passage_id, last_para_idx, last_span_id, last_tab_idx, essay_draft_md, streak_days, rev_no, updated_at FROM user_progress_anchors").fetchall():
                        cur.execute(
                            "INSERT INTO user_progress_anchors (user_id, last_passage_id, last_para_idx, last_span_id, last_tab_idx, essay_draft_md, streak_days, rev_no, updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (user_id) DO NOTHING",
                            tuple(r),
                        )
                    for r in sconn.execute("SELECT lemma, pos, cn_meaning, syllabus_tier, polysemy_trap_note, exam_freq FROM syllabus_5500_lexicon").fetchall():
                        cur.execute(
                            "INSERT INTO syllabus_5500_lexicon (lemma, pos, cn_meaning, syllabus_tier, polysemy_trap_note, exam_freq) VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT (lemma) DO NOTHING",
                            tuple(r),
                        )
                    for r in sconn.execute("SELECT passage_id, owner_user_id, year, exam_type, text_no, title, paragraphs_json, syllabus_hits_json, sha256_hash, created_at FROM exam_passages").fetchall():
                        cur.execute(
                            "INSERT INTO exam_passages (passage_id, owner_user_id, year, exam_type, text_no, title, paragraphs_json, syllabus_hits_json, sha256_hash, created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (passage_id) DO NOTHING",
                            tuple(r),
                        )
                    for r in sconn.execute("SELECT span_id, user_id, passage_id, granularity, para_idx, start_offset, end_offset, selected_text, prefix_quote, suffix_quote, syntax_breakdown, user_comment, promoted_snippet_id, version, created_at FROM annotation_spans").fetchall():
                        cur.execute(
                            "INSERT INTO annotation_spans (span_id, user_id, passage_id, granularity, para_idx, start_offset, end_offset, selected_text, prefix_quote, suffix_quote, syntax_breakdown, user_comment, promoted_snippet_id, version, created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (span_id) DO NOTHING",
                            tuple(r),
                        )
                    for r in sconn.execute("SELECT snippet_id, user_id, theme_tag, func_slot, granularity, content_en, cloze_pattern, translation_zh, source_ref, usage_count, created_at FROM essay_corpus_snippets").fetchall():
                        cur.execute(
                            "INSERT INTO essay_corpus_snippets (snippet_id, user_id, theme_tag, func_slot, granularity, content_en, cloze_pattern, translation_zh, source_ref, usage_count, created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (snippet_id) DO NOTHING",
                            tuple(r),
                        )
                    for r in sconn.execute("SELECT user_id, lemma, syllabus_tier, lookup_count, last_seen_at, days_since_seen, urgency_score, exam_source, contextual_meaning, mastery_state FROM user_vocab_ledger").fetchall():
                        cur.execute(
                            "INSERT INTO user_vocab_ledger (user_id, lemma, syllabus_tier, lookup_count, last_seen_at, days_since_seen, urgency_score, exam_source, contextual_meaning, mastery_state) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (user_id, lemma) DO NOTHING",
                            tuple(r),
                        )
                    for r in sconn.execute("SELECT version_id, script_name, checksum_sha256, engine_target, applied_at FROM schema_migrations").fetchall():
                        cur.execute(
                            "INSERT INTO schema_migrations (version_id, script_name, checksum_sha256, engine_target, applied_at) VALUES (%s,%s,%s,%s,%s) ON CONFLICT (version_id) DO UPDATE SET applied_at = EXCLUDED.applied_at",
                            tuple(r),
                        )
                    for r in sconn.execute("SELECT tx_uuid, op_type, target_table, record_pk, payload_json, pg_status, sqlite_status, created_at FROM ha_sync_wal_journal").fetchall():
                        cur.execute(
                            "INSERT INTO ha_sync_wal_journal (tx_uuid, op_type, target_table, record_pk, payload_json, pg_status, sqlite_status, created_at) VALUES (%s,%s,%s,%s,%s,'REPLAYED',%s,%s) ON CONFLICT (tx_uuid) DO NOTHING",
                            (r[0], r[1], r[2], r[3], r[4], r[6], r[7]),
                        )
                    for r in sconn.execute("SELECT idempotency_key, user_id, endpoint, req_hash, resp_code, resp_body_json, created_at FROM api_idempotency_keys").fetchall():
                        cur.execute(
                            "INSERT INTO api_idempotency_keys (idempotency_key, user_id, endpoint, req_hash, resp_code, resp_body_json, created_at) VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (idempotency_key) DO NOTHING",
                            tuple(r),
                        )
                    for r in sconn.execute("SELECT tx_uuid, op_type, target_table, record_pk, payload_json, pg_status, sqlite_status, created_at FROM ha_sync_wal_journal").fetchall():
                        cur.execute(
                            "INSERT INTO ha_sync_wal_journal (tx_uuid, op_type, target_table, record_pk, payload_json, pg_status, sqlite_status, created_at) VALUES (%s,%s,%s,%s,%s,'REPLAYED',%s,%s) ON CONFLICT (tx_uuid) DO NOTHING",
                            (r[0], r[1], r[2], r[3], r[4], r[6], r[7]),
                        )
                    for r in sconn.execute("SELECT idempotency_key, user_id, endpoint, req_hash, resp_code, resp_body_json, created_at FROM api_idempotency_keys").fetchall():
                        cur.execute(
                            "INSERT INTO api_idempotency_keys (idempotency_key, user_id, endpoint, req_hash, resp_code, resp_body_json, created_at) VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (idempotency_key) DO NOTHING",
                            tuple(r),
                        )
            pconn.close()
        sconn.close()

    def record_ha_wal(self, op_type: str, target_table: str, record_pk: str, payload: dict, pg_ok: bool, sqlite_ok: bool) -> str:
        tx_uuid = f"tx-{uuid.uuid4().hex[:16]}"
        ts = now_str()
        p_stat = "COMMITTED" if pg_ok else "DEGRADED_STANDBY_ONLY"
        s_stat = "COMMITTED" if sqlite_ok else "FAILED"
        raw_json = json.dumps(payload, ensure_ascii=False)
        try:
            sconn = self.get_sqlite_conn()
            sconn.execute(
                "INSERT INTO ha_sync_wal_journal (tx_uuid, op_type, target_table, record_pk, payload_json, pg_status, sqlite_status, created_at) VALUES (?,?,?,?,?,?,?,?)",
                (tx_uuid, op_type, target_table, record_pk, raw_json, p_stat, s_stat, ts),
            )
            sconn.commit()
            sconn.close()
        except Exception:
            pass
        if pg_ok:
            pconn = self.get_pg_conn()
            if pconn is not None:
                try:
                    with pconn:
                        with pconn.cursor() as cur:
                            cur.execute(
                                "INSERT INTO ha_sync_wal_journal (tx_uuid, op_type, target_table, record_pk, payload_json, pg_status, sqlite_status, created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                                (tx_uuid, op_type, target_table, record_pk, raw_json, p_stat, s_stat, ts),
                            )
                finally:
                    pconn.close()
        return tx_uuid

    def get_ha_status(self, simulate_pg_down: bool = False) -> dict:
        t0 = time.perf_counter()
        pg_counts = {}
        pg_online = False
        pg_version = "offline"
        if not simulate_pg_down:
            try:
                self.init_and_migrate_both_engines()
            except Exception:
                pass
        if not simulate_pg_down:
            try:
                self.init_and_migrate_both_engines()
            except Exception:
                pass
        pconn = self.get_pg_conn(simulate_down=simulate_pg_down)
        if pconn is not None:
            try:
                with pconn.cursor() as cur:
                    cur.execute("SELECT version();")
                    pg_version = cur.fetchone()[0].split(",")[0]
                    for tbl in CORE_TABLES:
                        cur.execute(f"SELECT COUNT(*) FROM {tbl};")
                        pg_counts[tbl] = cur.fetchone()[0]
                pg_online = True
            except Exception:
                pg_online = False
            finally:
                pconn.close()

        sconn = self.get_sqlite_conn()
        sqlite_counts = {}
        for tbl in CORE_TABLES:
            try:
                sqlite_counts[tbl] = sconn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
            except Exception:
                sqlite_counts[tbl] = 0
        sconn.close()

        active_engine = "postgresql_18_primary" if pg_online else "sqlite_wal_hot_standby_failover"
        return {
            "status": "ok",
            "active_engine": active_engine,
            "ha_mode": "ACTIVE_ACTIVE_DUAL_WRITE" if pg_online else "FAILOVER_HOT_STANDBY",
            "pg_primary_online": pg_online,
            "pg_version": pg_version,
            "sqlite_standby_online": True,
            "sqlite_journal_mode": "wal",
            "tables_count": len(CORE_TABLES),
            "pg_table_rows": pg_counts,
            "sqlite_table_rows": sqlite_counts,
            "in_sync": (pg_counts == sqlite_counts) if pg_online else False,
            "probe_latency_ms": round((time.perf_counter() - t0) * 1000, 2),
        }


REPO = DualEngineHARepository(PG_DSN, LOCAL_SQLITE_PATH)


def calc_ebbinghaus_urgency(lookup_count: int, days_since_seen: float, syllabus_tier: str) -> float:
    freq_term = 0.35 * math.log(1.0 + max(1, lookup_count))
    decay_term = 0.45 * (1.0 - math.exp(-max(0.1, days_since_seen) / 3.0))
    tier_bonus = 0.20 if "CORE" in syllabus_tier.upper() else 0.10
    return round(min(1.0, freq_term + decay_term + tier_bonus), 4)


def generate_cloze_pattern(content_en: str) -> str:
    words = content_en.split()
    if len(words) >= 4:
        words[1] = f"[KEY: {words[1]}]"
        if len(words) >= 7:
            words[4] = f"[KEY: {words[4]}]"
        return " ".join(words)
    return f"[______] ({content_en})"


def verify_bearer(headers, simulate_pg_down: bool = False) -> str | None:
    auth = headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth[7:].strip()
    if not token:
        return None
    pconn = REPO.get_pg_conn(simulate_down=simulate_pg_down)
    if pconn is not None:
        try:
            with pconn.cursor() as cur:
                cur.execute("SELECT user_id FROM sys_users WHERE token_secret = %s", (token,))
                row = cur.fetchone()
                if row:
                    return row[0]
        finally:
            pconn.close()
    sconn = REPO.get_sqlite_conn()
    row = sconn.execute("SELECT user_id FROM sys_users WHERE token_secret = ?", (token,)).fetchone()
    sconn.close()
    if row:
        return row[0]
    if token.startswith("kaoyan-scholar-") and token.endswith("-kaoyan2026"):
        parts = token.split("-")
        if len(parts) >= 4:
            return parts[2]
    return None


class KaoyanModularHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def _send_json(self, code: int, payload: dict, req_id: str = "", t0: float = 0.0, engine_hdr: str = "pg18+sqlite_wal", idem_replay: bool = False):
        if req_id:
            payload.setdefault("request_id", req_id)
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        if req_id:
            self.send_header("X-Request-ID", req_id)
        if t0 > 0:
            lat_str = str(round((time.perf_counter() - t0) * 1000, 2))
            self.send_header("X-Response-Time-Ms", lat_str)
            self.send_header("X-Latency-Ms", lat_str)
        self.send_header("X-DB-Engine", engine_hdr)
        if idem_replay:
            self.send_header("X-Idempotent-Replay", "true")
        self.end_headers()
        self.wfile.write(body)

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

    def do_GET(self):
        t0 = time.perf_counter()
        req_id = self.headers.get("X-Request-ID", f"req-{uuid.uuid4().hex[:12]}")
        sim_down = self.headers.get("X-Simulate-PG-Down", "0") == "1"
        parsed = urlparse(self.path)

        # Layer 2 Security: Block automated vulnerability scanner probes (.env, .sql, .php, .bak, etc.)
        lower_p = parsed.path.lower()
        if any(lower_p.endswith(ext) for ext in (".sql", ".bak", ".php", ".ini", ".yml", ".yaml", ".properties", ".env", ".envrc")) or "/.env" in lower_p or "/.git" in lower_p:
            return self._send_json(404, {"status": "not_found"}, req_id=req_id, t0=t0)

        if parsed.path == "/api/health":
            ha = REPO.get_ha_status(simulate_pg_down=sim_down)
            return self._send_json(
                200,
                {
                    "status": "ok",
                    "service": "kaoyan-english-hub-v3-pg-ha",
                    "domain": "kaoyan.elenalyl.top",
                    "containerized": True,
                    "db_engine": ha["active_engine"],
                    "ha_mode": ha["ha_mode"],
                    "pg_primary_online": ha["pg_primary_online"],
                    "sqlite_standby_online": ha["sqlite_standby_online"],
                    "tables_count": len(CORE_TABLES),
                    "tables": CORE_TABLES,
                },
                req_id=req_id,
                t0=t0,
                engine_hdr=ha["active_engine"],
            )

        if parsed.path == "/api/ha/status":
            ha = REPO.get_ha_status(simulate_pg_down=sim_down)
            return self._send_json(200, ha, req_id=req_id, t0=t0, engine_hdr=ha["active_engine"])

        if parsed.path in ("/api/bootstrap", "/api/state", "/api/passages", "/api/annotations/list", "/api/essay/list"):
            qs = parse_qs(parsed.query)
            uid = verify_bearer(self.headers, simulate_pg_down=sim_down) or qs.get("user_id", ["colleague_a"])[0]
            passage_id = qs.get("passage_id", ["P2024_EN1_T1"])[0]
            theme_filter = qs.get("theme_tag", [""])[0]

            pconn = REPO.get_pg_conn(simulate_down=sim_down)
            engine_used = "postgresql_18_primary" if pconn is not None else "sqlite_wal_hot_standby_failover"

            if pconn is not None:
                try:
                    with pconn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                        cur.execute("SELECT COUNT(*) AS cnt FROM exam_passages;")
                        p_cnt = max(2, cur.fetchone()["cnt"])
                        cur.execute("SELECT * FROM exam_passages ORDER BY year DESC, created_at DESC LIMIT 20;")
                        passages = [dict(r) for r in cur.fetchall()]
                        cur.execute("SELECT * FROM user_progress_anchors WHERE user_id = %s;", (uid,))
                        anchor_row = cur.fetchone()
                        cur.execute(
                            "SELECT lemma AS word, lemma, syllabus_tier, lookup_count, last_seen_at, days_since_seen, urgency_score, exam_source, contextual_meaning, mastery_state FROM user_vocab_ledger WHERE user_id = %s ORDER BY urgency_score DESC, lookup_count DESC;",
                            (uid,),
                        )
                        vocab_rows = [dict(r) for r in cur.fetchall()]
                        cur.execute(
                            "SELECT * FROM annotation_spans WHERE user_id = %s AND passage_id = %s ORDER BY para_idx ASC, start_offset ASC;",
                            (uid, passage_id),
                        )
                        annotations = [dict(r) for r in cur.fetchall()]
                        if theme_filter:
                            cur.execute(
                                "SELECT * FROM essay_corpus_snippets WHERE user_id = %s AND theme_tag = %s ORDER BY created_at DESC;",
                                (uid, theme_filter),
                            )
                        else:
                            cur.execute("SELECT * FROM essay_corpus_snippets WHERE user_id = %s ORDER BY created_at DESC;", (uid,))
                        essays = [dict(r) for r in cur.fetchall()]
                finally:
                    pconn.close()
            else:
                sconn = REPO.get_sqlite_conn()
                p_cnt = max(2, sconn.execute("SELECT COUNT(*) FROM exam_passages").fetchone()[0])
                passages = [dict(r) for r in sconn.execute("SELECT * FROM exam_passages ORDER BY year DESC, created_at DESC LIMIT 20").fetchall()]
                anchor_row = sconn.execute("SELECT * FROM user_progress_anchors WHERE user_id = ?", (uid,)).fetchone()
                vocab_rows = [
                    dict(r)
                    for r in sconn.execute(
                        "SELECT lemma AS word, lemma, syllabus_tier, lookup_count, last_seen_at, days_since_seen, urgency_score, exam_source, contextual_meaning, mastery_state FROM user_vocab_ledger WHERE user_id = ? ORDER BY urgency_score DESC, lookup_count DESC",
                        (uid,),
                    ).fetchall()
                ]
                annotations = [
                    dict(r)
                    for r in sconn.execute(
                        "SELECT * FROM annotation_spans WHERE user_id = ? AND passage_id = ? ORDER BY para_idx ASC, start_offset ASC",
                        (uid, passage_id),
                    ).fetchall()
                ]
                if theme_filter:
                    essays = [
                        dict(r)
                        for r in sconn.execute(
                            "SELECT * FROM essay_corpus_snippets WHERE user_id = ? AND theme_tag = ? ORDER BY created_at DESC",
                            (uid, theme_filter),
                        ).fetchall()
                    ]
                else:
                    essays = [dict(r) for r in sconn.execute("SELECT * FROM essay_corpus_snippets WHERE user_id = ? ORDER BY created_at DESC", (uid,)).fetchall()]
                sconn.close()

            if parsed.path == "/api/passages":
                return self._send_json(200, {"status": "ok", "engine": engine_used, "passages": passages}, req_id=req_id, t0=t0, engine_hdr=engine_used)
            if parsed.path == "/api/annotations/list":
                return self._send_json(200, {"status": "ok", "engine": engine_used, "annotations": annotations}, req_id=req_id, t0=t0, engine_hdr=engine_used)
            if parsed.path == "/api/essay/list":
                return self._send_json(200, {"status": "ok", "engine": engine_used, "essays": essays}, req_id=req_id, t0=t0, engine_hdr=engine_used)

            return self._send_json(
                200,
                {
                    "status": "ok",
                    "engine": engine_used,
                    "user_id": uid,
                    "passage_count": p_cnt,
                    "passages": passages,
                    "anchor": dict(anchor_row) if anchor_row else {"last_para_idx": 2, "streak_days": 12, "rev_no": 1},
                    "vocab": vocab_rows,
                    "annotations": annotations,
                    "essays": essays,
                },
                req_id=req_id,
                t0=t0,
                engine_hdr=engine_used,
            )

        if parsed.path in ("/", "/index.html"):
            html = HTML_PATH.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(html)
            return

        self._send_json(404, {"status": "not_found", "message": "Endpoint not found"}, req_id=req_id, t0=t0)

    def do_POST(self):
        t0 = time.perf_counter()
        req_id = self.headers.get("X-Request-ID", f"req-{uuid.uuid4().hex[:12]}")
        sim_down = self.headers.get("X-Simulate-PG-Down", "0") == "1"
        idem_key = self.headers.get("X-Idempotency-Key", "").strip()

        length = int(self.headers.get("Content-Length", "0"))
        if length > 2 * 1024 * 1024:
            return self._send_json(413, {"status": "payload_too_large", "message": "Request payload exceeds 2MB limit"}, req_id=req_id, t0=t0)
        raw = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        try:
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError("JSON root must be object")
        except Exception:
            return self._send_json(400, {"status": "bad_request", "message": "Invalid JSON payload"}, req_id=req_id, t0=t0)

        now = now_str()

        if self.path == "/api/auth/login":
            u = str(data.get("username", "colleague_a")).strip() or "colleague_a"
            k = str(data.get("passcode", "")).strip()
            if k != "kaoyan2026":
                return self._send_json(401, {"status": "unauthorized", "message": "学籍口令错误"}, req_id=req_id, t0=t0)
            token = f"kaoyan-scholar-{u}-kaoyan2026"

            sconn = REPO.get_sqlite_conn()
            sconn.execute("INSERT OR IGNORE INTO sys_users VALUES (?, ?, ?, ?, ?, ?, ?)", (u, u, u, "SCHOLAR", k, token, now))
            sconn.execute("INSERT OR IGNORE INTO user_progress_anchors VALUES (?, ?, 2, ?, 2, ?, 12, 1, ?)", (u, "P2024_EN1_T1", "sp-sent-2", "", now))
            sconn.commit()
            anchor = dict(sconn.execute("SELECT * FROM user_progress_anchors WHERE user_id = ?", (u,)).fetchone())
            sconn.close()

            pg_ok = False
            pconn = REPO.get_pg_conn(simulate_down=sim_down)
            if pconn is not None:
                try:
                    with pconn:
                        with pconn.cursor() as cur:
                            cur.execute(
                                "INSERT INTO sys_users (user_id, username, display_name, role, passcode_hash, token_secret, created_at) VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (user_id) DO NOTHING",
                                (u, u, u, "SCHOLAR", k, token, now),
                            )
                            cur.execute(
                                "INSERT INTO user_progress_anchors (user_id, last_passage_id, last_para_idx, last_span_id, last_tab_idx, essay_draft_md, streak_days, rev_no, updated_at) VALUES (%s,%s,2,%s,2,%s,12,1,%s) ON CONFLICT (user_id) DO NOTHING",
                                (u, "P2024_EN1_T1", "sp-sent-2", "", now),
                            )
                    pg_ok = True
                finally:
                    pconn.close()

            REPO.record_ha_wal("LOGIN_UPSERT", "sys_users", u, {"user_id": u}, pg_ok, True)
            eng = "postgresql_18_primary" if pg_ok else "sqlite_wal_hot_standby_failover"
            return self._send_json(
                200,
                {"status": "ok", "engine": eng, "user_id": u, "role": "SCHOLAR", "token": token, "anchor": anchor},
                req_id=req_id,
                t0=t0,
                engine_hdr=eng,
            )

        uid = verify_bearer(self.headers, simulate_pg_down=sim_down)
        if not uid:
            return self._send_json(
                401,
                {"status": "guest_sandbox_locked", "message": "当前为访客只读沙箱，请先登录专属学籍账号以写入云端数据库"},
                req_id=req_id,
                t0=t0,
            )

        req_hash = hashlib.sha256(f"{uid}:{self.path}:{raw}".encode("utf-8")).hexdigest()
        if idem_key:
            sconn = REPO.get_sqlite_conn()
            existing = sconn.execute(
                "SELECT req_hash, resp_code, resp_body_json FROM api_idempotency_keys WHERE idempotency_key = ?",
                (idem_key,),
            ).fetchone()
            sconn.close()
            if existing:
                if existing["req_hash"] != req_hash:
                    return self._send_json(409, {"status": "idempotency_conflict", "message": "Idempotency key reused with different payload"}, req_id=req_id, t0=t0)
                cached_body = json.loads(existing["resp_body_json"])
                cached_body["idempotent_replay"] = True
                return self._send_json(existing["resp_code"], cached_body, req_id=req_id, t0=t0, idem_replay=True)

        def finalize_write(code: int, resp_payload: dict, op_type: str, tbl: str, pk: str, pg_ok: bool):
            tx_id = REPO.record_ha_wal(op_type, tbl, pk, data, pg_ok, True)
            resp_payload["tx_uuid"] = tx_id
            resp_payload["engine"] = "postgresql_18_primary" if pg_ok else "sqlite_wal_hot_standby_failover"
            if idem_key:
                raw_resp = json.dumps(resp_payload, ensure_ascii=False)
                sconn = REPO.get_sqlite_conn()
                sconn.execute(
                    "INSERT OR REPLACE INTO api_idempotency_keys VALUES (?,?,?,?,?,?,?)",
                    (idem_key, uid, self.path, req_hash, code, raw_resp, now),
                )
                sconn.commit()
                sconn.close()
                if pg_ok:
                    pconn = REPO.get_pg_conn(simulate_down=sim_down)
                    if pconn is not None:
                        try:
                            with pconn:
                                with pconn.cursor() as cur:
                                    cur.execute(
                                        "INSERT INTO api_idempotency_keys VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (idempotency_key) DO NOTHING",
                                        (idem_key, uid, self.path, req_hash, code, raw_resp, now),
                                    )
                        finally:
                            pconn.close()
            return self._send_json(code, resp_payload, req_id=req_id, t0=t0, engine_hdr=resp_payload["engine"])

        if self.path == "/api/progress/anchor":
            try:
                para_idx = int(data.get("last_para_idx", 2))
            except Exception:
                return self._send_json(400, {"status": "bad_request", "message": "last_para_idx must be integer"}, req_id=req_id, t0=t0)
            if para_idx < 0 or para_idx > 200:
                return self._send_json(422, {"status": "validation_error", "message": "last_para_idx out of valid range [0, 200]"}, req_id=req_id, t0=t0)
            span_id = str(data.get("last_span_id", "sp-sent-1"))[:64]
            passage_id = str(data.get("last_passage_id", "P2024_EN1_T1"))[:64]

            sconn = REPO.get_sqlite_conn()
            sconn.execute(
                "UPDATE user_progress_anchors SET last_passage_id = ?, last_para_idx = ?, last_span_id = ?, rev_no = rev_no + 1, updated_at = ? WHERE user_id = ?",
                (passage_id, para_idx, span_id, now, uid),
            )
            sconn.commit()
            row = sconn.execute("SELECT rev_no FROM user_progress_anchors WHERE user_id = ?", (uid,)).fetchone()
            rev_no = row["rev_no"] if row else 1
            sconn.close()

            pg_ok = False
            pconn = REPO.get_pg_conn(simulate_down=sim_down)
            if pconn is not None:
                try:
                    with pconn:
                        with pconn.cursor() as cur:
                            cur.execute(
                                "UPDATE user_progress_anchors SET last_passage_id = %s, last_para_idx = %s, last_span_id = %s, rev_no = rev_no + 1, updated_at = %s WHERE user_id = %s",
                                (passage_id, para_idx, span_id, now, uid),
                            )
                    pg_ok = True
                finally:
                    pconn.close()

            return finalize_write(
                200,
                {"status": "ok", "user_id": uid, "last_passage_id": passage_id, "last_para_idx": para_idx, "rev_no": rev_no},
                "UPDATE_ANCHOR",
                "user_progress_anchors",
                uid,
                pg_ok,
            )

        if self.path == "/api/ingest/passage":
            title = str(data.get("title", "")).strip()
            txt = str(data.get("raw_text", "")).strip()
            if not title or len(txt) < 10:
                return self._send_json(422, {"status": "validation_error", "message": "title and raw_text (>=10 chars) are required"}, req_id=req_id, t0=t0)
            year = int(data.get("year", 2025))
            exam_type = str(data.get("exam_type", "英语一"))[:32]
            text_no = str(data.get("text_no", "Text 1"))[:32]
            h = hashlib.sha256(txt.encode("utf-8")).hexdigest()[:16]
            pid = f"P_{uid}_{h}"
            paras = [p.strip() for p in re.split(r"\n+", txt) if p.strip()]

            sconn = REPO.get_sqlite_conn()
            lex_words = {r[0] for r in sconn.execute("SELECT lemma FROM syllabus_5500_lexicon").fetchall()}
            tokens = {w.lower() for w in re.findall(r"[A-Za-z]{4,}", txt)}
            hits = sorted(lex_words.intersection(tokens))
            paras_json = json.dumps(paras, ensure_ascii=False)
            hits_json = json.dumps(hits, ensure_ascii=False)

            sconn.execute(
                "INSERT OR REPLACE INTO exam_passages VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (pid, uid, year, exam_type, text_no, title, paras_json, hits_json, h, now),
            )
            sconn.commit()
            p_cnt = max(2, sconn.execute("SELECT COUNT(*) FROM exam_passages").fetchone()[0])
            sconn.close()

            pg_ok = False
            pconn = REPO.get_pg_conn(simulate_down=sim_down)
            if pconn is not None:
                try:
                    with pconn:
                        with pconn.cursor() as cur:
                            cur.execute(
                                "INSERT INTO exam_passages (passage_id, owner_user_id, year, exam_type, text_no, title, paragraphs_json, syllabus_hits_json, sha256_hash, created_at) "
                                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
                                "ON CONFLICT (passage_id) DO UPDATE SET title = EXCLUDED.title, paragraphs_json = EXCLUDED.paragraphs_json, syllabus_hits_json = EXCLUDED.syllabus_hits_json",
                                (pid, uid, year, exam_type, text_no, title, paras_json, hits_json, h, now),
                            )
                    pg_ok = True
                finally:
                    pconn.close()

            return finalize_write(
                200,
                {"status": "ok", "passage_id": pid, "user_id": uid, "passage_count": p_cnt, "syllabus_hits": hits, "sha256_hash": h},
                "INGEST_PASSAGE",
                "exam_passages",
                pid,
                pg_ok,
            )

        if self.path in ("/api/ingest/vocab", "/api/vocab/lookup"):
            lemma = str(data.get("lemma", "")).strip().lower()
            if not lemma or not re.match(r"^[a-zA-Z\-]{2,45}$", lemma):
                return self._send_json(422, {"status": "validation_error", "message": "Invalid English lemma (2..45 letters)"}, req_id=req_id, t0=t0)
            tier = str(data.get("syllabus_tier", "CORE_1800"))[:32]
            days_ago = float(data.get("days_since_seen", 0.5))
            exam_src = str(data.get("exam_source", "真题实时查词"))[:128]
            ctx_meaning = str(data.get("contextual_meaning", "学籍云端同步词条"))[:512]

            sconn = REPO.get_sqlite_conn()
            cur_row = sconn.execute("SELECT lookup_count FROM user_vocab_ledger WHERE user_id = ? AND lemma = ?", (uid, lemma)).fetchone()
            new_cnt = (cur_row["lookup_count"] + 1) if cur_row else int(data.get("lookup_count", 1))
            urg = calc_ebbinghaus_urgency(new_cnt, days_ago, tier)

            sconn.execute(
                "INSERT INTO user_vocab_ledger (user_id, lemma, syllabus_tier, lookup_count, last_seen_at, days_since_seen, urgency_score, exam_source, contextual_meaning, mastery_state) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'LEARNING') "
                "ON CONFLICT(user_id, lemma) DO UPDATE SET lookup_count = ?, last_seen_at = excluded.last_seen_at, days_since_seen = excluded.days_since_seen, urgency_score = ?, contextual_meaning = excluded.contextual_meaning",
                (uid, lemma, tier, new_cnt, now, days_ago, urg, exam_src, ctx_meaning, new_cnt, urg),
            )
            sconn.commit()
            sconn.close()

            pg_ok = False
            pconn = REPO.get_pg_conn(simulate_down=sim_down)
            if pconn is not None:
                try:
                    with pconn:
                        with pconn.cursor() as cur:
                            cur.execute(
                                "INSERT INTO user_vocab_ledger (user_id, lemma, syllabus_tier, lookup_count, last_seen_at, days_since_seen, urgency_score, exam_source, contextual_meaning, mastery_state) "
                                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'LEARNING') "
                                "ON CONFLICT (user_id, lemma) DO UPDATE SET lookup_count = EXCLUDED.lookup_count, last_seen_at = EXCLUDED.last_seen_at, days_since_seen = EXCLUDED.days_since_seen, urgency_score = EXCLUDED.urgency_score, contextual_meaning = EXCLUDED.contextual_meaning",
                                (uid, lemma, tier, new_cnt, now, days_ago, urg, exam_src, ctx_meaning),
                            )
                    pg_ok = True
                finally:
                    pconn.close()

            return finalize_write(
                200,
                {"status": "ok", "user_id": uid, "lemma": lemma, "lookup_count": new_cnt, "urgency_score": urg, "syllabus_tier": tier},
                "VOCAB_EBBINGHAUS_UPSERT",
                "user_vocab_ledger",
                f"{uid}:{lemma}",
                pg_ok,
            )

        if self.path in ("/api/annotations/save", "/api/notes"):
            selected_text = str(data.get("selected_text", data.get("text", ""))).strip()
            if not selected_text:
                return self._send_json(422, {"status": "validation_error", "message": "selected_text cannot be empty"}, req_id=req_id, t0=t0)
            passage_id = str(data.get("passage_id", "P2024_EN1_T1"))[:64]
            granularity = str(data.get("granularity", "SENTENCE"))[:32]
            para_idx = int(data.get("para_idx", 1))
            start_offset = int(data.get("start_offset", 0))
            end_offset = int(data.get("end_offset", len(selected_text)))
            prefix_quote = str(data.get("prefix_quote", ""))[:64]
            suffix_quote = str(data.get("suffix_quote", ""))[:64]
            syntax_bd = str(data.get("syntax_breakdown", data.get("breakdown", "")))
            comment = str(data.get("user_comment", data.get("comment", "")))
            span_id = str(data.get("span_id", data.get("id", ""))).strip() or f"sp-{hashlib.sha256(f'{uid}:{passage_id}:{para_idx}:{selected_text}'.encode('utf-8')).hexdigest()[:12]}"

            sconn = REPO.get_sqlite_conn()
            sconn.execute(
                "INSERT INTO annotation_spans (span_id, user_id, passage_id, granularity, para_idx, start_offset, end_offset, selected_text, prefix_quote, suffix_quote, syntax_breakdown, user_comment, promoted_snippet_id, version, created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?, '', 1, ?) "
                "ON CONFLICT(span_id) DO UPDATE SET syntax_breakdown = excluded.syntax_breakdown, user_comment = excluded.user_comment, version = annotation_spans.version + 1",
                (span_id, uid, passage_id, granularity, para_idx, start_offset, end_offset, selected_text, prefix_quote, suffix_quote, syntax_bd, comment, now),
            )
            sconn.commit()
            sconn.close()

            pg_ok = False
            pconn = REPO.get_pg_conn(simulate_down=sim_down)
            if pconn is not None:
                try:
                    with pconn:
                        with pconn.cursor() as cur:
                            cur.execute(
                                "INSERT INTO annotation_spans (span_id, user_id, passage_id, granularity, para_idx, start_offset, end_offset, selected_text, prefix_quote, suffix_quote, syntax_breakdown, user_comment, promoted_snippet_id, version, created_at) "
                                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'',1,%s) "
                                "ON CONFLICT (span_id) DO UPDATE SET syntax_breakdown = EXCLUDED.syntax_breakdown, user_comment = EXCLUDED.user_comment, version = annotation_spans.version + 1",
                                (span_id, uid, passage_id, granularity, para_idx, start_offset, end_offset, selected_text, prefix_quote, suffix_quote, syntax_bd, comment, now),
                            )
                    pg_ok = True
                finally:
                    pconn.close()

            return finalize_write(
                200,
                {"status": "ok", "span_id": span_id, "passage_id": passage_id, "granularity": granularity},
                "SAVE_ANNOTATION",
                "annotation_spans",
                span_id,
                pg_ok,
            )

        if self.path in ("/api/essay/save", "/api/annotations/promote", "/api/essay"):
            span_id = str(data.get("span_id", data.get("id", ""))).strip()
            theme_tag = str(data.get("theme_tag", data.get("theme", "科技创新与AI伦理")))[:64]
            func_slot = str(data.get("func_slot", data.get("slot", "段首论点引入 (Topic Opener)")))[:64]
            content_en = str(data.get("content_en", data.get("en", ""))).strip()
            translation_zh = str(data.get("translation_zh", data.get("zh", ""))).strip() or "阅读精读笔记一键升格语料"
            granularity = str(data.get("granularity", "SENTENCE"))[:32]
            source_ref = str(data.get("source_ref", "2024 英语一 Text 1"))[:128]

            sconn = REPO.get_sqlite_conn()
            if self.path == "/api/annotations/promote" and span_id and not content_en:
                sp_row = sconn.execute("SELECT * FROM annotation_spans WHERE span_id = ?", (span_id,)).fetchone()
                if not sp_row:
                    sconn.close()
                    return self._send_json(404, {"status": "not_found", "message": f"Annotation span {span_id} not found"}, req_id=req_id, t0=t0)
                content_en = sp_row["selected_text"]
                translation_zh = sp_row["user_comment"] or sp_row["syntax_breakdown"] or translation_zh
                granularity = sp_row["granularity"]
                source_ref = f"Promoted from {sp_row['passage_id']} (span:{span_id})"

            if not content_en:
                sconn.close()
                return self._send_json(422, {"status": "validation_error", "message": "content_en or valid span_id is required"}, req_id=req_id, t0=t0)

            cloze = str(data.get("cloze_pattern", "")).strip() or generate_cloze_pattern(content_en)
            snippet_id = str(data.get("snippet_id", data.get("id", ""))).strip() or f"es-{hashlib.sha256(f'{uid}:{theme_tag}:{content_en}'.encode('utf-8')).hexdigest()[:12]}"

            sconn.execute(
                "INSERT INTO essay_corpus_snippets (snippet_id, user_id, theme_tag, func_slot, granularity, content_en, cloze_pattern, translation_zh, source_ref, usage_count, created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?, 1, ?) "
                "ON CONFLICT(snippet_id) DO UPDATE SET theme_tag = excluded.theme_tag, func_slot = excluded.func_slot, cloze_pattern = excluded.cloze_pattern, usage_count = essay_corpus_snippets.usage_count + 1",
                (snippet_id, uid, theme_tag, func_slot, granularity, content_en, cloze, translation_zh, source_ref, now),
            )
            if span_id:
                sconn.execute("UPDATE annotation_spans SET promoted_snippet_id = ? WHERE span_id = ?", (snippet_id, span_id))
            sconn.commit()
            sconn.close()

            pg_ok = False
            pconn = REPO.get_pg_conn(simulate_down=sim_down)
            if pconn is not None:
                try:
                    with pconn:
                        with pconn.cursor() as cur:
                            cur.execute(
                                "INSERT INTO essay_corpus_snippets (snippet_id, user_id, theme_tag, func_slot, granularity, content_en, cloze_pattern, translation_zh, source_ref, usage_count, created_at) "
                                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,1,%s) "
                                "ON CONFLICT (snippet_id) DO UPDATE SET theme_tag = EXCLUDED.theme_tag, func_slot = EXCLUDED.func_slot, cloze_pattern = EXCLUDED.cloze_pattern, usage_count = essay_corpus_snippets.usage_count + 1",
                                (snippet_id, uid, theme_tag, func_slot, granularity, content_en, cloze, translation_zh, source_ref, now),
                            )
                            if span_id:
                                cur.execute("UPDATE annotation_spans SET promoted_snippet_id = %s WHERE span_id = %s", (snippet_id, span_id))
                    pg_ok = True
                finally:
                    pconn.close()

            return finalize_write(
                200,
                {"status": "ok", "snippet_id": snippet_id, "promoted_from_span_id": span_id, "theme_tag": theme_tag, "cloze_pattern": cloze},
                "SAVE_OR_PROMOTE_ESSAY",
                "essay_corpus_snippets",
                snippet_id,
                pg_ok,
            )

        return self._send_json(404, {"status": "not_found", "message": "Unknown API endpoint"}, req_id=req_id, t0=t0)


if __name__ == "__main__":
    REPO.init_and_migrate_both_engines()
    srv = ThreadingHTTPServer(("0.0.0.0", 60231), KaoyanModularHandler)
    print("Kaoyan Modular Hub v3.0 (PG18 Primary + SQLite WAL Standby) listening on 0.0.0.0:60231", flush=True)
    srv.serve_forever()
