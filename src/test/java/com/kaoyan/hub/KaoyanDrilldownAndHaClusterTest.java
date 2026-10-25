package com.kaoyan.hub;

import com.kaoyan.hub.config.DualEngineHaDataSourceConfig;
import com.kaoyan.hub.config.KaoyanHaProperties;
import com.kaoyan.hub.ha.ClusterEpochCoordinatorService;
import com.kaoyan.hub.schema.Schema18TableCatalogRegistry;
import com.kaoyan.hub.service.EidsDrilldownAndLineageService;
import com.kaoyan.hub.service.RbacAccountManagementService;
import com.kaoyan.hub.service.StudyAndEbbinghausService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * JUnit 5 Verification Suite for EIDS 5-Layer Database Drill-Down (L1..L5),
 * Full-Text Search {@code q}, {@code highlight_col}, 7-Table User Cascade,
 * 3-Tier RBAC Lineage, and Dual-Engine HA + 3-Node Cluster Failover.
 */
class KaoyanDrilldownAndHaClusterTest {

    private Schema18TableCatalogRegistry catalogRegistry;
    private DualEngineHaDataSourceConfig dataSourceConfig;
    private ClusterEpochCoordinatorService coordinatorService;
    private RbacAccountManagementService rbacService;
    private StudyAndEbbinghausService studyService;
    private EidsDrilldownAndLineageService drilldownService;

    @BeforeEach
    void setUp() {
        KaoyanHaProperties props = new KaoyanHaProperties();
        catalogRegistry = new Schema18TableCatalogRegistry();
        dataSourceConfig = new DualEngineHaDataSourceConfig();
        coordinatorService = new ClusterEpochCoordinatorService(props, dataSourceConfig);
        rbacService = new RbacAccountManagementService();
        studyService = new StudyAndEbbinghausService(coordinatorService);
        drilldownService = new EidsDrilldownAndLineageService(
                catalogRegistry, studyService, rbacService, coordinatorService);
    }

    @Test
    void verify5LayerDrilldownAnd100PercentColumnExposure() {
        // L1 Overview
        Map<String, Object> l1 = drilldownService.executeAdminDrilldown(
                null, null, null, null, null, null, 1, 20);
        assertEquals("L1_OVERVIEW", l1.get("drilldown_layer"));
        assertEquals(18, l1.get("total_tables"));
        assertEquals(146, l1.get("total_columns"));
        assertEquals(146, l1.get("exposed_columns"));
        assertEquals("100.0%", l1.get("column_coverage_ratio"));

        // L4 Table Rows + highlight_col + keyword search q
        Map<String, Object> l4 = drilldownService.executeAdminDrilldown(
                "DOM_01_LEXEME_AND_PASSAGE", "syllabus_lexemes", null, null,
                "empirical", "word", 1, 20);
        assertEquals("L4_TABLE_ROWS", l4.get("drilldown_layer"));
        assertEquals("word", l4.get("highlight_col"));
        List<?> rows = (List<?>) l4.get("l4_rows");
        assertEquals(1, rows.size());

        // Invalid highlight_col must be rejected
        assertThrows(IllegalArgumentException.class, () ->
                drilldownService.executeAdminDrilldown(
                        "DOM_01_LEXEME_AND_PASSAGE", "syllabus_lexemes", null, null,
                        null, "non_existent_col", 1, 20));

        // L5 Single-Record Drawer on sys_users must redact password_hash & password_salt
        Map<String, Object> l5 = drilldownService.executeAdminDrilldown(
                "DOM_04_RBAC_SECURITY", "sys_users", "101", null, null, null, 1, 20);
        assertEquals("L5_RECORD_DRAWER", l5.get("drilldown_layer"));
        @SuppressWarnings("unchecked")
        Map<String, Object> record = (Map<String, Object>) l5.get("l5_record");
        assertNotNull(record);
        assertEquals("********", record.get("password_hash"));
        assertEquals("********", record.get("password_salt"));
    }

    @Test
    void verifyUserForeignKeyCascadeAnd3TierLineage() {
        Map<String, Object> cascadeResp = drilldownService.executeAdminDrilldown(
                null, null, null, "elena", null, null, 1, 20);
        assertEquals("L5_USER_CASCADE", cascadeResp.get("drilldown_layer"));
        @SuppressWarnings("unchecked")
        Map<String, Object> cascade = (Map<String, Object>) cascadeResp.get("user_cascade");
        assertNotNull(cascade);
        assertTrue(cascade.containsKey("user_vocab_ledger"));
        assertTrue(cascade.containsKey("annotation_spans"));

        // Verify 3-tier /api/db/lineage access control
        var guest = rbacService.resolvePrincipal(null);
        Map<String, Object> guestLineage = drilldownService.buildTieredLineageResponse(guest);
        assertEquals("GUEST_TEASER_SUMMARY", guestLineage.get("access_tier"));

        String adminToken = String.valueOf(
                rbacService.authenticate("admin", "Admin@Kaoyan2026!", "trc-test").get("token"));
        var admin = rbacService.resolvePrincipal(adminToken);
        Map<String, Object> adminLineage = drilldownService.buildTieredLineageResponse(admin);
        assertEquals("ADMIN_FULL_18TABLES_146COLS", adminLineage.get("access_tier"));
    }

    @Test
    void verifyDualEngineFailoverAndClusterEpochAdvance() {
        Map<String, Object> promoted = dataSourceConfig.promotePostgresPrimary("TEST_PROMOTE_PG18");
        assertEquals(DualEngineHaDataSourceConfig.ENGINE_PG18_PRIMARY, promoted.get("active_route"));

        Map<String, Object> failedOver = dataSourceConfig.triggerFailoverToSqliteWal("SIMULATED_PG18_NET_DROP");
        assertEquals(DualEngineHaDataSourceConfig.ENGINE_SQLITE_WAL, failedOver.get("active_route"));
        assertEquals(0, failedOver.get("rpo_seconds"));

        long oldEpoch = coordinatorService.getCurrentEpoch();
        long newEpoch = coordinatorService.advanceEpoch(oldEpoch + 1, "JUNIT_FAILOVER_DRILL");
        assertEquals(oldEpoch + 1, newEpoch);
    }
}
