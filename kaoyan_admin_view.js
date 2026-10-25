// All displayed columns come from the current database. Labels only enrich semantics.
function runtimeCatalog() {
  return isAdmin() ? Object.values(adminDrillState.catalog?.tables || {}) : [];
}
function fieldConstraints(column) {
  const parts = [];
  if (column.pk) parts.push('PK #' + column.pk);
  if (column.notnull) parts.push('NOT NULL');
  if (column.default_value !== null && column.default_value !== undefined) parts.push('DEFAULT ' + column.default_value);
  if (column.hidden) parts.push('GENERATED / HIDDEN ' + column.hidden);
  return parts.join(' · ') || '—';
}
function fieldDescription(table, name) {
  const entry = ADMIN_DB_CATALOG_18T_146C.find(t => t.table_name === table);
  return entry?.columns.find(c => c[0] === name)?.[3] || '实际库表字段 (Database field)';
}
function fieldValue(value) {
  if (value === null || value === undefined) return 'NULL';
  if (value === '') return '""';
  return typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value);
}
function drillButton(label, attribute, value, active = false) {
  return '<button class="btn' + (active ? ' active' : '') + '" ' + attribute + '="' +
    escapeHtmlStr(value) + '">' + escapeHtmlStr(label) + '</button>';
}
function bindDataClick(element, attribute, callback) {
  if (!element) return;
  element.onclick = event => {
    const target = event.target.closest('[' + attribute + ']');
    if (target && element.contains(target)) callback(target.getAttribute(attribute), target);
  };
}
function renderRuntimeSchema() {
  const body = document.getElementById('dbSchemaTableBody');
  if (!body) return;
  body.innerHTML = runtimeCatalog().map(t => '<tr><td>' + escapeHtmlStr(t.table_no) +
    '</td><td><code>' + escapeHtmlStr(t.table_name) + '</code></td><td>' +
    escapeHtmlStr(t.pk_columns.join(', ')) + '</td><td><code>' +
    escapeHtmlStr(t.columns.map(c => c.name).join(', ')) + '</code></td><td>' +
    t.column_count + ' 字段 (fields)</td></tr>').join('');
}
function renderFullFieldCatalog() {
  const body = document.getElementById('adminFullFieldCatalogBody');
  if (!body) return;
  const query = (document.getElementById('adminFieldSearchInput')?.value || '').trim().toLowerCase();
  let total = 0, matched = 0;
  body.innerHTML = runtimeCatalog().map(t => t.columns.map(c => {
    total++;
    const description = fieldDescription(t.table_name, c.name);
    if (query && ![t.table_name, t.domain_id, c.name, c.type, description].join(' ').toLowerCase().includes(query)) return '';
    matched++;
    return '<tr data-table="' + escapeHtmlStr(t.table_name) + '" data-column="' + escapeHtmlStr(c.name) +
      '"><td>' + matched + '</td><td>' + escapeHtmlStr(t.domain_id) + '</td><td><code>' +
      escapeHtmlStr(t.table_name) + '</code></td><td>' + c.cid + '</td><td><code>' +
      escapeHtmlStr(c.name) + '</code></td><td>' + escapeHtmlStr(c.type) + '</td><td>' +
      escapeHtmlStr(fieldConstraints(c)) + '</td><td>' + escapeHtmlStr(description) + '</td><td>' +
      drillButton('查看数据 (View data)', 'data-open-table', t.table_name) + '</td></tr>';
  }).join('')).join('');
  const badge = document.getElementById('adminFullCatalogCountBadge');
  if (badge) badge.textContent = matched + ' / ' + total + ' 实际字段 (Live fields)';
  bindDataClick(body, 'data-open-table', table => {
    adminDrillState.selectedDomain = 'ALL';
    selectDrillTable(table);
    document.getElementById('admin5LayerDrilldownCard')?.scrollIntoView({block:'start'});
  });
}
function renderAdminDrilldownUI() {
  const state = adminDrillState, catalog = state.catalog, live = state.livePayload;
  const tables = runtimeCatalog();
  const get = id => document.getElementById(id);
  const summary = get('adminDrillSummaryBadge');
  if (summary) summary.textContent = live ? live.summary.total_tables + ' 表 · ' + live.summary.total_columns +
    ' 实际字段 (Live fields)' : '等待实测数据 (Waiting for data)';
  if (get('adminDbCoverageBadge')) get('adminDbCoverageBadge').textContent = summary?.textContent || '—';
  const domainBar = get('adminDrillDomainBar'), tableBar = get('adminDrillTableBar');
  if (domainBar) {
    domainBar.innerHTML = drillButton('全部 (All)', 'data-domain', 'ALL', state.selectedDomain === 'ALL') +
      (catalog?.domains || []).map(d => drillButton(d.domain_name + ' · ' + d.table_count + '表 / ' +
        d.column_count + '字段', 'data-domain', d.domain_id, state.selectedDomain === d.domain_id)).join('');
    bindDataClick(domainBar, 'data-domain', selectDrillDomain);
  }
  if (tableBar) {
    tableBar.innerHTML = tables.filter(t => state.selectedDomain === 'ALL' || t.domain_id === state.selectedDomain)
      .map(t => drillButton(t.table_name + ' · ' + t.column_count + '列 / ' + t.row_count + '行',
        'data-table', t.table_name, state.selectedTable === t.table_name)).join('');
    bindDataClick(tableBar, 'data-table', selectDrillTable);
  }
  const cascade = get('adminUserCascadeSummary');
  if (cascade) {
    cascade.style.display = state.selectedUser ? 'block' : 'none';
    cascade.innerHTML = live ? Object.entries(live.user_cascade.tables).map(([table, info]) =>
      drillButton(table + ': ' + info.matched_count, 'data-table', table, state.selectedTable === table)).join('') : '';
    bindDataClick(cascade, 'data-table', selectDrillTable);
  }
  const userSelect = get('adminDrillUserSelect');
  if (userSelect) userSelect.value = state.selectedUser;
  const notice = get('adminDrillStatus');
  if (notice) notice.textContent = state.loading ? '正在加载 (Loading)' :
    state.error ? '加载失败 (Load failed): ' + state.error : live ? '数据已更新 (Updated)' : '尚未加载 (Not loaded)';
  const table = live?.selected_table;
  const columns = table?.columns || [];
  const rows = table?.rows || [];
  get('adminDrillActiveTableLabel').textContent = state.selectedTable;
  get('adminDrillTableColBadge').textContent = table ? columns.length + ' 字段 · ' + table.row_count + ' 匹配行 (Matching rows)' : '—';
  get('adminDrillRowTableHead').innerHTML = table ? '<tr><th>记录 (Record)</th>' +
    columns.map(c => '<th><code>' + escapeHtmlStr(c.name) + '</code><br>' + escapeHtmlStr(c.type) + '</th>').join('') + '</tr>' : '';
  const body = get('adminDrillRowTableBody');
  body.innerHTML = rows.map((row, index) => '<tr data-row="' + index + '"' +
    (index === state.selectedRowIdx ? ' style="background:var(--primary-soft)"' : '') +
    '><td>' + drillButton('#' + (table.offset + index + 1) + ' 查看 (Inspect)', 'data-row', index) + '</td>' +
    columns.map(c => '<td data-column="' + escapeHtmlStr(c.name) +
      '"><code class="field-value">' + escapeHtmlStr(fieldValue(row[c.name])) + '</code></td>').join('') + '</tr>').join('');
  if (table && !rows.length) body.innerHTML = '<tr><td colspan="' + (columns.length + 1) + '">无匹配记录 (No matching records)</td></tr>';
  bindDataClick(body, 'data-row', index => inspectDrillRow(Number(index)));
  const pageInfo = get('adminPageInfo');
  if (pageInfo) pageInfo.textContent = table ? (rows.length ? table.offset + 1 : 0) + '–' +
    (table.offset + rows.length) + ' / ' + table.row_count + ' 记录 (Records)' : '—';
  const previous = get('adminPrevPage'), next = get('adminNextPage');
  if (previous) previous.disabled = !table?.has_previous || state.loading;
  if (next) next.disabled = !table?.has_next || state.loading;
  const select = get('adminFilterColumn');
  if (select && table) {
    select.innerHTML = '<option value="">全部字段 (No filter)</option>' + columns.map(c =>
      '<option value="' + escapeHtmlStr(c.name) + '">' + escapeHtmlStr(c.name) + '</option>').join('');
    select.value = state.filterColumn || '';
    get('adminFilterValue').value = state.filterValue || '';
  }
  if (state.selectedRowIdx >= rows.length) state.selectedRowIdx = 0;
  renderFieldInspector(table, rows[state.selectedRowIdx]);
}
function renderFieldInspector(table, row) {
  const body = document.getElementById('adminInspectorTableBody');
  const title = document.getElementById('adminInspectorRowTitle');
  title.textContent = row ? table.table_name + ' · #' + (table.offset + adminDrillState.selectedRowIdx + 1) +
    ' · ' + table.columns.length + ' 字段 (Fields)' : '未选中记录 (No selected record)';
  body.innerHTML = !row ? '' : table.columns.map(c => {
    const value = row[c.name], text = fieldValue(value);
    let drill = '';
    if (c.is_json && value !== null) {
      try {
        const parsed = typeof value === 'string' ? JSON.parse(value) : value;
        drill = '<details><summary>展开 JSON (Expand)</summary><pre class="field-value">' +
          escapeHtmlStr(JSON.stringify(parsed, null, 2)) + '</pre></details>';
      } catch (_) { drill = '原始文本 (Raw text)'; }
    } else if (c.fk_target && value !== null && value !== undefined && value !== '') {
      drill = '<button class="btn" data-fk="' + escapeHtmlStr(c.fk_target) + '" data-value="' +
        escapeHtmlStr(value) + '">查看关联 (Related): ' + escapeHtmlStr(c.fk_target) + '</button>';
    }
    return '<tr data-column="' + escapeHtmlStr(c.name) + '"><td>' + c.cid +
      '</td><td><code>' + escapeHtmlStr(c.name) + '</code></td><td>' + escapeHtmlStr(c.type) +
      '</td><td>' + escapeHtmlStr(fieldConstraints(c)) + '</td><td>' +
      escapeHtmlStr(fieldDescription(table.table_name, c.name)) + '</td><td><code class="field-value">' +
      escapeHtmlStr(text) + '</code></td><td>' + drill + '</td></tr>';
  }).join('');
  bindDataClick(body, 'data-fk', (spec, target) => jumpToForeignKeyTarget(spec, target.getAttribute('data-value')));
}
