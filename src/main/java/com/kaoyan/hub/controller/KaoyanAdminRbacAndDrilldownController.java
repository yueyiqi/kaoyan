package com.kaoyan.hub.controller;

import com.kaoyan.hub.config.DualEngineHaDataSourceConfig;
import com.kaoyan.hub.domain.KaoyanOntologyAxioms;
import com.kaoyan.hub.ha.ClusterEpochCoordinatorService;
import com.kaoyan.hub.middleware.TraceAndScannerDefenseFilter;
import com.kaoyan.hub.middleware.ZeroTrustRbacAndIdempotencyFilter;
import com.kaoyan.hub.service.EidsDrilldownAndLineageService;
import com.kaoyan.hub.service.RbacAccountManagementService;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

/**
 * Spring Boot 3 REST Controller for Zero-Trust Admin RBAC Account Management,
 * EIDS 5-Layer Database Drill-Down ({@code L1..L5}), and 3-Node HA Cluster Control.
 */
@RestController
public class KaoyanAdminRbacAndDrilldownController {

    private final RbacAccountManagementService rbacService;
    private final EidsDrilldownAndLineageService drilldownService;
    private final ClusterEpochCoordinatorService coordinatorService;
    private final DualEngineHaDataSourceConfig dataSourceConfig;

    public KaoyanAdminRbacAndDrilldownController(
            RbacAccountManagementService rbacService,
            EidsDrilldownAndLineageService drilldownService,
            ClusterEpochCoordinatorService coordinatorService,
            DualEngineHaDataSourceConfig dataSourceConfig) {
        this.rbacService = rbacService;
        this.drilldownService = drilldownService;
        this.coordinatorService = coordinatorService;
        this.dataSourceConfig = dataSourceConfig;
    }

    @GetMapping("/api/admin/users")
    public Map<String, Object> listUsers() {
        return Map.of(
                "ok", true,
                "users", rbacService.listSanitizedUsers(),
                "zero_memory_enforced", true
        );
    }

    @PostMapping("/api/admin/users")
    public ResponseEntity<Map<String, Object>> createUser(
            @RequestBody Map<String, Object> body,
            HttpServletRequest request) {
        RbacAccountManagementService.AuthenticatedPrincipal operator = extractPrincipal(request);
        String traceId = String.valueOf(request.getAttribute(TraceAndScannerDefenseFilter.ATTR_TRACE_ID));
        try {
            String username = String.valueOf(body.getOrDefault("username", ""));
            String displayName = String.valueOf(body.getOrDefault("display_name", username));
            String roleCode = String.valueOf(body.getOrDefault("role_code", "SCHOLAR"));
            String password = String.valueOf(body.getOrDefault("password", ""));
            Map<String, Object> created = rbacService.createAccountByAdmin(
                    operator, username, displayName, roleCode, password, traceId);
            return ResponseEntity.status(HttpStatus.CREATED).body(Map.of("ok", true, "user", created));
        } catch (IllegalArgumentException ex) {
            return ResponseEntity.unprocessableEntity().body(Map.of("ok", false, "error", ex.getMessage()));
        }
    }

    @PostMapping("/api/admin/users/role_status")
    public ResponseEntity<Map<String, Object>> updateRoleOrStatus(
            @RequestBody Map<String, Object> body,
            HttpServletRequest request) {
        RbacAccountManagementService.AuthenticatedPrincipal operator = extractPrincipal(request);
        String traceId = String.valueOf(request.getAttribute(TraceAndScannerDefenseFilter.ATTR_TRACE_ID));
        try {
            String targetUser = String.valueOf(body.getOrDefault("username", ""));
            String roleCode = String.valueOf(body.getOrDefault("role_code", "SCHOLAR"));
            String status = String.valueOf(body.getOrDefault("account_status", "ACTIVE"));
            Map<String, Object> updated = rbacService.updateAccountRoleOrStatus(
                    operator, targetUser, roleCode, status, traceId);
            return ResponseEntity.ok(Map.of("ok", true, "user", updated));
        } catch (IllegalArgumentException ex) {
            return ResponseEntity.unprocessableEntity().body(Map.of("ok", false, "error", ex.getMessage()));
        }
    }

    @PostMapping("/api/admin/users/password")
    public ResponseEntity<Map<String, Object>> adminResetPassword(
            @RequestBody Map<String, Object> body,
            HttpServletRequest request) {
        RbacAccountManagementService.AuthenticatedPrincipal operator = extractPrincipal(request);
        String traceId = String.valueOf(request.getAttribute(TraceAndScannerDefenseFilter.ATTR_TRACE_ID));
        try {
            String targetUser = String.valueOf(body.getOrDefault("username", ""));
            String newPassword = String.valueOf(body.getOrDefault("new_password", ""));
            rbacService.resetOrChangePassword(operator, targetUser, null, newPassword, traceId);
            return ResponseEntity.ok(Map.of(
                    "ok", true,
                    "username", targetUser,
                    "password_mask", ZeroTrustRbacAndIdempotencyFilter.PASSWORD_MASK,
                    "zero_memory_enforced", true
            ));
        } catch (IllegalArgumentException ex) {
            return ResponseEntity.unprocessableEntity().body(Map.of("ok", false, "error", ex.getMessage()));
        }
    }

    @PostMapping("/api/auth/password/change")
    public ResponseEntity<Map<String, Object>> selfChangePassword(
            @RequestBody Map<String, Object> body,
            HttpServletRequest request) {
        RbacAccountManagementService.AuthenticatedPrincipal operator = extractPrincipal(request);
        if (!operator.authenticated() || operator.roleLevel() <= KaoyanOntologyAxioms.LEVEL_GUEST) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(Map.of("ok", false, "error", "Authentication required"));
        }
        String traceId = String.valueOf(request.getAttribute(TraceAndScannerDefenseFilter.ATTR_TRACE_ID));
        try {
            String currentPwd = String.valueOf(body.getOrDefault("current_password", ""));
            String newPwd = String.valueOf(body.getOrDefault("new_password", ""));
            rbacService.resetOrChangePassword(operator, operator.username(), currentPwd, newPwd, traceId);
            return ResponseEntity.ok(Map.of(
                    "ok", true,
                    "username", operator.username(),
                    "password_mask", ZeroTrustRbacAndIdempotencyFilter.PASSWORD_MASK
            ));
        } catch (SecurityException ex) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN).body(Map.of("ok", false, "error", ex.getMessage()));
        } catch (IllegalArgumentException ex) {
            return ResponseEntity.unprocessableEntity().body(Map.of("ok", false, "error", ex.getMessage()));
        }
    }

    @GetMapping("/api/admin/db/drilldown")
    public ResponseEntity<Map<String, Object>> adminDbDrilldown(
            @RequestParam(name = "domain", required = false) String domain,
            @RequestParam(name = "table", required = false) String table,
            @RequestParam(name = "pk", required = false) String pk,
            @RequestParam(name = "user_id", required = false) String userId,
            @RequestParam(name = "q", required = false) String query,
            @RequestParam(name = "highlight_col", required = false) String highlightCol,
            @RequestParam(name = "page", defaultValue = "1") int page,
            @RequestParam(name = "page_size", defaultValue = "20") int pageSize) {
        try {
            Map<String, Object> payload = drilldownService.executeAdminDrilldown(
                    domain, table, pk, userId, query, highlightCol, page, pageSize);
            return ResponseEntity.ok(payload);
        } catch (IllegalArgumentException ex) {
            return ResponseEntity.badRequest().body(Map.of("ok", false, "error", ex.getMessage()));
        }
    }

    @PostMapping("/_cluster/control")
    public ResponseEntity<Map<String, Object>> clusterControl(@RequestBody Map<String, Object> body) {
        String action = String.valueOf(body.getOrDefault("action", "STATUS"));
        if ("FAILOVER_SQLITE_WAL".equalsIgnoreCase(action)) {
            return ResponseEntity.ok(dataSourceConfig.triggerFailoverToSqliteWal("CLUSTER_RPC_FAILOVER"));
        }
        if ("PROMOTE_PG18_PRIMARY".equalsIgnoreCase(action)) {
            return ResponseEntity.ok(dataSourceConfig.promotePostgresPrimary("CLUSTER_RPC_PROMOTE"));
        }
        if ("ADVANCE_EPOCH".equalsIgnoreCase(action)) {
            long proposed = ((Number) body.getOrDefault("epoch", coordinatorService.getCurrentEpoch() + 1)).longValue();
            long next = coordinatorService.advanceEpoch(proposed, "CLUSTER_CONTROL_ADVANCE");
            return ResponseEntity.ok(Map.of("ok", true, "current_epoch", next));
        }
        return ResponseEntity.ok(coordinatorService.buildCompleteHaStatus());
    }

    private RbacAccountManagementService.AuthenticatedPrincipal extractPrincipal(HttpServletRequest request) {
        Object attr = request.getAttribute(ZeroTrustRbacAndIdempotencyFilter.ATTR_AUTH_SESSION);
        if (attr instanceof RbacAccountManagementService.AuthenticatedPrincipal p) {
            return p;
        }
        return rbacService.resolvePrincipal(null);
    }
}
