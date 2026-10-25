"""Database bootstrap, health, and write journal; canonical shared repository."""
from __future__ import annotations
from threading import local
from kaoyan_runtime import BACKUP_DIR, CORE_TABLES, HAS_PG, LOCAL_SQLITE_PATH, PG_DSN, Path, RBAC_PERMS_SEED, RBAC_ROLES_SEED, RBAC_ROLE_PERMS_MAP, SEED_USERS, ensure_pg_schema, ensure_schema, hashlib, inspect_schema, json, now_str, psycopg2, sqlite3, time, uuid

REQUEST_TRANSACTION = local()


class DualEngineHARepository:
    # Manages Dual-Write and Automatic Failover between PostgreSQL 18 (Primary) and SQLite WAL (Hot Standby).

    def __init__(self, pg_dsn: str, sqlite_path: Path) -> None:
        self.pg_dsn = pg_dsn
        self.sqlite_path = sqlite_path
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    def get_sqlite_conn(self) -> sqlite3.Connection:
        if getattr(REQUEST_TRANSACTION, "connection", None) is not None:
            return REQUEST_TRANSACTION.connection
        conn = sqlite3.connect(str(self.sqlite_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        return conn

    def get_pg_conn(self, simulate_down: bool = False):
        if simulate_down or not HAS_PG or not self.pg_dsn:
            return None
        try:
            conn = psycopg2.connect(self.pg_dsn, connect_timeout=2)
            return conn
        except Exception:
            return None

    def init_and_migrate_both_engines(self) -> None:
        # 1. Initialize & Upgrade SQLite WAL Hot Standby
        sconn = self.get_sqlite_conn()
        try:
            ensure_schema(sconn)
        except BaseException:
            sconn.close()
            raise
        ts_seed = now_str()
        sconn.execute(
            "INSERT OR IGNORE INTO schema_migrations (version_id, script_name, checksum_sha256, engine_target, applied_at) VALUES (?, ?, ?, ?, ?)",
            ("V003", "V003__rbac_5tables_and_pbkdf2_security.sql", hashlib.sha256(b"V003_RBAC_5TABLES").hexdigest(), "DUAL_PG_SQLITE", ts_seed),
        )
        # Seed RBAC roles, permissions, role_permissions
        for rc, rn, rl, is_sys, rdesc in RBAC_ROLES_SEED:
            sconn.execute(
                "INSERT OR IGNORE INTO sys_roles (role_code, role_name, role_level, is_system, description, created_at) VALUES (?,?,?,?,?,?)",
                (rc, rn, rl, is_sys, rdesc, ts_seed),
            )
        for pc, pn, dom, act, pdesc in RBAC_PERMS_SEED:
            sconn.execute(
                "INSERT OR IGNORE INTO sys_permissions (perm_code, perm_name, resource_domain, action_type, description) VALUES (?,?,?,?,?)",
                (pc, pn, dom, act, pdesc),
            )
        for rc, plist in RBAC_ROLE_PERMS_MAP.items():
            for pc in plist:
                sconn.execute(
                    "INSERT OR IGNORE INTO sys_role_permissions (role_code, perm_code, granted_at, granted_by) VALUES (?,?,?,?)",
                    (rc, pc, ts_seed, "system"),
                )
        # Seed or upgrade default ADMIN and SCHOLAR accounts with PBKDF2 hashes
        for uid_s, disp_s, role_s, stat_s, salt_s, hash_s, tok_s, para_s, streak_s in SEED_USERS:
            existing_u = sconn.execute("SELECT user_id, passcode_hash, passcode_salt FROM sys_users WHERE user_id = ?", (uid_s,)).fetchone()
            if existing_u is None:
                sconn.execute(
                    "INSERT INTO sys_users (user_id, username, display_name, role, account_status, passcode_hash, passcode_salt, token_secret, failed_login_count, last_login_at, password_updated_at, created_by, created_at) VALUES (?,?,?,?,?,?,?,?,0,'',?,'system',?)",
                    (uid_s, uid_s, disp_s, role_s, stat_s, hash_s, salt_s, tok_s, ts_seed, ts_seed),
                )
            # Existing account credentials, role and status belong to the operator.
            # Schema repair must never reset accounts or promote seed usernames.
            sconn.execute(
                "INSERT OR IGNORE INTO user_progress_anchors (user_id, last_passage_id, last_para_idx, last_span_id, last_tab_idx, essay_draft_md, streak_days, rev_no, updated_at) VALUES (?, ?, ?, ?, 2, '', ?, 1, ?)",
                (uid_s, "P2024_EN1_T1", para_s, "sp-sent-2", streak_s, ts_seed),
            )
        # Ensure at least one initial RBAC audit entry exists
        aud_cnt = sconn.execute("SELECT COUNT(*) FROM sys_rbac_audit_log").fetchone()[0]
        if aud_cnt == 0:
            sconn.execute(
                "INSERT INTO sys_rbac_audit_log (audit_id, actor_user_id, actor_role, target_user_id, action, detail_json, client_ip, created_at) VALUES (?,?,?,?,?,?,?,?)",
                ("aud-init-v34", "system", "ADMIN", "all", "RBAC_SCHEMA_V34_INITIALIZED", json.dumps({"tables": 5, "hash_algo": "PBKDF2-HMAC-SHA256"}, ensure_ascii=False), "127.0.0.1", ts_seed),
            )
        sconn.commit()

        # 2. Initialize & Sync PostgreSQL 18 Primary
        pconn = self.get_pg_conn()
        if pconn is not None:
            with pconn:
                with pconn.cursor() as cur:
                    ensure_pg_schema(pconn)
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
                    cur.execute(
                        "CREATE TABLE IF NOT EXISTS sys_roles ("
                        "role_code VARCHAR(32) PRIMARY KEY, "
                        "role_name VARCHAR(64) NOT NULL, "
                        "role_level INTEGER NOT NULL DEFAULT 50, "
                        "is_system INTEGER NOT NULL DEFAULT 1, "
                        "description TEXT NOT NULL DEFAULT '', "
                        "created_at VARCHAR(64) NOT NULL);"
                    )
                    cur.execute(
                        "CREATE TABLE IF NOT EXISTS sys_permissions ("
                        "perm_code VARCHAR(64) PRIMARY KEY, "
                        "perm_name VARCHAR(128) NOT NULL, "
                        "resource_domain VARCHAR(64) NOT NULL, "
                        "action_type VARCHAR(32) NOT NULL, "
                        "description TEXT NOT NULL DEFAULT '');"
                    )
                    cur.execute(
                        "CREATE TABLE IF NOT EXISTS sys_role_permissions ("
                        "role_code VARCHAR(32) NOT NULL, "
                        "perm_code VARCHAR(64) NOT NULL, "
                        "granted_at VARCHAR(64) NOT NULL, "
                        "granted_by VARCHAR(64) NOT NULL DEFAULT 'system', "
                        "PRIMARY KEY (role_code, perm_code));"
                    )
                    cur.execute(
                        "CREATE TABLE IF NOT EXISTS sys_rbac_audit_log ("
                        "audit_id VARCHAR(64) PRIMARY KEY, "
                        "actor_user_id VARCHAR(64) NOT NULL, "
                        "actor_role VARCHAR(32) NOT NULL, "
                        "target_user_id VARCHAR(64) NOT NULL, "
                        "action VARCHAR(64) NOT NULL, "
                        "detail_json TEXT NOT NULL DEFAULT '{}', "
                        "client_ip VARCHAR(64) NOT NULL DEFAULT '127.0.0.1', "
                        "created_at VARCHAR(64) NOT NULL);"
                    )
                    for pg_alter in [
                        "ALTER TABLE sys_users ADD COLUMN IF NOT EXISTS account_status VARCHAR(24) NOT NULL DEFAULT 'ACTIVE';",
                        "ALTER TABLE sys_users ADD COLUMN IF NOT EXISTS passcode_salt VARCHAR(64) NOT NULL DEFAULT 'kaoyan_salt_2026';",
                        "ALTER TABLE sys_users ADD COLUMN IF NOT EXISTS failed_login_count INTEGER NOT NULL DEFAULT 0;",
                        "ALTER TABLE sys_users ADD COLUMN IF NOT EXISTS last_login_at VARCHAR(64) NOT NULL DEFAULT '';",
                        "ALTER TABLE sys_users ADD COLUMN IF NOT EXISTS password_updated_at VARCHAR(64) NOT NULL DEFAULT '';",
                        "ALTER TABLE sys_users ADD COLUMN IF NOT EXISTS created_by VARCHAR(64) NOT NULL DEFAULT 'system';",
                    ]:
                        cur.execute(pg_alter)

                    cur.execute("CREATE INDEX IF NOT EXISTS idx_spans_user_passage ON annotation_spans(user_id, passage_id, para_idx, start_offset);")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_essay_user_theme ON essay_corpus_snippets(user_id, theme_tag, func_slot);")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_vocab_user_urgency ON user_vocab_ledger(user_id, urgency_score DESC);")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_passages_sha256 ON exam_passages(sha256_hash);")

                    for r in sconn.execute("SELECT user_id, username, display_name, role, account_status, passcode_hash, passcode_salt, token_secret, failed_login_count, last_login_at, password_updated_at, created_by, created_at FROM sys_users").fetchall():
                        cur.execute(
                            "INSERT INTO sys_users (user_id, username, display_name, role, account_status, passcode_hash, passcode_salt, token_secret, failed_login_count, last_login_at, password_updated_at, created_by, created_at) "
                            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
                            "ON CONFLICT (user_id) DO UPDATE SET role=EXCLUDED.role, account_status=EXCLUDED.account_status, passcode_hash=EXCLUDED.passcode_hash, passcode_salt=EXCLUDED.passcode_salt, token_secret=EXCLUDED.token_secret, display_name=EXCLUDED.display_name",
                            tuple(r),
                        )
                    for r in sconn.execute("SELECT role_code, role_name, role_level, is_system, description, created_at FROM sys_roles").fetchall():
                        cur.execute(
                            "INSERT INTO sys_roles (role_code, role_name, role_level, is_system, description, created_at) VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT (role_code) DO UPDATE SET role_name=EXCLUDED.role_name, role_level=EXCLUDED.role_level, description=EXCLUDED.description",
                            tuple(r),
                        )
                    for r in sconn.execute("SELECT perm_code, perm_name, resource_domain, action_type, description FROM sys_permissions").fetchall():
                        cur.execute(
                            "INSERT INTO sys_permissions (perm_code, perm_name, resource_domain, action_type, description) VALUES (%s,%s,%s,%s,%s) ON CONFLICT (perm_code) DO UPDATE SET perm_name=EXCLUDED.perm_name, description=EXCLUDED.description",
                            tuple(r),
                        )
                    for r in sconn.execute("SELECT role_code, perm_code, granted_at, granted_by FROM sys_role_permissions").fetchall():
                        cur.execute(
                            "INSERT INTO sys_role_permissions (role_code, perm_code, granted_at, granted_by) VALUES (%s,%s,%s,%s) ON CONFLICT (role_code, perm_code) DO NOTHING",
                            tuple(r),
                        )
                    for r in sconn.execute("SELECT audit_id, actor_user_id, actor_role, target_user_id, action, detail_json, client_ip, created_at FROM sys_rbac_audit_log").fetchall():
                        cur.execute(
                            "INSERT INTO sys_rbac_audit_log (audit_id, actor_user_id, actor_role, target_user_id, action, detail_json, client_ip, created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (audit_id) DO NOTHING",
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
        schema = inspect_schema(sconn)
        sqlite_counts = {}
        for tbl in CORE_TABLES:
            try:
                sqlite_counts[tbl] = sconn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
            except Exception:
                sqlite_counts[tbl] = None
        sconn.close()

        active_engine = "postgresql_18_primary" if pg_online else "sqlite_wal_hot_standby_failover"
        return {
            "status": "ok" if schema["ready"] else "unavailable",
            "schema": schema,
            "active_engine": active_engine,
            "ha_mode": "ACTIVE_ACTIVE_DUAL_WRITE" if pg_online else "FAILOVER_HOT_STANDBY",
            "pg_primary_online": pg_online,
            "pg_version": pg_version,
            "sqlite_standby_online": schema["ready"],
            "sqlite_journal_mode": "wal",
            "tables_count": len(CORE_TABLES),
            "pg_table_rows": pg_counts,
            "sqlite_table_rows": sqlite_counts,
            "in_sync": (pg_counts == sqlite_counts) if pg_online and schema["ready"] else False,
            "sync_check": "row_counts_only",
            "probe_latency_ms": round((time.perf_counter() - t0) * 1000, 2),
        }


REPO = DualEngineHARepository(PG_DSN, LOCAL_SQLITE_PATH)
