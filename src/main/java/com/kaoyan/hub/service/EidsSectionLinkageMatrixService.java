package com.kaoyan.hub.service;

import org.springframework.stereotype.Service;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * EIDS Section-to-Database Drill-Down Linkage Matrix Service.
 *
 * Maps all 12 UI sections of KaoyanEnglish Hub (Top 5 KPI Cards + Tab 0 .. Tab 6 Action Bars)
 * to their exact Business Domain, Database Table, Primary Key, Highlighted Column ({@code highlight_col}),
 * and Full-Text Search Keyword ({@code q}), enabling 1-click EIDS Dual-Modal (Center Modal + Right Drawer)
 * drill-down across the entire platform.
 */
@Service
public class EidsSectionLinkageMatrixService {

    public record SectionDrilldownTarget(
            String sectionId,
            String sectionNameCn,
            String domainCode,
            String tableName,
            String highlightCol,
            String defaultSearchQuery,
            String interactionMode
    ) {}

    private final List<SectionDrilldownTarget> linkageMatrix = List.of(
            new SectionDrilldownTarget(
                    "KPI_01_PASSAGE_PROGRESS", "顶部KPI-1: 当前篇章阅读进度",
                    "DOM_02_PROGRESS_AND_SPANS", "user_progress_anchors",
                    "scroll_ratio", "ENG1_2025_TEXT1", "CENTER_MODAL_PLUS_RIGHT_DRAWER"),
            new SectionDrilldownTarget(
                    "KPI_02_EBBINGHAUS_DUE", "顶部KPI-2: 今日艾宾浩斯待复习词",
                    "DOM_03_VOCAB_AND_ESSAY", "user_vocab_ledger",
                    "ebbinghaus_urgency", "empirical", "CENTER_MODAL_PLUS_RIGHT_DRAWER"),
            new SectionDrilldownTarget(
                    "KPI_03_ANNOTATION_SPANS", "顶部KPI-3: 累计高亮精读批注数",
                    "DOM_02_PROGRESS_AND_SPANS", "annotation_spans",
                    "selected_text", "anomaly", "CENTER_MODAL_PLUS_RIGHT_DRAWER"),
            new SectionDrilldownTarget(
                    "KPI_04_ESSAY_SNIPPETS", "顶部KPI-4: 作文模板语料沉淀池",
                    "DOM_03_VOCAB_AND_ESSAY", "essay_corpus_snippets",
                    "cloze_template", "[KEY:", "CENTER_MODAL_PLUS_RIGHT_DRAWER"),
            new SectionDrilldownTarget(
                    "KPI_05_HA_CLUSTER_RPO", "顶部KPI-5: PG18双擎集群RPO=0状态",
                    "DOM_05_HA_CLUSTER_OPS", "ha_cluster_roaming_state",
                    "engine_mode", "W1", "CENTER_MODAL_PLUS_RIGHT_DRAWER"),
            new SectionDrilldownTarget(
                    "TAB_00_OVERVIEW_DASHBOARD", "Tab-0: 平台总览与18表146字段全景矩阵",
                    "DOM_01_LEXEME_AND_PASSAGE", "exam_passages",
                    "title_en", "2025", "BENTO_MATRIX_AND_DRAWER"),
            new SectionDrilldownTarget(
                    "TAB_01_SPLIT_PASSAGE_READER", "Tab-1: 双栏真题精读与段落语法树下钻",
                    "DOM_01_LEXEME_AND_PASSAGE", "passage_paragraphs",
                    "content_en", "paradigm", "INLINE_PARAGRAPH_AND_SYNTAX_DRAWER"),
            new SectionDrilldownTarget(
                    "TAB_02_EBBINGHAUS_VOCAB_LEDGER", "Tab-2: 艾宾浩斯生词账本与词根词缀溯源",
                    "DOM_03_VOCAB_AND_ESSAY", "user_vocab_ledger",
                    "mastery_level", "elena", "ROW_CLICK_LEXEME_AND_LEDGER_DRAWER"),
            new SectionDrilldownTarget(
                    "TAB_03_ANNOTATION_HUB", "Tab-3: 三粒度高亮批注与偏移量契约审计",
                    "DOM_02_PROGRESS_AND_SPANS", "annotation_spans",
                    "granularity", "phrase", "SPAN_CARD_TO_L5_RECORD_DRAWER"),
            new SectionDrilldownTarget(
                    "TAB_04_ESSAY_CLOZE_WORKSHOP", "Tab-4: 作文语料工坊与挖空默写流水下钻",
                    "DOM_03_VOCAB_AND_ESSAY", "cloze_drill_records",
                    "submitted_answer", "empirical", "SNIPPET_CARD_TO_DRILL_HISTORY_DRAWER"),
            new SectionDrilldownTarget(
                    "TAB_05_DATA_LINEAGE_CENTER", "Tab-5: 五域十八表数据血缘与外键级联探针",
                    "DOM_05_HA_CLUSTER_OPS", "ha_wal_replication_journal",
                    "payload_sha256", "tx-", "DOMAIN_BENTO_TO_L4_TABLE_AND_L5_DRAWER"),
            new SectionDrilldownTarget(
                    "TAB_06_ADMIN_RBAC_CONSOLE", "Tab-6: 管理员五层下钻工作台与账号7表级联",
                    "DOM_04_RBAC_SECURITY", "sys_users",
                    "role_code", "admin", "ADMIN_5LAYER_AND_7TABLE_USER_CASCADE")
    );

    public List<SectionDrilldownTarget> getAllSectionTargets() {
        return linkageMatrix;
    }

    public SectionDrilldownTarget findTargetBySectionId(String sectionId) {
        return linkageMatrix.stream()
                .filter(t -> t.sectionId().equalsIgnoreCase(sectionId))
                .findFirst()
                .orElseThrow(() -> new IllegalArgumentException("Unknown UI sectionId: " + sectionId));
    }

    public Map<String, Object> buildLinkageSummaryPayload() {
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("ok", true);
        out.put("total_linked_sections", linkageMatrix.size());
        out.put("kpi_cards_linked", 5);
        out.put("workspace_tabs_linked", 7);
        out.put("dual_modal_architecture", "CENTER_MODAL_88VW + RIGHT_DRAWER_540PX");
        out.put("sections", linkageMatrix);
        return out;
    }
}
