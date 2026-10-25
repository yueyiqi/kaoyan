"""Read routes and response formatting; preserves existing endpoint contracts."""
from __future__ import annotations
from kaoyan_runtime import CORE_TABLES, HTML_PATH, RBAC_ROLE_PERMS_MAP, annotations, json, parse_qs, psycopg2, time, urlparse, uuid
from kaoyan_repository import REPO
from kaoyan_auth import build_admin_db_drilldown_payload, build_eids_lineage_payload, get_role_permissions, get_session_user, mask_sensitive_row_fields, require_admin, verify_bearer

class ReadHandlerMixin:
    def log_message(self, format, *args):
        return

    def _send_json(self, code: int, payload: dict, req_id: str = "", t0: float = 0.0, engine_hdr: str = "pg18+sqlite_wal", idem_replay: bool = False):
        if req_id:
            payload.setdefault("request_id", req_id)
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        if req_id:
            self.send_header("X-Request-ID", req_id)
        if t0 > 0:
            lat_str = str(round((time.perf_counter() - t0) * 1000, 2))
            self.send_header("X-Response-Time-Ms", lat_str)
            self.send_header("X-Latency-Ms", lat_str)
        self.send_header("X-DB-Engine", engine_hdr)
        if idem_replay:
            self.send_header("X-Idempotent-Replay", "true")
        self.end_headers()
        self.wfile.write(body)

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

    def do_GET(self):
        t0 = time.perf_counter()
        req_id = self.headers.get("X-Request-ID", f"req-{uuid.uuid4().hex[:12]}")
        sim_down = self.headers.get("X-Simulate-PG-Down", "0") == "1"
        parsed = urlparse(self.path)

        # Layer 2 Security: Block automated vulnerability scanner probes (.env, .sql, .php, .bak, etc.)
        lower_p = parsed.path.lower()
        if any(lower_p.endswith(ext) for ext in (".sql", ".bak", ".php", ".ini", ".yml", ".yaml", ".properties", ".env", ".envrc")) or "/.env" in lower_p or "/.git" in lower_p:
            return self._send_json(404, {"status": "not_found"}, req_id=req_id, t0=t0)

        if parsed.path == "/api/health":
            ha = REPO.get_ha_status(simulate_pg_down=sim_down)
            return self._send_json(
                200 if ha["sqlite_standby_online"] else 503,
                {
                    "status": ha["status"],
                    "service": "kaoyan-english-hub-v3-pg-ha",
                    "domain": "kaoyan.elenalyl.top",
                    "containerized": True,
                    "db_engine": ha["active_engine"],
                    "ha_mode": ha["ha_mode"],
                    "pg_primary_online": ha["pg_primary_online"],
                    "sqlite_standby_online": ha["sqlite_standby_online"],
                    "tables_count": len(CORE_TABLES),
                    "tables": CORE_TABLES,
                },
                req_id=req_id,
                t0=t0,
                engine_hdr=ha["active_engine"],
            )

        if parsed.path == "/api/ha/status":
            ha = REPO.get_ha_status(simulate_pg_down=sim_down)
            return self._send_json(200 if ha["sqlite_standby_online"] else 503, ha, req_id=req_id, t0=t0, engine_hdr=ha["active_engine"])

        if parsed.path in ("/api/bootstrap", "/api/state", "/api/passages", "/api/annotations/list", "/api/essay/list"):
            qs = parse_qs(parsed.query)
            verified_uid = verify_bearer(self.headers, simulate_pg_down=sim_down)
            passage_id = qs.get("passage_id", ["P2024_EN1_T1"])[0]
            theme_filter = qs.get("theme_tag", [""])[0]

            pconn = REPO.get_pg_conn(simulate_down=sim_down)
            engine_used = "postgresql_18_primary" if pconn is not None else "sqlite_wal_hot_standby_failover"

            if not verified_uid:
                if pconn is not None:
                    try:
                        pconn.close()
                    except Exception:
                        pass
                guest_passages = [
                    {
                        "passage_id": "P2024_EN1_T1",
                        "year": 2024,
                        "exam_type": "英语一",
                        "text_no": "Text 1",
                        "title": "2024 考研英语一 Text 1 (访客 30% 公开试读样章)",
                        "cleartext_para_1": "In recent decades, the relationship between intellectual history and the broader humanities has undergone a profound transformation. The modern university structure segments knowledge into narrow compartments, making it increasingly perilous for scholars to venture beyond their fortified disciplinary boundaries.",
                        "blurred_para_2_teaser": "While empirical specialization has undoubtedly accelerated... [🔒 访客免费试读已达 30% 阈值：后端 API 已硬截断后续段落，请登录学籍解锁 Para 2~5 全文、熟词僻义预警与五维进度锚点]",
                        "is_truncated": True,
                    }
                ]
                guest_annotations = [
                    {
                        "id": "sp-para-1",
                        "granularity": "PARAGRAPH",
                        "tag": "🟣 段落主旨卡 [Para 1 · 公开试读 1/2]",
                        "text": "Para 1: 现代大学学科壁垒割裂了知识体系，导致学者跨学科探索面临风险。",
                        "breakdown": "【篇章功能】开篇立论（欲抑先扬）：指出 narrow compartments 对跨学科知识分子的束缚。",
                        "comment": "常考态度题：作者对过度学科细分持批判态度 (critical / skeptical)。",
                        "is_blurred": False,
                    },
                    {
                        "id": "sp-sent-1",
                        "granularity": "SENTENCE",
                        "tag": "🔵 长难句解剖卡 [Para 1 · 公开试读 2/2]",
                        "text": "The modern university structure segments knowledge into narrow compartments, making it increasingly perilous for scholars to venture beyond their fortified disciplinary boundaries.",
                        "breakdown": "【主干】structure segments knowledge | 【分词结果状语】making it perilous for scholars to venture beyond...",
                        "comment": "绝佳写作句式！可改写用于【教育文化/科技创新】大作文。",
                        "is_blurred": False,
                    },
                    {
                        "id": "sp-sent-2-redacted",
                        "granularity": "SENTENCE",
                        "tag": "🔒 长难句解剖卡 [Para 2 · 45% 毛玻璃预览]",
                        "text": "While empirical specialization has undoubtedly accelerated technical breakthroughs, it often fails to accommodate broader philosophical inquiry.",
                        "breakdown": "【让步状语从句】While empirical specialization has... | 【主干】it fails to accommodate... (服务端脱敏样板 ██)",
                        "comment": "🔒 登录学籍后解锁完整句法切分与双刃剑论证升格模板",
                        "is_blurred": True,
                    },
                    {
                        "id": "sp-word-1-redacted",
                        "granularity": "WORD",
                        "tag": "🔒 真题熟词僻义卡 [Para 2 · 45% 毛玻璃预览]",
                        "text": "accommodate / empirical (考研高频熟词僻义陷阱)",
                        "breakdown": "【熟词僻义预警】考研阅读常考『容纳、顾及、顺应』之意，切忌死背基础词义 (服务端脱敏样板 ██)",
                        "comment": "🔒 登录学籍后解锁个人真题语境查词频次与艾宾浩斯复习锚点",
                        "is_blurred": True,
                    },
                ]
                guest_vocab = [
                    {
                        "word": "accommodate",
                        "lemma": "accommodate",
                        "syllabus_tier": "POLYSEMY_TRAP",
                        "lookup_count": "5",
                        "days_since_seen": 0.0,
                        "last_seen_at": "2026-10-20",
                        "exam_source": "2022 英语一 Text 2 Para 3 (公共考纲样板)",
                        "contextual_meaning": "v. 适应，顺应；容纳，顾及（考研熟词僻义：非仅提供食宿）",
                        "urgency_score": "0.85",
                        "is_blurred": False,
                    },
                    {
                        "word": "intellectual",
                        "lemma": "intellectual",
                        "syllabus_tier": "CORE_1800",
                        "lookup_count": "4",
                        "days_since_seen": 0.0,
                        "last_seen_at": "2026-10-21",
                        "exam_source": "2024 英语一 Text 1 Para 1 (公共考纲样板)",
                        "contextual_meaning": "adj. 智力的，理智的；n. 知识分子",
                        "urgency_score": "0.69",
                        "is_blurred": False,
                    },
                    {
                        "word": "empirical",
                        "lemma": "empirical",
                        "syllabus_tier": "CORE_1800",
                        "lookup_count": "3",
                        "days_since_seen": 0.0,
                        "last_seen_at": "2026-10-18",
                        "exam_source": "2023 英语一 Text 3 Para 2",
                        "contextual_meaning": "adj. 实证的，以经验或观察为依据的（反义：theoretical · 脱敏样板 ██）",
                        "urgency_score": "0.74",
                        "is_blurred": True,
                    },
                    {
                        "word": "archaeology",
                        "lemma": "archaeology",
                        "syllabus_tier": "EXT_HYPER",
                        "lookup_count": "2",
                        "days_since_seen": 0.0,
                        "last_seen_at": "2026-10-22",
                        "exam_source": "2024 英语一 Text 1 Para 2",
                        "contextual_meaning": "n. 考古学；文化遗迹研究（个人真题生词账本 · 脱敏样板 ██）",
                        "urgency_score": "0.42",
                        "is_blurred": True,
                    },
                ]
                guest_essays = [
                    {
                        "id": "ec-1",
                        "theme": "科技创新",
                        "slot": "第一段·图画图表描述",
                        "gran": "模板骨架 (公开样板)",
                        "en": "As is vividly depicted in the cartoon, the rapid proliferation of artificial intelligence has sparked heated debate.",
                        "cloze": "As is [vividly depicted] in the cartoon, the [rapid proliferation] of artificial intelligence has [sparked heated debate].",
                        "zh": "正如漫画生动描绘的那样，人工智能的迅猛普及引发了激烈讨论。",
                        "source": "2024 英语一大作文公开样板",
                        "is_blurred": False,
                    },
                    {
                        "id": "ec-2-redacted",
                        "theme": "科技创新",
                        "slot": "第二段·原因与正反论证",
                        "gran": "🔒 真题升格长难句",
                        "en": "While technological specialization has undoubtedly accelerated breakthroughs, it often fails to accommodate broader ethical questions.",
                        "cloze": "[While] technological specialization has [accelerated breakthroughs], it often [fails to accommodate] broader ethical questions.",
                        "zh": "尽管技术专门化加速了突破，但往往未能顾及更广泛的伦理问题（服务端脱敏样板 ██）",
                        "source": "🔒 登录学籍解锁",
                        "is_blurred": True,
                    },
                    {
                        "id": "ec-3-redacted",
                        "theme": "教育文化",
                        "slot": "第二段·原因与正反论证",
                        "gran": "🔒 真题升格长难句",
                        "en": "Rigid compartmentalization of knowledge makes it perilous for young minds to venture beyond conventional boundaries.",
                        "cloze": "Rigid [compartmentalization] of knowledge makes it [perilous] for young minds to venture beyond.",
                        "zh": "知识的僵化割裂使得青年学者跨越传统边界变得困难重重（服务端脱敏样板 ██）",
                        "source": "🔒 登录学籍解锁",
                        "is_blurred": True,
                    },
                ]
                if parsed.path == "/api/passages":
                    return self._send_json(200, {"status": "ok", "auth_tier": "GUEST_TEASER", "engine": engine_used, "passages": guest_passages}, req_id=req_id, t0=t0, engine_hdr=engine_used)
                if parsed.path == "/api/annotations/list":
                    return self._send_json(200, {"status": "ok", "auth_tier": "GUEST_TEASER", "engine": engine_used, "annotations": guest_annotations}, req_id=req_id, t0=t0, engine_hdr=engine_used)
                if parsed.path == "/api/essay/list":
                    return self._send_json(200, {"status": "ok", "auth_tier": "GUEST_TEASER", "engine": engine_used, "essays": guest_essays}, req_id=req_id, t0=t0, engine_hdr=engine_used)
                return self._send_json(
                    200,
                    {
                        "status": "ok",
                        "auth_tier": "GUEST_TEASER",
                        "exposure_policy": {
                            "cleartext_ratio_pct": 30,
                            "blurred_teaser_pct": 45,
                            "hard_locked_pct": 25,
                            "strategy": "HYBRID_API_TRUNCATION_GRADIENT_AND_FROSTED_BLUR",
                        },
                        "engine": engine_used,
                        "user_id": "guest",
                        "passage_count": 2,
                        "passages": guest_passages,
                        "anchor": {
                            "last_para_idx": None,
                            "streak_days": None,
                            "rev_no": 0,
                            "masked_label": "Para * · 连续 ** 天 (🔒登录解锁)",
                        },
                        "vocab": guest_vocab,
                        "annotations": guest_annotations,
                        "essays": guest_essays,
                    },
                    req_id=req_id,
                    t0=t0,
                    engine_hdr=engine_used,
                )

            uid = verified_uid
            if pconn is not None:
                try:
                    with pconn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                        cur.execute("SELECT COUNT(*) AS cnt FROM exam_passages;")
                        p_cnt = max(2, cur.fetchone()["cnt"])
                        cur.execute("SELECT * FROM exam_passages ORDER BY year DESC, created_at DESC LIMIT 20;")
                        passages = [dict(r) for r in cur.fetchall()]
                        cur.execute("SELECT * FROM user_progress_anchors WHERE user_id = %s;", (uid,))
                        anchor_row = cur.fetchone()
                        cur.execute(
                            "SELECT lemma AS word, lemma, syllabus_tier, lookup_count, last_seen_at, days_since_seen, urgency_score, exam_source, contextual_meaning, mastery_state FROM user_vocab_ledger WHERE user_id = %s ORDER BY urgency_score DESC, lookup_count DESC;",
                            (uid,),
                        )
                        vocab_rows = [dict(r) for r in cur.fetchall()]
                        cur.execute(
                            "SELECT * FROM annotation_spans WHERE user_id = %s AND passage_id = %s ORDER BY para_idx ASC, start_offset ASC;",
                            (uid, passage_id),
                        )
                        annotations = [dict(r) for r in cur.fetchall()]
                        if theme_filter:
                            cur.execute(
                                "SELECT * FROM essay_corpus_snippets WHERE user_id = %s AND theme_tag = %s ORDER BY created_at DESC;",
                                (uid, theme_filter),
                            )
                        else:
                            cur.execute("SELECT * FROM essay_corpus_snippets WHERE user_id = %s ORDER BY created_at DESC;", (uid,))
                        essays = [dict(r) for r in cur.fetchall()]
                finally:
                    pconn.close()
            else:
                sconn = REPO.get_sqlite_conn()
                p_cnt = max(2, sconn.execute("SELECT COUNT(*) FROM exam_passages").fetchone()[0])
                passages = [dict(r) for r in sconn.execute("SELECT * FROM exam_passages ORDER BY year DESC, created_at DESC LIMIT 20").fetchall()]
                anchor_row = sconn.execute("SELECT * FROM user_progress_anchors WHERE user_id = ?", (uid,)).fetchone()
                vocab_rows = [
                    dict(r)
                    for r in sconn.execute(
                        "SELECT lemma AS word, lemma, syllabus_tier, lookup_count, last_seen_at, days_since_seen, urgency_score, exam_source, contextual_meaning, mastery_state FROM user_vocab_ledger WHERE user_id = ? ORDER BY urgency_score DESC, lookup_count DESC",
                        (uid,),
                    ).fetchall()
                ]
                annotations = [
                    dict(r)
                    for r in sconn.execute(
                        "SELECT * FROM annotation_spans WHERE user_id = ? AND passage_id = ? ORDER BY para_idx ASC, start_offset ASC",
                        (uid, passage_id),
                    ).fetchall()
                ]
                if theme_filter:
                    essays = [
                        dict(r)
                        for r in sconn.execute(
                            "SELECT * FROM essay_corpus_snippets WHERE user_id = ? AND theme_tag = ? ORDER BY created_at DESC",
                            (uid, theme_filter),
                        ).fetchall()
                    ]
                else:
                    essays = [dict(r) for r in sconn.execute("SELECT * FROM essay_corpus_snippets WHERE user_id = ? ORDER BY created_at DESC", (uid,)).fetchall()]
                sconn.close()

            if parsed.path == "/api/passages":
                return self._send_json(200, {"status": "ok", "auth_tier": "SCHOLAR_FULL", "engine": engine_used, "passages": passages}, req_id=req_id, t0=t0, engine_hdr=engine_used)
            if parsed.path == "/api/annotations/list":
                return self._send_json(200, {"status": "ok", "auth_tier": "SCHOLAR_FULL", "engine": engine_used, "annotations": annotations}, req_id=req_id, t0=t0, engine_hdr=engine_used)
            if parsed.path == "/api/essay/list":
                return self._send_json(200, {"status": "ok", "auth_tier": "SCHOLAR_FULL", "engine": engine_used, "essays": essays}, req_id=req_id, t0=t0, engine_hdr=engine_used)

            return self._send_json(
                200,
                {
                    "status": "ok",
                    "auth_tier": "SCHOLAR_FULL",
                    "engine": engine_used,
                    "user_id": uid,
                    "passage_count": p_cnt,
                    "passages": passages,
                    "anchor": dict(anchor_row) if anchor_row else {"last_para_idx": 2, "streak_days": 12, "rev_no": 1},
                    "vocab": vocab_rows,
                    "annotations": annotations,
                    "essays": essays,
                },
                req_id=req_id,
                t0=t0,
                engine_hdr=engine_used,
            )

        if parsed.path in ("/", "/index.html", "/kaoyan_network.js", "/kaoyan_admin_view.js", "/kaoyan_admin.js", "/kaoyan_admin_accounts.js", "/kaoyan_login.js", "/kaoyan_eids_drilldown.js"):
            is_script = parsed.path.endswith(".js")
            html = (HTML_PATH.with_name(parsed.path.lstrip("/")) if is_script else HTML_PATH).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/javascript; charset=utf-8" if is_script else "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(html)
            return

        if parsed.path in ("/api/db/lineage", "/api/eids/drilldown"):
            ctx = get_session_user(self.headers, simulate_pg_down=sim_down)
            sconn = REPO.get_sqlite_conn()
            try:
                payload = build_eids_lineage_payload(sconn, parse_qs(parsed.query, keep_blank_values=True), ctx)
            except ValueError as exc:
                return self._send_json(400, {"status": "invalid_filter", "message": str(exc)}, req_id=req_id, t0=t0)
            finally:
                sconn.close()
            return self._send_json(200, payload, req_id=req_id, t0=t0)

        if parsed.path == "/api/auth/me":
            ctx = get_session_user(self.headers, simulate_pg_down=sim_down)
            if ctx is None:
                return self._send_json(
                    200,
                    {
                        "status": "ok",
                        "authenticated": False,
                        "user_id": "guest",
                        "display_name": "未登录访客",
                        "role": "GUEST",
                        "account_status": "GUEST_SANDBOX",
                        "permissions": get_role_permissions("GUEST"),
                    },
                    req_id=req_id,
                    t0=t0,
                )
            return self._send_json(200, {"status": "ok", "authenticated": True, **ctx}, req_id=req_id, t0=t0)

        if parsed.path in ("/api/admin/users", "/api/auth/users", "/api/admin/rbac/audit"):
            client_ip = self.headers.get("X-Forwarded-For", self.client_address[0] if self.client_address else "127.0.0.1")
            admin_ctx, code, msg = require_admin(self.headers, client_ip=client_ip, endpoint=parsed.path, simulate_pg_down=sim_down)
            if admin_ctx is None:
                return self._send_json(code, {"status": "rbac_forbidden" if code == 403 else "unauthorized", "message": msg}, req_id=req_id, t0=t0)
            sconn = REPO.get_sqlite_conn()
            u_rows = sconn.execute(
                "SELECT user_id, username, display_name, role, account_status, passcode_hash, passcode_salt, token_secret, failed_login_count, last_login_at, password_updated_at, created_by, created_at FROM sys_users ORDER BY CASE WHEN role='ADMIN' THEN 0 ELSE 1 END, created_at ASC"
            ).fetchall()
            r_rows = sconn.execute("SELECT role_code, role_name, role_level, is_system, description, created_at FROM sys_roles ORDER BY role_level DESC").fetchall()
            p_rows = sconn.execute("SELECT perm_code, perm_name, resource_domain, action_type, description FROM sys_permissions ORDER BY resource_domain ASC, perm_code ASC").fetchall()
            rp_rows = sconn.execute("SELECT role_code, perm_code, granted_at, granted_by FROM sys_role_permissions ORDER BY role_code ASC, perm_code ASC").fetchall()
            a_rows = sconn.execute("SELECT audit_id, actor_user_id, actor_role, target_user_id, action, detail_json, client_ip, created_at FROM sys_rbac_audit_log ORDER BY created_at DESC LIMIT 40").fetchall()
            sconn.close()
            users_list = []
            for r in u_rows:
                d = mask_sensitive_row_fields("sys_users", dict(r))
                d["passcode_mask"] = "PBKDF2-HMAC-SHA256 (••••••••)"
                d["password_masked"] = "••••••••"
                d["kdf_algo"] = "PBKDF2-HMAC-SHA256"
                d["permissions"] = get_role_permissions(d.get("role", "SCHOLAR"))
                users_list.append(d)
            return self._send_json(
                200,
                {
                    "status": "ok",
                    "admin_actor": admin_ctx["user_id"],
                    "users": users_list,
                    "roles": [dict(r) for r in r_rows],
                    "permissions": [dict(r) for r in p_rows],
                    "role_permissions": [dict(r) for r in rp_rows],
                    "role_permission_matrix": RBAC_ROLE_PERMS_MAP,
                    "audit_logs": [mask_sensitive_row_fields("sys_rbac_audit_log", dict(r)) for r in a_rows],
                },
                req_id=req_id,
                t0=t0,
            )

        if parsed.path in ("/api/admin/db/drilldown", "/api/admin/schema/full"):
            client_ip = self.headers.get("X-Forwarded-For", self.client_address[0] if self.client_address else "127.0.0.1")
            admin_ctx, code, msg = require_admin(self.headers, client_ip=client_ip, endpoint=parsed.path, simulate_pg_down=sim_down)
            if admin_ctx is None:
                return self._send_json(code, {"status": "rbac_forbidden" if code == 403 else "unauthorized", "message": msg}, req_id=req_id, t0=t0)
            sconn = REPO.get_sqlite_conn()
            try:
                payload = build_admin_db_drilldown_payload(sconn, parse_qs(parsed.query, keep_blank_values=True), admin_ctx["user_id"])
            except ValueError as exc:
                return self._send_json(400, {"status": "invalid_filter", "message": str(exc)}, req_id=req_id, t0=t0)
            finally:
                sconn.close()
            return self._send_json(200, payload, req_id=req_id, t0=t0)

        self._send_json(404, {"status": "not_found", "message": "Endpoint not found"}, req_id=req_id, t0=t0)
