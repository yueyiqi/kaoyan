package com.kaoyan.hub.schema;

import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Authoritative 18-Table x 146-Column Schema Catalog Registry for KaoyanEnglish Hub v6.0.
 *
 * Provides zero-trust metadata introspection for:
 * - L1: 5 Business Domains (DOM_01 .. DOM_05)
 * - L2: 18 Database Tables with Primary Keys & Foreign Key Graph
 * - L3: 146 Columns with SQL Types, Nullability, Sensitivity Classification & Exposure Ratios
 */
@Component
public class Schema18TableCatalogRegistry {

    public record TableSpec(
            String tableName,
            String domainCode,
            String domainNameCn,
            String tableLabelCn,
            String primaryKey,
            List<String> columns,
            List<String> sensitiveColumns,
            Map<String, String> foreignKeys
    ) {}

    private final Map<String, TableSpec> tableCatalog = new LinkedHashMap<>();
    private final Map<String, String> domainLabels = new LinkedHashMap<>();

    public Schema18TableCatalogRegistry() {
        domainLabels.put("DOM_01_LEXEME_AND_PASSAGE", "大纲词族与真题篇章域 (Lexeme & Passage Domain)");
        domainLabels.put("DOM_02_PROGRESS_AND_SPANS", "精读进度与多粒度批注域 (Progress & Spans Domain)");
        domainLabels.put("DOM_03_VOCAB_AND_ESSAY", "艾宾浩斯生词与作文语料域 (Vocab & Essay Domain)");
        domainLabels.put("DOM_04_RBAC_SECURITY", "零信任账号权限与审计域 (Zero-Trust RBAC Domain)");
        domainLabels.put("DOM_05_HA_CLUSTER_OPS", "PG18双擎高可用与冷备域 (Dual-Engine HA Ops Domain)");
        registerAll18Tables();
    }

    private void registerAll18Tables() {
        // DOM_01 (4 tables: 9 + 12 + 8 + 9 = 38 columns)
        register("syllabus_lexemes", "DOM_01_LEXEME_AND_PASSAGE", "考纲核心词根词缀表", "id",
                List.of("id", "word", "phonetic", "pos_tag", "cn_definition",
                        "exam_frequency", "freq_tier", "root_affix_note", "created_at"),
                List.of(), Map.of());

        register("exam_passages", "DOM_01_LEXEME_AND_PASSAGE", "历年真题篇章主表", "passage_key",
                List.of("passage_key", "exam_year", "exam_type", "section_name", "title_en", "title_cn",
                        "topic_category", "difficulty_rating", "word_count", "paragraphs_json",
                        "content_sha256", "updated_at"),
                List.of(), Map.of());

        register("passage_paragraphs", "DOM_01_LEXEME_AND_PASSAGE", "真题段落结构化拆解表", "id",
                List.of("id", "passage_key", "paragraph_index", "content_en",
                        "translation_cn", "discourse_role", "key_syntax_note", "created_at"),
                List.of(), Map.of("passage_key", "exam_passages.passage_key"));

        register("syntax_tree_nodes", "DOM_01_LEXEME_AND_PASSAGE", "长难句语法依存树节点表", "id",
                List.of("id", "passage_key", "paragraph_index", "sentence_no", "clause_type",
                        "head_token", "dependency_grammar", "translation_tip", "created_at"),
                List.of(), Map.of("passage_key", "exam_passages.passage_key"));

        // DOM_02 (3 tables: 10 + 12 + 8 = 30 columns)
        register("user_progress_anchors", "DOM_02_PROGRESS_AND_SPANS", "多端漫游阅读进度锚点表", "id",
                List.of("id", "user_id", "passage_key", "active_paragraph_idx", "char_offset",
                        "scroll_ratio", "reading_seconds", "device_tag", "sync_version", "updated_at"),
                List.of(), Map.of("user_id", "sys_users.username", "passage_key", "exam_passages.passage_key"));

        register("annotation_spans", "DOM_02_PROGRESS_AND_SPANS", "三粒度高亮批注跨度表", "span_uuid",
                List.of("span_uuid", "user_id", "passage_key", "paragraph_idx", "start_offset", "end_offset",
                        "selected_text", "granularity", "highlight_color", "note_markdown",
                        "is_promoted_essay", "created_at"),
                List.of(), Map.of("user_id", "sys_users.username", "passage_key", "exam_passages.passage_key"));

        register("reading_session_telemetry", "DOM_02_PROGRESS_AND_SPANS", "精读会话停留遥测流水表", "session_id",
                List.of("session_id", "user_id", "passage_key", "dwell_seconds",
                        "lookup_count", "annotation_count", "client_viewport", "recorded_at"),
                List.of(), Map.of("user_id", "sys_users.username", "passage_key", "exam_passages.passage_key"));

        // DOM_03 (3 tables: 11 + 9 + 8 = 28 columns)
        register("user_vocab_ledger", "DOM_03_VOCAB_AND_ESSAY", "艾宾浩斯个人生词账本表", "id",
                List.of("id", "user_id", "word", "source_passage_key", "context_sentence", "mastery_level",
                        "review_count", "lapse_count", "ebbinghaus_urgency", "next_review_at", "updated_at"),
                List.of(), Map.of("user_id", "sys_users.username", "word", "syllabus_lexemes.word"));

        register("essay_corpus_snippets", "DOM_03_VOCAB_AND_ESSAY", "高分作文句型语料库表", "id",
                List.of("id", "user_id", "source_span_uuid", "rhetorical_category", "english_sentence",
                        "chinese_meaning", "cloze_template", "practice_count", "created_at"),
                List.of(), Map.of("user_id", "sys_users.username", "source_span_uuid", "annotation_spans.span_uuid"));

        register("cloze_drill_records", "DOM_03_VOCAB_AND_ESSAY", "语料挖空默写训练流水表", "drill_id",
                List.of("drill_id", "user_id", "snippet_id", "submitted_answer",
                        "is_correct", "response_time_ms", "error_category", "practiced_at"),
                List.of(), Map.of("user_id", "sys_users.username", "snippet_id", "essay_corpus_snippets.id"));

        // DOM_04 (5 tables: 11 + 7 + 6 + 5 + 9 = 38 columns)
        register("sys_users", "DOM_04_RBAC_SECURITY", "零信任平台账号主表", "user_id",
                List.of("user_id", "username", "display_name", "role_code", "role_level", "account_status",
                        "password_hash", "password_salt", "zero_memory_enforced", "last_login_at", "updated_at"),
                List.of("password_hash", "password_salt"), Map.of("role_code", "sys_roles.role_code"));

        register("sys_roles", "DOM_04_RBAC_SECURITY", "RBAC角色层级定义表", "role_code",
                List.of("role_code", "role_name_cn", "role_level", "data_scope_mode",
                        "can_access_admin_console", "description", "created_at"),
                List.of(), Map.of());

        register("sys_permissions", "DOM_04_RBAC_SECURITY", "细粒度API与视图权限点表", "perm_code",
                List.of("perm_code", "perm_name_cn", "resource_group", "http_method", "endpoint_pattern", "created_at"),
                List.of(), Map.of());

        register("sys_role_permissions", "DOM_04_RBAC_SECURITY", "角色与权限点多对多映射表", "id",
                List.of("id", "role_code", "perm_code", "granted_by", "granted_at"),
                List.of(), Map.of("role_code", "sys_roles.role_code", "perm_code", "sys_permissions.perm_code"));

        register("sys_rbac_audit_log", "DOM_04_RBAC_SECURITY", "管理端安全操作与鉴权审计表", "audit_id",
                List.of("audit_id", "actor_username", "actor_role", "action_type", "target_entity",
                        "decision_outcome", "client_ip_hash", "trace_id", "created_at"),
                List.of(), Map.of("actor_username", "sys_users.username"));

        // DOM_05 (3 tables: 4 + 4 + 4 = 12 columns -> Total 38+30+28+38+12 = 146 columns)
        register("ha_cluster_roaming_state", "DOM_05_HA_CLUSTER_OPS", "三节点集群纪元与漫游状态表", "node_id",
                List.of("node_id", "cluster_epoch", "engine_mode", "heartbeat_at"),
                List.of(), Map.of());

        register("ha_wal_replication_journal", "DOM_05_HA_CLUSTER_OPS", "PG18与SQLite双擎WAL复制日志表", "lsn_seq",
                List.of("lsn_seq", "idempotency_key", "payload_sha256", "replicated_at"),
                List.of(), Map.of());

        register("ha_t2_cold_backup_manifest", "DOM_05_HA_CLUSTER_OPS", "T2金库Zstd冷备快照清单表", "snapshot_id",
                List.of("snapshot_id", "archive_sha256", "compressed_bytes", "verified_at"),
                List.of(), Map.of());
    }

    private void register(
            String tableName,
            String domainCode,
            String tableLabelCn,
            String primaryKey,
            List<String> columns,
            List<String> sensitiveColumns,
            Map<String, String> foreignKeys) {
        tableCatalog.put(tableName, new TableSpec(
                tableName,
                domainCode,
                domainLabels.getOrDefault(domainCode, domainCode),
                tableLabelCn,
                primaryKey,
                List.copyOf(columns),
                List.copyOf(sensitiveColumns),
                Map.copyOf(foreignKeys)));
    }

    public int getTableCount() {
        return tableCatalog.size();
    }

    public int getDomainCount() {
        return domainLabels.size();
    }

    public int getTotalColumnCount() {
        return tableCatalog.values().stream().mapToInt(t -> t.columns().size()).sum();
    }

    public Map<String, TableSpec> getAllTables() {
        return Collections.unmodifiableMap(tableCatalog);
    }

    public TableSpec getTableSpec(String tableName) {
        return tableCatalog.get(tableName);
    }

    public List<Map<String, Object>> buildDomainSummaryTree() {
        List<Map<String, Object>> result = new ArrayList<>();
        for (Map.Entry<String, String> dom : domainLabels.entrySet()) {
            String domCode = dom.getKey();
            List<Map<String, Object>> tables = new ArrayList<>();
            int domainCols = 0;
            for (TableSpec spec : tableCatalog.values()) {
                if (spec.domainCode().equals(domCode)) {
                    domainCols += spec.columns().size();
                    Map<String, Object> tMap = new LinkedHashMap<>();
                    tMap.put("table_name", spec.tableName());
                    tMap.put("label_cn", spec.tableLabelCn());
                    tMap.put("primary_key", spec.primaryKey());
                    tMap.put("column_count", spec.columns().size());
                    tMap.put("columns", spec.columns());
                    tMap.put("foreign_keys", spec.foreignKeys());
                    tables.add(tMap);
                }
            }
            Map<String, Object> dMap = new LinkedHashMap<>();
            dMap.put("domain_code", domCode);
            dMap.put("domain_label", dom.getValue());
            dMap.put("table_count", tables.size());
            dMap.put("column_count", domainCols);
            dMap.put("tables", tables);
            result.add(dMap);
        }
        return result;
    }
}
