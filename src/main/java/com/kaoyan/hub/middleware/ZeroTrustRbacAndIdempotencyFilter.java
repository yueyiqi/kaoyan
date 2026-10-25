package com.kaoyan.hub.middleware;

import com.kaoyan.hub.domain.KaoyanOntologyAxioms;
import com.kaoyan.hub.service.RbacAccountManagementService;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Middleware Layers 3, 4 & 5:
 * - Layer 3: Zero-Trust RBAC Guard (GUEST L10 / SCHOLAR L50 / ADMIN L100) enforcing {@code require_admin}
 *   on all {@code /api/admin/**} endpoints with audit trail recording.
 * - Layer 4: Idempotency Key SHA-256 Fingerprinting ({@code X-Idempotency-Key}) & HTTP 409 Conflict Guard.
 * - Layer 5: Zero-Memory Credential Redaction Helper ({@link #maskSensitiveRowFields(Map)}).
 */
@Component
@Order(Ordered.HIGHEST_PRECEDENCE + 10)
public class ZeroTrustRbacAndIdempotencyFilter extends OncePerRequestFilter {

    public static final String ATTR_AUTH_SESSION = "kaoyan.auth_session";
    public static final String PASSWORD_MASK = "********";

    private static final Set<String> SENSITIVE_KEYS = Set.of(
            "password", "password_hash", "password_salt", "secret", "session_token", "token_hash"
    );

    private final RbacAccountManagementService rbacService;
    private final Map<String, String> idempotencyLedger = new ConcurrentHashMap<>();

    public ZeroTrustRbacAndIdempotencyFilter(RbacAccountManagementService rbacService) {
        this.rbacService = rbacService;
    }

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain) throws ServletException, IOException {

        String token = extractBearerOrHeaderToken(request);
        RbacAccountManagementService.AuthenticatedPrincipal principal = rbacService.resolvePrincipal(token);
        request.setAttribute(ATTR_AUTH_SESSION, principal);

        String uri = request.getRequestURI() != null ? request.getRequestURI() : "";
        String traceId = String.valueOf(request.getAttribute(TraceAndScannerDefenseFilter.ATTR_TRACE_ID));

        // Layer 3: Strict Admin RBAC Gate on /api/admin/**
        if (uri.startsWith("/api/admin/")) {
            if (principal.roleLevel() < KaoyanOntologyAxioms.LEVEL_ADMIN) {
                int status = principal.roleLevel() <= KaoyanOntologyAxioms.LEVEL_GUEST
                        ? HttpServletResponse.SC_UNAUTHORIZED
                        : HttpServletResponse.SC_FORBIDDEN;
                rbacService.recordAuditLog(
                        principal.username(), principal.roleCode(),
                        "ADMIN_API_BLOCKED", uri, "DENY_" + status, traceId);
                response.setStatus(status);
                response.setContentType("application/json;charset=UTF-8");
                response.getWriter().write(String.format(
                        "{\"ok\":false,\"status\":%d,\"error\":\"Admin privilege (L100) required\",\"role\":\"%s\",\"trace_id\":\"%s\"}",
                        status, principal.roleCode(), traceId));
                return;
            }
        }

        // Layer 4: Idempotency Key SHA-256 Conflict Check on Mutating Requests
        if ("POST".equalsIgnoreCase(request.getMethod()) || "PUT".equalsIgnoreCase(request.getMethod())) {
            String idemKey = request.getHeader("X-Idempotency-Key");
            if (idemKey != null && !idemKey.isBlank()) {
                String payloadSig = sha256Hex(request.getMethod() + ":" + uri + ":" + principal.username());
                String validation = checkOrRegisterIdempotency(idemKey.trim(), payloadSig);
                if ("CONFLICT".equals(validation)) {
                    response.setStatus(HttpServletResponse.SC_CONFLICT);
                    response.setContentType("application/json;charset=UTF-8");
                    response.getWriter().write(String.format(
                            "{\"ok\":false,\"status\":409,\"error\":\"Idempotency key payload mismatch\",\"idempotency_key\":\"%s\"}",
                            idemKey.trim()));
                    return;
                }
                response.setHeader("X-Idempotency-Status", validation);
            }
        }

        filterChain.doFilter(request, response);
    }

    /**
     * Checks or registers an idempotency key. Returns {@code NEW}, {@code REPLAY}, or {@code CONFLICT}.
     */
    public String checkOrRegisterIdempotency(String idemKey, String payloadSha256) {
        String existing = idempotencyLedger.putIfAbsent(idemKey, payloadSha256);
        if (existing == null) {
            return "NEW";
        }
        return existing.equals(payloadSha256) ? "REPLAY" : "CONFLICT";
    }

    /**
     * Layer 5: Zero-Memory Credential Redaction — masks any sensitive password/hash/salt fields in row maps.
     */
    public static Map<String, Object> maskSensitiveRowFields(Map<String, Object> rawRow) {
        if (rawRow == null) {
            return Map.of();
        }
        Map<String, Object> clean = new LinkedHashMap<>();
        for (Map.Entry<String, Object> entry : rawRow.entrySet()) {
            String key = entry.getKey();
            String lower = key != null ? key.toLowerCase() : "";
            if (SENSITIVE_KEYS.contains(lower) || lower.contains("password") || lower.contains("salt")) {
                clean.put(key, PASSWORD_MASK);
            } else {
                clean.put(key, entry.getValue());
            }
        }
        return clean;
    }

    public static String sha256Hex(String input) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] digest = md.digest((input != null ? input : "").getBytes(StandardCharsets.UTF_8));
            return HexFormat.of().formatHex(digest);
        } catch (Exception e) {
            throw new IllegalStateException("SHA-256 unavailable", e);
        }
    }

    private String extractBearerOrHeaderToken(HttpServletRequest request) {
        String auth = request.getHeader("Authorization");
        if (auth != null && auth.toLowerCase().startsWith("bearer ")) {
            return auth.substring(7).trim();
        }
        String custom = request.getHeader("X-Kaoyan-Token");
        if (custom != null && !custom.isBlank()) {
            return custom.trim();
        }
        return request.getParameter("token");
    }
}
