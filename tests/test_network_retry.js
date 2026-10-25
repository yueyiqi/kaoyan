const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const crypto = require('node:crypto');
const source = fs.readFileSync(require('node:path').join(__dirname, '../kaoyan_network.js'), 'utf8');
function setup(responses) {
  const calls = [], notices = [];
  const context = {
    Headers, crypto, setTimeout: fn => fn(),
    document: { getElementById: () => null, createElement: () => ({ setAttribute() {}, style: {} }),
      body: { appendChild: item => notices.push(item) } },
    window: { fetch: async (url, options) => {
      calls.push({ url, options });
      const item = responses.shift();
      if (item instanceof Error) throw item;
      return typeof item === 'object' ? item : { status: item, body: { cancel: async () => {} } };
    } }
  };
  vm.runInNewContext(source, context);
  return { context, calls, notices };
}
(async () => {
  const one = setup([503, new Error('connection dropped'), 200]);
  assert.equal((await one.context.window.fetch('/api/notes', { method: 'POST', body: '{"text":"test"}', headers: { Authorization: 'Bearer fake-test-token' } })).status, 200);
  assert.equal(one.calls.length, 3);
  assert.equal(new Set(one.calls.map(c => c.options.headers.get('X-Idempotency-Key'))).size, 1);
  assert.equal(one.calls[0].options.body, one.calls[2].options.body);
  assert.equal(one.calls[2].options.headers.get('Authorization'), 'Bearer fake-test-token');
  assert.equal(one.notices.length, 0);
  const two = setup([503, 503, 503]);
  assert.equal((await two.context.window.fetch('/api/notes', { method: 'POST', headers: { 'X-Idempotency-Key': 'existing' } })).status, 503);
  assert.equal(two.calls[2].options.headers.get('X-Idempotency-Key'), 'existing');
  assert.match(two.notices[0].textContent, /Save not confirmed/);
  const three = setup([503, 503]);
  await three.context.window.fetch('/api/state');
  await three.context.window.fetch('https://example.invalid/api/write', { method: 'POST' });
  assert.equal(three.calls.length, 2);
  const four = setup([{ status: 200, json: async () => ({ status: 'ok', replicas_confirmed: 3, tables_count: 18 }) }]);
  await four.context.window.refreshHaTelemetry();
  assert.match(four.notices[0].textContent, /Cloud save ready/);
  assert.match(four.notices[0].textContent, /18/);
  assert.doesNotMatch(four.notices[0].textContent, /PG18|100%|1\.2ms/);
  const five = setup([{ status: 503, json: async () => ({ status: 'temporarily_unavailable' }) }]);
  await five.context.window.refreshHaTelemetry();
  assert.match(five.notices[0].textContent, /Cloud save unavailable/);
  console.log('PASS: stable replay key/body, auth preserved, bounded retry, visible failure, same-origin POST scope');
})().catch(error => { console.error(error); process.exitCode = 1; });
