// Account summary actions bind values as data, never as executable HTML.
let adminAccountsTask = null, adminAccountsToken = '';
function loadAdminRbacData() {
  if (!isAdmin()) return Promise.resolve();
  const token = authState.token;
  if (adminAccountsTask && adminAccountsToken === token) return adminAccountsTask;
  adminAccountsToken = token;
  const task = Promise.all([loadAdminAccounts(token), loadAdminDbDrilldown()]);
  adminAccountsTask = task;
  task.finally(() => { if (adminAccountsTask === task) adminAccountsTask = null; });
  return task;
}
async function loadAdminAccounts(token) {
  const status = document.getElementById('adminAccountsStatus');
  if (status) status.textContent = '正在加载账号 (Loading accounts)';
  try {
    const response = await fetch('/api/admin/users', {headers:authHeaders()});
    const data = await response.json();
    if (authState.token !== token || !isAdmin()) return;
    if (response.status === 401 || response.status === 403) {
      resetPrivateSession('会话或权限已变更，请重新登录 (Session or permission changed)'); return;
    }
    if (!response.ok) throw new Error(data.message || '账号加载失败 (Accounts unavailable)');
    const select = document.getElementById('adminDrillUserSelect');
    select.innerHTML = '<option value="">全部账号 (All accounts)</option>' + data.users.map(u =>
      '<option value="' + escapeHtmlStr(u.user_id) + '">' + escapeHtmlStr(u.user_id + ' · ' + u.display_name) + '</option>').join('');
    select.value = adminDrillState.selectedUser;
    renderAdminAccounts(data.users);
    const audit = document.getElementById('adminAuditTableBody');
    audit.innerHTML = data.audit_logs.map(r => '<tr>' +
      [r.audit_id, fieldValue(r.actor_user_id) + ' / ' + fieldValue(r.actor_role),
       r.target_user_id, r.action, r.detail_json, r.client_ip, r.created_at]
        .map(value => '<td><code class="field-value">' + escapeHtmlStr(fieldValue(value)) + '</code></td>').join('') + '</tr>').join('');
    if (status) status.textContent = '账号已更新；完整审计记录请在下方选择审计表 (Accounts updated; browse the audit table below for all records)';
  } catch (error) {
    if (authState.token !== token || !isAdmin()) return;
    document.getElementById('adminUsersTableBody').innerHTML = '';
    document.getElementById('adminAuditTableBody').innerHTML = '';
    if (status) status.textContent = '加载失败 (Load failed): ' + error.message;
  }
}
function renderAdminAccounts(users) {
  const body = document.getElementById('adminUsersTableBody');
  body.innerHTML = users.map(u => {
    const values = [u.user_id + ' / ' + u.username, u.display_name, u.role + ' / ' + u.account_status,
      u.passcode_hash + ' / ' + u.passcode_salt + ' / ' + u.token_secret,
      u.failed_login_count + ' / ' + u.created_by, [u.created_at,u.last_login_at,u.password_updated_at].join(' / ')];
    const button = (label, action) => '<button class="btn" data-account-action="' + action +
      '" data-user="' + escapeHtmlStr(u.user_id) + '">' + escapeHtmlStr(label) + '</button>';
    let actions = button('查看数据 (Data)', 'drill') + button('重置密码 (Reset)', 'reset');
    if (u.user_id !== authState.userId) actions += button('切换角色 (Role)', 'role') + button('切换启用 (Status)', 'status');
    return '<tr>' + values.map(v => '<td><code class="field-value">' + escapeHtmlStr(v) + '</code></td>').join('') + '<td>' + actions + '</td></tr>';
  }).join('');
  bindDataClick(body, 'data-account-action', (action, button) => {
    const id = button.getAttribute('data-user'), user = users.find(u => u.user_id === id);
    if (!user) return;
    if (action === 'drill') {
      adminDrillState.selectedTable = 'sys_users';
      selectDrillUserCascade(id);
      document.getElementById('admin5LayerDrilldownCard').scrollIntoView({block:'start'});
    } else if (action === 'reset') {
      document.getElementById('adminResetTarget').value = id;
      document.getElementById('adminResetPwd').focus();
    } else if (action === 'role') {
      toggleUserRoleStatus(id, user.role === 'ADMIN' ? 'SCHOLAR' : 'ADMIN', user.account_status);
    } else if (action === 'status') {
      toggleUserRoleStatus(id, user.role, user.account_status === 'ACTIVE' ? 'DISABLED' : 'ACTIVE');
    }
  });
}
