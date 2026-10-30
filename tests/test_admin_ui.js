// Test real page functions against controlled async transport; browser checks are separate.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
function setup() {
  const nodes = new Map(), alerts = [], calls = [];
  const node = id => {
    if (!nodes.has(id)) nodes.set(id, {id, value: '', textContent: '', innerHTML: '', disabled: false,
      style: {}, classList: {toggle() {}, add() {}, remove() {}},
      focus() {}, scrollIntoView() {}, setAttribute() {}, replaceChildren() {},
      appendChild() {}, addEventListener() {}, querySelectorAll() { return []; }});
    return nodes.get(id);
  };
  const context = vm.createContext({URLSearchParams, console, setTimeout, clearTimeout,
    location: {protocol: 'https:'}, localStorage: {setItem() {}, removeItem() {}, getItem() {return null;}},
    document: {
      getElementById: node,
      querySelectorAll() {return [];},
      createElement: tag => node('new-' + tag),
      body: node('body'),
      documentElement: {scrollHeight: 2000, clientHeight: 800, setAttribute(k, v) { this[k] = v; }}
    },
    alert: text => alerts.push(text), window: {scrollY: 600, addEventListener() {}, performance: {mark() {}}},
    fetch: (url, opts) => new Promise(resolve => calls.push({url, opts, resolve}))
  });
  const main = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]).find(s => s.includes('let authState'));
  vm.runInContext(main.slice(0, main.lastIndexOf("try {\n  clearAllPasswordInputs();")), context);
  const orthScript = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]).find(s => s.includes('toggleZenFocusMode'));
  if (orthScript) vm.runInContext(orthScript, context);
  for (const name of ['kaoyan_admin_view.js','kaoyan_admin.js','kaoyan_admin_accounts.js','kaoyan_login.js','kaoyan_eids_drilldown.js','kaoyan_tri_exam_polysemy.js']) {
    const f = path.join(root,name);
    if (fs.existsSync(f)) vm.runInContext(fs.readFileSync(f,'utf8'),context);
  }
  vm.runInContext(`updateRbacTabUI = () => {};
    renderPassageCanvas = renderNotes = renderVocab = renderEssayCorpus = () => {};
    syncFromServer = async () => {};
    switchTab = idx => { window.selectedTab = idx; };`, context);
  node('scholarUserInput').value = 'commander';
  node('scholarKeyInput').value = 'test-password';
  return {context, node, calls, alerts, run: code => vm.runInContext(code, context)};
}
async function testLogin() {
  const s = setup();
  const pending = s.run('loginWithCredentials()');
  assert.equal(s.node('scholarKeyInput').value, '', 'password must clear immediately');
  assert.equal(s.node('loginSubmitBtn').disabled, true, 'pending login must disable submit');
  await s.run('loginWithCredentials()');
  assert.equal(s.calls.length, 1, 'double click must issue only one authentication');
  assert.deepEqual(s.alerts, [], 'double click must not report empty password');
  s.calls[0].resolve({ok:true,json:async()=>({role:'ADMIN',user_id:'commander',token:'test-session',anchor:{last_para_idx:1}})});
  await pending;
  assert.equal(s.context.window.selectedTab, 6, 'admin must enter management after first click');
  assert.equal(s.node('guestLoginControls').style.display, 'none', 'hide obsolete credential form');
  assert.match(s.node('loginStatus').textContent, /登录成功|Signed in/);
  await s.run('loginWithCredentials()');
  assert.equal(s.calls.length, 1, 'authenticated click must not rotate token');
  assert.deepEqual(s.alerts, []);
}
async function testLoginFailure() {
  const s = setup();
  const pending = s.run('loginWithCredentials()');
  s.calls[0].resolve({ok:false,status:401,json:async()=>({message:'Wrong credentials'})});
  await pending;
  assert.equal(s.node('loginSubmitBtn').disabled,false);
  assert.match(s.node('loginStatus').textContent,/Wrong credentials/);
  assert.equal(s.run('authState.role'),'GUEST');
  assert.equal(s.node('scholarKeyInput').value,'');
}
async function testEmptyPassword() {
  const s = setup();
  s.node('scholarKeyInput').value = '';
  await s.run('loginWithCredentials()');
  assert.equal(s.calls.length, 0);
  assert.match(s.node('loginStatus').textContent,/密码|password/i);
}
async function testDrillRaceAndFailure() {
  const s = setup();
  s.run(`authState = {role:'ADMIN',token:'session'}; renderAdminDrilldownUI = renderFullFieldCatalog = renderRuntimeSchema = () => {};`);
  const first = s.run("selectDrillTable('sys_users')");
  const second = s.run("selectDrillTable('exam_passages')");
  s.calls[1].resolve({ok:true,json:async()=>({selected_table:{table_name:'exam_passages'}})});
  await second;
  s.calls[0].resolve({ok:true,json:async()=>({selected_table:{table_name:'sys_users'}})});
  await first;
  assert.equal(s.run('adminDrillState.livePayload.selected_table.table_name'),'exam_passages');
  const failed = s.run("selectDrillTable('sys_roles')");
  s.calls[2].resolve({ok:false,status:503,json:async()=>({message:'Temporary failure'})});
  await failed;
  assert.equal(s.run('adminDrillState.livePayload'),null);
  assert.match(s.run('adminDrillState.error'),/Temporary failure/);
}
async function testForeignKeyAndLogout() {
  const s = setup();
  s.run(`authState = {role:'ADMIN',token:'session'}; renderAdminDrilldownUI = renderFullFieldCatalog = renderRuntimeSchema = () => {};`);
  const pending = s.run(`jumpToForeignKeyTarget('sys_users.user_id', "O'Brien <new>")`);
  const query = new URL('https://test.invalid' + s.calls[0].url).searchParams;
  assert.equal(query.get('filter_column'),'user_id');
  assert.equal(query.get('filter_value'),"O'Brien <new>");
  s.node('adminUsersTableBody').innerHTML = 'private';
  s.node('adminInspectorTableBody').innerHTML = 'private';
  s.run('resetPrivateSession()');
  s.calls[0].resolve({ok:true,json:async()=>({selected_table:{table_name:'sys_users'}})});
  await pending;
  assert.equal(s.run('authState.role'),'GUEST');
  assert.equal(s.run('adminDrillState.livePayload'),null);
  assert.equal(s.node('adminUsersTableBody').innerHTML,'');
  assert.equal(s.node('adminInspectorTableBody').innerHTML,'');
}
async function testExpiredRestoreAndNullRendering() {
  const s = setup();
  s.context.localStorage.getItem = () => JSON.stringify({role:'ADMIN',token:'expired'});
  const pending = s.run('initializeSession()');
  assert.equal(s.run('authState.role'),'GUEST','stored role cannot grant a session');
  s.calls[0].resolve({ok:true,json:async()=>({authenticated:false})});
  await pending;
  assert.equal(s.run('authState.role'),'GUEST');
  assert.match(s.node('loginStatus').textContent,/Session expired/);
  assert.equal(s.run('fieldValue(null)'),'NULL');
  assert.equal(s.run("fieldValue('')"),'""');
  assert.equal(s.run('fieldValue(0)'),'0');
  assert.equal(s.run("fieldConstraints({pk:1,notnull:true,default_value:'0'})"),'PK #1 · NOT NULL · DEFAULT 0');
}
async function testAuditPreviewAllFields() {
  const s = setup();
  s.run("authState = {role:'ADMIN',token:'session'};");
  const audit = Object.fromEntries(['audit_id','actor_user_id','actor_role','target_user_id',
    'action','detail_json','client_ip','created_at'].map(key => [key, key + '_probe']));
  const pending = s.run("loadAdminAccounts('session')");
  s.calls[0].resolve({ok:true,json:async()=>({users:[],audit_logs:[audit]})});
  await pending;
  for (const value of Object.values(audit)) assert.ok(s.node('adminAuditTableBody').innerHTML.includes(value),value);
}
async function testEidsCrossModuleModalsAndLiveTableBrowser() {
  const s = setup();
  for (const [lens, id, expectedTable] of [
    ['MODULE', 'MOD_01_READING', 'annotation_spans'],
    ['TRACK', 'TRK_01_SYLLABUS_CSV', 'syllabus_5500_lexicon'],
    ['PASSAGE', 'P2024_EN1_T1', 'exam_passages'],
    ['NOTE', 'sp-para-1', 'annotation_spans'],
    ['VOCAB', 'accommodate', 'user_vocab_ledger'],
    ['ESSAY', 'ec-1', 'essay_corpus_snippets']
  ]) {
    s.run(`openDetailModal('${lens}', '${id}')`);
    assert.equal(s.node('detailModalOverlay').style.display, 'flex');
    assert.ok(s.node('detBody').innerHTML.includes(expectedTable), `detail modal for ${lens} must show ${expectedTable}`);
  }
  s.run('closeDetailModal()');
  assert.equal(s.node('detailModalOverlay').style.display, 'none');
  s.run("openDomainDrilldownModal('DOM_03_SCHOLAR_STUDY')");
  assert.equal(s.node('infoModalOverlay').style.display, 'flex');
  assert.ok(s.node('eidsDomainModalTbody').innerHTML.includes('user_vocab_ledger'));
  const pending = s.run("openLiveTableBrowser('exam_passages', 'title', '2024')");
  s.calls[0].resolve({
    ok: true,
    json: async () => ({
      status: 'ok',
      auth_tier: 'GUEST_TEASER',
      selected_table: {
        table_name: 'exam_passages',
        row_count: 1,
        offset: 0,
        limit: 12,
        has_previous: false,
        has_next: false,
        columns: [{ name: 'passage_id', type: 'VARCHAR(64)' }, { name: 'title', type: 'VARCHAR(256)' }],
        rows: [{ passage_id: 'P2024_EN1_T1', title: '2024 英语一 Text 1' }]
      },
      tables: { exam_passages: { table_no: 'T07', table_name: 'exam_passages', column_count: 2, row_count: 1 } }
    })
  });
  await pending;
  assert.ok(s.node('modalLiveSqlBrowserBox').innerHTML.includes('2024 英语一 Text 1'));
  assert.ok(s.node('modalLiveSqlBrowserBox').innerHTML.includes('🎯'));
}

async function testTriExamPolysemyAndContextualLadder() {
  const s = setup();
  assert.equal(s.run('window.TRI_EXAM_DATA.stats.tri_union_total'), 8390, 'Tri-exam union must be 8390 words');
  assert.equal(s.run('window.TRI_EXAM_DATA.stats.tri_intersection_3way'), 2259, '3-way core must be 2259 words');
  s.run("selectTriExamWord('check')");
  assert.match(s.node('triExamPolysemyStudio').innerHTML, /keep inflation in check/, 'must render check phrases and contextual ladder');
  assert.match(s.node('triExamPolysemyStudio').innerHTML, /brake-check/, 'must render micro-passage story');
  s.run("toggleTriClozeMask()");
  assert.match(s.node('triExamPolysemyStudio').innerHTML, /点我揭晓/, 'cloze mask must mask target word in micro-passage');
  s.run("setTriViewMode('GLANCE')");
  assert.match(s.node('triExamPolysemyStudio').innerHTML, /triGlanceTableBody/, 'must switch to single-line 9-column glanceable table');
  s.run("setTriExamTrack('IELTS')");
  assert.match(s.node('triExamPolysemyStudio').innerHTML, /IELTS/, 'must filter IELTS track');
}

async function testOrthogonalAestheticAndCommandPalette() {
  const s = setup();
  s.run('toggleZenFocusMode()');
  assert.equal(s.run('zenFocusActive'), true);
  assert.match(s.node('zenFocusBtn').textContent, /退出专注/);
  s.run('cycleReadingFontSize()');
  assert.equal(s.context.document.documentElement['data-font-scale'], 'large');
  assert.match(s.node('fontScaleBtn').textContent, /大字护眼/);
  s.run('openCommandPalette()');
  assert.equal(s.node('cmdPaletteOverlay').style.display, 'flex');
  s.run("renderCommandPaletteList('专注')");
  assert.ok(s.node('cmdPaletteList').innerHTML.includes('Alt+Z'));
  s.run('runCommandPaletteItem(0)');
  assert.equal(s.node('cmdPaletteOverlay').style.display, 'none');
  assert.equal(s.context.window.selectedTab, 2);
  s.run('updateReadingProgressHairline()');
  assert.equal(s.node('readingProgressBar').style.width, '50%');
}
(async () => {
  const failures = [];
  for (const test of [testLogin,testLoginFailure,testEmptyPassword,testDrillRaceAndFailure,testForeignKeyAndLogout,testExpiredRestoreAndNullRendering,testAuditPreviewAllFields,testEidsCrossModuleModalsAndLiveTableBrowser,testOrthogonalAestheticAndCommandPalette]) {
    try { await test(); console.log('PASS',test.name); }
    catch (e) { failures.push(test.name); console.error('FAIL',test.name,e.message); }
  }
  assert.deepEqual(failures, []);
})().catch(e => {console.error(e.message); process.exitCode=1;});
