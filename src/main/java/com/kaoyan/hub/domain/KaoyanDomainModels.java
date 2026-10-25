package com.kaoyan.hub.domain;

import java.util.List;
import java.util.Map;

/**
 * Immutable Java 17 Record Domain Entities & DTOs covering all 18 Tables and 146 Columns
 * across the 5 Business Domains of KaoyanEnglish Hub v6.0.
 */
public final class KaoyanDomainModels {

    private KaoyanDomainModels() {
    }

    /** DOM_01 Table 01: syllabus_lexemes (9 columns) */
    public record SyllabusLexeme(
            long id,
            String word,
            String phonetic,
            String posTag,
            String cnDefinition,
            int examFrequency,
            String freqTier,
            String rootAffixNote,
            String createdAt
    ) {}

    /** DOM_01 Table 02: exam_passages (12 columns) */
    public record ExamPassage(
            String passageKey,
            int examYear,
            String examType,
            String sectionName,
            String titleEn,
            String titleCn,
            String topicCategory,
            String difficultyRating,
            int wordCount,
            String paragraphsJson,
            String contentSha256,
            String updatedAt
    ) {}

    /** DOM_01 Table 03: passage_paragraphs (8 columns) */
    public record PassageParagraph(
            long id,
            String passageKey,
            int paragraphIndex,
            String contentEn,
            String translationCn,
            String discourseRole,
            String keySyntaxNote,
            String createdAt
    ) {}

    /** DOM_01 Table 04: syntax_tree_nodes (9 columns) */
    public record SyntaxTreeNode(
            long id,
            String passageKey,
            int paragraphIndex,
            String sentenceNo,
            String clauseType,
            String headToken,
            String dependencyGrammar,
            String translationTip,
            String createdAt
    ) {}

    /** DOM_02 Table 05: user_progress_anchors (10 columns) */
    public record UserProgressAnchor(
            long id,
            String userId,
            String passageKey,
            int activeParagraphIdx,
            int charOffset,
            double scrollRatio,
            int readingSeconds,
            String deviceTag,
            int syncVersion,
            String updatedAt
    ) {}

    /** DOM_02 Table 06: annotation_spans (12 columns) */
    public record AnnotationSpan(
            String spanUuid,
            String userId,
            String passageKey,
            int paragraphIdx,
            int startOffset,
            int endOffset,
            String selectedText,
            String granularity,
            String highlightColor,
            String noteMarkdown,
            int isPromotedEssay,
            String createdAt
    ) {}

    /** DOM_02 Table 07: reading_session_telemetry (8 columns) */
    public record ReadingSessionTelemetry(
            long sessionId,
            String userId,
            String passageKey,
            int dwellSeconds,
            int lookupCount,
            int annotationCount,
            String clientViewport,
            String recordedAt
    ) {}

    /** DOM_03 Table 08: user_vocab_ledger (11 columns) */
    public record UserVocabLedger(
            long id,
            String userId,
            String word,
            String sourcePassageKey,
            String contextSentence,
            int masteryLevel,
            int reviewCount,
            int lapseCount,
            double ebbinghausUrgency,
            String nextReviewAt,
            String updatedAt
    ) {}

    /** DOM_03 Table 09: essay_corpus_snippets (9 columns) */
    public record EssayCorpusSnippet(
            long id,
            String userId,
            String sourceSpanUuid,
            String rhetoricalCategory,
            String englishSentence,
            String chineseMeaning,
            String clozeTemplate,
            int practiceCount,
            String createdAt
    ) {}

    /** DOM_03 Table 10: cloze_drill_records (8 columns) */
    public record ClozeDrillRecord(
            long drillId,
            String userId,
            long snippetId,
            String submittedAnswer,
            int isCorrect,
            int responseTimeMs,
            String errorCategory,
            String practicedAt
    ) {}

    /** DOM_04 Table 11: sys_users (11 columns, password_hash & password_salt masked in DTOs) */
    public record SysUserView(
            long userId,
            String username,
            String displayName,
            String roleCode,
            int roleLevel,
            String accountStatus,
            String passwordMask,
            int zeroMemoryEnforced,
            String lastLoginAt,
            String createdBy,
            String updatedAt
    ) {}

    /** DOM_04 Table 12: sys_roles (7 columns) */
    public record SysRole(
            String roleCode,
            String roleNameCn,
            int roleLevel,
            String dataScopeMode,
            int canAccessAdminConsole,
            String description,
            String createdAt
    ) {}

    /** DOM_04 Table 13: sys_permissions (6 columns) */
    public record SysPermission(
            String permCode,
            String permNameCn,
            String resourceGroup,
            String httpMethod,
            String endpointPattern,
            String createdAt
    ) {}

    /** DOM_04 Table 14: sys_role_permissions (5 columns) */
    public record SysRolePermission(
            long id,
            String roleCode,
            String permCode,
            String grantedBy,
            String grantedAt
    ) {}

    /** DOM_04 Table 15: sys_rbac_audit_log (9 columns) */
    public record SysRbacAuditLog(
            long auditId,
            String actorUsername,
            String actorRole,
            String actionType,
            String targetEntity,
            String decisionOutcome,
            String clientIpHash,
            String traceId,
            String createdAt
    ) {}

    /** DOM_05 Table 16–18 Summary Record for HA Cluster & Cold Backups */
    public record HaClusterStatusView(
            String clusterId,
            long currentEpoch,
            String primaryNode,
            String activeEngine,
            int rpoSeconds,
            long rtoMs,
            List<Map<String, Object>> replicaNodes,
            Map<String, Object> t2BackupManifest
    ) {}
}
