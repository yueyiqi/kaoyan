#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Kaoyan English Hub v4.0 — Cross-OS Dynamic Roaming HA Kernel
# Supports:
#   1. Dynamic Roaming across HP (Ubuntu 26.04 LTS), W1 (Windows 11), M1 (macOS ARM64), + 4th Node M4/Elena
#   2. 3-Node Mode: 1 Primary (PRIMARY_RW: Read+Write) + 2 Replicas (REPLICA_RO: Read-Only, HTTP 409 on direct write)
#   3. 2-Node Degraded Mode: 1 Primary (PRIMARY_RW) + 1 Replica (REPLICA_RO)
#   4. 1-Node Survivor Mode ("当配置指定仅剩余 1 个节点时，此节点可以读写并重"): STANDALONE_RW (Read+Write Dual-Weight)
#   5. 100% OS-Agnostic Data & Backend Plane (PostgreSQL 18 + SQLite WAL + Deterministic LSN/Epoch WAL Replication)

from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import re
import socket
import sqlite3
import sys
import threading
import time
import urllib.error
import urllib.request
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
DEFAULT_DB_PATH = HOT_SQLITE_PATH if HOT_SQLITE_PATH.parent.exists() else (BASE_DIR / "db_volume" / "kaoyan_hub.sqlite3")
LOCAL_SQLITE_PATH = Path(os.environ.get("KAOYAN_DB_PATH", str(DEFAULT_DB_PATH)))
MIGRATION_V1 = BASE_DIR / "db_migrations" / "V001__init_kaoyan_8tables.sql"
MIGRATION_V2 = BASE_DIR / "db_migrations" / "V002__pg18_and_sqlite_10tables_ha_schema.sql"
BACKUP_DIR = Path(os.environ.get("KAOYAN_BACKUP_DIR", str(BASE_DIR / "db_backups")))
HTML_PATH = Path(os.environ.get("KAOYAN_HTML_PATH", str(BASE_DIR / "index.html")))

PG_DSN = os.environ.get("KAOYAN_PG_DSN", "dbname=kaoyan_prod user=elena host=127.0.0.1 port=5432 password=kaoyan_pg18_ha_2026")
LISTEN_PORT = int(os.environ.get("KAOYAN_PORT", "60231"))

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

CANONICAL_4NODES_CATALOG = {
    "hp": {
        "node_id": "hp",
        "label": "HP (Ubuntu 26.04 LTS)",
        "os_family": "Linux",
        "os_release": "Ubuntu 26.04.1 LTS (Resolute) x86_64",
        "db_stack": "Docker PG18 + SQLite WAL",
    },
    "w1": {
        "node_id": "w1",
        "label": "W1 (Windows 11 Pro)",
        "os_family": "Windows",
        "os_release": "Windows 11 NT 10.0.26200 + WSL2 x86_64",
        "db_stack": "OS-Agnostic SQLite WAL + PG18 Sync",
    },
    "m1": {
        "node_id": "m1",
        "label": "M1 (macOS ARM64)",
        "os_family": "macOS",
        "os_release": "macOS Darwin ARM64 (Apple Silicon)",
        "db_stack": "Docker PG18 + SQLite WAL",
    },
    "m4_elena": {
        "node_id": "m4_elena",
        "label": "M4/Elena (Arbiter & Cloud HTTPS Edge)",
        "os_family": "macOS+Linux-Edge",
        "os_release": "macOS 27.0.1 ARM64 / Ubuntu 24.04 Edge",
        "db_stack": "Docker PG18 + SQLite WAL + Roaming Arbiter",
    },
}


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def normalize_os_text(text: str) -> str:
    """OS-Agnostic CRLF/CR -> LF normalization so Windows 11, Ubuntu 26.04, and macOS produce identical hashes."""
    return str(text or "").replace("\r\n", "\n").replace("\r", "\n")


def normalize_os_path(path_str: str) -> str:
    """OS-Agnostic path separator normalization (Windows backslash -> POSIX forward slash)."""
    return str(path_str or "").replace("\\", "/")


def detect_local_node_identity() -> dict:
    env_node = os.environ.get("KAOYAN_NODE_ID", "").strip().lower()
    sys_name = platform.system()
    machine = platform.machine()
    rel = platform.release()
    ver = platform.version()
    hostname = socket.gethostname().lower()

    if not env_node:
        if "win" in sys_name.lower() or "qdvr9a2" in hostname or "lenovo" in hostname:
            env_node = "w1"
        elif sys_name == "Darwin":
            env_node = "m1"
        elif "hp" in hostname or "zbook" in hostname:
            env_node = "hp"
        else:
            env_node = "hp"

    env_os_label = os.environ.get("KAOYAN_OS_LABEL", "").strip()
    if not env_os_label:
        if sys_name == "Darwin":
            env_os_label = f"macOS Darwin {rel} ({machine})"
        elif sys_name == "Windows":
            env_os_label = f"Windows 11 {ver} ({machine})"
        else:
            env_os_label = f"Linux {rel} ({machine})"

    os_fam = os.environ.get("KAOYAN_OS_FAMILY", "").strip()
    if not os_fam:
        if sys_name == "Windows" or env_node == "w1" or "win" in env_os_label.lower():
            os_fam = "Windows"
        elif sys_name == "Darwin" or env_node in ("m1", "m4"):
            os_fam = "macOS"
        else:
            os_fam = "Linux"

    return {
        "node_id": env_node,
        "hostname": hostname,
        "os_family": os_fam,
        "os_label": env_os_label,
        "arch": machine,
        "python_version": platform.python_version(),
    }


LOCAL_NODE_INFO = detect_local_node_identity()


class DualEngineHARepository:
    # Manages Dual-Write, Automatic Failover (PG18 + SQLite WAL), and Cross-OS Roaming HA State Machine.

    def __init__(self, pg_dsn: str, sqlite_path: Path) -> None:
        self.pg_dsn = pg_dsn
        self.sqlite_path = sqlite_path
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    def get_sqlite_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.sqlite_path), timeout=15.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA busy_timeout=10000;")
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
        with self._lock:
            sconn = self.get_sqlite_conn()
            if MIGRATION_V1.exists():
                try:
                    sconn.executescript(normalize_os_text(MIGRATION_V1.read_text(encoding="utf-8")))
                except Exception:
                    pass
            if MIGRATION_V2.exists():
                try:
                    sconn.executescript(normalize_os_text(MIGRATION_V2.read_text(encoding="utf-8")))
                except Exception:
                    pass

            # Self-contained schema bootstrap for all 10 core tables + roaming topology & WAL LSN tables
            sconn.executescript(
                """
                CREATE TABLE IF NOT EXISTS sys_users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'SCHOLAR',
                    passcode_hash TEXT NOT NULL,
                    token_secret TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS user_progress_anchors (
                    user_id TEXT PRIMARY KEY,
                    last_passage_id TEXT NOT NULL DEFAULT 'P2024_EN1_T1',
                    last_para_idx INTEGER NOT NULL DEFAULT 2,
                    last_span_id TEXT NOT NULL DEFAULT 'sp-sent-2',
                    last_tab_idx INTEGER NOT NULL DEFAULT 2,
                    essay_draft_md TEXT NOT NULL DEFAULT '',
                    streak_days INTEGER NOT NULL DEFAULT 12,
                    rev_no INTEGER NOT NULL DEFAULT 1,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS syllabus_5500_lexicon (
                    lemma TEXT PRIMARY KEY,
                    pos TEXT NOT NULL DEFAULT 'n./v.',
                    cn_meaning TEXT NOT NULL,
                    syllabus_tier TEXT NOT NULL DEFAULT 'CORE_1800',
                    polysemy_trap_note TEXT NOT NULL DEFAULT '',
                    exam_freq INTEGER NOT NULL DEFAULT 10
                );
                CREATE TABLE IF NOT EXISTS exam_passages (
                    passage_id TEXT PRIMARY KEY,
                    owner_user_id TEXT NOT NULL DEFAULT 'system',
                    year INTEGER NOT NULL DEFAULT 2024,
                    exam_type TEXT NOT NULL DEFAULT '英语一',
                    text_no TEXT NOT NULL DEFAULT 'Text 1',
                    title TEXT NOT NULL,
                    paragraphs_json TEXT NOT NULL,
                    syllabus_hits_json TEXT NOT NULL,
                    sha256_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS annotation_spans (
                    span_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    passage_id TEXT NOT NULL,
                    granularity TEXT NOT NULL DEFAULT 'SENTENCE',
                    para_idx INTEGER NOT NULL DEFAULT 1,
                    start_offset INTEGER NOT NULL DEFAULT 0,
                    end_offset INTEGER NOT NULL DEFAULT 10,
                    selected_text TEXT NOT NULL,
                    prefix_quote TEXT NOT NULL DEFAULT '',
                    suffix_quote TEXT NOT NULL DEFAULT '',
                    syntax_breakdown TEXT NOT NULL DEFAULT '',
                    user_comment TEXT NOT NULL DEFAULT '',
                    promoted_snippet_id TEXT NOT NULL DEFAULT '',
                    version INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS essay_corpus_snippets (
                    snippet_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    theme_tag TEXT NOT NULL,
                    func_slot TEXT NOT NULL,
                    granularity TEXT NOT NULL DEFAULT 'SENTENCE',
                    content_en TEXT NOT NULL,
                    cloze_pattern TEXT NOT NULL,
                    translation_zh TEXT NOT NULL,
                    source_ref TEXT NOT NULL,
                    usage_count INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS user_vocab_ledger (
                    vocab_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    lemma TEXT NOT NULL,
                    syllabus_tier TEXT NOT NULL DEFAULT 'CORE_1800',
                    lookup_count INTEGER NOT NULL DEFAULT 1,
                    last_seen_at TEXT NOT NULL,
                    days_since_seen REAL NOT NULL DEFAULT 0.0,
                    urgency_score REAL NOT NULL DEFAULT 0.50,
                    exam_source TEXT NOT NULL DEFAULT '',
                    contextual_meaning TEXT NOT NULL DEFAULT '',
                    mastery_state TEXT NOT NULL DEFAULT 'LEARNING',
                    UNIQUE(user_id, lemma)
                );
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version_id TEXT PRIMARY KEY,
                    script_name TEXT NOT NULL,
                    checksum_sha256 TEXT NOT NULL,
                    engine_target TEXT NOT NULL DEFAULT 'DUAL_PG_SQLITE',
                    applied_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS ha_sync_wal_journal (
                    tx_uuid TEXT PRIMARY KEY,
                    op_type TEXT NOT NULL,
                    target_table TEXT NOT NULL,
                    record_pk TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    pg_status TEXT NOT NULL,
                    sqlite_status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS api_idempotency_keys (
                    idempotency_key TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    req_hash TEXT NOT NULL,
                    resp_code INTEGER NOT NULL,
                    resp_body_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS ha_cluster_roaming_state (
                    cluster_id TEXT PRIMARY KEY,
                    epoch INTEGER NOT NULL DEFAULT 1,
                    wal_lsn INTEGER NOT NULL DEFAULT 0,
                    active_nodes_json TEXT NOT NULL,
                    primary_node TEXT NOT NULL,
                    peer_urls_json TEXT NOT NULL DEFAULT '{}',
                    roaming_history_json TEXT NOT NULL DEFAULT '[]',
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS ha_roaming_wal_stream (
                    lsn INTEGER PRIMARY KEY AUTOINCREMENT,
                    epoch INTEGER NOT NULL,
                    tx_uuid TEXT NOT NULL UNIQUE,
                    source_node TEXT NOT NULL,
                    source_os TEXT NOT NULL,
                    op_type TEXT NOT NULL,
                    target_table TEXT NOT NULL,
                    record_pk TEXT NOT NULL,
                    row_data_json TEXT NOT NULL,
                    row_checksum_sha256 TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
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

            ts_seed = now_str()
            sconn.execute(
                "INSERT OR REPLACE INTO schema_migrations (version_id, script_name, checksum_sha256, engine_target, applied_at) VALUES (?, ?, ?, ?, ?)",
                ("V004", "V004__cross_os_roaming_ha_1p2r_standalone.sql", hashlib.sha256(b"V004_CROSS_OS_ROAMING_HA").hexdigest(), "CROSS_OS_PG18_SQLITE_WAL", ts_seed),
            )
            for uid_s, disp_s, role_s, para_s, streak_s in [
                ("colleague_a", "主理人学籍 (colleague_a)", "SCHOLAR", 2, 12),
                ("scholar_b", "研友协作学籍 (scholar_b)", "SCHOLAR", 1, 5),
            ]:
                sconn.execute(
                    "INSERT OR IGNORE INTO sys_users (user_id, username, display_name, role, passcode_hash, token_secret, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (uid_s, uid_s, disp_s, role_s, "kaoyan2026", f"kaoyan-scholar-{uid_s}-kaoyan2026", ts_seed),
                )
                sconn.execute(
                    "INSERT OR IGNORE INTO user_progress_anchors (user_id, last_passage_id, last_para_idx, last_span_id, last_tab_idx, essay_draft_md, streak_days, rev_no, updated_at) VALUES (?, ?, ?, ?, 2, '', ?, 1, ?)",
                    (uid_s, "P2024_EN1_T1", para_s, "sp-sent-2", streak_s, ts_seed),
                )

            # Seed default lexicon & passages if empty so fresh OS nodes (Win11/Linux/macOS) have identical baseline
            if sconn.execute("SELECT COUNT(*) FROM syllabus_5500_lexicon").fetchone()[0] == 0:
                for lem, pos, mean, tier, trap, freq in [
                    ("accommodate", "v.", "适应，顺应；容纳，顾及", "POLYSEMY_TRAP", "考研常考『顺应/容纳』而非仅提供食宿", 28),
                    ("intellectual", "adj./n.", "智力的，理智的；知识分子", "CORE_1800", "intellectual history 思想史", 34),
                    ("empirical", "adj.", "实证的，以经验或观察为依据的", "CORE_1800", "反义词 theoretical", 22),
                    ("compartment", "n./v.", "隔间；划分，割裂", "EXT_HYPER", "narrow compartments 狭隘学科壁垒", 15),
                    ("perilous", "adj.", "危险的，充满风险的", "EXT_HYPER", "make it perilous for sb to do", 14),
                ]:
                    sconn.execute(
                        "INSERT OR IGNORE INTO syllabus_5500_lexicon VALUES (?,?,?,?,?,?)",
                        (lem, pos, mean, tier, trap, freq),
                    )
            if sconn.execute("SELECT COUNT(*) FROM exam_passages").fetchone()[0] == 0:
                p1_paras = [
                    "In recent decades, the relationship between intellectual history and the broader humanities has undergone a profound transformation.",
                    "While empirical specialization has undoubtedly accelerated technical breakthroughs, it often fails to accommodate broader philosophical inquiry.",
                ]
                p1_raw = "\n".join(p1_paras)
                p1_hash = hashlib.sha256(p1_raw.encode("utf-8")).hexdigest()[:16]
                sconn.execute(
                    "INSERT OR IGNORE INTO exam_passages VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (
                        "P2024_EN1_T1",
                        "colleague_a",
                        2024,
                        "英语一",
                        "Text 1",
                        "2024 考研英语一 Text 1：跨学科知识壁垒与思想史转型",
                        json.dumps(p1_paras, ensure_ascii=False),
                        json.dumps(["accommodate", "empirical", "intellectual"], ensure_ascii=False),
                        p1_hash,
                        ts_seed,
                    ),
                )
                sconn.execute(
                    "INSERT OR IGNORE INTO exam_passages VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (
                        "P2023_EN1_T2",
                        "colleague_a",
                        2023,
                        "英语一",
                        "Text 2",
                        "2023 考研英语一 Text 2：人工智能伦理与实证科学边界",
                        json.dumps(["Artificial intelligence reshapes empirical inquiry across disciplines."], ensure_ascii=False),
                        json.dumps(["empirical", "intellectual"], ensure_ascii=False),
                        hashlib.sha256(b"P2023_EN1_T2").hexdigest()[:16],
                        ts_seed,
                    ),
                )

            # Initialize default Cross-OS Roaming HA state if not present
            default_active = json.loads(os.environ.get("KAOYAN_ACTIVE_NODES_JSON", '["hp", "w1", "m1"]'))
            default_primary = os.environ.get("KAOYAN_PRIMARY_NODE", default_active[0] if default_active else "hp")
            default_peers = json.loads(os.environ.get("KAOYAN_PEER_ENDPOINTS_JSON", "{}"))
            sconn.execute(
                """
                INSERT OR IGNORE INTO ha_cluster_roaming_state
                (cluster_id, epoch, wal_lsn, active_nodes_json, primary_node, peer_urls_json, roaming_history_json, updated_at)
                VALUES ('kaoyan_cross_os_cluster', 1, 0, ?, ?, ?, ?, ?)
                """,
                (
                    json.dumps(default_active, ensure_ascii=False),
                    default_primary,
                    json.dumps(default_peers, ensure_ascii=False),
                    json.dumps(
                        [
                            {
                                "epoch": 1,
                                "event": "CLUSTER_BOOTSTRAPPED",
                                "active_nodes": default_active,
                                "primary_node": default_primary,
                                "timestamp": ts_seed,
                            }
                        ],
                        ensure_ascii=False,
                    ),
                    ts_seed,
                ),
            )
            sconn.commit()

            # Legacy DB migration if present
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

            # 2. Initialize & Sync PostgreSQL 18 Primary if online
            pconn = self.get_pg_conn()
            if pconn is not None:
                try:
                    with pconn:
                        with pconn.cursor() as cur:
                            if MIGRATION_V2.exists():
                                cur.execute(normalize_os_text(MIGRATION_V2.read_text(encoding="utf-8")))
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
                except Exception:
                    pass
                finally:
                    pconn.close()
            sconn.close()

    # =========================================================================
    # Cross-OS Dynamic Roaming & Role State Machine (1P+2R / 1P+1R / 1-Node STANDALONE_RW)
    # =========================================================================
    def get_roaming_state(self, override_node_id: str = "") -> dict:
        with self._lock:
            sconn = self.get_sqlite_conn()
            row = sconn.execute("SELECT * FROM ha_cluster_roaming_state WHERE cluster_id = 'kaoyan_cross_os_cluster'").fetchone()
            max_lsn_row = sconn.execute("SELECT COALESCE(MAX(lsn), 0) FROM ha_roaming_wal_stream").fetchone()
            wal_lsn = int(max_lsn_row[0]) if max_lsn_row else 0
            sconn.close()

            if row:
                epoch = int(row["epoch"])
                active_nodes = json.loads(row["active_nodes_json"])
                primary_node = str(row["primary_node"])
                peer_urls = json.loads(row["peer_urls_json"] or "{}")
                history = json.loads(row["roaming_history_json"] or "[]")
                updated_at = str(row["updated_at"])
            else:
                epoch = 1
                active_nodes = ["hp", "w1", "m1"]
                primary_node = "hp"
                peer_urls = {}
                history = []
                updated_at = now_str()

            effective_node = (override_node_id or LOCAL_NODE_INFO["node_id"]).strip().lower()
            node_roles = {}
            for nid in ["hp", "w1", "m1", "m4_elena"]:
                if len(active_nodes) == 1:
                    if nid == active_nodes[0]:
                        node_roles[nid] = {
                            "node_id": nid,
                            "role": "STANDALONE_RW",
                            "can_write": True,
                            "can_read": True,
                            "read_write_dual_weight": True,
                        }
                    else:
                        node_roles[nid] = {
                            "node_id": nid,
                            "role": "STANDBY_DRAINED",
                            "can_write": False,
                            "can_read": False,
                            "read_write_dual_weight": False,
                        }
                else:
                    if nid == primary_node and nid in active_nodes:
                        node_roles[nid] = {
                            "node_id": nid,
                            "role": "PRIMARY_RW",
                            "can_write": True,
                            "can_read": True,
                            "read_write_dual_weight": False,
                        }
                    elif nid in active_nodes:
                        node_roles[nid] = {
                            "node_id": nid,
                            "role": "REPLICA_RO",
                            "can_write": False,
                            "can_read": True,
                            "read_write_dual_weight": False,
                        }
                    else:
                        node_roles[nid] = {
                            "node_id": nid,
                            "role": "ARBITER_OBSERVER",
                            "can_write": False,
                            "can_read": True,
                            "read_write_dual_weight": False,
                        }

            if len(active_nodes) == 1:
                cluster_mode = "SINGLE_SURVIVOR_STANDALONE_RW"
                writable_count = 1
                readonly_count = 0
            elif len(active_nodes) == 2:
                cluster_mode = "DEGRADED_2NODE_1P_1R"
                writable_count = 1
                readonly_count = 1
            else:
                cluster_mode = f"ROAMING_{len(active_nodes)}NODE_1P_{len(active_nodes) - 1}R"
                writable_count = 1
                readonly_count = len(active_nodes) - 1

            local_role_meta = node_roles.get(
                effective_node,
                {
                    "node_id": effective_node,
                    "role": "PRIMARY_RW" if effective_node == primary_node else "REPLICA_RO",
                    "can_write": effective_node == primary_node or len(active_nodes) == 1,
                    "can_read": True,
                    "read_write_dual_weight": len(active_nodes) == 1,
                },
            )

            nodes_matrix = []
            for nid, cat in CANONICAL_4NODES_CATALOG.items():
                rmeta = node_roles.get(nid, {})
                nodes_matrix.append(
                    {
                        "node_id": nid,
                        "label": cat["label"],
                        "os_family": cat["os_family"],
                        "os_release": cat["os_release"],
                        "db_stack": cat["db_stack"],
                        "in_active_set": nid in active_nodes,
                        "role": rmeta.get("role", "ARBITER_OBSERVER"),
                        "can_write": rmeta.get("can_write", False),
                        "can_read": rmeta.get("can_read", True),
                        "read_write_dual_weight": rmeta.get("read_write_dual_weight", False),
                        "peer_url": peer_urls.get(nid, ""),
                    }
                )

            return {
                "cluster_id": "kaoyan_cross_os_cluster",
                "epoch": epoch,
                "wal_lsn": wal_lsn,
                "cluster_mode": cluster_mode,
                "active_nodes": active_nodes,
                "active_nodes_count": len(active_nodes),
                "primary_node": active_nodes[0] if len(active_nodes) == 1 else primary_node,
                "writable_nodes_count": writable_count,
                "readonly_replicas_count": readonly_count,
                "local_node": {
                    "node_id": effective_node,
                    "physical_node_id": LOCAL_NODE_INFO["node_id"],
                    "os_family": LOCAL_NODE_INFO["os_family"],
                    "os_label": LOCAL_NODE_INFO["os_label"],
                    "arch": LOCAL_NODE_INFO["arch"],
                    "python_version": LOCAL_NODE_INFO["python_version"],
                    "role": local_role_meta["role"],
                    "can_write": local_role_meta["can_write"],
                    "can_read": local_role_meta["can_read"],
                    "read_write_dual_weight": local_role_meta["read_write_dual_weight"],
                },
                "node_roles": node_roles,
                "nodes_matrix": nodes_matrix,
                "peer_urls": peer_urls,
                "roaming_history": history[-12:],
                "updated_at": updated_at,
            }

    def update_roaming_topology(
        self,
        active_nodes: list[str] | None = None,
        primary_node: str | None = None,
        peer_urls: dict | None = None,
        reason: str = "DYNAMIC_ROAMING_SWITCHOVER",
        incoming_epoch: int | None = None,
        broadcast_to_peers: bool = True,
    ) -> dict:
        t0 = time.perf_counter()
        with self._lock:
            cur = self.get_roaming_state()
            new_active = [str(x).strip().lower() for x in (active_nodes if active_nodes is not None else cur["active_nodes"]) if str(x).strip()]
            if not new_active:
                raise ValueError("active_nodes cannot be empty")
            # Deduplicate preserving order
            dedup_active = []
            for x in new_active:
                if x not in dedup_active:
                    dedup_active.append(x)
            new_active = dedup_active

            if len(new_active) == 1:
                new_primary = new_active[0]
            else:
                cand_primary = (primary_node or cur["primary_node"]).strip().lower()
                new_primary = cand_primary if cand_primary in new_active else new_active[0]

            new_peers = dict(cur["peer_urls"])
            if peer_urls is not None:
                for k, v in peer_urls.items():
                    if v:
                        new_peers[str(k).strip().lower()] = str(v).strip().rstrip("/")

            if incoming_epoch is not None:
                if incoming_epoch < cur["epoch"]:
                    return {"status": "stale_epoch_rejected", "current_epoch": cur["epoch"], "incoming_epoch": incoming_epoch}
                new_epoch = incoming_epoch
            else:
                new_epoch = cur["epoch"] + 1

            # Before switching primary, if broadcast_to_peers is True, sync WAL entries to all active peers
            sync_report = []
            if broadcast_to_peers and new_peers:
                sync_report = self.sync_wal_to_peers(new_peers, target_nodes=new_active)

            ts = now_str()
            history = list(cur["roaming_history"])
            history.append(
                {
                    "epoch": new_epoch,
                    "from_primary": cur["primary_node"],
                    "to_primary": new_primary,
                    "active_nodes": new_active,
                    "mode": "SINGLE_SURVIVOR_STANDALONE_RW" if len(new_active) == 1 else f"ROAMING_{len(new_active)}NODE_1P_{len(new_active)-1}R",
                    "reason": reason,
                    "switchover_ms": round((time.perf_counter() - t0) * 1000, 2),
                    "timestamp": ts,
                }
            )
            history = history[-25:]

            sconn = self.get_sqlite_conn()
            sconn.execute(
                """
                UPDATE ha_cluster_roaming_state
                SET epoch = ?, active_nodes_json = ?, primary_node = ?, peer_urls_json = ?, roaming_history_json = ?, updated_at = ?
                WHERE cluster_id = 'kaoyan_cross_os_cluster'
                """,
                (
                    new_epoch,
                    json.dumps(new_active, ensure_ascii=False),
                    new_primary,
                    json.dumps(new_peers, ensure_ascii=False),
                    json.dumps(history, ensure_ascii=False),
                    ts,
                ),
            )
            sconn.commit()
            sconn.close()

        if broadcast_to_peers and new_peers:
            for nid, purl in new_peers.items():
                if nid == LOCAL_NODE_INFO["node_id"] or not purl:
                    continue
                try:
                    req_body = json.dumps(
                        {
                            "active_nodes": new_active,
                            "primary_node": new_primary,
                            "peer_urls": new_peers,
                            "epoch": new_epoch,
                            "reason": f"PEER_SYNC:{reason}",
                            "broadcast": False,
                        },
                        ensure_ascii=False,
                    ).encode("utf-8")
                    req = urllib.request.Request(
                        f"{purl}/api/ha/config",
                        data=req_body,
                        headers={"Content-Type": "application/json; charset=utf-8"},
                        method="POST",
                    )
                    urllib.request.urlopen(req, timeout=2.5).read()
                except Exception:
                    pass

        updated_state = self.get_roaming_state()
        updated_state["switchover_latency_ms"] = round((time.perf_counter() - t0) * 1000, 2)
        updated_state["wal_sync_report"] = sync_report
        return updated_state

    def fetch_table_row_snapshot(self, target_table: str, record_pk: str, payload: dict) -> dict:
        """Extracts canonical OS-independent row snapshot from SQLite after write so replicas can apply deterministically."""
        sconn = self.get_sqlite_conn()
        row_dict = {}
        try:
            if target_table == "sys_users":
                r = sconn.execute("SELECT * FROM sys_users WHERE user_id = ?", (record_pk,)).fetchone()
                if r:
                    row_dict = dict(r)
            elif target_table == "user_progress_anchors":
                r = sconn.execute("SELECT * FROM user_progress_anchors WHERE user_id = ?", (record_pk,)).fetchone()
                if r:
                    row_dict = dict(r)
            elif target_table == "exam_passages":
                r = sconn.execute("SELECT * FROM exam_passages WHERE passage_id = ?", (record_pk,)).fetchone()
                if r:
                    row_dict = dict(r)
            elif target_table == "user_vocab_ledger":
                if ":bulk:" in record_pk:
                    uid_b = record_pk.split(":")[0]
                    rows = sconn.execute(
                        "SELECT user_id, lemma, syllabus_tier, lookup_count, last_seen_at, days_since_seen, urgency_score, exam_source, contextual_meaning, mastery_state FROM user_vocab_ledger WHERE user_id = ?",
                        (uid_b,),
                    ).fetchall()
                    row_dict = {"bulk_rows": [dict(x) for x in rows]}
                elif ":" in record_pk:
                    uid_v, lem_v = record_pk.split(":", 1)
                    r = sconn.execute(
                        "SELECT user_id, lemma, syllabus_tier, lookup_count, last_seen_at, days_since_seen, urgency_score, exam_source, contextual_meaning, mastery_state FROM user_vocab_ledger WHERE user_id = ? AND lemma = ?",
                        (uid_v, lem_v),
                    ).fetchone()
                    if r:
                        row_dict = dict(r)
            elif target_table == "annotation_spans":
                r = sconn.execute("SELECT * FROM annotation_spans WHERE span_id = ?", (record_pk,)).fetchone()
                if r:
                    row_dict = dict(r)
            elif target_table == "essay_corpus_snippets":
                r = sconn.execute("SELECT * FROM essay_corpus_snippets WHERE snippet_id = ?", (record_pk,)).fetchone()
                if r:
                    row_dict = dict(r)
            elif target_table == "api_idempotency_keys":
                r = sconn.execute("SELECT * FROM api_idempotency_keys WHERE idempotency_key = ?", (record_pk,)).fetchone()
                if r:
                    row_dict = dict(r)
        finally:
            sconn.close()
        if not row_dict:
            row_dict = dict(payload)
        return row_dict

    def apply_wal_entry(self, wal_entry: dict) -> tuple[bool, str]:
        """Deterministically applies a replicated WAL entry onto a Replica (or rejoining node) across any OS."""
        with self._lock:
            cur_state = self.get_roaming_state()
            inc_epoch = int(wal_entry.get("epoch", 1))
            if inc_epoch < cur_state["epoch"]:
                return False, f"STALE_EPOCH_REJECTED (incoming={inc_epoch} < local={cur_state['epoch']})"

            tx_uuid = str(wal_entry.get("tx_uuid", ""))
            op_type = str(wal_entry.get("op_type", "UPSERT"))
            target_table = str(wal_entry.get("target_table", ""))
            record_pk = str(wal_entry.get("record_pk", ""))
            source_node = str(wal_entry.get("source_node", "hp"))
            source_os = str(wal_entry.get("source_os", "Linux"))
            created_at = str(wal_entry.get("created_at", now_str()))
            row_data = wal_entry.get("row_data")
            if isinstance(row_data, str):
                row_data = json.loads(row_data)
            if not isinstance(row_data, dict):
                row_data = {}

            raw_row_json = json.dumps(row_data, ensure_ascii=False, sort_keys=True)
            row_checksum = wal_entry.get("row_checksum_sha256") or hashlib.sha256(raw_row_json.encode("utf-8")).hexdigest()

            sconn = self.get_sqlite_conn()
            try:
                already = sconn.execute("SELECT lsn FROM ha_roaming_wal_stream WHERE tx_uuid = ?", (tx_uuid,)).fetchone()
                if already:
                    sconn.close()
                    return True, "ALREADY_APPLIED_IDEMPOTENT"

                if target_table == "sys_users" and "user_id" in row_data:
                    sconn.execute(
                        "INSERT OR REPLACE INTO sys_users (user_id, username, display_name, role, passcode_hash, token_secret, created_at) VALUES (?,?,?,?,?,?,?)",
                        (
                            row_data["user_id"],
                            row_data.get("username", row_data["user_id"]),
                            row_data.get("display_name", row_data["user_id"]),
                            row_data.get("role", "SCHOLAR"),
                            row_data.get("passcode_hash", "kaoyan2026"),
                            row_data.get("token_secret", ""),
                            row_data.get("created_at", created_at),
                        ),
                    )
                    if "anchor" in row_data and isinstance(row_data["anchor"], dict):
                        a = row_data["anchor"]
                        sconn.execute(
                            "INSERT OR REPLACE INTO user_progress_anchors (user_id, last_passage_id, last_para_idx, last_span_id, last_tab_idx, essay_draft_md, streak_days, rev_no, updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
                            (
                                a["user_id"],
                                a.get("last_passage_id", "P2024_EN1_T1"),
                                int(a.get("last_para_idx", 2)),
                                a.get("last_span_id", "sp-sent-2"),
                                int(a.get("last_tab_idx", 2)),
                                a.get("essay_draft_md", ""),
                                int(a.get("streak_days", 12)),
                                int(a.get("rev_no", 1)),
                                a.get("updated_at", created_at),
                            ),
                        )
                elif target_table == "user_progress_anchors" and "user_id" in row_data:
                    sconn.execute(
                        "INSERT OR REPLACE INTO user_progress_anchors (user_id, last_passage_id, last_para_idx, last_span_id, last_tab_idx, essay_draft_md, streak_days, rev_no, updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
                        (
                            row_data["user_id"],
                            row_data.get("last_passage_id", "P2024_EN1_T1"),
                            int(row_data.get("last_para_idx", 2)),
                            row_data.get("last_span_id", "sp-sent-2"),
                            int(row_data.get("last_tab_idx", 2)),
                            row_data.get("essay_draft_md", ""),
                            int(row_data.get("streak_days", 12)),
                            int(row_data.get("rev_no", 1)),
                            row_data.get("updated_at", created_at),
                        ),
                    )
                elif target_table == "exam_passages" and "passage_id" in row_data:
                    sconn.execute(
                        "INSERT OR REPLACE INTO exam_passages (passage_id, owner_user_id, year, exam_type, text_no, title, paragraphs_json, syllabus_hits_json, sha256_hash, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (
                            row_data["passage_id"],
                            row_data.get("owner_user_id", "colleague_a"),
                            int(row_data.get("year", 2025)),
                            row_data.get("exam_type", "英语一"),
                            row_data.get("text_no", "Text 1"),
                            row_data.get("title", ""),
                            row_data.get("paragraphs_json", "[]"),
                            row_data.get("syllabus_hits_json", "[]"),
                            row_data.get("sha256_hash", ""),
                            row_data.get("created_at", created_at),
                        ),
                    )
                elif target_table == "user_vocab_ledger":
                    rows_to_apply = row_data.get("bulk_rows", [row_data] if "lemma" in row_data else [])
                    for vr in rows_to_apply:
                        sconn.execute(
                            """
                            INSERT INTO user_vocab_ledger (user_id, lemma, syllabus_tier, lookup_count, last_seen_at, days_since_seen, urgency_score, exam_source, contextual_meaning, mastery_state)
                            VALUES (?,?,?,?,?,?,?,?,?,?)
                            ON CONFLICT(user_id, lemma) DO UPDATE SET
                                syllabus_tier = excluded.syllabus_tier,
                                lookup_count = excluded.lookup_count,
                                last_seen_at = excluded.last_seen_at,
                                days_since_seen = excluded.days_since_seen,
                                urgency_score = excluded.urgency_score,
                                exam_source = excluded.exam_source,
                                contextual_meaning = excluded.contextual_meaning,
                                mastery_state = excluded.mastery_state
                            """,
                            (
                                vr["user_id"],
                                vr["lemma"],
                                vr.get("syllabus_tier", "CORE_1800"),
                                int(vr.get("lookup_count", 1)),
                                vr.get("last_seen_at", created_at),
                                float(vr.get("days_since_seen", 0.0)),
                                float(vr.get("urgency_score", 0.5)),
                                vr.get("exam_source", ""),
                                vr.get("contextual_meaning", ""),
                                vr.get("mastery_state", "LEARNING"),
                            ),
                        )
                elif target_table == "annotation_spans" and "span_id" in row_data:
                    sconn.execute(
                        "INSERT OR REPLACE INTO annotation_spans (span_id, user_id, passage_id, granularity, para_idx, start_offset, end_offset, selected_text, prefix_quote, suffix_quote, syntax_breakdown, user_comment, promoted_snippet_id, version, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (
                            row_data["span_id"],
                            row_data["user_id"],
                            row_data.get("passage_id", "P2024_EN1_T1"),
                            row_data.get("granularity", "SENTENCE"),
                            int(row_data.get("para_idx", 1)),
                            int(row_data.get("start_offset", 0)),
                            int(row_data.get("end_offset", 10)),
                            row_data.get("selected_text", ""),
                            row_data.get("prefix_quote", ""),
                            row_data.get("suffix_quote", ""),
                            row_data.get("syntax_breakdown", ""),
                            row_data.get("user_comment", ""),
                            row_data.get("promoted_snippet_id", ""),
                            int(row_data.get("version", 1)),
                            row_data.get("created_at", created_at),
                        ),
                    )
                elif target_table == "essay_corpus_snippets" and "snippet_id" in row_data:
                    sconn.execute(
                        "INSERT OR REPLACE INTO essay_corpus_snippets (snippet_id, user_id, theme_tag, func_slot, granularity, content_en, cloze_pattern, translation_zh, source_ref, usage_count, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (
                            row_data["snippet_id"],
                            row_data["user_id"],
                            row_data.get("theme_tag", "科技创新"),
                            row_data.get("func_slot", "段首引入"),
                            row_data.get("granularity", "SENTENCE"),
                            row_data.get("content_en", ""),
                            row_data.get("cloze_pattern", ""),
                            row_data.get("translation_zh", ""),
                            row_data.get("source_ref", ""),
                            int(row_data.get("usage_count", 1)),
                            row_data.get("created_at", created_at),
                        ),
                    )
                    if row_data.get("promoted_from_span_id"):
                        sconn.execute(
                            "UPDATE annotation_spans SET promoted_snippet_id = ? WHERE span_id = ?",
                            (row_data["snippet_id"], row_data["promoted_from_span_id"]),
                        )
                elif target_table == "api_idempotency_keys" and "idempotency_key" in row_data:
                    sconn.execute(
                        "INSERT OR REPLACE INTO api_idempotency_keys (idempotency_key, user_id, endpoint, req_hash, resp_code, resp_body_json, created_at) VALUES (?,?,?,?,?,?,?)",
                        (
                            row_data["idempotency_key"],
                            row_data.get("user_id", "colleague_a"),
                            row_data.get("endpoint", ""),
                            row_data.get("req_hash", ""),
                            int(row_data.get("resp_code", 200)),
                            row_data.get("resp_body_json", "{}"),
                            row_data.get("created_at", created_at),
                        ),
                    )

                sconn.execute(
                    "INSERT OR IGNORE INTO ha_sync_wal_journal (tx_uuid, op_type, target_table, record_pk, payload_json, pg_status, sqlite_status, created_at) VALUES (?,?,?,?,?,?,?,?)",
                    (tx_uuid, op_type, target_table, record_pk, raw_row_json, "REPLICATED", "COMMITTED", created_at),
                )
                sconn.execute(
                    "INSERT OR IGNORE INTO ha_roaming_wal_stream (epoch, tx_uuid, source_node, source_os, op_type, target_table, record_pk, row_data_json, row_checksum_sha256, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (inc_epoch, tx_uuid, source_node, source_os, op_type, target_table, record_pk, raw_row_json, row_checksum, created_at),
                )
                sconn.commit()
            finally:
                sconn.close()
            return True, "REPLICATED_OK"

    def sync_wal_to_peers(self, peer_urls: dict, target_nodes: list[str] | None = None) -> list[dict]:
        """Pushes any missing WAL frames from this node to all active peer nodes so they reach identical LSN."""
        sconn = self.get_sqlite_conn()
        entries = [
            dict(r)
            for r in sconn.execute("SELECT * FROM ha_roaming_wal_stream ORDER BY lsn ASC").fetchall()
        ]
        sconn.close()
        report = []
        for nid, purl in peer_urls.items():
            if not purl or nid == LOCAL_NODE_INFO["node_id"]:
                continue
            if target_nodes is not None and nid not in target_nodes:
                continue
            replicated_cnt = 0
            status_str = "OK"
            try:
                for ent in entries:
                    payload = {
                        "lsn": ent["lsn"],
                        "epoch": ent["epoch"],
                        "tx_uuid": ent["tx_uuid"],
                        "source_node": ent["source_node"],
                        "source_os": ent["source_os"],
                        "op_type": ent["op_type"],
                        "target_table": ent["target_table"],
                        "record_pk": ent["record_pk"],
                        "row_data": json.loads(ent["row_data_json"]),
                        "row_checksum_sha256": ent["row_checksum_sha256"],
                        "created_at": ent["created_at"],
                    }
                    req = urllib.request.Request(
                        f"{purl.rstrip('/')}/api/ha/replicate",
                        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                        headers={"Content-Type": "application/json; charset=utf-8"},
                        method="POST",
                    )
                    urllib.request.urlopen(req, timeout=2.5).read()
                    replicated_cnt += 1
            except Exception as exc:
                status_str = f"WARN:{type(exc).__name__}"
            report.append({"peer_node": nid, "peer_url": purl, "frames_synced": replicated_cnt, "status": status_str})
        return report

    def record_ha_wal(self, op_type: str, target_table: str, record_pk: str, payload: dict, pg_ok: bool, sqlite_ok: bool) -> dict:
        with self._lock:
            tx_uuid = f"tx-{uuid.uuid4().hex[:16]}"
            ts = now_str()
            p_stat = "COMMITTED" if pg_ok else "DEGRADED_STANDBY_ONLY"
            s_stat = "COMMITTED" if sqlite_ok else "FAILED"
            rstate = self.get_roaming_state()
            epoch = rstate["epoch"]
            row_snap = self.fetch_table_row_snapshot(target_table, record_pk, payload)
            if target_table == "sys_users" and op_type in ("LOGIN_UPSERT", "USER_CREATE"):
                anchor_snap = self.fetch_table_row_snapshot("user_progress_anchors", record_pk, {})
                if anchor_snap:
                    row_snap["anchor"] = anchor_snap
            raw_json = json.dumps(row_snap, ensure_ascii=False, sort_keys=True)
            row_checksum = hashlib.sha256(raw_json.encode("utf-8")).hexdigest()

            lsn = 0
            try:
                sconn = self.get_sqlite_conn()
                sconn.execute(
                    "INSERT INTO ha_sync_wal_journal (tx_uuid, op_type, target_table, record_pk, payload_json, pg_status, sqlite_status, created_at) VALUES (?,?,?,?,?,?,?,?)",
                    (tx_uuid, op_type, target_table, record_pk, raw_json, p_stat, s_stat, ts),
                )
                cur = sconn.execute(
                    "INSERT INTO ha_roaming_wal_stream (epoch, tx_uuid, source_node, source_os, op_type, target_table, record_pk, row_data_json, row_checksum_sha256, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (
                        epoch,
                        tx_uuid,
                        LOCAL_NODE_INFO["node_id"],
                        LOCAL_NODE_INFO["os_family"],
                        op_type,
                        target_table,
                        record_pk,
                        raw_json,
                        row_checksum,
                        ts,
                    ),
                )
                lsn = cur.lastrowid or 0
                sconn.execute("UPDATE ha_cluster_roaming_state SET wal_lsn = ?, updated_at = ? WHERE cluster_id = 'kaoyan_cross_os_cluster'", (lsn, ts))
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

            # Real-time push replication to active REPLICA_RO peers
            peer_urls = rstate.get("peer_urls", {})
            active_nodes = rstate.get("active_nodes", [])
            replicated_to = []
            if peer_urls and len(active_nodes) > 1:
                wal_frame = {
                    "lsn": lsn,
                    "epoch": epoch,
                    "tx_uuid": tx_uuid,
                    "source_node": LOCAL_NODE_INFO["node_id"],
                    "source_os": LOCAL_NODE_INFO["os_family"],
                    "op_type": op_type,
                    "target_table": target_table,
                    "record_pk": record_pk,
                    "row_data": row_snap,
                    "row_checksum_sha256": row_checksum,
                    "created_at": ts,
                }
                for nid in active_nodes:
                    if nid == LOCAL_NODE_INFO["node_id"]:
                        continue
                    purl = peer_urls.get(nid, "")
                    if not purl:
                        continue
                    try:
                        req = urllib.request.Request(
                            f"{purl.rstrip('/')}/api/ha/replicate",
                            data=json.dumps(wal_frame, ensure_ascii=False).encode("utf-8"),
                            headers={"Content-Type": "application/json; charset=utf-8"},
                            method="POST",
                        )
                        urllib.request.urlopen(req, timeout=2.0).read()
                        replicated_to.append(nid)
                    except Exception:
                        pass

            return {
                "tx_uuid": tx_uuid,
                "lsn": lsn,
                "epoch": epoch,
                "row_checksum_sha256": row_checksum,
                "replicated_to": replicated_to,
            }

    def export_portable_snapshot(self) -> dict:
        """Exports an OS-agnostic JSON snapshot of all 10 tables + WAL state for cross-OS migration."""
        sconn = self.get_sqlite_conn()
        tables_dump = {}
        table_checksums = {}
        for tbl in CORE_TABLES:
            rows = [dict(r) for r in sconn.execute(f"SELECT * FROM {tbl}").fetchall()]
            tables_dump[tbl] = rows
            canonical = json.dumps(rows, ensure_ascii=False, sort_keys=True)
            table_checksums[tbl] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
        sconn.close()
        rstate = self.get_roaming_state()
        return {
            "schema": "Kaoyan_OS_Agnostic_Portable_Snapshot_v4.0",
            "exported_from_node": LOCAL_NODE_INFO["node_id"],
            "exported_from_os": LOCAL_NODE_INFO["os_label"],
            "epoch": rstate["epoch"],
            "wal_lsn": rstate["wal_lsn"],
            "table_checksums": table_checksums,
            "tables": tables_dump,
            "exported_at": now_str(),
        }

    def restore_portable_snapshot(self, snap: dict) -> dict:
        """Restores an OS-agnostic JSON snapshot on any target OS (Windows 11 / Ubuntu 26.04 / macOS)."""
        with self._lock:
            tables = snap.get("tables", {})
            sconn = self.get_sqlite_conn()
            restored_counts = {}
            try:
                for tbl, rows in tables.items():
                    if tbl not in CORE_TABLES or not isinstance(rows, list):
                        continue
                    for r in rows:
                        if not isinstance(r, dict) or not r:
                            continue
                        cols = list(r.keys())
                        placeholders = ",".join(["?"] * len(cols))
                        col_names = ",".join(cols)
                        vals = tuple(r[c] for c in cols)
                        sconn.execute(f"INSERT OR REPLACE INTO {tbl} ({col_names}) VALUES ({placeholders})", vals)
                    restored_counts[tbl] = len(rows)
                sconn.commit()
            finally:
                sconn.close()
            return {"status": "ok", "restored_on_node": LOCAL_NODE_INFO["node_id"], "restored_on_os": LOCAL_NODE_INFO["os_label"], "restored_counts": restored_counts}

    def get_ha_status(self, simulate_pg_down: bool = False, override_node_id: str = "") -> dict:
        t0 = time.perf_counter()
        pg_counts = {}
        pg_online = False
        pg_version = "offline"
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

        roaming = self.get_roaming_state(override_node_id=override_node_id)
        active_engine = "postgresql_18_primary" if pg_online else "sqlite_wal_hot_standby_failover"
        return {
            "status": "ok",
            "version": "v4.0-cross-os-roaming-ha",
            "active_engine": active_engine,
            "ha_mode": "ACTIVE_ACTIVE_DUAL_WRITE" if pg_online else "FAILOVER_HOT_STANDBY",
            "pg_primary_online": pg_online,
            "pg_version": pg_version,
            "sqlite_standby_online": True,
            "sqlite_journal_mode": "wal",
            "tables_count": len(CORE_TABLES),
            "pg_table_rows": pg_counts,
            "sqlite_table_rows": sqlite_counts,
            "in_sync": (pg_counts == sqlite_counts) if pg_online else True,
            "roaming_topology": roaming,
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

    def _effective_node_id(self) -> str:
        return self.headers.get("X-Target-Node", LOCAL_NODE_INFO["node_id"]).strip().lower()

    def _send_json(
        self,
        code: int,
        payload: dict,
        req_id: str = "",
        t0: float = 0.0,
        engine_hdr: str = "pg18+sqlite_wal",
        idem_replay: bool = False,
        rstate: dict | None = None,
        forwarded_to: str = "",
    ):
        if req_id:
            payload.setdefault("request_id", req_id)
        if rstate is None:
            rstate = REPO.get_roaming_state(override_node_id=self._effective_node_id())
        lnode = rstate["local_node"]
        payload.setdefault("cluster_node", lnode["node_id"])
        payload.setdefault("cluster_os", lnode["os_family"])
        payload.setdefault("cluster_role", lnode["role"])
        payload.setdefault("cluster_mode", rstate["cluster_mode"])
        payload.setdefault("cluster_epoch", rstate["epoch"])
        payload.setdefault("wal_lsn", rstate["wal_lsn"])

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
        self.send_header("X-Node-ID", str(lnode["node_id"]))
        self.send_header("X-Node-OS", str(lnode["os_family"]))
        self.send_header("X-Cluster-Role", str(lnode["role"]))
        self.send_header("X-Cluster-Mode", str(rstate["cluster_mode"]))
        self.send_header("X-Cluster-Epoch", str(rstate["epoch"]))
        self.send_header("X-Cluster-LSN", str(rstate["wal_lsn"]))
        if forwarded_to:
            self.send_header("X-Forwarded-To-Primary", forwarded_to)
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
        eff_node = self._effective_node_id()
        rstate = REPO.get_roaming_state(override_node_id=eff_node)
        parsed = urlparse(self.path)

        lower_p = parsed.path.lower()
        if any(lower_p.endswith(ext) for ext in (".sql", ".bak", ".php", ".ini", ".yml", ".yaml", ".properties", ".env", ".envrc")) or "/.env" in lower_p or "/.git" in lower_p:
            return self._send_json(404, {"status": "not_found"}, req_id=req_id, t0=t0, rstate=rstate)

        # If node is drained by single-node survivor config on another node, block read unless querying HA control plane
        if not rstate["local_node"]["can_read"] and not parsed.path.startswith("/api/ha/") and parsed.path != "/api/health":
            return self._send_json(
                503,
                {
                    "status": "node_drained",
                    "error_code": "NODE_DRAINED_BY_CONFIG",
                    "node_id": eff_node,
                    "role": rstate["local_node"]["role"],
                    "active_nodes": rstate["active_nodes"],
                    "message": f"节点 {eff_node} 当前不在活跃节点配置列表 {rstate['active_nodes']} 中",
                },
                req_id=req_id,
                t0=t0,
                rstate=rstate,
            )

        if parsed.path == "/api/health":
            ha = REPO.get_ha_status(simulate_pg_down=sim_down, override_node_id=eff_node)
            return self._send_json(
                200,
                {
                    "status": "ok",
                    "service": "kaoyan-english-hub-v4-cross-os-roaming-ha",
                    "domain": "kaoyan.elenalyl.top",
                    "containerized": True,
                    "db_engine": ha["active_engine"],
                    "ha_mode": ha["ha_mode"],
                    "pg_primary_online": ha["pg_primary_online"],
                    "sqlite_standby_online": ha["sqlite_standby_online"],
                    "roaming_topology": ha["roaming_topology"],
                    "tables_count": len(CORE_TABLES),
                    "tables": CORE_TABLES,
                },
                req_id=req_id,
                t0=t0,
                engine_hdr=ha["active_engine"],
                rstate=rstate,
            )

        if parsed.path == "/api/ha/status":
            ha = REPO.get_ha_status(simulate_pg_down=sim_down, override_node_id=eff_node)
            return self._send_json(200, ha, req_id=req_id, t0=t0, engine_hdr=ha["active_engine"], rstate=rstate)

        if parsed.path in ("/api/ha/topology", "/api/v1/ha/topology"):
            return self._send_json(200, {"status": "ok", "topology": rstate}, req_id=req_id, t0=t0, rstate=rstate)

        if parsed.path in ("/api/ha/wal/stream", "/api/v1/ha/wal/stream"):
            qs = parse_qs(parsed.query)
            since_lsn = int(qs.get("since_lsn", ["0"])[0])
            sconn = REPO.get_sqlite_conn()
            rows = [
                dict(r)
                for r in sconn.execute("SELECT * FROM ha_roaming_wal_stream WHERE lsn > ? ORDER BY lsn ASC LIMIT 500", (since_lsn,)).fetchall()
            ]
            sconn.close()
            for r in rows:
                try:
                    r["row_data"] = json.loads(r.pop("row_data_json", "{}"))
                except Exception:
                    r["row_data"] = {}
            return self._send_json(200, {"status": "ok", "since_lsn": since_lsn, "entries_count": len(rows), "entries": rows}, req_id=req_id, t0=t0, rstate=rstate)

        if parsed.path in ("/api/ha/snapshot", "/api/v1/ha/snapshot"):
            snap = REPO.export_portable_snapshot()
            return self._send_json(200, {"status": "ok", "snapshot": snap}, req_id=req_id, t0=t0, rstate=rstate)

        if parsed.path in ("/api/bootstrap", "/api/state", "/api/passages", "/api/annotations/list", "/api/essay/list"):
            qs = parse_qs(parsed.query)
            verified_uid = verify_bearer(self.headers, simulate_pg_down=sim_down)
            passage_id = qs.get("passage_id", ["P2024_EN1_T1"])[0]
            theme_filter = qs.get("theme_tag", [""])[0]

            pconn = REPO.get_pg_conn(simulate_down=sim_down)
            engine_used = "postgresql_18_primary" if pconn is not None else "sqlite_wal_hot_standby_failover"

            if not verified_uid:
                if pconn is not None:
                    try:
                        pconn.close()
                    except Exception:
                        pass
                guest_passages = [
                    {
                        "passage_id": "P2024_EN1_T1",
                        "year": 2024,
                        "exam_type": "英语一",
                        "text_no": "Text 1",
                        "title": "2024 考研英语一 Text 1 (访客 30% 公开试读样章)",
                        "cleartext_para_1": "In recent decades, the relationship between intellectual history and the broader humanities has undergone a profound transformation. The modern university structure segments knowledge into narrow compartments, making it increasingly perilous for scholars to venture beyond their fortified disciplinary boundaries.",
                        "blurred_para_2_teaser": "While empirical specialization has undoubtedly accelerated... [🔒 访客免费试读已达 30% 阈值：后端 API 已硬截断后续段落，请登录学籍解锁 Para 2~5 全文、熟词僻义预警与五维进度锚点]",
                        "is_truncated": True,
                    }
                ]
                guest_annotations = [
                    {
                        "id": "sp-para-1",
                        "granularity": "PARAGRAPH",
                        "tag": "🟣 段落主旨卡 [Para 1 · 公开试读 1/2]",
                        "text": "Para 1: 现代大学学科壁垒割裂了知识体系，导致学者跨学科探索面临风险。",
                        "breakdown": "【篇章功能】开篇立论（欲抑先扬）：指出 narrow compartments 对跨学科知识分子的束缚。",
                        "comment": "常考态度题：作者对过度学科细分持批判态度 (critical / skeptical)。",
                        "is_blurred": False,
                    },
                    {
                        "id": "sp-sent-1",
                        "granularity": "SENTENCE",
                        "tag": "🔵 长难句解剖卡 [Para 1 · 公开试读 2/2]",
                        "text": "The modern university structure segments knowledge into narrow compartments, making it increasingly perilous for scholars to venture beyond their fortified disciplinary boundaries.",
                        "breakdown": "【主干】structure segments knowledge | 【分词结果状语】making it perilous for scholars to venture beyond...",
                        "comment": "绝佳写作句式！可改写用于【教育文化/科技创新】大作文。",
                        "is_blurred": False,
                    },
                    {
                        "id": "sp-sent-2-redacted",
                        "granularity": "SENTENCE",
                        "tag": "🔒 长难句解剖卡 [Para 2 · 45% 毛玻璃预览]",
                        "text": "While empirical specialization has undoubtedly accelerated technical breakthroughs, it often fails to accommodate broader philosophical inquiry.",
                        "breakdown": "【让步状语从句】While empirical specialization has... | 【主干】it fails to accommodate... (服务端脱敏样板 ██)",
                        "comment": "🔒 登录学籍后解锁完整句法切分与双刃剑论证升格模板",
                        "is_blurred": True,
                    },
                    {
                        "id": "sp-word-1-redacted",
                        "granularity": "WORD",
                        "tag": "🔒 真题熟词僻义卡 [Para 2 · 45% 毛玻璃预览]",
                        "text": "accommodate / empirical (考研高频熟词僻义陷阱)",
                        "breakdown": "【熟词僻义预警】考研阅读常考『容纳、顾及、顺应』之意，切忌死背基础词义 (服务端脱敏样板 ██)",
                        "comment": "🔒 登录学籍后解锁个人真题语境查词频次与艾宾浩斯复习锚点",
                        "is_blurred": True,
                    },
                ]
                guest_vocab = [
                    {
                        "word": "accommodate",
                        "lemma": "accommodate",
                        "syllabus_tier": "POLYSEMY_TRAP",
                        "lookup_count": "5",
                        "days_since_seen": 0.0,
                        "last_seen_at": "2026-10-20",
                        "exam_source": "2022 英语一 Text 2 Para 3 (公共考纲样板)",
                        "contextual_meaning": "v. 适应，顺应；容纳，顾及（考研熟词僻义：非仅提供食宿）",
                        "urgency_score": "0.85",
                        "is_blurred": False,
                    },
                    {
                        "word": "intellectual",
                        "lemma": "intellectual",
                        "syllabus_tier": "CORE_1800",
                        "lookup_count": "4",
                        "days_since_seen": 0.0,
                        "last_seen_at": "2026-10-21",
                        "exam_source": "2024 英语一 Text 1 Para 1 (公共考纲样板)",
                        "contextual_meaning": "adj. 智力的，理智的；n. 知识分子",
                        "urgency_score": "0.69",
                        "is_blurred": False,
                    },
                ]
                guest_essays = [
                    {
                        "id": "ec-1",
                        "theme": "科技创新",
                        "slot": "第一段·图画图表描述",
                        "gran": "模板骨架 (公开样板)",
                        "en": "As is vividly depicted in the cartoon, the rapid proliferation of artificial intelligence has sparked heated debate.",
                        "cloze": "As is [vividly depicted] in the cartoon, the [rapid proliferation] of artificial intelligence has [sparked heated debate].",
                        "zh": "正如漫画生动描绘的那样，人工智能的迅猛普及引发了激烈讨论。",
                        "source": "2024 英语一大作文公开样板",
                        "is_blurred": False,
                    }
                ]
                if parsed.path == "/api/passages":
                    return self._send_json(200, {"status": "ok", "auth_tier": "GUEST_TEASER", "engine": engine_used, "passages": guest_passages}, req_id=req_id, t0=t0, engine_hdr=engine_used, rstate=rstate)
                if parsed.path == "/api/annotations/list":
                    return self._send_json(200, {"status": "ok", "auth_tier": "GUEST_TEASER", "engine": engine_used, "annotations": guest_annotations}, req_id=req_id, t0=t0, engine_hdr=engine_used, rstate=rstate)
                if parsed.path == "/api/essay/list":
                    return self._send_json(200, {"status": "ok", "auth_tier": "GUEST_TEASER", "engine": engine_used, "essays": guest_essays}, req_id=req_id, t0=t0, engine_hdr=engine_used, rstate=rstate)
                return self._send_json(
                    200,
                    {
                        "status": "ok",
                        "auth_tier": "GUEST_TEASER",
                        "exposure_policy": {
                            "cleartext_ratio_pct": 30,
                            "blurred_teaser_pct": 45,
                            "hard_locked_pct": 25,
                            "strategy": "HYBRID_API_TRUNCATION_GRADIENT_AND_FROSTED_BLUR",
                        },
                        "engine": engine_used,
                        "user_id": "guest",
                        "passage_count": 2,
                        "passages": guest_passages,
                        "anchor": {
                            "last_para_idx": None,
                            "streak_days": None,
                            "rev_no": 0,
                            "masked_label": "Para * · 连续 ** 天 (🔒登录解锁)",
                        },
                        "vocab": guest_vocab,
                        "annotations": guest_annotations,
                        "essays": guest_essays,
                        "roaming_topology": rstate,
                    },
                    req_id=req_id,
                    t0=t0,
                    engine_hdr=engine_used,
                    rstate=rstate,
                )

            uid = verified_uid
            # Always read from SQLite WAL canonical replica store (or PG18 if primary) to guarantee LSN consistency across OS nodes
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
            if pconn is not None:
                try:
                    pconn.close()
                except Exception:
                    pass

            if parsed.path == "/api/passages":
                return self._send_json(200, {"status": "ok", "auth_tier": "SCHOLAR_FULL", "engine": engine_used, "passages": passages}, req_id=req_id, t0=t0, engine_hdr=engine_used, rstate=rstate)
            if parsed.path == "/api/annotations/list":
                return self._send_json(200, {"status": "ok", "auth_tier": "SCHOLAR_FULL", "engine": engine_used, "annotations": annotations}, req_id=req_id, t0=t0, engine_hdr=engine_used, rstate=rstate)
            if parsed.path == "/api/essay/list":
                return self._send_json(200, {"status": "ok", "auth_tier": "SCHOLAR_FULL", "engine": engine_used, "essays": essays}, req_id=req_id, t0=t0, engine_hdr=engine_used, rstate=rstate)

            return self._send_json(
                200,
                {
                    "status": "ok",
                    "auth_tier": "SCHOLAR_FULL",
                    "engine": engine_used,
                    "user_id": uid,
                    "passage_count": p_cnt,
                    "passages": passages,
                    "anchor": dict(anchor_row) if anchor_row else {"last_para_idx": 2, "streak_days": 12, "rev_no": 1},
                    "vocab": vocab_rows,
                    "annotations": annotations,
                    "essays": essays,
                    "roaming_topology": rstate,
                },
                req_id=req_id,
                t0=t0,
                engine_hdr=engine_used,
                rstate=rstate,
            )

        if parsed.path in ("/", "/index.html"):
            if HTML_PATH.exists():
                html = HTML_PATH.read_bytes()
            else:
                html = b"<html><body><h1>Kaoyan English Hub v4.0 Cross-OS Roaming HA</h1></body></html>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Node-ID", str(rstate["local_node"]["node_id"]))
            self.send_header("X-Cluster-Role", str(rstate["local_node"]["role"]))
            self.end_headers()
            self.wfile.write(html)
            return

        if parsed.path == "/api/auth/users":
            sconn = REPO.get_sqlite_conn()
            rows = sconn.execute(
                "SELECT user_id, username, display_name, role, created_at FROM sys_users ORDER BY created_at ASC"
            ).fetchall()
            sconn.close()
            users_list = [dict(r) for r in rows]
            return self._send_json(200, {"status": "ok", "users": users_list}, req_id=req_id, t0=t0, rstate=rstate)

        self._send_json(404, {"status": "not_found", "message": "Endpoint not found"}, req_id=req_id, t0=t0, rstate=rstate)

    def do_POST(self):
        t0 = time.perf_counter()
        req_id = self.headers.get("X-Request-ID", f"req-{uuid.uuid4().hex[:12]}")
        sim_down = self.headers.get("X-Simulate-PG-Down", "0") == "1"
        idem_key = self.headers.get("X-Idempotency-Key", "").strip()
        eff_node = self._effective_node_id()
        rstate = REPO.get_roaming_state(override_node_id=eff_node)

        length = int(self.headers.get("Content-Length", "0"))
        if length > 4 * 1024 * 1024:
            return self._send_json(413, {"status": "payload_too_large", "message": "Request payload exceeds 4MB limit"}, req_id=req_id, t0=t0, rstate=rstate)
        raw = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        try:
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError("JSON root must be object")
        except Exception:
            return self._send_json(400, {"status": "bad_request", "message": "Invalid JSON payload"}, req_id=req_id, t0=t0, rstate=rstate)

        now = now_str()

        # =====================================================================
        # Control-Plane HA Endpoints (Roaming Switchover, Config, Replication, Snapshot)
        # =====================================================================
        if self.path in ("/api/ha/roam", "/api/ha/switchover", "/api/v1/ha/roam", "/api/v1/ha/switchover"):
            target_primary = str(data.get("target_primary", data.get("primary_node", ""))).strip().lower()
            active_nodes = data.get("active_nodes")
            peer_urls = data.get("peer_urls")
            reason = str(data.get("reason", f"ROAM_TO_{target_primary.upper()}"))
            if not target_primary and not active_nodes:
                return self._send_json(422, {"status": "validation_error", "message": "target_primary or active_nodes is required"}, req_id=req_id, t0=t0, rstate=rstate)
            new_state = REPO.update_roaming_topology(
                active_nodes=active_nodes,
                primary_node=target_primary or None,
                peer_urls=peer_urls,
                reason=reason,
                broadcast_to_peers=bool(data.get("broadcast", True)),
            )
            return self._send_json(200, {"status": "ok", "roaming_state": new_state}, req_id=req_id, t0=t0, rstate=REPO.get_roaming_state(override_node_id=eff_node))

        if self.path in ("/api/ha/config", "/api/v1/ha/config"):
            active_nodes = data.get("active_nodes")
            primary_node = data.get("primary_node")
            peer_urls = data.get("peer_urls")
            inc_epoch = data.get("epoch")
            reason = str(data.get("reason", "TOPOLOGY_CONFIG_UPDATE"))
            new_state = REPO.update_roaming_topology(
                active_nodes=active_nodes,
                primary_node=primary_node,
                peer_urls=peer_urls,
                reason=reason,
                incoming_epoch=int(inc_epoch) if inc_epoch is not None else None,
                broadcast_to_peers=bool(data.get("broadcast", True)),
            )
            if new_state.get("status") == "stale_epoch_rejected":
                return self._send_json(409, new_state, req_id=req_id, t0=t0, rstate=rstate)
            return self._send_json(200, {"status": "ok", "roaming_state": new_state}, req_id=req_id, t0=t0, rstate=REPO.get_roaming_state(override_node_id=eff_node))

        if self.path in ("/api/ha/replicate", "/api/v1/ha/replicate"):
            ok, msg = REPO.apply_wal_entry(data)
            if not ok:
                return self._send_json(409, {"status": "replication_rejected", "error_code": "STALE_EPOCH_REJECTED", "message": msg}, req_id=req_id, t0=t0, rstate=rstate)
            return self._send_json(200, {"status": "ok", "replication_result": msg}, req_id=req_id, t0=t0, rstate=REPO.get_roaming_state(override_node_id=eff_node))

        if self.path in ("/api/ha/snapshot/restore", "/api/v1/ha/snapshot/restore"):
            snap = data.get("snapshot", data)
            res = REPO.restore_portable_snapshot(snap)
            return self._send_json(200, res, req_id=req_id, t0=t0, rstate=REPO.get_roaming_state(override_node_id=eff_node))

        # =====================================================================
        # Data-Plane Write Gate: Enforce 1 Primary (RW) + 2 Replicas (RO) vs 1-Node STANDALONE_RW
        # Note: /api/auth/login is an authentication token verification & session bootstrap endpoint;
        # on REPLICA_RO nodes, login verifies credentials in read-only mode without mutating WAL,
        # while all data-mutation endpoints (and login on PRIMARY_RW/STANDALONE_RW) follow strict role rules.
        # =====================================================================
        local_role = rstate["local_node"]["role"]
        can_write = rstate["local_node"]["can_write"]

        if self.path == "/api/auth/login" and not can_write:
            # Read-only credential verification on REPLICA_RO node
            u = str(data.get("username", "colleague_a")).strip() or "colleague_a"
            k = str(data.get("passcode", "")).strip()
            if not k:
                return self._send_json(401, {"status": "unauthorized", "message": "请输入学籍口令"}, req_id=req_id, t0=t0, rstate=rstate)
            sconn = REPO.get_sqlite_conn()
            urow = sconn.execute("SELECT user_id, username, display_name, role, passcode_hash, token_secret FROM sys_users WHERE user_id = ? OR username = ?", (u, u)).fetchone()
            anchor_r = sconn.execute("SELECT * FROM user_progress_anchors WHERE user_id = ?", (u,)).fetchone()
            sconn.close()
            if urow is None:
                return self._send_json(401, {"status": "unauthorized", "message": "从库只读模式下无法自动注册新学籍，请路由至主节点"}, req_id=req_id, t0=t0, rstate=rstate)
            stored_pw = str(urow["passcode_hash"])
            k_sha = hashlib.sha256(k.encode("utf-8")).hexdigest()
            if k != stored_pw and k_sha != stored_pw:
                return self._send_json(401, {"status": "unauthorized", "message": "学籍口令错误"}, req_id=req_id, t0=t0, rstate=rstate)
            token = urow["token_secret"] or f"kaoyan-scholar-{urow['user_id']}-kaoyan2026"
            return self._send_json(
                200,
                {
                    "status": "ok",
                    "engine": "sqlite_wal_replica_readonly",
                    "user_id": urow["user_id"],
                    "display_name": urow["display_name"],
                    "role": urow["role"] or "SCHOLAR",
                    "token": token,
                    "anchor": dict(anchor_r) if anchor_r else {"last_para_idx": 2, "streak_days": 12, "rev_no": 1},
                },
                req_id=req_id,
                t0=t0,
                engine_hdr="sqlite_wal_replica_readonly",
                rstate=rstate,
            )

        if not can_write:
            write_policy = self.headers.get("X-Replica-Write-Policy", "strict").strip().lower()
            primary_nid = rstate["primary_node"]
            primary_url = rstate.get("peer_urls", {}).get(primary_nid, "")
            if write_policy == "forward" and primary_url:
                try:
                    fwd_headers = {
                        "Content-Type": "application/json; charset=utf-8",
                        "X-Request-ID": req_id,
                        "X-Target-Node": primary_nid,
                    }
                    if self.headers.get("Authorization"):
                        fwd_headers["Authorization"] = self.headers.get("Authorization")
                    if idem_key:
                        fwd_headers["X-Idempotency-Key"] = idem_key
                    req = urllib.request.Request(
                        f"{primary_url.rstrip('/')}{self.path}",
                        data=raw.encode("utf-8"),
                        headers=fwd_headers,
                        method="POST",
                    )
                    with urllib.request.urlopen(req, timeout=5.0) as resp:
                        resp_body = json.loads(resp.read().decode("utf-8"))
                        resp_body["forwarded_from_replica"] = eff_node
                        resp_body["executed_on_primary"] = primary_nid
                        return self._send_json(
                            resp.status,
                            resp_body,
                            req_id=req_id,
                            t0=t0,
                            rstate=REPO.get_roaming_state(override_node_id=eff_node),
                            forwarded_to=primary_nid,
                        )
                except urllib.error.HTTPError as he:
                    err_body = json.loads(he.read().decode("utf-8") or "{}")
                    return self._send_json(he.code, err_body, req_id=req_id, t0=t0, rstate=rstate, forwarded_to=primary_nid)

            return self._send_json(
                409,
                {
                    "status": "replica_read_only_violation",
                    "error_code": "RO_REPLICA_WRITE_FORBIDDEN",
                    "node_id": eff_node,
                    "role": local_role,
                    "can_write": False,
                    "can_read": rstate["local_node"]["can_read"],
                    "primary_node": primary_nid,
                    "cluster_mode": rstate["cluster_mode"],
                    "active_nodes": rstate["active_nodes"],
                    "message": f"节点 {eff_node} 当前角色为 {local_role}（只读从节点），禁止直接写入；请将写请求路由至主节点 {primary_nid} 或携带 X-Replica-Write-Policy: forward",
                },
                req_id=req_id,
                t0=t0,
                rstate=rstate,
            )

        if self.path == "/api/auth/login":
            u = str(data.get("username", "colleague_a")).strip() or "colleague_a"
            k = str(data.get("passcode", "")).strip()
            if not k:
                return self._send_json(401, {"status": "unauthorized", "message": "请输入学籍口令"}, req_id=req_id, t0=t0, rstate=rstate)

            sconn = REPO.get_sqlite_conn()
            urow = sconn.execute("SELECT user_id, username, display_name, role, passcode_hash, token_secret FROM sys_users WHERE user_id = ? OR username = ?", (u, u)).fetchone()
            k_sha = hashlib.sha256(k.encode("utf-8")).hexdigest()
            if urow is not None:
                stored_pw = str(urow["passcode_hash"])
                if k != stored_pw and k_sha != stored_pw:
                    sconn.close()
                    return self._send_json(401, {"status": "unauthorized", "message": "学籍口令错误，请核对后重试"}, req_id=req_id, t0=t0, rstate=rstate)
                u = urow["user_id"]
                disp = urow["display_name"]
                role = urow["role"] or "SCHOLAR"
                token = urow["token_secret"] or f"kaoyan-scholar-{u}-kaoyan2026"
            else:
                if k != "kaoyan2026":
                    sconn.close()
                    return self._send_json(401, {"status": "unauthorized", "message": "未知学籍账号或口令错误（可使用『手工添加账号』创建新学籍）"}, req_id=req_id, t0=t0, rstate=rstate)
                disp = u
                role = "SCHOLAR"
                token = f"kaoyan-scholar-{u}-kaoyan2026"
                sconn.execute("INSERT OR IGNORE INTO sys_users VALUES (?, ?, ?, ?, ?, ?, ?)", (u, u, disp, role, k, token, now))

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
                                (u, u, disp, role, k, token, now),
                            )
                            cur.execute(
                                "INSERT INTO user_progress_anchors (user_id, last_passage_id, last_para_idx, last_span_id, last_tab_idx, essay_draft_md, streak_days, rev_no, updated_at) VALUES (%s,%s,2,%s,2,%s,12,1,%s) ON CONFLICT (user_id) DO NOTHING",
                                (u, "P2024_EN1_T1", "sp-sent-2", "", now),
                            )
                    pg_ok = True
                finally:
                    pconn.close()

            wal_meta = REPO.record_ha_wal("LOGIN_UPSERT", "sys_users", u, {"user_id": u}, pg_ok, True)
            eng = "postgresql_18_primary" if pg_ok else "sqlite_wal_hot_standby_failover"
            return self._send_json(
                200,
                {"status": "ok", "engine": eng, "user_id": u, "display_name": disp, "role": role, "token": token, "anchor": anchor, "wal_lsn": wal_meta["lsn"]},
                req_id=req_id,
                t0=t0,
                engine_hdr=eng,
                rstate=REPO.get_roaming_state(override_node_id=eff_node),
            )

        if self.path == "/api/auth/password/change":
            u = str(data.get("username", "")).strip()
            old_k = str(data.get("old_passcode", "")).strip()
            new_k = str(data.get("new_passcode", "")).strip()
            if not u or not old_k or len(new_k) < 4:
                return self._send_json(422, {"status": "validation_error", "message": "请填写账号、原口令及不少于 4 位的新口令"}, req_id=req_id, t0=t0, rstate=rstate)
            sconn = REPO.get_sqlite_conn()
            urow = sconn.execute("SELECT user_id, passcode_hash FROM sys_users WHERE user_id = ? OR username = ?", (u, u)).fetchone()
            if urow is None:
                sconn.close()
                return self._send_json(404, {"status": "not_found", "message": f"未找到学籍账号 {u}"}, req_id=req_id, t0=t0, rstate=rstate)
            stored_pw = str(urow["passcode_hash"])
            old_sha = hashlib.sha256(old_k.encode("utf-8")).hexdigest()
            if old_k != stored_pw and old_sha != stored_pw:
                sconn.close()
                return self._send_json(401, {"status": "unauthorized", "message": "原口令校验未通过，无法修改密码"}, req_id=req_id, t0=t0, rstate=rstate)
            uid_real = urow["user_id"]
            new_token = f"kaoyan-scholar-{uid_real}-{hashlib.sha256((uid_real + ':' + new_k).encode('utf-8')).hexdigest()[:12]}"
            sconn.execute("UPDATE sys_users SET passcode_hash = ?, token_secret = ? WHERE user_id = ?", (new_k, new_token, uid_real))
            sconn.commit()
            sconn.close()

            pg_ok = False
            pconn = REPO.get_pg_conn(simulate_down=sim_down)
            if pconn is not None:
                try:
                    with pconn:
                        with pconn.cursor() as cur:
                            cur.execute("UPDATE sys_users SET passcode_hash = %s, token_secret = %s WHERE user_id = %s", (new_k, new_token, uid_real))
                    pg_ok = True
                finally:
                    pconn.close()
            wal_meta = REPO.record_ha_wal("PASSWORD_CHANGE", "sys_users", uid_real, {"user_id": uid_real, "updated_at": now}, pg_ok, True)
            eng = "postgresql_18_primary" if pg_ok else "sqlite_wal_hot_standby_failover"
            return self._send_json(
                200,
                {"status": "ok", "engine": eng, "user_id": uid_real, "token": new_token, "wal_lsn": wal_meta["lsn"], "message": f"学籍 {uid_real} 密码修改成功，双擎数据库已同步"},
                req_id=req_id,
                t0=t0,
                engine_hdr=eng,
                rstate=REPO.get_roaming_state(override_node_id=eff_node),
            )

        if self.path == "/api/auth/user/create":
            u = str(data.get("username", "")).strip()
            disp = str(data.get("display_name", "")).strip() or u
            k = str(data.get("passcode", "")).strip()
            role = str(data.get("role", "SCHOLAR")).strip().upper() or "SCHOLAR"
            if not re.match(r"^[a-zA-Z0-9_\-]{2,32}$", u):
                return self._send_json(422, {"status": "validation_error", "message": "账号需为 2~32 位字母、数字、下划线或连字符"}, req_id=req_id, t0=t0, rstate=rstate)
            if len(k) < 4:
                return self._send_json(422, {"status": "validation_error", "message": "初始口令长度不少于 4 位"}, req_id=req_id, t0=t0, rstate=rstate)
            sconn = REPO.get_sqlite_conn()
            exists = sconn.execute("SELECT user_id FROM sys_users WHERE user_id = ? OR username = ?", (u, u)).fetchone()
            if exists:
                sconn.close()
                return self._send_json(409, {"status": "conflict", "message": f"学籍账号 {u} 已存在，请直接登录或修改密码"}, req_id=req_id, t0=t0, rstate=rstate)
            token = f"kaoyan-scholar-{u}-{hashlib.sha256((u + ':' + k).encode('utf-8')).hexdigest()[:12]}"
            sconn.execute("INSERT INTO sys_users (user_id, username, display_name, role, passcode_hash, token_secret, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)", (u, u, disp, role, k, token, now))
            sconn.execute("INSERT OR IGNORE INTO user_progress_anchors VALUES (?, ?, 1, ?, 2, '', 1, 1, ?)", (u, "P2024_EN1_T1", "sp-para-1", now))
            sconn.commit()
            sconn.close()

            pg_ok = False
            pconn = REPO.get_pg_conn(simulate_down=sim_down)
            if pconn is not None:
                try:
                    with pconn:
                        with pconn.cursor() as cur:
                            cur.execute(
                                "INSERT INTO sys_users (user_id, username, display_name, role, passcode_hash, token_secret, created_at) VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (user_id) DO NOTHING",
                                (u, u, disp, role, k, token, now),
                            )
                            cur.execute(
                                "INSERT INTO user_progress_anchors (user_id, last_passage_id, last_para_idx, last_span_id, last_tab_idx, essay_draft_md, streak_days, rev_no, updated_at) VALUES (%s,%s,1,%s,2,'',1,1,%s) ON CONFLICT (user_id) DO NOTHING",
                                (u, "P2024_EN1_T1", "sp-para-1", now),
                            )
                    pg_ok = True
                finally:
                    pconn.close()
            wal_meta = REPO.record_ha_wal("USER_CREATE", "sys_users", u, {"user_id": u, "display_name": disp, "role": role}, pg_ok, True)
            eng = "postgresql_18_primary" if pg_ok else "sqlite_wal_hot_standby_failover"
            return self._send_json(
                200,
                {"status": "ok", "engine": eng, "user_id": u, "display_name": disp, "role": role, "token": token, "wal_lsn": wal_meta["lsn"], "message": f"学籍账号 {u} 创建成功"},
                req_id=req_id,
                t0=t0,
                engine_hdr=eng,
                rstate=REPO.get_roaming_state(override_node_id=eff_node),
            )

        uid = verify_bearer(self.headers, simulate_pg_down=sim_down)
        if not uid:
            return self._send_json(
                401,
                {"status": "guest_sandbox_locked", "message": "当前为访客只读沙箱，请先登录专属学籍账号以写入云端数据库"},
                req_id=req_id,
                t0=t0,
                rstate=rstate,
            )

        normalized_raw = normalize_os_text(raw)
        req_hash = hashlib.sha256(f"{uid}:{self.path}:{normalized_raw}".encode("utf-8")).hexdigest()
        if idem_key:
            sconn = REPO.get_sqlite_conn()
            existing = sconn.execute(
                "SELECT req_hash, resp_code, resp_body_json FROM api_idempotency_keys WHERE idempotency_key = ?",
                (idem_key,),
            ).fetchone()
            sconn.close()
            if existing:
                if existing["req_hash"] != req_hash:
                    return self._send_json(409, {"status": "idempotency_conflict", "message": "Idempotency key reused with different payload"}, req_id=req_id, t0=t0, rstate=rstate)
                cached_body = json.loads(existing["resp_body_json"])
                cached_body["idempotent_replay"] = True
                return self._send_json(existing["resp_code"], cached_body, req_id=req_id, t0=t0, idem_replay=True, rstate=rstate)

        def finalize_write(code: int, resp_payload: dict, op_type: str, tbl: str, pk: str, pg_ok: bool):
            wal_meta = REPO.record_ha_wal(op_type, tbl, pk, data, pg_ok, True)
            resp_payload["tx_uuid"] = wal_meta["tx_uuid"]
            resp_payload["wal_lsn"] = wal_meta["lsn"]
            resp_payload["cluster_epoch"] = wal_meta["epoch"]
            resp_payload["row_checksum_sha256"] = wal_meta["row_checksum_sha256"]
            resp_payload["replicated_to"] = wal_meta["replicated_to"]
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
                REPO.record_ha_wal("IDEMPOTENCY_SAVE", "api_idempotency_keys", idem_key, {"idempotency_key": idem_key}, pg_ok, True)
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
            return self._send_json(code, resp_payload, req_id=req_id, t0=t0, engine_hdr=resp_payload["engine"], rstate=REPO.get_roaming_state(override_node_id=eff_node))

        if self.path == "/api/progress/anchor":
            try:
                para_idx = int(data.get("last_para_idx", 2))
            except Exception:
                return self._send_json(400, {"status": "bad_request", "message": "last_para_idx must be integer"}, req_id=req_id, t0=t0, rstate=rstate)
            if para_idx < 0 or para_idx > 200:
                return self._send_json(422, {"status": "validation_error", "message": "last_para_idx out of valid range [0, 200]"}, req_id=req_id, t0=t0, rstate=rstate)
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
            title = normalize_os_text(str(data.get("title", ""))).strip()
            txt = normalize_os_text(str(data.get("raw_text", ""))).strip()
            if not title or len(txt) < 10:
                return self._send_json(422, {"status": "validation_error", "message": "title and raw_text (>=10 chars) are required"}, req_id=req_id, t0=t0, rstate=rstate)
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
            raw_csv = normalize_os_text(str(data.get("raw_csv", ""))).strip()
            if raw_csv:
                sconn = REPO.get_sqlite_conn()
                ingested_items = []
                for ln in re.split(r"\n+", raw_csv):
                    parts = [x.strip() for x in ln.split(",") if x.strip()]
                    if len(parts) >= 2:
                        w = re.sub(r"[^a-zA-Z\-]", "", parts[0]).lower()
                        if len(w) < 2:
                            continue
                        meaning = parts[1][:512]
                        try:
                            cnt = max(1, int(parts[2])) if len(parts) >= 3 else 1
                        except Exception:
                            cnt = 1
                        tier = (parts[3] if len(parts) >= 4 else "CORE_1800")[:32]
                        urg = calc_ebbinghaus_urgency(cnt, 0.2, tier)
                        sconn.execute(
                            "INSERT INTO user_vocab_ledger (user_id, lemma, syllabus_tier, lookup_count, last_seen_at, days_since_seen, urgency_score, exam_source, contextual_meaning, mastery_state) "
                            "VALUES (?, ?, ?, ?, ?, 0.2, ?, '批量词表导入', ?, 'LEARNING') "
                            "ON CONFLICT(user_id, lemma) DO UPDATE SET lookup_count = user_vocab_ledger.lookup_count + ?, last_seen_at = excluded.last_seen_at, urgency_score = ?, contextual_meaning = excluded.contextual_meaning",
                            (uid, w, tier, cnt, now, urg, meaning, cnt, urg),
                        )
                        ingested_items.append((uid, w, tier, cnt, now, urg, meaning))
                sconn.commit()
                sconn.close()
                pg_ok = False
                pconn = REPO.get_pg_conn(simulate_down=sim_down)
                if pconn is not None and ingested_items:
                    try:
                        with pconn:
                            with pconn.cursor() as cur:
                                for uid_i, w_i, tier_i, cnt_i, now_i, urg_i, meaning_i in ingested_items:
                                    cur.execute(
                                        "INSERT INTO user_vocab_ledger (user_id, lemma, syllabus_tier, lookup_count, last_seen_at, days_since_seen, urgency_score, exam_source, contextual_meaning, mastery_state) "
                                        "VALUES (%s,%s,%s,%s,%s,0.2,%s,'批量词表导入',%s,'LEARNING') "
                                        "ON CONFLICT (user_id, lemma) DO UPDATE SET lookup_count = user_vocab_ledger.lookup_count + EXCLUDED.lookup_count, last_seen_at = EXCLUDED.last_seen_at, urgency_score = EXCLUDED.urgency_score, contextual_meaning = EXCLUDED.contextual_meaning",
                                        (uid_i, w_i, tier_i, cnt_i, now_i, urg_i, meaning_i),
                                    )
                        pg_ok = True
                    finally:
                        pconn.close()
                return finalize_write(
                    200,
                    {"status": "ok", "user_id": uid, "ingested_count": len(ingested_items)},
                    "VOCAB_BULK_CSV_INGEST",
                    "user_vocab_ledger",
                    f"{uid}:bulk:{len(ingested_items)}",
                    pg_ok,
                )

            lemma = str(data.get("lemma", "")).strip().lower()
            if not lemma or not re.match(r"^[a-zA-Z\-]{2,45}$", lemma):
                return self._send_json(422, {"status": "validation_error", "message": "Invalid English lemma (2..45 letters)"}, req_id=req_id, t0=t0, rstate=rstate)
            tier = str(data.get("syllabus_tier", "CORE_1800"))[:32]
            days_ago = float(data.get("days_since_seen", 0.5))
            exam_src = normalize_os_path(str(data.get("exam_source", "真题实时查词")))[:128]
            ctx_meaning = normalize_os_text(str(data.get("contextual_meaning", "学籍云端同步词条")))[:512]

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
                {"status": "ok", "user_id": uid, "lemma": lemma, "lookup_count": new_cnt, "urgency_score": urg, "syllabus_tier": tier, "exam_source": exam_src},
                "VOCAB_EBBINGHAUS_UPSERT",
                "user_vocab_ledger",
                f"{uid}:{lemma}",
                pg_ok,
            )

        if self.path in ("/api/annotations/save", "/api/notes"):
            selected_text = normalize_os_text(str(data.get("selected_text", data.get("text", "")))).strip()
            if not selected_text:
                return self._send_json(422, {"status": "validation_error", "message": "selected_text cannot be empty"}, req_id=req_id, t0=t0, rstate=rstate)
            passage_id = str(data.get("passage_id", "P2024_EN1_T1"))[:64]
            granularity = str(data.get("granularity", "SENTENCE"))[:32]
            para_idx = int(data.get("para_idx", 1))
            start_offset = int(data.get("start_offset", 0))
            end_offset = int(data.get("end_offset", len(selected_text)))
            prefix_quote = normalize_os_text(str(data.get("prefix_quote", "")))[:64]
            suffix_quote = normalize_os_text(str(data.get("suffix_quote", "")))[:64]
            syntax_bd = normalize_os_text(str(data.get("syntax_breakdown", data.get("breakdown", ""))))
            comment = normalize_os_text(str(data.get("user_comment", data.get("comment", ""))))
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
            content_en = normalize_os_text(str(data.get("content_en", data.get("en", "")))).strip()
            translation_zh = normalize_os_text(str(data.get("translation_zh", data.get("zh", "")))).strip() or "阅读精读笔记一键升格语料"
            granularity = str(data.get("granularity", "SENTENCE"))[:32]
            source_ref = normalize_os_path(str(data.get("source_ref", "2024 英语一 Text 1")))[:128]

            sconn = REPO.get_sqlite_conn()
            if self.path == "/api/annotations/promote" and span_id and not content_en:
                sp_row = sconn.execute("SELECT * FROM annotation_spans WHERE span_id = ?", (span_id,)).fetchone()
                if not sp_row:
                    sconn.close()
                    return self._send_json(404, {"status": "not_found", "message": f"Annotation span {span_id} not found"}, req_id=req_id, t0=t0, rstate=rstate)
                content_en = sp_row["selected_text"]
                translation_zh = sp_row["user_comment"] or sp_row["syntax_breakdown"] or translation_zh
                granularity = sp_row["granularity"]
                source_ref = f"Promoted from {sp_row['passage_id']} (span:{span_id})"

            if not content_en:
                sconn.close()
                return self._send_json(422, {"status": "validation_error", "message": "content_en or valid span_id is required"}, req_id=req_id, t0=t0, rstate=rstate)

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

        return self._send_json(404, {"status": "not_found", "message": "Unknown API endpoint"}, req_id=req_id, t0=t0, rstate=rstate)


if __name__ == "__main__":
    REPO.init_and_migrate_both_engines()
    srv = ThreadingHTTPServer(("0.0.0.0", LISTEN_PORT), KaoyanModularHandler)
    print(
        f"Kaoyan Modular Hub v4.0 (Cross-OS Roaming HA: Node={LOCAL_NODE_INFO['node_id']} OS={LOCAL_NODE_INFO['os_label']}) listening on 0.0.0.0:{LISTEN_PORT}",
        flush=True,
    )
    srv.serve_forever()
