package com.kaoyan.hub.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

import java.util.ArrayList;
import java.util.List;

/**
 * Strongly-typed configuration properties for KaoyanEnglish Hub Dual-Engine HA & 3-Node Cluster.
 * Bound to prefix {@code kaoyan.ha} in {@code application.yml}.
 */
@ConfigurationProperties(prefix = "kaoyan.ha")
public class KaoyanHaProperties {

    private String nodeId = "W1-DOCKER-PRIMARY";
    private String activeEngine = "DUAL_PG18_SQLITE_WAL";
    private long failoverThresholdMs = 5L;
    private int rpoSeconds = 0;
    private int rtoSeconds = 3;

    private final PostgresConfig postgres = new PostgresConfig();
    private final SqliteConfig sqlite = new SqliteConfig();
    private final ClusterConfig cluster = new ClusterConfig();
    private final SecurityConfig security = new SecurityConfig();

    public String getNodeId() {
        return nodeId;
    }

    public void setNodeId(String nodeId) {
        this.nodeId = nodeId;
    }

    public String getActiveEngine() {
        return activeEngine;
    }

    public void setActiveEngine(String activeEngine) {
        this.activeEngine = activeEngine;
    }

    public long getFailoverThresholdMs() {
        return failoverThresholdMs;
    }

    public void setFailoverThresholdMs(long failoverThresholdMs) {
        this.failoverThresholdMs = failoverThresholdMs;
    }

    public int getRpoSeconds() {
        return rpoSeconds;
    }

    public void setRpoSeconds(int rpoSeconds) {
        this.rpoSeconds = rpoSeconds;
    }

    public int getRtoSeconds() {
        return rtoSeconds;
    }

    public void setRtoSeconds(int rtoSeconds) {
        this.rtoSeconds = rtoSeconds;
    }

    public PostgresConfig getPostgres() {
        return postgres;
    }

    public SqliteConfig getSqlite() {
        return sqlite;
    }

    public ClusterConfig getCluster() {
        return cluster;
    }

    public SecurityConfig getSecurity() {
        return security;
    }

    public static class PostgresConfig {
        private String jdbcUrl = "jdbc:postgresql://127.0.0.1:5432/kaoyan_hub";
        private String username = "kaoyan_app";
        private String password = "KaoyanPg18HaPass";
        private int maxPoolSize = 16;

        public String getJdbcUrl() {
            return jdbcUrl;
        }

        public void setJdbcUrl(String jdbcUrl) {
            this.jdbcUrl = jdbcUrl;
        }

        public String getUsername() {
            return username;
        }

        public void setUsername(String username) {
            this.username = username;
        }

        public String getPassword() {
            return password;
        }

        public void setPassword(String password) {
            this.password = password;
        }

        public int getMaxPoolSize() {
            return maxPoolSize;
        }

        public void setMaxPoolSize(int maxPoolSize) {
            this.maxPoolSize = maxPoolSize;
        }
    }

    public static class SqliteConfig {
        private String jdbcUrl = "jdbc:sqlite:./db_volume/kaoyan_hub.sqlite3";
        private boolean walEnabled = true;
        private int busyTimeoutMs = 5000;

        public String getJdbcUrl() {
            return jdbcUrl;
        }

        public void setJdbcUrl(String jdbcUrl) {
            this.jdbcUrl = jdbcUrl;
        }

        public boolean isWalEnabled() {
            return walEnabled;
        }

        public void setWalEnabled(boolean walEnabled) {
            this.walEnabled = walEnabled;
        }

        public int getBusyTimeoutMs() {
            return busyTimeoutMs;
        }

        public void setBusyTimeoutMs(int busyTimeoutMs) {
            this.busyTimeoutMs = busyTimeoutMs;
        }
    }

    public static class ClusterConfig {
        private long epoch = 600L;
        private int quorumSize = 2;
        private List<PeerNode> peers = new ArrayList<>();

        public long getEpoch() {
            return epoch;
        }

        public void setEpoch(long epoch) {
            this.epoch = epoch;
        }

        public int getQuorumSize() {
            return quorumSize;
        }

        public void setQuorumSize(int quorumSize) {
            this.quorumSize = quorumSize;
        }

        public List<PeerNode> getPeers() {
            return peers;
        }

        public void setPeers(List<PeerNode> peers) {
            this.peers = peers;
        }
    }

    public static class PeerNode {
        private String nodeId;
        private String role;
        private String endpoint;

        public PeerNode() {
        }

        public PeerNode(String nodeId, String role, String endpoint) {
            this.nodeId = nodeId;
            this.role = role;
            this.endpoint = endpoint;
        }

        public String getNodeId() {
            return nodeId;
        }

        public void setNodeId(String nodeId) {
            this.nodeId = nodeId;
        }

        public String getRole() {
            return role;
        }

        public void setRole(String role) {
            this.role = role;
        }

        public String getEndpoint() {
            return endpoint;
        }

        public void setEndpoint(String endpoint) {
            this.endpoint = endpoint;
        }
    }

    public static class SecurityConfig {
        private int pbkdf2Iterations = 10000;
        private long tokenTtlSeconds = 86400L;
        private String zeroMemoryPasswordMask = "********";

        public int getPbkdf2Iterations() {
            return pbkdf2Iterations;
        }

        public void setPbkdf2Iterations(int pbkdf2Iterations) {
            this.pbkdf2Iterations = pbkdf2Iterations;
        }

        public long getTokenTtlSeconds() {
            return tokenTtlSeconds;
        }

        public void setTokenTtlSeconds(long tokenTtlSeconds) {
            this.tokenTtlSeconds = tokenTtlSeconds;
        }

        public String getZeroMemoryPasswordMask() {
            return zeroMemoryPasswordMask;
        }

        public void setZeroMemoryPasswordMask(String zeroMemoryPasswordMask) {
            this.zeroMemoryPasswordMask = zeroMemoryPasswordMask;
        }
    }
}
