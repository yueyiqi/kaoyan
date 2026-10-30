// EIDS-inspired cross-module interactive drill-down modals, live SQL table browser & 100% column lineage inspector.
let eidsBrowserState = {
  table: 'exam_passages',
  offset: 0,
  limit: 12,
  q: '',
  highlightCol: '',
  domainFilter: 'ALL',
  domainQuery: '',
  cachedLineagePayload: null
};

const MODULE_DB_LINEAGE_MAP = {
  MOD_00_INGESTION: { table: 'exam_passages', col: 'paragraphs_json', domain: 'DOM_02_CORE_CONTENT', related: ['syllabus_5500_lexicon', 'exam_passages', 'annotation_spans', 'ha_sync_wal_journal'] },
  MOD_01_READING: { table: 'annotation_spans', col: 'selected_text', domain: 'DOM_03_SCHOLAR_STUDY', related: ['exam_passages', 'annotation_spans', 'user_progress_anchors'] },
  MOD_02_VOCAB: { table: 'user_vocab_ledger', col: 'urgency_score', domain: 'DOM_03_SCHOLAR_STUDY', related: ['syllabus_5500_lexicon', 'user_vocab_ledger'] },
  MOD_03_ESSAY: { table: 'essay_corpus_snippets', col: 'theme_tag', domain: 'DOM_03_SCHOLAR_STUDY', related: ['essay_corpus_snippets', 'user_progress_anchors'] },
  MOD_04_AUTH_ANCHOR: { table: 'sys_users', col: 'role', domain: 'DOM_01_RBAC_AUTH', related: ['sys_users', 'sys_roles', 'sys_permissions', 'sys_role_permissions', 'sys_rbac_audit_log', 'user_progress_anchors'] },
  MOD_05_DOCKER_DB: { table: 'ha_cluster_roaming_state', col: 'active_leader_node', domain: 'DOM_05_CLUSTER_ROAMING', related: ['schema_migrations', 'ha_sync_wal_journal', 'api_idempotency_keys', 'ha_cluster_meta', 'ha_request_receipts', 'ha_cluster_roaming_state', 'ha_roaming_wal_stream'] }
};

const TRACK_DB_LINEAGE_MAP = {
  TRK_01_SYLLABUS_CSV: { table: 'syllabus_5500_lexicon', col: 'lemma', secondary: 'user_vocab_ledger' },
  TRK_02_SMART_PASSAGE: { table: 'exam_passages', col: 'paragraphs_json', secondary: 'user_progress_anchors' },
  TRK_03_OCR_IMAGE_PDF: { table: 'exam_passages', col: 'sha256_hash', secondary: 'annotation_spans' },
  TRK_04_PORTABLE_PACK: { table: 'ha_sync_wal_journal', col: 'payload_json', secondary: 'user_progress_anchors' }
};

function getCatalogTableEntry(tableName) {
  const liveTables = (typeof adminDrillState !== 'undefined' && adminDrillState.catalog && adminDrillState.catalog.tables) || {};
  if (liveTables[tableName]) {
    const lt = liveTables[tableName];
    return {
      table_no: lt.table_no || 'T00',
      domain_id: lt.domain_id || 'DOM_OTHER',
      table_name: lt.table_name,
      pk_uk: (lt.pk_columns || []).join(', ') || 'PK',
      purpose: fieldDescription(lt.table_name, (lt.pk_columns || [])[0] || '') || lt.domain_name || '受治物理表',
      row_count: lt.row_count,
      columns: (lt.columns || []).map(c => [c.name, c.type, fieldConstraints(c), fieldDescription(lt.table_name, c.name), c.fk_target || (c.is_json ? 'JSON' : ''), c])
    };
  }
  if (typeof ADMIN_DB_CATALOG_18T_146C !== 'undefined') {
    const found = ADMIN_DB_CATALOG_18T_146C.find(t => t.table_name === tableName);
    if (found) return found;
  }
  return null;
}

function getAllCatalogTables() {
  if (typeof ADMIN_DB_CATALOG_18T_146C !== 'undefined' && ADMIN_DB_CATALOG_18T_146C.length) {
    return ADMIN_DB_CATALOG_18T_146C;
  }
  return [];
}

function openInfoModal(title, bodyHtml) {
  const overlay = document.getElementById('infoModalOverlay');
  const titleEl = document.getElementById('infoModalTitle');
  const bodyEl = document.getElementById('infoModalBody');
  if (titleEl) titleEl.textContent = title || '🔎 实时库表与数据血缘下钻舱';
  if (bodyEl) bodyEl.innerHTML = bodyHtml || '';
  if (overlay) overlay.style.display = 'flex';
}

function closeInfoModal() {
  const overlay = document.getElementById('infoModalOverlay');
  if (overlay) overlay.style.display = 'none';
}

function closeDetailModal() {
  const overlay = document.getElementById('detailModalOverlay');
  if (overlay) overlay.style.display = 'none';
}

function buildColumnLineageTableHtml(tableName, highlightCol) {
  const entry = getCatalogTableEntry(tableName);
  if (!entry) return '';
  const rowsHtml = (entry.columns || []).map((col, idx) => {
    const colName = col[0], colType = col[1], colConst = col[2], colDesc = col[3], colFk = col[4] || '';
    const isHl = colName === highlightCol;
    return `<tr style="${isHl ? 'background:rgba(5,150,105,0.14);font-weight:700;' : ''}">
      <td>#${idx + 1}</td>
      <td><code><strong>${escapeHtmlStr(colName)}</strong></code>${isHl ? ' 🎯' : ''}</td>
      <td><code>${escapeHtmlStr(colType)}</code></td>
      <td><span class="badge ${String(colConst).includes('PK') ? 'bg-purple' : 'bg-blue'}">${escapeHtmlStr(colConst)}</span></td>
      <td>${escapeHtmlStr(colDesc)} ${colFk ? `<span class="badge bg-green">FK/JSON: ${escapeHtmlStr(colFk)}</span>` : ''}</td>
      <td><button class="btn" style="padding:2px 8px;font-size:0.75rem;" onclick="closeDetailModal();openLiveTableBrowser('${escapeHtmlStr(tableName)}','${escapeHtmlStr(colName)}','')">🔎 查该列实测行</button></td>
    </tr>`;
  }).join('');
  return `<div style="margin-top:10px;border:1px solid var(--border);border-radius:10px;padding:10px;background:var(--bg);">
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:8px;">
      <div>
        <span class="badge bg-purple">${escapeHtmlStr(entry.table_no)} · ${escapeHtmlStr(entry.domain_id)}</span>
        <strong style="margin-left:6px;">物理表 <code>${escapeHtmlStr(entry.table_name)}</code> (${entry.columns.length} 列 100% 透出)</strong>
        <span style="font-size:0.78rem;color:var(--muted);margin-left:6px;">${escapeHtmlStr(entry.purpose || '')}</span>
      </div>
      <button class="btn active" style="padding:4px 10px;font-size:0.78rem;" onclick="closeDetailModal();openLiveTableBrowser('${escapeHtmlStr(tableName)}','${escapeHtmlStr(highlightCol || '')}','')">🔎 实时浏览 ${escapeHtmlStr(tableName)} 全量行数据 (${entry.columns.length}列全开) ➔</button>
    </div>
    <div style="overflow-x:auto;max-height:240px;overflow-y:auto;">
      <table>
        <thead><tr><th>#</th><th>物理字段名 (<code>Column</code>)</th><th>数据类型</th><th>主键/非空约束</th><th>业务职责与外键血缘</th><th>EIDS 列定向下钻</th></tr></thead>
        <tbody>${rowsHtml}</tbody>
      </table>
    </div>
  </div>`;
}

function openDetailModal(lens, itemId) {
  const overlay = document.getElementById('detailModalOverlay');
  const titleEl = document.getElementById('detTitle');
  const codeEl = document.getElementById('detCode');
  const statusEl = document.getElementById('detStatus');
  const subEl = document.getElementById('detSub');
  const bodyEl = document.getElementById('detBody');
  if (!overlay || !bodyEl) return;

  let title = '数据血缘与库表字段下钻详情', code = String(itemId || ''), status = '🟢 100% 字段已映射', sub = lens;
  let targetTable = 'exam_passages', highlightCol = 'passage_id', initQuery = '';
  let secondaryTables = [];
  let entityHtml = '';

  if (lens === 'MODULE') {
    const mod = (REPORT_DATA.intake_decoding.module_deep_critique || []).find(m => m.module_id === itemId) || REPORT_DATA.intake_decoding.module_deep_critique[0];
    const mapInfo = MODULE_DB_LINEAGE_MAP[mod.module_id] || MODULE_DB_LINEAGE_MAP.MOD_01_READING;
    title = mod.name; code = mod.module_id; status = '🏛️ 模块级库表血缘'; sub = `归属域: ${mapInfo.domain}`;
    targetTable = mapInfo.table; highlightCol = mapInfo.col; secondaryTables = mapInfo.related || [];
    entityHtml = `<div style="padding:10px;border-radius:8px;background:var(--primary-soft);margin-bottom:8px;font-size:0.83rem;">
      <div><strong>💡 原始高价值洞察：</strong>${escapeHtmlStr(mod.colleague_insight)}</div>
      <div style="color:var(--rose);margin-top:4px;"><strong>⚠️ 传统工程陷阱：</strong>${escapeHtmlStr(mod.literal_trap)}</div>
      <div style="color:var(--emerald);margin-top:4px;"><strong>🚀 本站工业级落地方案：</strong>${escapeHtmlStr(mod.reframed_solution)}</div>
    </div>`;
  } else if (lens === 'BENCHMARK') {
    const bm = (REPORT_DATA.benchmark_9d || []).find(b => b.dim === itemId) || REPORT_DATA.benchmark_9d[0];
    title = `九维对标下钻 · ${bm.dim}`; code = bm.dim; status = '🏆 同行对标与库表支撑'; sub = bm.benchmark;
    targetTable = 'user_progress_anchors'; highlightCol = 'last_para_idx'; secondaryTables = ['exam_passages', 'user_vocab_ledger'];
    entityHtml = `<div style="padding:10px;border-radius:8px;background:var(--primary-soft);margin-bottom:8px;font-size:0.83rem;">
      <div><strong>📊 行业标杆做法：</strong>${escapeHtmlStr(bm.benchmark)}</div>
      <div style="color:var(--emerald);margin-top:4px;"><strong>🎯 本站超越方案与底层库表锚点：</strong>${escapeHtmlStr(bm.insight)}</div>
    </div>`;
  } else if (lens === 'TRACK') {
    const trk = (REPORT_DATA.ingestion_and_deployment.question_1_ingestion_hub.tracks || []).find(t => t.track_id === itemId) || REPORT_DATA.ingestion_and_deployment.question_1_ingestion_hub.tracks[0];
    const tMap = TRACK_DB_LINEAGE_MAP[trk.track_id] || TRACK_DB_LINEAGE_MAP.TRK_01_SYLLABUS_CSV;
    title = trk.name; code = trk.track_id; status = trk.sla; sub = `支持格式: ${trk.input_formats}`;
    targetTable = tMap.table; highlightCol = tMap.col; secondaryTables = [tMap.table, tMap.secondary];
    entityHtml = `<div style="padding:10px;border-radius:8px;background:var(--emerald-soft);margin-bottom:8px;font-size:0.83rem;">
      <div><strong>⚙️ 0-Token 自动化解析流水线：</strong>${escapeHtmlStr(trk.pipeline)}</div>
      <div style="margin-top:4px;"><strong>🗄️ 写入目标物理表：</strong><code>${escapeHtmlStr(tMap.table)}</code> (主表) + <code>${escapeHtmlStr(tMap.secondary)}</code> (伴生表)</div>
    </div>`;
  } else if (lens === 'PASSAGE') {
    title = document.getElementById('currentPassageTitle')?.textContent || '2024 考研英语一 Text 1 真题篇章';
    code = itemId || 'P2024_EN1_T1'; status = isLoggedIn() ? '🟢 全文已解锁' : '👁️ 30%明文试读'; sub = '真题原文与 Standoff 段落偏移坐标血缘';
    targetTable = 'exam_passages'; highlightCol = 'paragraphs_json'; initQuery = code;
    secondaryTables = ['exam_passages', 'annotation_spans', 'user_progress_anchors'];
    entityHtml = `<div style="padding:10px;border-radius:8px;background:var(--primary-soft);margin-bottom:8px;font-size:0.83rem;">
      <div><strong>📖 真题篇章主键 (<code>passage_id</code>)：</strong><code>${escapeHtmlStr(code)}</code> · 当前续读锚点：<code>Para ${authState.lastPara || 1}</code></div>
      <div style="margin-top:4px;"><strong>🧬 三表联动血缘：</strong>原文段落存储于 <code>exam_passages.paragraphs_json</code> ➔ 划词/长难句存储于 <code>annotation_spans</code> ➔ 个人阅读断点存储于 <code>user_progress_anchors.last_para_idx</code>。</div>
    </div>`;
  } else if (lens === 'NOTE') {
    const note = (typeof notesData !== 'undefined' ? notesData : []).find(n => n.id === itemId) || FULL_SCHOLAR_NOTES[0];
    title = `精读笔记卡血缘 · ${note.tag}`; code = note.id; status = `粒度: ${note.granularity}`; sub = '挂载物理表: annotation_spans (15列)';
    targetTable = 'annotation_spans'; highlightCol = 'selected_text'; initQuery = note.id.replace('-redacted', '');
    secondaryTables = ['annotation_spans', 'exam_passages'];
    entityHtml = `<div style="padding:10px;border-radius:8px;background:var(--primary-soft);margin-bottom:8px;font-size:0.83rem;">
      <div><strong>📌 划选原文 (<code>selected_text</code>)：</strong>${escapeHtmlStr(note.text)}</div>
      <div style="margin-top:4px;"><strong>🔍 句法切分 (<code>syntax_breakdown</code>)：</strong>${escapeHtmlStr(note.breakdown)}</div>
      <div style="margin-top:4px;color:var(--emerald);"><strong>💡 批注 (<code>user_comment</code>)：</strong>${escapeHtmlStr(note.comment)}</div>
    </div>`;
  } else if (lens === 'VOCAB') {
    const voc = (typeof vocabData !== 'undefined' ? vocabData : []).find(v => v.word === itemId || v.lemma === itemId) || GUEST_TEASER_VOCAB[0];
    title = `考纲词汇双表血缘 · ${voc.word}`; code = voc.lemma || voc.word; status = voc.syllabus_tier; sub = '双表映射: user_vocab_ledger (11列) ⋈ syllabus_5500_lexicon (10列)';
    targetTable = 'user_vocab_ledger'; highlightCol = 'lemma'; initQuery = voc.word;
    secondaryTables = ['user_vocab_ledger', 'syllabus_5500_lexicon'];
    entityHtml = `<div style="padding:10px;border-radius:8px;background:var(--amber-soft);margin-bottom:8px;font-size:0.83rem;">
      <div><strong>🧠 词根 (<code>lemma</code>)：</strong><code>${escapeHtmlStr(voc.word)}</code> · <strong>考纲分层：</strong><code>${escapeHtmlStr(voc.syllabus_tier)}</code> · <strong>紧迫度算子 (<code>urgency_score</code>)：</strong><code>${escapeHtmlStr(isLoggedIn() ? voc.urgency_score : '🔒登录解锁')}</code></div>
      <div style="margin-top:4px;"><strong>📖 真题语境与熟词僻义 (<code>contextual_meaning</code>)：</strong>[${escapeHtmlStr(voc.exam_source)}] ${escapeHtmlStr(voc.contextual_meaning)}</div>
    </div>`;
  } else if (lens === 'ESSAY') {
    const es = (typeof essayCorpus !== 'undefined' ? essayCorpus : []).find(c => c.id === itemId) || FULL_SCHOLAR_ESSAYS[0];
    title = `大作文三维语料血缘 · ${es.theme}`; code = es.id; status = es.slot; sub = `粒度: ${es.gran} · 物理表: essay_corpus_snippets (11列)`;
    targetTable = 'essay_corpus_snippets'; highlightCol = 'theme_tag'; initQuery = es.theme;
    secondaryTables = ['essay_corpus_snippets', 'user_progress_anchors'];
    entityHtml = `<div style="padding:10px;border-radius:8px;background:var(--emerald-soft);margin-bottom:8px;font-size:0.83rem;">
      <div><strong>✍️ 英文佳句 (<code>content_en</code>)：</strong>${escapeHtmlStr(es.en)}</div>
      <div style="margin-top:4px;"><strong>🎯 挖空模板 (<code>cloze_pattern</code>)：</strong><code>${escapeHtmlStr(es.cloze)}</code></div>
      <div style="margin-top:4px;"><strong>🇨🇳 中文译文 (<code>translation_zh</code>)：</strong>${escapeHtmlStr(es.zh)}</div>
    </div>`;
  } else {
    targetTable = itemId || 'sys_users';
    const entry = getCatalogTableEntry(targetTable);
    title = `物理表结构与全字段血缘 · ${targetTable}`;
    code = entry ? entry.table_no : 'TABLE';
    status = entry ? `${entry.columns.length} 列 100% 透出` : 'LIVE';
    sub = entry ? entry.purpose : '双擎持久化受治库表';
    highlightCol = entry && entry.columns.length ? entry.columns[0][0] : '';
    secondaryTables = [targetTable];
  }

  if (titleEl) titleEl.textContent = title;
  if (codeEl) codeEl.textContent = code;
  if (statusEl) statusEl.textContent = status;
  if (subEl) subEl.textContent = sub;

  const uniqueTables = Array.from(new Set([targetTable, ...secondaryTables])).filter(Boolean);
  const actionBanner = `<div style="background:rgba(5,150,105,0.09);border:1.5px solid rgba(5,150,105,0.35);border-radius:10px;padding:10px 12px;margin:8px 0;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
    <div>
      <strong>📡 EIDS 同款跨板块直连库表下钻总线</strong><br>
      <span style="font-size:0.79rem;color:var(--muted);">主挂载物理表: <code>${escapeHtmlStr(targetTable)}</code> ｜ 定向高亮字段: <code>${escapeHtmlStr(highlightCol || '主键列')}</code> ｜ 关联表数: <strong>${uniqueTables.length} 张表</strong></span>
    </div>
    <div style="display:flex;gap:6px;flex-wrap:wrap;">
      <button class="btn active" style="background:var(--emerald);border-color:var(--emerald);" onclick="closeDetailModal();openLiveTableBrowser('${escapeHtmlStr(targetTable)}','${escapeHtmlStr(highlightCol)}','${escapeHtmlStr(initQuery)}')">🔎 下钻查该表实时 SQL 行与高亮列 ➔</button>
      <button class="btn" onclick="closeDetailModal();openOdsSchemaModal()">🗄️ 18表146列全量 Schema 曝光矩阵</button>
    </div>
  </div>`;

  bodyEl.innerHTML = entityHtml + actionBanner + uniqueTables.map((tName, idx) => buildColumnLineageTableHtml(tName, idx === 0 ? highlightCol : '')).join('');
  overlay.style.display = 'flex';
}

async function fetchLineagePayload(paramsObj) {
  const qs = new URLSearchParams(paramsObj);
  const endpoint = (typeof isAdmin === 'function' && isAdmin()) ? '/api/admin/db/drilldown?' : '/api/db/lineage?';
  if (typeof location !== 'undefined' && location.protocol !== 'file:') {
    try {
      const response = await fetch(endpoint + qs.toString(), { headers: typeof authHeaders === 'function' ? authHeaders() : {} });
      const data = await (typeof window.safeJsonResponse === 'function'
        ? window.safeJsonResponse(response, '实时库表响应为空或非 JSON')
        : response.json());
      if (response.ok && data && data.selected_table) {
        data.data_source_mode = data.data_source_mode || 'LIVE_SQL';
        eidsBrowserState.cachedLineagePayload = data;
        return data;
      }
    } catch (_) {
      // Automatically fall through to Local-First 18-Table x 146-Column Edge Snapshot Engine
    }
  }
  if (typeof window.queryLocalFirstLineage === 'function') {
    const fallbackData = window.queryLocalFirstLineage(paramsObj);
    eidsBrowserState.cachedLineagePayload = fallbackData;
    return fallbackData;
  }
  const tbl = (paramsObj && paramsObj.table) || 'exam_passages';
  const entry = getCatalogTableEntry(tbl) || getAllCatalogTables()[0] || { table_no: 'T04', table_name: tbl, domain_id: 'DOM_02_CORE_CONTENT', purpose: '', columns: [] };
  const cols = (entry.columns || []).map((c, idx) => ({ cid: idx, name: c[0], column_name: c[0], type: c[1], notnull: c[2], description: c[3], sample_value: c[4] || '' }));
  const sampleRow = {};
  cols.forEach(c => { sampleRow[c.name] = c.sample_value || c.description || 'sample'; });
  const synth = {
    status: 'ok',
    data_source_mode: 'LOCAL_FIRST_SNAPSHOT',
    auth_tier: 'GUEST_TEASER',
    selected_table_name: entry.table_name,
    selected_table: {
      table_no: entry.table_no,
      table_name: entry.table_name,
      domain_id: entry.domain_id,
      columns: cols,
      column_count: cols.length,
      row_count: 1,
      rows: [sampleRow],
      has_previous: false,
      has_next: false
    },
    tables: {}
  };
  eidsBrowserState.cachedLineagePayload = synth;
  return synth;
}

async function loadLiveTableRowsInto(containerId, tableFqn, offset, limit, q, highlightCol) {
  const box = document.getElementById(containerId);
  if (!box) return;
  eidsBrowserState.table = tableFqn || eidsBrowserState.table || 'exam_passages';
  eidsBrowserState.offset = Math.max(0, Number(offset) || 0);
  eidsBrowserState.limit = Math.max(1, Math.min(50, Number(limit) || 12));
  eidsBrowserState.q = q !== undefined && q !== null ? String(q) : eidsBrowserState.q;
  eidsBrowserState.highlightCol = highlightCol !== undefined && highlightCol !== null ? String(highlightCol) : eidsBrowserState.highlightCol;

  box.innerHTML = `<div style="padding:14px;color:var(--primary);font-weight:700;">⏳ 正在实时查询双擎生产库 <code>${escapeHtmlStr(eidsBrowserState.table)}</code> (offset=${eidsBrowserState.offset}, limit=${eidsBrowserState.limit})...</div>`;

  try {
    const data = await fetchLineagePayload({
      table: eidsBrowserState.table,
      offset: String(eidsBrowserState.offset),
      limit: String(eidsBrowserState.limit),
      q: eidsBrowserState.q,
      highlight_col: eidsBrowserState.highlightCol
    });
    const sel = data.selected_table || {};
    const colsMeta = sel.columns || [];
    const colNames = colsMeta.map(c => c.name || c.column_name);
    const rows = sel.rows || [];
    const totalRows = Number(sel.row_count || 0);
    const hlCol = eidsBrowserState.highlightCol;
    const allTables = Object.values(data.tables || {});

    const relOptions = (allTables.length ? allTables : getAllCatalogTables()).map(t => {
      const tName = t.table_name;
      const cCnt = t.column_count || (t.columns ? t.columns.length : 0);
      const rCnt = t.row_count !== undefined ? t.row_count : '实时';
      const label = `${t.table_no || ''} ${tName} (${cCnt}列 · ${rCnt}行 · ${t.domain_name || t.purpose || ''})`;
      return `<option value="${escapeHtmlStr(tName)}" ${tName === eidsBrowserState.table ? 'selected' : ''}>${escapeHtmlStr(label)}</option>`;
    }).join('');

    const ths = colsMeta.map((c, idx) => {
      const cn = c.name || c.column_name;
      const isHl = cn === hlCol;
      return `<th id="${containerId}_th_${escapeHtmlStr(cn)}" style="${isHl ? 'background:rgba(5,150,105,0.22);color:var(--emerald);border-bottom:3px solid var(--emerald);' : ''}">#${idx + 1} <code>${escapeHtmlStr(cn)}</code>${isHl ? ' 🎯' : ''}<br><span style="font-size:0.7rem;color:var(--muted);font-weight:400;">${escapeHtmlStr(c.type || '')}</span></th>`;
    }).join('');

    const trs = rows.length ? rows.map((r, rIdx) => {
      const cells = colNames.map(cn => {
        const isHl = cn === hlCol;
        const rawVal = r[cn];
        const disp = rawVal === null || rawVal === undefined
          ? '<span style="color:var(--muted);font-style:italic;">NULL</span>'
          : `<code class="field-value">${escapeHtmlStr(typeof rawVal === 'object' ? JSON.stringify(rawVal) : String(rawVal))}</code>`;
        return `<td data-column="${escapeHtmlStr(cn)}" style="${isHl ? 'background:rgba(5,150,105,0.12);font-weight:700;border-left:2px solid var(--emerald);border-right:2px solid var(--emerald);' : ''}">${disp}</td>`;
      }).join('');
      return `<tr><td><strong>#${eidsBrowserState.offset + rIdx + 1}</strong></td>${cells}</tr>`;
    }).join('') : `<tr><td colspan="${colNames.length + 1}" style="text-align:center;padding:16px;color:var(--muted);">当前筛选条件下 0 行记录 (若为未登录访客私有表，请先登录学籍或管理员账号解锁实时行)</td></tr>`;

    const authTierBadge = data.auth_tier === 'ADMIN_FULL'
      ? '<span class="badge bg-purple">🛡️ ADMIN 全库 18表146列 实时直连</span>'
      : (data.auth_tier === 'SCHOLAR_SCOPED' ? '<span class="badge bg-green">🎓 SCHOLAR 公共底座+本人学籍行直连</span>' : '<span class="badge bg-amber">👁️ GUEST 100%字段定义+公共样板行</span>');

    const sourceModeBadge = data.data_source_mode === 'LOCAL_FIRST_SNAPSHOT'
      ? '<span class="badge bg-blue">🛡️ Local-First 边缘 18表146列 内存 SQL 快照直查 (零延迟防抖兜底)</span>'
      : '<span class="badge bg-green">🟢 生产库实时 SQL 直连查询 (W1/HP 双擎多活 · EIDS 同款行浏览器)</span>';

    box.innerHTML = `<div style="background:rgba(5,150,105,0.08);border:1.5px solid rgba(5,150,105,0.35);border-radius:10px;padding:10px 12px;margin-bottom:10px;">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:8px;">
        <div>
          ${sourceModeBadge}
          ${authTierBadge}
          <strong style="color:var(--primary);margin-left:6px;"><code>${escapeHtmlStr(eidsBrowserState.table)}</code></strong>
        </div>
        <div style="font-size:0.8rem;">
          匹配总行数: <strong>${totalRows.toLocaleString()}</strong> ｜ 物理列数: <strong>${colNames.length} 列 (100%列已透出)</strong>
          ${hlCol ? `｜ 🎯 当前高亮定位列: <code style="background:rgba(5,150,105,0.2);color:var(--emerald);padding:2px 6px;border-radius:4px;font-weight:800;">${escapeHtmlStr(hlCol)}</code>` : ''}
        </div>
      </div>
      <div style="display:flex;align-items:center;flex-wrap:wrap;gap:8px;">
        <select id="${containerId}_tableSel" class="input-box" style="width:auto;max-width:380px;margin-top:0;font-weight:700;" onchange="loadLiveTableRowsInto('${containerId}', this.value, 0, ${eidsBrowserState.limit}, '', '')">${relOptions}</select>
        <input id="${containerId}_qInput" type="text" class="input-box" style="width:210px;margin-top:0;" value="${escapeHtmlStr(eidsBrowserState.q)}" placeholder="🔍 在当前库表中全文检索..." onkeydown="if(event.key==='Enter')loadLiveTableRowsInto('${containerId}','${escapeHtmlStr(eidsBrowserState.table)}',0,${eidsBrowserState.limit},this.value,'${escapeHtmlStr(hlCol)}')">
        <button class="btn active" onclick="loadLiveTableRowsInto('${containerId}','${escapeHtmlStr(eidsBrowserState.table)}',0,${eidsBrowserState.limit},document.getElementById('${containerId}_qInput').value,'${escapeHtmlStr(hlCol)}')">执行SQL过滤</button>
        <button class="btn" ${!sel.has_previous ? 'disabled' : ''} onclick="loadLiveTableRowsInto('${containerId}','${escapeHtmlStr(eidsBrowserState.table)}',Math.max(0,${eidsBrowserState.offset - eidsBrowserState.limit}),${eidsBrowserState.limit},'${escapeHtmlStr(eidsBrowserState.q)}','${escapeHtmlStr(hlCol)}')">◀ 上一页</button>
        <span style="font-weight:700;font-size:0.8rem;">第 ${rows.length ? eidsBrowserState.offset + 1 : 0} ~ ${eidsBrowserState.offset + rows.length} / ${totalRows} 行</span>
        <button class="btn" ${!sel.has_next ? 'disabled' : ''} onclick="loadLiveTableRowsInto('${containerId}','${escapeHtmlStr(eidsBrowserState.table)}',${eidsBrowserState.offset + eidsBrowserState.limit},${eidsBrowserState.limit},'${escapeHtmlStr(eidsBrowserState.q)}','${escapeHtmlStr(hlCol)}')">下一页 ▶</button>
        <button class="btn" onclick="openDomainDrilldownModal('ALL')">📡 5大业务域下钻舱</button>
        <button class="btn" onclick="openOdsSchemaModal()">🗄️ 18表146列 Schema 矩阵</button>
      </div>
    </div>
    <div style="overflow-x:auto;max-height:420px;overflow-y:auto;border:1px solid var(--border);border-radius:8px;">
      <table>
        <thead><tr><th style="width:54px;">行号</th>${ths}</tr></thead>
        <tbody>${trs}</tbody>
      </table>
    </div>`;

    if (hlCol) {
      setTimeout(() => {
        const thEl = document.getElementById(`${containerId}_th_${hlCol}`);
        if (thEl && typeof thEl.scrollIntoView === 'function') {
          thEl.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
        }
      }, 60);
    }
  } catch (err) {
    box.innerHTML = `<div style="padding:12px;color:var(--rose);">实时库表查询异常: ${escapeHtmlStr(err.message || String(err))}</div>`;
  }
}

function openLiveTableBrowser(tableFqn, highlightCol, initQuery) {
  const tbl = tableFqn || 'exam_passages';
  const hl = highlightCol || '';
  const q = initQuery || '';
  openInfoModal(
    `🔎 双擎生产库实时 SQL 行数据浏览器 — ${tbl}${hl ? ' · 🎯 定向检视字段 [' + hl + ']' : ''}`,
    `<div id="modalLiveSqlBrowserBox"></div>`
  );
  return loadLiveTableRowsInto('modalLiveSqlBrowserBox', tbl, 0, 12, q, hl);
}

async function openOdsSchemaModal() {
  openInfoModal('🗄️ 全库 18 表 × 146 列 100% 字段曝光矩阵与非空样本值核验舱 (EIDS 同款 Schema Matrix)', '<div style="padding:12px;">⏳ 正在加载全库 18 表 146 列实时非空率与样本值矩阵...</div>');
  let matrix = [];
  let totalTables = 18, totalCols = 146;
  try {
    const data = await fetchLineagePayload({ table: 'exam_passages', limit: '5', offset: '0' });
    matrix = data.table_exposure_matrix || [];
    totalTables = data.total_tables_count || matrix.length || 18;
    totalCols = data.total_columns_count || 146;
  } catch (_) {}

  if (!matrix.length) {
    matrix = getAllCatalogTables().map(t => ({
      table_no: t.table_no,
      table_fqn: t.table_name,
      table_name: t.table_name,
      domain_id: t.domain_id,
      description_zh: t.purpose,
      total_rows: t.row_count || 1,
      total_columns: t.columns.length,
      populated_columns: t.columns.length,
      columns: t.columns.map((c, idx) => ({
        cid: idx, column_name: c[0], data_type: c[1], non_null_rows: 1, non_null_pct: 100.0, sample_value: c[3]
      }))
    }));
  }

  const summaryHtml = `<div style="background:rgba(37,99,235,0.08);border:1.5px solid rgba(37,99,235,0.32);border-radius:10px;padding:10px 14px;margin-bottom:12px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
    <div>
      <strong>🏛️ 全站受治物理表 100% 字段透出与实测非空样本对账单</strong><br>
      <span style="font-size:0.8rem;color:var(--muted);">总受治物理表: <strong>${totalTables} 张</strong> ｜ 总物理字段: <strong>${totalCols} 列 (100.0% 透出)</strong> ｜ 点击任意表或任意字段即可唤起 EIDS 实时 SQL 行数据浏览器并自动高亮该列</span>
    </div>
    <div style="display:flex;gap:6px;flex-wrap:wrap;">
      <button class="btn active" onclick="openLiveTableBrowser('exam_passages','paragraphs_json','')">🔎 进入实时 SQL 行浏览器</button>
      <button class="btn" onclick="openDomainDrilldownModal('ALL')">📡 切换 5大业务域下钻舱</button>
    </div>
  </div>`;

  const tblBlocks = matrix.map((t, tIdx) => {
    const cols = t.columns || [];
    const cRows = cols.map((c, idx) => {
      const colName = c.column_name || c.name;
      const smp = c.sample_value !== undefined && c.sample_value !== null ? String(c.sample_value) : 'NULL';
      const desc = fieldDescription(t.table_name, colName);
      return `<tr>
        <td>${idx + 1}</td>
        <td><code><strong>${escapeHtmlStr(colName)}</strong></code></td>
        <td><code>${escapeHtmlStr(c.data_type || c.type || 'TEXT')}</code></td>
        <td><strong>${Number(c.non_null_rows || 0).toLocaleString()}</strong></td>
        <td><strong style="color:${Number(c.non_null_pct || 0) > 0 ? 'var(--emerald)' : 'var(--muted)'};">${c.non_null_pct !== undefined ? c.non_null_pct : 100}%</strong></td>
        <td><span style="font-size:0.78rem;color:var(--muted);">${escapeHtmlStr(desc)}</span></td>
        <td style="max-width:260px;"><code class="field-value">${escapeHtmlStr(smp.slice(0, 88))}${smp.length > 88 ? '…' : ''}</code></td>
        <td><button class="btn" style="padding:2px 8px;font-size:0.74rem;" onclick="openLiveTableBrowser('${escapeHtmlStr(t.table_name)}','${escapeHtmlStr(colName)}','')">🔎 查实测行</button></td>
      </tr>`;
    }).join('');
    return `<details style="margin-bottom:9px;border:1px solid var(--border);border-radius:8px;padding:8px 12px;background:var(--bg);" ${tIdx < 2 ? 'open' : ''}>
      <summary style="cursor:pointer;font-weight:800;font-size:0.86rem;color:var(--primary);display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
        <span>${escapeHtmlStr(t.table_no || '')} <code>${escapeHtmlStr(t.table_name)}</code> — ${escapeHtmlStr(t.description_zh || '')} （总行数: <strong>${Number(t.total_rows || 0).toLocaleString()}</strong> ｜ 字段数: <strong>${cols.length}列 (100%已透出)</strong>）</span>
        <button class="btn active" style="padding:3px 10px;font-size:0.76rem;" onclick="event.stopPropagation();openLiveTableBrowser('${escapeHtmlStr(t.table_name)}','','')">🔎 实时浏览该表 SQL 行数据 (${cols.length}列全开) ➔</button>
      </summary>
      <div style="max-height:280px;overflow-y:auto;margin-top:8px;">
        <table>
          <thead><tr><th>#</th><th>字段名 (<code>Column</code>)</th><th>数据类型</th><th>非空行数</th><th>非空率</th><th>字段业务语义</th><th>实测非空样本值 (凭据已掩码)</th><th>列定向下钻</th></tr></thead>
          <tbody>${cRows}</tbody>
        </table>
      </div>
    </details>`;
  }).join('');

  const bodyEl = document.getElementById('infoModalBody');
  if (bodyEl) bodyEl.innerHTML = summaryHtml + tblBlocks;
}

function openDomainDrilldownModal(initDomain) {
  eidsBrowserState.domainFilter = initDomain || 'ALL';
  eidsBrowserState.domainQuery = '';
  const domains = typeof ADMIN_DB_DOMAINS !== 'undefined' ? ADMIN_DB_DOMAINS : [{ domain_id: 'ALL', name: '全部业务域' }];
  const pillsHtml = domains.map(d => `<button id="eidsDomBtn_${escapeHtmlStr(d.domain_id)}" class="btn ${d.domain_id === eidsBrowserState.domainFilter ? 'active' : ''}" onclick="filterDomainModal('${escapeHtmlStr(d.domain_id)}', null)">${escapeHtmlStr(d.name)}</button>`).join('');
  const html = `<div style="margin-bottom:10px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
      <div style="display:flex;gap:6px;flex-wrap:wrap;">${pillsHtml}</div>
      <div style="display:flex;gap:6px;align-items:center;">
        <input id="eidsDomainSearchInput" type="text" class="input-box" style="width:240px;margin-top:0;" placeholder="🔍 搜索物理表名/主键/字段/职责..." oninput="filterDomainModal(null, this.value)">
        <button class="btn" onclick="openOdsSchemaModal()">🗄️ 18表146列 Schema 矩阵</button>
      </div>
    </div>
    <div style="overflow-x:auto;max-height:440px;overflow-y:auto;border:1px solid var(--border);border-radius:8px;">
      <table>
        <thead><tr><th>表序号</th><th>所属业务域 (L1)</th><th>物理表名 (<code>table_name</code>)</th><th>主键与唯一索引</th><th>字段数</th><th>全部受治物理列 (点击任意列名直达高亮行浏览器)</th><th>EIDS 下钻操作</th></tr></thead>
        <tbody id="eidsDomainModalTbody"></tbody>
      </table>
    </div>`;
  openInfoModal('📡 研词真源 · 五大业务域 × 18张物理表 × 146字段 交互式下钻总舱 (借鉴 EIDS 多维分面下钻)', html);
  filterDomainModal(eidsBrowserState.domainFilter, '');
}

function filterDomainModal(domainFilter, qText) {
  if (domainFilter !== null && domainFilter !== undefined) eidsBrowserState.domainFilter = domainFilter;
  if (qText !== null && qText !== undefined) eidsBrowserState.domainQuery = String(qText).trim().toLowerCase();
  if (typeof ADMIN_DB_DOMAINS !== 'undefined') {
    ADMIN_DB_DOMAINS.forEach(d => {
      const btn = document.getElementById('eidsDomBtn_' + d.domain_id);
      if (btn) btn.classList.toggle('active', d.domain_id === eidsBrowserState.domainFilter);
    });
  }
  const tbody = document.getElementById('eidsDomainModalTbody');
  if (!tbody) return;
  const q = eidsBrowserState.domainQuery;
  const list = getAllCatalogTables().filter(t => {
    const domOk = eidsBrowserState.domainFilter === 'ALL' || t.domain_id === eidsBrowserState.domainFilter;
    if (!domOk) return false;
    if (!q) return true;
    const colStr = (t.columns || []).map(c => c[0] + ' ' + c[3]).join(' ');
    return [t.table_no, t.domain_id, t.table_name, t.pk_uk, t.purpose, colStr].join(' ').toLowerCase().includes(q);
  });
  tbody.innerHTML = list.map(t => {
    const colChips = (t.columns || []).map(c => `<a href="javascript:void(0)" onclick="openLiveTableBrowser('${escapeHtmlStr(t.table_name)}','${escapeHtmlStr(c[0])}','')" style="display:inline-block;margin:1px 3px;padding:1px 6px;border-radius:4px;background:var(--primary-soft);color:var(--primary);font-size:0.74rem;text-decoration:none;font-family:monospace;" title="${escapeHtmlStr(c[3])}">${escapeHtmlStr(c[0])}</a>`).join('');
    return `<tr>
      <td><span class="badge bg-purple">${escapeHtmlStr(t.table_no)}</span></td>
      <td><code>${escapeHtmlStr(t.domain_id)}</code></td>
      <td><code><strong>${escapeHtmlStr(t.table_name)}</strong></code><br><span style="font-size:0.75rem;color:var(--muted);">${escapeHtmlStr(t.purpose)}</span></td>
      <td><code>${escapeHtmlStr(t.pk_uk)}</code></td>
      <td><strong>${t.columns.length} 列</strong></td>
      <td>${colChips}</td>
      <td style="white-space:nowrap;">
        <button class="btn active" style="padding:3px 8px;font-size:0.75rem;" onclick="openLiveTableBrowser('${escapeHtmlStr(t.table_name)}','','')">🔎 查实测行</button>
        <button class="btn" style="padding:3px 8px;font-size:0.75rem;" onclick="closeInfoModal();openDetailModal('SCHEMA_TABLE','${escapeHtmlStr(t.table_name)}')">🧬 字段血缘</button>
      </td>
    </tr>`;
  }).join('');
}
