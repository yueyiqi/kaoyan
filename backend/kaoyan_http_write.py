"""Business write routes with shared authentication and idempotency contract."""
from __future__ import annotations
from kaoyan_runtime import hashlib, json, now_str, re, time, uuid
from kaoyan_repository import REPO
from kaoyan_auth import calc_ebbinghaus_urgency, generate_cloze_pattern, verify_bearer

class WriteHandlerMixin:
    def do_POST(self):
        t0 = time.perf_counter()
        req_id = self.headers.get("X-Request-ID", f"req-{uuid.uuid4().hex[:12]}")
        sim_down = self.headers.get("X-Simulate-PG-Down", "0") == "1"
        idem_key = self.headers.get("X-Idempotency-Key", "").strip()
        client_ip = self.headers.get("X-Forwarded-For", self.client_address[0] if self.client_address else "127.0.0.1")

        length = int(self.headers.get("Content-Length", "0"))
        if length > 2 * 1024 * 1024:
            return self._send_json(413, {"status": "payload_too_large", "message": "Request payload exceeds 2MB limit"}, req_id=req_id, t0=t0)
        raw = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        try:
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError("JSON root must be object")
        except Exception:
            return self._send_json(400, {"status": "bad_request", "message": "Invalid JSON payload"}, req_id=req_id, t0=t0)

        now = now_str()

        if self.path in ('/api/auth/login', '/api/auth/password/change', '/api/admin/users', '/api/auth/user/create', '/api/admin/users/password', '/api/admin/users/role_status'):
            return self._post_account(data, now, req_id, t0, sim_down, client_ip)

        uid = verify_bearer(self.headers, simulate_pg_down=sim_down)
        if not uid:
            return self._send_json(
                401,
                {"status": "guest_sandbox_locked", "message": "当前为访客只读沙箱，请先登录专属学籍账号以写入云端数据库"},
                req_id=req_id,
                t0=t0,
            )

        req_hash = hashlib.sha256(f"{uid}:{self.path}:{raw}".encode("utf-8")).hexdigest()
        if idem_key:
            sconn = REPO.get_sqlite_conn()
            existing = sconn.execute(
                "SELECT req_hash, resp_code, resp_body_json FROM api_idempotency_keys WHERE idempotency_key = ?",
                (idem_key,),
            ).fetchone()
            sconn.close()
            if existing:
                if existing["req_hash"] != req_hash:
                    return self._send_json(409, {"status": "idempotency_conflict", "message": "Idempotency key reused with different payload"}, req_id=req_id, t0=t0)
                cached_body = json.loads(existing["resp_body_json"])
                cached_body["idempotent_replay"] = True
                return self._send_json(existing["resp_code"], cached_body, req_id=req_id, t0=t0, idem_replay=True)

        def finalize_write(code: int, resp_payload: dict, op_type: str, tbl: str, pk: str, pg_ok: bool):
            tx_id = REPO.record_ha_wal(op_type, tbl, pk, data, pg_ok, True)
            resp_payload["tx_uuid"] = tx_id
            resp_payload["engine"] = "postgresql_18_primary" if pg_ok else "sqlite_wal_hot_standby_failover"
            if idem_key:
                raw_resp = json.dumps(resp_payload, ensure_ascii=False)
                sconn = REPO.get_sqlite_conn()
                sconn.execute(
                    "INSERT OR REPLACE INTO api_idempotency_keys VALUES (?,?,?,?,?,?,?)",
                    (idem_key, uid, self.path, req_hash, code, raw_resp, now),
                )
                sconn.commit()
                sconn.close()
                if pg_ok:
                    pconn = REPO.get_pg_conn(simulate_down=sim_down)
                    if pconn is not None:
                        try:
                            with pconn:
                                with pconn.cursor() as cur:
                                    cur.execute(
                                        "INSERT INTO api_idempotency_keys VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (idempotency_key) DO NOTHING",
                                        (idem_key, uid, self.path, req_hash, code, raw_resp, now),
                                    )
                        finally:
                            pconn.close()
            return self._send_json(code, resp_payload, req_id=req_id, t0=t0, engine_hdr=resp_payload["engine"])

        if self.path == "/api/progress/anchor":
            try:
                para_idx = int(data.get("last_para_idx", 2))
            except Exception:
                return self._send_json(400, {"status": "bad_request", "message": "last_para_idx must be integer"}, req_id=req_id, t0=t0)
            if para_idx < 0 or para_idx > 200:
                return self._send_json(422, {"status": "validation_error", "message": "last_para_idx out of valid range [0, 200]"}, req_id=req_id, t0=t0)
            span_id = str(data.get("last_span_id", "sp-sent-1"))[:64]
            passage_id = str(data.get("last_passage_id", "P2024_EN1_T1"))[:64]

            sconn = REPO.get_sqlite_conn()
            sconn.execute(
                "UPDATE user_progress_anchors SET last_passage_id = ?, last_para_idx = ?, last_span_id = ?, rev_no = rev_no + 1, updated_at = ? WHERE user_id = ?",
                (passage_id, para_idx, span_id, now, uid),
            )
            sconn.commit()
            row = sconn.execute("SELECT rev_no FROM user_progress_anchors WHERE user_id = ?", (uid,)).fetchone()
            rev_no = row["rev_no"] if row else 1
            sconn.close()

            pg_ok = False
            pconn = REPO.get_pg_conn(simulate_down=sim_down)
            if pconn is not None:
                try:
                    with pconn:
                        with pconn.cursor() as cur:
                            cur.execute(
                                "UPDATE user_progress_anchors SET last_passage_id = %s, last_para_idx = %s, last_span_id = %s, rev_no = rev_no + 1, updated_at = %s WHERE user_id = %s",
                                (passage_id, para_idx, span_id, now, uid),
                            )
                    pg_ok = True
                finally:
                    pconn.close()

            return finalize_write(
                200,
                {"status": "ok", "user_id": uid, "last_passage_id": passage_id, "last_para_idx": para_idx, "rev_no": rev_no},
                "UPDATE_ANCHOR",
                "user_progress_anchors",
                uid,
                pg_ok,
            )

        if self.path == "/api/ingest/passage":
            title = str(data.get("title", "")).strip()
            txt = str(data.get("raw_text", "")).strip()
            if not title or len(txt) < 10:
                return self._send_json(422, {"status": "validation_error", "message": "title and raw_text (>=10 chars) are required"}, req_id=req_id, t0=t0)
            year = int(data.get("year", 2025))
            exam_type = str(data.get("exam_type", "英语一"))[:32]
            text_no = str(data.get("text_no", "Text 1"))[:32]
            h = hashlib.sha256(txt.encode("utf-8")).hexdigest()[:16]
            pid = f"P_{uid}_{h}"
            paras = [p.strip() for p in re.split(r"\n+", txt) if p.strip()]

            sconn = REPO.get_sqlite_conn()
            lex_words = {r[0] for r in sconn.execute("SELECT lemma FROM syllabus_5500_lexicon").fetchall()}
            tokens = {w.lower() for w in re.findall(r"[A-Za-z]{4,}", txt)}
            hits = sorted(lex_words.intersection(tokens))
            paras_json = json.dumps(paras, ensure_ascii=False)
            hits_json = json.dumps(hits, ensure_ascii=False)

            sconn.execute(
                "INSERT OR REPLACE INTO exam_passages VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (pid, uid, year, exam_type, text_no, title, paras_json, hits_json, h, now),
            )
            sconn.commit()
            p_cnt = max(2, sconn.execute("SELECT COUNT(*) FROM exam_passages").fetchone()[0])
            sconn.close()

            pg_ok = False
            pconn = REPO.get_pg_conn(simulate_down=sim_down)
            if pconn is not None:
                try:
                    with pconn:
                        with pconn.cursor() as cur:
                            cur.execute(
                                "INSERT INTO exam_passages (passage_id, owner_user_id, year, exam_type, text_no, title, paragraphs_json, syllabus_hits_json, sha256_hash, created_at) "
                                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
                                "ON CONFLICT (passage_id) DO UPDATE SET title = EXCLUDED.title, paragraphs_json = EXCLUDED.paragraphs_json, syllabus_hits_json = EXCLUDED.syllabus_hits_json",
                                (pid, uid, year, exam_type, text_no, title, paras_json, hits_json, h, now),
                            )
                    pg_ok = True
                finally:
                    pconn.close()

            return finalize_write(
                200,
                {"status": "ok", "passage_id": pid, "user_id": uid, "passage_count": p_cnt, "syllabus_hits": hits, "sha256_hash": h},
                "INGEST_PASSAGE",
                "exam_passages",
                pid,
                pg_ok,
            )

        if self.path in ("/api/ingest/vocab", "/api/vocab/lookup"):
            raw_csv = str(data.get("raw_csv", "")).strip()
            if raw_csv:
                sconn = REPO.get_sqlite_conn()
                ingested_items = []
                for ln in re.split(r"\n+", raw_csv):
                    parts = [x.strip() for x in ln.split(",") if x.strip()]
                    if len(parts) >= 2:
                        w = re.sub(r"[^a-zA-Z\-]", "", parts[0]).lower()
                        if len(w) < 2:
                            continue
                        meaning = parts[1][:512]
                        try:
                            cnt = max(1, int(parts[2])) if len(parts) >= 3 else 1
                        except Exception:
                            cnt = 1
                        tier = (parts[3] if len(parts) >= 4 else "CORE_1800")[:32]
                        urg = calc_ebbinghaus_urgency(cnt, 0.2, tier)
                        sconn.execute(
                            "INSERT INTO user_vocab_ledger (user_id, lemma, syllabus_tier, lookup_count, last_seen_at, days_since_seen, urgency_score, exam_source, contextual_meaning, mastery_state) "
                            "VALUES (?, ?, ?, ?, ?, 0.2, ?, '批量词表导入', ?, 'LEARNING') "
                            "ON CONFLICT(user_id, lemma) DO UPDATE SET lookup_count = user_vocab_ledger.lookup_count + ?, last_seen_at = excluded.last_seen_at, urgency_score = ?, contextual_meaning = excluded.contextual_meaning",
                            (uid, w, tier, cnt, now, urg, meaning, cnt, urg),
                        )
                        ingested_items.append((uid, w, tier, cnt, now, urg, meaning))
                sconn.commit()
                sconn.close()
                pg_ok = False
                pconn = REPO.get_pg_conn(simulate_down=sim_down)
                if pconn is not None and ingested_items:
                    try:
                        with pconn:
                            with pconn.cursor() as cur:
                                for uid_i, w_i, tier_i, cnt_i, now_i, urg_i, meaning_i in ingested_items:
                                    cur.execute(
                                        "INSERT INTO user_vocab_ledger (user_id, lemma, syllabus_tier, lookup_count, last_seen_at, days_since_seen, urgency_score, exam_source, contextual_meaning, mastery_state) "
                                        "VALUES (%s,%s,%s,%s,%s,0.2,%s,'批量词表导入',%s,'LEARNING') "
                                        "ON CONFLICT (user_id, lemma) DO UPDATE SET lookup_count = user_vocab_ledger.lookup_count + EXCLUDED.lookup_count, last_seen_at = EXCLUDED.last_seen_at, urgency_score = EXCLUDED.urgency_score, contextual_meaning = EXCLUDED.contextual_meaning",
                                        (uid_i, w_i, tier_i, cnt_i, now_i, urg_i, meaning_i),
                                    )
                        pg_ok = True
                    finally:
                        pconn.close()
                return finalize_write(
                    200,
                    {"status": "ok", "user_id": uid, "ingested_count": len(ingested_items)},
                    "VOCAB_BULK_CSV_INGEST",
                    "user_vocab_ledger",
                    f"{uid}:bulk:{len(ingested_items)}",
                    pg_ok,
                )

            lemma = str(data.get("lemma", "")).strip().lower()
            if not lemma or not re.match(r"^[a-zA-Z\-]{2,45}$", lemma):
                return self._send_json(422, {"status": "validation_error", "message": "Invalid English lemma (2..45 letters)"}, req_id=req_id, t0=t0)
            tier = str(data.get("syllabus_tier", "CORE_1800"))[:32]
            days_ago = float(data.get("days_since_seen", 0.5))
            exam_src = str(data.get("exam_source", "真题实时查词"))[:128]
            ctx_meaning = str(data.get("contextual_meaning", "学籍云端同步词条"))[:512]

            sconn = REPO.get_sqlite_conn()
            cur_row = sconn.execute("SELECT lookup_count FROM user_vocab_ledger WHERE user_id = ? AND lemma = ?", (uid, lemma)).fetchone()
            new_cnt = (cur_row["lookup_count"] + 1) if cur_row else int(data.get("lookup_count", 1))
            urg = calc_ebbinghaus_urgency(new_cnt, days_ago, tier)

            sconn.execute(
                "INSERT INTO user_vocab_ledger (user_id, lemma, syllabus_tier, lookup_count, last_seen_at, days_since_seen, urgency_score, exam_source, contextual_meaning, mastery_state) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'LEARNING') "
                "ON CONFLICT(user_id, lemma) DO UPDATE SET lookup_count = ?, last_seen_at = excluded.last_seen_at, days_since_seen = excluded.days_since_seen, urgency_score = ?, contextual_meaning = excluded.contextual_meaning",
                (uid, lemma, tier, new_cnt, now, days_ago, urg, exam_src, ctx_meaning, new_cnt, urg),
            )
            sconn.commit()
            sconn.close()

            pg_ok = False
            pconn = REPO.get_pg_conn(simulate_down=sim_down)
            if pconn is not None:
                try:
                    with pconn:
                        with pconn.cursor() as cur:
                            cur.execute(
                                "INSERT INTO user_vocab_ledger (user_id, lemma, syllabus_tier, lookup_count, last_seen_at, days_since_seen, urgency_score, exam_source, contextual_meaning, mastery_state) "
                                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'LEARNING') "
                                "ON CONFLICT (user_id, lemma) DO UPDATE SET lookup_count = EXCLUDED.lookup_count, last_seen_at = EXCLUDED.last_seen_at, days_since_seen = EXCLUDED.days_since_seen, urgency_score = EXCLUDED.urgency_score, contextual_meaning = EXCLUDED.contextual_meaning",
                                (uid, lemma, tier, new_cnt, now, days_ago, urg, exam_src, ctx_meaning),
                            )
                    pg_ok = True
                finally:
                    pconn.close()

            return finalize_write(
                200,
                {"status": "ok", "user_id": uid, "lemma": lemma, "lookup_count": new_cnt, "urgency_score": urg, "syllabus_tier": tier},
                "VOCAB_EBBINGHAUS_UPSERT",
                "user_vocab_ledger",
                f"{uid}:{lemma}",
                pg_ok,
            )

        if self.path in ("/api/annotations/save", "/api/notes"):
            selected_text = str(data.get("selected_text", data.get("text", ""))).strip()
            if not selected_text:
                return self._send_json(422, {"status": "validation_error", "message": "selected_text cannot be empty"}, req_id=req_id, t0=t0)
            passage_id = str(data.get("passage_id", "P2024_EN1_T1"))[:64]
            granularity = str(data.get("granularity", "SENTENCE"))[:32]
            para_idx = int(data.get("para_idx", 1))
            start_offset = int(data.get("start_offset", 0))
            end_offset = int(data.get("end_offset", len(selected_text)))
            prefix_quote = str(data.get("prefix_quote", ""))[:64]
            suffix_quote = str(data.get("suffix_quote", ""))[:64]
            syntax_bd = str(data.get("syntax_breakdown", data.get("breakdown", "")))
            comment = str(data.get("user_comment", data.get("comment", "")))
            span_id = str(data.get("span_id", data.get("id", ""))).strip() or f"sp-{hashlib.sha256(f'{uid}:{passage_id}:{para_idx}:{selected_text}'.encode('utf-8')).hexdigest()[:12]}"

            sconn = REPO.get_sqlite_conn()
            sconn.execute(
                "INSERT INTO annotation_spans (span_id, user_id, passage_id, granularity, para_idx, start_offset, end_offset, selected_text, prefix_quote, suffix_quote, syntax_breakdown, user_comment, promoted_snippet_id, version, created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?, '', 1, ?) "
                "ON CONFLICT(span_id) DO UPDATE SET syntax_breakdown = excluded.syntax_breakdown, user_comment = excluded.user_comment, version = annotation_spans.version + 1",
                (span_id, uid, passage_id, granularity, para_idx, start_offset, end_offset, selected_text, prefix_quote, suffix_quote, syntax_bd, comment, now),
            )
            sconn.commit()
            sconn.close()

            pg_ok = False
            pconn = REPO.get_pg_conn(simulate_down=sim_down)
            if pconn is not None:
                try:
                    with pconn:
                        with pconn.cursor() as cur:
                            cur.execute(
                                "INSERT INTO annotation_spans (span_id, user_id, passage_id, granularity, para_idx, start_offset, end_offset, selected_text, prefix_quote, suffix_quote, syntax_breakdown, user_comment, promoted_snippet_id, version, created_at) "
                                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'',1,%s) "
                                "ON CONFLICT (span_id) DO UPDATE SET syntax_breakdown = EXCLUDED.syntax_breakdown, user_comment = EXCLUDED.user_comment, version = annotation_spans.version + 1",
                                (span_id, uid, passage_id, granularity, para_idx, start_offset, end_offset, selected_text, prefix_quote, suffix_quote, syntax_bd, comment, now),
                            )
                    pg_ok = True
                finally:
                    pconn.close()

            return finalize_write(
                200,
                {"status": "ok", "span_id": span_id, "passage_id": passage_id, "granularity": granularity},
                "SAVE_ANNOTATION",
                "annotation_spans",
                span_id,
                pg_ok,
            )

        if self.path in ("/api/essay/save", "/api/annotations/promote", "/api/essay"):
            span_id = str(data.get("span_id", data.get("id", ""))).strip()
            theme_tag = str(data.get("theme_tag", data.get("theme", "科技创新与AI伦理")))[:64]
            func_slot = str(data.get("func_slot", data.get("slot", "段首论点引入 (Topic Opener)")))[:64]
            content_en = str(data.get("content_en", data.get("en", ""))).strip()
            translation_zh = str(data.get("translation_zh", data.get("zh", ""))).strip() or "阅读精读笔记一键升格语料"
            granularity = str(data.get("granularity", "SENTENCE"))[:32]
            source_ref = str(data.get("source_ref", "2024 英语一 Text 1"))[:128]

            sconn = REPO.get_sqlite_conn()
            if self.path == "/api/annotations/promote" and span_id and not content_en:
                sp_row = sconn.execute("SELECT * FROM annotation_spans WHERE span_id = ?", (span_id,)).fetchone()
                if not sp_row:
                    sconn.close()
                    return self._send_json(404, {"status": "not_found", "message": f"Annotation span {span_id} not found"}, req_id=req_id, t0=t0)
                content_en = sp_row["selected_text"]
                translation_zh = sp_row["user_comment"] or sp_row["syntax_breakdown"] or translation_zh
                granularity = sp_row["granularity"]
                source_ref = f"Promoted from {sp_row['passage_id']} (span:{span_id})"

            if not content_en:
                sconn.close()
                return self._send_json(422, {"status": "validation_error", "message": "content_en or valid span_id is required"}, req_id=req_id, t0=t0)

            cloze = str(data.get("cloze_pattern", "")).strip() or generate_cloze_pattern(content_en)
            snippet_id = str(data.get("snippet_id", data.get("id", ""))).strip() or f"es-{hashlib.sha256(f'{uid}:{theme_tag}:{content_en}'.encode('utf-8')).hexdigest()[:12]}"

            sconn.execute(
                "INSERT INTO essay_corpus_snippets (snippet_id, user_id, theme_tag, func_slot, granularity, content_en, cloze_pattern, translation_zh, source_ref, usage_count, created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?, 1, ?) "
                "ON CONFLICT(snippet_id) DO UPDATE SET theme_tag = excluded.theme_tag, func_slot = excluded.func_slot, cloze_pattern = excluded.cloze_pattern, usage_count = essay_corpus_snippets.usage_count + 1",
                (snippet_id, uid, theme_tag, func_slot, granularity, content_en, cloze, translation_zh, source_ref, now),
            )
            if span_id:
                sconn.execute("UPDATE annotation_spans SET promoted_snippet_id = ? WHERE span_id = ?", (snippet_id, span_id))
            sconn.commit()
            sconn.close()

            pg_ok = False
            pconn = REPO.get_pg_conn(simulate_down=sim_down)
            if pconn is not None:
                try:
                    with pconn:
                        with pconn.cursor() as cur:
                            cur.execute(
                                "INSERT INTO essay_corpus_snippets (snippet_id, user_id, theme_tag, func_slot, granularity, content_en, cloze_pattern, translation_zh, source_ref, usage_count, created_at) "
                                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,1,%s) "
                                "ON CONFLICT (snippet_id) DO UPDATE SET theme_tag = EXCLUDED.theme_tag, func_slot = EXCLUDED.func_slot, cloze_pattern = EXCLUDED.cloze_pattern, usage_count = essay_corpus_snippets.usage_count + 1",
                                (snippet_id, uid, theme_tag, func_slot, granularity, content_en, cloze, translation_zh, source_ref, now),
                            )
                            if span_id:
                                cur.execute("UPDATE annotation_spans SET promoted_snippet_id = %s WHERE span_id = %s", (snippet_id, span_id))
                    pg_ok = True
                finally:
                    pconn.close()

            return finalize_write(
                200,
                {"status": "ok", "snippet_id": snippet_id, "promoted_from_span_id": span_id, "theme_tag": theme_tag, "cloze_pattern": cloze},
                "SAVE_OR_PROMOTE_ESSAY",
                "essay_corpus_snippets",
                snippet_id,
                pg_ok,
            )

        return self._send_json(404, {"status": "not_found", "message": "Unknown API endpoint"}, req_id=req_id, t0=t0)
