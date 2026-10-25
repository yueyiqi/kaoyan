package com.kaoyan.hub.service;

import org.springframework.stereotype.Service;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Bidirectional Requirements Traceability Matrix (RTM) & 4D Test Scenario Registry (Skill 205 / Skill 209).
 *
 * Maps every functional and non-functional requirement across Happy Path, Boundary, Exception,
 * and RBAC Security dimensions to concrete JUnit 5 and E2E verification probes.
 */
@Service
public class TestScenarioRtmVerificationService {

    public record RtmScenarioCase(
            String testId,
            String dimension4D,
            String requirementId,
            String scenarioTitleCn,
            String targetComponent,
            String expectedAssertion,
            String verificationProbe
    ) {}

    private final List<RtmScenarioCase> scenarioMatrix = List.of(
            new RtmScenarioCase("TC-HP-01", "HAPPY_PATH", "REQ-DB-18T-146C",
                    "五域十八表146字段全量元数据注册与100%前端曝光校验",
                    "Schema18TableCatalogRegistry",
                    "domains==5 && tables==18 && columns==146 && coverage==100.0%",
                    "KaoyanOntologyAndRbacServiceTest#verify18TablesAnd146ColumnsCatalogCompleteness"),
            new RtmScenarioCase("TC-HP-02", "HAPPY_PATH", "REQ-EBBINGHAUS-QUEUE",
                    "艾宾浩斯遗忘曲线紧迫度 U(w) 单调递减与复习队列排序",
                    "StudyAndEbbinghausService",
                    "U(m=0) > U(m=4) && queue sorted descending by ebbinghaus_urgency",
                    "KaoyanOntologyAndRbacServiceTest#verifyOntologyAxioms1To5Enforcement"),
            new RtmScenarioCase("TC-HP-03", "HAPPY_PATH", "REQ-EIDS-12SECTION-DRILL",
                    "顶部5张KPI卡片与Tab0..6全板块一键触发EIDS双模态下钻",
                    "EidsSectionLinkageMatrixService",
                    "12 UI sections mapped to domain/table/highlight_col/q with L4+L5 drawer",
                    "KaoyanControllerAndFullStackIntegrationTest#verify12SectionEidsLinkageAnd35PercentUnauthPreviewPolicy"),
            new RtmScenarioCase("TC-BD-01", "BOUNDARY", "REQ-AXIOM1-SPAN-OFFSET",
                    "三粒度高亮批注起止偏移量 [start, end) 边界与非法粒度拦截",
                    "KaoyanOntologyAxioms",
                    "0 <= start < end <= |C| allowed; start >= end or unknown granularity throws 422",
                    "KaoyanOntologyAndRbacServiceTest#verifyOntologyAxioms1To5Enforcement"),
            new RtmScenarioCase("TC-BD-02", "BOUNDARY", "REQ-UNAUTH-35PCT-BLUR",
                    "未登录访客35%黄金分割清晰预览与65%高斯模糊(6px)零布局偏移",
                    "UnauthPreviewTieredExposureService",
                    "GUEST visible_ratio==0.35 && blur==6px && CLS==0.00; ADMIN visible_ratio==1.0",
                    "KaoyanControllerAndFullStackIntegrationTest#verify12SectionEidsLinkageAnd35PercentUnauthPreviewPolicy"),
            new RtmScenarioCase("TC-EX-01", "EXCEPTION", "REQ-IDEMPOTENCY-409",
                    "同一 X-Idempotency-Key 携带篡改载荷触发 HTTP 409 Conflict 阻断",
                    "ZeroTrustRbacAndIdempotencyFilter",
                    "First call -> NEW; identical payload -> REPLAY; mutated payload -> CONFLICT (409)",
                    "KaoyanOntologyAndRbacServiceTest#verifyMiddlewareScannerDefenseAndIdempotencyConflict"),
            new RtmScenarioCase("TC-EX-02", "EXCEPTION", "REQ-DUAL-ENGINE-FAILOVER",
                    "PostgreSQL 18 主库断连时 <5ms 无损切换至 SQLite WAL 热备 (RPO=0)",
                    "DualEngineHaDataSourceConfig",
                    "active_route switches PG18_PRIMARY -> SQLITE_WAL_STANDBY with rpo_seconds==0",
                    "KaoyanDrilldownAndHaClusterTest#verifyDualEngineFailoverAndClusterEpochAdvance"),
            new RtmScenarioCase("TC-SEC-01", "RBAC_SECURITY", "REQ-ZERO-MEMORY-MASK",
                    "管理员与研友密码 PBKDF2-10000 哈希存储、全链路 ******** 掩码与零记忆属性",
                    "RbacAccountManagementService",
                    "password_hash=='********' && password_salt=='********' && autocomplete=='new-password'",
                    "KaoyanOntologyAndRbacServiceTest#verifyRbacAuthenticationZeroMemoryMaskingAndSelfLockout"),
            new RtmScenarioCase("TC-SEC-02", "RBAC_SECURITY", "REQ-ADMIN-SELF-LOCKOUT-422",
                    "管理员尝试降级或禁用自身当前活跃账号触发 Axiom-4 HTTP 422 刚性拦截",
                    "RbacAccountManagementService",
                    "updateAccountRoleOrStatus(admin -> SCHOLAR/DISABLED) throws IllegalArgumentException",
                    "KaoyanOntologyAndRbacServiceTest#verifyRbacAuthenticationZeroMemoryMaskingAndSelfLockout"),
            new RtmScenarioCase("TC-SEC-03", "RBAC_SECURITY", "REQ-SCANNER-DEFENSE-404",
                    "恶意扫描器探测 /.env、/.git、.sql、.php 触发二层中间件 HTTP 404 脱敏拦截",
                    "TraceAndScannerDefenseFilter",
                    "isMaliciousScannerProbe('/.env') == true && zero stacktrace leakage",
                    "KaoyanOntologyAndRbacServiceTest#verifyMiddlewareScannerDefenseAndIdempotencyConflict")
    );

    public List<RtmScenarioCase> getScenarioMatrix() {
        return scenarioMatrix;
    }

    public Map<String, Object> buildRtmReport() {
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("ok", true);
        out.put("total_scenarios", scenarioMatrix.size());
        out.put("dimensions_covered", List.of("HAPPY_PATH", "BOUNDARY", "EXCEPTION", "RBAC_SECURITY"));
        out.put("scenarios", scenarioMatrix);
        return out;
    }
}
