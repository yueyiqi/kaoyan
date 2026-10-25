// Request generations prevent a slow response from replacing a newer selection or session.
let drillRequestGeneration = 0;

function resetAdminDrilldown() {
  ++drillRequestGeneration;
  Object.assign(adminDrillState, {selectedDomain:'ALL', selectedTable:'sys_users', selectedUser:'',
    selectedRowIdx:0, offset:0, limit:25, filterColumn:'', filterValue:'', livePayload:null,
    catalog:null, loading:false, error:''});
  ['adminDrillDomainBar','adminDrillTableBar','adminDrillRowTableHead','adminDrillRowTableBody',
    'adminInspectorTableBody','adminFullFieldCatalogBody','dbSchemaTableBody','adminUserCascadeSummary'].forEach(id => {
    const el = document.getElementById(id); if (el) el.innerHTML = '';
  });
}

async function loadAdminDbDrilldown() {
  if (!isAdmin()) return;
  const generation = ++drillRequestGeneration, token = authState.token;
  adminDrillState.loading = true;
  adminDrillState.error = '';
  adminDrillState.livePayload = null;
  renderAdminDrilldownUI();
  const qs = new URLSearchParams({table:adminDrillState.selectedTable,
    limit:String(adminDrillState.limit || 25), offset:String(adminDrillState.offset || 0)});
  if (adminDrillState.selectedUser) qs.set('user_id', adminDrillState.selectedUser);
  if (adminDrillState.filterColumn) {
    qs.set('filter_column', adminDrillState.filterColumn);
    qs.set('filter_value', adminDrillState.filterValue);
  }
  try {
    const response = await fetch('/api/admin/db/drilldown?' + qs.toString(), {headers:authHeaders()});
    const data = await response.json();
    if (generation !== drillRequestGeneration || token !== authState.token || !isAdmin()) return;
    if (response.status === 401 || response.status === 403) {
      resetPrivateSession('会话或权限已变更，请重新登录 (Session or permission changed)');
      return;
    }
    if (!response.ok) throw new Error(data.message || '数据暂不可用 (Data unavailable)');
    adminDrillState.livePayload = data;
    adminDrillState.catalog = data;
  } catch (error) {
    if (generation !== drillRequestGeneration || token !== authState.token || !isAdmin()) return;
    adminDrillState.error = error.message || '数据加载失败 (Load failed)';
  } finally {
    if (generation === drillRequestGeneration && token === authState.token && isAdmin()) {
      adminDrillState.loading = false;
      renderAdminDrilldownUI();
      renderFullFieldCatalog();
      renderRuntimeSchema();
    }
  }
}

function selectDrillDomain(domainId) {
  adminDrillState.selectedDomain = domainId;
  const tables = runtimeCatalog().filter(t => domainId === 'ALL' || t.domain_id === domainId);
  if (tables.length && !tables.some(t => t.table_name === adminDrillState.selectedTable)) {
    adminDrillState.selectedTable = tables[0].table_name;
  }
  adminDrillState.offset = 0;
  adminDrillState.filterColumn = '';
  adminDrillState.selectedRowIdx = 0;
  return loadAdminDbDrilldown();
}

function selectDrillTable(name) {
  adminDrillState.selectedTable = name;
  adminDrillState.offset = 0;
  adminDrillState.filterColumn = '';
  adminDrillState.selectedRowIdx = 0;
  return loadAdminDbDrilldown();
}

function selectDrillUserCascade(userId) {
  adminDrillState.selectedUser = userId || '';
  adminDrillState.offset = 0;
  adminDrillState.filterColumn = '';
  adminDrillState.selectedRowIdx = 0;
  const select = document.getElementById('adminDrillUserSelect');
  if (select) select.value = userId || '';
  return loadAdminDbDrilldown();
}

function inspectDrillRow(index) {
  adminDrillState.selectedRowIdx = index;
  renderAdminDrilldownUI();
}

function jumpToForeignKeyTarget(spec, value) {
  if (!spec || value === null || value === undefined) return;
  const index = spec.lastIndexOf('.');
  adminDrillState.selectedDomain = 'ALL';
  adminDrillState.selectedTable = spec.slice(0, index);
  adminDrillState.filterColumn = spec.slice(index + 1);
  adminDrillState.filterValue = String(value);
  adminDrillState.selectedUser = '';
  adminDrillState.offset = 0;
  adminDrillState.selectedRowIdx = 0;
  return loadAdminDbDrilldown();
}

function pageAdminDrill(direction) {
  const table = adminDrillState.livePayload?.selected_table;
  if (!table || (direction > 0 ? !table.has_next : !table.has_previous)) return;
  adminDrillState.offset = Math.max(0, table.offset + direction * table.limit);
  adminDrillState.selectedRowIdx = 0;
  return loadAdminDbDrilldown();
}

function applyDrillFilter() {
  adminDrillState.filterColumn = document.getElementById('adminFilterColumn').value;
  adminDrillState.filterValue = document.getElementById('adminFilterValue').value;
  adminDrillState.offset = 0;
  adminDrillState.selectedRowIdx = 0;
  return loadAdminDbDrilldown();
}
