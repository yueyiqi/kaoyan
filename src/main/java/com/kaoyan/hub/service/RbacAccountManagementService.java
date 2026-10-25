package com.kaoyan.hub.service;

import com.kaoyan.hub.domain.KaoyanOntologyAxioms;
import com.kaoyan.hub.middleware.ZeroTrustRbacAndIdempotencyFilter;
import org.springframework.stereotype.Service;

import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.atomic.AtomicLong;

/**
 * 5-Table Zero-Trust RBAC Account & Password Management Service (DOM_04_RBAC_SECURITY).
 *
 * Implements:
 * - PBKDF2-HMAC-SHA256 (10,000 iterations) password derivation & verification
 * - Zero-memory password masking ({@code ********}, {@code autocomplete="new-password"})
 * - Role hierarchy enforcement: GUEST (L10) < SCHOLAR (L50) < ADMIN (L100)
 * - Self-lockout guard (HTTP 422 equivalent {@link IllegalArgumentException})
 * - Full audit trail in {@code sys_rbac_audit_log}
 */
@Service
public class RbacAccountManagementService {

    public record AuthenticatedPrincipal(
            String username,
            String displayName,
            String roleCode,
            int roleLevel,
            boolean authenticated
    ) {}

    private static class UserAccountRecord {
        long userId;
        String username;
        String displayName;
        String roleCode;
        int roleLevel;
        String accountStatus;
        String passwordSalt;
        String passwordHash;
        int zeroMemoryEnforced = 1;
        String lastLoginAt;
        String updatedAt;
    }

    private final Map<String, UserAccountRecord> usersByUsername = new ConcurrentHashMap<>();
    private final Map<String, String> activeTokensToUsername = new ConcurrentHashMap<>();
    private final List<Map<String, Object>> auditLogs = new CopyOnWriteArrayList<>();
    private final AtomicLong userIdSeq = new AtomicLong(100L);
    private final AtomicLong auditIdSeq = new AtomicLong(500L);

    public RbacAccountManagementService() {
        seedDefaultAccounts();
    }

    private void seedDefaultAccounts() {
        createInternalUser("admin", "Platform Chief Admin (平台总控管理员)", "ADMIN", 100, "Admin@Kaoyan2026!");
        createInternalUser("elena", "Elena Scholar Lead (研友主账号)", "SCHOLAR", 50, "Elena@Study2026!");
        createInternalUser("kaoyan_vip", "VIP Intensive Reader (冲刺精读学员)", "SCHOLAR", 50, "Vip@Kaoyan2026!");
        recordAuditLog("system", "ADMIN", "RBAC_SEED_INIT", "sys_users", "ALLOW", "trc-boot-0001");
    }

    private void createInternalUser(
            String username, String displayName, String roleCode, int roleLevel, String rawPassword) {
        UserAccountRecord rec = new UserAccountRecord();
        rec.userId = userIdSeq.incrementAndGet();
        rec.username = username;
        rec.displayName = displayName;
        rec.roleCode = roleCode;
        rec.roleLevel = roleLevel;
        rec.accountStatus = "ACTIVE";
        rec.passwordSalt = "salt-" + username + "-v6";
        rec.passwordHash = pbkdf2Hex(rawPassword, rec.passwordSalt, 10000);
        rec.lastLoginAt = Instant.now().toString();
        rec.updatedAt = rec.lastLoginAt;
        usersByUsername.put(username, rec);
    }

    public static String pbkdf2Hex(String password, String salt, int iterations) {
        try {
            PBEKeySpec spec = new PBEKeySpec(
                    password.toCharArray(),
                    salt.getBytes(StandardCharsets.UTF_8),
                    iterations,
                    256);
            SecretKeyFactory skf = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256");
            byte[] hash = skf.generateSecret(spec).getEncoded();
            spec.clearPassword();
            return HexFormat.of().formatHex(hash);
        } catch (Exception e) {
            throw new IllegalStateException("PBKDF2WithHmacSHA256 failure", e);
        }
    }

    public Map<String, Object> authenticate(String username, String rawPassword, String traceId) {
        if (username == null || rawPassword == null) {
            throw new SecurityException("Username and password are required");
        }
        UserAccountRecord user = usersByUsername.get(username.trim());
        if (user == null || !"ACTIVE".equalsIgnoreCase(user.accountStatus)) {
            recordAuditLog(username, "GUEST", "AUTH_LOGIN_FAIL", username, "DENY", traceId);
            throw new SecurityException("Invalid credentials or disabled account");
        }
        String candidateHash = pbkdf2Hex(rawPassword, user.passwordSalt, 10000);
        if (!candidateHash.equals(user.passwordHash)) {
            recordAuditLog(username, user.roleCode, "AUTH_LOGIN_BAD_PWD", username, "DENY", traceId);
            throw new SecurityException("Invalid credentials");
        }
        user.lastLoginAt = Instant.now().toString();
        String token = "ky6-" + user.roleCode.toLowerCase() + "-" + UUID.randomUUID();
        activeTokensToUsername.put(token, user.username);
        recordAuditLog(user.username, user.roleCode, "AUTH_LOGIN_SUCCESS", user.username, "ALLOW", traceId);

        Map<String, Object> resp = new LinkedHashMap<>();
        resp.put("ok", true);
        resp.put("token", token);
        resp.put("username", user.username);
        resp.put("display_name", user.displayName);
        resp.put("role_code", user.roleCode);
        resp.put("role_level", user.roleLevel);
        resp.put("password_mask", ZeroTrustRbacAndIdempotencyFilter.PASSWORD_MASK);
        resp.put("zero_memory_enforced", true);
        return resp;
    }

    public AuthenticatedPrincipal resolvePrincipal(String token) {
        if (token == null || token.isBlank()) {
            return new AuthenticatedPrincipal("guest", "Anonymous Visitor", "GUEST", 10, false);
        }
        String uname = activeTokensToUsername.get(token.trim());
        if (uname == null) {
            return new AuthenticatedPrincipal("guest", "Anonymous Visitor", "GUEST", 10, false);
        }
        UserAccountRecord rec = usersByUsername.get(uname);
        if (rec == null || !"ACTIVE".equalsIgnoreCase(rec.accountStatus)) {
            return new AuthenticatedPrincipal("guest", "Anonymous Visitor", "GUEST", 10, false);
        }
        return new AuthenticatedPrincipal(rec.username, rec.displayName, rec.roleCode, rec.roleLevel, true);
    }

    public Map<String, Object> createAccountByAdmin(
            AuthenticatedPrincipal operator,
            String newUsername,
            String displayName,
            String roleCode,
            String rawPassword,
            String traceId) {
        if (operator.roleLevel() < KaoyanOntologyAxioms.LEVEL_ADMIN) {
            throw new SecurityException("Admin privilege required");
        }
        validatePasswordPolicy(rawPassword);
        String cleanUser = newUsername != null ? newUsername.trim() : "";
        if (cleanUser.length() < 3 || usersByUsername.containsKey(cleanUser)) {
            throw new IllegalArgumentException("Username invalid or already exists: " + cleanUser);
        }
        int level = "ADMIN".equalsIgnoreCase(roleCode) ? 100 : 50;
        createInternalUser(cleanUser, displayName != null ? displayName : cleanUser,
                roleCode.toUpperCase(), level, rawPassword);
        recordAuditLog(operator.username(), operator.roleCode(), "CREATE_USER", cleanUser, "ALLOW", traceId);
        return getSanitizedUserByUsername(cleanUser);
    }

    public Map<String, Object> updateAccountRoleOrStatus(
            AuthenticatedPrincipal operator,
            String targetUsername,
            String newRoleCode,
            String newStatus,
            String traceId) {
        KaoyanOntologyAxioms.assertAxiom4RbacMutation(
                operator.roleLevel(), operator.username(), targetUsername, newRoleCode, newStatus);
        UserAccountRecord rec = usersByUsername.get(targetUsername);
        if (rec == null) {
            throw new IllegalArgumentException("Target user not found: " + targetUsername);
        }
        rec.roleCode = newRoleCode.toUpperCase();
        rec.roleLevel = "ADMIN".equalsIgnoreCase(rec.roleCode) ? 100 : 50;
        rec.accountStatus = newStatus.toUpperCase();
        rec.updatedAt = Instant.now().toString();
        recordAuditLog(operator.username(), operator.roleCode(),
                "UPDATE_ROLE_STATUS:" + rec.roleCode + "/" + rec.accountStatus, targetUsername, "ALLOW", traceId);
        return getSanitizedUserByUsername(targetUsername);
    }

    public void resetOrChangePassword(
            AuthenticatedPrincipal operator,
            String targetUsername,
            String currentPasswordOrNull,
            String newPassword,
            String traceId) {
        validatePasswordPolicy(newPassword);
        UserAccountRecord rec = usersByUsername.get(targetUsername);
        if (rec == null) {
            throw new IllegalArgumentException("User not found: " + targetUsername);
        }
        boolean isAdminReset = operator.roleLevel() >= KaoyanOntologyAxioms.LEVEL_ADMIN
                && (currentPasswordOrNull == null || currentPasswordOrNull.isBlank());
        if (!isAdminReset) {
            String verifyHash = pbkdf2Hex(
                    currentPasswordOrNull != null ? currentPasswordOrNull : "", rec.passwordSalt, 10000);
            if (!verifyHash.equals(rec.passwordHash)) {
                throw new SecurityException("Current password verification failed");
            }
        }
        rec.passwordSalt = "salt-" + rec.username + "-" + UUID.randomUUID().toString().substring(0, 8);
        rec.passwordHash = pbkdf2Hex(newPassword, rec.passwordSalt, 10000);
        rec.updatedAt = Instant.now().toString();
        recordAuditLog(operator.username(), operator.roleCode(), "PASSWORD_ROTATED", targetUsername, "ALLOW", traceId);
    }

    private void validatePasswordPolicy(String pwd) {
        if (pwd == null || pwd.length() < 8) {
            throw new IllegalArgumentException("Password must be at least 8 characters");
        }
    }

    public List<Map<String, Object>> listSanitizedUsers() {
        List<Map<String, Object>> list = new ArrayList<>();
        for (UserAccountRecord rec : usersByUsername.values()) {
            list.add(toSanitizedMap(rec));
        }
        return list;
    }

    public Map<String, Object> getSanitizedUserByUsername(String username) {
        UserAccountRecord rec = usersByUsername.get(username);
        return rec != null ? toSanitizedMap(rec) : Map.of();
    }

    private Map<String, Object> toSanitizedMap(UserAccountRecord rec) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("user_id", rec.userId);
        m.put("username", rec.username);
        m.put("display_name", rec.displayName);
        m.put("role_code", rec.roleCode);
        m.put("role_level", rec.roleLevel);
        m.put("account_status", rec.accountStatus);
        m.put("password_hash", ZeroTrustRbacAndIdempotencyFilter.PASSWORD_MASK);
        m.put("password_salt", ZeroTrustRbacAndIdempotencyFilter.PASSWORD_MASK);
        m.put("zero_memory_enforced", rec.zeroMemoryEnforced);
        m.put("last_login_at", rec.lastLoginAt);
        m.put("updated_at", rec.updatedAt);
        return m;
    }

    public void recordAuditLog(
            String actor, String role, String action, String target, String outcome, String traceId) {
        Map<String, Object> log = new LinkedHashMap<>();
        log.put("audit_id", auditIdSeq.incrementAndGet());
        log.put("actor_username", actor != null ? actor : "guest");
        log.put("actor_role", role != null ? role : "GUEST");
        log.put("action_type", action);
        log.put("target_entity", target);
        log.put("decision_outcome", outcome);
        log.put("client_ip_hash", "sha256:loopback");
        log.put("trace_id", traceId != null ? traceId : "trc-internal");
        log.put("created_at", Instant.now().toString());
        auditLogs.add(log);
    }

    public List<Map<String, Object>> getAuditLogs() {
        return new ArrayList<>(auditLogs);
    }
}
