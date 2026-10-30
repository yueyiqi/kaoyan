// Authentication has one visible state and one in-flight request.
let loginBusy = false;
let sessionGeneration = 0;

function loginNotice(message, error = false) {
  const status = document.getElementById('loginStatus');
  if (status) { status.textContent = message; status.style.color = error ? 'var(--rose)' : 'var(--emerald)'; }
}

function loginPending(busy) {
  loginBusy = busy;
  const button = document.getElementById('loginSubmitBtn');
  if (button) {
    button.disabled = busy;
    button.textContent = busy ? '正在登录 (Signing in)' : '🔑 登录并恢复进度';
  }
}

async function loginWithCredentials() {
  if (loginBusy) return;
  if (isLoggedIn()) { switchTab(isAdmin() ? 6 : 2); return; }
  const uInput = document.getElementById('scholarUserInput');
  const kInput = document.getElementById('scholarKeyInput');
  const username = uInput.value.trim();
  const passcode = kInput.value; // Spaces are part of a password.
  if (!username || !passcode) {
    loginNotice('请输入账号与密码 (Enter account and password)', true);
    (!username ? uInput : kInput).focus();
    return;
  }
  const generation = ++sessionGeneration;
  kInput.value = '';
  loginPending(true);
  loginNotice('正在验证账号，请稍候 (Verifying your account)');
  try {
    const response = await fetch('/api/auth/login', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({username, passcode})
    });
    const data = await (window.safeJsonResponse ? window.safeJsonResponse(response, '登录服务暂不可用，请稍后重试') : response.json());
    if (generation !== sessionGeneration) return;
    if (!response.ok) throw new Error(data.message || '登录失败，请重试 (Sign-in failed)');
    if (!data.token || !['ADMIN', 'SCHOLAR'].includes(data.role)) throw new Error('登录响应无效 (Invalid sign-in response)');
    authState = {role: data.role, userId: data.user_id, displayName: data.display_name || data.user_id,
      token: data.token, lastPara: data.anchor?.last_para_idx || 1, streakDays: data.anchor?.streak_days || 0,
      permissions: data.permissions || RBAC_PERMS_BY_ROLE[data.role]};
    try { localStorage.setItem('kaoyan_auth', JSON.stringify(authState)); } catch (_) {}
    clearAllPasswordInputs();
    updateAuthUI();
    switchTab(isAdmin() ? 6 : 2);
    loginNotice(isAdmin() ? '登录成功，已进入管理员后台 (Signed in · Administration)' : '登录成功，已恢复学习进度 (Signed in · Study restored)');
    syncFromServer();
  } catch (error) {
    if (generation === sessionGeneration) loginNotice(error.message || '登录暂未确认，请重试 (Sign-in not confirmed)', true);
  } finally {
    if (generation === sessionGeneration) { clearAllPasswordInputs(); loginPending(false); }
  }
}

function resetPrivateSession(message = '') {
  ++sessionGeneration;
  loginPending(false);
  authState = {role:'GUEST', userId:'guest', displayName:'未登录访客', token:'', lastPara:1,
    streakDays:0, permissions:RBAC_PERMS_BY_ROLE.GUEST};
  try { localStorage.removeItem('kaoyan_auth'); } catch (_) {}
  if (typeof resetAdminDrilldown === 'function') resetAdminDrilldown();
  ['adminUsersTableBody','adminAuditTableBody','adminRoleTableBody','adminPermTableBody','adminAccountsStatus'].forEach(id => {
    const element = document.getElementById(id); if (element) element.innerHTML = '';
  });
  notesData = GUEST_TEASER_NOTES.slice();
  vocabData = GUEST_TEASER_VOCAB.slice();
  essayCorpus = GUEST_TEASER_ESSAYS.slice();
  const draft = document.getElementById('essayDraftBox');
  if (draft) draft.value = '';
  document.getElementById('scholarUserInput').value = '';
  clearAllPasswordInputs();
  updateAuthUI();
  switchTab(defaultGuestTab);
  loginNotice(message);
}

function toggleScholarAuth() {
  if (isLoggedIn()) resetPrivateSession('已安全退出 (Signed out)');
  else focusLoginBox();
}

async function initializeSession() {
  let saved = null;
  try { saved = JSON.parse(localStorage.getItem('kaoyan_auth') || 'null'); } catch (_) {}
  if (!saved?.token) return;
  const generation = ++sessionGeneration;
  loginPending(true);
  loginNotice('正在恢复会话 (Restoring session)');
  try {
    const response = await fetch('/api/auth/me', {headers:{Authorization:'Bearer ' + saved.token}});
    if (!response.ok) throw new Error('Session unavailable');
    const me = await (window.safeJsonResponse ? window.safeJsonResponse(response) : response.json());
    if (generation !== sessionGeneration) return;
    if (!me.authenticated || !['ADMIN','SCHOLAR'].includes(me.role)) {
      resetPrivateSession('会话已失效，请重新登录 (Session expired)');
      return;
    }
    authState = {...saved, role:me.role, userId:me.user_id, displayName:me.display_name, permissions:me.permissions};
    updateAuthUI();
    switchTab(isAdmin() ? 6 : 2);
    loginNotice('会话已恢复 (Session restored)');
    syncFromServer();
  } catch (_) {
    if (generation === sessionGeneration) resetPrivateSession('会话恢复暂未确认，请重新登录 (Session not confirmed)');
  } finally {
    if (generation === sessionGeneration) loginPending(false);
  }
}
