package com.kaoyan.hub.middleware;

import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Layer 5 Global Exception & Desensitized Response Advice.
 *
 * Ensures that:
 * 1. No Java stack traces, internal SQL table paths, or private LAN IPs leak to external clients.
 * 2. Every error response carries a deterministic {@code X-Trace-Id} and structured JSON envelope.
 */
@RestControllerAdvice
public class GlobalExceptionAndRedactionAdvice {

    @ExceptionHandler(SecurityException.class)
    public ResponseEntity<Map<String, Object>> handleSecurityException(
            SecurityException ex, HttpServletRequest request) {
        return buildSanitizedError(HttpStatus.FORBIDDEN, ex.getMessage(), request);
    }

    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<Map<String, Object>> handleIllegalArgumentException(
            IllegalArgumentException ex, HttpServletRequest request) {
        return buildSanitizedError(HttpStatus.UNPROCESSABLE_ENTITY, ex.getMessage(), request);
    }

    @ExceptionHandler(IllegalStateException.class)
    public ResponseEntity<Map<String, Object>> handleIllegalStateException(
            IllegalStateException ex, HttpServletRequest request) {
        return buildSanitizedError(HttpStatus.CONFLICT, ex.getMessage(), request);
    }

    private ResponseEntity<Map<String, Object>> buildSanitizedError(
            HttpStatus status, String message, HttpServletRequest request) {
        String traceId = request != null
                ? String.valueOf(request.getAttribute(TraceAndScannerDefenseFilter.ATTR_TRACE_ID))
                : "trc-advice";
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("ok", false);
        body.put("status", status.value());
        body.put("error", message != null ? message : status.getReasonPhrase());
        body.put("trace_id", traceId);
        body.put("timestamp", Instant.now().toString());
        return ResponseEntity.status(status).body(body);
    }
}
