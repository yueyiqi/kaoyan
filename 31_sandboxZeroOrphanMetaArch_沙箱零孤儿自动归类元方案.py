#!/usr/bin/env python3
"""Four-Modal Visual Compiler for #31 Sandbox Zero-Orphan & Auto-BZ Meta-Architecture."""

from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
BRAIN_DIR = Path("/Users/liuzengyu/.gemini/antigravity/brain/8cbcf770-f72a-45c2-ab19-d6745928da4b")
ADR_PY = REPO_ROOT / ".adr/701-800/711-720/adr_0716_sandboxZeroOrphanAutoBzRouter_沙箱零孤儿与BZ自动立项归类路由/adr_0716_sandboxZeroOrphanAutoBzRouter_沙箱零孤儿与BZ自动立项归类路由.py"
STEM = "31_sandboxZeroOrphanMetaArch_沙箱零孤儿自动归类元方案"
TITLE = "31 · 沙箱零孤儿不变量与外部 .bz 自动立项及主动语义归类元方案"
SUBTITLE = "Sandbox Zero-Orphan Invariant & Proactive .bz Semantic Routing Meta-Architecture (ADR-0716)"

CARDS = [
    (
        "① 一揽子方案 1-2：ADR-0716 与 0-Token 语义路由外专",
        (219, 234, 254), (37, 99, 235), (30, 64, 175), "#DBEAFE", "#2563EB", "#1E40AF",
        [
            ("ADR-0716 全局架构裁决", "确立『五槽位过程账本留沙箱，一切实质资产归 .bz/』第一性公理。"),
            ("sandbox_to_bz_semantic_router_shunt.py", "支撑 census / route / bind-eb / consolidate-kaoyan / verify 五大算子。"),
            ("全仓 375 个 EB 定量普查", "识别 244 个 EB (65.07%) 共 2,940 项非槽位资产并建立路由矩阵。"),
        ],
        "架构定谳: 彻底终结『资产困在沙箱』与『人工提醒建目录』",
    ),
    (
        "② 一揽子方案 3-4：.bz/95_kaoyan_考研 与 261 项资产归仓",
        (209, 250, 229), (5, 150, 105), (6, 95, 70), "#D1FAE5", "#059669", "#065F46",
        [
            ("顶层直达入口 .bz/95_kaoyan_考研", "符合 ADR-0701 v2.0 双数字+驼峰+中文正则，直通 01..32 核心大典。"),
            ("12 个核心运维脚本晋升 Git 纳管", "落盘 ops_cluster_ha_集群高可用运维/ 并附 SHA-256 机器总账本。"),
            ("7+1 考研 EB 261 项非槽位文件全量镜像", "1:1 归仓 _workspace_eb_campaigns_沙箱全量归仓/，孤儿残留 = 0。"),
        ],
        "跨槽对齐: srbg10 / srbg0 / idea0 / cfzy0 四大工作树 100% 同步",
    ),
    (
        "③ 一揽子方案 5：入口自动立项与绑定 (new_eb.sh)",
        (254, 226, 226), (239, 68, 68), (153, 27, 27), "#FEE2E2", "#EF4444", "#991B1B",
        [
            ("状态 1 (Score>=0.65): 自动绑定存量 .bz", "命中 kaoyan/考研 等特征词自动写入 Cogni-Target-BZ: .bz/95_kaoyan_考研。"),
            ("状态 2 (0.35<=Score<0.65): 路由治理域", "命中 skill/gate/adr/rrsi 自动归入 .adr / .agents/skills / scripts。"),
            ("状态 3 (Score<0.35): 自动触发 new_bz.sh", "全新业务/探索课题自动发号建立外部 .bz 项目目录，零冗余追问。"),
        ],
        "前置赋能: 会话创建即完成外部 .bz 目标目录绑定",
    ),
    (
        "④ 一揽子方案 6：出口门禁哨兵 (gate_0522 v3.0 & Skill 42)",
        (237, 233, 254), (124, 58, 237), (91, 33, 182), "#EDE9FE", "#7C3AED", "#5B21B6",
        [
            ("gate_0522 v3.0 Section 0.5 守卫", "SANDBOX_ONLY_ORPHAN_GUARD 自动扫描暂存区 EB 非五槽位实质文件。"),
            ("Skill 42 (slot-artifact-persistence v6)", "固化 G13 零沙箱孤儿铁律与自动 .bz 语义归类标准作业程序。"),
            ("真机实测与哈希链证据入账", "verify 模式实测 sandbox_only_orphan_count = 0 (ev:ev-0002)。"),
        ],
        "门禁闭环: Rule + ADR-0716 + Skill 42 v6 + Gate 0522 v3.0",
    ),
]


def build_html() -> None:
    html = f"""<!DOCTYPE html>
<html lang="zh-CN" data-theme="daylight">
<head>
  <meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <title>{TITLE}</title>
  <script>(function(){{document.documentElement.setAttribute('data-theme',localStorage.getItem('bz31_theme')||'daylight');}})();</script>
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
    <div class="card"><h2>① ADR-0716 与 0-Token 路由外专</h2><p>确立『五槽位留沙箱，一切实质资产归 .bz/』公理；全仓 375 个 EB 中 244 个含非槽位资产已纳入三态自动语义路由。</p></div>
    <div class="card"><h2>② .bz/95_kaoyan_考研 独立入口与 261 项归仓</h2><p>建立顶层 .bz/95_kaoyan_考研 软链入口，12 个核心运维脚本晋升 Git 纳管，8 个 EB 共 261 项非槽位文件 100% 归仓，四槽同步。</p></div>
    <div class="card"><h2>③ 入口自动绑定与自动立项 (new_eb.sh)</h2><p>new_eb.sh 自动调用 --mode bind-eb 注入 Cogni-Target-BZ；遇到全新业务主题自动触发 new_bz.sh 立项，无需人工提醒。</p></div>
    <div class="card"><h2>④ 出口门禁哨兵 (gate_0522 v3.0 &amp; Skill 42 v6)</h2><p>新增 SANDBOX_ONLY_ORPHAN_GUARD 与 Skill 42 G13 规约，从制度与代码双层阻断沙箱孤儿资产逃逸。</p></div>
  </div>
  <script>function setTheme(t){{document.documentElement.setAttribute('data-theme',t);localStorage.setItem('bz31_theme',t);}}</script>
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
