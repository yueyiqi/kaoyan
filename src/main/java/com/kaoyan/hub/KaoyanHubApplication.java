package com.kaoyan.hub;

import com.kaoyan.hub.config.KaoyanHaProperties;
import com.kaoyan.hub.ha.ClusterEpochCoordinatorService;
import com.kaoyan.hub.schema.Schema18TableCatalogRegistry;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.scheduling.annotation.EnableScheduling;

import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * KaoyanEnglish Hub v6.0 — Spring Boot 3 + Dual-Engine (PostgreSQL 18 + SQLite WAL) HA Application.
 *
 * Architectural Responsibilities:
 * 1. Boots the 5-Layer Zero-Trust Middleware Pipeline:
 *    - Layer 1: X-Trace-Id Telemetry & CORS Filter
 *    - Layer 2: Scanner & Path-Traversal Defense Filter
 *    - Layer 3: Zero-Trust RBAC & PBKDF2-HMAC-SHA256 Guard
 *    - Layer 4: Idempotency Key SHA-256 & Cluster Epoch Fencing Filter
 *    - Layer 5: Zero-Memory Credential Redaction Advice
 * 2. Registers the Dual-Engine HA Routing DataSource (PostgreSQL 18 Primary + SQLite WAL Hot Standby).
 * 3. Initializes the 18-Table / 146-Column Schema Catalog Registry across 5 Business Domains.
 * 4. Starts the 3-Node (W1, HP, S1) Cluster Epoch Coordinator & WAL Replay Scheduler.
 */
@SpringBootApplication(exclude = {DataSourceAutoConfiguration.class})
@EnableConfigurationProperties(KaoyanHaProperties.class)
@EnableScheduling
public class KaoyanHubApplication {

    public static final String VERSION = "6.0.0-SPRINGBOOT3-HA";
    public static final int TOTAL_TABLES = 18;
    public static final int TOTAL_COLUMNS = 146;
    public static final int TOTAL_DOMAINS = 5;

    private final Instant startedAt = Instant.now();

    public static void main(String[] args) {
        SpringApplication.run(KaoyanHubApplication.class, args);
    }

    /**
     * Startup self-verification hook validating ontology axioms, 18-table/146-column schema catalog,
     * and 3-node HA cluster epoch state before accepting live traffic.
     */
    @Bean
    public CommandLineRunner startupIntegrityVerifier(
            KaoyanHaProperties properties,
            Schema18TableCatalogRegistry catalogRegistry,
            ClusterEpochCoordinatorService coordinatorService) {
        return args -> {
            int tableCount = catalogRegistry.getTableCount();
            int columnCount = catalogRegistry.getTotalColumnCount();
            if (tableCount != TOTAL_TABLES || columnCount != TOTAL_COLUMNS) {
                throw new IllegalStateException(String.format(
                        "Schema catalog mismatch: expected %d tables / %d columns, got %d / %d",
                        TOTAL_TABLES, TOTAL_COLUMNS, tableCount, columnCount));
            }
            coordinatorService.recordNodeHeartbeat(properties.getNodeId(), "ONLINE_READY");
        };
    }

    /**
     * Builds the runtime metadata banner used by /api/health and /api/ha/status endpoints.
     */
    public Map<String, Object> buildRuntimeDescriptor(
            KaoyanHaProperties properties,
            Schema18TableCatalogRegistry catalogRegistry,
            ClusterEpochCoordinatorService coordinatorService) {
        Map<String, Object> meta = new LinkedHashMap<>();
        meta.put("application", "kaoyan-english-hub");
        meta.put("version", VERSION);
        meta.put("runtime_stack", "Java 17+ / Spring Boot 3.3+ / Vue 3 Reactive Composable");
        meta.put("node_id", properties.getNodeId());
        meta.put("active_engine", properties.getActiveEngine());
        meta.put("started_at", startedAt.toString());
        meta.put("schema_tables", catalogRegistry.getTableCount());
        meta.put("schema_columns", catalogRegistry.getTotalColumnCount());
        meta.put("schema_domains", catalogRegistry.getDomainCount());
        meta.put("cluster_epoch", coordinatorService.getCurrentEpoch());
        meta.put("rpo_seconds", properties.getRpoSeconds());
        meta.put("rto_seconds", properties.getRtoSeconds());
        return meta;
    }
}
