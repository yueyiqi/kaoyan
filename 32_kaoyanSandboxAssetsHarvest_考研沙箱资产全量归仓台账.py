#!/usr/bin/env python3
"""Four-Modal Visual Compiler for #32 Kaoyan Full Sandbox Assets Harvest Ledger."""

from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
BRAIN_DIR = Path("/Users/liuzengyu/.gemini/antigravity/brain/8cbcf770-f72a-45c2-ab19-d6745928da4b")
ADR_PY = REPO_ROOT / ".adr/701-800/711-720/adr_0716_sandboxZeroOrphanAutoBzRouter_沙箱零孤儿与BZ自动立项归类路由/adr_0716_sandboxZeroOrphanAutoBzRouter_沙箱零孤儿与BZ自动立项归类路由.py"
STEM = "32_kaoyanSandboxAssetsHarvest_考研沙箱资产全量归仓台账"
TITLE = "32 · 考研项目 (.bz/95_kaoyan_考研) 沙箱资产全量归仓与 SHA-256 核验台账"
SUBTITLE = "Kaoyan Project .bz/95_kaoyan_考研 Full Sandbox Asset Harvest & SHA-256 Verification Ledger (ev:ev-0002)"

CARDS = [
    (
        "① 舱位 A-B：01..32 核心大典与生产工程源码",
        (219, 234, 254), (37, 99, 235), (30, 64, 175), "#DBEAFE", "#2563EB", "#1E40AF",
        [
            ("01..32 编号化核心大典 (230+ 项资产)", "全部配备 .md + .py + .svg + .png + .pptx + .html 四模态伴生文件。"),
            ("src_kaoyan_english_web_v2/ 生产源码树", "涵盖 backend/、frontend/、Dockerfile、Compose 与完整自动化测试套件。"),
            ("顶层直达入口 .bz/95_kaoyan_考研", "软链指向 95_kaoyanEnglishHub_考研英语精读平台，消除深层寻址盲区。"),
        ],
        "核心基座: 01..32 大典与全栈源码 100% 齐备",
    ),
    (
        "② 舱位 C：晋升 Git 纳管的 12 个集群高可用运维脚本",
        (209, 250, 229), (5, 150, 105), (6, 95, 70), "#D1FAE5", "#059669", "#065F46",
        [
            ("跨 OS 巡检与 16 表对账", "remote.py / runtime_audit.py / deep_schema_audit.py 纳管入库。"),
            ("边缘白名单与无脑裂切主", "deploy_edge.py / verify_edge.py / cutover_runtime.py / failover。"),
            ("生产终验与单写租约法医", "production_acceptance.py / final_signoff.py / srbg10_lease_forensics。"),
        ],
        "持久纳管: ops_cluster_ha_集群高可用运维/ + SHA-256 总账本",
    ),
    (
        "③ 舱位 D：Codex 四大历史战役全量镜像 (134 项)",
        (254, 226, 226), (239, 68, 68), (153, 27, 27), "#FEE2E2", "#EF4444", "#991B1B",
        [
            ("eb_20261019 (26 项)", "跨 OS 字段级 Schema 对账、HP/S1 往返测试与模拟器边界验证。"),
            ("eb_20261020 (21 项) & eb_20261022 (27 项)", "Windows 在线主备切换窗口、管理后台登录修复与发布核验。"),
            ("eb_20261024 (60 项)", "W1 Docker 容器主库与 ECS 边缘前端分离 P0..P7 全部脚本与收据。"),
        ],
        "无损镜像: 134 项 Codex 战役产物 1:1 归仓",
    ),
    (
        "④ 舱位 D：Antigravity 四大历史战役全量镜像 (127 项)",
        (237, 233, 254), (124, 58, 237), (91, 33, 182), "#EDE9FE", "#7C3AED", "#5B21B6",
        [
            ("eb_9036 (118 项) & eb_9039 (3 项)", "考研精读语义规范初始版、PG18 部署脚本与未登录预览糊化报告。"),
            ("eb_9041 (4 项) & eb_9044 (2 项)", "单写租约法医报告、L0-L7 真机探针 JSON 与本次归仓核验收据。"),
            ("四槽工作树 100% 同步对齐", "srbg10 / srbg0 / idea0 / cfzy0 四槽均已完成全量资产同步。"),
        ],
        "核验结论: 受检 261 项 · sandbox_only_orphan_count = 0 (ev:ev-0002)",
    ),
]


def build_html() -> None:
    html = f"""<!DOCTYPE html>
<html lang="zh-CN" data-theme="daylight">
<head>
  <meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <title>{TITLE}</title>
  <script>(function(){{document.documentElement.setAttribute('data-theme',localStorage.getItem('bz32_theme')||'daylight');}})();</script>
  <style>
    :root[data-theme="daylight"]{{--bg:#F8FAFC;--card:#FFFFFF;--text:#0F172A;--muted:#475569;--accent:#2563EB;--border:#E2E8F0;}}
    :root[data-theme="midnight"]{{--bg:#0F172A;--card:#1E293B;--text:#F8FAFC;--muted:#94A3B8;--accent:#60A5FA;--border:#334155;}}
    :root[data-theme="eyecare"]{{--bg:#F4F1EA;--card:#FAF8F5;--text:#1F2937;--muted:#4B5563;--accent:#059669;--border:#D6D3CD;}}
    body{{margin:0;font-family:-apple-system,"PingFang SC",sans-serif;background:var(--bg);color:var(--text);padding:24px;line-height:1.6;}}
    .hdr{{display:flex;justify-content:space-between;align-items:center;background:var(--card);border:1px solid var(--border);border-radius:14px;padding:20px 28px;margin-bottom:24px;flex-wrap:wrap;gap:12px;}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(460px,1fr));gap:20px;}}
    .card{{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:22px;}}
    h1{{margin:0 0 6px 0;font-size:22px;}} h2{{margin:0 0 12px 0;font-size:18px;color:var(--accent);}}
    button{{cursor:pointer;padding:8px 14px;border-radius:8px;border:1px solid var(--border);background:var(--card);color:var(--text);margin-left:6px;font-weight:600;}}
  </style>
</head>
<body>
  <div class="hdr">
    <div><h1>{TITLE}</h1><div>{SUBTITLE}</div></div>
    <div><button onclick="setTheme('daylight')">☀️ Daylight</button><button onclick="setTheme('midnight')">🌙 Midnight</button><button onclick="setTheme('eyecare')">🍵 Eyecare</button></div>
  </div>
  <div class="grid">
    <div class="card"><h2>① 舱位 A-B：01..32 大典与生产源码树</h2><p>.bz/95_kaoyan_考研 下汇集 01..32 共 32 套四模态大典与 src_kaoyan_english_web_v2/ 完整生产源码树。</p></div>
    <div class="card"><h2>② 舱位 C：12 个核心高可用运维脚本晋升 Git</h2><p>ops_cluster_ha_集群高可用运维/ 纳管 remote.py、deploy_edge.py、cutover_runtime.py、kaoyan_coordinator_failover.py 等 12 个核心脚本及 SHA-256 总账本。</p></div>
    <div class="card"><h2>③ 舱位 D：Codex 历史战役全量归仓 (134 项)</h2><p>eb_20261019 (26项)、eb_20261020 (21项)、eb_20261022 (27项)、eb_20261024 (60项) 100% 物理镜像归仓。</p></div>
    <div class="card"><h2>④ 舱位 D：Antigravity 历史战役全量归仓 (127 项)</h2><p>eb_9036 (118项)、eb_9039 (3项)、eb_9041 (4项)、eb_9044 (2项) 100% 归仓，四槽工作树实时对齐。</p></div>
  </div>
  <script>function setTheme(t){{document.documentElement.setAttribute('data-theme',t);localStorage.setItem('bz32_theme',t);}}</script>
</body></html>
"""
    (HERE / f"{STEM}.html").write_text(html, encoding="utf-8")


def main() -> int:
    spec = importlib.util.spec_from_file_location("adr0716_mod", ADR_PY)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    mod.render_all(HERE, STEM, TITLE, SUBTITLE, CARDS)
    build_html()
    if BRAIN_DIR.is_dir():
        for ext in (".md", ".svg", ".png", ".pptx", ".html"):
            src = HERE / f"{STEM}{ext}"
            if src.is_file():
                shutil.copy2(src, BRAIN_DIR / src.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
