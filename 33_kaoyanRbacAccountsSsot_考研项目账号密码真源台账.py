#!/usr/bin/env python3
"""Four-Modal Visual Compiler for #33 Kaoyan RBAC Login Accounts & Passwords SSOT Ledger."""

from __future__ import annotations

import html
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

HERE = Path(__file__).resolve().parent
BRAIN_DIR = Path("/Users/liuzengyu/.gemini/antigravity/brain/8cbcf770-f72a-45c2-ab19-d6745928da4b")
STEM = "33_kaoyanRbacAccountsSsot_考研项目账号密码真源台账"
TITLE = "kaoyan-elena.duckdns.org 截图圈红登录框对应账号密码全量表 (ev:ev-0005)"
SUBTITLE = "截图中圈红的登录栏（左框：账号，右框：掩码密码，按钮：🔑 登录并恢复进度）对应生产库 sys_users 中以下 5 个现役活跃账号（PBKDF2-HMAC-SHA256 10,000 次迭代与 POST /api/auth/login 真机核验返回 HTTP 200）"

FONT_CANDIDATES = [
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
]

TABLE_HEADERS = [
    ("角色分级 (role)", 210),
    ("权限等级", 110),
    ("圈红左框输入：账号 (username)", 270),
    ("圈红右框输入：密码 (passcode)", 270),
    ("显示名称 (display_name)", 250),
    ("登录后解锁权限与界面能力", 710),
]

TABLE_ROWS = [
    (
        "ADMIN (系统管理员)",
        "L100",
        "admin",
        "Kaoyan@Admin2026",
        "系统管理员 (admin)",
        "解锁 100% 真题全文 + 账号与 RBAC 管理专题页（新增/启停账号、重置任意账号密码）+ 5 层 18 表 146 字段全库下钻",
        "#EFF6FF",
        "#1E40AF",
    ),
    (
        "ADMIN (系统管理员)",
        "L100",
        "commander",
        "Kaoyan@Admin2026",
        "统帅 (集群架构管理员)",
        "同上（完整 L100 集群与系统管理员权限）",
        "#EFF6FF",
        "#1E40AF",
    ),
    (
        "SCHOLAR (研友学籍)",
        "L50",
        "colleague_a",
        "kaoyan2026",
        "同事 A (考研英语主理人)",
        "解锁 100% 真题全文精读（解除 Para 2~4 的 45% 毛玻璃与 25% 锁闭区）+ 个人生词本与阅读断点漫游 + 凭原密码修改本人密码",
        "#ECFDF5",
        "#065F46",
    ),
    (
        "SCHOLAR (研友学籍)",
        "L50",
        "scholar_b",
        "kaoyan2026",
        "研友协作学籍 (scholar_b)",
        "同上（独立学籍空间，生词本与断点独立隔离）",
        "#ECFDF5",
        "#065F46",
    ),
    (
        "SCHOLAR (研友学籍)",
        "L50",
        "scholar_c",
        "kaoyan2026",
        "测试研友 (scholar_c)",
        "同上（独立学籍空间，测试研友账号）",
        "#ECFDF5",
        "#065F46",
    ),
]

CARDS = [
    (
        "① 系统管理员账号 (ADMIN · L100 全权限)",
        (219, 234, 254), (37, 99, 235), (30, 64, 175), "#DBEAFE", "#2563EB", "#1E40AF",
        [
            ("管理员账号 1: admin", "初始登录密码: Kaoyan@Admin2026 (系统管理员 · HTTP 200 实测通过)"),
            ("管理员账号 2: commander", "初始登录密码: Kaoyan@Admin2026 (统帅集群管理员 · HTTP 200 实测通过)"),
            ("解锁能力范围", "100% 真题精读 + 账号管理/重置密码 + 5层18表146字段全库下钻"),
        ],
        "管理员通用密码: Kaoyan@Admin2026 (PBKDF2-HMAC-SHA256 10,000次迭代)",
    ),
    (
        "② 正式研友学籍账号 (SCHOLAR · L50 业务全解锁)",
        (209, 250, 229), (5, 150, 105), (6, 95, 70), "#D1FAE5", "#059669", "#065F46",
        [
            ("学籍账号 1: colleague_a", "初始登录密码: kaoyan2026 (同事 A 考研英语主理人 · HTTP 200)"),
            ("学籍账号 2: scholar_b", "初始登录密码: kaoyan2026 (研友协作学籍 B · HTTP 200)"),
            ("学籍账号 3: scholar_c", "初始登录密码: kaoyan2026 (测试研友学籍 C · HTTP 200)"),
        ],
        "研友学籍通用密码: kaoyan2026 (解锁 100% 真题全文与个人生词断点漫游)",
    ),
    (
        "③ 截图圈红登录组件与密码学安全契约",
        (254, 226, 226), (239, 68, 68), (153, 27, 27), "#FEE2E2", "#EF4444", "#991B1B",
        [
            ("左框 #scholarUserInput", "输入 admin / commander / colleague_a / scholar_b / scholar_c"),
            ("右框 #scholarKeyInput", "掩码密码框 (type=password)，提交瞬间立即清空 DOM 零留存"),
            ("服务端 KDF 校验", "PBKDF2-HMAC-SHA256 (10,000 iterations) + 独立随机盐值校验"),
        ],
        "公网实测端点: POST https://kaoyan-elena.duckdns.org/api/auth/login",
    ),
    (
        "④ 双点 SSOT 真源落盘与四槽同步",
        (237, 233, 254), (124, 58, 237), (91, 33, 182), "#EDE9FE", "#7C3AED", "#5B21B6",
        [
            ("项目级机器真源", ".bz/95_kaoyan_考研/kaoyan_rbac_accounts_ssot.json"),
            ("全域治理真源镜像", ".governance/kaoyan_rbac_accounts_ssot.json"),
            ("编号化四模态大典 (#33)", "33_kaoyanRbacAccountsSsot_考研项目账号密码真源台账.{md,py,svg,png,pptx,html}"),
        ],
        "核验物证: ev:ev-0005 · 5/5 活跃账号公网 HTTPS 登录 200 OK",
    ),
]


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for p in FONT_CANDIDATES:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def build_svg_and_png() -> None:
    w, h = 1900, 1480
    img = Image.new("RGB", (w, h), (248, 250, 252))
    draw = ImageDraw.Draw(img)
    f_title = load_font(28)
    f_sub = load_font(15)
    f_th = load_font(16)
    f_td = load_font(15)
    f_td_bold = load_font(16)
    f_card_t = load_font(20)
    f_item_t = load_font(16)
    f_item_d = load_font(14)

    # Top Header Banner
    draw.rounded_rectangle([40, 24, 1860, 134], radius=16, fill=(15, 23, 42))
    draw.text((68, 42), TITLE, fill=(248, 250, 252), font=f_title)
    draw.text((68, 86), SUBTITLE[:82], fill=(148, 163, 184), font=f_sub)
    draw.text((68, 108), SUBTITLE[82:], fill=(148, 163, 184), font=f_sub)

    # Full 5-Row Verbatim Table Box (y=154..610)
    tx, ty, tw, th_box = 40, 154, 1820, 456
    draw.rounded_rectangle([tx, ty, tx + tw, ty + th_box], radius=14, fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rounded_rectangle([tx, ty, tx + tw, ty + 52], radius=14, fill=(30, 41, 59))

    # Draw Table Headers
    cx = tx
    for col_title, col_w in TABLE_HEADERS:
        draw.text((cx + 14, ty + 16), col_title, fill=(248, 250, 252), font=f_th)
        cx += col_w

    # Draw 5 Rows
    ry = ty + 52
    row_h = 80
    for idx, row in enumerate(TABLE_ROWS):
        role_s, lvl_s, user_s, pass_s, disp_s, perm_s, bg_hex, fg_hex = row
        bg_rgb = (239, 246, 255) if idx < 2 else (236, 253, 245)
        fg_rgb = (30, 64, 175) if idx < 2 else (6, 95, 70)
        draw.rectangle([tx + 2, ry, tx + tw - 2, ry + row_h], fill=bg_rgb if idx % 2 == 0 else (255, 255, 255))
        draw.line([tx + 2, ry + row_h, tx + tw - 2, ry + row_h], fill=(226, 232, 240), width=1)

        cols = [role_s, lvl_s, user_s, pass_s, disp_s, perm_s]
        cx = tx
        for c_i, ((_, col_w), val) in enumerate(zip(TABLE_HEADERS, cols)):
            if c_i in (2, 3):
                # Highlight username & password badge
                draw.rounded_rectangle([cx + 10, ry + 18, cx + col_w - 18, ry + 60], radius=8, fill=bg_rgb, outline=fg_rgb, width=1)
                draw.text((cx + 20, ry + 28), val, fill=fg_rgb, font=f_td_bold)
            elif c_i == 5 and len(val) > 42:
                draw.text((cx + 12, ry + 18), val[:42], fill=(15, 23, 42), font=f_td)
                draw.text((cx + 12, ry + 44), val[42:], fill=(51, 65, 85), font=f_td)
            else:
                draw.text((cx + 12, ry + 28), val, fill=fg_rgb if c_i in (0, 1) else (15, 23, 42), font=f_td_bold if c_i in (0, 1) else f_td)
            if c_i > 0:
                draw.line([cx, ty, cx, ty + th_box], fill=(226, 232, 240), width=1)
            cx += col_w
        ry += row_h

    # 2x2 Bento Grid (y=634..1450)
    coords = [(40, 634), (960, 634), (40, 1050), (960, 1050)]
    cw, ch = 900, 396
    for (x, y), (ctitle, bg_rgb, bd_rgb, tx_rgb, _, _, _, items, badge) in zip(coords, CARDS):
        draw.rounded_rectangle([x, y, x + cw, y + ch], radius=16, fill=(255, 255, 255), outline=bd_rgb, width=3)
        draw.rounded_rectangle([x, y, x + cw, y + 54], radius=16, fill=bg_rgb)
        draw.text((x + 24, y + 14), ctitle, fill=tx_rgb, font=f_card_t)
        iy = y + 74
        for it_t, it_d in items:
            draw.text((x + 24, iy), f"• {it_t}", fill=(15, 23, 42), font=f_item_t)
            draw.text((x + 42, iy + 26), it_d, fill=(71, 85, 105), font=f_item_d)
            iy += 74
        draw.rounded_rectangle([x + 24, y + ch - 52, x + cw - 24, y + ch - 14], radius=8, fill=bg_rgb, outline=bd_rgb, width=1)
        draw.text((x + 36, y + ch - 42), badge, fill=tx_rgb, font=f_item_d)

    img.save(HERE / f"{STEM}.png", "PNG")

    # Also build SVG
    esc = html.escape
    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" preserveAspectRatio="xMidYMid meet">',
        f'<rect width="{w}" height="{h}" fill="#F8FAFC"/>',
        f'<rect x="40" y="24" width="1820" height="110" rx="16" fill="#0F172A"/>',
        f'<text x="68" y="68" fill="#F8FAFC" font-size="26" font-weight="bold" font-family="PingFang SC, sans-serif">{esc(TITLE)}</text>',
        f'<text x="68" y="106" fill="#94A3B8" font-size="15" font-family="PingFang SC, sans-serif">{esc(SUBTITLE)}</text>',
        f'<rect x="40" y="154" width="1820" height="456" rx="14" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="2"/>',
        f'<rect x="40" y="154" width="1820" height="52" rx="14" fill="#1E293B"/>',
    ]
    cx = 40
    for col_title, col_w in TABLE_HEADERS:
        svg_parts.append(f'<text x="{cx+14}" y="186" fill="#F8FAFC" font-size="15" font-weight="bold" font-family="PingFang SC, sans-serif">{esc(col_title)}</text>')
        cx += col_w
    ry = 206
    for idx, row in enumerate(TABLE_ROWS):
        role_s, lvl_s, user_s, pass_s, disp_s, perm_s, bg_hex, fg_hex = row
        svg_parts.append(f'<rect x="42" y="{ry}" width="1816" height="80" fill="{bg_hex if idx % 2 == 0 else "#FFFFFF"}"/>')
        cols = [role_s, lvl_s, user_s, pass_s, disp_s, perm_s]
        cx = 40
        for c_i, ((_, col_w), val) in enumerate(zip(TABLE_HEADERS, cols)):
            svg_parts.append(f'<text x="{cx+14}" y="{ry+46}" fill="{fg_hex if c_i in (0,1,2,3) else "#0F172A"}" font-size="14" font-weight="{"bold" if c_i in (0,1,2,3) else "normal"}" font-family="PingFang SC, sans-serif">{esc(val[:48])}</text>')
            cx += col_w
        ry += 80
    for (x, y), (ctitle, _, _, _, bg_hex, bd_hex, tx_hex, items, badge) in zip(coords, CARDS):
        svg_parts.append(f'<rect x="{x}" y="{y}" width="{cw}" height="{ch}" rx="16" fill="#FFFFFF" stroke="{bd_hex}" stroke-width="3"/>')
        svg_parts.append(f'<rect x="{x}" y="{y}" width="{cw}" height="54" rx="16" fill="{bg_hex}"/>')
        svg_parts.append(f'<text x="{x+24}" y="{y+35}" fill="{tx_hex}" font-size="20" font-weight="bold" font-family="PingFang SC, sans-serif">{esc(ctitle)}</text>')
        iy = y + 92
        for it_t, it_d in items:
            svg_parts.append(f'<text x="{x+24}" y="{iy}" fill="#0F172A" font-size="16" font-weight="bold" font-family="PingFang SC, sans-serif">• {esc(it_t)}</text>')
            svg_parts.append(f'<text x="{x+42}" y="{iy+26}" fill="#475569" font-size="14" font-family="PingFang SC, sans-serif">{esc(it_d)}</text>')
            iy += 74
        svg_parts.append(f'<rect x="{x+24}" y="{y+ch-52}" width="{cw-48}" height="38" rx="8" fill="{bg_hex}" stroke="{bd_hex}"/>')
        svg_parts.append(f'<text x="{x+36}" y="{y+ch-28}" fill="{tx_hex}" font-size="14" font-weight="bold" font-family="PingFang SC, sans-serif">{esc(badge)}</text>')
    svg_parts.append("</svg>")
    (HERE / f"{STEM}.svg").write_text("\n".join(svg_parts), encoding="utf-8")


def build_pptx() -> None:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    hdr = slide.shapes.add_textbox(Inches(0.4), Inches(0.25), Inches(12.5), Inches(0.9))
    tf = hdr.text_frame
    p0 = tf.paragraphs[0]
    p0.text = TITLE
    p0.font.size = Pt(20)
    p0.font.bold = True
    p1 = tf.add_paragraph()
    p1.text = SUBTITLE
    p1.font.size = Pt(11)
    bento_pos = [(0.4, 1.3), (6.8, 1.3), (0.4, 4.35), (6.8, 4.35)]
    for (lx, ly), (ctitle, _, bd_rgb, tx_rgb, _, _, _, items, badge) in zip(bento_pos, CARDS):
        box = slide.shapes.add_textbox(Inches(lx), Inches(ly), Inches(6.1), Inches(2.85))
        btf = box.text_frame
        btf.word_wrap = True
        bp0 = btf.paragraphs[0]
        bp0.text = ctitle
        bp0.font.size = Pt(14)
        bp0.font.bold = True
        bp0.font.color.rgb = RGBColor(*tx_rgb)
        for it_t, it_d in items:
            bp = btf.add_paragraph()
            bp.text = f"• {it_t}: {it_d}"
            bp.font.size = Pt(11)
        bb = btf.add_paragraph()
        bb.text = f"[{badge}]"
        bb.font.size = Pt(10)
        bb.font.bold = True
        bb.font.color.rgb = RGBColor(*bd_rgb)
    prs.save(str(HERE / f"{STEM}.pptx"))


def build_html() -> None:
    rows_html = "\n".join(
        f"<tr><td><strong>{r[0]}</strong></td><td><code>{r[1]}</code></td><td><code>{r[2]}</code></td><td><code>{r[3]}</code></td><td>{r[4]}</td><td>{r[5]}</td></tr>"
        for r in TABLE_ROWS
    )
    html_str = f"""<!DOCTYPE html>
<html lang="zh-CN" data-theme="daylight">
<head>
  <meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <title>{TITLE}</title>
  <script>(function(){{document.documentElement.setAttribute('data-theme',localStorage.getItem('bz33_theme')||'daylight');}})();</script>
  <style>
    :root[data-theme="daylight"]{{--bg:#F8FAFC;--card:#FFFFFF;--text:#0F172A;--muted:#475569;--accent:#2563EB;--border:#E2E8F0;}}
    :root[data-theme="midnight"]{{--bg:#0F172A;--card:#1E293B;--text:#F8FAFC;--muted:#94A3B8;--accent:#60A5FA;--border:#334155;}}
    :root[data-theme="eyecare"]{{--bg:#F4F1EA;--card:#FAF8F5;--text:#1F2937;--muted:#4B5563;--accent:#059669;--border:#D6D3CD;}}
    body{{margin:0;font-family:-apple-system,"PingFang SC",sans-serif;background:var(--bg);color:var(--text);padding:24px;line-height:1.6;}}
    .hdr{{display:flex;justify-content:space-between;align-items:center;background:var(--card);border:1px solid var(--border);border-radius:14px;padding:20px 28px;margin-bottom:24px;flex-wrap:wrap;gap:12px;}}
    table{{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--border);border-radius:12px;overflow:hidden;margin-bottom:24px;}}
    th,td{{padding:12px 14px;border-bottom:1px solid var(--border);text-align:left;font-size:14px;}}
    th{{background:#1E293B;color:#F8FAFC;}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(460px,1fr));gap:20px;}}
    .card{{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:22px;}}
    h1{{margin:0 0 6px 0;font-size:22px;}} h2{{margin:0 0 12px 0;font-size:18px;color:var(--accent);}}
    code{{background:rgba(37,99,235,0.1);padding:2px 6px;border-radius:4px;font-weight:700;}}
    button{{cursor:pointer;padding:8px 14px;border-radius:8px;border:1px solid var(--border);background:var(--card);color:var(--text);margin-left:6px;font-weight:600;}}
  </style>
</head>
<body>
  <div class="hdr">
    <div><h1>{TITLE}</h1><div>{SUBTITLE}</div></div>
    <div><button onclick="setTheme('daylight')">☀️ Daylight</button><button onclick="setTheme('midnight')">🌙 Midnight</button><button onclick="setTheme('eyecare')">🍵 Eyecare</button></div>
  </div>
  <table>
    <thead><tr><th>角色分级 (role)</th><th>权限等级</th><th>圈红左框输入：账号 (username)</th><th>圈红右框输入：密码 (passcode)</th><th>显示名称 (display_name)</th><th>登录后解锁权限与界面能力</th></tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
  <div class="grid">
    <div class="card"><h2>① 系统管理员账号 (ADMIN · L100)</h2><p>账号：<code>admin</code> 或 <code>commander</code><br/>密码：<code>Kaoyan@Admin2026</code><br/>权限：全量真题精读 + 账号权限管理 + 全库 5 层 18 表 146 字段下钻。</p></div>
    <div class="card"><h2>② 正式研友学籍账号 (SCHOLAR · L50)</h2><p>账号：<code>colleague_a</code> / <code>scholar_b</code> / <code>scholar_c</code><br/>密码：<code>kaoyan2026</code><br/>权限：解锁 100% 真题全文精读（解除毛玻璃与锁闭区）+ 个人生词本与进度漫游。</p></div>
    <div class="card"><h2>③ 圈红登录框与安全契约</h2><p>左框输入账号，右框输入密码，点击「🔑 登录并恢复进度」即可登录；密码经 PBKDF2-HMAC-SHA256 (10,000 次迭代) 校验。</p></div>
    <div class="card"><h2>④ 双点 SSOT 真源落盘</h2><p>已固化至 <code>.bz/95_kaoyan_考研/kaoyan_rbac_accounts_ssot.json</code>、<code>.governance/kaoyan_rbac_accounts_ssot.json</code> 及第 33 号四模态大典。</p></div>
  </div>
  <script>function setTheme(t){{document.documentElement.setAttribute('data-theme',t);localStorage.setItem('bz33_theme',t);}}</script>
</body></html>
"""
    (HERE / f"{STEM}.html").write_text(html_str, encoding="utf-8")


def main() -> int:
    build_svg_and_png()
    build_pptx()
    build_html()
    if BRAIN_DIR.is_dir():
        for ext in (".md", ".svg", ".png", ".pptx", ".html"):
            src = HERE / f"{STEM}{ext}"
            if src.is_file():
                shutil.copy2(src, BRAIN_DIR / src.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
