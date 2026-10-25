package com.kaoyan.hub;

import com.kaoyan.hub.domain.KaoyanOntologyAxioms;
import com.kaoyan.hub.middleware.TraceAndScannerDefenseFilter;
import com.kaoyan.hub.middleware.ZeroTrustRbacAndIdempotencyFilter;
import com.kaoyan.hub.schema.Schema18TableCatalogRegistry;
import com.kaoyan.hub.service.RbacAccountManagementService;
import org.junit.jupiter.api.Test;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * JUnit 5 Verification Suite for Ontology Axioms (1..5), 18-Table/146-Column Schema Registry,
 * 5-Layer Middleware Defenses, and Zero-Trust RBAC Account Management.
 */
class KaoyanOntologyAndRbacServiceTest {

    @Test
    void verify18TablesAnd146ColumnsCatalogCompleteness() {
        Schema18TableCatalogRegistry registry = new Schema18TableCatalogRegistry();
        assertEquals(5, registry.getDomainCount(), "Must have 5 business domains (DOM_01..DOM_05)");
        assertEquals(18, registry.getTableCount(), "Must register all 18 tables");
        assertEquals(146, registry.getTotalColumnCount(), "Must register all 146 columns across 18 tables");
        assertNotNull(registry.getTableSpec("sys_users"));
        assertNotNull(registry.getTableSpec("ha_wal_replication_journal"));
    }

    @Test
    void verifyOntologyAxioms1To5Enforcement() {
        // Axiom 1: Valid span vs out-of-bounds span
        KaoyanOntologyAxioms.assertAxiom1SpanBoundary(0, 18, 120, "empirical anomaly", "phrase");
        assertThrows(IllegalArgumentException.class, () ->
                KaoyanOntologyAxioms.assertAxiom1SpanBoundary(25, 10, 120, "bad span", "phrase"));
        assertThrows(IllegalArgumentException.class, () ->
                KaoyanOntologyAxioms.assertAxiom1SpanBoundary(0, 10, 120, "bad granularity", "paragraph_blob"));

        // Axiom 2: Ebbinghaus urgency monotonically decreases with higher mastery
        double uMastery0 = KaoyanOntologyAxioms.computeAndAssertAxiom2Urgency(0, 35, 3.0);
        double uMastery4 = KaoyanOntologyAxioms.computeAndAssertAxiom2Urgency(4, 35, 3.0);
        assertTrue(uMastery0 > uMastery4, "Urgency at mastery 0 must exceed mastery 4");
        assertThrows(IllegalArgumentException.class, () ->
                KaoyanOntologyAxioms.computeAndAssertAxiom2Urgency(9, 10, 1.0));

        // Axiom 3: Essay cloze template auto-injection
        String cloze = KaoyanOntologyAxioms.ensureAxiom3ClozeTemplate(
                "Empirical anomalies accumulate until a paradigm shifts.", "paradigm shifts");
        assertTrue(cloze.contains("[KEY: paradigm shifts]"));

        // Axiom 4: Admin self-lockout protection
        assertThrows(IllegalArgumentException.class, () ->
                KaoyanOntologyAxioms.assertAxiom4RbacMutation(100, "admin", "admin", "SCHOLAR", "ACTIVE"));
        assertThrows(IllegalArgumentException.class, () ->
                KaoyanOntologyAxioms.assertAxiom4RbacMutation(100, "admin", "admin", "ADMIN", "DISABLED"));

        // Axiom 5: Cluster epoch fencing
        KaoyanOntologyAxioms.assertAxiom5EpochFencing(601L, 600L);
        assertThrows(IllegalStateException.class, () ->
                KaoyanOntologyAxioms.assertAxiom5EpochFencing(598L, 600L));
    }

    @Test
    void verifyRbacAuthenticationZeroMemoryMaskingAndSelfLockout() {
        RbacAccountManagementService rbac = new RbacAccountManagementService();

        Map<String, Object> loginResp = rbac.authenticate("admin", "Admin@Kaoyan2026!", "trc-junit-01");
        assertTrue((Boolean) loginResp.get("ok"));
        assertEquals("ADMIN", loginResp.get("role_code"));
        assertEquals(100, loginResp.get("role_level"));
        assertEquals("********", loginResp.get("password_mask"));

        String token = String.valueOf(loginResp.get("token"));
        RbacAccountManagementService.AuthenticatedPrincipal adminPrincipal = rbac.resolvePrincipal(token);
        assertTrue(adminPrincipal.authenticated());
        assertEquals(100, adminPrincipal.roleLevel());

        // Create new scholar account and verify password hash & salt are masked in sanitized view
        Map<String, Object> created = rbac.createAccountByAdmin(
                adminPrincipal, "junit_scholar", "JUnit Scholar", "SCHOLAR", "Scholar@2026!", "trc-junit-02");
        assertEquals("********", created.get("password_hash"));
        assertEquals("********", created.get("password_salt"));

        // Self-lockout attempt by admin must throw IllegalArgumentException (HTTP 422)
        assertThrows(IllegalArgumentException.class, () ->
                rbac.updateAccountRoleOrStatus(adminPrincipal, "admin", "ADMIN", "DISABLED", "trc-junit-03"));
    }

    @Test
    void verifyMiddlewareScannerDefenseAndIdempotencyConflict() {
        assertTrue(TraceAndScannerDefenseFilter.isMaliciousScannerProbe("/.env"));
        assertTrue(TraceAndScannerDefenseFilter.isMaliciousScannerProbe("/.git/config"));
        assertTrue(TraceAndScannerDefenseFilter.isMaliciousScannerProbe("/backup/dump.sql"));
        assertFalse(TraceAndScannerDefenseFilter.isMaliciousScannerProbe("/api/admin/db/drilldown"));

        RbacAccountManagementService rbac = new RbacAccountManagementService();
        ZeroTrustRbacAndIdempotencyFilter filter = new ZeroTrustRbacAndIdempotencyFilter(rbac);

        assertEquals("NEW", filter.checkOrRegisterIdempotency("idem-001", "sha-payload-a"));
        assertEquals("REPLAY", filter.checkOrRegisterIdempotency("idem-001", "sha-payload-a"));
        assertEquals("CONFLICT", filter.checkOrRegisterIdempotency("idem-001", "sha-payload-b"));
    }
}
