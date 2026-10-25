/* Stable request identity survives transient transport errors during switchover. */
(function () {
  'use strict';
  const original = window.fetch.bind(window);
  function unconfirmed() {
    let notice = document.getElementById('network-save-notice');
    if (!notice) {
      notice = document.createElement('div');
      notice.id = 'network-save-notice';
      notice.setAttribute('role', 'alert');
      notice.style.cssText = 'position:fixed;bottom:16px;left:16px;right:16px;z-index:9999;padding:16px;border:2px solid var(--amber);background:var(--card);color:var(--text);border-radius:12px;';
      document.body.appendChild(notice);
    }
    notice.textContent = '保存尚未确认，请保留当前内容并重试。 (Save not confirmed. Keep your content and retry.)';
  }
  window.fetch = async function (input, init) {
    if (typeof input !== 'string' || !input.startsWith('/api/') || (init?.method || 'GET').toUpperCase() !== 'POST') {
      return original(input, init);
    }
    const headers = new Headers(init.headers || {});
    if (!headers.has('X-Idempotency-Key')) headers.set('X-Idempotency-Key', crypto.randomUUID());
    const options = { ...init, headers };
    for (let attempt = 0; attempt < 3; attempt++) {
      try {
        const response = await original(input, options);
        if (![502, 503, 504].includes(response.status)) return response;
        if (attempt === 2) { unconfirmed(); return response; }
        await response.body?.cancel();
      } catch (error) {
        if (init.signal?.aborted || attempt === 2) { unconfirmed(); throw error; }
      }
      await new Promise(resolve => setTimeout(resolve, 500 * (attempt + 1)));
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
      const state = await response.json();
      if (response.status !== 200 || state.status !== 'ok' || state.replicas_confirmed < 2) throw new Error('Storage unavailable');
      banner.textContent = '云端保存就绪 (Cloud save ready) · 已确认副本 (Confirmed replicas): ' + state.replicas_confirmed +
        ' · 数据表 (Tables): ' + state.tables_count + ' · 检查耗时 (Check): ' + (Date.now() - started) + ' ms';
    } catch (_) {
      banner.textContent = '云端保存暂不可用，请保留当前内容 (Cloud save unavailable; keep your content)';
    }
  };
})();
