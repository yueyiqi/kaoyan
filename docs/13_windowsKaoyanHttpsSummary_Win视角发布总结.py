#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
13_windowsKaoyanHttpsSummary_Win视角发布总结.py
====================================================================================================
Pure Windows-Perspective End-to-End Kaoyan HTTPS Site Publishing Master Summary Compiler:
Synthesizes the entire Windows -> GitHub -> Alibaba Cloud (elena 8.163.29.42) -> Hong Kong Edge (43.160.227.166)
-> Let's Encrypt HTTPS Site Publishing workflow into 4 synchronized deliverables:
  1. Markdown Master Summary (.md) with Mermaid End-to-End Architecture, Publish Swimlane & HTTPS Routing
  2. Bento 2x2 Master Summary Infographic (.svg + .png) via svg_bento_layout_engine
  3. Dedicated Windows-to-HTTPS Full-Chain Architecture Diagram (.svg + .png)
  4. 6-Slide 100% Native Editable MSU PPTX (.pptx + _slides_preview.png/.md) via AdaptivePresentationCompiler
  5. Interactive Tri-Modal (Daylight/Midnight/Eyecare) HTML Master Console (.html) with 5 Interactive Tabs
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
STEM = "13_windowsKaoyanHttpsSummary_Win视角发布总结"
MD_P = BASE / f"{STEM}.md"
SVG_P = BASE / f"{STEM}.svg"
PNG_P = BASE / f"{STEM}.png"
PPTX_P = BASE / f"{STEM}.pptx"
HTML_P = BASE / f"{STEM}.html"

ARCH_SVG_P = BASE / "13_windowsHttpsPublishArch_Win发布架构图.svg"
ARCH_PNG_P = BASE / "13_windowsHttpsPublishArch_Win发布架构图.png"

TITLE_CN = "Windows 视角发布考研英语 HTTPS 站点全链路总结大典"
TITLE_EN = "Windows-to-HTTPS Kaoyan English Site Publishing Master Summary: SSH Keyring, VS Code Git Push, Non-Root Runtime & Dual-Path TLS"

CARDS = [
    CardSpec(
        title="一、Windows 本地研发与双门禁免密基座",
        subtitle="Win11 PowerShell / Git Bash / VS Code + 2 Keys vs. 2 Locks",
        badge="阶段 1 · 免密基座",
        accent="#2563eb",
        metrics=MetricPair(
            left_label="本地工作区与密钥",
            left_value="D:\\kaoyanEnglish (VS Code)",
            right_label="双向免密覆盖率",
            right_value="100% 双向免密 (2钥×2锁)",
        ),
        items=[
            ("钥匙#1 (Windows私钥): ", "C:\\Users\\Lenovo\\.ssh\\id_ed25519_codeup (OFeU8L1B...)，经 icacls 收敛只读权限"),
            ("Windows ~/.ssh/config: ", "统一绑定 Host elena (8.163.29.42) 与 Host github.com 自动挂载钥匙#1"),
            ("钥匙#2 (阿里云私钥): ", "elena:/home/elena/.ssh/id_ed25519 (1/zjU68N...) 已加入 GitHub SSH Keys"),
            ("安全收益: ", "彻底告别密码输入与 Permission denied，打通本地改码到云端拉取的认证闭环"),
        ],
    ),
    CardSpec(
        title="二、VS Code 改码与双通道秒级自动发布",
        subtitle="GitHub Pull Channel (deploy-kaoyan) & Direct Git Hook Channel",
        badge="阶段 2 · 代码发布",
        accent="#059669",
        metrics=MetricPair(
            left_label="标准发布命令",
            left_value="git push + deploy-kaoyan",
            right_label="端到端生效耗时",
            right_value="<= 3.0 秒 (含自动重启与健康探针)",
        ),
        items=[
            ("通道A (GitHub协同流): ", "VS Code 推送 origin main 后，执行 ssh elena \"deploy-kaoyan\" 一键拉取上线"),
            ("通道B (Git直推钩子流): ", "git push elena main 触发服务端 .git/hooks/post-receive 自动同步并重启"),
            ("前后端双目录自动对齐: ", "脚本自动双向同步 frontend/index.html <-> index.html 与 backend/ 服务脚本"),
            ("数据安全防误删保护: ", ".git/info/exclude 锁定 SQLite 热库与备份目录，代码重置绝不丢失用户学习数据"),
        ],
    ),
    CardSpec(
        title="三、阿里云 elena 非 Root 生产运行时底座",
        subtitle="User=elena (uid=1000) Systemd Service + 8-Table SQLite WAL",
        badge="阶段 3 · 生产宿主",
        accent="#7c3aed",
        metrics=MetricPair(
            left_label="后端监听与权限",
            left_value="127.0.0.1:60231 (User=elena)",
            right_label="SQLite WAL 核心表",
            right_value="8 张表 + 40GB 冷热防爆分层",
        ),
        items=[
            ("非Root最小权限原则: ", "kaoyan-english-hub.service 由普通账号 elena 运行，禁止 root 密码 SSH 登录"),
            ("8表持久化存储引擎: ", "涵盖真题篇章、5500考纲词、精读批注、生词本、作文语料、阅读进度锚点等 8 表"),
            ("40GB磁盘防爆治理: ", "热库 (<=4GB) + 温快照 (<=2GB, 7天) + 每日 03:30 自动压缩归档，磁盘仅占 8%"),
            ("本机双协议网关接入: ", "elena Caddy 监听 :443 (nip.io 极速直连) 与 :80/:3389 (供香港边缘免备案回源)"),
        ],
    ),
    CardSpec(
        title="四、HTTPS 证书架构与四大公网访问入口",
        subtitle="Direct TLS-ALPN-01 (nip.io) + HK Edge SNI/ICP Bypass Proxy",
        badge="阶段 4 · HTTPS 上线",
        accent="#ea580c",
        metrics=MetricPair(
            left_label="已签发受信任证书入口",
            left_value="3 条立即秒开 + 1 条待实名解封",
            right_label="最快 HTTPS 首包响应",
            right_value="0.145s (kaoyan.8.163.29.42.nip.io)",
        ),
        items=[
            ("直连极速入口 (首选): ", "https://kaoyan.8.163.29.42.nip.io (Let's Encrypt TLS-ALPN-01 证书，0.145s)"),
            ("香港边缘同构入口: ", "https://kaoyan.43.160.227.166.nip.io 与 https://kaoyan.liuzengyu.top (HTTP 200)"),
            ("为什么自定义域名走香港: ", "绕开境内机房对未 ICP 备案域名的 80 端口 403 与 443 端口 SNI RST 阻断"),
            ("kaoyan.elenalyl.top 收口: ", "阿里云域名控制台【快速过户】勾选已实名模板 25324778 解除 clientHold 即刻自动签发"),
        ],
    ),
]


def build_dedicated_arch_svg() -> str:
    """Builds a high-clarity, pure Windows-perspective end-to-end HTTPS publishing architecture SVG."""
    return r"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100%" viewBox="0 0 1600 1060" preserveAspectRatio="xMidYMid meet" style="background:#f8fafc;font-family:'PingFang SC','Microsoft YaHei','Helvetica Neue',Arial,sans-serif;">
  <defs>
    <linearGradient id="hdrGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="55%" stop-color="#1e3a8a"/>
      <stop offset="100%" stop-color="#047857"/>
    </linearGradient>
    <filter id="cardShadow" x="-2%" y="-2%" width="104%" height="106%">
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#0f172a" flood-opacity="0.08"/>
    </filter>
    <marker id="arrBlue" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1 L 9 5 L 0 9 z" fill="#2563eb"/>
    </marker>
    <marker id="arrGreen" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1 L 9 5 L 0 9 z" fill="#059669"/>
    </marker>
    <marker id="arrPurple" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1 L 9 5 L 0 9 z" fill="#7c3aed"/>
    </marker>
    <marker id="arrOrange" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1 L 9 5 L 0 9 z" fill="#ea580c"/>
    </marker>
  </defs>

  <!-- Title Banner -->
  <rect x="24" y="20" width="1552" height="92" rx="16" fill="url(#hdrGrad)" filter="url(#cardShadow)"/>
  <text x="52" y="58" fill="#ffffff" font-size="25" font-weight="800">Windows 视角发布考研英语 HTTPS 站点全链路架构总览图 (End-to-End Publishing &amp; HTTPS Topology)</text>
  <text x="52" y="88" fill="#cbd5e1" font-size="14" font-weight="500">从 Windows 本地 VS Code 改码、GitHub 双向免密同步、阿里云 elena 非 Root 部署，到 Let's Encrypt 双通道 HTTPS 证书签发与公网访问</text>
  <rect x="1310" y="38" width="242" height="44" rx="22" fill="#10b981"/>
  <text x="1431" y="66" text-anchor="middle" fill="#ffffff" font-size="14" font-weight="800">纯 Windows 视角 · 4 阶全闭环</text>

  <!-- ==================== UPPER HALF: 4-STAGE PUBLISHING PIPELINE ==================== -->
  <rect x="24" y="128" width="1552" height="470" rx="14" fill="#ffffff" stroke="#cbd5e1" stroke-width="1.5" filter="url(#cardShadow)"/>
  <text x="48" y="160" fill="#0f172a" font-size="18" font-weight="800">第一部分：Windows 研发到线上 HTTPS 生产站点的 4 大核心工位 (4-Stage End-to-End Pipeline)</text>

  <!-- Stage 1: Windows Workstation -->
  <rect x="44" y="180" width="350" height="398" rx="12" fill="#eff6ff" stroke="#3b82f6" stroke-width="2"/>
  <rect x="44" y="180" width="350" height="54" rx="12" fill="#2563eb"/>
  <text x="219" y="205" text-anchor="middle" fill="#ffffff" font-size="16" font-weight="800">工位 1：Windows 研发本机</text>
  <text x="219" y="224" text-anchor="middle" fill="#dbeafe" font-size="11">Lenovo@LAPTOP-8M5JKBS4 (Win11)</text>

  <rect x="60" y="248" width="318" height="74" rx="8" fill="#ffffff" stroke="#93c5fd" stroke-width="1.5"/>
  <text x="74" y="270" fill="#1e3a8a" font-size="13" font-weight="800">1. 本地私钥 #1 与 ~/.ssh/config</text>
  <text x="74" y="290" fill="#334155" font-size="11">• 私钥: C:\Users\Lenovo\.ssh\id_ed25519_codeup</text>
  <text x="74" y="308" fill="#2563eb" font-size="11" font-weight="700">• 别名: Host elena (8.163.29.42) &amp; Host github.com</text>

  <rect x="60" y="334" width="318" height="74" rx="8" fill="#ffffff" stroke="#93c5fd" stroke-width="1.5"/>
  <text x="74" y="356" fill="#1e3a8a" font-size="13" font-weight="800">2. VS Code 本地代码工作区</text>
  <text x="74" y="376" fill="#334155" font-size="11">• 路径: D:\kaoyanEnglish (Git Bash MINGW64)</text>
  <text x="74" y="394" fill="#334155" font-size="11">• 改码: frontend/index.html &amp; kaoyan_hub_server.py</text>

  <rect x="60" y="420" width="318" height="68" rx="8" fill="#dbeafe" stroke="#2563eb" stroke-width="1.5"/>
  <text x="74" y="442" fill="#1e40af" font-size="13" font-weight="800">3. Windows 终端一键发布指令</text>
  <text x="74" y="461" fill="#1e3a8a" font-size="11" font-weight="700">① git add -A &amp;&amp; git commit -m "..." &amp;&amp; git push</text>
  <text x="74" y="478" fill="#1e3a8a" font-size="11" font-weight="700">② ssh elena "deploy-kaoyan" (或 git push elena main)</text>

  <rect x="60" y="500" width="318" height="62" rx="8" fill="#f0fdf4" stroke="#10b981" stroke-width="1.5"/>
  <text x="74" y="522" fill="#065f46" font-size="13" font-weight="800">4. Windows 浏览器 HTTPS 验收</text>
  <text x="74" y="542" fill="#047857" font-size="11" font-weight="700">• Edge/Chrome 打开 https://kaoyan.8.163.29.42.nip.io</text>
  <text x="74" y="556" fill="#334155" font-size="10">• 验证绿色安全锁 (Let's Encrypt) 与最新页面改动</text>

  <!-- Stage 2: GitHub Remote -->
  <rect x="434" y="180" width="340" height="398" rx="12" fill="#f5f3ff" stroke="#8b5cf6" stroke-width="2"/>
  <rect x="434" y="180" width="340" height="54" rx="12" fill="#7c3aed"/>
  <text x="604" y="205" text-anchor="middle" fill="#ffffff" font-size="16" font-weight="800">工位 2：GitHub 远端代码库</text>
  <text x="604" y="224" text-anchor="middle" fill="#ede9fe" font-size="11">git@github.com:yueyiqi/kaoyan.git (main)</text>

  <rect x="450" y="248" width="308" height="96" rx="8" fill="#ffffff" stroke="#c4b5fd" stroke-width="1.5"/>
  <text x="464" y="270" fill="#5b21b6" font-size="13" font-weight="800">门禁锁芯 B：github.com/settings/keys</text>
  <text x="464" y="292" fill="#334155" font-size="11">• 公钥 #1 (Windows cl-715-codeup):</text>
  <text x="474" y="308" fill="#2563eb" font-size="10.5" font-weight="700">指纹: SHA256:OFeU8L1Blc+ECOmWayaw... (ED25519)</text>
  <text x="464" y="324" fill="#334155" font-size="11">• 公钥 #2 (阿里云 elena@8.163.29.42):</text>
  <text x="474" y="338" fill="#7c3aed" font-size="10.5" font-weight="700">指纹: SHA256:1/zjU68Npra3hsJq6zhX8... (ED25519)</text>

  <rect x="450" y="358" width="308" height="98" rx="8" fill="#ffffff" stroke="#c4b5fd" stroke-width="1.5"/>
  <text x="464" y="380" fill="#5b21b6" font-size="13" font-weight="800">代码单点真源 (Single Source of Truth)</text>
  <text x="464" y="400" fill="#334155" font-size="11">• 接收来自 Windows VS Code 的 git push origin main</text>
  <text x="464" y="418" fill="#334155" font-size="11">• 响应来自阿里云 elena 的 git fetch origin main</text>
  <text x="464" y="436" fill="#059669" font-size="11" font-weight="700">• 实测 ssh -T git@github.com 返回 Hi yueyiqi!</text>

  <rect x="450" y="470" width="308" height="92" rx="8" fill="#ede9fe" stroke="#7c3aed" stroke-width="1.5"/>
  <text x="464" y="492" fill="#4c1d95" font-size="13" font-weight="800">核心防混淆原则 (Key vs. Lock Axiom)</text>
  <text x="464" y="512" fill="#334155" font-size="11">• Windows 推代码用【钥匙#1】开 GitHub 门禁</text>
  <text x="464" y="530" fill="#334155" font-size="11">• 阿里云拉代码用【钥匙#2】开 GitHub 门禁</text>
  <text x="464" y="548" fill="#5b21b6" font-size="11" font-weight="700">• 两把公钥同登 GitHub，彻底终结 Permission denied</text>

  <!-- Stage 3: Alibaba Cloud Elena -->
  <rect x="814" y="180" width="360" height="398" rx="12" fill="#ecfdf5" stroke="#10b981" stroke-width="2"/>
  <rect x="814" y="180" width="360" height="54" rx="12" fill="#059669"/>
  <text x="994" y="205" text-anchor="middle" fill="#ffffff" font-size="16" font-weight="800">工位 3：阿里云生产宿主 elena</text>
  <text x="994" y="224" text-anchor="middle" fill="#d1fae5" font-size="11">elena@8.163.29.42 (广州 ECS · Ubuntu 26.04)</text>

  <rect x="830" y="248" width="328" height="74" rx="8" fill="#ffffff" stroke="#6ee7b7" stroke-width="1.5"/>
  <text x="844" y="270" fill="#065f46" font-size="13" font-weight="800">1. 门禁锁芯 A 与自动发布引擎</text>
  <text x="844" y="290" fill="#334155" font-size="11">• 门禁: /home/elena/.ssh/authorized_keys (放行钥匙#1)</text>
  <text x="844" y="308" fill="#047857" font-size="11" font-weight="700">• 引擎: /usr/local/bin/deploy-kaoyan &amp; post-receive</text>

  <rect x="830" y="334" width="328" height="82" rx="8" fill="#ffffff" stroke="#6ee7b7" stroke-width="1.5"/>
  <text x="844" y="356" fill="#065f46" font-size="13" font-weight="800">2. 非 Root 业务服务与 8 表 SQLite WAL</text>
  <text x="844" y="376" fill="#334155" font-size="11">• 服务: kaoyan-english-hub.service (User=elena, :60231)</text>
  <text x="844" y="394" fill="#334155" font-size="11">• 热库: /home/elena/kaoyan_storage/hot_db/*.sqlite3</text>
  <text x="844" y="410" fill="#059669" font-size="10" font-weight="700">• 8 张核心表在线，40GB 磁盘冷热分层 (占用仅 8%)</text>

  <rect x="830" y="428" width="328" height="134" rx="8" fill="#d1fae5" stroke="#059669" stroke-width="1.5"/>
  <text x="844" y="450" fill="#065f46" font-size="13" font-weight="800">3. 本机 Caddy 双协议网关 (/etc/caddy/Caddyfile)</text>
  <text x="844" y="470" fill="#047857" font-size="11" font-weight="700">• 直连 HTTPS (:443): kaoyan.8.163.29.42.nip.io</text>
  <text x="854" y="488" fill="#334155" font-size="10">启用 TLS-ALPN-01 (disable_http_challenge) 自动签发真证书</text>
  <text x="844" y="508" fill="#047857" font-size="11" font-weight="700">• 边缘回源端口 (:3389 / :80):</text>
  <text x="854" y="526" fill="#334155" font-size="10">接收香港网关 Host: 127.0.0.1 回源流量 -> 反代 127.0.0.1:60231</text>
  <text x="854" y="544" fill="#065f46" font-size="10" font-weight="700">完美规避境内机房对未备案域名的 Host/SNI 拦截！</text>

  <!-- Stage 4: HK Edge Gateway & Public HTTPS -->
  <rect x="1214" y="180" width="342" height="398" rx="12" fill="#fff7ed" stroke="#f97316" stroke-width="2"/>
  <rect x="1214" y="180" width="342" height="54" rx="12" fill="#ea580c"/>
  <text x="1385" y="205" text-anchor="middle" fill="#ffffff" font-size="16" font-weight="800">工位 4：香港免备案边缘与 HTTPS 入口</text>
  <text x="1385" y="224" text-anchor="middle" fill="#ffedd5" font-size="11">43.160.227.166 (:443 Let's Encrypt) + 四大域名</text>

  <rect x="1230" y="248" width="310" height="82" rx="8" fill="#ffffff" stroke="#fdba74" stroke-width="1.5"/>
  <text x="1244" y="270" fill="#9a3412" font-size="13" font-weight="800">为什么要配香港免备案边缘网关？</text>
  <text x="1244" y="290" fill="#334155" font-size="11">• 广州机房对未备案域名在 :80 返 403、在 :443 发 RST</text>
  <text x="1244" y="308" fill="#ea580c" font-size="11" font-weight="700">• 自定义域名 A 记录指香港 43.160.227.166 签发证书</text>
  <text x="1244" y="324" fill="#334155" font-size="10">• 香港网关以 Host:127.0.0.1 隐身回源 8.163.29.42:3389</text>

  <rect x="1230" y="342" width="310" height="134" rx="8" fill="#ffffff" stroke="#10b981" stroke-width="2"/>
  <text x="1244" y="364" fill="#065f46" font-size="13" font-weight="800">已开通受信任证书的 3 条生产 HTTPS 入口</text>
  <text x="1244" y="386" fill="#047857" font-size="11" font-weight="700">① https://kaoyan.8.163.29.42.nip.io (0.145s 直连首选)</text>
  <text x="1244" y="408" fill="#047857" font-size="11" font-weight="700">② https://kaoyan.43.160.227.166.nip.io (香港边缘)</text>
  <text x="1244" y="430" fill="#047857" font-size="11" font-weight="700">③ https://kaoyan.liuzengyu.top (生产正式域名)</text>
  <text x="1244" y="452" fill="#334155" font-size="10">• 实测全部 HTTP 200 OK · Let's Encrypt 证书校验通过</text>
  <text x="1244" y="468" fill="#334155" font-size="10">• P1(首页) + P2(API鉴权) + P3(无拦截) 100% 绿灯</text>

  <rect x="1230" y="488" width="310" height="74" rx="8" fill="#fef3c7" stroke="#f59e0b" stroke-width="1.5"/>
  <text x="1244" y="508" fill="#92400e" font-size="12" font-weight="800">④ https://kaoyan.elenalyl.top (待实名过户收口)</text>
  <text x="1244" y="526" fill="#78350f" font-size="10">• 服务端与香港 Caddy 已 100% 配妥 (A记录=43.160.227.166)</text>
  <text x="1244" y="544" fill="#b45309" font-size="10" font-weight="700">• 阿里云【快速过户】勾选已实名模板 25324778 即刻自动签发</text>

  <!-- Connectors between Stages -->
  <line x1="394" y1="448" x2="448" y2="410" stroke="#2563eb" stroke-width="2.5" marker-end="url(#arrBlue)"/>
  <rect x="394" y="402" width="44" height="18" rx="4" fill="#dbeafe"/>
  <text x="416" y="415" text-anchor="middle" fill="#1e40af" font-size="9.5" font-weight="800">git push</text>

  <line x1="774" y1="410" x2="828" y2="300" stroke="#7c3aed" stroke-width="2.5" marker-end="url(#arrPurple)"/>
  <rect x="774" y="330" width="44" height="18" rx="4" fill="#ede9fe"/>
  <text x="796" y="343" text-anchor="middle" fill="#5b21b6" font-size="9.5" font-weight="800">git fetch</text>

  <path d="M 219 578 L 219 592 L 994 592 L 994 578" fill="none" stroke="#059669" stroke-width="2.5" stroke-dasharray="6,4" marker-end="url(#arrGreen)"/>
  <rect x="410" y="581" width="388" height="20" rx="10" fill="#ecfdf5" stroke="#10b981" stroke-width="1"/>
  <text x="604" y="595" text-anchor="middle" fill="#065f46" font-size="10.5" font-weight="800">Windows 触发: ssh elena "deploy-kaoyan" (或 git push elena main)</text>

  <line x1="1214" y1="310" x2="1174" y2="510" stroke="#ea580c" stroke-width="2.5" marker-end="url(#arrOrange)"/>
  <rect x="1172" y="394" width="46" height="18" rx="4" fill="#ffedd5"/>
  <text x="1195" y="407" text-anchor="middle" fill="#9a3412" font-size="9.5" font-weight="800">回源:3389</text>

  <!-- ==================== LOWER HALF: WINDOWS PUBLISH SOP & HTTPS ROUTING COMPARISON ==================== -->
  <!-- Left Box: Windows 3-Step Daily Publishing SOP -->
  <rect x="24" y="614" width="764" height="422" rx="14" fill="#ffffff" stroke="#cbd5e1" stroke-width="1.5" filter="url(#cardShadow)"/>
  <text x="48" y="648" fill="#0f172a" font-size="18" font-weight="800">第二部分：Windows 日常改码发布 3 步标准作业程序 (Windows 3-Step SOP)</text>
  <text x="48" y="670" fill="#475569" font-size="12">在 Windows 电脑 D:\kaoyanEnglish 用 VS Code 修改代码后，只需在终端执行以下 3 步即可发布到 HTTPS 站点：</text>

  <rect x="48" y="688" width="716" height="96" rx="10" fill="#eff6ff" stroke="#60a5fa" stroke-width="1.5"/>
  <rect x="64" y="704" width="110" height="28" rx="14" fill="#2563eb"/>
  <text x="119" y="723" text-anchor="middle" fill="#ffffff" font-size="12" font-weight="800">Step 1 · 本地提交</text>
  <text x="188" y="723" fill="#1e3a8a" font-size="14" font-weight="800">在 VS Code 终端 / Git Bash 提交并推送到 GitHub</text>
  <text x="64" y="750" fill="#0f172a" font-size="11.2" font-family="monospace" font-weight="700">cd /d/kaoyanEnglish &amp;&amp; git add -A &amp;&amp; git commit -m "feat: update UI" &amp;&amp; git push origin main</text>
  <text x="64" y="772" fill="#475569" font-size="11">作用：利用 Windows 本地私钥 id_ed25519_codeup 免密将最新代码归档至 GitHub (yueyiqi/kaoyan.git)</text>

  <rect x="48" y="798" width="716" height="96" rx="10" fill="#ecfdf5" stroke="#34d399" stroke-width="1.5"/>
  <rect x="64" y="814" width="110" height="28" rx="14" fill="#059669"/>
  <text x="119" y="833" text-anchor="middle" fill="#ffffff" font-size="12" font-weight="800">Step 2 · 云端同步</text>
  <text x="188" y="833" fill="#065f46" font-size="14" font-weight="800">在 Windows PowerShell 触发阿里云一键拉取与重启</text>
  <text x="64" y="860" fill="#0f172a" font-size="12" font-family="monospace" font-weight="700">ssh elena "deploy-kaoyan"    # 或直接运行: git push elena main</text>
  <text x="64" y="882" fill="#475569" font-size="11">作用：阿里云自动拉取最新 main 分支、同步前后端入口、重启 kaoyan-english-hub 服务并校验 :60231/api/health</text>

  <rect x="48" y="908" width="716" height="106" rx="10" fill="#fff7ed" stroke="#fb923c" stroke-width="1.5"/>
  <rect x="64" y="924" width="110" height="28" rx="14" fill="#ea580c"/>
  <text x="119" y="943" text-anchor="middle" fill="#ffffff" font-size="12" font-weight="800">Step 3 · 线上验收</text>
  <text x="188" y="943" fill="#9a3412" font-size="14" font-weight="800">在 Windows 浏览器或终端探针验证 HTTPS 站点实时生效</text>
  <text x="64" y="970" fill="#0f172a" font-size="12" font-family="monospace" font-weight="700">curl.exe -I https://kaoyan.8.163.29.42.nip.io/api/health   # 浏览器 Ctrl+F5 强刷查看页面</text>
  <text x="64" y="994" fill="#047857" font-size="11" font-weight="700">预期返回：HTTP/1.1 200 OK · Let's Encrypt 证书有效 · 8 张 SQLite WAL 表完好无损！</text>

  <!-- Right Box: Dual HTTPS Routing & Domain Matrix -->
  <rect x="812" y="614" width="764" height="422" rx="14" fill="#ffffff" stroke="#cbd5e1" stroke-width="1.5" filter="url(#cardShadow)"/>
  <text x="836" y="648" fill="#0f172a" font-size="18" font-weight="800">第三部分：考研英语 HTTPS 站点双路由通道与域名状态矩阵 (HTTPS Domain Matrix)</text>
  <text x="836" y="670" fill="#475569" font-size="12">针对境内未备案云主机限制，实装「直连 nip.io 极速通道」与「香港免备案边缘回源通道」双轨并跑：</text>

  <!-- Route A Card -->
  <rect x="836" y="688" width="716" height="148" rx="10" fill="#f0fdf4" stroke="#10b981" stroke-width="1.5"/>
  <text x="856" y="714" fill="#065f46" font-size="14" font-weight="800">通道 1：广州阿里云直连极速 HTTPS 通道 (TLS-ALPN-01 · 免香港绕行 · 0.145s)</text>
  <text x="856" y="738" fill="#047857" font-size="13" font-weight="800">• 访问地址：https://kaoyan.8.163.29.42.nip.io   [状态：VERIFIED · 推荐日常首选]</text>
  <text x="856" y="762" fill="#334155" font-size="12">• 链路拓扑：Windows 浏览器 --(HTTPS :443)--&gt; 广州 elena (8.163.29.42 Caddy) --&gt; 127.0.0.1:60231</text>
  <text x="856" y="784" fill="#334155" font-size="12">• 技术原理：利用 nip.io 免备案公共泛解析 + Caddy disable_http_challenge (纯 443 TLS-ALPN-01 验证)，</text>
  <text x="856" y="804" fill="#334155" font-size="12">  直接由 8.163.29.42 本机签发 Let's Encrypt 受信任证书，延迟最低 (0.145s)、速度最快！</text>
  <text x="856" y="824" fill="#059669" font-size="11" font-weight="700">• 适用场景：学员与老师日常刷题、精读批注、查词入账、VS Code 改码后即时预览验证</text>

  <!-- Route B Card -->
  <rect x="836" y="852" width="716" height="162" rx="10" fill="#eff6ff" stroke="#3b82f6" stroke-width="1.5"/>
  <text x="856" y="878" fill="#1e40af" font-size="14" font-weight="800">通道 2：香港免备案边缘网关 HTTPS 回源通道 (绕开境内未备案域名 SNI/Host 拦截)</text>
  <text x="856" y="902" fill="#1e3a8a" font-size="12" font-weight="800">• 已上线入口 A：https://kaoyan.43.160.227.166.nip.io   [状态：VERIFIED · HTTP 200]</text>
  <text x="856" y="922" fill="#1e3a8a" font-size="12" font-weight="800">• 已上线入口 B：https://kaoyan.liuzengyu.top          [状态：VERIFIED · HTTP 200]</text>
  <text x="856" y="942" fill="#b45309" font-size="12" font-weight="800">• 专属自定义域名：https://kaoyan.elenalyl.top         [状态：服务端已就绪 · 待快速过户解封]</text>
  <text x="856" y="964" fill="#334155" font-size="12">• 链路拓扑：Windows 浏览器 --(HTTPS :443)--&gt; 香港网关 (43.160.227.166) --(Host:127.0.0.1)--&gt; elena:3389 --&gt; :60231</text>
  <text x="856" y="986" fill="#334155" font-size="11">• elenalyl.top 激活最后一步：在阿里云【域名控制台 -&gt; 快速过户】勾选已实名成功的模板 25324778 提交，</text>
  <text x="856" y="1004" fill="#1e40af" font-size="11" font-weight="700">  一旦注册局解除 clientHold，香港网关 Caddy 将全自动完成 Let's Encrypt 证书签发并点亮 https://kaoyan.elenalyl.top！</text>
</svg>
"""


def build_markdown() -> str:
    return r"""<!-- [IoC_Skill_Telemetry]
Status: VERIFIED
Evidence_IDs:
  - ev:ev-0023
  - ev:ev-0025
  - ev:ev-0027
  - ev:ev-0028
  - ev:ev-0032
  - ev:ev-0034
  - ev:ev-0035
Skills_Mounted:
  - adaptive-presentation-compiler
  - adaptive-html-response-pipeline
  - completion-evidence-protocol
-->

# Windows 视角发布考研英语 (`kaoyan`) HTTPS 站点全链路总结大典 (Windows-Perspective Kaoyan HTTPS Site Publishing Master Summary)

> **文档状态 (`Status`)**：`IMPLEMENTED & VERIFIED`（实测证据链：`ev:ev-0023`, `ev:ev-0025`, `ev:ev-0027`, `ev:ev-0028`, `ev:ev-0032`, `ev:ev-0034`, `ev:ev-0035`）
> **视角基准**：**100% 纯 Windows 研发与发布视角**（本机 `Lenovo@LAPTOP-8M5JKBS4` $\rightarrow$ `GitHub (yueyiqi/kaoyan.git)` $\rightarrow$ `阿里云广州生产服 elena@8.163.29.42` $\rightarrow$ `香港免备案边缘网关 43.160.227.166` $\rightarrow$ `公网受信任 HTTPS 站点`）

---

## 一、 全景执行摘要：从 Windows 本地改码到 HTTPS 站点上线的 4 大里程碑

![Windows 发布考研英语 HTTPS 站点全链路架构图](13_windowsHttpsPublishArch_Win发布架构图.png)

| 阶段里程碑 | 核心目标 | Windows 侧与云端关键配置落点 | 当前实测状态 (`[K]`) |
| :--- | :--- | :--- | :--- |
| **里程碑 1：双门禁免密认证基座** | 让 Windows 免密登录阿里云与 GitHub，且让阿里云也能免密从 GitHub 拉代码 | ① **Windows 私钥 #1** (`C:\Users\Lenovo\.ssh\id_ed25519_codeup`，指纹 `SHA256:OFeU8L1B...`) 同时登记至阿里云 `/home/elena/.ssh/authorized_keys` 与 GitHub SSH Keys；<br>② **阿里云私钥 #2** (`/home/elena/.ssh/id_ed25519`，指纹 `SHA256:1/zjU68N...`) 登记至 GitHub SSH Keys。 | ✅ **100% 实装打通** (`ev:ev-0025`, `ev:ev-0028`) |
| **里程碑 2：VS Code 改码与一键自动上线** | 在 Windows `D:\kaoyanEnglish` 用 VS Code 改完代码后，3 秒内自动同步上线并重启服务 | ① **通道 A（GitHub 标准流）**：`git push origin main` + `ssh elena "deploy-kaoyan"`；<br>② **通道 B（Git Hook 直推流）**：`git push elena main` 触发 `.git/hooks/post-receive`。 | ✅ **100% 实装打通** (`ev:ev-0027`, `ev:ev-0028`) |
| **里程碑 3：非 Root 安全运行时与 8 表数据库** | 严禁 `root` 裸跑业务；保障代码更新时不覆盖用户学习数据；防止 40GB 云盘爆满 | ① `kaoyan-english-hub.service` 以普通账号 `User=elena` (`uid=1000`) 运行于 `127.0.0.1:60231`；<br>② 8 表 SQLite WAL 热库独立存放于 `/home/elena/kaoyan_storage/hot_db/kaoyan_hub.sqlite3`，与 Git 目录解耦。 | ✅ **100% 在线运行** (`ev:ev-0015`, `ev:ev-0023`) |
| **里程碑 4：双轨 HTTPS 证书签发与公网发布** | 解决境内未备案云主机 `80` 端口 `403` 与 `443` 端口 `SNI RST` 阻断，提供受信任 HTTPS 访问 | ① **广州直连极速 HTTPS**：`https://kaoyan.8.163.29.42.nip.io`（`TLS-ALPN-01`，`0.145s`）；<br>② **香港免备案边缘回源 HTTPS**：`https://kaoyan.43.160.227.166.nip.io`、`https://kaoyan.liuzengyu.top` 及待实名过户收口的 `https://kaoyan.elenalyl.top`。 | ✅ **3 条 HTTPS 绿灯秒开**<br>⏳ **1 条待快速过户收口** (`ev:ev-0023`, `ev:ev-0024`) |

---

## 二、 阶段一：Windows 本地环境与「2 把钥匙 vs 2 道门禁」免密配置总结

### 2.1 为什么需要 2 把钥匙开 2 道门禁？

```mermaid
flowchart LR
    subgraph WIN["💻 Windows 研发本机 (Lenovo@LAPTOP-8M5JKBS4)"]
        K1["🔑 钥匙 #1：Windows 本地私钥<br/>C:\\Users\\Lenovo\\.ssh\\id_ed25519_codeup<br/>注释: cl-715-codeup<br/>指纹: SHA256:OFeU8L1Blc..."]
        CFG["⚙️ C:\\Users\\Lenovo\\.ssh\\config<br/>Host elena -> 8.163.29.42 (User elena)<br/>Host github.com -> git@github.com"]
        K1 --- CFG
    end

    subgraph ECS["☁️ 阿里云生产服务器 (elena@8.163.29.42)"]
        L1["🔒 门禁锁芯 A：阿里云 authorized_keys<br/>/home/elena/.ssh/authorized_keys<br/>已写入公钥 #1 (cl-715-codeup)"]
        K2["🔑 钥匙 #2：阿里云出站私钥<br/>/home/elena/.ssh/id_ed25519<br/>注释: elena@8.163.29.42<br/>指纹: SHA256:1/zjU68Npra..."]
    end

    subgraph GH["🐙 GitHub 远端代码库 (yueyiqi/kaoyan.git)"]
        L2["🔒 门禁锁芯 B：GitHub SSH Keys<br/>https://github.com/settings/keys<br/>同时登记【公钥 #1】与【公钥 #2】"]
    end

    K1 ==>|"① ssh elena 免密运维<br/>git push elena main"| L1
    K1 ==>|"② VS Code 本地克隆与推送<br/>git push origin main"| L2
    K2 ==>|"③ 阿里云 deploy-kaoyan 自动拉取<br/>git fetch origin main"| L2

    style WIN fill:#eff6ff,stroke:#2563eb,stroke-width:2px
    style ECS fill:#ecfdf5,stroke:#059669,stroke-width:2px
    style GH fill:#f5f3ff,stroke:#7c3aed,stroke-width:2px
```

### 2.2 Windows 端标准 `~/.ssh/config` 配置文件 (`C:\Users\Lenovo\.ssh\config`)

```sshconfig
# 1. GitHub 远端代码仓库免密配置 (供 VS Code / Git Bash 克隆与推送)
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_codeup
    IdentitiesOnly yes

# 2. 阿里云生产服务器 elena 普通管理账号免密配置 (自带免密 sudo，日常发布首选)
Host elena
    HostName 8.163.29.42
    User elena
    Port 22
    IdentityFile ~/.ssh/id_ed25519_codeup
    IdentitiesOnly yes
    ServerAliveInterval 30
    ServerAliveCountMax 3
```

---

## 三、 阶段二：Windows VS Code 代码修改与一键发布 HTTPS 站点标准流程 (SOP)

在 Windows 本地 `D:\kaoyanEnglish` 用 VS Code 完成前端界面（`frontend/index.html` 或根目录 `index.html`）或后端接口（`backend/kaoyan_hub_server.py` 或 `kaoyan_hub_server.py`）优化后，提供 **两条全自动上线通道**：

### 3.1 通道 A：GitHub 标准协同发布流（推荐日常使用）

```powershell
# 【第 1 步】在 VS Code 终端 / Git Bash (D:\kaoyanEnglish) 提交并推送到 GitHub：
cd /d/kaoyanEnglish
git add -A
git commit -m "feat: 优化考研英语阅读与词汇界面"
git push origin main

# 【第 2 步】在 Windows 终端远程触发阿里云一键拉取、同步并重启服务：
ssh elena "deploy-kaoyan"
```

**服务端 `/usr/local/bin/deploy-kaoyan` 自动完成的 4 件事**：
1. 从 `git@github.com:yueyiqi/kaoyan.git` 拉取最新 `main` 分支 (`git fetch origin main && git reset --hard origin/main`)；
2. 智能检测本次提交修改的是 `frontend/index.html` 还是根 `index.html`（以及 `backend/kaoyan_hub_server.py` 与根 `kaoyan_hub_server.py`），自动双向同步对齐；
3. 执行 `sudo systemctl restart kaoyan-english-hub` 重启后端服务；
4. 自动执行 `curl -fsS http://127.0.0.1:60231/api/health` 探活并打印 8 张数据库表健康状态。

### 3.2 通道 B：Git 远端钩子直推流（一步到位）

```bash
# 仅首次在 D:\kaoyanEnglish 绑定一次 elena 远端：
git remote add elena elena:/home/elena/kaoyan_english_hub

# 之后每次改完代码，直接一行命令推送到阿里云并自动重启生效：
git push elena main
```

---

## 四、 阶段三：HTTPS 证书签发架构与境内未备案拦截穿透总结

### 4.1 为什么自定义域名不能直接解析到广州 `8.163.29.42`？

```mermaid
flowchart TB
    WIN_B["🌐 Windows 浏览器 (Edge / Chrome)<br/>访问考研英语 HTTPS 站点"]

    subgraph DIRECT["⚡ 通道 1：广州直连极速 HTTPS 通道 (0.145s)"]
        NIP_ELENA["https://kaoyan.8.163.29.42.nip.io<br/>(免备案公共泛解析域名)"]
        CADDY_ELENA_443["阿里云广州 elena (8.163.29.42:443)<br/>Caddy TLS-ALPN-01 (disable_http_challenge)<br/>Let's Encrypt 真实受信任证书"]
    end

    subgraph EDGE["🛡️ 通道 2：香港免备案边缘回源 HTTPS 通道 (自定义域名必选)"]
        DOMAINS["• https://kaoyan.elenalyl.top (专属域名)<br/>• https://kaoyan.liuzengyu.top (已上线)<br/>• https://kaoyan.43.160.227.166.nip.io (已上线)"]
        HK_CADDY["香港免备案边缘网关 (43.160.227.166:443)<br/>Caddy 自动签发 Let's Encrypt 证书并终止 TLS"]
        CADDY_ELENA_3389["阿里云广州 elena (8.163.29.42:3389)<br/>Caddy 明文回源入口 (接收 Host: 127.0.0.1)"]
    end

    APP["🚀 考研英语生产后端服务 (kaoyan-english-hub.service)<br/>User=elena · 127.0.0.1:60231 · SQLite WAL 8 表热库"]

    WIN_B ==>|"首选极速直连 (0.145s)"| NIP_ELENA
    NIP_ELENA ==> CADDY_ELENA_443
    CADDY_ELENA_443 ==> APP

    WIN_B ==>|"自定义域名访问"| DOMAINS
    DOMAINS ==>|"DNS A记录 -> 43.160.227.166"| HK_CADDY
    HK_CADDY ==>|"reverse_proxy 8.163.29.42:3389<br/>header_up Host 127.0.0.1 (绕开未备案拦截)"| CADDY_ELENA_3389
    CADDY_ELENA_3389 ==> APP

    style DIRECT fill:#ecfdf5,stroke:#059669,stroke-width:2px
    style EDGE fill:#eff6ff,stroke:#2563eb,stroke-width:2px
    style APP fill:#fef3c7,stroke:#d97706,stroke-width:2px
```

- **物理事实 (`[K]`)**：阿里云广州机房 (`8.163.29.42`) 网关对未完成境内 ICP 备案的自定义域名（如 `kaoyan.elenalyl.top`、`*.duckdns.org`），在 `:80` 端口按 `HTTP Host` 拦截返回 `403`，在 `:443` 端口按 TLS `SNI` 注入 `TCP RST` 阻断连接。
- **架构解法**：
  1. **直连极速通道 (`https://kaoyan.8.163.29.42.nip.io`)**：利用 `nip.io` 公共泛解析，在广州 `8.163.29.42` 本机 Caddy 开启 `disable_http_challenge`（仅走 `:443` `TLS-ALPN-01` 验证），成功签发 Let's Encrypt 证书，实现 **0.145 秒直连秒开**。
  2. **自定义域名香港免备案边缘回源通道 (`https://kaoyan.elenalyl.top` / `https://kaoyan.liuzengyu.top`)**：将自定义域名的 DNS `A` 记录指向香港免备案边缘网关 `43.160.227.166`，由香港网关完成 Let's Encrypt 证书签发与 HTTPS 握手，再将内部回源请求头改写为 `Host: 127.0.0.1` 转发至广州 `8.163.29.42:3389`，100% 穿透未备案拦截。

---

## 五、 四大 HTTPS 站点入口状态与 Windows 端验收速查表

![Bento 2x2 总结全览图](13_windowsKaoyanHttpsSummary_Win视角发布总结.png)

| 序号 | HTTPS 站点入口地址 | 证书与路由机制 | 响应状态与耗时 | 当前状态与操作建议 |
| :---: | :--- | :--- | :---: | :--- |
| **1** | **`https://kaoyan.8.163.29.42.nip.io`** | 广州 `8.163.29.42:443` 直连 (`TLS-ALPN-01` Let's Encrypt) | **`HTTP 200` (`0.145s`)** | ✅ **全网直连可用（推荐 Windows 日常首选）** |
| **2** | **`https://kaoyan.43.160.227.166.nip.io`** | 香港 `43.160.227.166:443` $\rightarrow$ 广州 `8.163.29.42:3389` | **`HTTP 200` (`SSL=0`)** | ✅ **全网可用（与 `kaoyan.elenalyl.top` 完全同构）** |
| **3** | **`https://kaoyan.liuzengyu.top`** | 香港 `43.160.227.166:443` $\rightarrow$ 广州 `8.163.29.42:3389` | **`HTTP 200` (`SSL=0`)** | ✅ **全网可用（正式域名对照入口）** |
| **4** | **`https://kaoyan.elenalyl.top`** | 香港 `43.160.227.166:443` $\rightarrow$ 广州 `8.163.29.42:3389` | ⏳ 待解除 `clientHold` | ⏳ **服务端与 DNS A记录 (`43.160.227.166`) 已 100% 就绪**；只需在阿里云「域名控制台 $\rightarrow$ 快速过户」勾选已实名模板 `25324778` 提交，解除 `clientHold` 后自动签发证书 |

---

## 六、 落盘四模态交付物全集索引 (Persisted Deliverables)

""" + f"""1. **Markdown 总结大典（本文件）**：[{STEM}.md](file://{MD_P})
2. **Windows 发布 HTTPS 站点全链路架构总览图 (`.png` / `.svg`)**：[{ARCH_PNG_P.name}](file://{ARCH_PNG_P}) / [{ARCH_SVG_P.name}](file://{ARCH_SVG_P})
3. **2x2 Bento 四象限总结海报 (`.png` / `.svg`)**：[{PNG_P.name}](file://{PNG_P}) / [{SVG_P.name}](file://{SVG_P})
4. **三模态 5-Tab 交互式 HTML 总控台**：[{HTML_P.name}](file://{HTML_P})
5. **6 页 100% 原生可编辑 MSU PPTX 演示文稿**：`{PPTX_P}`（幻灯片网格预览：[{STEM}_slides_preview.png](file://{BASE / f"{STEM}_slides_preview.png"}) / 摘要：[{STEM}_slides_preview.md](file://{BASE / f"{STEM}_slides_preview.md"})）
"""


PPTX_MANIFEST: Dict[str, Any] = {
    "deck_title": TITLE_CN,
    "deck_subtitle": "纯 Windows 研发视角 · 双门禁免密基座 · VS Code 3秒自动发布 · 阿里云非 Root 生产宿主 · 双轨 Let's Encrypt HTTPS",
    "author": "Windows Dev & HTTPS Publishing Guide",
    "date": "2026-10-24",
    "slug": STEM,
    "style": "executive_bento",
    "slides": [
        {
            "layout": "executive_cover",
            "badge": "WINDOWS-TO-HTTPS PUBLISHING SUMMARY · 纯 Windows 视角发布总结",
            "title": "Windows 视角发布考研英语 HTTPS 站点全链路总结",
            "subtitle": "从 Windows 本地 VS Code 改码、双门禁免密认证、阿里云非 Root 生产宿主，到双通道 Let's Encrypt HTTPS 站点发布",
            "cards": [
                {
                    "metric": "4 大里程碑",
                    "title": "Windows -> GitHub -> 阿里云 -> HTTPS",
                    "bullets": ["打通本地研发、双端免密、非 Root 部署与受信任 HTTPS 证书签发全闭环"],
                },
                {
                    "metric": "<= 3.0 秒",
                    "title": "VS Code 改码一键自动上线",
                    "bullets": ["支持 git push origin main + ssh elena deploy-kaoyan 或直推钩子秒级生效"],
                },
                {
                    "metric": "0.145s 首包",
                    "title": "双轨 Let's Encrypt HTTPS 入口",
                    "bullets": ["广州直连 TLS-ALPN-01 极速通道 + 香港免备案边缘网关隐身回源通道"],
                },
            ],
        },
        {
            "layout": "asymmetric_bento",
            "badge": "STAGE 1 · WINDOWS PASSWORDLESS FOUNDATION",
            "title": "阶段一：Windows 本地环境与「2 把钥匙 vs 2 道门禁」免密基座",
            "cards": [
                {
                    "hero": True,
                    "metric": "2 钥 × 2 锁",
                    "title": "消除一切密码弹窗与 Permission denied (publickey) 的核心防混淆架构",
                    "bullets": [
                        "1. 【钥匙 #1：Windows 本地私钥】C:\\Users\\Lenovo\\.ssh\\id_ed25519_codeup (注释 cl-715-codeup，指纹 SHA256:OFeU8L1B...)",
                        "2. 【Windows ~/.ssh/config 路由表】统一声明 Host elena (8.163.29.42) 与 Host github.com 自动挂载钥匙 #1",
                        "3. 【门禁 A：阿里云 authorized_keys】/home/elena/.ssh/authorized_keys (权限 700/600) 放行 Windows 免密登录",
                        "4. 【门禁 B：GitHub settings/keys】同时录入 Windows 公钥 #1 与阿里云公钥 #2 (/home/elena/.ssh/id_ed25519.pub)",
                    ],
                },
                {
                    "metric": "icacls 只读",
                    "title": "Windows 私钥权限收敛",
                    "bullets": [
                        "消除 UNPROTECTED PRIVATE KEY 报错",
                        "icacls /inheritance:r 移除继承权限",
                        "仅保留当前 Windows 登录用户 (R) 只读",
                    ],
                },
                {
                    "metric": "ssh elena",
                    "title": "一行命令秒进阿里云",
                    "bullets": [
                        "PowerShell 与 Git Bash 配置完全共享",
                        "直接登录普通管理账号 elena (uid=1000)",
                        "自带免密 sudo，兼顾安全性与运维效率",
                    ],
                },
            ],
        },
        {
            "layout": "asymmetric_bento",
            "badge": "STAGE 2 · VS CODE CODING & 3-SECOND AUTO-DEPLOY",
            "title": "阶段二：Windows VS Code 改码与双通道一键自动上线流",
            "cards": [
                {
                    "hero": True,
                    "metric": "双通道发布",
                    "title": "在 D:\\kaoyanEnglish 修改前后端代码后的 3 步标准上线流程 (SOP)",
                    "bullets": [
                        "Step 1 (本地改码)：在 VS Code 中修改 frontend/index.html 或 backend/kaoyan_hub_server.py 并本地保存",
                        "Step 2 (推送 GitHub)：执行 git add -A && git commit -m 'feat: update' && git push origin main",
                        "Step 3 (触发阿里云上线)：执行 ssh elena \"deploy-kaoyan\" (或直接 git push elena main)",
                        "Step 4 (自动同步与探活)：服务端自动双向对齐目录、重启 kaoyan-english-hub 并验证 :60231/api/health 返回 200",
                    ],
                },
                {
                    "metric": "deploy-kaoyan",
                    "title": "通道 A：GitHub 标准协同流",
                    "bullets": [
                        "先推 GitHub 留存完整版本历史",
                        "再敲 ssh elena deploy-kaoyan 拉取",
                        "自动同步根目录与子目录入口文件",
                    ],
                },
                {
                    "metric": "post-receive",
                    "title": "通道 B：Git 钩子直推流",
                    "bullets": [
                        "绑定 elena:/home/elena/kaoyan_english_hub",
                        "执行 git push elena main 一步到位",
                        "服务端 post-receive 钩子自动重启服务",
                    ],
                },
            ],
        },
        {
            "layout": "split_comparison",
            "badge": "STAGE 3 · NON-ROOT RUNTIME & DATA PROTECTION",
            "title": "阶段三：阿里云 elena (8.163.29.42) 非 Root 生产底座与数据防丢架构",
            "cards": [
                {
                    "tag": "NON-ROOT SERVICE · 最小权限与双目录自动对齐",
                    "title": "左半平面：普通账号 User=elena 守护进程与 Git 工作区",
                    "bullets": [
                        "1. 【非 Root 运行身份】：kaoyan-english-hub.service 显式锁定 User=elena (uid=1000)，监听 127.0.0.1:60231",
                        "2. 【SSH 硬化防暴力破解】：/etc/ssh/sshd_config 关闭密码登录与 root 密码登录，仅放行 ED25519 公钥",
                        "3. 【前后端双目录自动对齐】：解决仓库同时存在 frontend/index.html 与根 index.html 的历史痛点，改任意一处均自动同步",
                        "4. 【本机 Caddy 双协议守卫】：同时监听 :443 (直连 nip.io HTTPS) 与 :80/:3389 (接收香港边缘回源)",
                    ],
                },
                {
                    "tag": "DATA ISOLATION · 8 表 SQLite WAL 与 40GB 云盘防爆",
                    "title": "右半平面：代码与数据库物理隔离（git reset 绝不丢数据）",
                    "bullets": [
                        "A. 【8 表 SQLite WAL 独立热库】：存放于 /home/elena/kaoyan_storage/hot_db/kaoyan_hub.sqlite3 (独立于代码目录之外)",
                        "B. 【Git 排除保护锁】：.git/info/exclude 显式排除 db_backups/、db_volume/ 与 *.sqlite3*，代码重置 0 数据丢失",
                        "C. 【8 张核心业务表在线】：涵盖真题篇章、5500考纲词、精读批注、生词本、作文语料、五维阅读锚点等",
                        "D. 【40GB 云盘冷热分层】：热库 (<=4GB) + 温快照 (<=2GB, 7天) + 每日 03:30 自动压缩归档，磁盘仅占 8%",
                    ],
                },
            ],
        },
        {
            "layout": "split_comparison",
            "badge": "STAGE 4 · DUAL-PATH HTTPS & DOMAIN MATRIX",
            "title": "阶段四：双通道 Let's Encrypt HTTPS 签发机制与四大公网入口对比",
            "cards": [
                {
                    "tag": "ROUTE 1 · 广州直连极速 HTTPS 通道 (0.145s 首选)",
                    "title": "通道一：https://kaoyan.8.163.29.42.nip.io (TLS-ALPN-01 直签)",
                    "bullets": [
                        "1. 【路由拓扑】：Windows 浏览器 -> 广州 elena (8.163.29.42:443) -> 127.0.0.1:60231",
                        "2. 【为什么能绕开 80 端口拦截？】：Caddy 配置 disable_http_challenge，仅使用 443 端口 TLS-ALPN-01 完成证书验证",
                        "3. 【实测性能指标】：HTTP 200 OK · Let's Encrypt 证书校验通过 (SSL_VERIFY=0) · 首包响应仅 0.145 秒",
                        "4. 【推荐使用场景】：Windows 日常刷题、精读批注、查词入账以及 VS Code 改码后的第一时间真机预览",
                    ],
                },
                {
                    "tag": "ROUTE 2 · 香港免备案边缘回源通道 (自定义域名必选)",
                    "title": "通道二：香港网关 (43.160.227.166:443) -> 广州 elena:3389",
                    "bullets": [
                        "A. 【为什么自定义域名必走香港？】：广州机房对未备案域名在 :80 返 403、在 :443 按 SNI 注入 TCP RST 阻断",
                        "B. 【隐身回源机制】：DNS A 记录指香港 43.160.227.166 签发证书，再以 Host: 127.0.0.1 回源 8.163.29.42:3389",
                        "C. 【已上线香港入口】：https://kaoyan.43.160.227.166.nip.io 与 https://kaoyan.liuzengyu.top (均 HTTP 200)",
                        "D. 【kaoyan.elenalyl.top 收口】：阿里云【域名控制台 -> 快速过户】勾选已实名模板 25324778 提交后即刻自动签发",
                    ],
                },
            ],
        },
        {
            "layout": "asymmetric_bento",
            "badge": "SUMMARY · WINDOWS DEVELOPER QUICK CHEATSHEET",
            "title": "Windows 端考研英语 HTTPS 站点日常发布与运维速查卡",
            "cards": [
                {
                    "hero": True,
                    "metric": "3 行核心指令",
                    "title": "Windows 开发者每天最高频使用的 3 条黄金命令",
                    "bullets": [
                        "① 【免密登录阿里云生产服】：ssh elena   (直接进入 elena@8.163.29.42，自带免密 sudo)",
                        "② 【VS Code 改码后一键发布】：cd /d/kaoyanEnglish && git add -A && git commit -m 'update' && git push origin main && ssh elena \"deploy-kaoyan\"",
                        "③ 【Windows 终端健康探针】：curl.exe -I https://kaoyan.8.163.29.42.nip.io/api/health   (浏览器按 Ctrl+F5 强刷)",
                        "④ 【线上首选 HTTPS 网址】：https://kaoyan.8.163.29.42.nip.io (极速直连) / https://kaoyan.liuzengyu.top (边缘回源)",
                    ],
                },
                {
                    "metric": "Ctrl + F5",
                    "title": "前端改码生效确认",
                    "bullets": [
                        "deploy-kaoyan 会自动重启后端服务",
                        "Caddy 已配 Cache-Control: no-cache",
                        "浏览器按 Ctrl+F5 即可看到最新界面",
                    ],
                },
                {
                    "metric": "模板 25324778",
                    "title": "elenalyl.top 激活步骤",
                    "bullets": [
                        "进入阿里云域名控制台【快速过户】",
                        "勾选已实名成功的模板 25324778",
                        "解除 clientHold 后证书全自动签发",
                    ],
                },
            ],
        },
    ],
}


def build_interactive_html() -> str:
    return r"""<!DOCTYPE html>
<html lang="zh-CN" data-theme="daylight">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Windows 视角发布考研英语 HTTPS 站点全链路总结大典 (Interactive Master Console)</title>
<script>
(function() {
  try {
    var saved = localStorage.getItem('kaoyan_win_pub_theme') || 'daylight';
    document.documentElement.setAttribute('data-theme', saved);
  } catch (e) {}
})();
</script>
<style>
:root, [data-theme="daylight"] {
  --bg-main: #f8fafc;
  --bg-card: #ffffff;
  --bg-subtle: #f1f5f9;
  --text-main: #0f172a;
  --text-muted: #475569;
  --border-color: #cbd5e1;
  --accent-blue: #2563eb;
  --accent-green: #059669;
  --accent-purple: #7c3aed;
  --accent-orange: #ea580c;
  --shadow: 0 4px 16px rgba(15, 23, 42, 0.06);
}
[data-theme="midnight"] {
  --bg-main: #0f172a;
  --bg-card: #1e293b;
  --bg-subtle: #334155;
  --text-main: #f8fafc;
  --text-muted: #cbd5e1;
  --border-color: #475569;
  --accent-blue: #60a5fa;
  --accent-green: #34d399;
  --accent-purple: #a78bfa;
  --accent-orange: #fb923c;
  --shadow: 0 4px 20px rgba(0, 0, 0, 0.35);
}
[data-theme="eyecare"] {
  --bg-main: #f4f1ea;
  --bg-card: #faf8f2;
  --bg-subtle: #eae4d7;
  --text-main: #2c2620;
  --text-muted: #5c5346;
  --border-color: #d6cebf;
  --accent-blue: #1d4ed8;
  --accent-green: #047857;
  --accent-purple: #6d28d9;
  --accent-orange: #c2410c;
  --shadow: 0 4px 14px rgba(44, 38, 32, 0.07);
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'PingFang SC', 'Microsoft YaHei', -apple-system, BlinkMacSystemFont, sans-serif;
  background: var(--bg-main);
  color: var(--text-main);
  line-height: 1.6;
  padding: 20px;
}
.container { max-width: 1440px; margin: 0 auto; }
.header {
  background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 55%, #047857 100%);
  color: #fff;
  padding: 24px 30px;
  border-radius: 16px;
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
  box-shadow: var(--shadow);
}
.header h1 { font-size: 23px; font-weight: 800; margin-bottom: 6px; }
.header p { font-size: 13px; color: #cbd5e1; }
.theme-switcher { display: flex; gap: 8px; }
.theme-btn {
  border: 1px solid rgba(255,255,255,0.3);
  background: rgba(255,255,255,0.12);
  color: #fff;
  padding: 7px 14px;
  border-radius: 20px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 700;
}
.theme-btn.active { background: #10b981; border-color: #10b981; }
.tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 20px;
}
.tab-btn {
  background: var(--bg-card);
  color: var(--text-main);
  border: 1.5px solid var(--border-color);
  padding: 10px 18px;
  border-radius: 12px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 700;
  transition: all 0.2s;
}
.tab-btn.active {
  background: var(--accent-blue);
  color: #fff;
  border-color: var(--accent-blue);
}
.panel { display: none; background: var(--bg-card); border: 1.5px solid var(--border-color); border-radius: 16px; padding: 24px; box-shadow: var(--shadow); }
.panel.active { display: block; }
.grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); gap: 18px; margin-top: 16px; }
.grid-4 { display: grid; grid-template-columns: repeat(auto-fit, minmax(290px, 1fr)); gap: 16px; margin-top: 16px; }
.card {
  background: var(--bg-subtle);
  border: 1.5px solid var(--border-color);
  border-radius: 12px;
  padding: 18px;
}
.card h3 { font-size: 16px; margin-bottom: 8px; color: var(--accent-blue); }
.badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 800;
  color: #fff;
  margin-bottom: 8px;
}
.bg-blue { background: #2563eb; }
.bg-green { background: #059669; }
.bg-purple { background: #7c3aed; }
.bg-orange { background: #ea580c; }
pre {
  background: #0f172a;
  color: #e2e8f0;
  padding: 14px;
  border-radius: 10px;
  font-size: 12px;
  overflow-x: auto;
  margin-top: 10px;
  font-family: 'Consolas', 'Monaco', monospace;
}
table { width: 100%; border-collapse: collapse; margin-top: 14px; font-size: 13px; }
th, td { border: 1px solid var(--border-color); padding: 10px 12px; text-align: left; }
th { background: var(--bg-subtle); font-weight: 800; }
.copy-btn {
  background: var(--accent-green);
  color: #fff;
  border: none;
  padding: 5px 12px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  float: right;
}
@media (max-width: 768px) {
  .grid-2, .grid-4 { grid-template-columns: 1fr; }
}
</style>
</head>
<body>
<div class="container">
  <header class="header">
    <div>
      <h1>Windows 视角发布考研英语 (kaoyan) HTTPS 站点全链路总结大典</h1>
      <p>纯 Windows 视角 (Lenovo@LAPTOP-8M5JKBS4) · 双门禁免密认证 · VS Code 3秒自动发布 · 阿里云非 Root 生产底座 · 双轨 Let's Encrypt HTTPS</p>
    </div>
    <div class="theme-switcher">
      <button class="theme-btn active" onclick="setTheme('daylight')" id="btn-daylight">☀️ 日间模式</button>
      <button class="theme-btn" onclick="setTheme('midnight')" id="btn-midnight">🌙 暗夜模式</button>
      <button class="theme-btn" onclick="setTheme('eyecare')" id="btn-eyecare">🌿 护眼模式</button>
    </div>
  </header>

  <nav class="tabs">
    <button class="tab-btn active" onclick="showTab(0)">1. 全链路发布架构总览图 (Architecture)</button>
    <button class="tab-btn" onclick="showTab(1)">2. Windows 免密与 2钥2锁配置 (SSH Keyring)</button>
    <button class="tab-btn" onclick="showTab(2)">3. VS Code 日常改码发布 3 步 SOP (Deploy Loop)</button>
    <button class="tab-btn" onclick="showTab(3)">4. HTTPS 证书双通道与四大域名矩阵 (HTTPS &amp; TLS)</button>
    <button class="tab-btn" onclick="showTab(4)">5. 阿里云 elena 生产底座与排障速查 (Runtime &amp; Debug)</button>
  </nav>

  <!-- TAB 0: Architecture Overview -->
  <section class="panel active" id="tab-0">
    <h2>一、从 Windows 本地改码到 HTTPS 生产站点的 4 大核心工位</h2>
    <p style="color:var(--text-muted);font-size:13px;margin-top:4px;">点击下方分页可查看对应的 Windows 配置代码、一键发布指令及 HTTPS 域名实时状态。</p>
    <div class="grid-4">
      <div class="card">
        <span class="badge bg-blue">工位 1 · Windows 研发本机</span>
        <h3>Lenovo@LAPTOP-8M5JKBS4</h3>
        <p>• <strong>本地私钥 #1</strong>：<code>C:\Users\Lenovo\.ssh\id_ed25519_codeup</code></p>
        <p>• <strong>SSH 路由表</strong>：<code>C:\Users\Lenovo\.ssh\config</code> 绑定 <code>elena</code> 与 <code>github.com</code></p>
        <p>• <strong>本地代码库</strong>：<code>D:\kaoyanEnglish</code> (VS Code + Git Bash)</p>
      </div>
      <div class="card">
        <span class="badge bg-purple">工位 2 · GitHub 远端仓库</span>
        <h3>yueyiqi/kaoyan.git (main)</h3>
        <p>• <strong>门禁锁芯 B</strong>：<code>github.com/settings/keys</code></p>
        <p>• <strong>双公钥绑定</strong>：同时登记 Windows 公钥 #1 与阿里云 <code>elena</code> 公钥 #2</p>
        <p>• <strong>核心作用</strong>：接收 Windows <code>git push</code>，响应阿里云 <code>git fetch</code></p>
      </div>
      <div class="card">
        <span class="badge bg-green">工位 3 · 阿里云广州生产宿主</span>
        <h3>elena@8.163.29.42</h3>
        <p>• <strong>门禁锁芯 A</strong>：<code>/home/elena/.ssh/authorized_keys</code></p>
        <p>• <strong>自动发布器</strong>：<code>/usr/local/bin/deploy-kaoyan</code> &amp; <code>post-receive</code></p>
        <p>• <strong>非 Root 服务</strong>：<code>User=elena</code> 监听 <code>:60231</code> + 8 表 SQLite WAL</p>
      </div>
      <div class="card">
        <span class="badge bg-orange">工位 4 · 双通道 HTTPS 入口</span>
        <h3>Let's Encrypt 受信任证书</h3>
        <p>• <strong>直连极速入口</strong>：<code>https://kaoyan.8.163.29.42.nip.io</code> (<code>0.145s</code>)</p>
        <p>• <strong>香港免备案回源</strong>：<code>43.160.227.166:443</code> 隐身回源 <code>elena:3389</code></p>
        <p>• <strong>专属域名</strong>：<code>https://kaoyan.elenalyl.top</code> (快速过户后即刻签发)</p>
      </div>
    </div>
  </section>

  <!-- TAB 1: Windows SSH Keyring -->
  <section class="panel" id="tab-1">
    <h2>二、Windows 本地免密配置与「2 把钥匙 vs 2 道门禁」对账表</h2>
    <div class="grid-2">
      <div class="card">
        <h3>1. Windows ~/.ssh/config 标准配置 (C:\Users\Lenovo\.ssh\config)</h3>
        <p style="font-size:12px;color:var(--text-muted);">消除每次手动输入 <code>-i ~/.ssh/id_ed25519_codeup</code>，同时服务 PowerShell、Git Bash 与 VS Code：</p>
        <pre>Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_codeup
    IdentitiesOnly yes

Host elena
    HostName 8.163.29.42
    User elena
    Port 22
    IdentityFile ~/.ssh/id_ed25519_codeup
    IdentitiesOnly yes
    ServerAliveInterval 30
    ServerAliveCountMax 3</pre>
      </div>
      <div class="card">
        <h3>2. 「2 把私钥 vs 2 道门禁」方向关系表</h3>
        <table>
          <thead>
            <tr><th>私钥持有方 (主动发起连接)</th><th>门禁锁芯 A (阿里云 8.163.29.42)</th><th>门禁锁芯 B (GitHub settings/keys)</th></tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>🔑 钥匙 #1：Windows 私钥</strong><br><code>id_ed25519_codeup</code><br><code>SHA256:OFeU8L1B...</code></td>
              <td>✅ <strong>已登记</strong><br><code>ssh elena</code> 免密登录<br><code>git push elena main</code></td>
              <td>✅ <strong>已登记</strong><br>VS Code / Git Bash<br><code>git clone / push origin main</code></td>
            </tr>
            <tr>
              <td><strong>🔑 钥匙 #2：阿里云私钥</strong><br><code>/home/elena/.ssh/id_ed25519</code><br><code>SHA256:1/zjU68N...</code></td>
              <td>➖ 本机无需连自己</td>
              <td>✅ <strong>已登记</strong><br>阿里云 <code>deploy-kaoyan</code><br>免密执行 <code>git fetch origin main</code></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>

  <!-- TAB 2: VS Code Daily Deploy SOP -->
  <section class="panel" id="tab-2">
    <h2>三、Windows VS Code 修改代码后一键发布到 HTTPS 站点 (3 步 SOP)</h2>
    <div class="grid-2">
      <div class="card">
        <span class="badge bg-green">推荐方式 · 通道 A (GitHub 标准协同流)</span>
        <h3>VS Code 推送 GitHub + 触发阿里云拉取重启</h3>
        <pre># Step 1: 在 VS Code 终端 (D:\kaoyanEnglish) 提交并推送到 GitHub
cd /d/kaoyanEnglish
git add -A
git commit -m "feat: update kaoyan English UI"
git push origin main

# Step 2: 在 Windows 终端触发阿里云自动拉取、同步并重启服务
ssh elena "deploy-kaoyan"</pre>
      </div>
      <div class="card">
        <span class="badge bg-blue">快捷方式 · 通道 B (Git Hook 直推流)</span>
        <h3>从 Windows 直接 git push 到阿里云服务器</h3>
        <pre># 仅首次在 D:\kaoyanEnglish 绑定一次 elena 远端：
cd /d/kaoyanEnglish
git remote add elena elena:/home/elena/kaoyan_english_hub

# 之后每次改完代码，一行命令直接推送到阿里云并自动重启生效：
git push elena main</pre>
      </div>
    </div>
  </section>

  <!-- TAB 3: HTTPS & TLS Matrix -->
  <section class="panel" id="tab-3">
    <h2>四、HTTPS 证书签发架构与四大公网访问入口状态矩阵</h2>
    <table>
      <thead>
        <tr>
          <th>HTTPS 访问入口</th>
          <th>底层路由链路</th>
          <th>TLS 证书机制</th>
          <th>实测状态与延迟</th>
          <th>Windows 端使用说明</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong><a href="https://kaoyan.8.163.29.42.nip.io" target="_blank">https://kaoyan.8.163.29.42.nip.io</a></strong></td>
          <td>Windows 浏览器 &rarr; 广州 <code>8.163.29.42:443</code> &rarr; <code>:60231</code></td>
          <td>Let's Encrypt (<code>TLS-ALPN-01</code> 直签)</td>
          <td>✅ <strong>HTTP 200 (0.145s)</strong></td>
          <td><strong>推荐日常首选</strong>：免香港绕行，直连广州生产服，响应最快</td>
        </tr>
        <tr>
          <td><strong><a href="https://kaoyan.43.160.227.166.nip.io" target="_blank">https://kaoyan.43.160.227.166.nip.io</a></strong></td>
          <td>Windows 浏览器 &rarr; 香港 <code>43.160.227.166:443</code> &rarr; 广州 <code>elena:3389</code></td>
          <td>Let's Encrypt (香港边缘自动签发)</td>
          <td>✅ <strong>HTTP 200 (SSL=0)</strong></td>
          <td>与 <code>kaoyan.elenalyl.top</code> 完全同构的香港边缘回源入口</td>
        </tr>
        <tr>
          <td><strong><a href="https://kaoyan.liuzengyu.top" target="_blank">https://kaoyan.liuzengyu.top</a></strong></td>
          <td>Windows 浏览器 &rarr; 香港 <code>43.160.227.166:443</code> &rarr; 广州 <code>elena:3389</code></td>
          <td>Let's Encrypt (香港边缘自动签发)</td>
          <td>✅ <strong>HTTP 200 (SSL=0)</strong></td>
          <td>存量正式域名生产入口，全功能在线</td>
        </tr>
        <tr>
          <td><strong>https://kaoyan.elenalyl.top</strong></td>
          <td>Windows 浏览器 &rarr; 香港 <code>43.160.227.166:443</code> &rarr; 广州 <code>elena:3389</code></td>
          <td>香港 Caddy 自动轮询签发中</td>
          <td>⏳ <strong>待解除 clientHold</strong></td>
          <td>在阿里云【域名控制台 &rarr; 快速过户】勾选已实名模板 <code>25324778</code> 提交后自动点亮</td>
        </tr>
      </tbody>
    </table>
  </section>

  <!-- TAB 4: Runtime & Troubleshooting -->
  <section class="panel" id="tab-4">
    <h2>五、阿里云 elena 生产底座核验与 Windows 常见排障速查</h2>
    <div class="grid-2">
      <div class="card">
        <h3>1. Windows 远程巡检阿里云生产服常用命令</h3>
        <pre># 查看考研英语后端服务与 Caddy 网关运行状态
ssh elena "systemctl is-active kaoyan-english-hub caddy"

# 查看生产服当前 Git 版本与本地健康接口
ssh elena "cd /home/elena/kaoyan_english_hub && git log -1 --oneline && curl -s http://127.0.0.1:60231/api/health"

# 查看 8 表 SQLite WAL 数据库文件大小
ssh elena "ls -lh /home/elena/kaoyan_storage/hot_db/kaoyan_hub.sqlite3*"</pre>
      </div>
      <div class="card">
        <h3>2. Windows 高频问题 30 秒排障表</h3>
        <p>• <strong>问题 1：VS Code 改了 <code>index.html</code> 推送后网页没变？</strong><br>
          答：确认执行了 <code>ssh elena "deploy-kaoyan"</code>，并在 Windows 浏览器按 <code>Ctrl + F5</code> 强制刷新缓存。</p>
        <p style="margin-top:8px;">• <strong>问题 2：PowerShell 报 <code>UNPROTECTED PRIVATE KEY FILE</code>？</strong><br>
          答：运行 <code>icacls "$env:USERPROFILE\.ssh\id_ed25519_codeup" /inheritance:r /grant:r "$($env:USERNAME):(R)"</code> 收敛权限。</p>
        <p style="margin-top:8px;">• <strong>问题 3：为什么 <code>kaoyan.elenalyl.top</code> 还在等证书？</strong><br>
          答：新注册 <code>.top</code> 域名需在阿里云控制台完成「快速过户」绑定已实名模板 <code>25324778</code> 解除注册局 <code>clientHold</code>。</p>
      </div>
    </div>
  </section>
</div>

<script>
function showTab(idx) {
  var tabs = document.querySelectorAll('.tab-btn');
  var panels = document.querySelectorAll('.panel');
  for (var i = 0; i < tabs.length; i++) {
    tabs[i].classList.toggle('active', i === idx);
    panels[i].classList.toggle('active', i === idx);
  }
}
function setTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  try { localStorage.setItem('kaoyan_win_pub_theme', theme); } catch (e) {}
  var btns = document.querySelectorAll('.theme-btn');
  btns.forEach(function(b) { b.classList.remove('active'); });
  var activeBtn = document.getElementById('btn-' + theme);
  if (activeBtn) activeBtn.classList.add('active');
}
</script>
</body>
</html>
"""


def main() -> int:
    # 1. Write Markdown Spec
    MD_P.write_text(build_markdown(), encoding="utf-8")

    # 2. Build 2x2 Bento SVG & PNG
    grid = BentoGrid2x2(page_title=TITLE_CN, page_subtitle=TITLE_EN)
    grid.add_cards(CARDS)
    grid.render_to_file(SVG_P)

    # 3. Build Dedicated Architecture SVG & PNG
    ARCH_SVG_P.write_text(build_dedicated_arch_svg(), encoding="utf-8")

    rsvg = "/opt/homebrew/bin/rsvg-convert"
    if os.path.exists(rsvg):
        subprocess.run(
            [rsvg, "-w", "1600", "--background-color", "#F8FAFC", str(SVG_P), "-o", str(PNG_P)],
            check=True,
        )
        subprocess.run(
            [rsvg, "-w", "1600", "--background-color", "#F8FAFC", str(ARCH_SVG_P), "-o", str(ARCH_PNG_P)],
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

    print("[SUCCESS] All pure Windows-perspective HTTPS publishing summary deliverables generated:")
    for p in [MD_P, SVG_P, PNG_P, ARCH_SVG_P, ARCH_PNG_P, PPTX_P, HTML_P]:
        print(f"  - {p.name} ({p.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
