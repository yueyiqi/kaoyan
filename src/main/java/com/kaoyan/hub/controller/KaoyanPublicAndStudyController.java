package com.kaoyan.hub.controller;

import com.kaoyan.hub.KaoyanHubApplication;
import com.kaoyan.hub.config.KaoyanHaProperties;
import com.kaoyan.hub.ha.ClusterEpochCoordinatorService;
import com.kaoyan.hub.middleware.TraceAndScannerDefenseFilter;
import com.kaoyan.hub.middleware.ZeroTrustRbacAndIdempotencyFilter;
import com.kaoyan.hub.schema.Schema18TableCatalogRegistry;
import com.kaoyan.hub.service.EidsDrilldownAndLineageService;
import com.kaoyan.hub.service.RbacAccountManagementService;
import com.kaoyan.hub.service.StudyAndEbbinghausService;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Spring Boot 3 REST Controller for Public Health, HA Cluster Telemetry, Authentication,
 * Deep Reading Progress, Multi-Granularity Annotations, Ebbinghaus Vocab, and Tiered Lineage.
 */
@RestController
public class KaoyanPublicAndStudyController {

    private final KaoyanHubApplication app;
    private final KaoyanHaProperties properties;
    private final Schema18TableCatalogRegistry catalogRegistry;
    private final ClusterEpochCoordinatorService coordinatorService;
    private final RbacAccountManagementService rbacService;
    private final StudyAndEbbinghausService studyService;
    private final EidsDrilldownAndLineageService drilldownService;

    public KaoyanPublicAndStudyController(
            KaoyanHubApplication app,
            KaoyanHaProperties properties,
            Schema18TableCatalogRegistry catalogRegistry,
            ClusterEpochCoordinatorService coordinatorService,
            RbacAccountManagementService rbacService,
            StudyAndEbbinghausService studyService,
            EidsDrilldownAndLineageService drilldownService) {
        this.app = app;
        this.properties = properties;
        this.catalogRegistry = catalogRegistry;
        this.coordinatorService = coordinatorService;
        this.rbacService = rbacService;
        this.studyService = studyService;
        this.drilldownService = drilldownService;
    }

    @GetMapping("/api/health")
    public Map<String, Object> health() {
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("ok", true);
        out.put("status", "UP");
        out.putAll(app.buildRuntimeDescriptor(properties, catalogRegistry, coordinatorService));
        return out;
    }

    @GetMapping("/api/ha/status")
    public Map<String, Object> haStatus() {
        return coordinatorService.buildCompleteHaStatus();
    }

    @GetMapping("/api/state")
    public Map<String, Object> fullWorkspaceState(HttpServletRequest request) {
        RbacAccountManagementService.AuthenticatedPrincipal principal = extractPrincipal(request);
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("ok", true);
        out.put("viewer", Map.of(
                "username", principal.username(),
                "role_code", principal.roleCode(),
                "role_level", principal.roleLevel(),
                "authenticated", principal.authenticated()
        ));
        out.put("passages", studyService.getTableRows("exam_passages"));
        out.put("paragraphs", studyService.getTableRows("passage_paragraphs"));
        out.put("vocab_queue", studyService.getVocabQueueSortedByUrgency());
        out.put("annotations", studyService.getTableRows("annotation_spans"));
        out.put("essay_snippets", studyService.getTableRows("essay_corpus_snippets"));
        out.put("ha_status", coordinatorService.buildCompleteHaStatus());
        return out;
    }

    @PostMapping("/api/auth/login")
    public ResponseEntity<Map<String, Object>> login(
            @RequestBody Map<String, Object> body,
            HttpServletRequest request) {
        String traceId = String.valueOf(request.getAttribute(TraceAndScannerDefenseFilter.ATTR_TRACE_ID));
        try {
            String username = String.valueOf(body.getOrDefault("username", ""));
            String password = String.valueOf(body.getOrDefault("password", body.getOrDefault("passcode", "")));
            return ResponseEntity.ok(rbacService.authenticate(username, password, traceId));
        } catch (SecurityException ex) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(Map.of("ok", false, "error", ex.getMessage(), "trace_id", traceId));
        }
    }

    @GetMapping("/api/vocab/lookup")
    public Map<String, Object> lookupVocab(@RequestParam(name = "word", defaultValue = "empirical") String word) {
        String clean = word.trim().toLowerCase();
        List<Map<String, Object>> matches = studyService.getTableRows("syllabus_lexemes").stream()
                .filter(r -> clean.equalsIgnoreCase(String.valueOf(r.get("word"))))
                .toList();
        return Map.of(
                "ok", true,
                "word", clean,
                "found", !matches.isEmpty(),
                "lexeme", matches.isEmpty() ? Map.of("word", clean, "cn_definition", "考纲拓展学术词汇") : matches.get(0)
        );
    }

    @PostMapping("/api/progress/save")
    public ResponseEntity<Map<String, Object>> saveProgress(
            @RequestBody Map<String, Object> body,
            HttpServletRequest request) {
        RbacAccountManagementService.AuthenticatedPrincipal principal = extractPrincipal(request);
        String passageKey = String.valueOf(body.getOrDefault("passage_key", "ENG1_2025_TEXT1"));
        int paraIdx = ((Number) body.getOrDefault("active_paragraph_idx", 0)).intValue();
        int charOffset = ((Number) body.getOrDefault("char_offset", 0)).intValue();
        double ratio = ((Number) body.getOrDefault("scroll_ratio", 0.5)).doubleValue();
        int seconds = ((Number) body.getOrDefault("reading_seconds", 60)).intValue();
        String device = String.valueOf(body.getOrDefault("device_tag", "Spring-Web-Client"));
        Map<String, Object> saved = studyService.saveProgressAnchor(
                principal.username(), passageKey, paraIdx, charOffset, ratio, seconds, device);
        return ResponseEntity.ok(Map.of("ok", true, "progress", saved));
    }

    @PostMapping("/api/annotations/save")
    public ResponseEntity<Map<String, Object>> saveAnnotation(
            @RequestBody Map<String, Object> body,
            HttpServletRequest request) {
        RbacAccountManagementService.AuthenticatedPrincipal principal = extractPrincipal(request);
        try {
            String passageKey = String.valueOf(body.getOrDefault("passage_key", "ENG1_2025_TEXT1"));
            int paraIdx = ((Number) body.getOrDefault("paragraph_idx", 0)).intValue();
            int start = ((Number) body.getOrDefault("start_offset", 0)).intValue();
            int end = ((Number) body.getOrDefault("end_offset", 10)).intValue();
            int length = ((Number) body.getOrDefault("passage_length", 500)).intValue();
            String text = String.valueOf(body.getOrDefault("selected_text", ""));
            String gran = String.valueOf(body.getOrDefault("granularity", "phrase"));
            String color = String.valueOf(body.getOrDefault("highlight_color", "amber"));
            String note = String.valueOf(body.getOrDefault("note_markdown", ""));
            boolean promote = Boolean.parseBoolean(String.valueOf(body.getOrDefault("promote_to_essay", false)));

            Map<String, Object> span = studyService.saveAnnotationSpan(
                    principal.username(), passageKey, paraIdx, start, end, length, text, gran, color, note, promote);
            return ResponseEntity.ok(Map.of("ok", true, "annotation", span));
        } catch (IllegalArgumentException ex) {
            return ResponseEntity.badRequest().body(Map.of("ok", false, "error", ex.getMessage()));
        }
    }

    @GetMapping("/api/db/lineage")
    public Map<String, Object> dbLineage(HttpServletRequest request) {
        return drilldownService.buildTieredLineageResponse(extractPrincipal(request));
    }

    private RbacAccountManagementService.AuthenticatedPrincipal extractPrincipal(HttpServletRequest request) {
        Object attr = request.getAttribute(ZeroTrustRbacAndIdempotencyFilter.ATTR_AUTH_SESSION);
        if (attr instanceof RbacAccountManagementService.AuthenticatedPrincipal p) {
            return p;
        }
        return rbacService.resolvePrincipal(null);
    }
}
