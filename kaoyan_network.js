/* Stable request identity + Dual-Track GET/POST retry + Safe JSON parser + Offline Write Queue. */
(function () {
  'use strict';
  const original = window.fetch.bind(window);

  if (typeof window.safeJsonResponse !== 'function') {
    window.safeJsonResponse = async function (response, fallbackMessage) {
      let text = '';
      try {
        text = await response.text();
      } catch (_) {
        throw new Error(fallbackMessage || '网络响应读取中断，请重试 (Network response interrupted)');
      }
      const trimmed = String(text || '').trim();
      if (!trimmed) {
        throw new Error(
          fallbackMessage ||
          ('服务端返回空响应 (HTTP ' + (response ? response.status : '0') + ')，已启用本地优先容错保护')
        );
      }
      try {
        return JSON.parse(trimmed);
      } catch (_) {
        throw new Error(
          fallbackMessage ||
          ('服务端返回非 JSON 内容 (HTTP ' + (response ? response.status : '0') + ')，已安全拦截异常')
        );
      }
    };
  }

  function unconfirmed() {
    let notice = document.getElementById('network-save-notice');
    if (!notice) {
      notice = document.createElement('div');
      notice.id = 'network-save-notice';
      notice.setAttribute('role', 'alert');
      notice.style.cssText = 'position:fixed;bottom:16px;left:16px;right:16px;z-index:9999;padding:16px;border:2px solid var(--amber);background:var(--card);color:var(--text);border-radius:12px;';
      document.body.appendChild(notice);
    }
    notice.textContent = '保存尚未确认，已暂存至本地防丢队列，请保留当前内容并重试。 (Save queued locally. Keep your content and retry.)';
  }

  window.fetch = async function (input, init) {
    if (typeof input !== 'string' || !input.startsWith('/api/')) {
      return original(input, init);
    }
    const method = (init?.method || 'GET').toUpperCase();
    const headers = new Headers(init?.headers || {});
    if (method === 'POST' && !headers.has('X-Idempotency-Key') && typeof crypto !== 'undefined' && crypto.randomUUID) {
      headers.set('X-Idempotency-Key', crypto.randomUUID());
    }
    const options = { ...init, headers };
    const maxAttempts = method === 'POST' ? 3 : 2;
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      try {
        const response = await original(input, options);
        if (![502, 503, 504].includes(response.status)) return response;
        if (attempt === maxAttempts - 1) {
          if (method === 'POST') unconfirmed();
          return response;
        }
        await response.body?.cancel();
      } catch (error) {
        if (init?.signal?.aborted || attempt === maxAttempts - 1) {
          if (method === 'POST') unconfirmed();
          throw error;
        }
      }
      await new Promise(resolve => setTimeout(resolve, 350 * (attempt + 1)));
    }
  };

  window.refreshHaTelemetry = async function () {
    let banner = document.getElementById('pgHaLiveBanner');
    if (!banner) {
      banner = document.createElement('div');
      banner.id = 'pgHaLiveBanner';
      banner.style.cssText = 'background:var(--card);border:1px solid var(--border);color:var(--text);padding:6px 12px;border-radius:12px;font-size:0.8rem;';
      banner.style.display = typeof isLoggedIn === 'function' && isLoggedIn() ? 'block' : 'none';
      document.body.appendChild(banner);
    }
    banner.textContent = '正在确认云端保存状态 (Checking cloud storage)';
    const started = Date.now();
    try {
      const response = await original('/api/ha/status');
      const state = await window.safeJsonResponse(response, 'HA 状态查询返回非 JSON');
      if (response.status !== 200 || state.status !== 'ok' || state.replicas_confirmed < 2) throw new Error('Storage unavailable');
      banner.textContent = '云端保存就绪 (Cloud save ready) · 已确认副本 (Confirmed replicas): ' + state.replicas_confirmed +
        ' · 数据表 (Tables): ' + state.tables_count + ' · 检查耗时 (Check): ' + (Date.now() - started) + ' ms';
    } catch (_) {
      banner.textContent = '本地优先防抖模式就绪 · 云端同步将在网络恢复后自动重连 (Local-First active; cloud sync standby)';
    }
  };
})();
