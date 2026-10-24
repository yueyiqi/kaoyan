#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Kaoyan English Hub v3.0 — Modular Monolith Micro-Kernel with Dual-Engine HA (PostgreSQL 18 Primary + SQLite WAL Standby)

from __future__ import annotations

import hashlib
import hmac
import json
import math
import os
import re
import sqlite3
import time
import uuid
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from kaoyan_schema import ensure_schema, ensure_pg_schema, inspect_schema

try:
    import psycopg2
    import psycopg2.extras
    HAS_PG = True
except ImportError:
    psycopg2 = None
    HAS_PG = False

BASE_DIR = Path(__file__).resolve().parent
LOCAL_SQLITE_PATH = Path(os.environ.get("KAOYAN_DB_PATH", str(BASE_DIR / "db_volume" / "kaoyan_hub.sqlite3"))).expanduser().resolve()
BACKUP_DIR = Path(os.environ.get("KAOYAN_BACKUP_DIR", str(BASE_DIR / "db_backups"))).expanduser().resolve()
HTML_PATH = Path(os.environ.get("KAOYAN_HTML_PATH", str(BASE_DIR / "index.html")))
PG_DSN = os.environ.get("KAOYAN_PG_DSN", "")

CORE_TABLES = [
    "annotation_spans",
    "api_idempotency_keys",
    "essay_corpus_snippets",
    "exam_passages",
    "ha_sync_wal_journal",
    "schema_migrations",
    "syllabus_5500_lexicon",
    "sys_users",
    "sys_roles",
    "sys_permissions",
    "sys_role_permissions",
    "sys_rbac_audit_log",
    "user_progress_anchors",
    "user_vocab_ledger",
]

RBAC_ROLES_SEED = [
    ("ADMIN", "系统管理员 (Admin)", 100, 1, "拥有全量业务读写、全量账号创建/启停/角色分配/重置密码及RBAC安全审计权限"),
    ("SCHOLAR", "正式研友学籍 (Scholar)", 50, 1, "拥有真题全文精读、个人词频账本、大作文语料、四轨导入及修改本人密码权限"),
    ("GUEST", "未登录访客 (Guest)", 10, 1, "仅限首段30%明文试读与45%毛玻璃脱敏预览，写操作与管理接口零信任硬隔离"),
]

RBAC_PERMS_SEED = [
    ("passage:read:teaser", "真题首段30%试读", "PASSAGE", "READ", "允许读取真题首段30%明文与45%脱敏毛玻璃预览"),
    ("passage:read:full", "真题全文与批注精读", "PASSAGE", "READ", "允许读取100%真题全文、句法树拆解与个人精读批注"),
    ("vocab:write:own", "个人生词账本读写", "VOCAB", "WRITE", "允许划词记入生词账本、艾宾浩斯紧迫度打分与排序"),
    ("essay:write:own", "个人作文语料读写", "ESSAY", "WRITE", "允许升格真题长难句至作文库及保存草稿"),
    ("ingest:write:own", "四轨导入中心写入", "INGEST", "WRITE", "允许导入新真题篇章、批量CSV词表与导出便携包"),
    ("account:password:self", "修改本人登录密码", "ACCOUNT", "WRITE", "允许校验原密码后更新本人PBKDF2密码哈希与轮换令牌"),
    ("admin:user:list", "查看全量账号台账", "RBAC_ADMIN", "READ", "管理员查看全部注册账号、角色、状态与脱敏密码掩码"),
    ("admin:user:create", "手工添加新账号", "RBAC_ADMIN", "MANAGE", "管理员手工创建普通研友(SCHOLAR)或管理员(ADMIN)账号"),
    ("admin:user:password_reset", "重置任意账号密码", "RBAC_ADMIN", "MANAGE", "管理员强制重置指定账号密码并使其旧会话失效"),
    ("admin:user:role_status", "切换角色与账号启停", "RBAC_ADMIN", "MANAGE", "管理员修改账号角色(ADMIN/SCHOLAR)或启停状态(ACTIVE/DISABLED)"),
    ("admin:rbac:audit", "查看RBAC矩阵与安全审计", "RBAC_ADMIN", "AUDIT", "管理员查看五表RBAC关系矩阵与敏感操作安全审计流水"),
]

RBAC_ROLE_PERMS_MAP = {
    "GUEST": ["passage:read:teaser"],
    "SCHOLAR": [
        "passage:read:teaser",
        "passage:read:full",
        "vocab:write:own",
        "essay:write:own",
        "ingest:write:own",
        "account:password:self",
    ],
    "ADMIN": [
        "passage:read:teaser",
        "passage:read:full",
        "vocab:write:own",
        "essay:write:own",
        "ingest:write:own",
        "account:password:self",
        "admin:user:list",
        "admin:user:create",
        "admin:user:password_reset",
        "admin:user:role_status",
        "admin:rbac:audit",
    ],
}

# Pre-computed PBKDF2-HMAC-SHA256 (10,000 iterations) digests — zero plaintext passwords in code
SEED_USERS = [
    (
        "admin",
        "系统管理员 (admin)",
        "ADMIN",
        "ACTIVE",
        "salt_admin_2026",
        "d567d098a5c267dcff373bd8b43aa54e020a38af87db169e1e6f940ff3aefa4c",
        "kaoyan-admin-admin-650d6d7f095e7b3a",
        2,
        30,
    ),
    (
        "commander",
        "集群统帅管理员 (commander)",
        "ADMIN",
        "ACTIVE",
        "salt_cmd_2026",
        "b698890defe2ff1fb8078c7d283e0268dda519fa12c8862f70fc3dd6c2255783",
        "kaoyan-admin-commander-76edc95f69143d12",
        2,
        30,
    ),
    (
        "colleague_a",
        "同事 A (考研英语主理人)",
        "SCHOLAR",
        "ACTIVE",
        "salt_cola_2026",
        "9dc7c79a7ef68a4a86304d2d61c44411c5ef6935721d4f47023580b202519333",
        "kaoyan-scholar-colleague_a-dbc344e7e08ea543",
        2,
        12,
    ),
    (
        "scholar_b",
        "研友协作学籍 (scholar_b)",
        "SCHOLAR",
        "ACTIVE",
        "salt_schb_2026",
        "f2b7a73a26d66873bf248bca3ffa5fa7759124cd915687cd3b9632830dfd845d",
        "kaoyan-scholar-scholar_b-76b02df956732f3e",
        1,
        5,
    ),
]


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def hash_passcode(raw_pw: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", raw_pw.encode("utf-8"), salt.encode("utf-8"), 10000).hex()


def verify_passcode(raw_pw: str, stored_hash: str, salt: str) -> bool:
    if not raw_pw or not stored_hash:
        return False
    pbk = hash_passcode(raw_pw, salt or "kaoyan_salt_2026")
    sha = hashlib.sha256(raw_pw.encode("utf-8")).hexdigest()
    return (
        hmac.compare_digest(pbk, stored_hash)
        or hmac.compare_digest(sha, stored_hash)
        or hmac.compare_digest(raw_pw, stored_hash)
    )
