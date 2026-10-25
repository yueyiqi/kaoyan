package com.kaoyan.hub.service;

import com.kaoyan.hub.ha.ClusterEpochCoordinatorService;
import com.kaoyan.hub.middleware.ZeroTrustRbacAndIdempotencyFilter;
import com.kaoyan.hub.schema.Schema18TableCatalogRegistry;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * EIDS-Assimilated 5-Layer Database Drill-Down & 3-Tier RBAC Lineage Service.
 *
 * Implements:
 * - L1 (5 Business Domains) -> L2 (18 Tables) -> L3 (146 Columns Spec)
 *   -> L4 (Paginated Rows + Full-Text Search {@code q} + {@code highlight_col})
 *   -> L5 (Single-Record 100% Column Drawer + 7-Table User Foreign-Key Cascade)
 * - 3-Tier RBAC {@code /api/db/lineage} response (GUEST teaser vs SCHOLAR scoped vs ADMIN full).
 */
@Service
public class EidsDrilldownAndLineageService {

    private static final List<String> USER_CASCADE_TABLES = List.of(
            "sys_users", "user_progress_anchors", "annotation_spans", "reading_session_telemetry",
            "user_vocab_ledger", "essay_corpus_snippets", "cloze_drill_records", "sys_rbac_audit_log"
    );

    private final Schema18TableCatalogRegistry catalogRegistry;
    private final StudyAndEbbinghausService studyService;
    private final RbacAccountManagementService rbacService;
    private final ClusterEpochCoordinatorService coordinatorService;

    public EidsDrilldownAndLineageService(
            Schema18TableCatalogRegistry catalogRegistry,
            StudyAndEbbinghausService studyService,
            RbacAccountManagementService rbacService,
            ClusterEpochCoordinatorService coordinatorService) {
        this.catalogRegistry = catalogRegistry;
        this.studyService = studyService;
        this.rbacService = rbacService;
        this.coordinatorService = coordinatorService;
    }

    public List<Map<String, Object>> resolveSanitizedTableRows(String tableName) {
        List<Map<String, Object>> raw = switch (tableName) {
            case "sys_users" -> rbacService.listSanitizedUsers();
            case "sys_roles" -> List.of(
                    Map.of("role_code", "ADMIN", "role_name_cn", "平台总控管理员", "role_level", 100,
                            "data_scope_mode", "ALL_TENANT_18TABLES", "can_access_admin_console", 1,
                            "description", "Full 5-layer drilldown & RBAC governance", "created_at", "2026-10-25T00:00:00Z"),
                    Map.of("role_code", "SCHOLAR", "role_name_cn", "正式精读研友", "role_level", 50,
                            "data_scope_mode", "SELF_OWNED_RECORDS", "can_access_admin_console", 0,
                            "description", "Full reading, Ebbinghaus & essay workshop", "created_at", "2026-10-25T00:00:00Z"),
                    Map.of("role_code", "GUEST", "role_name_cn", "未登录访客", "role_level", 10,
                            "data_scope_mode", "PUBLIC_TEASER_35PCT", "can_access_admin_console", 0,
                            "description", "35% unblurred preview & teaser metrics", "created_at", "2026-10-25T00:00:00Z")
            );
            case "sys_permissions" -> List.of(
                    Map.of("perm_code", "PERM_ADMIN_DRILLDOWN", "perm_name_cn", "五层全表下钻审计",
                            "resource_group", "DOM_04", "http_method", "GET",
                            "endpoint_pattern", "/api/admin/db/drilldown", "created_at", "2026-10-25T00:00:00Z"),
                    Map.of("perm_code", "PERM_RBAC_USER_WRITE", "perm_name_cn", "账号创建与角色状态变更",
                            "resource_group", "DOM_04", "http_method", "POST",
                            "endpoint_pattern", "/api/admin/users/**", "created_at", "2026-10-25T00:00:00Z")
            );
            case "sys_role_permissions" -> List.of(
                    Map.of("id", 1L, "role_code", "ADMIN", "perm_code", "PERM_ADMIN_DRILLDOWN",
                            "granted_by", "system", "granted_at", "2026-10-25T00:00:00Z"),
                    Map.of("id", 2L, "role_code", "ADMIN", "perm_code", "PERM_RBAC_USER_WRITE",
                            "granted_by", "system", "granted_at", "2026-10-25T00:00:00Z")
            );
            case "sys_rbac_audit_log" -> rbacService.getAuditLogs();
            case "ha_cluster_roaming_state" -> coordinatorService.getRoamingStateRows();
            case "ha_wal_replication_journal" -> coordinatorService.getWalJournalRows();
            case "ha_t2_cold_backup_manifest" -> coordinatorService.getT2ColdBackupRows();
            default -> studyService.getTableRows(tableName);
        };
        List<Map<String, Object>> sanitized = new ArrayList<>(raw.size());
        for (Map<String, Object> r : raw) {
            sanitized.add(ZeroTrustRbacAndIdempotencyFilter.maskSensitiveRowFields(r));
        }
        return sanitized;
    }

    /**
     * Executes the 5-Layer Admin Drilldown query with optional full-text keyword {@code q},
     * {@code highlightCol}, {@code pkValue} (L5 single record), or {@code userId} (7-table cascade).
     */
    public Map<String, Object> executeAdminDrilldown(
            String domain, String table, String pkValue, String userId,
            String searchQuery, String highlightCol, int page, int pageSize) {
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("ok", true);
        out.put("total_domains", catalogRegistry.getDomainCount());
        out.put("total_tables", catalogRegistry.getTableCount());
        out.put("total_columns", catalogRegistry.getTotalColumnCount());
        out.put("exposed_columns", catalogRegistry.getTotalColumnCount());
        out.put("column_coverage_ratio", "100.0%");
        out.put("l1_domains", catalogRegistry.buildDomainSummaryTree());

        if (userId != null && !userId.isBlank()) {
            out.put("drilldown_layer", "L5_USER_CASCADE");
            out.put("target_user_id", userId.trim());
            out.put("user_cascade", buildUserCascade(userId.trim()));
            return out;
        }

        if (table == null || table.isBlank()) {
            out.put("drilldown_layer", domain != null && !domain.isBlank() ? "L2_DOMAIN_TABLES" : "L1_OVERVIEW");
            return out;
        }

        Schema18TableCatalogRegistry.TableSpec spec = catalogRegistry.getTableSpec(table.trim());
        if (spec == null) {
            throw new IllegalArgumentException("Unknown table in 18-table catalog: " + table);
        }
        if (highlightCol != null && !highlightCol.isBlank() && !spec.columns().contains(highlightCol.trim())) {
            throw new IllegalArgumentException(
                    "Column '" + highlightCol + "' does not belong to table '" + spec.tableName() + "'");
        }

        List<Map<String, Object>> rows = resolveSanitizedTableRows(spec.tableName());
        if (searchQuery != null && !searchQuery.isBlank()) {
            String qLower = searchQuery.trim().toLowerCase();
            rows = rows.stream()
                    .filter(r -> r.values().stream().anyMatch(
                            v -> v != null && String.valueOf(v).toLowerCase().contains(qLower)))
                    .toList();
        }

        out.put("active_table", spec.tableName());
        out.put("table_label_cn", spec.tableLabelCn());
        out.put("primary_key", spec.primaryKey());
        out.put("l3_columns", spec.columns());
        out.put("foreign_keys", spec.foreignKeys());
        out.put("highlight_col", highlightCol != null ? highlightCol.trim() : "");
        out.put("search_query", searchQuery != null ? searchQuery.trim() : "");

        if (pkValue != null && !pkValue.isBlank()) {
            out.put("drilldown_layer", "L5_RECORD_DRAWER");
            Map<String, Object> record = rows.stream()
                    .filter(r -> pkValue.trim().equals(String.valueOf(r.get(spec.primaryKey()))))
                    .findFirst()
                    .orElse(rows.isEmpty() ? Map.of() : rows.get(0));
            out.put("l5_record", record);
            out.put("l5_column_count", spec.columns().size());
            return out;
        }

        int safeSize = Math.max(1, Math.min(100, pageSize));
        int safePage = Math.max(1, page);
        int fromIdx = Math.min((safePage - 1) * safeSize, rows.size());
        int toIdx = Math.min(fromIdx + safeSize, rows.size());

        out.put("drilldown_layer", "L4_TABLE_ROWS");
        out.put("total_rows", rows.size());
        out.put("page", safePage);
        out.put("page_size", safeSize);
        out.put("l4_rows", rows.subList(fromIdx, toIdx));
        return out;
    }

    private Map<String, Object> buildUserCascade(String username) {
        Map<String, Object> cascade = new LinkedHashMap<>();
        for (String tbl : USER_CASCADE_TABLES) {
            List<Map<String, Object>> rows = resolveSanitizedTableRows(tbl).stream()
                    .filter(r -> username.equalsIgnoreCase(String.valueOf(r.getOrDefault("username", "")))
                            || username.equalsIgnoreCase(String.valueOf(r.getOrDefault("user_id", "")))
                            || username.equalsIgnoreCase(String.valueOf(r.getOrDefault("actor_username", ""))))
                    .toList();
            cascade.put(tbl, rows);
        }
        return cascade;
    }

    public Map<String, Object> buildTieredLineageResponse(
            RbacAccountManagementService.AuthenticatedPrincipal principal) {
        Map<String, Object> resp = new LinkedHashMap<>();
        resp.put("ok", true);
        resp.put("viewer_role", principal.roleCode());
        resp.put("viewer_level", principal.roleLevel());
        resp.put("total_tables", catalogRegistry.getTableCount());
        resp.put("total_columns", catalogRegistry.getTotalColumnCount());
        resp.put("generated_at", Instant.now().toString());
        if (principal.roleLevel() <= 10) {
            resp.put("access_tier", "GUEST_TEASER_SUMMARY");
            resp.put("domains", catalogRegistry.buildDomainSummaryTree());
            resp.put("sample_rows_locked", true);
        } else if (principal.roleLevel() < 100) {
            resp.put("access_tier", "SCHOLAR_SELF_SCOPED");
            resp.put("domains", catalogRegistry.buildDomainSummaryTree());
            resp.put("self_cascade", buildUserCascade(principal.username()));
        } else {
            resp.put("access_tier", "ADMIN_FULL_18TABLES_146COLS");
            resp.put("domains", catalogRegistry.buildDomainSummaryTree());
        }
        return resp;
    }
}
