#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
12_sshPasswordlessUmlSwimlane_免密框架UML泳道图.py
====================================================================================================
Pure Windows-Perspective Single-Source Compiler (100% stripped of M4):
Describes the SSH Passwordless Login & VS Code Git Auto-Deploy Framework purely from the
Windows Developer Perspective (Windows PowerShell/SSH + Windows Git Bash/VS Code + Alibaba Cloud Elena + GitHub):
  1. Markdown Spec (.md) with Mermaid UML Swimlane, Sequence, Key-vs-Lock Bipartite Graph, Troubleshooting Tree
  2. Bento 2x2 Infographic (.svg + .png) via svg_bento_layout_engine
  3. Dedicated Visual UML Swimlane & Key-Lock Diagram (.svg + .png)
  4. 6-Slide 100% Native Editable MSU PPTX (.pptx + _slides_preview.png/.md) via AdaptivePresentationCompiler
  5. Interactive Tri-Modal (Daylight/Midnight/Eyecare) HTML Visual Sandbox (.html) with 5 Interactive Views
====================================================================================================
"""

from __future__ import annotations

import os
import subprocess
import sys
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
import pptx_preview_shunt_engine as preview_engine  # noqa: E402

BASE = Path(__file__).resolve().parent
STEM = "12_sshPasswordlessUmlSwimlane_免密框架UML泳道图"
MD_P = BASE / f"{STEM}.md"
SVG_P = BASE / f"{STEM}.svg"
PNG_P = BASE / f"{STEM}.png"
PPTX_P = BASE / f"{STEM}.pptx"
HTML_P = BASE / f"{STEM}.html"

SWIMLANE_SVG_P = BASE / "12_ssh_passwordless_uml_swimlane_and_key_lock_diagram_泳道与锁钥拓扑图.svg"
SWIMLANE_PNG_P = BASE / "12_ssh_passwordless_uml_swimlane_and_key_lock_diagram_泳道与锁钥拓扑图.png"

TITLE_CN = "Windows 视角 SSH 免密登录与 Git 发布框架 — UML 互动泳道图及五大可视化大典"
TITLE_EN = "Windows-Centric SSH ED25519 Passwordless Auth & VS Code Git Auto-Deploy: UML Swimlane, Sequence & Key-Lock Topology"

CARDS = [
    CardSpec(
        title="一、Windows 视角四泳道互动流程图 (Swimlane)",
        subtitle="Win SSH Config / Win VS Code & Git / Alibaba Cloud Elena / GitHub",
        badge="纯 Windows 研发视角",
        accent="#2563eb",
        metrics=MetricPair(
            left_label="核心交互泳道",
            left_value="4 泳道 (Win终端/VSCode/阿里云/GH)",
            right_label="代码推送上线耗时",
            right_value="<= 3.0 秒 (自动同步重启)",
        ),
        items=[
            ("泳道1 Win密钥与SSH: ", "本地持有 id_ed25519_codeup 私钥，通过 ~/.ssh/config 免密直连 ssh elena"),
            ("泳道2 Win Git与VSCode: ", "MINGW64 克隆仓库至 D:\\kaoyanEnglish，VS Code 改码后一键 git push"),
            ("泳道3 阿里云 8.163.29.42: ", "elena 账号 authorized_keys 验签放行，post-receive / deploy-kaoyan 自动重启"),
            ("泳道4 GitHub 代码中枢: ", "yueyiqi/kaoyan.git 同时绑定 Windows 公钥与阿里云公钥，实现双向免密闭环"),
        ],
    ),
    CardSpec(
        title="二、密码学挑战-应答时序图 (Sequence)",
        subtitle="Windows OpenSSH Client <-> Alibaba Cloud sshd (:22)",
        badge="私钥永不出 Windows",
        accent="#059669",
        metrics=MetricPair(
            left_label="非对称签名算法",
            left_value="OpenSSH ED25519 (256-bit)",
            right_label="私钥网络传输量",
            right_value="0 Bytes (仅传签名值)",
        ),
        items=[
            ("第1步 寻钥声明: ", "Windows 读取 ~/.ssh/config 锁定 id_ed25519_codeup 并向服务端声明公钥 ID"),
            ("第2步 门禁质询: ", "阿里云 sshd 核对 /home/elena/.ssh/authorized_keys 命中公钥，下发随机 Nonce"),
            ("第3步 本地签名: ", "Windows 用本地私钥对 (SessionID + Nonce) 签名，私钥文件绝不离开电脑"),
            ("第4步 验签放行: ", "阿里云用公钥验签成功，开启 elena 会话并在 /var/log/auth.log 记录指纹"),
        ],
    ),
    CardSpec(
        title="三、『2把钥匙 vs 2道门禁』二分拓扑图",
        subtitle="2 Outbound Private Keys (Win & ECS) vs. 2 Inbound Locks (ECS & GitHub)",
        badge="一秒讲清方向关系",
        accent="#7c3aed",
        metrics=MetricPair(
            left_label="出站客户端私钥串",
            left_value="2 把钥匙 (Windows + 阿里云)",
            right_label="入站服务端门禁锁芯",
            right_value="2 道门禁 (阿里云 + GitHub)",
        ),
        items=[
            ("核心防混淆公理: ", "谁主动敲门 (ssh / git clone)，谁就掏自己本地的私钥；被连方只用公钥锁芯验签"),
            ("钥匙#1 (Windows私钥): ", "id_ed25519_codeup (OFeU8L1B...) -> 同时开【阿里云门禁】与【GitHub门禁】"),
            ("钥匙#2 (阿里云私钥): ", "/home/elena/.ssh/id_ed25519 (1/zjU68N...) -> 专门开【GitHub门禁】拉代码"),
            ("闭环效果: ", "Windows 可免密登阿里云、免密推 GitHub；阿里云也可免密从 GitHub 拉取更新"),
        ],
    ),
    CardSpec(
        title="四、五大互补可视化方式与排障决策树",
        subtitle="5 Complementary Visual Paradigms & Permission-Denied Decision Tree",
        badge="实战排障 100% 命中",
        accent="#ea580c",
        metrics=MetricPair(
            left_label="最佳可视化组合",
            left_value="泳道 + 二分 + 时序 + 决策 + 沙盒",
            right_label="Windows 高频坑点",
            right_value="4 类报错秒级定位",
        ),
        items=[
            ("坑点1 私钥非默认名: ", "私钥叫 id_ed25519_codeup -> 需在 Windows ~/.ssh/config 配 IdentityFile"),
            ("坑点2 Windows权限过宽: ", "报 UNPROTECTED PRIVATE KEY -> 用 PowerShell icacls 收敛为当前用户只读"),
            ("坑点3 公钥首部漏字母: ", "粘贴漏 s 变 sh-ed25519 -> 服务端用 ssh-keygen -lf 校验指纹排雷"),
            ("坑点4 服务器拉取GitHub: ", "在 ssh elena 内拉 GitHub -> 需将服务器自身 id_ed25519.pub 录入 GitHub"),
        ],
    ),
]

PPTX_MANIFEST: Dict[str, Any] = {
    "deck_title": "Windows 视角 SSH 免密登录与 Git 发布框架：UML 互动泳道图及五大可视化大典",
    "deck_subtitle": "纯 Windows 研发视角 · 四泳道互动流程 · 2把钥匙×2道锁芯二分图 · ED25519握手时序 · 4步排障决策树",
    "author": "Windows Dev & Architecture Guide",
    "date": "2026-10-24",
    "slug": STEM,
    "style": "executive_bento",
    "slides": [
        {
            "layout": "executive_cover",
            "badge": "WINDOWS DEVELOPER PERSPECTIVE · SSH & GIT VISUAL BIBLE",
            "title": "Windows 视角 SSH 免密登录：UML 泳道图与五大可视化",
            "subtitle": "从 Windows 本地配置、免密登录阿里云 elena@8.163.29.42 到 VS Code 代码一键发布全流程",
            "cards": [
                {
                    "metric": "UML 互动泳道",
                    "title": "Windows × 阿里云 × GitHub",
                    "bullets": ["纯 Windows 视角展现本地配置、远程登录、代码克隆与一键发布"],
                },
                {
                    "metric": "2 钥 × 2 锁",
                    "title": "『钥匙串 vs 门禁锁芯』二分图",
                    "bullets": ["一眼看懂 Windows 私钥与阿里云自身私钥各自开哪扇门"],
                },
                {
                    "metric": "5 大视图",
                    "title": "多维互补可视化体系",
                    "bullets": ["UML泳道图 + 锁钥二分图 + 密码学时序图 + 排障决策树 + 交互沙盒"],
                },
            ],
        },
        {
            "layout": "asymmetric_bento",
            "badge": "VISUAL PARADIGM SELECTION · 为什么需要多种可视化互补",
            "title": "除 UML 泳道图外，还有哪些更合适的免密登录可视化方式？",
            "cards": [
                {
                    "hero": True,
                    "metric": "5 大核心视图",
                    "title": "面向 Windows 开发者的五维最佳可视化方式对比",
                    "bullets": [
                        "1. 【UML 跨端互动泳道图 (Swimlane)】：最适合展示『我在 Windows 敲什么命令 -> 阿里云和 GitHub 发生什么响应』",
                        "2. 【『钥匙串 vs 门禁锁芯』二分拓扑图 (Bipartite Graph)】：最适合讲清『Windows 私钥 vs 阿里云私钥』的方向边界",
                        "3. 【UML 挑战-应答时序图 (Sequence Diagram)】：最适合解释『为什么免密登录时私钥永远不会传到服务器上』",
                        "4. 【Permission denied 故障排错决策树 (Decision Tree)】：最适合遇到报错时按 4 个分支一步步自检修复",
                    ],
                },
                {
                    "metric": "配置流向图",
                    "title": "Windows 本地文件映射图",
                    "bullets": [
                        "直观展示 C:\\Users\\Lenovo\\.ssh\\ 目录结构",
                        "config -> id_ed25519_codeup -> known_hosts",
                        "消除 PowerShell 与 Git Bash 路径混淆",
                    ],
                },
                {
                    "metric": "交互式沙盒",
                    "title": "三模态 HTML 动态仿真台",
                    "bullets": [
                        "点击泳道任意步骤即时显示对应命令与日志",
                        "支持 Daylight / Midnight / Eyecare 切换",
                        "单文件零依赖，直接在 Windows 浏览器打开",
                    ],
                },
            ],
        },
        {
            "layout": "asymmetric_bento",
            "badge": "VIEW 1 · WINDOWS-CENTRIC UML SWIMLANE",
            "title": "视图一：纯 Windows 视角四泳道互动流程图 (UML Swimlane)",
            "cards": [
                {
                    "hero": True,
                    "metric": "4 泳道 × 8 步",
                    "title": "从 Windows 本地配置到 VS Code 代码上线的完整互动链条",
                    "bullets": [
                        "【泳道 1：Windows 终端与 SSH 配置】生成 id_ed25519_codeup -> 配置 ~/.ssh/config -> 执行 ssh elena 发起免密连接",
                        "【泳道 2：Windows Git Bash 与 VS Code】git clone 拉取代码至 D:\\kaoyanEnglish -> VS Code 优化代码 -> git push 双端发布",
                        "【泳道 3：阿里云服务器 (elena@8.163.29.42)】authorized_keys 验签放行 -> post-receive 钩子或 deploy-kaoyan 自动重启服务",
                        "【泳道 4：GitHub 仓库 (yueyiqi/kaoyan.git)】settings/keys 同时验证 Windows 公钥与阿里云服务器公钥，打通双向同步",
                    ],
                },
                {
                    "metric": "ssh elena",
                    "title": "免密登录互动闭环",
                    "bullets": [
                        "Windows 自动选取 id_ed25519_codeup",
                        "阿里云 sshd 验签 SHA256:OFeU8L1B...",
                        "直接进入 elena@8.163.29.42 终端",
                    ],
                },
                {
                    "metric": "git push",
                    "title": "VS Code 发布互动闭环",
                    "bullets": [
                        "git push origin main 推送至 GitHub",
                        "git push elena main 直推阿里云自动重启",
                        "或运行 ssh elena deploy-kaoyan 拉取上线",
                    ],
                },
            ],
        },
        {
            "layout": "split_comparison",
            "badge": "VIEW 2 · KEYRING VS LOCK CYLINDER TOPOLOGY",
            "title": "视图二：最直观破除方向误区的『2 把钥匙 vs 2 道门禁』二分图",
            "cards": [
                {
                    "tag": "OUTBOUND KEYRINGS · 谁发起连接，谁掏出本地私钥",
                    "title": "左半平面：2 把本地私钥钥匙 (各自保存在本地，绝不外传)",
                    "bullets": [
                        "1. 【钥匙 #1：Windows 电脑私钥】C:\\Users\\Lenovo\\.ssh\\id_ed25519_codeup",
                        "   -> 指纹: SHA256:OFeU8L1Blc+ECOmWayawRMLIYace0UuxIVM+ojmTNiw (cl-715-codeup)",
                        "   -> 用途: 当你在 Windows 上敲 ssh elena 或 git clone/push 时，Windows 掏出这把钥匙！",
                        "2. 【钥匙 #2：阿里云服务器自身私钥】/home/elena/.ssh/id_ed25519",
                        "   -> 指纹: SHA256:1/zjU68Npra3hsJq6zhX8EDdEKVxnsHgJ4NWzDqmeI8 (elena@8.163.29.42)",
                        "   -> 用途: 当你在阿里云服务器里面敲 git clone/pull 连 GitHub 时，服务器掏出这把钥匙！",
                    ],
                },
                {
                    "tag": "INBOUND LOCK CYLINDERS · 谁接收连接，谁核对门禁白名单",
                    "title": "右半平面：2 道目标服务端公钥门禁锁芯 (Authorized Keys)",
                    "bullets": [
                        "A. 【锁芯 A：阿里云 8.163.29.42 门禁 (/home/elena/.ssh/authorized_keys)】",
                        "   -> 已录入：钥匙 #1 的公钥 (cl-715-codeup)",
                        "   -> 效果：允许 Windows 电脑通过 ssh elena 免密登录阿里云服务器！",
                        "B. 【锁芯 B：GitHub 账号 yueyiqi 门禁 (github.com/settings/keys)】",
                        "   -> 已录入：钥匙 #1 公钥 (cl-715-codeup) + 钥匙 #2 公钥 (elena@8.163.29.42)",
                        "   -> 效果：Windows 电脑和阿里云服务器都能免密向 GitHub 拉取与推送代码！",
                    ],
                },
            ],
        },
        {
            "layout": "asymmetric_bento",
            "badge": "VIEW 3 & 4 · SEQUENCE & TROUBLESHOOTING TREE",
            "title": "视图三 & 四：ED25519 挑战-应答握手时序与 Windows 排障决策树",
            "cards": [
                {
                    "hero": True,
                    "metric": "4 步密码学握手",
                    "title": "UML 时序图：按下回车执行 ssh elena 后底层发生了什么？",
                    "bullets": [
                        "Step 1 (本地寻钥)：Windows 读取 ~/.ssh/config，找到 Host elena 对应的 IdentityFile ~/.ssh/id_ed25519_codeup",
                        "Step 2 (门禁比对)：阿里云 sshd 在 /home/elena/.ssh/authorized_keys 中匹配到 cl-715-codeup 公钥，生成随机质询码 Nonce",
                        "Step 3 (私钥签名)：Windows 用本地私钥 id_ed25519_codeup 对 (SessionID + Nonce) 签名并传回（私钥本身 0 字节外传）",
                        "Step 4 (验签放行)：阿里云用公钥验签通过，开启 elena 会话并在 /var/log/auth.log 记下 Accepted publickey",
                    ],
                },
                {
                    "metric": "Windows 侧",
                    "title": "常见报错 1 & 2 (本地配置)",
                    "bullets": [
                        "报错 1: 私钥叫 id_ed25519_codeup 没配进 config",
                        "报错 2: Windows 私钥文件权限过宽被拒",
                        "解决: 配好 ~/.ssh/config + icacls 收敛权限",
                    ],
                },
                {
                    "metric": "服务端侧",
                    "title": "常见报错 3 & 4 (远端门禁)",
                    "bullets": [
                        "报错 3: 复制公钥漏了首字母 s 变 sh-ed25519",
                        "报错 4: 服务器连 GitHub 缺 elena@8.163.29.42 公钥",
                        "解决: 补齐公钥并在 GitHub 录入服务器公钥",
                    ],
                },
            ],
        },
        {
            "layout": "asymmetric_bento",
            "badge": "SUMMARY · WINDOWS DEVELOPER CHEATSHEET",
            "title": "Windows 开发者日常免密登录与 VS Code 一键上线速查卡",
            "cards": [
                {
                    "hero": True,
                    "metric": "One-Time Setup",
                    "title": "Windows 本地 ~/.ssh/config 终极标准配置 (PowerShell 与 Git Bash 通用)",
                    "bullets": [
                        "Host elena -> HostName 8.163.29.42 / User elena / IdentityFile ~/.ssh/id_ed25519_codeup / IdentitiesOnly yes",
                        "Host github.com -> HostName github.com / User git / IdentityFile ~/.ssh/id_ed25519_codeup / IdentitiesOnly yes",
                        "仓库远端绑定 (D:\\kaoyanEnglish)：origin -> git@github.com:yueyiqi/kaoyan.git | elena -> elena:/home/elena/kaoyan_english_hub",
                        "配置完成后，无论是 ssh elena 还是 git clone / pull / push 均自动匹配私钥，彻底告别手敲 -i 参数！",
                    ],
                },
                {
                    "metric": "3 秒直推",
                    "title": "方式 A：VS Code 直接推阿里云",
                    "bullets": [
                        "git add -A && git commit -m 'update'",
                        "git push origin main (同步 GitHub)",
                        "git push elena main (直推阿里云并自动重启)",
                    ],
                },
                {
                    "metric": "拉取发布",
                    "title": "方式 B：从 GitHub 拉取上线",
                    "bullets": [
                        "先在本地 git push origin main",
                        "再敲 ssh elena deploy-kaoyan",
                        "阿里云自动从 GitHub 拉取并重启服务",
                    ],
                },
            ],
        },
    ],
}


def build_dedicated_swimlane_svg() -> str:
    """Builds a pure Windows-perspective light-mode SVG combining the 4-Lane Interactive
    UML Swimlane Diagram and the 2-Key vs 2-Lock Bipartite Topology Diagram (zero M4 references)."""
    return r"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1080" width="100%" preserveAspectRatio="xMidYMid meet">
  <defs>
    <linearGradient id="bgGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#F8FAFC"/>
      <stop offset="100%" stop-color="#EFF6FF"/>
    </linearGradient>
    <marker id="arrowBlue" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#2563EB"/>
    </marker>
    <marker id="arrowGreen" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#059669"/>
    </marker>
    <marker id="arrowPurple" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#7C3AED"/>
    </marker>
    <marker id="arrowOrange" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#EA580C"/>
    </marker>
  </defs>

  <rect width="1600" height="1080" fill="url(#bgGrad)"/>

  <!-- Header Banner -->
  <rect x="30" y="20" width="1540" height="82" rx="14" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1.5"/>
  <rect x="48" y="38" width="230" height="28" rx="6" fill="#DBEAFE"/>
  <text x="163" y="57" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="13" font-weight="700" fill="#1D4ED8" text-anchor="middle">WINDOWS PERSPECTIVE UML</text>
  <text x="295" y="57" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="22" font-weight="800" fill="#0F172A">Windows 视角 SSH 免密登录与 Git 发布框架：四泳道互动流程图 × 『2钥 vs 2锁』拓扑图</text>
  <text x="295" y="84" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="13" fill="#475569">Pure Windows Developer Perspective: Windows SSH/PowerShell × Windows Git/VS Code × Alibaba Cloud (elena@8.163.29.42) × GitHub (yueyiqi/kaoyan.git)</text>

  <!-- ==================== TOP HALF: 4-LANE WINDOWS-CENTRIC UML SWIMLANE DIAGRAM ==================== -->
  <rect x="30" y="116" width="1540" height="530" rx="14" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1.5"/>
  <text x="54" y="146" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="17" font-weight="800" fill="#0F172A">视图 A：纯 Windows 视角四泳道免密登录与代码上线互动流程图 (UML Interactive Swimlane Diagram)</text>
  <text x="930" y="146" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="13" font-weight="600" fill="#2563EB">从 Windows 本地配置、免密登录阿里云到 VS Code 修改上线的端到端闭环</text>

  <!-- 4 Swimlane Columns -->
  <!-- Lane 1: Windows SSH & PowerShell -->
  <rect x="50" y="162" width="360" height="466" rx="10" fill="#F8FAFC" stroke="#93C5FD" stroke-width="1.5"/>
  <rect x="50" y="162" width="360" height="46" rx="10" fill="#EFF6FF" stroke="#93C5FD" stroke-width="1.5"/>
  <text x="230" y="184" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="14.5" font-weight="800" fill="#1E40AF" text-anchor="middle">泳道 1：Windows 密钥与终端 (PowerShell)</text>
  <text x="230" y="201" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11" fill="#2563EB" text-anchor="middle">本地私钥: ~/.ssh/id_ed25519_codeup (OFeU8L1B...)</text>

  <!-- Lane 2: Windows Git Bash & VS Code -->
  <rect x="430" y="162" width="380" height="466" rx="10" fill="#F8FAFC" stroke="#6EE7B7" stroke-width="1.5"/>
  <rect x="430" y="162" width="380" height="46" rx="10" fill="#ECFDF5" stroke="#6EE7B7" stroke-width="1.5"/>
  <text x="620" y="184" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="14.5" font-weight="800" fill="#065F46" text-anchor="middle">泳道 2：Windows 研发工作区 (Git Bash / VS Code)</text>
  <text x="620" y="201" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11" fill="#059669" text-anchor="middle">本地代码目录: D:\kaoyanEnglish (Lenovo@LAPTOP)</text>

  <!-- Lane 3: Alibaba Cloud Elena -->
  <rect x="830" y="162" width="380" height="466" rx="10" fill="#F8FAFC" stroke="#C4B5FD" stroke-width="1.5"/>
  <rect x="830" y="162" width="380" height="46" rx="10" fill="#F5F3FF" stroke="#C4B5FD" stroke-width="1.5"/>
  <text x="1020" y="184" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="14.5" font-weight="800" fill="#5B21B6" text-anchor="middle">泳道 3：阿里云生产服务器 (elena@8.163.29.42)</text>
  <text x="1020" y="201" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11" fill="#7C3AED" text-anchor="middle">门禁: authorized_keys | 自身私钥: SHA256:1/zjU68N...</text>

  <!-- Lane 4: GitHub Central -->
  <rect x="1230" y="162" width="320" height="466" rx="10" fill="#F8FAFC" stroke="#FDBA74" stroke-width="1.5"/>
  <rect x="1230" y="162" width="320" height="46" rx="10" fill="#FFF7ED" stroke="#FDBA74" stroke-width="1.5"/>
  <text x="1390" y="184" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="14.5" font-weight="800" fill="#9A3412" text-anchor="middle">泳道 4：GitHub 远端代码库 (yueyiqi)</text>
  <text x="1390" y="201" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11" fill="#EA580C" text-anchor="middle">仓库: git@github.com:yueyiqi/kaoyan.git</text>

  <!-- Swimlane Action Nodes -->
  <!-- Row 1: Key Registration & ~/.ssh/config -->
  <rect x="68" y="222" width="324" height="68" rx="8" fill="#EFF6FF" stroke="#3B82F6" stroke-width="1.5"/>
  <text x="82" y="243" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="13" font-weight="700" fill="#1E3A8A">[步骤 1] Windows 生成密钥并配置 ~/.ssh/config</text>
  <text x="82" y="262" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5" fill="#334155">私钥 id_ed25519_codeup 留本机 (icacls 收敛只读)</text>
  <text x="82" y="279" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5" fill="#1D4ED8">config 绑定 Host elena 与 Host github.com</text>

  <rect x="850" y="222" width="340" height="68" rx="8" fill="#F5F3FF" stroke="#8B5CF6" stroke-width="1.5"/>
  <text x="864" y="243" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="13" font-weight="700" fill="#4C1D95">[步骤 2a] 阿里云门禁录入 Windows 公钥</text>
  <text x="864" y="262" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5" fill="#334155">/home/elena/.ssh/authorized_keys (权限 600)</text>
  <text x="864" y="279" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5" fill="#6D28D9">登记指纹: SHA256:OFeU8L1Blc... (cl-715-codeup)</text>

  <rect x="1246" y="222" width="288" height="68" rx="8" fill="#FFF7ED" stroke="#F97316" stroke-width="1.5"/>
  <text x="1260" y="243" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="13" font-weight="700" fill="#9A3412">[步骤 2b] GitHub 录入双端公钥</text>
  <text x="1260" y="262" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5" fill="#334155">1. Win公钥: OFeU8L1B... (cl-715-codeup)</text>
  <text x="1260" y="279" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5" fill="#C2410C">2. 阿里云公钥: 1/zjU68N... (elena@8.163)</text>

  <path d="M 392 256 L 846 256" stroke="#2563EB" stroke-width="2.2" fill="none" marker-end="url(#arrowBlue)"/>
  <rect x="530" y="236" width="180" height="20" rx="4" fill="#DBEAFE"/>
  <text x="620" y="250" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11" font-weight="700" fill="#1D4ED8" text-anchor="middle">注册公钥 cl-715-codeup</text>

  <!-- Row 2: Windows SSH Passwordless Login to Elena -->
  <rect x="68" y="310" width="324" height="72" rx="8" fill="#EFF6FF" stroke="#3B82F6" stroke-width="1.5"/>
  <text x="82" y="331" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="13" font-weight="700" fill="#1E3A8A">[步骤 3] PowerShell 执行 ssh elena 免密登录</text>
  <text x="82" y="350" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5" fill="#334155">自动加载 id_ed25519_codeup 向 8.163.29.42:22</text>
  <text x="82" y="368" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5" fill="#1D4ED8">对服务端随机 Nonce 执行本地私钥签名应答</text>

  <rect x="850" y="310" width="340" height="72" rx="8" fill="#F5F3FF" stroke="#8B5CF6" stroke-width="1.5"/>
  <text x="864" y="331" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="13" font-weight="700" fill="#4C1D95">[步骤 4] 阿里云 sshd 验签通过并建立会话</text>
  <text x="864" y="350" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5" fill="#334155">auth.log: Accepted publickey for elena</text>
  <text x="864" y="368" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5" fill="#6D28D9">无需输入密码直接进入 elena@8.163.29.42 终端</text>

  <path d="M 392 346 L 846 346" stroke="#2563EB" stroke-width="2.2" fill="none" marker-end="url(#arrowBlue)"/>
  <rect x="520" y="326" width="200" height="20" rx="4" fill="#DBEAFE"/>
  <text x="620" y="340" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11" font-weight="700" fill="#1D4ED8" text-anchor="middle">ED25519 挑战-应答签名握手</text>

  <!-- Row 3: Windows Git Bash Clone from GitHub & VS Code Edit -->
  <rect x="448" y="402" width="344" height="74" rx="8" fill="#ECFDF5" stroke="#10B981" stroke-width="1.5"/>
  <text x="462" y="423" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="13" font-weight="700" fill="#065F46">[步骤 5] Git Bash 免密克隆与 VS Code 研发</text>
  <text x="462" y="442" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5" fill="#334155">git clone git@github.com:yueyiqi/kaoyan.git</text>
  <text x="462" y="460" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5" fill="#047857">拉取至 D:\kaoyanEnglish 并在 VS Code 优化代码</text>

  <rect x="1246" y="402" width="288" height="74" rx="8" fill="#FFF7ED" stroke="#F97316" stroke-width="1.5"/>
  <text x="1260" y="423" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="13" font-weight="700" fill="#9A3412">[步骤 6] GitHub 验签放行代码拉取</text>
  <text x="1260" y="442" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5" fill="#334155">匹配 cl-715-codeup (OFeU8L1B...) 公钥</text>
  <text x="1260" y="460" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5" fill="#C2410C">100% (17/17) 下发仓库对象至 Windows</text>

  <path d="M 792 439 L 1242 439" stroke="#EA580C" stroke-width="2.2" stroke-dasharray="6,4" fill="none" marker-end="url(#arrowOrange)"/>

  <!-- Row 4: VS Code Push & Auto-Deploy on Elena -->
  <rect x="448" y="498" width="344" height="88" rx="8" fill="#ECFDF5" stroke="#10B981" stroke-width="1.5"/>
  <text x="462" y="520" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="13" font-weight="700" fill="#065F46">[步骤 7] VS Code 提交并一键触发线上发布</text>
  <text x="462" y="540" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5" fill="#334155">① git push origin main (同步推送至 GitHub)</text>
  <text x="462" y="558" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5" fill="#047857">② git push elena main (或 ssh elena deploy-kaoyan)</text>
  <text x="462" y="575" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11" fill="#059669">全程免密，无需手动拷文件或进服务器敲重启命令</text>

  <rect x="850" y="498" width="340" height="88" rx="8" fill="#F5F3FF" stroke="#8B5CF6" stroke-width="1.5"/>
  <text x="864" y="520" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="13" font-weight="700" fill="#4C1D95">[步骤 8] 阿里云自动同步代码并重启生产服务</text>
  <text x="864" y="540" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5" fill="#334155">post-receive / deploy-kaoyan 自动对齐 index.html</text>
  <text x="864" y="558" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5" fill="#6D28D9">sudo systemctl restart kaoyan-english-hub</text>
  <text x="864" y="575" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11" fill="#059669" font-weight="700">探活 127.0.0.1:60231/api/health -&gt; HTTP 200 OK</text>

  <rect x="1246" y="498" width="288" height="88" rx="8" fill="#FFF7ED" stroke="#F97316" stroke-width="1.5"/>
  <text x="1260" y="520" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="13" font-weight="700" fill="#9A3412">[步骤 8b] 阿里云免密同步 GitHub</text>
  <text x="1260" y="540" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5" fill="#334155">origin = git@github.com:yueyiqi/kaoyan.git</text>
  <text x="1260" y="558" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5" fill="#C2410C">阿里云凭自身私钥 1/zjU68N... 免密拉取</text>
  <text x="1260" y="575" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11" fill="#9A3412">GitHub 与阿里云生产环境 100% 保持同源</text>

  <path d="M 792 542 L 846 542" stroke="#059669" stroke-width="2.4" fill="none" marker-end="url(#arrowGreen)"/>
  <path d="M 1190 542 L 1242 542" stroke="#7C3AED" stroke-width="2.2" fill="none" marker-end="url(#arrowPurple)"/>

  <!-- ==================== BOTTOM HALF: 2-KEY VS 2-LOCK BIPARTITE + 5 PARADIGMS ==================== -->
  <rect x="30" y="662" width="880" height="394" rx="14" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1.5"/>
  <text x="54" y="694" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="17" font-weight="800" fill="#0F172A">视图 B：Windows 视角『2 把私钥钥匙 vs 2 道公钥锁芯』二分拓扑图 (Bipartite Graph)</text>
  <text x="54" y="716" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="12.5" fill="#475569">核心公理：谁发起连接 (ssh / git clone)，谁就掏自己本地的【私钥钥匙】；目标服务器只用自己的【公钥锁芯】验签！</text>

  <!-- Left column of Bipartite: 2 Outbound Private Keyrings -->
  <rect x="54" y="732" width="370" height="304" rx="10" fill="#F8FAFC" stroke="#94A3B8" stroke-width="1.2"/>
  <text x="239" y="758" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="14" font-weight="800" fill="#1E293B" text-anchor="middle">[KEY] 出站客户端『私钥钥匙串』(仅存本机·绝不外传)</text>

  <rect x="70" y="778" width="338" height="114" rx="8" fill="#ECFDF5" stroke="#10B981" stroke-width="1.5"/>
  <text x="84" y="802" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="13" font-weight="800" fill="#065F46">钥匙 #1：Windows 电脑本地私钥 (你的主力钥匙)</text>
  <text x="84" y="824" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5" fill="#334155">文件: C:\Users\Lenovo\.ssh\id_ed25519_codeup</text>
  <text x="84" y="844" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5" fill="#334155">指纹: SHA256:OFeU8L1Blc+ECOmWayawRMLIYace0U...</text>
  <text x="84" y="864" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5" fill="#047857" font-weight="700">作用: 供 Windows 免密登阿里云 + 免密推拉 GitHub</text>

  <rect x="70" y="908" width="338" height="112" rx="8" fill="#F5F3FF" stroke="#8B5CF6" stroke-width="1.5"/>
  <text x="84" y="932" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="13" font-weight="800" fill="#5B21B6">钥匙 #2：阿里云服务器自身私钥 (服务器的钥匙)</text>
  <text x="84" y="954" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5" fill="#334155">文件: /home/elena/.ssh/id_ed25519 (在阿里云上)</text>
  <text x="84" y="974" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5" fill="#334155">指纹: SHA256:1/zjU68Npra3hsJq6zhX8EDdEKVxns...</text>
  <text x="84" y="994" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5" fill="#6D28D9" font-weight="700">作用: 供阿里云服务器自身免密从 GitHub 拉取代码</text>

  <!-- Right column of Bipartite: 2 Inbound Lock Cylinders -->
  <rect x="516" y="732" width="374" height="304" rx="10" fill="#F8FAFC" stroke="#94A3B8" stroke-width="1.2"/>
  <text x="703" y="758" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="14" font-weight="800" fill="#1E293B" text-anchor="middle">[LOCK] 入站服务端『公钥门禁锁芯』(Authorized Locks)</text>

  <rect x="532" y="778" width="342" height="114" rx="8" fill="#F5F3FF" stroke="#7C3AED" stroke-width="1.5"/>
  <text x="546" y="802" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="13" font-weight="800" fill="#4C1D95">锁芯 A：阿里云 8.163.29.42 (authorized_keys)</text>
  <text x="546" y="826" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5" fill="#047857" font-weight="700">[PASS] 已录入 钥匙 #1 公钥 (Win: cl-715-codeup)</text>
  <text x="546" y="848" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5" fill="#334155">位置: /home/elena/.ssh/authorized_keys (权限 600)</text>
  <text x="546" y="870" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5" fill="#6D28D9">效果: 你在 Windows 敲 ssh elena 直接免密进服务器</text>

  <rect x="532" y="908" width="342" height="112" rx="8" fill="#FFF7ED" stroke="#EA580C" stroke-width="1.5"/>
  <text x="546" y="932" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="13" font-weight="800" fill="#9A3412">锁芯 B：GitHub 账号 yueyiqi (settings/keys)</text>
  <text x="546" y="954" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5" fill="#047857" font-weight="700">[PASS] 已录入 钥匙 #1 公钥 (Win: cl-715-codeup)</text>
  <text x="546" y="974" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5" fill="#C2410C" font-weight="700">[PASS] 已录入 钥匙 #2 公钥 (阿里云: elena@8.163.29.42)</text>
  <text x="546" y="994" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5" fill="#9A3412">效果: Windows 与阿里云服务器均可免密推拉 GitHub</text>

  <!-- Bipartite Directed Edges -->
  <path d="M 408 825 L 528 825" stroke="#059669" stroke-width="2.6" fill="none" marker-end="url(#arrowGreen)"/>
  <path d="M 408 850 L 528 948" stroke="#059669" stroke-width="2.4" stroke-dasharray="6,3" fill="none" marker-end="url(#arrowGreen)"/>
  <path d="M 408 968 L 528 968" stroke="#7C3AED" stroke-width="2.6" fill="none" marker-end="url(#arrowPurple)"/>

  <!-- Right Card: 5 Visualization Paradigms & Decision Tree Summary -->
  <rect x="926" y="662" width="644" height="394" rx="14" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1.5"/>
  <text x="950" y="694" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="17" font-weight="800" fill="#0F172A">视图 C：Windows 免密框架『5 大可视化方式』选型矩阵</text>
  <text x="950" y="716" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="12.5" fill="#475569">除 UML 泳道图外，针对不同理解与排错需求的最合适可视化方式：</text>

  <!-- Table Rows -->
  <rect x="948" y="730" width="600" height="46" rx="7" fill="#EFF6FF" stroke="#BFDBFE" stroke-width="1"/>
  <text x="962" y="750" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="13" font-weight="700" fill="#1E40AF">1. UML 互动泳道图 (Activity Swimlane) — [5/5 跨端流程首选]</text>
  <text x="962" y="768" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5" fill="#334155">最佳场景：看清 Windows 终端、VS Code、阿里云与 GitHub 之间的操作顺序与触发关系</text>

  <rect x="948" y="784" width="600" height="46" rx="7" fill="#F5F3FF" stroke="#DDD6FE" stroke-width="1"/>
  <text x="962" y="804" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="13" font-weight="700" fill="#5B21B6">2. 『钥匙串 vs 门禁锁芯』二分拓扑图 (Bipartite Graph) — [5/5 破除混淆首选]</text>
  <text x="962" y="822" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5" fill="#334155">最佳场景：一秒讲透「Windows 私钥 (OFeU8L1B...)」与「阿里云私钥 (1/zjU68N...)」各自开哪把锁</text>

  <rect x="948" y="838" width="600" height="46" rx="7" fill="#ECFDF5" stroke="#A7F3D0" stroke-width="1"/>
  <text x="962" y="858" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="13" font-weight="700" fill="#065F46">3. UML 挑战-应答时序图 (Sequence Diagram) — [5/5 免密原理首选]</text>
  <text x="962" y="876" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5" fill="#334155">最佳场景：展示 sshd 随机质询 Nonce、Windows 本地签名应答、私钥为何 0 字节离开电脑</text>

  <rect x="948" y="892" width="600" height="46" rx="7" fill="#FFF7ED" stroke="#FED7AA" stroke-width="1"/>
  <text x="962" y="912" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="13" font-weight="700" fill="#9A3412">4. Permission Denied 排障决策树 (Decision Tree) — [5/5 实战排错首选]</text>
  <text x="962" y="930" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5" fill="#334155">最佳场景：遇到连不上时，按「私钥文件名 id_ed25519_codeup -&gt; 权限 -&gt; 锁芯方向」自检</text>

  <rect x="948" y="946" width="600" height="46" rx="7" fill="#F1F5F9" stroke="#CBD5E1" stroke-width="1"/>
  <text x="962" y="966" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="13" font-weight="700" fill="#0F172A">5. 三模态交互式 HTML 沙盒 &amp; 原生可编辑 PPTX — [5/5 演示与实操首选]</text>
  <text x="962" y="984" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5" fill="#334155">最佳场景：在浏览器中点击任意步骤查看对应 PowerShell/Git 命令与服务端 auth.log 日志</text>

  <rect x="948" y="1000" width="600" height="38" rx="7" fill="#FEF2F2" stroke="#FECACA" stroke-width="1"/>
  <text x="962" y="1024" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="12" font-weight="700" fill="#B91C1C">黄金法则：用【二分拓扑图】分清两把钥匙 + 用【UML泳道图】走通开发上线 + 用【决策树】秒级排错</text>
</svg>"""


def build_markdown() -> str:
    return f"""# Windows 视角 SSH 免密登录与 Git 发布框架：UML 互动泳道图及五大可视化大典
# (Windows-Centric SSH Passwordless Auth & VS Code Git Auto-Deploy: UML Swimlane & 5 Visual Paradigms Bible)

```yaml
[IoC_Skill_Telemetry]
Node_ID: srbg10
Agent: antigravity
LLM_Model: gemini-4-argon-high
Task_EB: eb_9036_srbg10_H_antigravity_gemini-4-argon-high_kaoyan-english-web-semantic-spec-and-prd-shunt
Status: VERIFIED
Evidence_IDs:
  - ev:ev-0025
  - ev:ev-0026
  - ev:ev-0027
  - ev:ev-0028
  - ev:ev-0029
  - ev:ev-0030
  - ev:ev-0032
Skills_Mounted:
  - adaptive-presentation-compiler (Skill 210)
  - completion-evidence-protocol (Skill 195)
  - anti-half-baked-reasoning
```

---

## 一、 核心解答：从纯 Windows 开发者视角，除了 UML 泳道图，还有哪些更合适的可视化方式？

> [!IMPORTANT]
> **纯 Windows 视角建模原则**：
> 剥离后台运维节点后，从 **Windows 开发者 (`Lenovo@LAPTOP-8M5JKBS4`)** 的视角来看，整个免密研发与上线世界只有 **3 个物理实体**：
> 1. **你的 Windows 电脑**（包含 `PowerShell / ~/.ssh` 密钥端 与 `Git Bash / VS Code D:\\kaoyanEnglish` 研发端）
> 2. **阿里云生产服务器**（`elena@8.163.29.42`，运行 `/home/elena/kaoyan_english_hub`）
> 3. **GitHub 代码托管仓库**（`git@github.com:yueyiqi/kaoyan.git`）
>
> **UML 互动泳道图 (Swimlane Diagram)** 最适合展示**「你在 Windows 上敲什么命令 $\rightarrow$ 阿里云和 GitHub 发生什么响应」**的操作流；而针对**「为什么有 2 把不同钥匙」**、**「底层如何免密握手」**、**「报 `Permission denied` 怎么排查」**，配合以下 **5 种可视化方式**效果最佳：

| 序号 | 可视化方式 (Visualization Paradigm) | 解决的核心问题（Windows 开发者视角） | 为什么在该维度比纯泳道图更直观？ |
| :--- | :--- | :--- | :--- |
| **1** | **UML 四泳道互动流程图**<br>*(Windows-Centric Activity Swimlane)* | **「我从配好免密、拉代码到 VS Code 改完上线，每一步在哪个窗口敲什么？」** | 将 Windows 拆为 `PowerShell/SSH配置` 与 `Git Bash/VS Code` 两条泳道，配合 `阿里云 elena` 与 `GitHub` 泳道，全流程一目了然 |
| **2** | **『2 把私钥钥匙 vs 2 道公钥锁芯』二分拓扑图**<br>*(2-Key vs. 2-Lock Bipartite Graph)* | **「为什么我 Windows 能连 GitHub，刚进阿里云服务器时却连不上 GitHub？」** | 左列画 **2 把出站私钥**（Windows 的 `id_ed25519_codeup` vs 阿里云的 `id_ed25519`），右列画 **2 道入站门禁锁芯**（阿里云 `authorized_keys` vs GitHub `settings/keys`），1 秒破除方向混淆 |
| **3** | **UML 密码学挑战-应答握手时序图**<br>*(ED25519 Challenge-Response Sequence)* | **「免密登录时，我的私钥文件有没有发给服务器？为什么安全？」** | 按时间轴展示 `声明公钥指纹 -> 阿里云下发随机 Nonce -> Windows 本地私钥签名 -> 阿里云公钥验签记入 auth.log`，直观证明**私钥 0 字节离开 Windows** |
| **4** | **`Permission denied` 4 步排障决策树**<br>*(Troubleshooting State Decision Tree)* | **「当 Git Bash 或 PowerShell 报 `Permission denied (publickey)` 时先查哪？」** | 把实战 4 大坑点（① 私钥文件名带 `_codeup` 后缀未配 `config`、② Windows 私钥文件权限过宽、③ 公钥漏首字母 `s`、④ 服务器缺自身 GitHub 公钥）变成傻瓜式排查树 |
| **5** | **三模态交互式 HTML 沙盒 + 原生可编辑 PPTX**<br>*(Interactive HTML Workbench & Native PPTX)* | **「如何边点边看每一步对应的真实命令与服务器日志，或直接放进汇报 PPT？」** | 点击任意泳道步骤即可查看对应命令与 `/var/log/auth.log` 原文，支持亮底/暗夜/护眼三模态切换与 PowerPoint 原生编辑 |

---

## 二、 落盘交付物全集索引 (Persisted Deliverables)

1. **Markdown 全景大典（本文件）**：[{STEM}.md](file://{MD_P})
2. **纯 Windows 视角 UML 泳道图 ×『2钥 vs 2锁』二分拓扑高清图 (`.png` / `.svg`)**：[12_ssh_passwordless_uml_swimlane_and_key_lock_diagram_泳道与锁钥拓扑图.png](file://{SWIMLANE_PNG_P}) / [12_ssh_passwordless_uml_swimlane_and_key_lock_diagram_泳道与锁钥拓扑图.svg](file://{SWIMLANE_SVG_P})
3. **2x2 Bento 四象限执行摘要图 (`.png` / `.svg`)**：[{STEM}.png](file://{PNG_P}) / [{STEM}.svg](file://{SVG_P})
4. **交互式三模态 HTML 沙盒（5 大可切换视图）**：[{STEM}.html](file://{HTML_P})
5. **100% 原生可编辑 MSU PPTX 演示文稿（6 页）**：`{PPTX_P}`（幻灯片网格预览：[{STEM}_slides_preview.png](file://{BASE / f"{STEM}_slides_preview.png"})）

---

## 三、 视图一：纯 Windows 视角四泳道免密登录与上线互动流程图 (UML Swimlane Diagram)

```mermaid
flowchart TB
    subgraph Lane_WinSSH["泳道 1：Windows 密钥与终端层 (PowerShell / ~/.ssh)<br/>本地私钥: C:\\Users\\Lenovo\\.ssh\\id_ed25519_codeup (SHA256:OFeU8L1B...)"]
        W_Key["1. 本地持有密钥对并收敛权限<br/>私钥 id_ed25519_codeup (icacls 当前用户只读)<br/>公钥 cl-715-codeup (ssh-ed25519 AAAAC3...)"]
        W_Cfg["2. 配置 C:\\Users\\Lenovo\\.ssh\\config<br/>将 Host elena (8.163.29.42) 与 Host github.com<br/>统一绑定 IdentityFile ~/.ssh/id_ed25519_codeup"]
        W_Login["3. PowerShell 免密登录阿里云<br/>执行 ssh elena<br/>用本地私钥对服务端随机 Nonce 签名应答"]
    end

    subgraph Lane_WinDev["泳道 2：Windows 研发工作区 (Git Bash MINGW64 & VS Code)<br/>本地项目路径: D:\\kaoyanEnglish (Lenovo@LAPTOP-8M5JKBS4)"]
        D_Clone["5. Git Bash 免密克隆代码至 D 盘<br/>git clone git@github.com:yueyiqi/kaoyan.git /d/kaoyanEnglish"]
        D_Edit["6. VS Code 本地修改与调试<br/>编辑 index.html / kaoyan_hub_server.py<br/>git add -A && git commit -m 'feat: 优化页面'"]
        D_Push["7. 一键免密双推上线<br/>① git push origin main (推 GitHub)<br/>② git push elena main (或 ssh elena deploy-kaoyan)"]
    end

    subgraph Lane_Elena["泳道 3：阿里云生产服务器 (elena@8.163.29.42)<br/>入站门禁: authorized_keys | 自身出站私钥: /home/elena/.ssh/id_ed25519 (SHA256:1/zjU68N...)"]
        E_Lock["1b. 阿里云门禁录入 Windows 公钥<br/>/home/elena/.ssh/authorized_keys (权限 600)<br/>登记 SHA256:OFeU8L1Blc... (cl-715-codeup)"]
        E_Auth["4. sshd 公钥验签通过并开启会话<br/>/var/log/auth.log 记录 Accepted publickey<br/>直接进入 elena@8.163.29.42 终端"]
        E_Deploy["8. 自动同步代码并重启生产服务<br/>post-receive 或 deploy-kaoyan 自动对齐 index.html<br/>sudo systemctl restart kaoyan-english-hub -> :60231 HTTP 200"]
    end

    subgraph Lane_GH["泳道 4：GitHub 代码托管中心 (git@github.com:yueyiqi/kaoyan.git)<br/>公钥门禁: https://github.com/settings/keys"]
        G_Lock["1c. GitHub 门禁录入 2 把公钥<br/>① Windows 公钥: cl-715-codeup (OFeU8L1B...)<br/>② 阿里云公钥: elena@8.163.29.42 (1/zjU68N...)"]
        G_Clone["5b. 验证 Windows 公钥放行 Clone/Push<br/>匹配 SHA256:OFeU8L1Blc...<br/>100% (17/17) 下发或接收代码提交"]
        G_Pull["8b. 验证阿里云公钥放行服务器 Pull<br/>匹配 SHA256:1/zjU68N...<br/>允许阿里云 git fetch / pull origin main"]
    end

    W_Key --> E_Lock
    W_Key --> G_Lock
    W_Key --> W_Cfg --> W_Login
    E_Lock --> E_Auth
    W_Login ==>|"ED25519 签名应答"| E_Auth
    W_Cfg --> D_Clone
    G_Lock --> G_Clone
    D_Clone ==>|"SSH 免密拉取"| G_Clone --> D_Edit --> D_Push
    D_Push ==>|"① git push origin main"| G_Clone
    D_Push ==>|"② git push elena main"| E_Deploy
    G_Clone --> G_Pull ==>|"deploy-kaoyan 免密拉取"| E_Deploy
```

---

## 四、 视图二：比泳道图更直观破除方向误区的『2 把钥匙 vs 2 道门禁』二分拓扑图 (Bipartite Graph)

```mermaid
flowchart LR
    subgraph Outbound_Keys["🔑 左半平面：出站客户端『私钥钥匙串』(谁主动连别人，谁掏自己的私钥)"]
        K_WIN["钥匙 #1：Windows 电脑本地私钥<br/>C:\\Users\\Lenovo\\.ssh\\id_ed25519_codeup<br/>指纹: SHA256:OFeU8L1Blc... (cl-715-codeup)"]
        K_ELENA["钥匙 #2：阿里云服务器自身私钥<br/>/home/elena/.ssh/id_ed25519<br/>指纹: SHA256:1/zjU68Npr... (elena@8.163.29.42)"]
    end

    subgraph Inbound_Locks["🔒 右半平面：入站服务端『公钥门禁锁芯』(谁被连接，谁用门禁白名单验签)"]
        L_ELENA["锁芯 A：阿里云 8.163.29.42 门禁<br/>/home/elena/.ssh/authorized_keys<br/>(已录入 钥匙 #1 公钥)"]
        L_GH["锁芯 B：GitHub 账号 yueyiqi 门禁<br/>https://github.com/settings/keys<br/>(已录入 钥匙 #1 公钥 + 钥匙 #2 公钥)"]
    end

    K_WIN ==>|"① Windows 免密登阿里云 (ssh elena)<br/>及一键直推 (git push elena main)"| L_ELENA
    K_WIN ==>|"② Windows 免密克隆与推送 GitHub<br/>(git clone / git push origin main)"| L_GH
    K_ELENA ==>|"③ 阿里云服务器免密从 GitHub 拉取代码<br/>(deploy-kaoyan / git pull origin main)"| L_GH
```

---

## 五、 视图三：Windows 执行 `ssh elena` 时的 ED25519 挑战-应答握手时序图 (Sequence Diagram)

```mermaid
sequenceDiagram
    autonumber
    participant User as 👩‍💻 Windows 开发者<br/>(PowerShell / Git Bash)
    participant SshClient as 🔑 Windows OpenSSH 客户端<br/>(~/.ssh/config & id_ed25519_codeup)
    participant Sshd as 🛡️ 阿里云 sshd 服务端<br/>(8.163.29.42:22 & authorized_keys)
    participant Audit as 📜 阿里云审计与发布引擎<br/>(/var/log/auth.log & post-receive)

    User->>SshClient: 输入 `ssh elena` (或 `git push elena main`)
    SshClient->>SshClient: 读取 ~/.ssh/config 匹配 Host elena<br/>定位私钥 IdentityFile ~/.ssh/id_ed25519_codeup
    SshClient->>Sshd: 发起 SSH_MSG_USERAUTH_REQUEST<br/>(User: elena, Alg: ssh-ed25519, PubKey FP: SHA256:OFeU8L1Blc...)
    Sshd->>Sshd: 检查 /home/elena/.ssh/authorized_keys (600)<br/>找到匹配的 cl-715-codeup 公钥行
    Sshd-->>SshClient: 返回一次性随机质询码 (Challenge Nonce)
    Note over SshClient: 使用 Windows 本地私钥 id_ed25519_codeup<br/>对 (SessionID + Nonce) 进行数学签名<br/>【私钥文件 0 字节离开 Windows！】
    SshClient->>Sshd: 发送 ED25519 数字签名结果
    Sshd->>Sshd: 使用 authorized_keys 中的公钥验证签名成功
    Sshd->>Audit: 记入 /var/log/auth.log:<br/>Accepted publickey for elena from 183.238.79.28 ... SHA256:OFeU8L1Blc...
    Sshd-->>User: 免密进入 elena@8.163.29.42 终端 (或自动触发 post-receive 重启网站)
```

---

## 六、 视图四：Windows 视角 `Permission denied (publickey)` 4 步排障决策树 (Decision Tree)

```mermaid
flowchart TD
    Err(["🚨 报错: Permission denied (publickey)"]) --> Step1{{"第 1 步：这行报错是在哪个窗口敲命令出现的？"}}

    Step1 -->|"在 Windows 本地窗口敲的<br/>(PowerShell 或 MINGW64 Git Bash)"| Step2{{"第 2 步：你的私钥文件名是不是非默认的 id_ed25519_codeup？"}}
    Step1 -->|"在 ssh elena 登进阿里云之后<br/>在服务器里面敲 git clone/pull 出现的"| Step_ECS{{"第 2b 步：GitHub settings/keys 里是否录入了<br/>阿里云服务器自己的公钥 elena@8.163.29.42？"}}

    Step2 -->|"是 id_ed25519_codeup，且没配进 ~/.ssh/config"| Sol_Config["✅ 修复 A：在 C:\\Users\\Lenovo\\.ssh\\config 中<br/>为 Host elena 和 Host github.com<br/>显式指定 IdentityFile ~/.ssh/id_ed25519_codeup"]
    Step2 -->|"已配好 ~/.ssh/config"| Step3{{"第 3 步：Windows 是否提示 UNPROTECTED PRIVATE KEY FILE？"}}

    Step3 -->|"是 (私钥权限过宽)"| Sol_Perm["✅ 修复 B：在 PowerShell 运行 icacls 收敛权限：<br/>icacls ~/.ssh/id_ed25519_codeup /inheritance:r<br/>icacls ~/.ssh/id_ed25519_codeup /grant:r \"$($env:USERNAME):(R)\""]
    Step3 -->|"否 (本地权限正常)"| Sol_Auth["✅ 修复 C：检查阿里云 authorized_keys 公钥首字母<br/>确保是完整 ssh-ed25519 开头 (勿漏首字母 s)<br/>且 /home/elena/.ssh 为 700、authorized_keys 为 600"]

    Step_ECS -->|"已补录 SHA256:1/zjU68N... (ev:ev-0028)"| Sol_ECS["✅ 已彻底打通：<br/>阿里云 elena@8.163.29.42 现已可直接免密 git pull GitHub！"]
```

---

## 七、 Windows 视角全链路密钥与门禁对账表 (Pure Windows-Centric Ledger)

| 钥匙编号 | 钥匙持有人 (Client) | 私钥存放路径 (永不外传) | 公钥注释 (`Comment`) | `ssh-keygen -lf` 实测 SHA256 指纹 | 锁芯 A：阿里云 `8.163.29.42` | 锁芯 B：GitHub `yueyiqi` |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **钥匙 #1** | **Windows 研发电脑 (`Lenovo`)** | `C:\\Users\\Lenovo\\.ssh\\id_ed25519_codeup` | `cl-715-codeup` | `SHA256:OFeU8L1Blc+ECOmWayawRMLIYace0UuxIVM+ojmTNiw` | ✅ 已授权 (`ssh elena` 免密) | ✅ 已授权 (`git clone/push` 免密) |
| **钥匙 #2** | **阿里云服务器 (`elena@8.163.29.42`)** | `/home/elena/.ssh/id_ed25519` | `elena@8.163.29.42` | `SHA256:1/zjU68Npra3hsJq6zhX8EDdEKVxnsHgJ4NWzDqmeI8` | *(服务器本机)* | ✅ 已授权 (`git pull` 免密) |
"""


def build_interactive_html() -> str:
    """Builds a pure Windows-perspective self-contained Tri-Modal (Daylight/Midnight/Eyecare)
    HTML visual workbench with 5 switchable visualization tabs (zero M4 references)."""
    return r"""<!DOCTYPE html>
<html lang="zh-CN" data-theme="daylight">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Windows 视角 SSH 免密登录与 Git 发布框架 — UML 互动泳道图及五大可视化沙盒</title>
<script>
(function() {
  try {
    var saved = localStorage.getItem('kaoyan_win_ssh_theme') || 'daylight';
    document.documentElement.setAttribute('data-theme', saved);
  } catch (e) {}
})();
</script>
<style>
:root, [data-theme="daylight"] {
  --bg-page: #F8FAFC;
  --bg-card: #FFFFFF;
  --bg-muted: #F1F5F9;
  --bg-accent: #EFF6FF;
  --text-main: #0F172A;
  --text-sub: #475569;
  --border-color: #CBD5E1;
  --primary: #2563EB;
  --emerald: #059669;
  --purple: #7C3AED;
  --orange: #EA580C;
  --shadow: 0 4px 16px rgba(15, 23, 42, 0.06);
}
[data-theme="midnight"] {
  --bg-page: #0B1120;
  --bg-card: #1E293B;
  --bg-muted: #0F172A;
  --bg-accent: #1E3A8A;
  --text-main: #F8FAFC;
  --text-sub: #94A3B8;
  --border-color: #334155;
  --primary: #60A5FA;
  --emerald: #34D399;
  --purple: #A78BFA;
  --orange: #FB923C;
  --shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
}
[data-theme="eyecare"] {
  --bg-page: #F4F1EA;
  --bg-card: #FAF8F3;
  --bg-muted: #EAE4D7;
  --bg-accent: #E3ECD8;
  --text-main: #2C2A25;
  --text-sub: #5C584F;
  --border-color: #D1C9B8;
  --primary: #1D4ED8;
  --emerald: #15803D;
  --purple: #6D28D9;
  --orange: #C2410C;
  --shadow: 0 4px 14px rgba(44, 42, 37, 0.08);
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif;
  background: var(--bg-page);
  color: var(--text-main);
  line-height: 1.55;
  padding: 20px;
}
.container { max-width: 1480px; margin: 0 auto; }
.topbar {
  display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center;
  gap: 16px; background: var(--bg-card); border: 1px solid var(--border-color);
  border-radius: 14px; padding: 18px 24px; box-shadow: var(--shadow); margin-bottom: 18px;
}
.badge {
  display: inline-block; padding: 4px 10px; border-radius: 6px; font-size: 12px;
  font-weight: 700; background: var(--bg-accent); color: var(--primary); margin-bottom: 6px;
}
.title-group h1 { font-size: 22px; font-weight: 800; }
.title-group p { font-size: 13px; color: var(--text-sub); margin-top: 2px; }
.theme-switcher { display: flex; gap: 8px; flex-wrap: wrap; }
.btn {
  padding: 8px 14px; border-radius: 8px; border: 1px solid var(--border-color);
  background: var(--bg-muted); color: var(--text-main); font-size: 13px; font-weight: 600;
  cursor: pointer; transition: all 0.15s ease;
}
.btn.active, .btn:hover { background: var(--primary); color: #FFF; border-color: var(--primary); }
.tabs { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 18px; }
.tab-btn {
  flex: 1 1 210px; padding: 12px 16px; border-radius: 10px; border: 1px solid var(--border-color);
  background: var(--bg-card); color: var(--text-main); font-size: 14px; font-weight: 700;
  cursor: pointer; text-align: left; box-shadow: var(--shadow);
}
.tab-btn small { display: block; font-size: 11.5px; color: var(--text-sub); font-weight: 500; margin-top: 3px; }
.tab-btn.active { border: 2px solid var(--primary); background: var(--bg-accent); }
.panel { display: none; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 14px; padding: 24px; box-shadow: var(--shadow); }
.panel.active { display: block; }
.swimlane-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-top: 16px; }
.lane { background: var(--bg-muted); border: 1px solid var(--border-color); border-radius: 12px; padding: 14px; }
.lane-header { padding-bottom: 10px; margin-bottom: 12px; border-bottom: 2px solid var(--primary); }
.lane-header h3 { font-size: 15px; font-weight: 800; }
.lane-header span { font-size: 11.5px; color: var(--text-sub); font-family: monospace; }
.step-card {
  background: var(--bg-card); border: 1px solid var(--border-color); border-left: 4px solid var(--primary);
  border-radius: 8px; padding: 12px; margin-bottom: 12px; cursor: pointer; transition: transform 0.15s ease;
}
.step-card:hover { transform: translateY(-2px); }
.step-card h4 { font-size: 13.5px; font-weight: 700; margin-bottom: 4px; }
.step-card p { font-size: 12px; color: var(--text-sub); }
.inspector {
  margin-top: 16px; padding: 16px; border-radius: 10px; background: var(--bg-muted);
  border: 1px solid var(--border-color); font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 13px; white-space: pre-wrap;
}
.bipartite-wrap { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 16px; }
.box-card { background: var(--bg-muted); border: 1px solid var(--border-color); border-radius: 12px; padding: 16px; margin-bottom: 12px; }
.box-card h4 { font-size: 15px; font-weight: 800; margin-bottom: 6px; }
.fp { font-family: monospace; font-size: 12px; padding: 4px 8px; background: var(--bg-card); border-radius: 6px; display: inline-block; margin: 4px 0; }
table.matrix { width: 100%; border-collapse: collapse; margin-top: 14px; font-size: 13.5px; }
table.matrix th, table.matrix td { border: 1px solid var(--border-color); padding: 10px 12px; text-align: left; }
table.matrix th { background: var(--bg-muted); font-weight: 700; }
pre.code {
  background: var(--bg-muted); padding: 12px; border-radius: 8px; overflow-x: auto;
  font-family: monospace; font-size: 12.5px; border: 1px solid var(--border-color); margin-top: 8px;
}
@media (max-width: 960px) {
  .swimlane-grid, .bipartite-wrap { grid-template-columns: 1fr; }
}
</style>
</head>
<body>
<div class="container">
  <header class="topbar">
    <div class="title-group">
      <span class="badge">WINDOWS DEVELOPER PERSPECTIVE · SSH &amp; GIT AUTO-DEPLOY SANDBOX</span>
      <h1>Windows 视角 SSH 免密登录与 Git 发布框架：UML 互动泳道图及五大可视化沙盒</h1>
      <p>纯 Windows 视角：Windows 终端/密钥 × Windows Git Bash/VS Code × 阿里云 (elena@8.163.29.42) × GitHub (yueyiqi/kaoyan.git)</p>
    </div>
    <div class="theme-switcher">
      <button class="btn" onclick="setTheme('daylight')">☀️ Daylight 亮底</button>
      <button class="btn" onclick="setTheme('midnight')">🌙 Midnight 暗夜</button>
      <button class="btn" onclick="setTheme('eyecare')">🌿 Eyecare 护眼</button>
    </div>
  </header>

  <nav class="tabs">
    <button class="tab-btn active" onclick="switchTab(0)">
      1. Windows 视角 UML 互动泳道图
      <small>4大泳道 × 8步点击查看底层命令与日志</small>
    </button>
    <button class="tab-btn" onclick="switchTab(1)">
      2. 『2把钥匙 vs 2道锁芯』二分图
      <small>一秒分清 Windows 私钥与阿里云自身私钥</small>
    </button>
    <button class="tab-btn" onclick="switchTab(2)">
      3. ED25519 挑战-应答握手时序
      <small>为什么免密登录时私钥 0 字节离开 Windows</small>
    </button>
    <button class="tab-btn" onclick="switchTab(3)">
      4. Permission Denied 排障决策树
      <small>Windows 常见 4 大报错秒级自检</small>
    </button>
    <button class="tab-btn" onclick="switchTab(4)">
      5. 五大可视化方式选型对比
      <small>不同场景下最合适的图表表达</small>
    </button>
  </nav>

  <!-- TAB 0: WINDOWS-CENTRIC UML SWIMLANE -->
  <section class="panel active" id="panel-0">
    <h2>视图一：纯 Windows 视角四泳道免密登录与上线互动流程图（点击任意步骤卡片查看命令与服务端响应）</h2>
    <div class="swimlane-grid">
      <div class="lane">
        <div class="lane-header">
          <h3>泳道 1：Windows 密钥与终端 (PowerShell)</h3>
          <span>私钥: ~/.ssh/id_ed25519_codeup (OFeU8L1B...)</span>
        </div>
        <div class="step-card" onclick="inspectStep(1)">
          <h4>[步骤 1] 本地密钥对准备与权限收敛</h4>
          <p>私钥 id_ed25519_codeup 保存在 C:\Users\Lenovo\.ssh\，公钥 cl-715-codeup 登记至阿里云与 GitHub。</p>
        </div>
        <div class="step-card" onclick="inspectStep(2)">
          <h4>[步骤 2] 配置 Windows ~/.ssh/config</h4>
          <p>将 Host elena (8.163.29.42) 与 Host github.com 统一绑定 IdentityFile ~/.ssh/id_ed25519_codeup。</p>
        </div>
        <div class="step-card" onclick="inspectStep(3)">
          <h4>[步骤 3] PowerShell 执行 ssh elena</h4>
          <p>发起免密连接，使用本地私钥对阿里云下发的随机质询码 Nonce 签名应答。</p>
        </div>
      </div>

      <div class="lane">
        <div class="lane-header" style="border-color: var(--emerald);">
          <h3>泳道 2：Windows 研发区 (Git Bash / VS Code)</h3>
          <span>工作目录: D:\kaoyanEnglish (Lenovo@LAPTOP)</span>
        </div>
        <div class="step-card" style="border-left-color: var(--emerald);" onclick="inspectStep(5)">
          <h4>[步骤 5] Git Bash 免密克隆仓库至 D 盘</h4>
          <p>执行 git clone git@github.com:yueyiqi/kaoyan.git /d/kaoyanEnglish 拉取完整项目。</p>
        </div>
        <div class="step-card" style="border-left-color: var(--emerald);" onclick="inspectStep(6)">
          <h4>[步骤 6] VS Code 修改代码并一键双推</h4>
          <p>修改前端/后端代码后，执行 git push origin main 推 GitHub，git push elena main 直推阿里云。</p>
        </div>
      </div>

      <div class="lane">
        <div class="lane-header" style="border-color: var(--purple);">
          <h3>泳道 3：阿里云服务器 (elena@8.163.29.42)</h3>
          <span>门禁: authorized_keys | 自身私钥: 1/zjU68N...</span>
        </div>
        <div class="step-card" style="border-left-color: var(--purple);" onclick="inspectStep(4)">
          <h4>[步骤 4] sshd 公钥验签放行并记入 auth.log</h4>
          <p>匹配 /home/elena/.ssh/authorized_keys 中的 cl-715-codeup 公钥，验签通过后开启 elena 会话。</p>
        </div>
        <div class="step-card" style="border-left-color: var(--purple);" onclick="inspectStep(7)">
          <h4>[步骤 7] 自动同步代码并重启生产服务</h4>
          <p>post-receive 钩子或 deploy-kaoyan 自动对齐 index.html，重启服务并校验 :60231 HTTP 200。</p>
        </div>
      </div>

      <div class="lane">
        <div class="lane-header" style="border-color: var(--orange);">
          <h3>泳道 4：GitHub 代码中枢 (yueyiqi/kaoyan)</h3>
          <span>门禁: github.com/settings/keys (2把公钥)</span>
        </div>
        <div class="step-card" style="border-left-color: var(--orange);" onclick="inspectStep(8)">
          <h4>[步骤 8] 验证 Windows 与阿里云双端公钥</h4>
          <p>同时信任 Windows 公钥 (OFeU8L1B...) 与阿里云自身公钥 (1/zjU68N...)，实现双向免密推拉。</p>
        </div>
      </div>
    </div>
    <div class="inspector" id="step-inspector">💡 点击上方任意步骤卡片，在此查看该步骤在 Windows / 阿里云上的真实命令、密钥指纹与日志输出。</div>
  </section>

  <!-- TAB 1: 2-KEY VS 2-LOCK BIPARTITE GRAPH -->
  <section class="panel" id="panel-1">
    <h2>视图二：『2 把私钥钥匙 vs 2 道公钥锁芯』二分拓扑图（最适合讲透方向关系）</h2>
    <p style="color: var(--text-sub); margin-top: 6px;">
      核心铁律：<b>谁主动发起连接（Client），谁就掏出自己本地的【私钥钥匙】</b>；<b>谁接收连接（Server），谁就查自己门禁里的【公钥锁芯】</b>。
    </p>
    <div class="bipartite-wrap">
      <div>
        <h3 style="margin-bottom: 10px;">🔑 左半平面：2 把出站客户端『私钥钥匙』(仅存本机·绝不外传)</h3>
        <div class="box-card">
          <h4>钥匙 #1：你的 Windows 电脑本地私钥</h4>
          <div>路径：<code>C:\Users\Lenovo\.ssh\id_ed25519_codeup</code> (`cl-715-codeup`)</div>
          <div class="fp">SHA256:OFeU8L1Blc+ECOmWayawRMLIYace0UuxIVM+ojmTNiw</div>
          <div>能开哪几把锁：<b>锁芯 A (阿里云 8.163.29.42)</b> + <b>锁芯 B (GitHub yueyiqi)</b></div>
        </div>
        <div class="box-card">
          <h4>钥匙 #2：阿里云服务器 (elena@8.163.29.42) 自身本地私钥</h4>
          <div>路径：<code>/home/elena/.ssh/id_ed25519</code> (`elena@8.163.29.42`)</div>
          <div class="fp">SHA256:1/zjU68Npra3hsJq6zhX8EDdEKVxnsHgJ4NWzDqmeI8</div>
          <div>能开哪把锁：<b>锁芯 B (GitHub yueyiqi)</b> —— 供阿里云服务器自己从 GitHub 免密拉代码</div>
        </div>
      </div>
      <div>
        <h3 style="margin-bottom: 10px;">🔒 右半平面：2 道入站服务端『公钥门禁锁芯』(Authorized Locks)</h3>
        <div class="box-card">
          <h4>锁芯 A：阿里云服务器 `8.163.29.42` 门禁白名单</h4>
          <div>物理路径：<code>/home/elena/.ssh/authorized_keys</code> (权限 600)</div>
          <ul style="margin-left: 18px; margin-top: 8px; font-size: 13px;">
            <li>✅ 已录入 <b>钥匙 #1 公钥 (`cl-715-codeup` / `OFeU8L1B...`)</b> -&gt; 允许 Windows 免密 `ssh elena` 登录与 `git push elena main`</li>
          </ul>
        </div>
        <div class="box-card">
          <h4>锁芯 B：GitHub 账号 `yueyiqi` 门禁白名单 (`github.com/settings/keys`)</h4>
          <div>保护仓库：<code>git@github.com:yueyiqi/kaoyan.git</code></div>
          <ul style="margin-left: 18px; margin-top: 8px; font-size: 13px;">
            <li>✅ 已录入 <b>钥匙 #1 公钥 (`cl-715-codeup` / `OFeU8L1B...`)</b> -&gt; 允许 Windows 免密 `git clone / push`</li>
            <li>✅ 已录入 <b>钥匙 #2 公钥 (`elena@8.163.29.42` / `1/zjU68N...`)</b> -&gt; 允许阿里云服务器免密 `git pull`</li>
          </ul>
        </div>
      </div>
    </div>
  </section>

  <!-- TAB 2: CRYPTOGRAPHIC SEQUENCE -->
  <section class="panel" id="panel-2">
    <h2>视图三：Windows 执行 `ssh elena` 时的 ED25519 挑战-应答握手时序</h2>
    <table class="matrix">
      <thead>
        <tr>
          <th>时序步号</th>
          <th>交互方向</th>
          <th>底层物理动作</th>
          <th>安全机制与验证点</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><b>Step 1</b></td>
          <td>Windows 终端 $\rightarrow$ 本地 <code>~/.ssh/config</code></td>
          <td>解析 <code>Host elena</code>，定位私钥文件 <code>IdentityFile ~/.ssh/id_ed25519_codeup</code></td>
          <td>解决非默认私钥文件名（带 <code>_codeup</code> 后缀）自动寻址问题</td>
        </tr>
        <tr>
          <td><b>Step 2</b></td>
          <td>Windows $\rightarrow$ 阿里云 <code>8.163.29.42:22</code></td>
          <td>发送公钥声明：请求登录用户 <code>elena</code>，算法 <code>ssh-ed25519</code>，公钥指纹 <code>SHA256:OFeU8L1Blc...</code></td>
          <td>仅发送公钥标识，私钥本身不经过网络</td>
        </tr>
        <tr>
          <td><b>Step 3</b></td>
          <td>阿里云 <code>sshd</code> $\rightarrow$ Windows</td>
          <td>在 <code>/home/elena/.ssh/authorized_keys</code> 查到匹配公钥，生成一次性随机质询码 <code>Nonce</code></td>
          <td>每次连接的 <code>Nonce</code> 完全随机，杜绝抓包重放攻击</td>
        </tr>
        <tr>
          <td><b>Step 4</b></td>
          <td>Windows $\rightarrow$ 阿里云 <code>sshd</code></td>
          <td>使用本地私钥 <code>id_ed25519_codeup</code> 对 <code>(SessionID + Nonce)</code> 签名并传回签名结果</td>
          <td><b>私钥全程 0 字节离开 Windows 电脑</b></td>
        </tr>
        <tr>
          <td><b>Step 5</b></td>
          <td>阿里云 <code>sshd</code> $\rightarrow$ <code>/var/log/auth.log</code></td>
          <td>用公钥验签成功，记入 <code>Accepted publickey for elena from 183.238.79.28 port 2846 ssh2: ED25519 SHA256:OFeU8L1Blc...</code></td>
          <td>免密进入 <code>elena@8.163.29.42</code> 会话</td>
        </tr>
      </tbody>
    </table>
  </section>

  <!-- TAB 3: TROUBLESHOOTING DECISION TREE -->
  <section class="panel" id="panel-3">
    <h2>视图四：Windows 视角 `Permission denied (publickey)` 4 步排障决策树</h2>
    <div class="bipartite-wrap">
      <div class="box-card">
        <h4>分支 1：在 Windows Git Bash 直接 git clone 报 Permission denied</h4>
        <p style="font-size: 13px; color: var(--text-sub); margin-top: 4px;">
          原因：私钥文件名叫 <code>id_ed25519_codeup</code>（非默认 <code>id_ed25519</code>），未写入 <code>~/.ssh/config</code> 时 Git 找不到这把钥匙。
        </p>
        <pre class="code">Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_codeup
    IdentitiesOnly yes

Host elena
    HostName 8.163.29.42
    User elena
    IdentityFile ~/.ssh/id_ed25519_codeup
    IdentitiesOnly yes</pre>
      </div>
      <div class="box-card">
        <h4>分支 2：登入 ssh elena 后在阿里云里敲 git clone 报 Permission denied</h4>
        <p style="font-size: 13px; color: var(--text-sub); margin-top: 4px;">
          原因：在服务器里连 GitHub 时，掏的是服务器自己的钥匙 <code>elena@8.163.29.42</code> (<code>SHA256:1/zjU68N...</code>)。将该公钥加入 GitHub <code>settings/keys</code> 即刻解决。
        </p>
        <pre class="code">ssh -T git@github.com
# 输出: Hi yueyiqi! You've successfully authenticated...</pre>
      </div>
      <div class="box-card">
        <h4>分支 3：Windows 提示 UNPROTECTED PRIVATE KEY FILE</h4>
        <p style="font-size: 13px; color: var(--text-sub); margin-top: 4px;">
          原因：Windows 私钥文件权限过宽，OpenSSH 强制要求仅当前用户可读。
        </p>
        <pre class="code">icacls "$env:USERPROFILE\.ssh\id_ed25519_codeup" /inheritance:r
icacls "$env:USERPROFILE\.ssh\id_ed25519_codeup" /grant:r "$($env:USERNAME):(R)"</pre>
      </div>
      <div class="box-card">
        <h4>分支 4：粘贴公钥时漏掉首字母 s (变成 sh-ed25519)</h4>
        <p style="font-size: 13px; color: var(--text-sub); margin-top: 4px;">
          原因：首部不是合法的 <code>ssh-ed25519</code>。在服务端执行 <code>ssh-keygen -lf ~/.ssh/authorized_keys</code> 即可校验是否合法。
        </p>
        <pre class="code">ssh-keygen -lf /home/elena/.ssh/authorized_keys</pre>
      </div>
    </div>
  </section>

  <!-- TAB 4: 5 PARADIGMS MATRIX -->
  <section class="panel" id="panel-4">
    <h2>视图五：为什么除 UML 泳道图外，推荐这 5 种可视化方式组合使用？</h2>
    <table class="matrix">
      <thead>
        <tr>
          <th>可视化方式</th>
          <th>从 Windows 视角解决的核心问题</th>
          <th>最佳使用场景</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><b>1. UML 四泳道互动流程图 (Swimlane)</b></td>
          <td>按「Win 终端 / Win VS Code / 阿里云 / GitHub」展示端到端操作顺序</td>
          <td>日常开发与发布标准操作流程 (SOP)</td>
        </tr>
        <tr>
          <td><b>2. 『2把钥匙 vs 2道锁芯』二分拓扑图 (Bipartite)</b></td>
          <td>左列画私钥（出站）、右列画门禁（入站），一眼分清 Windows 钥匙与阿里云钥匙</td>
          <td>破除「为什么公钥放进了服务器，服务器却不能连 GitHub」的方向误区</td>
        </tr>
        <tr>
          <td><b>3. UML 挑战-应答握手时序图 (Sequence)</b></td>
          <td>展示毫秒级 Nonce 签名验证过程，证明私钥永远不离开 Windows 本机</td>
          <td>理解免密登录安全原理与 <code>/var/log/auth.log</code> 审计日志</td>
        </tr>
        <tr>
          <td><b>4. Permission Denied 排障决策树 (Decision Tree)</b></td>
          <td>按报错位置与现象提供 4 步分支自检</td>
          <td>遇到连不上时 30 秒自助排错</td>
        </tr>
        <tr>
          <td><b>5. 三模态交互式 HTML 沙盒 + 原生 PPTX</b></td>
          <td>支持点击步骤查看命令与日志、切换护眼主题，并提供可编辑 PPT 汇报稿</td>
          <td>团队培训、交互式演示与文档归档</td>
        </tr>
      </tbody>
    </table>
  </section>
</div>

<script>
var STEP_DATA = {
  1: "【步骤 1 · Windows 本地密钥准备】\\n私钥路径: C:\\Users\\Lenovo\\.ssh\\id_ed25519_codeup (绝不外传)\\n公钥内容: ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFESj+nOVBhNImRjKod9BM+72uvv3Xf57mD+o9Ywnkkr cl-715-codeup\\n公钥指纹: 256 SHA256:OFeU8L1Blc+ECOmWayawRMLIYace0UuxIVM+ojmTNiw cl-715-codeup (ED25519)",
  2: "【步骤 2 · Windows 配置 ~/.ssh/config】\\nHost elena\\n    HostName 8.163.29.42\\n    User elena\\n    IdentityFile ~/.ssh/id_ed25519_codeup\\n    IdentitiesOnly yes\\n\\nHost github.com\\n    HostName github.com\\n    User git\\n    IdentityFile ~/.ssh/id_ed25519_codeup\\n    IdentitiesOnly yes",
  3: "【步骤 3 · Windows PowerShell 发起免密登录】\\n执行命令: ssh elena\\n底层动作: Windows 自动使用 id_ed25519_codeup 私钥对阿里云 sshd 发来的随机 Nonce 进行签名应答。",
  4: "【步骤 4 · 阿里云 8.163.29.42 验签放行并记入 /var/log/auth.log】\\n2026-10-24T12:40:24.743071+08:00 elena sshd-session[52849]: Accepted publickey for elena from 183.238.79.28 port 2846 ssh2: ED25519 SHA256:OFeU8L1Blc+ECOmWayawRMLIYace0UuxIVM+ojmTNiw",
  5: "【步骤 5 · Windows Git Bash (MINGW64) 克隆代码】\\n执行命令: git clone git@github.com:yueyiqi/kaoyan.git /d/kaoyanEnglish\\n输出: Receiving objects: 100% (17/17), 63.32 KiB, done.",
  6: "【步骤 6 · Windows VS Code 修改代码并一键上线】\\ncd /d/kaoyanEnglish\\ngit add -A && git commit -m \"feat: 优化前端页面\"\\ngit push origin main   # 1) 同步备份至 GitHub\\ngit push elena main    # 2) 直推阿里云并触发自动重启 (或执行 ssh elena deploy-kaoyan)",
  7: "【步骤 7 · 阿里云自动同步重启并探活】\\n触发钩子: /home/elena/kaoyan_english_hub/.git/hooks/post-receive (或 /usr/local/bin/deploy-kaoyan)\\n自动执行: sudo systemctl restart kaoyan-english-hub && curl -fsS http://127.0.0.1:60231/api/health -> HTTP 200 OK",
  8: "【步骤 8 · GitHub 门禁双端公钥放行】\\n1) Windows 公钥: cl-715-codeup (SHA256:OFeU8L1Blc...) -> 放行 Windows git clone / push\\n2) 阿里云公钥: elena@8.163.29.42 (SHA256:1/zjU68N...) -> 放行阿里云 git fetch / pull"
};
function inspectStep(id) {
  var el = document.getElementById('step-inspector');
  el.textContent = STEP_DATA[id] || '';
}
function switchTab(idx) {
  var btns = document.querySelectorAll('.tab-btn');
  var panels = document.querySelectorAll('.panel');
  for (var i = 0; i < btns.length; i++) {
    btns[i].classList.toggle('active', i === idx);
    panels[i].classList.toggle('active', i === idx);
  }
}
function setTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  try { localStorage.setItem('kaoyan_win_ssh_theme', theme); } catch (e) {}
}
</script>
</body>
</html>"""


def main() -> int:
    # 1. Write Markdown Spec
    MD_P.write_text(build_markdown(), encoding="utf-8")

    # 2. Build 2x2 Bento SVG & PNG
    grid = BentoGrid2x2(page_title=TITLE_CN, page_subtitle=TITLE_EN)
    grid.add_cards(CARDS)
    grid.render_to_file(SVG_P)

    # 3. Build Dedicated Swimlane + Key-Lock Topology SVG & PNG
    SWIMLANE_SVG_P.write_text(build_dedicated_swimlane_svg(), encoding="utf-8")

    rsvg = "/opt/homebrew/bin/rsvg-convert"
    if os.path.exists(rsvg):
        subprocess.run(
            [rsvg, "-w", "1600", "--background-color", "#F8FAFC", str(SVG_P), "-o", str(PNG_P)],
            check=True,
        )
        subprocess.run(
            [rsvg, "-w", "1600", "--background-color", "#F8FAFC", str(SWIMLANE_SVG_P), "-o", str(SWIMLANE_PNG_P)],
            check=True,
        )

    # 4. Build 6-Slide Native Editable MSU PPTX + Previews + Interactive HTML
    compiler = AdaptivePresentationCompiler(PPTX_MANIFEST)
    compiler.compile_pptx(PPTX_P)
    preview_engine.compile_pptx_to_interactive_html(PPTX_P, HTML_P)
    # Write the rich 5-tab interactive HTML workbench
    HTML_P.write_text(build_interactive_html(), encoding="utf-8")

    chk = preview_engine.run_self_check(PPTX_P, [MD_P])
    if not chk["self_consistent"]:
        raise RuntimeError(f"Preview self-check failed: {chk}")

    print("[SUCCESS] All pure Windows-perspective deliverables generated:")
    for p in [MD_P, SVG_P, PNG_P, SWIMLANE_SVG_P, SWIMLANE_PNG_P, PPTX_P, HTML_P]:
        print(f"  - {p.name} ({p.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
