PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version_id TEXT PRIMARY KEY,
    script_name TEXT NOT NULL,
    checksum_sha256 TEXT NOT NULL,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sys_users (
    user_id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
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
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES sys_users(user_id)
);

CREATE TABLE IF NOT EXISTS syllabus_5500_lexicon (
    lemma TEXT PRIMARY KEY,
    pos TEXT NOT NULL,
    cn_meaning TEXT NOT NULL,
    syllabus_tier TEXT NOT NULL,
    polysemy_trap_note TEXT DEFAULT '',
    exam_freq INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS exam_passages (
    passage_id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    exam_type TEXT NOT NULL,
    text_no TEXT NOT NULL,
    title TEXT NOT NULL,
    paragraphs_json TEXT NOT NULL,
    syllabus_hits_json TEXT NOT NULL DEFAULT '[]',
    sha256_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS annotation_spans (
    span_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    passage_id TEXT NOT NULL,
    granularity TEXT NOT NULL,
    para_idx INTEGER NOT NULL DEFAULT 1,
    start_offset INTEGER NOT NULL DEFAULT 0,
    end_offset INTEGER NOT NULL DEFAULT 0,
    selected_text TEXT NOT NULL,
    syntax_breakdown TEXT NOT NULL DEFAULT '',
    user_comment TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_spans_user_passage ON annotation_spans(user_id, passage_id, para_idx, start_offset);

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

CREATE TABLE IF NOT EXISTS essay_corpus_snippets (
    snippet_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    theme_tag TEXT NOT NULL,
    func_slot TEXT NOT NULL,
    granularity TEXT NOT NULL,
    content_en TEXT NOT NULL,
    cloze_pattern TEXT NOT NULL,
    translation_zh TEXT NOT NULL,
    source_ref TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_essay_user_theme ON essay_corpus_snippets(user_id, theme_tag, func_slot);

INSERT OR IGNORE INTO schema_migrations (version_id, script_name, checksum_sha256, applied_at) VALUES ('V001', 'V001__init_kaoyan_8tables.sql', 'sha256:8tables_v23', datetime('now'));
INSERT OR IGNORE INTO sys_users VALUES ('colleague_a', 'colleague_a', '同事 A (考研英语主理人)', 'SCHOLAR', 'kaoyan2026', 'kaoyan-scholar-colleague_a-kaoyan2026', datetime('now'));
INSERT OR IGNORE INTO sys_users VALUES ('commander', 'commander', '统帅 (集群架构管理员)', 'ADMIN', 'kaoyan2026', 'kaoyan-scholar-commander-kaoyan2026', datetime('now'));
INSERT OR IGNORE INTO user_progress_anchors VALUES ('colleague_a', 'P2024_EN1_T1', 2, 'sp-sent-2', 2, '', 12, 1, datetime('now'));
INSERT OR IGNORE INTO user_progress_anchors VALUES ('commander', 'P2024_EN1_T1', 1, 'sp-para-1', 0, '', 30, 1, datetime('now'));
INSERT OR IGNORE INTO syllabus_5500_lexicon VALUES ('accommodate', 'v.', '适应，顺应；容纳，顾及', 'POLYSEMY_TRAP', '考研常考【容纳/顺应观点】，非仅提供食宿', 18);
INSERT OR IGNORE INTO syllabus_5500_lexicon VALUES ('intellectual', 'adj./n.', '智力的；知识分子', 'CORE_1800', '', 26);
INSERT OR IGNORE INTO syllabus_5500_lexicon VALUES ('empirical', 'adj.', '实证的，以经验或观察为依据的', 'CORE_1800', '反义词 theoretical', 14);
