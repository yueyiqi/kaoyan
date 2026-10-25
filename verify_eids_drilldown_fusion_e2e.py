#!/usr/bin/env python3
"""Live E2E & Local Behavioral Verification for KaoyanEnglish Hub v3.6 (EIDS Drill-Down Fusion)."""
from __future__ import annotations

import json
from pathlib import Path
import ssl
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent
LIVE_URLS = [
    "https://kaoyan.8.163.29.42.nip.io",
    "https://kaoyan.liuzengyu.top",
    "https://kaoyan-elena.duckdns.org",
]


def _ssl_ctx() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _http_req(base_url: str, path: str, method: str = "GET", headers: dict | None = None, body: dict | None = None) -> tuple[int, str, dict]:
    req_headers = {"User-Agent": "KaoyanEidsDrilldownVerifier/3.6"}
    if headers:
        req_headers.update(headers)
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        req_headers["Content-Type"] = "application/json"
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=_ssl_ctx()))
    req = urllib.request.Request(base_url + path, data=data, headers=req_headers, method=method)
    try:
        with opener.open(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                js = json.loads(raw) if raw.lstrip().startswith(("{", "[")) else {}
            except Exception:
                js = {}
            return resp.status, raw, js
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            js = json.loads(raw) if raw.lstrip().startswith(("{", "[")) else {}
        except Exception:
            js = {}
        return exc.code, raw, js


def pick_reachable_live_url() -> str:
    for url in LIVE_URLS:
        try:
            code, _, js = _http_req(url, "/api/ha/status")
            if code == 200 and js.get("status") == "ok":
                return url
        except Exception:
            continue
    return LIVE_URLS[0]


def run_verification() -> dict:
    checks: list[dict] = []

    def record(cid: str, name: str, passed: bool, detail: str) -> None:
        checks.append({"id": cid, "name": name, "passed": bool(passed), "detail": detail})

    # 1. Local behavioral unit tests (Python + Node VM)
    shunt_proc = subprocess.run(
        [sys.executable, str(ROOT / "kaoyan_admin_drilldown_shunt_engine.py")],
        capture_output=True, text=True, timeout=60,
    )
    record("E01", "本地前置限幅外专与双栈行为单测 (test_admin_drilldown.py + test_admin_ui.js)", shunt_proc.returncode == 0, f"exit={shunt_proc.returncode}")

    base_url = pick_reachable_live_url()

    # 2. Live HTML & JS bundle checks
    code_html, html_text, _ = _http_req(base_url, "/")
    record("E02", f"线上首页 HTML 可达且挂载 kaoyan_eids_drilldown.js ({base_url})", code_html == 200 and "/kaoyan_eids_drilldown.js" in html_text, f"status={code_html}, len={len(html_text)}")
    record("E03", "线上首页具备 EIDS 双模态弹窗容器 (#detailModalOverlay + #infoModalOverlay)", "id=\"detailModalOverlay\"" in html_text and "id=\"infoModalOverlay\"" in html_text, "dual modal containers present")
    kpi_card_cnt = html_text.count('class="kpi-drill-hint"')
    record("E04", "顶部 5 张 KPI 卡片全量绑定 EIDS 点击下钻事件", kpi_card_cnt == 5 and "openLiveTableBrowser('user_progress_anchors'" in html_text, f"kpi_cards={kpi_card_cnt}")
    record("E05", "Tab 0 架构总览融入 EIDS 五大业务域 SVG 环形图与模块血缘下钻", "openDomainDrilldownModal('DOM_01_RBAC_AUTH')" in html_text and "openDetailModal('MODULE'" in html_text, "Tab 0 SVG donut + MODULE lens wired")
    record("E06", "Tab 1~5 全板块融入 EIDS 血缘下钻 (TRACK / PASSAGE / NOTE / VOCAB / ESSAY / SCHEMA)", all(tok in html_text for tok in ["openDetailModal('TRACK'", "openDetailModal('PASSAGE'", "openDetailModal('NOTE'", "openDetailModal('VOCAB'", "openDetailModal('ESSAY'", "openOdsSchemaModal()"]), "All 6 business lenses wired")
    record("E07", "线上页面零明文密码泄露与零记忆属性完备", "kaoyan2026" not in html_text and "Kaoyan@Admin2026" not in html_text and 'autocomplete="new-password"' in html_text, "0 plaintext credentials in HTML")

    code_js, js_text, _ = _http_req(base_url, "/kaoyan_eids_drilldown.js")
    record("E08", "线上 /kaoyan_eids_drilldown.js 静态脚本可达且含四大核心函数", code_js == 200 and all(fn in js_text for fn in ["openLiveTableBrowser", "loadLiveTableRowsInto", "openOdsSchemaModal", "openDomainDrilldownModal", "openDetailModal"]), f"status={code_js}, len={len(js_text)}")

    # 3. Guest lineage API checks
    code_gl, _, gl_pub = _http_req(base_url, "/api/db/lineage?table=exam_passages&highlight_col=title")
    record("E09", "未登录访客 (GUEST) 下钻公共表 exam_passages 返回 100% 字段定义与样板行", code_gl == 200 and gl_pub.get("auth_tier") == "GUEST_TEASER" and gl_pub.get("total_tables_count", 0) >= 18 and gl_pub.get("selected_table", {}).get("highlight_col") == "title", f"auth_tier={gl_pub.get('auth_tier')}, tables={gl_pub.get('total_tables_count')}, cols={gl_pub.get('total_columns_count')}")

    code_gp, _, gl_priv = _http_req(base_url, "/api/db/lineage?table=sys_users")
    record("E10", "未登录访客 (GUEST) 下钻私有表 sys_users 仅透出字段结构且隐藏数据行 (0 行泄露)", code_gp == 200 and gl_priv.get("selected_table", {}).get("rows") == [] and len(gl_priv.get("selected_table", {}).get("columns", [])) == 13, f"rows={len(gl_priv.get('selected_table', {}).get('rows', []))}, cols={len(gl_priv.get('selected_table', {}).get('columns', []))}")

    code_g_adm, _, _ = _http_req(base_url, "/api/admin/db/drilldown?table=sys_users")
    record("E11", "未登录访客直接请求管理员专属接口 /api/admin/db/drilldown 刚性返回 401", code_g_adm == 401, f"status={code_g_adm}")

    # 4. Scholar RBAC & scoped lineage checks
    code_sl, _, sl_login = _http_req(base_url, "/api/auth/login", method="POST", body={"username": "colleague_a", "passcode": "kaoyan2026"})
    s_token = sl_login.get("token", "")
    s_hdr = {"Authorization": f"Bearer {s_token}"}
    code_s_lin, _, s_lin = _http_req(base_url, "/api/db/lineage?table=user_vocab_ledger&highlight_col=urgency_score", headers=s_hdr)
    record("E12", "普通研友 (SCHOLAR) 登录后下钻个人生词表 user_vocab_ledger 正常返回本人记录与高亮列", code_sl == 200 and code_s_lin == 200 and s_lin.get("auth_tier") == "SCHOLAR_SCOPED" and s_lin.get("selected_table", {}).get("highlight_col") == "urgency_score", f"auth_tier={s_lin.get('auth_tier')}, rows={len(s_lin.get('selected_table', {}).get('rows', []))}")

    code_s_adm, _, _ = _http_req(base_url, "/api/admin/db/drilldown?table=sys_users", headers=s_hdr)
    record("E13", "普通研友 (SCHOLAR) 越权请求管理员全库接口 /api/admin/db/drilldown 刚性返回 403", code_s_adm == 403, f"status={code_s_adm}")

    # 5. Admin full 18-table / 146-column EIDS drilldown checks
    code_al, _, al_login = _http_req(base_url, "/api/auth/login", method="POST", body={"username": "admin", "passcode": "Kaoyan@Admin2026"})
    a_token = al_login.get("token", "")
    a_hdr = {"Authorization": f"Bearer {a_token}"}
    code_a_dr, raw_a_dr, a_dr = _http_req(base_url, "/api/admin/db/drilldown?table=sys_users&q=admin&highlight_col=role", headers=a_hdr)
    sel_tbl = a_dr.get("selected_table", {})
    record("E14", "管理员 (ADMIN) 全文检索 q=admin 且高亮列 highlight_col=role 精准命中且全字段透出", code_al == 200 and code_a_dr == 200 and sel_tbl.get("highlight_col") == "role" and sel_tbl.get("row_count", 0) >= 1 and len(sel_tbl.get("columns", [])) == 13, f"row_count={sel_tbl.get('row_count')}, cols={len(sel_tbl.get('columns', []))}")

    exp_mat = a_dr.get("table_exposure_matrix", [])
    record("E15", "管理员 (ADMIN) 返回 EIDS 同款 18表×146列 table_exposure_matrix (含非空率与脱敏样本值)", len(exp_mat) >= 18 and a_dr.get("total_columns_count", 0) >= 146 and a_dr.get("field_coverage_pct") == 100.0 and "Kaoyan@Admin2026" not in raw_a_dr, f"matrix_tables={len(exp_mat)}, total_cols={a_dr.get('total_columns_count')}")

    code_bad, _, _ = _http_req(base_url, "/api/admin/db/drilldown?table=sys_users&highlight_col=invalid_col", headers=a_hdr)
    record("E16", "非法 highlight_col 参数触发后端参数校验返回 400 (防注入)", code_bad == 400, f"status={code_bad}")

    passed_cnt = sum(1 for c in checks if c["passed"])
    summary = {
        "suite": "kaoyan_eids_drilldown_fusion_e2e_v3.6",
        "live_endpoint_tested": base_url,
        "total_checks": len(checks),
        "passed_checks": passed_cnt,
        "failed_checks": len(checks) - passed_cnt,
        "bug_count": len(checks) - passed_cnt,
        "status": "PASS" if passed_cnt == len(checks) else "FAIL",
        "checks": checks,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


if __name__ == "__main__":
    res = run_verification()
    raise SystemExit(0 if res["status"] == "PASS" else 1)
