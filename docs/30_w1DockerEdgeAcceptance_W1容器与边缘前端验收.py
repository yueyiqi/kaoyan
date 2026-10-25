#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
[IoC_Skill_Telemetry]
Status: VERIFIED (ev:ev-0040)
Author: antigravity (qwen3.8-max)
Date: 2026-10-24
Rule: Rule XXII / Rule LIV / Rule LV / Rule LVII-B / Rule LIX
Skill: claude-token-shunt-and-bulk-reader / completion-evidence-protocol

Four-Modal Compiler for Deliverable #30:
  - 30_w1DockerEdgeAcceptance_W1容器与边缘前端验收.md
  - 30_w1DockerEdgeAcceptance_W1容器与边缘前端验收.{svg,png,pptx,html}
"""
from __future__ import annotations

import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path("/Users/liuzengyu/treeworker/workers/srbg10")
BZ_DIR = REPO_ROOT / ".bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台"
EB_20261024 = REPO_ROOT / "_ephemeral_blackbox/2026-10/eb_20261024_srbg10_H_codex_gpt-6_kaoyan-w1-docker-edge-audit"
EB_9041 = REPO_ROOT / "_ephemeral_blackbox/2026-10/eb_9041_srbg10_H_antigravity_gemini-4-argon-high_kaoyan-w1-docker-edge-deep-arch-and-multiphase-remediation"
BRAIN_DIR = Path("/Users/liuzengyu/.gemini/antigravity/brain/8cbcf770-f72a-45c2-ab19-d6745928da4b")

BASE_NAME = "30_w1DockerEdgeAcceptance_W1容器与边缘前端验收"


def _load_font(size: int, bold: bool = False):
    for fp in ("/System/Library/Fonts/PingFang.ttc", "/System/Library/Fonts/STHeiti Medium.ttc", "/System/Library/Fonts/Hiragino Sans GB.ttc"):
        if Path(fp).exists():
            try:
                return ImageFont.truetype(fp, size, index=1 if bold else 0)
            except Exception:
                try:
                    return ImageFont.truetype(fp, size)
                except Exception:
                    pass
    return ImageFont.load_default()


def build_svg_and_png() -> None:
    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 960" width="100%" preserveAspectRatio="xMidYMid meet">
  <rect width="1600" height="960" fill="#F8FAFC"/>
  <rect x="36" y="28" width="1528" height="96" rx="16" fill="#0F172A"/>
  <text x="68" y="72" fill="#F8FAFC" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="25" font-weight="bold">考研英语精读平台 (KaoyanEnglish Hub v3.5) W1容器主权与边缘前端八层架构验收报告 (#30)</text>
  <text x="68" y="106" fill="#94A3B8" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="16">L0–L7 八层底层架构 + 4A 映射 · 两阶段元数据同步 (-99.56% 载荷 / 45.6x 切主提速) · 22 项根因修复 · 8-Phase 真机验收</text>

  <!-- Card 1: Top-Left -->
  <rect x="36" y="148" width="748" height="370" rx="14" fill="#FFFFFF" stroke="#2563EB" stroke-width="2.5"/>
  <rect x="36" y="148" width="748" height="48" rx="14" fill="#DBEAFE"/>
  <text x="60" y="180" fill="#1E40AF" font-family="PingFang SC, sans-serif" font-size="20" font-weight="bold">① L0–L7 八层底层架构与边缘静态分离 (8-Layer Stack &amp; Edge Split)</text>
  <text x="60" y="222" fill="#1E293B" font-family="PingFang SC, sans-serif" font-size="15" font-weight="bold">• L6 边缘白名单静态分发 (Elena ECS Caddy):</text>
  <text x="80" y="246" fill="#475569" font-family="PingFang SC, sans-serif" font-size="14">本地托管 6 个静态文件 (153,169 B)，X-Kaoyan-Frontend: ecs-static，MAX_RELEASES=5 自动 LRU。</text>
  <text x="60" y="282" fill="#1E293B" font-family="PingFang SC, sans-serif" font-size="15" font-weight="bold">• L1/L2 W1 WSL2 Linux Docker 容器主权:</text>
  <text x="80" y="306" fill="#475569" font-family="PingFang SC, sans-serif" font-size="14">kaoyan-w1-gateway (512m) + kaoyan-w1-worker (256m)，readonly rootfs、1000:1000、ext4 VHDX 挂载。</text>
  <text x="60" y="342" fill="#1E293B" font-family="PingFang SC, sans-serif" font-size="15" font-weight="bold">• L3/DA 18 表 × 146 字段全量迁移与三主机冷备金库:</text>
  <text x="80" y="366" fill="#475569" font-family="PingFang SC, sans-serif" font-size="14">W1(Leader)+HP(Replica)+S1(Replica) 100% 哈希一致；W1+HP+S1 三主机冷备金库 + T2 离线队列。</text>
  <text x="60" y="402" fill="#1E293B" font-family="PingFang SC, sans-serif" font-size="15" font-weight="bold">• L7 0-Token 前置限幅外专与实时巡检算子:</text>
  <text x="80" y="426" fill="#475569" font-family="PingFang SC, sans-serif" font-size="14">kaoyan_w1_docker_edge_shunt_engine.py (v2.0) 脱水率 98.04%，支持 live-l0-l7-probe 实时验证。</text>
  <rect x="60" y="452" width="700" height="44" rx="8" fill="#EFF6FF" stroke="#93C5FD"/>
  <text x="80" y="480" fill="#1D4ED8" font-family="PingFang SC, sans-serif" font-size="15" font-weight="bold">架构契约: ADR-0715 · 29 个受治文件跨三机 SHA-256 100% 精确一致</text>

  <!-- Card 2: Top-Right -->
  <rect x="816" y="148" width="748" height="370" rx="14" fill="#FFFFFF" stroke="#059669" stroke-width="2.5"/>
  <rect x="816" y="148" width="748" height="48" rx="14" fill="#D1FAE5"/>
  <text x="840" y="180" fill="#065F46" font-family="PingFang SC, sans-serif" font-size="20" font-weight="bold">② L4 两阶段元数据同步与 45.6 倍切主提速 (Protocol Optimization)</text>
  <text x="840" y="222" fill="#1E293B" font-family="PingFang SC, sans-serif" font-size="15" font-weight="bold">• 两阶段元数据优先同步 (Two-Phase Metadata-First Sync):</text>
  <text x="860" y="246" fill="#475569" font-family="PingFang SC, sans-serif" font-size="14">稳态发送 1.8 KB meta_snap 替代 410 KB 全库 Base64，跨机网络同步载荷降低 99.56%。</text>
  <text x="840" y="282" fill="#1E293B" font-family="PingFang SC, sans-serif" font-size="15" font-weight="bold">• GET/HEAD 只读快路径与单遍表扫描:</text>
  <text x="860" y="306" fill="#475569" font-family="PingFang SC, sans-serif" font-size="14">need_install=False 免除二次 18 表 SHA-256 扫描；只读请求跳过冗余 backup() 与二次同步。</text>
  <text x="840" y="342" fill="#1E293B" font-family="PingFang SC, sans-serif" font-size="15" font-weight="bold">• 公网 HTTPS 延迟与在线切主飞跃:</text>
  <text x="860" y="366" fill="#475569" font-family="PingFang SC, sans-serif" font-size="14">/api/health 3808ms ➔ 834ms (4.57x)；三节点切主 6835ms ➔ S1:149.55ms / HP:159.67ms / W1:238.40ms。</text>
  <text x="840" y="402" fill="#1E293B" font-family="PingFang SC, sans-serif" font-size="15" font-weight="bold">• HP 备用协调器 Epoch+1 围栏容灾演练:</text>
  <text x="860" y="426" fill="#475569" font-family="PingFang SC, sans-serif" font-size="14">W1 容器停机 ➔ HP 15.684s 接管 (epoch=23, 2/3 仲裁) ➔ W1 恢复回切 (epoch=24, 169.81ms, 3/3)。</text>
  <rect x="840" y="452" width="700" height="44" rx="8" fill="#ECFDF5" stroke="#6EE7B7"/>
  <text x="860" y="480" fill="#047857" font-family="PingFang SC, sans-serif" font-size="15" font-weight="bold">实测飞跃: 在线切主最高提速 45.6 倍 · 幂等重放提速 38.5 倍 (177ms)</text>

  <!-- Card 3: Bottom-Left -->
  <rect x="36" y="544" width="748" height="380" rx="14" fill="#FFFFFF" stroke="#EF4444" stroke-width="2.5"/>
  <rect x="36" y="544" width="748" height="48" rx="14" fill="#FEE2E2"/>
  <text x="60" y="576" fill="#991B1B" font-family="PingFang SC, sans-serif" font-size="20" font-weight="bold">③ 22 项底层故障与系统瓶颈闭环 (B01–B12 &amp; D01–D10 Matrix)</text>
  <text x="60" y="620" fill="#1E293B" font-family="PingFang SC, sans-serif" font-size="15" font-weight="bold">• 容器切入与跨内核边界修复 (B01–B12):</text>
  <text x="80" y="644" fill="#475569" font-family="PingFang SC, sans-serif" font-size="14">涵盖缺失卷 Fail-Closed、compose tmpfs 引号、PowerShell Base64 保引号、Caddy @spa 302 等 12 项。</text>
  <text x="60" y="684" fill="#1E293B" font-family="PingFang SC, sans-serif" font-size="15" font-weight="bold">• 协议、容灾、冷备与 WSL2 服务栈加固 (D01–D08):</text>
  <text x="80" y="708" fill="#475569" font-family="PingFang SC, sans-serif" font-size="14">涵盖两阶段同步、SSH ControlMaster 退避重试、三机冷备金库、HP 备用协调器与 WSL2 整栈冷重启。</text>
  <text x="60" y="748" fill="#1E293B" font-family="PingFang SC, sans-serif" font-size="15" font-weight="bold">• 工作树单写僵尸租约溯源与无损清障 (D09):</text>
  <text x="80" y="772" fill="#475569" font-family="PingFang SC, sans-serif" font-size="14">定位 Codex 01a16f50 派生的死进程 agy 子会话 e52c7517，清零 22 个脏文件并完成 VERIFIED 闭环。</text>
  <text x="60" y="812" fill="#1E293B" font-family="PingFang SC, sans-serif" font-size="15" font-weight="bold">• L0–L7 实时巡检算子与 30 号四模态编译器 (D10):</text>
  <text x="80" y="836" fill="#475569" font-family="PingFang SC, sans-serif" font-size="14">实装 --mode live-l0-l7-probe 跨 4 节点实时巡检与 30 号四模态 (.md/.svg/.png/.pptx/.html) 同源编译。</text>
  <rect x="60" y="860" width="700" height="44" rx="8" fill="#FEF2F2" stroke="#FCA5A5"/>
  <text x="80" y="888" fill="#B91C1C" font-family="PingFang SC, sans-serif" font-size="15" font-weight="bold">故障清零: B01–B12 (12项) + D01–D10 (10项) = 22/22 全部 VERIFIED</text>

  <!-- Card 4: Bottom-Right -->
  <rect x="816" y="544" width="748" height="380" rx="14" fill="#FFFFFF" stroke="#7C3AED" stroke-width="2.5"/>
  <rect x="816" y="544" width="748" height="48" rx="14" fill="#EDE9FE"/>
  <text x="840" y="576" fill="#5B21B6" font-family="PingFang SC, sans-serif" font-size="20" font-weight="bold">④ 八阶段 (P0–P7) 全链路验收与双 EB 证据链 (8-Phase Acceptance)</text>
  <text x="840" y="620" fill="#1E293B" font-family="PingFang SC, sans-serif" font-size="15" font-weight="bold">1. [P0–P2 基线取证、契约围栏与容器热升级 PASS]:</text>
  <text x="860" y="644" fill="#475569" font-family="PingFang SC, sans-serif" font-size="14">37 项单元/容器/集群测试 100% 通过；镜像 kaoyan-cluster:56a8353092a2 部署就绪。</text>
  <text x="840" y="684" fill="#1E293B" font-family="PingFang SC, sans-serif" font-size="15" font-weight="bold">2. [P3–P4 协调器容灾演练、三主机金库与 WSL2 冷重启 PASS]:</text>
  <text x="860" y="708" fill="#475569" font-family="PingFang SC, sans-serif" font-size="14">W1-&gt;HP-&gt;W1 演练零丢数；WSL2 隧道+双容器冷重启 17.80s/20.64s 自愈恢复。</text>
  <text x="840" y="748" fill="#1E293B" font-family="PingFang SC, sans-serif" font-size="15" font-weight="bold">3. [P5 公网 HTTPS 46 项高可用终验 PASS]:</text>
  <text x="860" y="772" fill="#475569" font-family="PingFang SC, sans-serif" font-size="14">验证默认 W1 主库、断链写入追平、S1/HP/W1 切主、幂等重放与 18 表 146 列全量一致。</text>
  <text x="840" y="812" fill="#1E293B" font-family="PingFang SC, sans-serif" font-size="15" font-weight="bold">4. [P6–P7 租约清障、L0–L7 实时探针与四模态收口 PASS]:</text>
  <text x="860" y="836" fill="#475569" font-family="PingFang SC, sans-serif" font-size="14">live-l0-l7-probe 跨 4 节点 8 层全绿 (ev:ev-0040 / ev:ev-0022)，工作区 0 脏文件。</text>
  <rect x="840" y="860" width="700" height="44" rx="8" fill="#F5F3FF" stroke="#C4B5FD"/>
  <text x="860" y="888" fill="#6D28D9" font-family="PingFang SC, sans-serif" font-size="15" font-weight="bold">终验结论: P0–P7 八阶段全绿 · primary=W1, version=81, epoch=28, 3/3 副本在线</text>
</svg>
"""
    (BZ_DIR / f"{BASE_NAME}.svg").write_text(svg_content, encoding="utf-8")

    img = Image.new("RGB", (2400, 1440), (248, 250, 252))
    d = ImageDraw.Draw(img)
    f_title = _load_font(32, bold=True)
    f_sub = _load_font(20, bold=False)
    f_h = _load_font(25, bold=True)
    f_b = _load_font(20, bold=True)
    f_p = _load_font(18, bold=False)

    d.rounded_rectangle([48, 36, 2352, 180], radius=22, fill=(15, 23, 42))
    d.text((88, 62), "考研英语精读平台 (KaoyanEnglish Hub v3.5) W1容器主权与边缘前端八层架构验收报告 (#30)", fill=(248, 250, 252), font=f_title)
    d.text((88, 122), "L0–L7 八层底层架构 + 4A 映射 · 两阶段元数据同步 (-99.56% 载荷 / 45.6x 切主提速) · 22 项根因修复 · P0–P7 全绿", fill=(148, 163, 184), font=f_sub)

    cards = [
        (
            48, 210, 1176, 780, (219, 234, 254), (37, 99, 235), (30, 64, 175),
            "① L0–L7 八层底层架构与边缘静态分离",
            [
                ("L6 边缘白名单静态分发 (Elena ECS Caddy)", "托管 6 个静态文件 (153,169 B)，X-Kaoyan-Frontend: ecs-static，LRU<=5。"),
                ("L1/L2 W1 WSL2 Linux Docker 容器主权", "kaoyan-w1-gateway + kaoyan-w1-worker，readonly rootfs、1000:1000、ext4 卷。"),
                ("L3/DA 18 表 × 146 字段与三主机冷备金库", "W1+HP+S1 实时 3 副本哈希一致；三主机冷备金库 + T2 离线同步队列。"),
                ("L7 0-Token 前置限幅外专 v2.0", "kaoyan_w1_docker_edge_shunt_engine.py 压缩率 98.04%，支持 live-l0-l7-probe。"),
            ],
            "架构契约: ADR-0715 · 29 个受治文件跨三机 SHA-256 100% 一致",
        ),
        (
            1224, 210, 2352, 780, (209, 250, 229), (5, 150, 105), (6, 95, 70),
            "② L4 两阶段元数据同步与 45.6 倍切主提速",
            [
                ("两阶段元数据优先同步 (meta_snap 1.8 KB)", "稳态免传 410 KB 全库 Base64，跨机网络同步载荷降低 99.56%。"),
                ("GET/HEAD 只读快路径与单遍表扫描", "need_install=False 免除二次全表扫描；只读请求免除冗余全库备份。"),
                ("公网 HTTPS 延迟与在线切主飞跃", "/api/health 降至 834ms；切主降至 S1:149.55ms / HP:159.67ms / W1:238.40ms。"),
                ("HP 备用协调器 Epoch+1 围栏容灾演练", "W1 停机 -> HP 15.68s 接管 (2/3) -> W1 恢复回切 (169.81ms, 3/3)。"),
            ],
            "实测飞跃: 在线切主最高提速 45.6 倍 · 幂等重放提速 38.5 倍",
        ),
        (
            48, 816, 1176, 1396, (254, 226, 226), (239, 68, 68), (153, 27, 27),
            "③ 22 项底层故障与系统瓶颈闭环 (B01–B12 & D01–D10)",
            [
                ("B01–B12 容器切入与跨内核边界修复", "覆盖缺卷拒启动、tmpfs 引号、PowerShell Base64 保引号、Caddy 302 等 12 项。"),
                ("D01–D08 协议、容灾、冷备与服务栈加固", "覆盖两阶段同步、SSH 退避重试、三机冷备金库、备用协调器与 WSL2 冷重启。"),
                ("D09 工作树单写僵尸租约溯源与清障", "定位 Codex 01a16f50 派生的死进程 agy 子会话 e52c7517，清零 22 个脏文件。"),
                ("D10 L0–L7 实时巡检与 30 号四模态编译", "实装 live-l0-l7-probe 跨 4 节点实时巡检与 30 号四模态同源编译。"),
            ],
            "故障清零: B01–B12 (12项) + D01–D10 (10项) = 22/22 VERIFIED",
        ),
        (
            1224, 816, 2352, 1396, (237, 233, 254), (124, 58, 237), (91, 33, 182),
            "④ 八阶段 (P0–P7) 全链路验收与双 EB 证据链",
            [
                ("P0–P2 基线取证、契约围栏与容器热升级", "37 项单元/容器/集群测试 100% 通过；kaoyan-cluster:56a8353092a2 就绪。"),
                ("P3–P4 协调器容灾、三主机金库与 WSL2 冷重启", "W1->HP->W1 演练零丢数；WSL2 整栈冷重启 17.80s/20.64s 自愈恢复。"),
                ("P5 公网 HTTPS 46 项高可用终验", "验证默认 W1 主库、断链写入追平、三节点切主与 18 表 146 列全量一致。"),
                ("P6–P7 租约清障、实时探针与四模态收口", "live-l0-l7-probe 8 层全绿 (ev:ev-0040 / ev:ev-0022)，工作区 0 脏文件。"),
            ],
            "终验结论: P0–P7 八阶段全绿 · primary=W1, version=81, epoch=28",
        ),
    ]

    for x1, y1, x2, y2, hfill, border, htxt, title, items, footer in cards:
        d.rounded_rectangle([x1, y1, x2, y2], radius=20, fill=(255, 255, 255), outline=border, width=4)
        d.rounded_rectangle([x1, y1, x2, y1 + 68], radius=20, fill=hfill)
        d.text((x1 + 28, y1 + 18), title, fill=htxt, font=f_h)
        cy = y1 + 92
        for b_line, p_line in items:
            d.text((x1 + 30, cy), "• " + b_line, fill=(15, 23, 42), font=f_b)
            d.text((x1 + 52, cy + 34), p_line, fill=(71, 85, 105), font=f_p)
            cy += 96
        d.rounded_rectangle([x1 + 28, y2 - 76, x2 - 28, y2 - 18], radius=12, fill=hfill, outline=border, width=2)
        d.text((x1 + 48, y2 - 60), footer, fill=htxt, font=f_b)

    img.save(BZ_DIR / f"{BASE_NAME}.png", "PNG")


def build_pptx() -> None:
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor

    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    blank_layout = prs.slide_layouts[6]
    slides_data = [
        ("Slide 1 · L0–L7 八层底层架构与边缘静态分离 (#30)", "Elena ECS 纯静态白名单入口 + W1 WSL2 Docker 协调器与默认主库 + HP/S1 跨 OS 同步副本", [
            ("L6 边缘白名单静态分发 (Elena ECS)", "托管 6 个静态文件 (153,169 B)，X-Kaoyan-Frontend: ecs-static，MAX_RELEASES=5 自动 LRU。"),
            ("L1/L2 W1 WSL2 Linux Docker 容器主权", "kaoyan-w1-gateway (512m) + kaoyan-w1-worker (256m)，readonly rootfs、1000:1000、ext4 挂载。"),
            ("L3/DA 18 表 × 146 字段与三主机冷备金库", "W1+HP+S1 实时 3 副本哈希一致；三主机冷备金库 + T2 离线同步队列。"),
            ("L7 0-Token 前置限幅外专 v2.0", "kaoyan_w1_docker_edge_shunt_engine.py 压缩率 98.04%，支持 live-l0-l7-probe。"),
        ]),
        ("Slide 2 · L4 两阶段元数据同步与 45.6 倍切主提速", "消除稳态 3×410KB Base64 全库广播与重复全表扫描，实现毫秒级在线切主", [
            ("两阶段元数据优先同步 (meta_snap 1.8 KB)", "版本匹配时仅发 1.8 KB 元数据，稳态网络载荷降低 99.56%，失步自动回退全量快照。"),
            ("GET/HEAD 只读快路径与单遍表扫描", "need_install=False 免除二次 18 表 SHA-256 扫描；只读请求跳过冗余 backup()。"),
            ("公网 HTTPS 延迟与在线切主飞跃", "/api/health 3808ms -> 834ms (4.57x)；三节点切主 6835ms -> 149.55ms~238.40ms (45.6x)。"),
            ("HP 备用协调器 Epoch+1 围栏容灾演练", "W1 容器停机 -> HP 15.684s 接管 (epoch=23, 2/3) -> W1 恢复回切 (epoch=24, 169.81ms)。"),
        ]),
        ("Slide 3 · 22 项底层故障与系统瓶颈闭环 (B01–B12 & D01–D10)", "穿透内核挂载、SSH 转义、Docker 生命周期、复制协议与工作树单写租约", [
            ("B01–B12 容器切入与跨内核边界修复", "覆盖缺卷拒启动、compose tmpfs 引号、PowerShell Base64 保引号、Caddy 302 等 12 项。"),
            ("D01–D08 协议、容灾、冷备与服务栈加固", "覆盖两阶段同步、SSH 退避重试、三机冷备金库、备用协调器与 WSL2 整栈冷重启。"),
            ("D09 工作树单写僵尸租约溯源与清障", "定位 Codex 01a16f50 派生的死进程 agy 子会话 e52c7517，清零 22 个脏文件。"),
            ("D10 L0–L7 实时巡检与 30 号四模态编译", "实装 live-l0-l7-probe 跨 4 节点实时巡检与 30 号四模态同源编译。"),
        ]),
        ("Slide 4 · 八阶段 (P0–P7) 全链路验收与双 EB 证据链", "46 项公网 HTTPS 断言 + 37 项单元/容器测试 + L0–L7 实时巡检 100% 通过", [
            ("P0–P2 基线取证、契约围栏与容器热升级", "37 项单元/容器/集群测试 100% 通过；镜像 kaoyan-cluster:56a8353092a2 部署就绪。"),
            ("P3–P4 协调器容灾、三主机金库与 WSL2 冷重启", "W1->HP->W1 演练零丢数；WSL2 整栈冷重启 17.80s/20.64s 自愈恢复。"),
            ("P5 公网 HTTPS 46 项高可用终验", "验证默认 W1 主库、断链写入追平、三节点切主与 18 表 146 列全量一致。"),
            ("P6–P7 租约清障、实时探针与四模态收口", "live-l0-l7-probe 8 层全绿 (ev:ev-0040 / ev:ev-0022)，工作区 0 脏文件。"),
        ]),
    ]
    coords = [(Inches(0.4), Inches(1.65)), (Inches(6.8), Inches(1.65)), (Inches(0.4), Inches(4.45)), (Inches(6.8), Inches(4.45))]
    for stitle, ssub, cards in slides_data:
        slide = prs.slides.add_slide(blank_layout)
        bg = slide.shapes.add_shape(1, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
        bg.fill.solid(); bg.fill.fore_color.rgb = RGBColor(248, 250, 252); bg.line.fill.background()
        hdr = slide.shapes.add_shape(1, Inches(0.4), Inches(0.3), Inches(12.533), Inches(1.15))
        hdr.fill.solid(); hdr.fill.fore_color.rgb = RGBColor(15, 23, 42); hdr.line.fill.background()
        tf = hdr.text_frame; tf.word_wrap = True
        p0 = tf.paragraphs[0]; p0.text = stitle; p0.font.size = Pt(21); p0.font.bold = True; p0.font.color.rgb = RGBColor(248, 250, 252)
        p1 = tf.add_paragraph(); p1.text = ssub; p1.font.size = Pt(13); p1.font.color.rgb = RGBColor(148, 163, 184)
        for (cx, cy), (ctitle, cbody) in zip(coords, cards):
            box = slide.shapes.add_shape(1, cx, cy, Inches(6.13), Inches(2.55))
            box.fill.solid(); box.fill.fore_color.rgb = RGBColor(255, 255, 255); box.line.color.rgb = RGBColor(37, 99, 235); box.line.width = Pt(1.5)
            btf = box.text_frame; btf.word_wrap = True
            bp0 = btf.paragraphs[0]; bp0.text = ctitle; bp0.font.size = Pt(15); bp0.font.bold = True; bp0.font.color.rgb = RGBColor(30, 64, 175)
            bp1 = btf.add_paragraph(); bp1.text = cbody; bp1.font.size = Pt(13); bp1.font.color.rgb = RGBColor(51, 65, 85)
    prs.save(str(BZ_DIR / f"{BASE_NAME}.pptx"))


def build_html() -> None:
    html_content = """<!DOCTYPE html>
<html lang="zh-CN" data-theme="daylight">
<head>
  <meta charset="UTF-8" /><meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>考研英语精读平台 (KaoyanEnglish Hub v3.5) W1容器与边缘前端八层架构验收报告 (#30)</title>
  <script>(function(){document.documentElement.setAttribute('data-theme',localStorage.getItem('kaoyan30_theme')||'daylight');})();</script>
  <style>
    :root[data-theme="daylight"] { --bg:#F8FAFC; --card:#FFFFFF; --text:#0F172A; --muted:#475569; --accent:#2563EB; --border:#E2E8F0; }
    :root[data-theme="midnight"] { --bg:#0F172A; --card:#1E293B; --text:#F8FAFC; --muted:#94A3B8; --accent:#60A5FA; --border:#334155; }
    :root[data-theme="eyecare"]  { --bg:#F4F1EA; --card:#FAF8F5; --text:#1F2937; --muted:#4B5563; --accent:#059669; --border:#D6D3CD; }
    body { margin:0; font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif; background:var(--bg); color:var(--text); padding:24px; line-height:1.6; }
    .header { display:flex; justify-content:space-between; align-items:center; background:var(--card); border:1px solid var(--border); border-radius:14px; padding:20px 28px; margin-bottom:24px; flex-wrap:wrap; gap:12px; }
    .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(460px,1fr)); gap:20px; }
    .card { background:var(--card); border:1px solid var(--border); border-radius:14px; padding:22px; }
    h1 { margin:0 0 8px 0; font-size:22px; } h2 { margin:0 0 12px 0; font-size:18px; color:var(--accent); }
    ul { padding-left:20px; margin:0; } button { cursor:pointer; padding:8px 14px; border-radius:8px; border:1px solid var(--border); background:var(--card); color:var(--text); margin-left:6px; font-weight:600; }
    .badge { display:inline-block; padding:4px 10px; border-radius:6px; background:#DCFCE7; color:#166534; font-weight:700; font-size:13px; }
  </style>
</head>
<body>
  <div class="header">
    <div><h1>考研英语精读平台 (KaoyanEnglish Hub v3.5) W1容器与边缘前端八层架构验收报告 (#30)</h1><div><span class="badge">VERIFIED · P0–P7 八阶段全绿 · 46/46 公网断言 PASS</span> · L0–L7 + 4A 深度架构 · 切主提速 45.6x (149.55ms)</div></div>
    <div><button onclick="setTheme('daylight')">☀️ Daylight</button><button onclick="setTheme('midnight')">🌙 Midnight</button><button onclick="setTheme('eyecare')">🍵 Eyecare</button></div>
  </div>
  <div class="grid">
    <div class="card"><h2>① L0–L7 八层底层架构与边缘静态分离</h2><ul>
      <li><b>L6 边缘白名单静态分发</b>：Elena ECS Caddy 托管 6 个静态文件 (153,169 B)，<code>X-Kaoyan-Frontend: ecs-static</code>，<code>MAX_RELEASES=5</code> 自动 LRU。</li>
      <li><b>L1/L2 W1 WSL2 容器主权</b>：<code>kaoyan-w1-gateway</code> + <code>kaoyan-w1-worker</code>，只读根文件系统、非特权用户 <code>1000:1000</code>、WSL2 原生 <code>ext4</code> 卷。</li>
      <li><b>L3/DA 18表146字段与三主机金库</b>：W1+HP+S1 三副本 SHA-256 100% 一致；三主机冷备金库 + T2 离线队列。</li>
    </ul></div>
    <div class="card"><h2>② 两阶段元数据同步、22 项修复与 P0–P7 终验</h2><ul>
      <li><b>协议级飞跃 (-99.56% 载荷)</b>：<code>meta_snap</code> (1.8 KB) 替代 410 KB 全库广播；在线切主从 6835ms 降至 149.55ms (45.6x 提速)。</li>
      <li><b>协调器 Epoch 围栏容灾演练</b>：W1 停机 -> HP 15.68s 接管 (epoch=23) -> W1 恢复回切 (epoch=24, 169.81ms)。</li>
      <li><b>22 项问题闭环</b>：B01–B12 + D01–D10 全部 VERIFIED (<code>ev:ev-0040</code> / <code>ev:ev-0022</code>)。</li>
    </ul></div>
  </div>
  <script>function setTheme(t){document.documentElement.setAttribute('data-theme',t);localStorage.getItem('kaoyan30_theme',t);}</script>
</body></html>
"""
    (BZ_DIR / f"{BASE_NAME}.html").write_text(html_content, encoding="utf-8")


def sync_to_brain() -> None:
    BRAIN_DIR.mkdir(parents=True, exist_ok=True)
    for ext in (".svg", ".png", ".pptx", ".html", ".md"):
        src = BZ_DIR / f"{BASE_NAME}{ext}"
        if src.exists():
            shutil.copy2(src, BRAIN_DIR / src.name)


def main() -> int:
    BZ_DIR.mkdir(parents=True, exist_ok=True)
    build_svg_and_png()
    build_pptx()
    build_html()
    sync_to_brain()
    print("Compiled Deliverable #30 visual & HTML assets in:", BZ_DIR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
