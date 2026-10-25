<template>
  <section class="eids-drilldown-workbench" :data-theme="activeTheme">
    <header class="workbench-header">
      <div class="title-group">
        <h3>🔎 EIDS 五层全量库表下钻工作台 (L1 业务域 → L5 单行 146 字段抽屉)</h3>
        <span class="badge-pill">{{ totalTables }} Tables · {{ totalColumns }} Columns · 100% Exposed</span>
      </div>
      <div class="search-controls">
        <input
          v-model="searchQuery"
          type="search"
          placeholder="输入任意字段关键字实时过滤 (q=...)..."
          class="search-input"
          @keyup.enter="triggerSearch"
        />
        <button class="btn-primary" @click="triggerSearch">执行下钻检索</button>
      </div>
    </header>

    <div class="domain-bento-grid">
      <article
        v-for="dom in domains"
        :key="dom.domain_code"
        class="domain-card"
        :class="{ active: dom.domain_code === activeDomain }"
        @click="selectDomain(dom.domain_code)"
      >
        <div class="domain-code">{{ dom.domain_code }}</div>
        <div class="domain-label">{{ dom.domain_label }}</div>
        <div class="domain-meta">{{ dom.table_count }} 张表 · {{ dom.column_count }} 个字段</div>
      </article>
    </div>

    <div class="table-explorer-panel">
      <div class="table-chips">
        <button
          v-for="tbl in activeDomainTables"
          :key="tbl.table_name"
          class="table-chip"
          :class="{ selected: tbl.table_name === activeTable }"
          @click="selectTable(tbl.table_name)"
        >
          {{ tbl.table_name }} ({{ tbl.column_count }}列)
        </button>
      </div>

      <div class="rows-table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th
                v-for="col in activeColumns"
                :key="col"
                :class="{ highlighted: col === highlightCol }"
              >
                {{ col }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(row, rIdx) in activeRows"
              :key="rIdx"
              class="clickable-row"
              @click="openRecordDrawer(row)"
            >
              <td
                v-for="col in activeColumns"
                :key="col"
                :class="{ highlighted: col === highlightCol }"
              >
                {{ formatCell(row[col]) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed } from 'vue';

const props = defineProps({
  activeTheme: { type: String, default: 'daylight' },
  initialDomain: { type: String, default: 'DOM_01_LEXEME_AND_PASSAGE' },
  initialTable: { type: String, default: 'exam_passages' },
  highlightCol: { type: String, default: 'title_en' }
});

const emit = defineEmits(['select-table', 'open-record-drawer', 'search']);

const totalTables = ref(18);
const totalColumns = ref(146);
const activeDomain = ref(props.initialDomain);
const activeTable = ref(props.initialTable);
const searchQuery = ref('');
const domains = ref([]);
const activeColumns = ref([]);
const activeRows = ref([]);

const activeDomainTables = computed(() => {
  const found = domains.value.find(d => d.domain_code === activeDomain.value);
  return found ? found.tables : [];
});

function selectDomain(domainCode) {
  activeDomain.value = domainCode;
}

function selectTable(tableName) {
  activeTable.value = tableName;
  emit('select-table', { domain: activeDomain.value, table: tableName, q: searchQuery.value });
}

function triggerSearch() {
  emit('search', { table: activeTable.value, q: searchQuery.value, highlightCol: props.highlightCol });
}

function openRecordDrawer(row) {
  emit('open-record-drawer', { table: activeTable.value, row });
}

function formatCell(val) {
  if (val === null || val === undefined) return '—';
  const str = String(val);
  return str.length > 72 ? str.slice(0, 72) + '...' : str;
}
</script>

<style scoped>
.eids-drilldown-workbench {
  border: 1px solid var(--border, #cbd5e1);
  border-radius: 12px;
  padding: 16px;
  background: var(--card, #ffffff);
  color: var(--text, #0f172a);
}
.workbench-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 14px;
}
.domain-bento-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}
.domain-card {
  padding: 12px;
  border-radius: 10px;
  border: 1px solid var(--border, #cbd5e1);
  cursor: pointer;
}
.domain-card.active {
  border-color: var(--primary, #2563eb);
  background: var(--primary-soft, #dbeafe);
}
.highlighted {
  background: rgba(245, 158, 11, 0.16);
  font-weight: 700;
}
</style>
