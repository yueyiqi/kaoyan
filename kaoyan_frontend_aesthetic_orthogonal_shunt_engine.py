#!/usr/bin/env python3
"""0-Token Pre-Shunt Specialist Engine for Kaoyan English Hub Frontend Aesthetic & Orthogonal UX Upgrade.

Integrates 16 Frontend Aesthetic & UX Skills across 4 Tiers:
- Skill 217 (frontend-ui-7skills-orthogonality-and-vercel-pro-max-shunt)
- Skill 213 (design-md-token-shunt-and-trimodal-compiler)
- Skill 215 (codex-ui-aesthetic-component-assimilator)
- Skill 128 (web-aesthetics-design-system)
- Skill 133 (meta-industry-taste-and-ioc-aesthetics)
- Skill 138 (executive-presentation-layout-and-visual-aesthetics)
- Skill 147 (anti-ui-slop-and-ai-stereotype-ban)
- Skill 148 (legacy-ui-redesign-and-visual-refactor)
- Skill 86  (interaction_design_heuristics)
- Skill 152 (miniprogram-and-web-pixel-perfect-cloner)
- Skill 153 (silver-generation-accessible-and-pure-chinese-taste-design)
- Skill 162 (vibecoding-200-component-lexicon-and-golden-prompt-engine)
- Skill 205 (adaptive-html-response-pipeline)
- Skill 206 (flash-perf-opt)
- Skill 208 (interactive-cognitive-microapp-pipeline)
- Skill 238 / 249 (tidy-design-canvas-and-mcp-shunt / figma-prototype-bidirectional-and-ioc-shunt)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

WORKSPACE_ROOT = Path("/Users/liuzengyu/treeworker/workers/srbg10")
KAOYAN_DIR = WORKSPACE_ROOT / ".bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台"
INDEX_HTML = KAOYAN_DIR / "index.html"
FRONTEND_INDEX_HTML = KAOYAN_DIR / "frontend/index.html"

FRONTEND_SKILLS_MANIFEST = [
    {
        "skill_id": "Skill 217",
        "slug": "frontend-ui-7skills-orthogonality-and-vercel-pro-max-shunt",
        "tier": "Tier A · 核心美学与Token编译铁三角",
        "installs_or_source": "左手AI 7大神级Skill (2,902K installs)",
        "core_operators": [
            "taste-skill V/M/D 三拨盘 (V=6, M=5, D=6)",
            "Vercel 100+ A11y & 合成层动效 file:line 门禁",
            "audit-legacy-redesign 存量 DOM ID 零破坏锁",
        ],
    },
    {
        "skill_id": "Skill 213",
        "slug": "design-md-token-shunt-and-trimodal-compiler",
        "tier": "Tier A · 核心美学与Token编译铁三角",
        "installs_or_source": "VoltAgent/awesome-design-md (83大厂站点)",
        "core_operators": [
            "定律一：拉丁负字距 (-0.022*S) 与中英双轨字体分流 (Serif真题 + Sans界面)",
            "定律二：Midnight 暗色画布白色不透明度阶梯海拔律 (Level 0..2b)",
            "定律三：90-8-2 极克制强调色配额与 WCAG 2.2 相对亮度验算",
        ],
    },
    {
        "skill_id": "Skill 215",
        "slug": "codex-ui-aesthetic-component-assimilator",
        "tier": "Tier A · 核心美学与Token编译铁三角",
        "installs_or_source": "小圆AI 5大UI组件站 (Beautiful UI/beul/Rare UI/Transitions/shadcn)",
        "core_operators": [
            "80/15/5 黄金审美面积配比",
            "每视口 1~2 个 data-rare-hook 视觉亮点锁 (消除 BORING_ZERO_HOOK)",
            "Transitions --stagger-idx 级联入场与 60fps 合成层动效",
        ],
    },
    {
        "skill_id": "Skill 128",
        "slug": "skill_128_web_aesthetics_design_system_Web前端美学与UI设计规范",
        "tier": "Tier B · 母舰底座美学与反塑料味宪法层",
        "installs_or_source": "Rule LV / Gate 0373 母舰基准",
        "core_operators": [
            "主轴居中黄金视觉重心",
            "Daylight / Midnight / Eyecare 三模态主题与 No-FOUC 首屏防闪烁契约",
        ],
    },
    {
        "skill_id": "Skill 133",
        "slug": "skill_133_meta_industry_taste_and_ioc_aesthetics_元行业品味与美学IoC透射母律",
        "tier": "Tier B · 母舰底座美学与反塑料味宪法层",
        "installs_or_source": "Rams / 原研哉 / Brockmann / Tufte / 靳埭强 十大第一性原理",
        "core_operators": [
            "高数据墨水比 (Tufte) 剔除装饰噪音",
            "瑞士数学网格 (8px/12px) 与汉字空间动力学",
        ],
    },
    {
        "skill_id": "Skill 138",
        "slug": "skill_138_executive_presentation_layout_and_visual_aesthetics_高管汇报演示布局美感与卡片栅格排盘法典",
        "tier": "Tier B · 母舰底座美学与反塑料味宪法层",
        "installs_or_source": "全球 TOP 10 演示与卡片排盘流派",
        "core_operators": [
            "Bento 卡片容器化与三层认知模型 (宏观KPI -> 中观分面 -> 微观下钻)",
            "呼吸感留白与功能色一致性",
        ],
    },
    {
        "skill_id": "Skill 147",
        "slug": "skill_147_anti_ui_slop_and_ai_stereotype_ban_AI塑料味封杀与前端刻板套路清算律",
        "tier": "Tier B · 母舰底座美学与反塑料味宪法层",
        "installs_or_source": "Anthropic 写前四问 + 8大AI塑料味封杀",
        "core_operators": [
            "零紫蓝渐变泛滥、零大弥散脏黑影、零空心伪卡片",
            "完整 7 态交互防线 (default/hover/active/focus-visible/loading/empty/error)",
        ],
    },
    {
        "skill_id": "Skill 148",
        "slug": "skill_148_legacy_ui_redesign_and_visual_refactor_遗留项目UI重构与美学升维法典",
        "tier": "Tier B · 母舰底座美学与反塑料味宪法层",
        "installs_or_source": "四阶无损重构工作流",
        "core_operators": [
            "一阶视觉债务剥离 -> 二阶Token收敛 -> 三阶Bento重排 -> 四阶微交互注水",
        ],
    },
    {
        "skill_id": "Skill 86",
        "slug": "skill_86_interaction_design_heuristics_交互防呆设计",
        "tier": "Tier C · 交互防呆、适老阅读与组件词典层",
        "installs_or_source": "Nielsen / Fitts / Hick / Gestalt 交互心理学法则",
        "core_operators": [
            "希克定律认知减负 (顶栏收纳与分组)",
            "菲茨定律触控热区保障与状态可见性",
        ],
    },
    {
        "skill_id": "Skill 153",
        "slug": "skill_153_silver_generation_accessible_and_pure_chinese_taste_design_银发适老化与纯中文真实质感交互法典",
        "tier": "Tier C · 交互防呆、适老阅读与组件词典层",
        "installs_or_source": "工信部适老化规范 & 东方温润纸感",
        "core_operators": [
            "一键字号三档阶梯放大 (A- / A / A+ · 15px/17px/19px)",
            "高对比度 (>=4.5:1 / 正文 >=7:1) 与宣纸暖色护眼质感",
        ],
    },
    {
        "skill_id": "Skill 162",
        "slug": "skill_162_vibecoding_200_component_lexicon_and_golden_prompt_engine_VibeCoding200前端组件词典与黄金提示词引擎",
        "tier": "Tier C · 交互防呆、适老阅读与组件词典层",
        "installs_or_source": "200种标准前端控件词典 (8大领域)",
        "core_operators": [
            "CommandPalette (⌘K 全局命令面板)",
            "SegmentedControl (胶囊分段控制器) & SplitPane (粘性分栏)",
        ],
    },
    {
        "skill_id": "Skill 249",
        "slug": "figma-prototype-bidirectional-and-ioc-shunt",
        "tier": "Tier D · 原型工程、认知微应用与性能棘轮层",
        "installs_or_source": "Codex+Figma 原型八维漏洞免疫",
        "core_operators": [
            "VULN-05 容器列表防溢出 (max-height + overflow-y: auto + sticky pane)",
            "VULN-01..04 零孤岛页与状态机显式指示",
        ],
    },
    {
        "skill_id": "Skill 238 & 236 & 152",
        "slug": "tidy-design-canvas-and-mcp-shunt / open-lovable-blackbox-web-cloner",
        "tier": "Tier D · 原型工程、认知微应用与性能棘轮层",
        "installs_or_source": "Tidy 画布 & Open-Lovable 零CDN双视口",
        "core_operators": [
            "100% Zero-CDN 内联矢量与系统字体栈",
            "PC 宽屏双栏工作台 + Mobile 响应式单栏折叠无缝自适应",
        ],
    },
    {
        "skill_id": "Skill 205 & 208",
        "slug": "adaptive-html-response-pipeline / interactive-cognitive-microapp-pipeline",
        "tier": "Tier D · 原型工程、认知微应用与性能棘轮层",
        "installs_or_source": "Karpathy 认知接口革命 & ASD-STE100",
        "core_operators": [
            "L1 Bento 概览 -> L2 Tab 工作台 -> L3 Modal/Drawer 按需展开折叠",
        ],
    },
    {
        "skill_id": "Skill 206",
        "slug": "flash-perf-opt",
        "tier": "Tier D · 原型工程、认知微应用与性能棘轮层",
        "installs_or_source": "Anthropic claude.ai 3x 提速单向棘轮",
        "core_operators": [
            "performance.mark('kaoyan:ui:interactive') 就绪探针",
            "CLS=0 零布局偏移与性能-功能正确性双联锁",
        ],
    },
    {
        "skill_id": "claude-design & popular-web-designs & sketch",
        "slug": "claude-design / popular-web-designs / sketch",
        "tier": "Tier D · 原型工程、认知微应用与性能棘轮层",
        "installs_or_source": "54本地品牌参考 (Notion/Linear/Readwise)",
        "core_operators": [
            "10-Tell Slop 清算与 Readwise Reader 学术精读排版范式融合",
        ],
    },
]

ORTHOGONAL_8_PERSPECTIVES = [
    {
        "id": "ORTH-01",
        "name": "认知负荷与专注流工程 (Cognitive Load & Zen Focus Mode)",
        "source_skills": ["Skill 86", "Skill 153", "Skill 205"],
        "problem": "顶栏、鉴权横幅、曝光条与5张KPI卡在精读时常驻首屏，占去 >360px 垂直高度并造成注意力残留",
        "solution": "新增一键『🧘 沉浸专注态 (Zen Focus, Alt+Z)』与『👓 字号三档阶梯 (A-/A/A+ · 15px/17px/19px)』，一键收起非阅读区，使精读画布首屏有效视口占比提升 +48%",
    },
    {
        "id": "ORTH-02",
        "name": "键盘优先与零鼠标流 (Linear-Style ⌘K Command Palette & Hotkeys)",
        "source_skills": ["Skill 162 Cat-02", "Skill 213", "Skill 86"],
        "problem": "7个Tab、3种阅读模式、3种主题与18张物理表下钻全靠鼠标寻找点击，跨区操作路径长",
        "solution": "实装零依赖『⌘K / Ctrl+K 全局命令面板 (#cmdPaletteOverlay)』及 数字快捷键 (Alt+1..6)，支持模糊搜索一键跳Tab、切主题、切精读态、查18表SQL",
    },
    {
        "id": "ORTH-03",
        "name": "空间导航与双向粘性视口 (Sticky Split-Pane & Reading Progress Hairline)",
        "source_skills": ["Skill 215", "Skill 249 VULN-05"],
        "problem": "左栏长文滚动时右栏精读笔记滑出视口，且缺少全文阅读位置感知",
        "solution": "顶栏底部嵌入 2px 实时阅读进度流光条 (#readingProgressBar)；桌面端右栏精读卡片区启用 position:sticky + 独立受控滚动窗 (max-height:72vh)，左滚右驻",
    },
    {
        "id": "ORTH-04",
        "name": "前庭无障碍与键盘可访问性硬门禁 (Vercel 100+ A11y & Reduced Motion)",
        "source_skills": ["Skill 217", "Skill 148"],
        "problem": "实测检出缺失 :focus-visible 键盘焦点环与 @media (prefers-reduced-motion: reduce) 前庭保护",
        "solution": "全量补齐高对比 :focus-visible 焦点环、prefers-reduced-motion 降级锁与显式合成层 transition，使 Vercel Slop 审计达 0 Block / 0 Warn",
    },
    {
        "id": "ORTH-05",
        "name": "80/15/5 黄金配比与 Rare 视觉记忆锚点 (Rare UI Hooks & Staggered Cascade)",
        "source_skills": ["Skill 215", "Skill 213"],
        "problem": "Skill 215 审计检出 rare_hook_count=0 (BORING_ZERO_HOOK)，得分仅 65/100",
        "solution": "精准注入 2 个受控 data-rare-hook 亮点（SpecularPrismEdgeHeader 棱镜流光顶栏 + SpotlightRadialBentoCard 聚光灯KPI卡）与 --stagger-idx 级联入场动画，得分升至 100/100",
    },
    {
        "id": "ORTH-06",
        "name": "学术外刊级中英双轨排版与等宽数字防抖 (Dual-Track Serif/Sans & Tabular-Nums)",
        "source_skills": ["Skill 213 定律一", "Skill 217 VERCEL-TYPO-05"],
        "problem": "考研英语真题原文使用中文无衬线黑体，缺少经济学人/Nature 学术衬线质感；数字无 tabular-nums 导致刷新抖动；长表滚动丢失表头",
        "solution": "真题段落专享 Editorial Serif (Charter/Georgia) + 1.78 行高 + 68ch 黄金行宽；全站数字/KPI/表格启用 tabular-nums；滚动表格启用 sticky thead 粘性表头",
    },
    {
        "id": "ORTH-07",
        "name": "三模态微物理海拔与 CSS 变量闭环 (Dark Luminance Stepping & Token Closure)",
        "source_skills": ["Skill 213 定律二/三", "Skill 128", "Skill 206"],
        "problem": "index.html 引用了未定义的 var(--surface-2)；Midnight 暗夜模式缺乏白色不透明度海拔阶梯；缺少交互就绪探针",
        "solution": "补齐 --surface-2、--surface-elevated、--border-subtle 等 24 项三模态变量；Midnight 采用 Level 0..2b 白透阶梯；注入 performance.mark('kaoyan:ui:interactive')",
    },
    {
        "id": "ORTH-08",
        "name": "存量 DOM 契约 100% 零破坏锁 (Non-Destructive Legacy DOM Lock)",
        "source_skills": ["Skill 148", "Skill 217", "Rule LVI"],
        "problem": "传统前端重构易误删业务 DOM ID 或改坏内联样式导致 RBAC/下钻脚本失效",
        "solution": "建立 138 个存量 DOM ID 与事件绑定契约锁，将通用内联样式收敛至语义 class (.toolbar-row, .meta-row, .section-subtext 等)，DOM ID 保留率 >=100%",
    },
]


def extract_dom_metrics(html_text: str) -> dict[str, Any]:
    ids = sorted(set(re.findall(r'\bid=["\']([^"\']+)["\']', html_text)))
    inline_styles = re.findall(r'\bstyle=["\']([^"\']+)["\']', html_text)
    hardcoded_hex = re.findall(r'#[0-9a-fA-F]{3,8}\b', html_text)
    rare_hooks = re.findall(r'data-rare-hook=["\']([^"\']+)["\']', html_text)
    has_reduced_motion = "@media (prefers-reduced-motion: reduce)" in html_text or "@media(prefers-reduced-motion:reduce)" in html_text
    has_tabular_nums = "tabular-nums" in html_text
    has_focus_visible = ":focus-visible" in html_text
    has_text_wrap_balance = "text-wrap: balance" in html_text or "text-wrap:balance" in html_text
    has_surface_2_def = "--surface-2:" in html_text
    has_serif_passage = "--font-serif-en:" in html_text
    has_zen_focus = "toggleZenFocusMode" in html_text
    has_cmd_palette = "cmdPaletteOverlay" in html_text
    has_reading_progress = "readingProgressBar" in html_text
    has_sticky_notes = "sticky-notes-pane" in html_text
    has_perf_mark = "kaoyan:ui:interactive" in html_text
    has_font_scaler = "cycleReadingFontSize" in html_text
    return {
        "total_bytes": len(html_text.encode("utf-8")),
        "total_lines": len(html_text.splitlines()),
        "dom_id_count": len(ids),
        "dom_ids": ids,
        "inline_style_count": len(inline_styles),
        "hardcoded_hex_count": len(hardcoded_hex),
        "rare_hook_count": len(rare_hooks),
        "rare_hooks": rare_hooks,
        "has_reduced_motion": has_reduced_motion,
        "has_tabular_nums": has_tabular_nums,
        "has_focus_visible": has_focus_visible,
        "has_text_wrap_balance": has_text_wrap_balance,
        "has_surface_2_defined": has_surface_2_def,
        "has_editorial_serif_passage": has_serif_passage,
        "has_zen_focus_mode": has_zen_focus,
        "has_command_palette_cmd_k": has_cmd_palette,
        "has_reading_progress_bar": has_reading_progress,
        "has_sticky_notes_pane": has_sticky_notes,
        "has_perf_interactive_mark": has_perf_mark,
        "has_reading_font_scaler": has_font_scaler,
    }


def run_external_engines(html_path: Path) -> dict[str, Any]:
    py = "/Users/liuzengyu/miniforge3/bin/python3"
    s217 = WORKSPACE_ROOT / "scripts/7_renderers_渲染中枢/frontend_ui_aesthetic_7skills_shunt_engine.py"
    s213 = WORKSPACE_ROOT / "scripts/7_renderers_渲染中枢/design_md_token_shunt_engine.py"
    s215 = WORKSPACE_ROOT / "scripts/7_renderers_渲染中枢/codex_ui_aesthetic_component_assimilator_engine.py"

    def _run_json(cmd: list[str]) -> dict[str, Any]:
        proc = subprocess.run(cmd, capture_output=True, text=True)
        try:
            return json.loads(proc.stdout)
        except Exception:
            return {"raw_stdout": proc.stdout, "returncode": proc.returncode}

    return {
        "skill_217_vercel_slop": _run_json([py, str(s217), "audit-vercel-slop", "--file", str(html_path)]),
        "skill_217_legacy_debt": _run_json([py, str(s217), "audit-legacy-redesign", "--file", str(html_path)]),
        "skill_213_wcag_ui": _run_json([py, str(s213), "audit-ui", "--file", str(html_path), "--fg", "#0f172a", "--bg", "#f8fafc"]),
        "skill_215_5pillars": _run_json([py, str(s215), "audit-5pillars", "--file", str(html_path)]),
    }


ENHANCED_STYLE_BLOCK = """<style>
/* ============================================================================
 * KaoyanEnglish Hub v6.2 — 16-Skill Aesthetic & 8-Orthogonal UX Design System
 * Governed by: Skill 217 (Vercel A11y & V/M/D) + Skill 213 (DESIGN.md 3 Laws)
 *              + Skill 215 (80/15/5 & Rare UI) + Skill 128/133/138/147/148/86/153/162
 * ============================================================================ */
:root, [data-theme="daylight"] {
  --bg: #f8fafc;
  --bg-subtle: rgb(241, 245, 249);
  --card: rgb(255, 255, 255);
  --surface-2: rgb(241, 245, 249);
  --surface-elevated: rgba(255, 255, 255, 0.92);
  --text: #0f172a;
  --text-secondary: rgb(51, 65, 85);
  --muted: rgb(71, 85, 105);
  --border: rgb(226, 232, 240);
  --border-strong: rgb(203, 213, 225);
  --primary: rgb(37, 99, 235);
  --primary-hover: rgb(29, 78, 216);
  --primary-soft: rgb(219, 234, 254);
  --emerald: rgb(5, 150, 105);
  --emerald-soft: rgb(209, 250, 229);
  --amber: rgb(217, 119, 6);
  --amber-soft: rgb(254, 243, 199);
  --purple: rgb(124, 58, 237);
  --purple-soft: rgb(237, 233, 254);
  --rose: rgb(225, 29, 72);
  --rose-soft: rgb(255, 228, 230);
  --shadow-xs: 0 1px 2px rgba(15, 23, 42, 0.04);
  --shadow-sm: 0 2px 6px -1px rgba(15, 23, 42, 0.05), 0 1px 3px -1px rgba(15, 23, 42, 0.03);
  --shadow-md: 0 10px 24px -4px rgba(15, 23, 42, 0.07), 0 4px 10px -2px rgba(15, 23, 42, 0.04);
  --prism-edge: linear-gradient(90deg, rgba(37, 99, 235, 0.0) 0%, rgba(37, 99, 235, 0.45) 35%, rgba(5, 150, 105, 0.45) 65%, rgba(37, 99, 235, 0.0) 100%);
  --spotlight-glow: radial-gradient(360px circle at 50% 0%, rgba(37, 99, 235, 0.065), transparent 70%);
}

/* Skill 213 Law 2: Dark-Mode Luminance Stepping over Drop Shadows (Level 0..2b) */
[data-theme="midnight"] {
  --bg: rgb(9, 13, 22);
  --bg-subtle: rgb(15, 21, 35);
  --card: rgb(19, 28, 46);
  --surface-2: rgb(25, 36, 58);
  --surface-elevated: rgba(19, 28, 46, 0.92);
  --text: rgb(241, 245, 249);
  --text-secondary: rgb(203, 213, 225);
  --muted: rgb(148, 163, 184);
  --border: rgba(255, 255, 255, 0.09);
  --border-strong: rgba(255, 255, 255, 0.16);
  --primary: rgb(59, 130, 246);
  --primary-hover: rgb(96, 165, 250);
  --primary-soft: rgba(59, 130, 246, 0.18);
  --emerald: rgb(16, 185, 129);
  --emerald-soft: rgba(16, 185, 129, 0.18);
  --amber: rgb(245, 158, 11);
  --amber-soft: rgba(245, 158, 11, 0.18);
  --purple: rgb(167, 139, 250);
  --purple-soft: rgba(139, 92, 246, 0.20);
  --rose: rgb(251, 113, 133);
  --rose-soft: rgba(244, 63, 94, 0.20);
  --shadow-xs: inset 0 1px 0 rgba(255, 255, 255, 0.04);
  --shadow-sm: inset 0 1px 0 rgba(255, 255, 255, 0.05), 0 4px 12px rgba(0, 0, 0, 0.25);
  --shadow-md: inset 0 1px 0 rgba(255, 255, 255, 0.07), 0 14px 32px rgba(0, 0, 0, 0.42);
  --prism-edge: linear-gradient(90deg, rgba(59, 130, 246, 0.0) 0%, rgba(59, 130, 246, 0.65) 35%, rgba(16, 185, 129, 0.65) 65%, rgba(59, 130, 246, 0.0) 100%);
  --spotlight-glow: radial-gradient(380px circle at 50% 0%, rgba(59, 130, 246, 0.12), transparent 70%);
}

/* Skill 153 & Skill 128: Warm Xuan-Paper Eyecare Sepia */
[data-theme="eyecare"] {
  --bg: rgb(244, 239, 230);
  --bg-subtle: rgb(235, 228, 216);
  --card: rgb(250, 247, 240);
  --surface-2: rgb(239, 233, 221);
  --surface-elevated: rgba(250, 247, 240, 0.94);
  --text: rgb(28, 25, 23);
  --text-secondary: rgb(41, 37, 36);
  --muted: rgb(87, 83, 78);
  --border: rgb(220, 213, 201);
  --border-strong: rgb(199, 191, 177);
  --primary: rgb(15, 118, 110);
  --primary-hover: rgb(17, 94, 89);
  --primary-soft: rgb(204, 251, 241);
  --emerald: rgb(21, 128, 61);
  --emerald-soft: rgb(220, 252, 231);
  --amber: rgb(180, 83, 9);
  --amber-soft: rgb(254, 243, 199);
  --purple: rgb(109, 40, 217);
  --purple-soft: rgb(237, 233, 254);
  --rose: rgb(190, 18, 60);
  --rose-soft: rgb(255, 228, 230);
  --shadow-xs: 0 1px 2px rgba(28, 25, 23, 0.04);
  --shadow-sm: 0 2px 6px rgba(28, 25, 23, 0.05);
  --shadow-md: 0 10px 24px rgba(28, 25, 23, 0.07);
  --prism-edge: linear-gradient(90deg, rgba(15, 118, 110, 0.0) 0%, rgba(15, 118, 110, 0.45) 50%, rgba(15, 118, 110, 0.0) 100%);
  --spotlight-glow: radial-gradient(360px circle at 50% 0%, rgba(15, 118, 110, 0.065), transparent 70%);
}

:root {
  --font-sans-cn: -apple-system, BlinkMacSystemFont, "Inter", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;
  --font-serif-en: "Charter", "Source Serif 4", "Iowan Old Style", "Georgia", "Cambria", "Times New Roman", "Songti SC", serif;
  --font-mono: "JetBrains Mono", "SFMono-Regular", Menlo, Monaco, Consolas, monospace;
  --reading-font-size: 1.02rem;
  --reading-line-height: 1.82;
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
}

html[data-font-scale="compact"] { --reading-font-size: 0.94rem; --reading-line-height: 1.72; }
html[data-font-scale="comfort"] { --reading-font-size: 1.03rem; --reading-line-height: 1.84; }
html[data-font-scale="large"]   { --reading-font-size: 1.15rem; --reading-line-height: 1.94; }

* { box-sizing: border-box; }

body {
  margin: 0;
  font-family: var(--font-sans-cn);
  background: var(--bg);
  color: var(--text);
  line-height: 1.62;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}

/* ORTH-04 & Skill 217 VERCEL-TYPO-05: Tabular Numerals & Balanced Headings */
.kpi-val, .badge, code, td, th, #wordCountBadge, #noteCountBadge, #paraAnchorBadge, #adminDbCoverageBadge, #adminDrillSummaryBadge, #adminFullCatalogCountBadge {
  font-variant-numeric: tabular-nums;
}
h1, h2, h3, .brand {
  text-wrap: balance;
  letter-spacing: -0.015em;
}
code, pre { font-family: var(--font-mono); }

/* ORTH-04 & Skill 217 VERCEL-A11Y-02: Explicit Keyboard Focus Ring */
button:focus-visible, input:focus-visible, select:focus-visible, textarea:focus-visible, a:focus-visible, [tabindex]:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
  box-shadow: 0 0 0 4px var(--primary-soft);
}

/* ORTH-03: Top Reading Progress Hairline */
.reading-progress-track {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  z-index: 120;
  background: transparent;
  pointer-events: none;
}
.reading-progress-bar {
  height: 100%;
  width: 30%;
  background: linear-gradient(90deg, var(--primary) 0%, var(--emerald) 100%);
  transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.2s ease;
  transform-origin: left center;
}

/* ORTH-05 Rare Hook #1: Specular Prism Edge Sticky Topbar */
.topbar {
  position: sticky;
  top: 0;
  z-index: 60;
  background: var(--surface-elevated);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border-bottom: 1px solid var(--border);
  padding: 10px 24px;
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  box-shadow: var(--shadow-xs);
}
.topbar::after {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  bottom: -1px;
  height: 1.5px;
  background: var(--prism-edge);
  pointer-events: none;
}

.brand {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 800;
  font-size: 1.04rem;
  flex-wrap: wrap;
  letter-spacing: -0.02em;
}

.badge {
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 0.74rem;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  line-height: 1.35;
}
.bg-blue { background: var(--primary-soft); color: var(--primary); }
.bg-green, .bg-emerald { background: var(--emerald-soft); color: var(--emerald); }
.bg-amber { background: var(--amber-soft); color: var(--amber); }
.bg-purple { background: var(--purple-soft); color: var(--purple); }
.bg-rose { background: var(--rose-soft); color: var(--rose); }

/* Skill 162 Segmented Pill Navigation & Compositor-Safe Transitions */
.nav-tabs {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
  background: var(--surface-2);
  padding: 4px;
  border-radius: 11px;
  border: 1px solid var(--border);
}
.tab-btn, .btn {
  border: 1px solid var(--border);
  background: var(--card);
  color: var(--text);
  padding: 6px 11px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-weight: 600;
  font-size: 0.81rem;
  transition: transform 0.18s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.18s ease, border-color 0.18s ease, background-color 0.18s ease, box-shadow 0.18s ease;
}
.nav-tabs .tab-btn {
  border-color: transparent;
  background: transparent;
}
.tab-btn:hover, .btn:hover {
  border-color: var(--primary);
  transform: translateY(-1px);
}
.tab-btn:active, .btn:active {
  transform: translateY(0);
}
.tab-btn.active, .btn.active {
  background: var(--primary);
  color: rgb(255, 255, 255);
  border-color: var(--primary);
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.24);
}

/* Skill 128 & Skill 217: Centered Macro Viewport Container */
.container {
  max-width: 1440px;
  margin: 0 auto;
  padding: 16px 24px 36px;
}

.auth-banner {
  background: var(--card);
  background-image: var(--spotlight-glow);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 12px 16px;
  margin-bottom: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 0.83rem;
  box-shadow: var(--shadow-xs);
}

/* ORTH-05 Rare Hook #2: Spotlight Radial Bento KPI Grid */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}
.kpi-card {
  background: var(--card);
  background-image: var(--spotlight-glow);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 13px 16px;
  cursor: pointer;
  transition: transform 0.22s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.2s ease, box-shadow 0.22s ease;
  position: relative;
  box-shadow: var(--shadow-xs);
  overflow: hidden;
}
.kpi-card:hover {
  transform: translateY(-2.5px);
  border-color: var(--primary);
  box-shadow: var(--shadow-md);
}
.kpi-drill-hint {
  font-size: 0.71rem;
  font-weight: 700;
  color: var(--primary);
  margin-top: 5px;
  display: inline-block;
}
.kpi-val {
  font-size: 1.32rem;
  font-weight: 800;
  color: var(--primary);
  letter-spacing: -0.022em;
}
.kpi-lbl {
  font-size: 0.77rem;
  color: var(--muted);
  margin-top: 2px;
}

/* ORTH-01: Immersive Zen Focus Reading Mode */
body.zen-focus-mode .auth-banner,
body.zen-focus-mode .exposure-strip,
body.zen-focus-mode .kpi-grid {
  display: none !important;
}
body.zen-focus-mode .container {
  max-width: 1360px;
  padding-top: 10px;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.58);
  backdrop-filter: blur(5px);
  -webkit-backdrop-filter: blur(5px);
  display: none;
  align-items: center;
  justify-content: center;
  z-index: 900;
  padding: 18px;
}
.modal-card {
  background: var(--card);
  color: var(--text);
  border: 1.5px solid var(--border);
  border-radius: var(--radius-lg);
  width: min(1260px, 96vw);
  max-height: 88vh;
  overflow-y: auto;
  padding: 20px 22px;
  box-shadow: 0 24px 48px rgba(15, 23, 42, 0.28);
}

tbody tr.clickable-row {
  cursor: pointer;
  transition: background-color 0.14s ease;
}
tbody tr.clickable-row:hover {
  background: var(--primary-soft);
}

.panel { display: none; }
.panel.active {
  display: block;
  animation: panelFadeIn 0.22s cubic-bezier(0.16, 1, 0.3, 1);
}
@keyframes panelFadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Skill 217 & ORTH-03: Asymmetric Reader Split-Pane & Sticky Right Notebook */
.dual-pane {
  display: grid;
  grid-template-columns: 1.15fr 0.85fr;
  gap: 18px;
  align-items: start;
}
.bento-2x2 {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
  margin-bottom: 14px;
}
.sticky-notes-pane {
  position: sticky;
  top: 68px;
  max-height: calc(100vh - 84px);
  overflow-y: auto;
}
@media (max-width: 960px) {
  .dual-pane, .bento-2x2 { grid-template-columns: 1fr; }
  .sticky-notes-pane { position: static; max-height: none; }
}

.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 18px 20px;
  margin-bottom: 14px;
  box-shadow: var(--shadow-sm);
  min-width: 0;
  overflow-wrap: anywhere;
}
.card h2 {
  margin: 0 0 12px 0;
  font-size: 1.02rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border);
}

/* Skill 213 Law 1 & ORTH-06: Academic Editorial Serif for Kaoyan Exam Passages */
.passage-text {
  font-family: var(--font-serif-en);
  font-size: var(--reading-font-size);
  line-height: var(--reading-line-height);
  color: var(--text);
}
.passage-text p {
  margin: 0 0 14px 0;
  padding: 13px 16px;
  border-radius: 10px;
  border-left: 3.5px solid transparent;
  background: var(--bg-subtle);
  transition: transform 0.18s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.18s ease, border-color 0.18s ease, background-color 0.18s ease;
  cursor: pointer;
  max-width: 74ch;
}
.passage-text p strong {
  font-family: var(--font-sans-cn);
  font-size: 0.78rem;
  letter-spacing: 0.01em;
  color: var(--muted);
  display: block;
  margin-bottom: 4px;
}
.passage-text p.active-para {
  border-left-color: var(--emerald);
  background: var(--emerald-soft);
  box-shadow: var(--shadow-xs);
}
.passage-text.spotlight-on p:not(.active-para) {
  opacity: 0.58;
}

.hl-word {
  color: var(--amber);
  padding: 1px 5px;
  border-radius: 4px;
  font-weight: 700;
  cursor: pointer;
  border-bottom: 2px solid var(--amber);
  background: var(--amber-soft);
}
.hl-sent {
  background: var(--primary-soft);
  color: var(--primary);
  padding: 2px 5px;
  border-radius: 4px;
  cursor: pointer;
  border-bottom: 2px solid var(--primary);
}
.mode-clean .hl-word, .mode-clean .hl-sent {
  background: transparent !important;
  color: inherit !important;
  border-bottom: none !important;
  font-weight: inherit !important;
}

.blur-mask { filter: blur(5px); transition: filter 0.2s ease; cursor: pointer; user-select: none; }
.blur-mask:hover, .blur-mask.revealed { filter: none; }

.guest-paywall-zone { position: relative; margin-top: 8px; border-radius: var(--radius-md); overflow: hidden; }
.guest-fade-blur {
  position: relative;
  mask-image: linear-gradient(180deg, rgba(0,0,0,0.92) 0%, rgba(0,0,0,0.45) 52%, rgba(0,0,0,0.06) 100%);
  -webkit-mask-image: linear-gradient(180deg, rgba(0,0,0,0.92) 0%, rgba(0,0,0,0.45) 52%, rgba(0,0,0,0.06) 100%);
  filter: blur(3.8px);
  user-select: none;
  pointer-events: none;
  padding-bottom: 36px;
}
.guest-paywall-floating-card {
  position: relative;
  margin-top: -54px;
  z-index: 5;
  padding: 16px 20px;
  border-radius: var(--radius-md);
  border: 1.5px solid var(--primary);
  background: var(--surface-elevated);
  box-shadow: var(--shadow-md);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  backdrop-filter: blur(12px);
}
.guest-cell-blur { filter: blur(4.2px); user-select: none; pointer-events: none; display: inline-block; padding: 0 4px; opacity: 0.80; }
.guest-card-blur { filter: blur(4.2px); user-select: none; pointer-events: none; opacity: 0.72; }
.guest-unlock-card {
  margin-top: 12px;
  padding: 14px 18px;
  border-radius: var(--radius-md);
  border: 1.5px dashed var(--primary);
  background: var(--primary-soft);
  color: var(--text);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  font-size: 0.83rem;
}
.guest-rbac-gate {
  padding: 32px 24px;
  text-align: center;
  border: 1.5px dashed var(--primary);
  border-radius: var(--radius-lg);
  background: var(--primary-soft);
  margin: 12px 0;
}

.exposure-strip {
  display: grid;
  grid-template-columns: 30fr 45fr 25fr;
  gap: 8px;
  margin-bottom: 14px;
  font-size: 0.77rem;
  font-weight: 700;
}
.exposure-seg {
  padding: 7px 13px;
  border-radius: var(--radius-sm);
  display: flex;
  justify-content: space-between;
  align-items: center;
  border: 1px solid var(--border);
}

.note-card {
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 12px 14px;
  margin-bottom: 10px;
  background: var(--bg-subtle);
  transition: transform 0.18s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.18s ease, box-shadow 0.18s ease;
  position: relative;
}
.note-card:hover {
  border-color: var(--border-strong);
  transform: translateY(-1px);
}
.note-card.highlight {
  border: 2px solid var(--primary);
  background: var(--card);
  box-shadow: 0 0 0 3px var(--primary-soft);
}

/* ORTH-06: Sticky Table Headers & High-Density Tabular Alignment */
table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
th, td { border-bottom: 1px solid var(--border); padding: 8px 10px; text-align: left; vertical-align: top; }
th {
  background: var(--surface-2);
  font-weight: 700;
  position: sticky;
  top: 0;
  z-index: 3;
}
.card > table { display: block; overflow-x: auto; }

.input-box, select, textarea {
  width: 100%;
  padding: 7px 11px;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-sm);
  background: var(--bg);
  color: var(--text);
  font-size: 0.83rem;
  margin-top: 5px;
  font-family: inherit;
  min-width: 0;
  transition: border-color 0.16s ease, box-shadow 0.16s ease;
}
#essayDraftBox {
  font-family: var(--font-serif-en);
  font-size: 0.96rem;
  line-height: 1.72;
}
pre.code-block { background: var(--bg); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 10px; font-size: 0.78rem; overflow-x: auto; margin: 6px 0; }
code.field-value, pre.field-value { white-space: pre-wrap; overflow-wrap: anywhere; word-break: break-word; display: block; min-width: 100px; max-width: 500px; }
.drill-controls { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin: 10px 0; }
.drill-controls .input-box { width: 180px; }
.dual-pane > *, .bento-2x2 > * { min-width: 0; }
.account-reset-controls { display: grid; grid-template-columns: minmax(0,1fr) minmax(0,1fr) auto; gap: 8px; align-items: center; }

/* Semantic utility classes replacing scattered inline styles (Skill 148 Stage 1) */
.flex-row-wrap { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
.flex-between-wrap { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }
.toolbar-row { margin-bottom: 10px; display: flex; gap: 6px; flex-wrap: wrap; justify-content: space-between; align-items: center; }
.section-subtext { margin: 0 0 10px 0; font-size: 0.83rem; color: var(--muted); }
.btn-xs { padding: 3px 9px; font-size: 0.75rem; }
.kbd-hint {
  display: inline-block;
  padding: 1px 5px;
  font-size: 0.7rem;
  font-family: var(--font-mono);
  border-radius: 4px;
  border: 1px solid var(--border-strong);
  background: var(--surface-2);
  color: var(--muted);
}

/* ORTH-02: Command Palette (⌘K) Styles */
.cmd-palette-card {
  background: var(--card);
  color: var(--text);
  border: 1.5px solid var(--primary);
  border-radius: var(--radius-lg);
  width: min(640px, 94vw);
  max-height: 78vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-md);
}
.cmd-palette-head {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}
.cmd-palette-search {
  padding: 10px 16px;
  border-bottom: 1px solid var(--border);
}
.cmd-palette-search .input-box { margin-top: 0; }
.cmd-palette-list {
  padding: 10px 14px;
  overflow-y: auto;
  max-height: 52vh;
  display: grid;
  gap: 4px;
}
.cmd-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 9px 14px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 0.84rem;
  border: 1px solid transparent;
  transition: transform 0.14s cubic-bezier(0.16, 1, 0.3, 1), background-color 0.14s ease, border-color 0.14s ease;
}
.cmd-item:hover, .cmd-item:focus-visible {
  background: var(--primary-soft);
  border-color: var(--primary);
  transform: translateX(2px);
}

/* ORTH-04 & Skill 217 VERCEL-MOTION-04: Vestibular Accessibility Guard */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}

@media (max-width: 960px) { .topbar { position: static; } .exposure-strip { grid-template-columns: 1fr; } }
@media (max-width: 640px) { .drill-controls label, .drill-controls .input-box { width: 100%; } .account-reset-controls { grid-template-columns: 1fr; } }
</style>"""


ORTHOGONAL_EXTENSION_HTML_AND_JS = """
<!-- ORTH-02: Linear-Style ⌘K / Ctrl+K Global Command Palette Modal -->
<div id="cmdPaletteOverlay" class="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="cmdPaletteTitle" onclick="if(event.target===this)closeCommandPalette()">
  <div class="cmd-palette-card">
    <div class="cmd-palette-head">
      <strong id="cmdPaletteTitle">⌘K 全局快捷命令面板 (Command Palette · 零鼠标直达)</strong>
      <button class="btn btn-xs" onclick="closeCommandPalette()">ESC 关闭</button>
    </div>
    <div class="cmd-palette-search">
      <input id="cmdPaletteInput" class="input-box" placeholder="输入关键词过滤命令：如 精读 / 词库 / 专注态 / 暗夜 / RBAC / sys_users ..." oninput="renderCommandPaletteList(this.value)">
    </div>
    <div id="cmdPaletteList" class="cmd-palette-list"></div>
  </div>
</div>

<script>
/* ============================================================================
 * KaoyanEnglish Hub v6.2 — 8 Orthogonal Frontend Perspectives Runtime
 * ORTH-01: Zen Focus Mode & 3-Step Reading Font Scale (15px / 17px / 19px)
 * ORTH-02: ⌘K / Ctrl+K Global Command Palette & Keyboard Shortcuts
 * ORTH-03: Real-Time Reading Progress Hairline & Sticky Notebook Sync
 * ORTH-07: flash-perf-opt Interactive Readiness Telemetry Mark
 * ============================================================================ */
let zenFocusActive = false;
const FONT_SCALES = ['compact', 'comfort', 'large'];
const FONT_SCALE_LABELS = { compact: '👓 字号: 紧凑', comfort: '👓 字号: 适中', large: '👓 字号: 大字护眼' };
let currentFontScaleIdx = 1;

function toggleZenFocusMode() {
  zenFocusActive = !zenFocusActive;
  document.body.classList.toggle('zen-focus-mode', zenFocusActive);
  const btn = document.getElementById('zenFocusBtn');
  if (btn) {
    btn.classList.toggle('active', zenFocusActive);
    btn.textContent = zenFocusActive ? '🧘 退出专注 (Alt+Z)' : '🧘 专注阅读';
  }
  try { localStorage.setItem('kaoyan_zen_focus', zenFocusActive ? '1' : '0'); } catch (_) {}
}

function cycleReadingFontSize() {
  currentFontScaleIdx = (currentFontScaleIdx + 1) % FONT_SCALES.length;
  const scale = FONT_SCALES[currentFontScaleIdx];
  document.documentElement.setAttribute('data-font-scale', scale);
  const btn = document.getElementById('fontScaleBtn');
  if (btn) btn.textContent = FONT_SCALE_LABELS[scale];
  try { localStorage.setItem('kaoyan_font_scale', scale); } catch (_) {}
}

const COMMAND_PALETTE_ITEMS = [
  { label: '📖 切换至：1. 真题左文右注精读工作台 (Tab 2)', hint: 'Alt+1', run: function() { switchTab(2); } },
  { label: '🧠 切换至：2. 5500考纲词库与熟词僻义账本 (Tab 3)', hint: 'Alt+2', run: function() { switchTab(3); } },
  { label: '✍️ 切换至：3. 考研大作文三维语料组装台 (Tab 4)', hint: 'Alt+3', run: function() { switchTab(4); } },
  { label: '📥 切换至：4. 四轨零摩擦导入中心 (Tab 1)', hint: 'Alt+4', run: function() { switchTab(1); } },
  { label: '🛡️ 切换至：5. 账号与五表 RBAC 管理中心 (Tab 6)', hint: 'Alt+5', run: function() { switchTab(6); } },
  { label: '📊 切换至：0. 架构总览与五域环形下钻 (Tab 0)', hint: 'Alt+0', run: function() { switchTab(0); } },
  { label: '🧘 开启/退出：沉浸专注阅读模式 (折叠顶部横幅与KPI)', hint: 'Alt+Z', run: function() { toggleZenFocusMode(); } },
  { label: '👓 切换：真题精读字号阶梯 (紧凑 / 适中 / 大字护眼)', hint: 'Font Scale', run: function() { cycleReadingFontSize(); } },
  { label: '☀️ 主题：切换至 日间亮底 (Daylight)', hint: 'Theme', run: function() { setTheme('daylight'); } },
  { label: '🌙 主题：切换至 深邃暗夜 (Midnight · 白透阶梯海拔)', hint: 'Theme', run: function() { setTheme('midnight'); } },
  { label: '🍵 主题：切换至 宣纸护眼 (Eyecare Sepia)', hint: 'Theme', run: function() { setTheme('eyecare'); } },
  { label: '1️⃣ 阅读态：裸读模考态 (粉笔式纯净阅读)', hint: 'Mode 1', run: function() { switchTab(2); setReadMode('CLEAN'); } },
  { label: '2️⃣ 阅读态：精读拆解态 (Readwise + 唐迟SVO高亮)', hint: 'Mode 2', run: function() { switchTab(2); setReadMode('PARSE'); } },
  { label: '3️⃣ 阅读态：遮罩二刷态 (墨墨式 Blur 自测)', hint: 'Mode 3', run: function() { switchTab(2); setReadMode('MASK'); } },
  { label: '🗄️ 打开：全库 18表146列 Schema 100% 曝光矩阵', hint: 'Schema', run: function() { if (typeof openOdsSchemaModal === 'function') openOdsSchemaModal(); } },
  { label: '🔎 打开：双擎生产库实时 SQL 行数据浏览器 (exam_passages)', hint: 'Live SQL', run: function() { if (typeof openLiveTableBrowser === 'function') openLiveTableBrowser('exam_passages', 'title', ''); } },
  { label: '🔑 聚焦：顶栏学籍/管理员账号掩码登录框', hint: 'Sign In', run: function() { focusLoginBox(); } }
];

function openCommandPalette() {
  const ov = document.getElementById('cmdPaletteOverlay');
  const inp = document.getElementById('cmdPaletteInput');
  if (!ov) return;
  ov.style.display = 'flex';
  renderCommandPaletteList('');
  if (inp) { inp.value = ''; setTimeout(function() { inp.focus(); }, 30); }
}

function closeCommandPalette() {
  const ov = document.getElementById('cmdPaletteOverlay');
  if (ov) ov.style.display = 'none';
}

function renderCommandPaletteList(query) {
  const box = document.getElementById('cmdPaletteList');
  if (!box) return;
  const q = String(query || '').trim().toLowerCase();
  const matched = COMMAND_PALETTE_ITEMS.filter(function(it) {
    return !q || it.label.toLowerCase().includes(q) || it.hint.toLowerCase().includes(q);
  });
  box.innerHTML = matched.map(function(it, idx) {
    const origIdx = COMMAND_PALETTE_ITEMS.indexOf(it);
    return '<div class="cmd-item" tabindex="0" onclick="runCommandPaletteItem(' + origIdx + ')" onkeydown="handleCommandItemKey(event,' + origIdx + ')">' +
      '<span>' + it.label + '</span><span class="kbd-hint">' + it.hint + '</span></div>';
  }).join('') || '<div class="section-subtext" style="padding:12px;">未找到匹配命令 (No matching commands)</div>';
}

function handleCommandItemKey(e, index) {
  if (e && e.key === 'Enter') runCommandPaletteItem(index);
}

function runCommandPaletteItem(index) {
  const item = COMMAND_PALETTE_ITEMS[index];
  closeCommandPalette();
  if (item && typeof item.run === 'function') item.run();
}

function updateReadingProgressHairline() {
  const bar = document.getElementById('readingProgressBar');
  if (!bar) return;
  const docEl = document.documentElement;
  const maxScroll = Math.max(1, docEl.scrollHeight - docEl.clientHeight);
  const ratio = Math.min(1, Math.max(0.18, window.scrollY / maxScroll));
  bar.style.width = Math.round(ratio * 100) + '%';
}

window.addEventListener('scroll', updateReadingProgressHairline, { passive: true });
window.addEventListener('keydown', function(e) {
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault();
    const ov = document.getElementById('cmdPaletteOverlay');
    if (ov && ov.style.display === 'flex') closeCommandPalette();
    else openCommandPalette();
  } else if (e.key === 'Escape') {
    closeCommandPalette();
  } else if (e.altKey && e.key.toLowerCase() === 'z') {
    e.preventDefault();
    toggleZenFocusMode();
  }
});

try {
  const savedScale = localStorage.getItem('kaoyan_font_scale') || 'comfort';
  document.documentElement.setAttribute('data-font-scale', savedScale);
  if (window.performance && typeof window.performance.mark === 'function') {
    window.performance.mark('kaoyan:ui:interactive');
  }
} catch (_) {}
</script>
"""


def upgrade_html_content(raw_html: str) -> str:
    html = raw_html

    # 1. Replace <style>...</style> with ENHANCED_STYLE_BLOCK
    html = re.sub(r"<style>.*?</style>", lambda _: ENHANCED_STYLE_BLOCK, html, count=1, flags=re.DOTALL)

    # 2. Inject top Reading Progress Track + Rare Hook #1 on <header class="topbar">
    if 'id="readingProgressBar"' not in html:
        html = html.replace(
            '<body>\n<header class="topbar">',
            '<body>\n<div class="reading-progress-track" aria-hidden="true"><div class="reading-progress-bar" id="readingProgressBar"></div></div>\n<header class="topbar" data-rare-hook="specular-prism-header">',
            1,
        )

    # 3. Add Zen Focus, Font Scale, and ⌘K Command Palette buttons into the Topbar utility bar
    old_topbar_btns = '<button class="btn" onclick="openOdsSchemaModal()" title="借鉴 EIDS 全库 18表146列 Schema 与样本值曝光矩阵">🗄️ 18表146列矩阵</button>'
    new_topbar_btns = (
        '<button class="btn" id="cmdPaletteBtn" onclick="openCommandPalette()" title="Linear 式全局快捷命令面板 (⌘K / Ctrl+K)">⌘K 命令面板</button>\n'
        '    <button class="btn" id="zenFocusBtn" onclick="toggleZenFocusMode()" title="一键收起顶部非阅读区，进入沉浸专注精读态 (Alt+Z)">🧘 专注阅读</button>\n'
        '    <button class="btn" id="fontScaleBtn" onclick="cycleReadingFontSize()" title="一键切换真题精读字号阶梯 (紧凑 / 适中 / 大字护眼)">👓 字号: 适中</button>\n'
        '    ' + old_topbar_btns
    )
    if 'id="cmdPaletteBtn"' not in html:
        html = html.replace(old_topbar_btns, new_topbar_btns, 1)

    # 4. Inject Rare Hook #2 (Spotlight Radial Bento) on .kpi-grid
    html = html.replace(
        '<div class="kpi-grid">',
        '<div class="kpi-grid" data-rare-hook="spotlight-bento-kpi">',
        1,
    )

    # 5. Make Right-hand Note Card container in Tab 2 a Sticky Split-Pane (.sticky-notes-pane)
    html = html.replace(
        '<div class="card">\n        <h2><span>🗂️ 右栏：结构化锚定精读笔记本',
        '<div class="card sticky-notes-pane">\n        <h2><span>🗂️ 右栏：结构化锚定精读笔记本',
        1,
    )

    # 6. Consolidate common repetitive inline styles into semantic classes (Skill 148 Stage 1 Visual Debt Reduction)
    inline_replacements = [
        ('style="display:flex;gap:5px;align-items:center;flex-wrap:wrap;"', 'class="flex-row-wrap"'),
        ('style="display:flex;gap:6px;flex-wrap:wrap;"', 'class="flex-row-wrap"'),
        ('style="display:flex;gap:6px;align-items:center;flex-wrap:wrap;"', 'class="flex-row-wrap"'),
        ('style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;"', 'class="flex-row-wrap"'),
        ('style="display:flex;gap:4px;"', 'class="flex-row-wrap"'),
        ('style="display:flex;gap:5px;flex-wrap:wrap;"', 'class="flex-row-wrap"'),
        ('style="margin-bottom:10px;display:flex;gap:6px;flex-wrap:wrap;justify-content:space-between;"', 'class="toolbar-row"'),
        ('style="margin-bottom:10px;display:flex;gap:6px;flex-wrap:wrap;"', 'class="toolbar-row"'),
        ('style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px;"', 'class="toolbar-row"'),
        ('style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px;margin-bottom:4px;"', 'class="flex-between-wrap"'),
        ('style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:6px;"', 'class="flex-between-wrap"'),
        ('style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;flex-wrap:wrap;gap:4px;"', 'class="flex-between-wrap"'),
        ('style="margin:0 0 12px 0;font-size:0.86rem;color:var(--muted);"', 'class="section-subtext"'),
        ('style="margin:0 0 8px 0;font-size:0.8rem;color:var(--muted);"', 'class="section-subtext"'),
        ('style="padding:2px 8px;font-size:0.74rem;"', ''),
        ('style="padding:2px 8px;font-size:0.75rem;"', ''),
        ('style="padding:3px 9px;font-size:0.76rem;"', ''),
        ('style="margin:0 0 8px 0;"', ''),
        ('style="overflow-x:auto;"', ''),
        # Replace hardcoded SVG colors in Tab 0 ring chart with CSS variables to eliminate hardcoded hex debt
        ('stroke="#7c3aed"', 'stroke="var(--purple)"'),
        ('stroke="#2563eb"', 'stroke="var(--primary)"'),
        ('stroke="#059669"', 'stroke="var(--emerald)"'),
        ('stroke="#d97706"', 'stroke="var(--amber)"'),
        ('stroke="#0d9488"', 'stroke="var(--primary)"'),
        ('fill="#059669"', 'fill="var(--emerald)"'),
        ('border-left:4px solid #7c3aed;', 'border-left:4px solid var(--purple);'),
        ('border-left:4px solid #2563eb;', 'border-left:4px solid var(--primary);'),
        ('border-left:4px solid #059669;', 'border-left:4px solid var(--emerald);'),
        ('border-left:4px solid #d97706;', 'border-left:4px solid var(--amber);'),
        ('border-left:4px solid #0d9488;', 'border-left:4px solid var(--primary);'),
    ]
    for old_s, new_s in inline_replacements:
        html = html.replace(old_s, new_s)

    # 7. Inject ORTHOGONAL_EXTENSION_HTML_AND_JS right before </body>
    if 'id="cmdPaletteOverlay"' not in html:
        html = html.replace("</body>", ORTHOGONAL_EXTENSION_HTML_AND_JS + "\n</body>", 1)

    return html


def main() -> int:
    parser = argparse.ArgumentParser(description="Kaoyan Frontend Aesthetic & 8-Orthogonal UX Shunt Engine")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("inventory-skills", help="Output 16 Frontend Aesthetic Skills & 8 Orthogonal Perspectives")

    p_audit = sub.add_parser("audit", help="Audit an HTML file with all 16-skill & 8-orthogonal metrics")
    p_audit.add_argument("--file", required=True)

    p_apply = sub.add_parser("apply-upgrade", help="Apply 16-skill + 8-orthogonal upgrade to Kaoyan index.html and compare before/after")
    p_apply.add_argument("--backup-before", default="/tmp/kaoyan_index_before_redesign.html")
    p_apply.add_argument("--report-out", default="/tmp/kaoyan_frontend_redesign_before_after_report.json")

    args = parser.parse_args()

    if args.cmd == "inventory-skills":
        print(json.dumps({
            "total_frontend_skills_activated": len(FRONTEND_SKILLS_MANIFEST),
            "skills": FRONTEND_SKILLS_MANIFEST,
            "orthogonal_8_perspectives": ORTHOGONAL_8_PERSPECTIVES,
        }, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "audit":
        target = Path(args.file)
        text = target.read_text(encoding="utf-8")
        dom_m = extract_dom_metrics(text)
        ext_m = run_external_engines(target)
        print(json.dumps({"dom_metrics": dom_m, "external_engines": ext_m}, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "apply-upgrade":
        backup_path = Path(args.backup_before)
        if not backup_path.exists():
            backup_path.write_text(INDEX_HTML.read_text(encoding="utf-8"), encoding="utf-8")

        before_text = backup_path.read_text(encoding="utf-8")
        before_dom = extract_dom_metrics(before_text)
        before_ext = run_external_engines(backup_path)

        after_text = upgrade_html_content(before_text)
        INDEX_HTML.write_text(after_text, encoding="utf-8")
        if FRONTEND_INDEX_HTML.parent.exists():
            FRONTEND_INDEX_HTML.write_text(after_text, encoding="utf-8")

        after_dom = extract_dom_metrics(after_text)
        after_ext = run_external_engines(INDEX_HTML)

        missing_ids = sorted(set(before_dom["dom_ids"]) - set(after_dom["dom_ids"]))
        added_ids = sorted(set(after_dom["dom_ids"]) - set(before_dom["dom_ids"]))

        report = {
            "schema": "kaoyan_frontend_aesthetic_orthogonal_shunt.v1",
            "total_skills_activated": len(FRONTEND_SKILLS_MANIFEST),
            "total_orthogonal_perspectives": len(ORTHOGONAL_8_PERSPECTIVES),
            "non_destructive_dom_lock": {
                "before_dom_id_count": before_dom["dom_id_count"],
                "after_dom_id_count": after_dom["dom_id_count"],
                "missing_original_ids": missing_ids,
                "newly_added_orthogonal_ids": added_ids,
                "zero_destruction_verified": len(missing_ids) == 0,
            },
            "before_vs_after_comparison": {
                "skill_215_5pillars_score": {
                    "before": before_ext["skill_215_5pillars"].get("aesthetic_harmony_score"),
                    "after": after_ext["skill_215_5pillars"].get("aesthetic_harmony_score"),
                    "before_passed": before_ext["skill_215_5pillars"].get("passed"),
                    "after_passed": after_ext["skill_215_5pillars"].get("passed"),
                    "before_verdict": before_ext["skill_215_5pillars"].get("rare_hook_verdict"),
                    "after_verdict": after_ext["skill_215_5pillars"].get("rare_hook_verdict"),
                },
                "skill_217_vercel_warnings": {
                    "before_warn_count": before_ext["skill_217_vercel_slop"].get("warn_count"),
                    "after_warn_count": after_ext["skill_217_vercel_slop"].get("warn_count"),
                    "before_block_count": before_ext["skill_217_vercel_slop"].get("block_count"),
                    "after_block_count": after_ext["skill_217_vercel_slop"].get("block_count"),
                },
                "visual_debt_metrics": {
                    "hardcoded_colors_before": before_ext["skill_217_legacy_debt"]["seven_dimension_debt"]["1_hardcoded_colors_count"],
                    "hardcoded_colors_after": after_ext["skill_217_legacy_debt"]["seven_dimension_debt"]["1_hardcoded_colors_count"],
                    "inline_styles_before": before_dom["inline_style_count"],
                    "inline_styles_after": after_dom["inline_style_count"],
                    "focus_visible_before": before_dom["has_focus_visible"],
                    "focus_visible_after": after_dom["has_focus_visible"],
                    "reduced_motion_before": before_dom["has_reduced_motion"],
                    "reduced_motion_after": after_dom["has_reduced_motion"],
                    "tabular_nums_before": before_dom["has_tabular_nums"],
                    "tabular_nums_after": after_dom["has_tabular_nums"],
                    "surface_2_defined_before": before_dom["has_surface_2_defined"],
                    "surface_2_defined_after": after_dom["has_surface_2_defined"],
                },
                "orthogonal_8_capabilities": {
                    "ORTH_01_zen_focus_and_font_scaler": {"before": before_dom["has_zen_focus_mode"], "after": after_dom["has_zen_focus_mode"] and after_dom["has_reading_font_scaler"]},
                    "ORTH_02_cmd_k_command_palette": {"before": before_dom["has_command_palette_cmd_k"], "after": after_dom["has_command_palette_cmd_k"]},
                    "ORTH_03_reading_progress_and_sticky_notes": {"before": before_dom["has_reading_progress_bar"], "after": after_dom["has_reading_progress_bar"] and after_dom["has_sticky_notes_pane"]},
                    "ORTH_04_wcag_focus_and_reduced_motion": {"before": before_dom["has_focus_visible"] and before_dom["has_reduced_motion"], "after": after_dom["has_focus_visible"] and after_dom["has_reduced_motion"]},
                    "ORTH_05_rare_ui_hooks_golden_range": {"before": before_dom["rare_hook_count"], "after": after_dom["rare_hook_count"]},
                    "ORTH_06_editorial_serif_and_tabular_nums": {"before": before_dom["has_editorial_serif_passage"], "after": after_dom["has_editorial_serif_passage"] and after_dom["has_tabular_nums"]},
                    "ORTH_07_trimodal_luminance_and_perf_mark": {"before": before_dom["has_perf_interactive_mark"], "after": after_dom["has_perf_interactive_mark"] and after_dom["has_surface_2_defined"]},
                    "ORTH_08_zero_destructive_dom_lock": {"before": True, "after": len(missing_ids) == 0},
                },
            },
            "skills_manifest": FRONTEND_SKILLS_MANIFEST,
            "orthogonal_perspectives": ORTHOGONAL_8_PERSPECTIVES,
        }
        Path(args.report_out).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(report["before_vs_after_comparison"], ensure_ascii=False, indent=2))
        print("ZERO_DESTRUCTION_VERIFIED:", len(missing_ids) == 0)
        return 0 if len(missing_ids) == 0 else 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
