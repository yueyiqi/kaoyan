package com.kaoyan.hub;

import com.kaoyan.hub.config.DualEngineHaDataSourceConfig;
import com.kaoyan.hub.config.KaoyanHaProperties;
import com.kaoyan.hub.controller.KaoyanAdminRbacAndDrilldownController;
import com.kaoyan.hub.controller.KaoyanPublicAndStudyController;
import com.kaoyan.hub.ha.ClusterEpochCoordinatorService;
import com.kaoyan.hub.ha.T2ColdBackupZstdArchiveService;
import com.kaoyan.hub.repository.DualEnginePortableSqlRepository;
import com.kaoyan.hub.schema.Schema18TableCatalogRegistry;
import com.kaoyan.hub.service.EidsDrilldownAndLineageService;
import com.kaoyan.hub.service.EidsSectionLinkageMatrixService;
import com.kaoyan.hub.service.RbacAccountManagementService;
import com.kaoyan.hub.service.StudyAndEbbinghausService;
import com.kaoyan.hub.service.UnauthPreviewTieredExposureService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * End-to-End JUnit 5 Integration Test Suite exercising REST Controllers, Portable SQL DDL/Upsert
 * Generation, T2 Cold-Backup Zstd Verification, 12-Section EIDS Linkage Matrix, and 35% Unauth Preview.
 */
class KaoyanControllerAndFullStackIntegrationTest {

    private KaoyanPublicAndStudyController publicController;
    private KaoyanAdminRbacAndDrilldownController adminController;
    private DualEnginePortableSqlRepository sqlRepository;
    private T2ColdBackupZstdArchiveService backupService;
    private EidsSectionLinkageMatrixService linkageService;
    private UnauthPreviewTieredExposureService previewService;

    @BeforeEach
    void setUp() {
        KaoyanHubApplication app = new KaoyanHubApplication();
        KaoyanHaProperties props = new KaoyanHaProperties();
        Schema18TableCatalogRegistry registry = new Schema18TableCatalogRegistry();
        DualEngineHaDataSourceConfig dsConfig = new DualEngineHaDataSourceConfig();
        ClusterEpochCoordinatorService coordinator = new ClusterEpochCoordinatorService(props, dsConfig);
        RbacAccountManagementService rbac = new RbacAccountManagementService();
        StudyAndEbbinghausService study = new StudyAndEbbinghausService(coordinator);
        EidsDrilldownAndLineageService drilldown = new EidsDrilldownAndLineageService(
                registry, study, rbac, coordinator);

        publicController = new KaoyanPublicAndStudyController(
                app, props, registry, coordinator, rbac, study, drilldown);
        adminController = new KaoyanAdminRbacAndDrilldownController(
                rbac, drilldown, coordinator, dsConfig);
        sqlRepository = new DualEnginePortableSqlRepository(registry);
        backupService = new T2ColdBackupZstdArchiveService();
        linkageService = new EidsSectionLinkageMatrixService();
        previewService = new UnauthPreviewTieredExposureService();
    }

    @Test
    void verifyPublicHealthHaStatusAndVocabLookupControllers() {
        Map<String, Object> health = publicController.health();
        assertEquals(true, health.get("ok"));
        assertEquals(18, health.get("schema_tables"));
        assertEquals(146, health.get("schema_columns"));

        Map<String, Object> ha = publicController.haStatus();
        assertEquals(true, ha.get("ok"));
        assertEquals("KAOYAN-3NODE-HA-CLUSTER", ha.get("cluster_id"));

        Map<String, Object> lookup = publicController.lookupVocab("empirical");
        assertEquals(true, lookup.get("found"));
    }

    @Test
    void verifyAdminDrilldownAndClusterControlControllers() {
        ResponseEntity<Map<String, Object>> resp = adminController.adminDbDrilldown(
                "DOM_04_RBAC_SECURITY", "sys_users", null, null, "admin", "username", 1, 20);
        assertEquals(HttpStatus.OK, resp.getStatusCode());
        assertNotNull(resp.getBody());
        assertEquals("L4_TABLE_ROWS", resp.getBody().get("drilldown_layer"));

        ResponseEntity<Map<String, Object>> failoverResp = adminController.clusterControl(
                Map.of("action", "FAILOVER_SQLITE_WAL"));
        assertEquals(HttpStatus.OK, failoverResp.getStatusCode());
        assertEquals(DualEngineHaDataSourceConfig.ENGINE_SQLITE_WAL,
                failoverResp.getBody().get("active_route"));
    }

    @Test
    void verifyPortableSqlDdlAndT2ZstdBackupIntegrity() {
        Map<String, Object> ddlReport = sqlRepository.buildFullDdlParityReport();
        assertEquals(18, ddlReport.get("total_tables_verified"));
        assertEquals(146, ddlReport.get("total_columns_verified"));

        String upsertSql = sqlRepository.generatePortableUpsertSql("user_vocab_ledger");
        assertTrue(upsertSql.contains("ON CONFLICT (id) DO UPDATE SET"));

        Map<String, Object> drill = backupService.runColdOffloadDrill("W1");
        assertEquals(true, drill.get("ok"));
        assertEquals(0, drill.get("rpo_guaranteed_seconds"));
    }

    @Test
    void verify12SectionEidsLinkageAnd35PercentUnauthPreviewPolicy() {
        Map<String, Object> linkage = linkageService.buildLinkageSummaryPayload();
        assertEquals(12, linkage.get("total_linked_sections"));
        assertEquals("user_vocab_ledger",
                linkageService.findTargetBySectionId("KPI_02_EBBINGHAUS_DUE").tableName());

        Map<String, Object> guestPolicy = previewService.evaluateViewportExposurePolicy(10, "daylight");
        assertEquals(0.35, guestPolicy.get("visible_content_ratio"));
        assertEquals("blur(6px)", guestPolicy.get("css_blur_filter"));

        Map<String, Object> adminPolicy = previewService.evaluateViewportExposurePolicy(100, "midnight");
        assertEquals(1.00, adminPolicy.get("visible_content_ratio"));
        assertEquals("none", adminPolicy.get("css_blur_filter"));
    }
}
