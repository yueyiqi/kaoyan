-- V005: Complete additive schema; no account or application-data seeds.
CREATE TABLE IF NOT EXISTS schema_migrations (
    version_id VARCHAR(32) PRIMARY KEY,
    script_name VARCHAR(128) NOT NULL,
    checksum_sha256 VARCHAR(64) NOT NULL,
    engine_target VARCHAR(32) NOT NULL DEFAULT 'DUAL_PG_SQLITE',
    applied_at VARCHAR(64) NOT NULL
);

CREATE TABLE IF NOT EXISTS sys_users (
    user_id VARCHAR(64) PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    display_name VARCHAR(128) NOT NULL,
    role VARCHAR(32) NOT NULL DEFAULT 'SCHOLAR',
    passcode_hash VARCHAR(128) NOT NULL,
    token_secret VARCHAR(128) NOT NULL,
    created_at VARCHAR(64) NOT NULL,
    account_status TEXT NOT NULL DEFAULT 'ACTIVE',
    passcode_salt TEXT NOT NULL DEFAULT 'kaoyan_salt_2026',
    failed_login_count INTEGER NOT NULL DEFAULT 0,
    last_login_at TEXT NOT NULL DEFAULT '',
    password_updated_at TEXT NOT NULL DEFAULT '',
    created_by TEXT NOT NULL DEFAULT 'system'
);

CREATE TABLE IF NOT EXISTS user_progress_anchors (
    user_id VARCHAR(64) PRIMARY KEY,
    last_passage_id VARCHAR(64) NOT NULL DEFAULT 'P2024_EN1_T1',
    last_para_idx INTEGER NOT NULL DEFAULT 2,
    last_span_id VARCHAR(64) NOT NULL DEFAULT 'sp-sent-2',
    last_tab_idx INTEGER NOT NULL DEFAULT 2,
    essay_draft_md TEXT NOT NULL DEFAULT '',
    streak_days INTEGER NOT NULL DEFAULT 12,
    rev_no INTEGER NOT NULL DEFAULT 1,
    updated_at VARCHAR(64) NOT NULL
);

CREATE TABLE IF NOT EXISTS syllabus_5500_lexicon (
    lemma VARCHAR(64) PRIMARY KEY,
    pos VARCHAR(32) NOT NULL,
    cn_meaning TEXT NOT NULL,
    syllabus_tier VARCHAR(32) NOT NULL,
    polysemy_trap_note TEXT DEFAULT '',
    exam_freq INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS exam_passages (
    passage_id VARCHAR(64) PRIMARY KEY,
    owner_user_id VARCHAR(64) NOT NULL,
    year INTEGER NOT NULL,
    exam_type VARCHAR(32) NOT NULL,
    text_no VARCHAR(32) NOT NULL,
    title VARCHAR(256) NOT NULL,
    paragraphs_json TEXT NOT NULL,
    syllabus_hits_json TEXT NOT NULL DEFAULT '[]',
    sha256_hash VARCHAR(64) NOT NULL,
    created_at VARCHAR(64) NOT NULL
);

CREATE TABLE IF NOT EXISTS annotation_spans (
    span_id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    passage_id VARCHAR(64) NOT NULL,
    granularity VARCHAR(32) NOT NULL,
    para_idx INTEGER NOT NULL DEFAULT 1,
    start_offset INTEGER NOT NULL DEFAULT 0,
    end_offset INTEGER NOT NULL DEFAULT 0,
    selected_text TEXT NOT NULL,
    prefix_quote VARCHAR(64) NOT NULL DEFAULT '',
    suffix_quote VARCHAR(64) NOT NULL DEFAULT '',
    syntax_breakdown TEXT NOT NULL DEFAULT '',
    user_comment TEXT NOT NULL DEFAULT '',
    promoted_snippet_id VARCHAR(64) NOT NULL DEFAULT '',
    version INTEGER NOT NULL DEFAULT 1,
    created_at VARCHAR(64) NOT NULL
);

CREATE TABLE IF NOT EXISTS essay_corpus_snippets (
    snippet_id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    theme_tag VARCHAR(64) NOT NULL,
    func_slot VARCHAR(64) NOT NULL,
    granularity VARCHAR(32) NOT NULL,
    content_en TEXT NOT NULL,
    cloze_pattern TEXT NOT NULL,
    translation_zh TEXT NOT NULL,
    source_ref VARCHAR(128) NOT NULL,
    usage_count INTEGER NOT NULL DEFAULT 0,
    created_at VARCHAR(64) NOT NULL
);

CREATE TABLE IF NOT EXISTS ha_sync_wal_journal (
    tx_uuid VARCHAR(64) PRIMARY KEY,
    op_type VARCHAR(32) NOT NULL,
    target_table VARCHAR(64) NOT NULL,
    record_pk VARCHAR(128) NOT NULL,
    payload_json TEXT NOT NULL,
    pg_status VARCHAR(16) NOT NULL,
    sqlite_status VARCHAR(16) NOT NULL,
    created_at VARCHAR(64) NOT NULL
);

CREATE TABLE IF NOT EXISTS api_idempotency_keys (
    idempotency_key VARCHAR(128) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    endpoint VARCHAR(128) NOT NULL,
    req_hash VARCHAR(64) NOT NULL,
    resp_code INTEGER NOT NULL,
    resp_body_json TEXT NOT NULL,
    created_at VARCHAR(64) NOT NULL
);

CREATE TABLE IF NOT EXISTS user_vocab_ledger (
    vocab_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, lemma TEXT NOT NULL, syllabus_tier TEXT NOT NULL DEFAULT 'CORE_1800', lookup_count INTEGER NOT NULL DEFAULT 1, last_seen_at TEXT NOT NULL, days_since_seen REAL NOT NULL DEFAULT 0.0, urgency_score REAL NOT NULL DEFAULT 0.50, exam_source TEXT NOT NULL DEFAULT '', contextual_meaning TEXT NOT NULL DEFAULT '', mastery_state TEXT NOT NULL DEFAULT 'LEARNING', UNIQUE(user_id, lemma)
);

CREATE TABLE IF NOT EXISTS sys_roles (
    role_code TEXT PRIMARY KEY, role_name TEXT NOT NULL, role_level INTEGER NOT NULL DEFAULT 50, is_system INTEGER NOT NULL DEFAULT 1, description TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sys_permissions (
    perm_code TEXT PRIMARY KEY, perm_name TEXT NOT NULL, resource_domain TEXT NOT NULL, action_type TEXT NOT NULL, description TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS sys_role_permissions (
    role_code TEXT NOT NULL, perm_code TEXT NOT NULL, granted_at TEXT NOT NULL, granted_by TEXT NOT NULL DEFAULT 'system', PRIMARY KEY (role_code, perm_code)
);

CREATE TABLE IF NOT EXISTS sys_rbac_audit_log (
    audit_id TEXT PRIMARY KEY, actor_user_id TEXT NOT NULL, actor_role TEXT NOT NULL, target_user_id TEXT NOT NULL, action TEXT NOT NULL, detail_json TEXT NOT NULL DEFAULT '{}', client_ip TEXT NOT NULL DEFAULT '127.0.0.1', created_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON sys_users(username);
CREATE UNIQUE INDEX IF NOT EXISTS idx_vocab_identity ON user_vocab_ledger(user_id, lemma);
CREATE INDEX IF NOT EXISTS idx_spans_user_passage ON annotation_spans(user_id, passage_id, para_idx, start_offset);
CREATE INDEX IF NOT EXISTS idx_essay_user_theme ON essay_corpus_snippets(user_id, theme_tag, func_slot);
CREATE INDEX IF NOT EXISTS idx_vocab_user_urgency ON user_vocab_ledger(user_id, urgency_score DESC);
CREATE INDEX IF NOT EXISTS idx_passages_sha256 ON exam_passages(sha256_hash);
