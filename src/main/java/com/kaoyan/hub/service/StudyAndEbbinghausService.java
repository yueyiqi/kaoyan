package com.kaoyan.hub.service;

import com.kaoyan.hub.domain.KaoyanOntologyAxioms;
import com.kaoyan.hub.ha.ClusterEpochCoordinatorService;
import com.kaoyan.hub.middleware.ZeroTrustRbacAndIdempotencyFilter;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.atomic.AtomicLong;

/**
 * Core Study & Ebbinghaus Spaced Repetition Service (DOM_01, DOM_02, DOM_03).
 *
 * Manages:
 * - Syllabus Lexemes & Exam Passages with SHA-256 integrity
 * - Reading Progress Anchors & 3-Granularity Annotation Spans (Axiom 1)
 * - Ebbinghaus Spaced-Repetition Vocabulary Queue (Axiom 2)
 * - Essay Corpus Snippets & Cloze Active-Recall Templates (Axiom 3)
 */
@Service
public class StudyAndEbbinghausService {

    private final ClusterEpochCoordinatorService coordinatorService;
    private final List<Map<String, Object>> lexemeRows = new CopyOnWriteArrayList<>();
    private final List<Map<String, Object>> passageRows = new CopyOnWriteArrayList<>();
    private final List<Map<String, Object>> paragraphRows = new CopyOnWriteArrayList<>();
    private final List<Map<String, Object>> syntaxRows = new CopyOnWriteArrayList<>();
    private final List<Map<String, Object>> progressRows = new CopyOnWriteArrayList<>();
    private final List<Map<String, Object>> annotationRows = new CopyOnWriteArrayList<>();
    private final List<Map<String, Object>> telemetryRows = new CopyOnWriteArrayList<>();
    private final List<Map<String, Object>> vocabRows = new CopyOnWriteArrayList<>();
    private final List<Map<String, Object>> essayRows = new CopyOnWriteArrayList<>();
    private final List<Map<String, Object>> clozeDrillRows = new CopyOnWriteArrayList<>();
    private final AtomicLong idSeq = new AtomicLong(2000L);

    public StudyAndEbbinghausService(ClusterEpochCoordinatorService coordinatorService) {
        this.coordinatorService = coordinatorService;
        seedCanonicalDataset();
    }

    private void seedCanonicalDataset() {
        String now = Instant.now().toString();
        seedLexeme("empirical", "/ɪmˈpɪrɪkl/", "adj.", "经验主义的；以实验或观察为依据的", 38, "TIER_CORE_A", "em(in)+pir(try)+ical");
        seedLexeme("paradigm", "/ˈpærədaɪm/", "n.", "范式；典范；思维框架", 31, "TIER_CORE_A", "para(beside)+digm(show)");
        seedLexeme("scrutinize", "/ˈskruːtənaɪz/", "v.", "仔细检查；细致审视", 24, "TIER_CORE_A", "scrutin(search)+ize");
        seedLexeme("unprecedented", "/ʌnˈpresɪdentɪd/", "adj.", "史无前例的；空前的", 29, "TIER_CORE_A", "un(not)+precede+nt+ed");

        String p1Text = "Scientific progress rarely follows a strictly linear trajectory; rather, empirical anomalies accumulate until an existing paradigm undergoes rigorous scrutiny.";
        Map<String, Object> passage = new LinkedHashMap<>();
        passage.put("passage_key", "ENG1_2025_TEXT1");
        passage.put("exam_year", 2025);
        passage.put("exam_type", "English_I");
        passage.put("section_name", "Reading Part A Text 1");
        passage.put("title_en", "Empirical Anomalies and Scientific Paradigm Shifts");
        passage.put("title_cn", "经验反常与科学范式转移");
        passage.put("topic_category", "Philosophy of Science & Epistemology");
        passage.put("difficulty_rating", "B2_C1_HARD");
        passage.put("word_count", 412);
        passage.put("paragraphs_json", "[\"" + p1Text + "\"]");
        passage.put("content_sha256", ZeroTrustRbacAndIdempotencyFilter.sha256Hex(p1Text));
        passage.put("updated_at", now);
        passageRows.add(passage);

        Map<String, Object> para = new LinkedHashMap<>();
        para.put("id", 1L);
        para.put("passage_key", "ENG1_2025_TEXT1");
        para.put("paragraph_index", 0);
        para.put("content_en", p1Text);
        para.put("translation_cn", "科学进步很少遵循严格线性的轨迹；相反，经验反常不断累积，直到既有范式接受严密审视。");
        para.put("discourse_role", "THESIS_CONTRAST_OPENING");
        para.put("key_syntax_note", "的分号并列对比结构 + until 时间状语从句");
        para.put("created_at", now);
        paragraphRows.add(para);

        Map<String, Object> syntax = new LinkedHashMap<>();
        syntax.put("id", 1L);
        syntax.put("passage_key", "ENG1_2025_TEXT1");
        syntax.put("paragraph_index", 0);
        syntax.put("sentence_no", "S1");
        syntax.put("clause_type", "Compound-Complex Contrastive");
        syntax.put("head_token", "follows / accumulate");
        syntax.put("dependency_grammar", "ROOT(follows) -> ADVMOD(rarely) ; COORD(accumulate) -> ADVCL(undergoes)");
        syntax.put("translation_tip", "先切分分号两侧主干，再顺译 until 引导的临界条件");
        syntax.put("created_at", now);
        syntaxRows.add(syntax);

        saveProgressAnchor("elena", "ENG1_2025_TEXT1", 0, 42, 0.65, 980, "macOS-Safari-Desktop");
        saveAnnotationSpan("elena", "ENG1_2025_TEXT1", 0, 11, 88, p1Text.length(),
                "empirical anomalies accumulate", "phrase", "amber", "核心论点转折短语", true);
        upsertVocabEntry("elena", "empirical", "ENG1_2025_TEXT1", p1Text, 2, 38, 3.5);
        upsertVocabEntry("elena", "paradigm", "ENG1_2025_TEXT1", p1Text, 1, 31, 4.0);
        upsertVocabEntry("admin", "scrutinize", "ENG1_2025_TEXT1", p1Text, 3, 24, 2.0);

        Map<String, Object> tel = new LinkedHashMap<>();
        tel.put("session_id", 1L);
        tel.put("user_id", "elena");
        tel.put("passage_key", "ENG1_2025_TEXT1");
        tel.put("dwell_seconds", 980);
        tel.put("lookup_count", 14);
        tel.put("annotation_count", 4);
        tel.put("client_viewport", "DESKTOP_SPLIT_1440");
        tel.put("recorded_at", now);
        telemetryRows.add(tel);

        Map<String, Object> drill = new LinkedHashMap<>();
        drill.put("drill_id", 1L);
        drill.put("user_id", "elena");
        drill.put("snippet_id", 1L);
        drill.put("submitted_answer", "empirical anomalies");
        drill.put("is_correct", 1);
        drill.put("response_time_ms", 1840);
        drill.put("error_category", "NONE");
        drill.put("practiced_at", now);
        clozeDrillRows.add(drill);
    }

    private void seedLexeme(String word, String phonetic, String pos, String defCn, int freq, String tier, String root) {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("id", idSeq.incrementAndGet());
        row.put("word", word);
        row.put("phonetic", phonetic);
        row.put("pos_tag", pos);
        row.put("cn_definition", defCn);
        row.put("exam_frequency", freq);
        row.put("freq_tier", tier);
        row.put("root_affix_note", root);
        row.put("created_at", Instant.now().toString());
        lexemeRows.add(row);
    }

    public Map<String, Object> saveProgressAnchor(
            String userId, String passageKey, int paragraphIdx, int charOffset,
            double scrollRatio, int readingSeconds, String deviceTag) {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("id", idSeq.incrementAndGet());
        row.put("user_id", userId);
        row.put("passage_key", passageKey);
        row.put("active_paragraph_idx", Math.max(0, paragraphIdx));
        row.put("char_offset", Math.max(0, charOffset));
        row.put("scroll_ratio", Math.max(0.0, Math.min(1.0, scrollRatio)));
        row.put("reading_seconds", Math.max(1, readingSeconds));
        row.put("device_tag", deviceTag != null ? deviceTag : "Web-Client");
        row.put("sync_version", progressRows.size() + 1);
        row.put("updated_at", Instant.now().toString());
        progressRows.add(row);
        coordinatorService.appendWalJournal("prog-" + row.get("id"), "UPSERT_PROGRESS", row.toString());
        return row;
    }

    public Map<String, Object> saveAnnotationSpan(
            String userId, String passageKey, int paragraphIdx, int startOffset, int endOffset,
            int passageLength, String selectedText, String granularity, String color,
            String noteMarkdown, boolean promoteToEssay) {
        KaoyanOntologyAxioms.assertAxiom1SpanBoundary(
                startOffset, endOffset, Math.max(passageLength, endOffset), selectedText, granularity);
        String spanUuid = "span-" + UUID.randomUUID().toString().substring(0, 12);
        String now = Instant.now().toString();
        Map<String, Object> span = new LinkedHashMap<>();
        span.put("span_uuid", spanUuid);
        span.put("user_id", userId);
        span.put("passage_key", passageKey);
        span.put("paragraph_idx", paragraphIdx);
        span.put("start_offset", startOffset);
        span.put("end_offset", endOffset);
        span.put("selected_text", selectedText.trim());
        span.put("granularity", granularity);
        span.put("highlight_color", KaoyanOntologyAxioms.VALID_COLORS.contains(color) ? color : "amber");
        span.put("note_markdown", noteMarkdown != null ? noteMarkdown : "");
        span.put("is_promoted_essay", promoteToEssay ? 1 : 0);
        span.put("created_at", now);
        annotationRows.add(span);

        if (promoteToEssay) {
            promoteSpanToEssayCorpus(userId, spanUuid, "Thesis & Argumentation", selectedText, noteMarkdown, null);
        }
        coordinatorService.appendWalJournal(spanUuid, "INSERT_ANNOTATION_SPAN", span.toString());
        return span;
    }

    public Map<String, Object> promoteSpanToEssayCorpus(
            String userId, String sourceSpanUuid, String category,
            String englishSentence, String chineseMeaning, String keyExpr) {
        String cloze = KaoyanOntologyAxioms.ensureAxiom3ClozeTemplate(englishSentence, keyExpr);
        Map<String, Object> essay = new LinkedHashMap<>();
        essay.put("id", (long) (essayRows.size() + 1));
        essay.put("user_id", userId);
        essay.put("source_span_uuid", sourceSpanUuid != null ? sourceSpanUuid : "span-manual");
        essay.put("rhetorical_category", category != null ? category : "Academic Contrast");
        essay.put("english_sentence", englishSentence.trim());
        essay.put("chinese_meaning", chineseMeaning != null ? chineseMeaning : "精选真题论证佳句");
        essay.put("cloze_template", cloze);
        essay.put("practice_count", 1);
        essay.put("created_at", Instant.now().toString());
        essayRows.add(essay);
        return essay;
    }

    public Map<String, Object> upsertVocabEntry(
            String userId, String word, String passageKey, String contextSentence,
            int masteryLevel, int examFreq, double elapsedDays) {
        double urgency = KaoyanOntologyAxioms.computeAndAssertAxiom2Urgency(masteryLevel, examFreq, elapsedDays);
        int intervalDays = KaoyanOntologyAxioms.EBBINGHAUS_INTERVAL_DAYS.get(
                Math.min(masteryLevel, KaoyanOntologyAxioms.EBBINGHAUS_INTERVAL_DAYS.size() - 1));
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("id", (long) (vocabRows.size() + 1));
        row.put("user_id", userId);
        row.put("word", word);
        row.put("source_passage_key", passageKey);
        row.put("context_sentence", contextSentence);
        row.put("mastery_level", masteryLevel);
        row.put("review_count", masteryLevel + 1);
        row.put("lapse_count", 0);
        row.put("ebbinghaus_urgency", urgency);
        row.put("next_review_at", Instant.now().plus(intervalDays, ChronoUnit.DAYS).toString());
        row.put("updated_at", Instant.now().toString());
        vocabRows.add(row);
        return row;
    }

    public List<Map<String, Object>> getVocabQueueSortedByUrgency() {
        List<Map<String, Object>> copy = new ArrayList<>(vocabRows);
        copy.sort(Comparator.comparingDouble(
                (Map<String, Object> r) -> ((Number) r.getOrDefault("ebbinghaus_urgency", 0.0)).doubleValue()
        ).reversed());
        return copy;
    }

    public List<Map<String, Object>> getTableRows(String tableName) {
        return switch (tableName) {
            case "syllabus_lexemes" -> lexemeRows;
            case "exam_passages" -> passageRows;
            case "passage_paragraphs" -> paragraphRows;
            case "syntax_tree_nodes" -> syntaxRows;
            case "user_progress_anchors" -> progressRows;
            case "annotation_spans" -> annotationRows;
            case "reading_session_telemetry" -> telemetryRows;
            case "user_vocab_ledger" -> getVocabQueueSortedByUrgency();
            case "essay_corpus_snippets" -> essayRows;
            case "cloze_drill_records" -> clozeDrillRows;
            default -> List.of();
        };
    }
}
