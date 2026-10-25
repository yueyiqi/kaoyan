package com.kaoyan.hub.middleware;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.List;
import java.util.UUID;

/**
 * Middleware Layers 1 & 2:
 * - Layer 1: Distributed Trace-Id Injection ({@code X-Trace-Id}), Latency Telemetry & CORS Policy.
 * - Layer 2: Scanner & Sensitive Dotfile Defense (blocks {@code /.env}, {@code /.git}, {@code .sql},
 *   {@code .php}, {@code wp-admin}, {@code actuator/heapdump} with sanitized JSON HTTP 404).
 */
@Component
@Order(Ordered.HIGHEST_PRECEDENCE)
public class TraceAndScannerDefenseFilter extends OncePerRequestFilter {

    public static final String ATTR_TRACE_ID = "kaoyan.trace_id";
    public static final String ATTR_START_NANOS = "kaoyan.start_nanos";

    private static final List<String> BLOCKED_SCANNER_PREFIXES = List.of(
            "/.env", "/.git", "/.svn", "/wp-admin", "/wp-login", "/phpmyadmin",
            "/actuator/heapdump", "/actuator/env", "/vendor/phpunit"
    );

    private static final List<String> BLOCKED_SCANNER_SUFFIXES = List.of(
            ".php", ".asp", ".aspx", ".jsp", ".sql", ".bak", ".sqlite3", ".zst"
    );

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain) throws ServletException, IOException {

        long startNanos = System.nanoTime();
        String incomingTrace = request.getHeader("X-Trace-Id");
        String traceId = (incomingTrace != null && !incomingTrace.isBlank())
                ? incomingTrace.trim()
                : "trc-" + UUID.randomUUID().toString().substring(0, 12);

        request.setAttribute(ATTR_TRACE_ID, traceId);
        request.setAttribute(ATTR_START_NANOS, startNanos);

        response.setHeader("X-Trace-Id", traceId);
        response.setHeader("X-Content-Type-Options", "nosniff");
        response.setHeader("X-Frame-Options", "SAMEORIGIN");
        response.setHeader("Cache-Control", "no-store, no-cache, must-revalidate");
        response.setHeader("Access-Control-Allow-Origin", "*");
        response.setHeader("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS");
        response.setHeader("Access-Control-Allow-Headers",
                "Authorization, Content-Type, X-Trace-Id, X-Idempotency-Key, X-Cluster-Epoch");

        if ("OPTIONS".equalsIgnoreCase(request.getMethod())) {
            response.setStatus(HttpServletResponse.SC_NO_CONTENT);
            return;
        }

        String uri = request.getRequestURI() != null ? request.getRequestURI().toLowerCase() : "";
        if (isMaliciousScannerProbe(uri)) {
            response.setStatus(HttpServletResponse.SC_NOT_FOUND);
            response.setContentType("application/json;charset=UTF-8");
            response.getWriter().write(String.format(
                    "{\"ok\":false,\"status\":404,\"error\":\"Resource not found\",\"trace_id\":\"%s\"}",
                    traceId));
            return;
        }

        try {
            filterChain.doFilter(request, response);
        } finally {
            long elapsedUs = (System.nanoTime() - startNanos) / 1_000L;
            response.setHeader("X-Runtime-Latency-Us", String.valueOf(elapsedUs));
        }
    }

    public static boolean isMaliciousScannerProbe(String lowerUri) {
        if (lowerUri == null || lowerUri.isEmpty()) {
            return false;
        }
        if (lowerUri.contains("..")) {
            return true;
        }
        for (String prefix : BLOCKED_SCANNER_PREFIXES) {
            if (lowerUri.startsWith(prefix)) {
                return true;
            }
        }
        for (String suffix : BLOCKED_SCANNER_SUFFIXES) {
            if (lowerUri.endsWith(suffix)) {
                return true;
            }
        }
        return false;
    }
}
