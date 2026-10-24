#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
01_kaoyanWebSrsPrd_考研网站语义单与PRD.py
====================================================================================================
三模态 Bento 图件 + 原生可编辑 MSU PPTX + 自适应交互 HTML 真机沙盒同源生成脚本 (v2.1 Live Deployed)
覆盖：
  1. [初始三思路] MOD-01 真题左文右卡精读 + MOD-02 5500动态词库 + MOD-03 作文三维语料组装
  2. [追问一] MOD-00 四轨零摩擦真题与词汇导入中枢 (5500预置+CSV批量/真题智能分段/截图OCR/知识包)
  3. [追问二] kaoyan.liuzengyu.top 域名已绑定上线 + HP(60231)->FRP(40131)->CVM Caddy 部署
====================================================================================================
"""

from __future__ import annotations
import json, os, subprocess, sys
from pathlib import Path
from typing import Any, Dict

REPO_ROOT = Path(__file__).resolve()
for _ in range(9):
    if (REPO_ROOT / "scripts" / "7_renderers_渲染中枢").exists():
        break
    REPO_ROOT = REPO_ROOT.parent

sys.path.insert(0, str(REPO_ROOT / "scripts" / "7_renderers_渲染中枢"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "3_governance_治理门禁" / "shunt"))

from svg_bento_layout_engine import BentoGrid2x2, CardSpec, MetricPair  # noqa: E402
from adaptive_presentation_compiler_engine import AdaptivePresentationCompiler  # noqa: E402
import kaoyan_english_web_semantic_prd_shunt_engine as prd_engine  # noqa: E402
import compile_kaoyan_english_web_visual_and_prototype as html_compiler  # noqa: E402
import pptx_preview_shunt_engine as preview_engine  # noqa: E402

BASE = Path(__file__).resolve().parent
STEM = "01_kaoyanWebSrsPrd_考研网站语义单与PRD"
SVG_P, PNG_P, PPTX_P = BASE / f"{STEM}.svg", BASE / f"{STEM}.png", BASE / f"{STEM}.pptx"
HTML_P, MD_P, JSON_P = BASE / f"{STEM}.html", BASE / f"{STEM}.md", BASE / "kaoyan_english_web_prd_report.json"

TITLE_CN = "研词真源 (KaoyanEnglish Hub v2.1) — 四轨导入、三模块语义单与 HP+CVM 真机部署大典"
TITLE_EN = "4-Track Ingestion Hub, Anchored Reader, 5500 Vocab, 3D Essay & kaoyan.liuzengyu.top (HP:60231 -> CVM:40131)"

CARDS = [
    CardSpec(
        title="追问一：真题与词汇四轨零摩擦导入 (MOD-00)",
        subtitle="4-Track Cold-Start & Bulk Data Intake Pipeline",
        badge="解决无题无词痛点",
        accent="#059669",
        metrics=MetricPair(left_label="预置考纲词库底座", left_value="5,500 词 + CSV批量导入", right_label="单篇真题智能切段", right_value="<= 25 ms (粘贴即成卷)"),
        items=[
            ("拒绝手填: ", "严禁逐题手敲表单；提供四轨批量摄入，彻底消除冷启动录入摩擦"),
            ("轨1 词表: ", "出厂内置5500考纲词 + 支持拖拽 CSV/TXT/墨墨/Anki 生词表 Lemma 去重"),
            ("轨2 真题: ", "整篇真题文本/Markdown/Word 一键粘贴，自动切段、算偏移、预高亮考纲词"),
            ("轨3 & 轨4: ", "支持纸质黄皮书截图 Ctrl+V OCR 识别 + .kaoyan.json 研友知识包一键互导"),
        ],
    ),
    CardSpec(
        title="模块一：真题左文右卡双向锚定精读 (MOD-01)",
        subtitle="Standoff Character-Offset Annotation [start, end)",
        badge="纠偏双栏重复原文",
        accent="#2563eb",
        metrics=MetricPair(left_label="三级摘录粒度", left_value="生词 / 长难句 / 段落", right_label="左右双向联动延迟", right_value="< 30 ms (零重影)"),
        items=[
            ("字面陷阱: ", "左右放两份相同原文浪费50%视口、引发视觉重影与跨句重叠DOM崩塌"),
            ("左栏真源: ", "唯一不可变真题画布，支持『考场净读模式』与『三色高亮精读模式』"),
            ("右栏卡片: ", "按 (para_idx, start_offset) 自动对齐长难句语法树切分卡与批注"),
            ("飞轮出口: ", "笔记卡一键『记入生词库(+1)』或『升格至作文语料库』"),
        ],
    ),
    CardSpec(
        title="模块二 & 三：5500动态词库与三维作文台 (MOD-02/03)",
        subtitle="Vocab Urgency S_urg + 6x5x3 Essay Slot Composer",
        badge="词根归一 + 挖空默写",
        accent="#7c3aed",
        metrics=MetricPair(left_label="词库三模排序视图", left_value="紧迫度 / 次数 / 时间", right_label="作文正交检索维度", right_value="6母题 × 5段落槽位"),
        items=[
            ("词库引擎: ", "Lemma 自动还原累加查询次数，强制挂载真题原句切片防背错熟词僻义"),
            ("防近因偏: ", "S_urg 融合查词次数对数、遗忘衰减与大纲权重，防新查低频词挤掉死穴词"),
            ("三维语料: ", "环保/教育/科技/文化/社会/品质 × 图画描述/立意/论证/原因/建议"),
            ("主动输出: ", "阅读好句一键升格入作文库，支持 [___] 挖空默写与右栏三段草稿拼装"),
        ],
    ),
    CardSpec(
        title="追问二/三/四：RBAC进度锚·Docker 8表与部署",
        subtitle="RBAC Progress Anchor + Dockerized 8-Table DB + HP/CVM",
        badge="Docker 8表 + 鉴权锚点",
        accent="#ea580c",
        metrics=MetricPair(left_label="受治库表与挂载卷", left_value="8 张表 · Docker /data/db", right_label="生产在线三层链路", right_value="kaoyan.liuzengyu.top"),
        items=[
            ("前端鉴权: ", "Rule LVIII 游客只读沙箱(写接口401拦截) + 学籍登录五维进度断点锚定"),
            ("后端8表: ", "T01迁移账本/T02学籍/T03进度锚/T04考纲/T05真题/T06笔记/T07词账本/T08作文"),
            ("Docker卷: ", "封装于 HP 容器 kaoyan-english-hub:2.3，挂载 db_volume 支持一键迁移升级"),
            ("CVM 网关: ", "kaoyan.liuzengyu.top 经 CVM:40131 反代至 HP:60231，避开 .vip 93%红线"),
        ],
    ),
]

PPTX_MANIFEST: Dict[str, Any] = {
    "deck_title": "研词真源 (KaoyanEnglish Hub v2.3) — 语义单、鉴权进度锚与 Docker 8表部署大典",
    "deck_subtitle": "MOD-00四轨导入 · MOD-01..03核心闭环 · MOD-04学籍鉴权锚点 · MOD-05 Docker 8表落盘 · kaoyan.liuzengyu.top",
    "author": "Product & Architecture Specialist",
    "date": "2026-10-23",
    "slug": STEM,
    "style": "executive_bento",
    "slides": [
        {
            "layout": "executive_cover",
            "badge": "KAOYAN ENGLISH PRD v2.3 · DOCKER & RBAC",
            "title": "研词真源：考研英语一体化网站 PRD 与容器化部署",
            "subtitle": "全量闭环：四轨导入 + 左文右卡精读 + 5500词库 + 三维作文 + RBAC进度锚 + Docker 8表落盘",
            "cards": [
                {"metric": "4 轨导入", "title": "MOD-00 零摩擦冷启动入口", "bullets": ["5500考纲预置 + 真题一键粘贴切段"]},
                {"metric": "RBAC 锚点", "title": "MOD-04 防乱点与五维进度锚", "bullets": ["游客只读沙箱 + 学籍跨端续读 Para K"]},
                {"metric": "Docker 8表", "title": "MOD-05 容器卷持久化与上线", "bullets": ["kaoyan.liuzengyu.top -> HP:60231"]},
            ],
        },
        {
            "layout": "asymmetric_bento",
            "badge": "QUESTION 1 · MOD-00 INGESTION HUB",
            "title": "专项突破一：真题与词汇「四轨零摩擦导入入口」方案",
            "cards": [
                {
                    "hero": True, "metric": "<= 25 ms", "title": "轨 1 & 轨 2：5500 考纲预置 + 真题智能粘贴切段",
                    "bullets": [
                        "破除冷启动死穴：拒绝『逐题填空+逐词手敲』高摩擦表单，开箱自带 5,500 大纲词根底座",
                        "轨 1 (批量词表)：支持拖拽导入 CSV / TXT / Anki / 墨墨 / 欧路生词本，自动执行 Lemma 词根归并去重",
                        "轨 2 (真题切段)：直接粘贴整篇真题文本或上传 .md/.docx，0-Token 自动提取年份题号并切分自然段",
                        "自动建系与预高亮：入库瞬间生成 [0..N) 字符偏移坐标系，并自动高亮文中命中的 5500 核心词与熟词僻义",
                    ],
                },
                {"metric": "Ctrl + V", "title": "轨 3：纸质卷 / PDF 截图 OCR 导入", "bullets": ["支持粘贴纸质黄皮书拍照或 PDF 截图", "自动识别英文段落并消除跨行连字符断词", "双栏快速预览校对后一键转入标准真题库"]},
                {"metric": ".kaoyan.json", "title": "轨 4：研友共享全站知识包互导", "bullets": ["一键打包『真题+偏移笔记+词库+作文模板』", "支持研友间直接导入成套历年真题精读包", "自带 SHA-256 校验与版本幂等合并保护"]},
            ],
        },
        {
            "layout": "split_comparison",
            "badge": "FIRST-PRINCIPLES CRITIQUE",
            "title": "第一性深入分析：同事 A 字面诉求 vs 外专升维架构",
            "cards": [
                {
                    "tag": "LITERAL ASK TRAPS", "title": "原始字面思路的四大工程与认知陷阱",
                    "bullets": [
                        "冷启动陷阱：若无批量导入与大纲预置，手工录入第一篇真题就会导致用户弃坑",
                        "阅读陷阱：左右放两份相同原文浪费 50% 视口，且跨句重叠选区破坏 HTML DOM",
                        "词汇陷阱：单按最近时间排序导致刚查 1 次的新词淹没 7 天前查过 5 次的死穴词",
                        "熟词僻义脱节：词库若脱离触发查词的那句真题原文，背默认词义上考场必丢分",
                        "作文陷阱：单维树状分类无法应对『科技+文化』双主题交叉，静态收藏易吃灰",
                    ],
                },
                {
                    "tag": "REFRAMED ARCHITECTURE", "title": "前置限幅外专升维后的工业级方案",
                    "bullets": [
                        "四轨导入中枢：5500底座预置 + 真题粘贴自动切段 + CSV词表批量归并 + 知识包互导",
                        "左文右卡锚定：左栏唯一真题画布(净读/高亮双态) + 右栏 (para_idx, start, end) 卡片流",
                        "语境动态词库：Lemma 词根归并 + 强制挂载真题原句切片 + S_urg 抗遗忘紧迫度算子",
                        "三视图自由切：支持切换『智能紧迫度 / 查询次数降序 / 最近遇到时间』+ 5500进度盘",
                        "三维语料组装：6大母题 × 5段功能槽位 × 3粒度检索 + 阅读一键升格 + 挖空默写台",
                    ],
                },
            ],
        },
        {
            "layout": "asymmetric_bento",
            "badge": "MOD-01 & MOD-02 · READING & VOCAB",
            "title": "模块一 & 二：左文右卡精读工作台与 5500 考纲词库引擎",
            "cards": [
                {
                    "hero": True, "metric": "[start, end)", "title": "Standoff 外部偏移锚定 + 词库三模排序联动",
                    "bullets": [
                        "左栏保持单一不可变真题段落 DOM，支持生词(黄)/长难句(蓝)/段落(紫)三色嵌套高亮",
                        "右栏按 (para_idx, start_offset) 严格排序长难句语法树切分卡，左点右闪、右点左居中 (<30ms)",
                        "划选生词自动还原词根 (accommodating -> accommodate)，lookup_count+1 并绑定当前真题原句",
                        "内置 S_urg = 0.45*ln(1+N) + 0.35*(1-exp(-t/tau)) + 0.20*W_tier 彻底根除近因偏差",
                    ],
                },
                {"metric": "5,500 词", "title": "考研大纲四级精准分层", "bullets": ["核心高频 1800 词 · 熟词僻义高危词 240 词", "基础大纲 3700 词 · 真题超纲背景词", "实时统计大纲覆盖率与个人顽固盲点词榜"]},
                {"metric": "1-Click", "title": "阅读 -> 词汇/作文单源飞轮", "bullets": ["阅读划词即刻充实个人高频词库", "阅读精选长难句一键升格入作文语料库", "一次真题精读同时收获阅读、词汇、写作三份资产"]},
            ],
        },
        {
            "layout": "asymmetric_bento",
            "badge": "MOD-03 · ESSAY CORPUS",
            "title": "模块三：考研作文三维语料库与挖空仿写组装台",
            "cards": [
                {
                    "hero": True, "metric": "6 × 5 × 3", "title": "主题 × 段落功能槽位 × 粒度三维正交检索",
                    "bullets": [
                        "6大考研母题：环保生态 / 教育文化 / 科技创新 / 传统文化 / 社会治理 / 青年品质",
                        "5大功能槽位：图画图表描述 / 核心立意引出 / 正反对比论证 / 原因分析 / 结尾建议",
                        "3级语料粒度：闪光词组 (Phrase) · 骨架句式模板 (Template) · 范文段落 (Paragraph)",
                        "支持『科技创新 × 传统文化 × 第二段原因分析』多维交集毫秒级检索 (< 20ms)",
                    ],
                },
                {"metric": "[______]", "title": "Cloze 挖空默写主动回忆", "bullets": ["一键将倒装/强调/让步从句骨架词变为填空", "消灭『收藏夹看懂了但考场写不出』假性掌握", "支持阅读模块精选长难句一键升格转入本库"]},
                {"metric": "160-200词", "title": "左查右写三段式草稿组装台", "bullets": ["左栏检索语料点击『+ 插入草稿』拼入右栏", "内置第一段描述/第二段论证/第三段建议框架", "实时统计英文词数，严守加尔法则不做黑盒批改"]},
            ],
        },
        {
            "layout": "asymmetric_bento",
            "badge": "QUESTION 2/3/4 · RBAC, DOCKER 8-TABLE DB & DEPLOY",
            "title": "专项突破二/三/四：RBAC进度锚、Docker 8表落盘与 HP+CVM 上线",
            "cards": [
                {
                    "hero": True, "metric": "8 Tables + RBAC", "title": "前端零信任鉴权进度锚 (MOD-04) + 后端 8 表 Docker 卷落盘 (MOD-05)",
                    "bullets": [
                        "防乱点保护 (MOD-04)：访客默认锁定本地沙箱(写接口401拦截)；学籍登录按 user_id 锚定五维进度(Para K/词频/笔记)",
                        "8张受治关系表 (MOD-05)：T01迁移账本/T02学籍/T03进度锚点/T04大纲词/T05真题/T06偏移笔记/T07个人词频/T08作文库",
                        "Docker 容器化封装：/home/hp/kaoyan_english_hub/docker-compose.yml 挂载 ./db_volume:/data/db (WAL 事务模式)",
                        "一键迁移升级：容器启动自动跑 V001__init_8tables.sql；打包 db_volume 即可 10 秒跨机迁移或升级 PostgreSQL",
                    ],
                },
                {"metric": "HP : 60231", "title": "Tier 2 HP Docker 容器宿主", "bullets": ["容器 kaoyan-english-hub:2.3 监听 127.0.0.1:60231", "遵循 CVM 防倒反天罡律：不在 CVM 裸跑业务容器", "每日自动导出 .sql 与 .kaoyan.json 冷备至节点 T2"]},
                {"metric": "CVM : 40131", "title": "Tier 1 kaoyan.liuzengyu.top", "bullets": ["首选 .top 付费版(避开 .vip 93%极危红线)，已绑定生效", "HP 经 frpc_cvm166_bulk 映射本地 60231 -> 40131", "CVM caddy-proxy 反代 :40131 并注入 Host 127.0.0.1"]},
            ],
        },
    ],
}


def build_svg_and_png() -> None:
    grid = BentoGrid2x2(page_title=TITLE_CN, page_subtitle=TITLE_EN)
    grid.add_cards(CARDS)
    grid.render_to_file(SVG_P)
    rsvg = "/opt/homebrew/bin/rsvg-convert"
    if os.path.exists(rsvg):
        subprocess.run([rsvg, "-w", "1600", "--background-color", "#F8FAFC", str(SVG_P), "-o", str(PNG_P)], check=True)


def build_pptx_and_previews(data: Dict[str, Any]) -> None:
    compiler = AdaptivePresentationCompiler(PPTX_MANIFEST)
    compiler.compile_pptx(PPTX_P)
    preview_engine.compile_pptx_to_interactive_html(PPTX_P, HTML_P)
    html_compiler.compile_html(data, HTML_P)
    chk = preview_engine.run_self_check(PPTX_P, [MD_P])
    if not chk["self_consistent"]:
        raise RuntimeError(f"Preview self-check failed: {chk}")


def main() -> int:
    data = prd_engine.evaluate_all()
    MD_P.write_text(data["prd_markdown"], encoding="utf-8")
    JSON_P.write_text(json.dumps({k: v for k, v in data.items() if k != "prd_markdown"}, ensure_ascii=False, indent=2), encoding="utf-8")
    build_svg_and_png()
    build_pptx_and_previews(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
