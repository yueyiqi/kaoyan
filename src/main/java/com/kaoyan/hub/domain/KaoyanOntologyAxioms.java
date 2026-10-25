package com.kaoyan.hub.domain;

import java.util.List;
import java.util.Set;
import java.util.regex.Pattern;

/**
 * Domain Ontology & 5 Machine-Verifiable Axioms for KaoyanEnglish Hub (Skill 188 / Spec Stage 3).
 *
 * Every state mutation (annotation creation, Ebbinghaus scheduling, essay snippet promotion,
 * RBAC account/role mutation, and cluster epoch transition) MUST pass these 5 deterministic axioms
 * before database persistence.
 */
public final class KaoyanOntologyAxioms {

    /** Standard Ebbinghaus spaced-repetition interval ladder in days. */
    public static final List<Integer> EBBINGHAUS_INTERVAL_DAYS = List.of(1, 2, 4, 7, 15, 30);

    /** Allowed annotation granularities for deep reading spans. */
    public static final Set<String> VALID_GRANULARITIES = Set.of("word", "phrase", "sentence");

    /** Allowed highlight colors corresponding to Daylight/Midnight/Eyecare semantic tokens. */
    public static final Set<String> VALID_COLORS = Set.of("amber", "emerald", "rose", "sky", "violet");

    /** Allowed RBAC role codes and hierarchy levels. */
    public static final int LEVEL_GUEST = 10;
    public static final int LEVEL_SCHOLAR = 50;
    public static final int LEVEL_ADMIN = 100;

    private static final Pattern CLOZE_KEY_PATTERN = Pattern.compile("\\[KEY:\\s*([^\\]]+)\\]");

    private KaoyanOntologyAxioms() {
    }

    /**
     * Axiom 1 (Span Boundary & Non-Empty Invariant):
     * For any annotation span {@code s} on passage content {@code C},
     * {@code 0 <= startOffset < endOffset <= |C|} and {@code granularity in {word, phrase, sentence}}.
     */
    public static void assertAxiom1SpanBoundary(
            int startOffset,
            int endOffset,
            int passageLength,
            String selectedText,
            String granularity) {
        if (startOffset < 0 || endOffset <= startOffset || endOffset > passageLength) {
            throw new IllegalArgumentException(String.format(
                    "[Axiom-1 Violation] Span offsets [%d, %d) out of bounds for passage length %d",
                    startOffset, endOffset, passageLength));
        }
        if (selectedText == null || selectedText.trim().isEmpty()) {
            throw new IllegalArgumentException("[Axiom-1 Violation] Selected text cannot be blank");
        }
        if (granularity == null || !VALID_GRANULARITIES.contains(granularity)) {
            throw new IllegalArgumentException(
                    "[Axiom-1 Violation] Invalid granularity: " + granularity);
        }
    }

    /**
     * Axiom 2 (Ebbinghaus Urgency & Monotonic Mastery Bound):
     * Mastery level {@code m in [0, 5]}, exam frequency {@code f >= 0}, and urgency score
     * {@code U(w) = (1 + elapsedDays / intervalDays) * (1.6 - 0.12 * m) * (1 + 0.18 * ln(1 + f)) > 0}.
     */
    public static double computeAndAssertAxiom2Urgency(
            int masteryLevel,
            int examFrequency,
            double elapsedDays) {
        if (masteryLevel < 0 || masteryLevel > 5) {
            throw new IllegalArgumentException(
                    "[Axiom-2 Violation] Mastery level must be in [0, 5], got: " + masteryLevel);
        }
        if (examFrequency < 0 || elapsedDays < 0.0) {
            throw new IllegalArgumentException(
                    "[Axiom-2 Violation] Exam frequency and elapsed days must be non-negative");
        }
        int intervalDays = EBBINGHAUS_INTERVAL_DAYS.get(Math.min(masteryLevel, EBBINGHAUS_INTERVAL_DAYS.size() - 1));
        double timeFactor = 1.0 + (elapsedDays / intervalDays);
        double masteryPenalty = 1.6 - (0.12 * masteryLevel);
        double freqBoost = 1.0 + (0.18 * Math.log1p(examFrequency));
        double urgency = Math.round(timeFactor * masteryPenalty * freqBoost * 1000.0) / 1000.0;
        if (urgency <= 0.0 || Double.isNaN(urgency) || Double.isInfinite(urgency)) {
            throw new IllegalStateException("[Axiom-2 Violation] Computed non-positive urgency: " + urgency);
        }
        return urgency;
    }

    /**
     * Axiom 3 (Essay Cloze Promotion Contract):
     * Every promoted essay snippet MUST contain at least one {@code [KEY: target]} cloze slot
     * so the active recall engine can mask and verify the key expression.
     */
    public static String ensureAxiom3ClozeTemplate(String rawSentence, String keyExpression) {
        if (rawSentence == null || rawSentence.trim().isEmpty()) {
            throw new IllegalArgumentException("[Axiom-3 Violation] Essay sentence cannot be empty");
        }
        if (CLOZE_KEY_PATTERN.matcher(rawSentence).find()) {
            return rawSentence.trim();
        }
        String cleanSentence = rawSentence.trim();
        String target = (keyExpression != null && !keyExpression.isBlank())
                ? keyExpression.trim()
                : extractLongestAcademicToken(cleanSentence);
        if (cleanSentence.contains(target)) {
            return cleanSentence.replaceFirst(Pattern.quote(target), "[KEY: " + target + "]");
        }
        return cleanSentence + " [KEY: " + target + "]";
    }

    /**
     * Axiom 4 (Zero-Trust RBAC Tier Hierarchy & Self-Lockout Prohibition):
     * Role levels strictly follow {@code GUEST(10) < SCHOLAR(50) < ADMIN(100)}, and an active
     * administrator cannot disable or demote their own currently authenticated account.
     */
    public static void assertAxiom4RbacMutation(
            int operatorLevel,
            String operatorUsername,
            String targetUsername,
            String newRoleCode,
            String newStatus) {
        if (operatorLevel < LEVEL_ADMIN) {
            throw new SecurityException("[Axiom-4 Violation] Admin level (100) required for RBAC mutation");
        }
        if (operatorUsername != null && operatorUsername.equalsIgnoreCase(targetUsername)) {
            if (!"ADMIN".equalsIgnoreCase(newRoleCode) || !"ACTIVE".equalsIgnoreCase(newStatus)) {
                throw new IllegalArgumentException(
                        "[Axiom-4 Violation] Self-lockout prohibited: active admin cannot demote or disable self");
            }
        }
    }

    /**
     * Axiom 5 (Monotonic Cluster Epoch Fencing):
     * Any write replicated across the 3-node cluster (W1, HP, S1) MUST carry {@code requestEpoch >= localEpoch}.
     */
    public static void assertAxiom5EpochFencing(long requestEpoch, long localEpoch) {
        if (requestEpoch < localEpoch) {
            throw new IllegalStateException(String.format(
                    "[Axiom-5 Violation] Stale cluster epoch rejected: requestEpoch=%d < localEpoch=%d",
                    requestEpoch, localEpoch));
        }
    }

    private static String extractLongestAcademicToken(String sentence) {
        String[] tokens = sentence.replaceAll("[^A-Za-z0-9\\s-]", " ").trim().split("\\s+");
        String best = "empirical";
        for (String token : tokens) {
            if (token.length() > best.length()) {
                best = token;
            }
        }
        return best;
    }
}
