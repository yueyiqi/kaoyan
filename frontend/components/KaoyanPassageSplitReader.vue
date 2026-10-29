<template>
  <div class="kaoyan-split-reader" :class="{ 'guest-metered': isGuest }">
    <div class="left-passage-pane">
      <header class="passage-meta-bar">
        <span class="exam-tag">{{ passage.exam_year }} {{ passage.exam_type }} · {{ passage.section_name }}</span>
        <h2>{{ passage.title_en }}</h2>
        <p class="subtitle-cn">{{ passage.title_cn }}</p>
      </header>

      <div
        v-for="(para, idx) in paragraphs"
        :key="para.id || idx"
        class="paragraph-block"
        :class="{ 'blurred-locked': isGuest && idx > 0 }"
        @mouseup="handleTextSelection(idx, $event)"
      >
        <div class="para-index">¶ {{ idx + 1 }}</div>
        <p class="para-en">{{ para.content_en }}</p>
        <p class="para-cn">{{ para.translation_cn }}</p>
        <div class="para-actions">
          <button class="btn-chip" @click="drillParagraphRow(idx)">
            🔎 下钻本段库表记录 (passage_paragraphs)
          </button>
          <button class="btn-chip" @click="drillSyntaxTree(idx)">
            🌳 语法依存树下钻 (syntax_tree_nodes)
          </button>
        </div>
      </div>
    </div>

    <aside class="right-annotation-pane">
      <h3>✍️ 三粒度精读批注与艾宾浩斯联动 ({{ annotations.length }})</h3>
      <ul class="annotation-list">
        <li
          v-for="span in annotations"
          :key="span.span_uuid"
          class="annotation-card"
          @click="openSpanRecordDrawer(span)"
        >
          <div class="span-header">
            <span class="granularity-badge">{{ span.granularity }}</span>
            <span class="offset-tag">[{{ span.start_offset }}, {{ span.end_offset }})</span>
          </div>
          <blockquote class="selected-quote">{{ span.selected_text }}</blockquote>
          <p class="span-note">{{ span.note_markdown }}</p>
        </li>
      </ul>
    </aside>
  </div>
</template>

<script setup>
defineProps({
  isGuest: { type: Boolean, default: false },
  passage: { type: Object, required: true },
  paragraphs: { type: Array, default: () => [] },
  annotations: { type: Array, default: () => [] }
});

const emit = defineEmits(['create-span', 'drill-paragraph', 'drill-syntax', 'open-span-drawer']);

function handleTextSelection(paragraphIdx, event) {
  const sel = window.getSelection ? window.getSelection().toString().trim() : '';
  if (sel.length >= 2) {
    emit('create-span', { paragraphIdx, selectedText: sel, clientX: event.clientX });
  }
}

function drillParagraphRow(paragraphIdx) {
  emit('drill-paragraph', { table: 'passage_paragraphs', paragraphIdx });
}

function drillSyntaxTree(paragraphIdx) {
  emit('drill-syntax', { table: 'syntax_tree_nodes', paragraphIdx });
}

function openSpanRecordDrawer(span) {
  emit('open-span-drawer', { table: 'annotation_spans', pk: span.span_uuid });
}
</script>

<style scoped>
.kaoyan-split-reader {
  display: grid;
  grid-template-columns: 1.15fr 0.85fr;
  gap: 18px;
  align-items: start;
}
.para-en {
  font-family: var(--font-serif-en, "Charter", "Source Serif 4", "Georgia", serif);
  font-size: var(--reading-font-size, 1.03rem);
  line-height: var(--reading-line-height, 1.82);
  max-width: 74ch;
}
.right-annotation-pane {
  position: sticky;
  top: 68px;
  max-height: calc(100vh - 84px);
  overflow-y: auto;
}
.para-index, .offset-tag {
  font-variant-numeric: tabular-nums;
}
.btn-chip:focus-visible {
  outline: 2px solid var(--primary, rgb(37, 99, 235));
  outline-offset: 2px;
}
.blurred-locked {
  filter: blur(6px);
  pointer-events: none;
  user-select: none;
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
@media (max-width: 960px) {
  .kaoyan-split-reader {
    grid-template-columns: 1fr;
  }
  .right-annotation-pane {
    position: static;
    max-height: none;
  }
}
</style>
