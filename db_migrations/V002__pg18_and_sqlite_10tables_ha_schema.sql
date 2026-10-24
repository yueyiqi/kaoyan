-- ============================================================================
-- V002: Kaoyan English Hub 10-Table Dual-Engine Schema (PostgreSQL 18 & SQLite WAL Compatible)
-- ============================================================================

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
    created_at VARCHAR(64) NOT NULL
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
