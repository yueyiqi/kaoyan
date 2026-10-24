"""Account mutation routes retain existing authorization checks."""
from __future__ import annotations
from kaoyan_runtime import hash_passcode, hashlib, re, uuid, verify_passcode
from kaoyan_repository import REPO
from kaoyan_auth import get_role_permissions, get_session_user, record_rbac_audit, require_admin

class AccountHandlerMixin:
    def _post_account(self, data, now, req_id, t0, sim_down, client_ip):
        if self.path == "/api/auth/login":
            u = str(data.get("username") or data.get("user_id") or "").strip()
            k = str(data.get("passcode") or data.get("password") or "").strip()
            if not u or not k:
                return self._send_json(401, {"status": "unauthorized", "message": "请输入账号与掩码登录密码"}, req_id=req_id, t0=t0)

            sconn = REPO.get_sqlite_conn()
            urow = sconn.execute(
                "SELECT user_id, username, display_name, role, account_status, passcode_hash, passcode_salt, token_secret, failed_login_count FROM sys_users WHERE user_id = ? OR username = ?",
                (u, u),
            ).fetchone()
            if urow is None:
                sconn.close()
                record_rbac_audit(u, "GUEST", u, "LOGIN_FAILED", {"reason": "account_not_found"}, client_ip, sim_down=sim_down)
                return self._send_json(401, {"status": "unauthorized", "message": "账号不存在或密码错误（如需开通新账号请联系管理员在 RBAC 中心创建）"}, req_id=req_id, t0=t0)

            uid_real = urow["user_id"]
            role = str(urow["role"] or "SCHOLAR").upper()
            acct_stat = str(urow["account_status"] or "ACTIVE").upper()
            if acct_stat != "ACTIVE":
                sconn.close()
                record_rbac_audit(uid_real, role, uid_real, "LOGIN_BLOCKED_DISABLED", {"account_status": acct_stat}, client_ip, sim_down=sim_down)
                return self._send_json(403, {"status": "account_disabled", "message": f"账号 {uid_real} 当前状态为 {acct_stat}，请联系管理员启用"}, req_id=req_id, t0=t0)

            stored_pw = str(urow["passcode_hash"] or "")
            salt = str(urow["passcode_salt"] or "kaoyan_salt_2026")
            if not verify_passcode(k, stored_pw, salt):
                fail_cnt = int(urow["failed_login_count"] or 0) + 1
                sconn.execute("UPDATE sys_users SET failed_login_count = ? WHERE user_id = ?", (fail_cnt, uid_real))
                sconn.commit()
                sconn.close()
                record_rbac_audit(uid_real, role, uid_real, "LOGIN_FAILED", {"reason": "bad_passcode", "failed_count": fail_cnt}, client_ip, sim_down=sim_down)
                return self._send_json(401, {"status": "unauthorized", "message": "登录密码校验未通过，请重新输入"}, req_id=req_id, t0=t0)

            disp = urow["display_name"]
            token = urow["token_secret"] or f"kaoyan-{role.lower()}-{uid_real}-{uuid.uuid4().hex[:16]}"
            sconn.execute(
                "UPDATE sys_users SET failed_login_count = 0, last_login_at = ?, token_secret = ? WHERE user_id = ?",
                (now, token, uid_real),
            )
            sconn.execute("INSERT OR IGNORE INTO user_progress_anchors VALUES (?, ?, 2, ?, 2, ?, 12, 1, ?)", (uid_real, "P2024_EN1_T1", "sp-sent-2", "", now))
            sconn.commit()
            anchor = dict(sconn.execute("SELECT * FROM user_progress_anchors WHERE user_id = ?", (uid_real,)).fetchone())
            sconn.close()

            pg_ok = False
            pconn = REPO.get_pg_conn(simulate_down=sim_down)
            if pconn is not None:
                try:
                    with pconn:
                        with pconn.cursor() as cur:
                            cur.execute(
                                "UPDATE sys_users SET failed_login_count = 0, last_login_at = %s, token_secret = %s WHERE user_id = %s",
                                (now, token, uid_real),
                            )
                    pg_ok = True
                finally:
                    pconn.close()

            record_rbac_audit(uid_real, role, uid_real, "LOGIN_SUCCESS", {"role": role, "engine": "pg18" if pg_ok else "sqlite"}, client_ip, sim_down=sim_down)
            REPO.record_ha_wal("LOGIN_SUCCESS", "sys_users", uid_real, {"user_id": uid_real, "last_login_at": now}, pg_ok, True)
            eng = "postgresql_18_primary" if pg_ok else "sqlite_wal_hot_standby_failover"
            return self._send_json(
                200,
                {
                    "status": "ok",
                    "engine": eng,
                    "user_id": uid_real,
                    "username": uid_real,
                    "display_name": disp,
                    "role": role,
                    "account_status": acct_stat,
                    "permissions": get_role_permissions(role),
                    "token": token,
                    "anchor": anchor,
                },
                req_id=req_id,
                t0=t0,
                engine_hdr=eng,
            )

        if self.path == "/api/auth/password/change":
            session_ctx = get_session_user(self.headers, simulate_pg_down=sim_down)
            u = str(data.get("username") or data.get("user_id") or (session_ctx["user_id"] if session_ctx else "")).strip()
            old_k = str(data.get("old_passcode") or data.get("old_password") or "").strip()
            new_k = str(data.get("new_passcode") or data.get("new_password") or "").strip()
            if not u or not old_k or len(new_k) < 4:
                return self._send_json(422, {"status": "validation_error", "message": "请填写原密码及不少于 4 位的新密码"}, req_id=req_id, t0=t0)
            if session_ctx is not None and session_ctx["role"] != "ADMIN" and session_ctx["user_id"] != u:
                record_rbac_audit(session_ctx["user_id"], session_ctx["role"], u, "UNAUTHORIZED_BLOCKED", {"reason": "scholar_cannot_change_other_user_password"}, client_ip, sim_down=sim_down)
                return self._send_json(403, {"status": "rbac_forbidden", "message": "普通用户仅可修改本人登录密码，不可越权修改他人密码"}, req_id=req_id, t0=t0)
            sconn = REPO.get_sqlite_conn()
            urow = sconn.execute("SELECT user_id, role, passcode_hash, passcode_salt FROM sys_users WHERE user_id = ? OR username = ?", (u, u)).fetchone()
            if urow is None:
                sconn.close()
                return self._send_json(404, {"status": "not_found", "message": f"未找到账号 {u}"}, req_id=req_id, t0=t0)
            uid_real = urow["user_id"]
            role_real = str(urow["role"] or "SCHOLAR").upper()
            stored_pw = str(urow["passcode_hash"] or "")
            salt_old = str(urow["passcode_salt"] or "kaoyan_salt_2026")
            if not verify_passcode(old_k, stored_pw, salt_old):
                sconn.close()
                record_rbac_audit(uid_real, role_real, uid_real, "SELF_PASSWORD_CHANGE_FAILED", {"reason": "old_passcode_mismatch"}, client_ip, sim_down=sim_down)
                return self._send_json(401, {"status": "unauthorized", "message": "原密码校验未通过，无法修改密码"}, req_id=req_id, t0=t0)
            new_salt = f"salt_{uuid.uuid4().hex[:10]}"
            new_hash = hash_passcode(new_k, new_salt)
            new_token = f"kaoyan-{role_real.lower()}-{uid_real}-{hashlib.sha256((uid_real + ':' + new_hash + ':' + now).encode('utf-8')).hexdigest()[:16]}"
            sconn.execute(
                "UPDATE sys_users SET passcode_hash = ?, passcode_salt = ?, token_secret = ?, password_updated_at = ? WHERE user_id = ?",
                (new_hash, new_salt, new_token, now, uid_real),
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
                                "UPDATE sys_users SET passcode_hash = %s, passcode_salt = %s, token_secret = %s, password_updated_at = %s WHERE user_id = %s",
                                (new_hash, new_salt, new_token, now, uid_real),
                            )
                    pg_ok = True
                finally:
                    pconn.close()
            record_rbac_audit(uid_real, role_real, uid_real, "SELF_PASSWORD_CHANGE", {"hash_algo": "PBKDF2-HMAC-SHA256", "token_rotated": True}, client_ip, sim_down=sim_down)
            REPO.record_ha_wal("PASSWORD_CHANGE", "sys_users", uid_real, {"user_id": uid_real, "updated_at": now}, pg_ok, True)
            eng = "postgresql_18_primary" if pg_ok else "sqlite_wal_hot_standby_failover"
            return self._send_json(
                200,
                {"status": "ok", "engine": eng, "user_id": uid_real, "role": role_real, "token": new_token, "message": f"账号 {uid_real} 密码已更新（PBKDF2 加密落盘，旧令牌已自动失效）"},
                req_id=req_id,
                t0=t0,
                engine_hdr=eng,
            )

        if self.path in ("/api/admin/users", "/api/auth/user/create"):
            admin_ctx, code, msg = require_admin(self.headers, client_ip=client_ip, endpoint=self.path, simulate_pg_down=sim_down)
            if admin_ctx is None:
                return self._send_json(code, {"status": "rbac_forbidden" if code == 403 else "unauthorized", "message": msg}, req_id=req_id, t0=t0)
            u = str(data.get("username") or data.get("user_id") or "").strip()
            disp = str(data.get("display_name") or "").strip() or u
            k = str(data.get("passcode") or data.get("password") or "").strip()
            role = str(data.get("role", "SCHOLAR")).strip().upper()
            if role not in ("SCHOLAR", "ADMIN"):
                role = "SCHOLAR"
            if not re.match(r"^[a-zA-Z0-9_\-]{2,32}$", u):
                return self._send_json(422, {"status": "validation_error", "message": "账号需为 2~32 位字母、数字、下划线或连字符"}, req_id=req_id, t0=t0)
            if len(k) < 4:
                return self._send_json(422, {"status": "validation_error", "message": "初始密码长度不少于 4 位"}, req_id=req_id, t0=t0)
            sconn = REPO.get_sqlite_conn()
            exists = sconn.execute("SELECT user_id FROM sys_users WHERE user_id = ? OR username = ?", (u, u)).fetchone()
            if exists:
                sconn.close()
                return self._send_json(409, {"status": "conflict", "message": f"账号 {u} 已存在，请使用管理员重置密码或切换角色功能"}, req_id=req_id, t0=t0)
            salt_new = f"salt_{uuid.uuid4().hex[:10]}"
            hash_new = hash_passcode(k, salt_new)
            token = f"kaoyan-{role.lower()}-{u}-{hashlib.sha256((u + ':' + hash_new).encode('utf-8')).hexdigest()[:16]}"
            sconn.execute(
                "INSERT INTO sys_users (user_id, username, display_name, role, account_status, passcode_hash, passcode_salt, token_secret, failed_login_count, last_login_at, password_updated_at, created_by, created_at) VALUES (?,?,?,?,'ACTIVE',?,?,?,0,'',?,?,?)",
                (u, u, disp, role, hash_new, salt_new, token, now, admin_ctx["user_id"], now),
            )
            sconn.execute("INSERT OR IGNORE INTO user_progress_anchors VALUES (?, ?, 1, ?, 2, '', 1, 1, ?)", (u, "P2024_EN1_T1", "sp-para-1", now))
            sconn.commit()
            sconn.close()

            pg_ok = False
            pconn = REPO.get_pg_conn(simulate_down=sim_down)
            if pconn is not None:
                try:
                    with pconn:
                        with pconn.cursor() as cur:
                            cur.execute(
                                "INSERT INTO sys_users (user_id, username, display_name, role, account_status, passcode_hash, passcode_salt, token_secret, failed_login_count, last_login_at, password_updated_at, created_by, created_at) VALUES (%s,%s,%s,%s,'ACTIVE',%s,%s,%s,0,'',%s,%s,%s) ON CONFLICT (user_id) DO NOTHING",
                                (u, u, disp, role, hash_new, salt_new, token, now, admin_ctx["user_id"], now),
                            )
                            cur.execute(
                                "INSERT INTO user_progress_anchors (user_id, last_passage_id, last_para_idx, last_span_id, last_tab_idx, essay_draft_md, streak_days, rev_no, updated_at) VALUES (%s,%s,1,%s,2,'',1,1,%s) ON CONFLICT (user_id) DO NOTHING",
                                (u, "P2024_EN1_T1", "sp-para-1", now),
                            )
                    pg_ok = True
                finally:
                    pconn.close()
            record_rbac_audit(admin_ctx["user_id"], "ADMIN", u, "ADMIN_USER_CREATE", {"new_user": u, "role": role, "display_name": disp}, client_ip, sim_down=sim_down)
            REPO.record_ha_wal("ADMIN_USER_CREATE", "sys_users", u, {"user_id": u, "display_name": disp, "role": role, "created_by": admin_ctx["user_id"]}, pg_ok, True)
            eng = "postgresql_18_primary" if pg_ok else "sqlite_wal_hot_standby_failover"
            return self._send_json(
                200,
                {"status": "ok", "engine": eng, "user_id": u, "display_name": disp, "role": role, "account_status": "ACTIVE", "message": f"管理员已成功创建账号 {u} (角色: {role})"},
                req_id=req_id,
                t0=t0,
                engine_hdr=eng,
            )

        if self.path == "/api/admin/users/password":
            admin_ctx, code, msg = require_admin(self.headers, client_ip=client_ip, endpoint=self.path, simulate_pg_down=sim_down)
            if admin_ctx is None:
                return self._send_json(code, {"status": "rbac_forbidden" if code == 403 else "unauthorized", "message": msg}, req_id=req_id, t0=t0)
            target_u = str(data.get("target_user_id") or data.get("username") or "").strip()
            new_k = str(data.get("new_passcode") or data.get("new_password") or "").strip()
            if not target_u or len(new_k) < 4:
                return self._send_json(422, {"status": "validation_error", "message": "请指定目标账号与不少于 4 位的新密码"}, req_id=req_id, t0=t0)
            sconn = REPO.get_sqlite_conn()
            urow = sconn.execute("SELECT user_id, role FROM sys_users WHERE user_id = ? OR username = ?", (target_u, target_u)).fetchone()
            if urow is None:
                sconn.close()
                return self._send_json(404, {"status": "not_found", "message": f"未找到目标账号 {target_u}"}, req_id=req_id, t0=t0)
            uid_real = urow["user_id"]
            role_real = str(urow["role"] or "SCHOLAR").upper()
            new_salt = f"salt_{uuid.uuid4().hex[:10]}"
            new_hash = hash_passcode(new_k, new_salt)
            new_token = f"kaoyan-{role_real.lower()}-{uid_real}-{hashlib.sha256((uid_real + ':' + new_hash + ':' + now).encode('utf-8')).hexdigest()[:16]}"
            sconn.execute(
                "UPDATE sys_users SET passcode_hash = ?, passcode_salt = ?, token_secret = ?, failed_login_count = 0, password_updated_at = ? WHERE user_id = ?",
                (new_hash, new_salt, new_token, now, uid_real),
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
                                "UPDATE sys_users SET passcode_hash = %s, passcode_salt = %s, token_secret = %s, failed_login_count = 0, password_updated_at = %s WHERE user_id = %s",
                                (new_hash, new_salt, new_token, now, uid_real),
                            )
                    pg_ok = True
                finally:
                    pconn.close()
            record_rbac_audit(admin_ctx["user_id"], "ADMIN", uid_real, "ADMIN_PASSWORD_RESET", {"target_user": uid_real, "token_rotated": True}, client_ip, sim_down=sim_down)
            REPO.record_ha_wal("ADMIN_PASSWORD_RESET", "sys_users", uid_real, {"user_id": uid_real, "reset_by": admin_ctx["user_id"]}, pg_ok, True)
            eng = "postgresql_18_primary" if pg_ok else "sqlite_wal_hot_standby_failover"
            return self._send_json(
                200,
                {"status": "ok", "engine": eng, "user_id": uid_real, "message": f"管理员已重置账号 {uid_real} 的登录密码，旧会话已自动失效"},
                req_id=req_id,
                t0=t0,
                engine_hdr=eng,
            )

        if self.path == "/api/admin/users/role_status":
            admin_ctx, code, msg = require_admin(self.headers, client_ip=client_ip, endpoint=self.path, simulate_pg_down=sim_down)
            if admin_ctx is None:
                return self._send_json(code, {"status": "rbac_forbidden" if code == 403 else "unauthorized", "message": msg}, req_id=req_id, t0=t0)
            target_u = str(data.get("target_user_id") or data.get("username") or "").strip()
            new_role = str(data.get("role") or "").strip().upper()
            new_status = str(data.get("account_status") or "").strip().upper()
            if not target_u:
                return self._send_json(422, {"status": "validation_error", "message": "请指定目标账号"}, req_id=req_id, t0=t0)
            sconn = REPO.get_sqlite_conn()
            urow = sconn.execute("SELECT user_id, role, account_status FROM sys_users WHERE user_id = ? OR username = ?", (target_u, target_u)).fetchone()
            if urow is None:
                sconn.close()
                return self._send_json(404, {"status": "not_found", "message": f"未找到目标账号 {target_u}"}, req_id=req_id, t0=t0)
            uid_real = urow["user_id"]
            final_role = new_role if new_role in ("ADMIN", "SCHOLAR") else str(urow["role"] or "SCHOLAR").upper()
            final_stat = new_status if new_status in ("ACTIVE", "DISABLED") else str(urow["account_status"] or "ACTIVE").upper()
            if uid_real == admin_ctx["user_id"] and (final_role != "ADMIN" or final_stat != "ACTIVE"):
                sconn.close()
                return self._send_json(422, {"status": "self_lockout_prevented", "message": "安全保护：管理员不可降级或停用当前自身登录账号"}, req_id=req_id, t0=t0)
            sconn.execute("UPDATE sys_users SET role = ?, account_status = ? WHERE user_id = ?", (final_role, final_stat, uid_real))
            sconn.commit()
            sconn.close()

            pg_ok = False
            pconn = REPO.get_pg_conn(simulate_down=sim_down)
            if pconn is not None:
                try:
                    with pconn:
                        with pconn.cursor() as cur:
                            cur.execute("UPDATE sys_users SET role = %s, account_status = %s WHERE user_id = %s", (final_role, final_stat, uid_real))
                    pg_ok = True
                finally:
                    pconn.close()
            record_rbac_audit(admin_ctx["user_id"], "ADMIN", uid_real, "ADMIN_ROLE_STATUS_CHANGE", {"role": final_role, "account_status": final_stat}, client_ip, sim_down=sim_down)
            REPO.record_ha_wal("ADMIN_ROLE_STATUS_CHANGE", "sys_users", uid_real, {"user_id": uid_real, "role": final_role, "account_status": final_stat}, pg_ok, True)
            eng = "postgresql_18_primary" if pg_ok else "sqlite_wal_hot_standby_failover"
            return self._send_json(
                200,
                {"status": "ok", "engine": eng, "user_id": uid_real, "role": final_role, "account_status": final_stat, "message": f"已更新账号 {uid_real} 状态为 Role={final_role}, Status={final_stat}"},
                req_id=req_id,
                t0=t0,
                engine_hdr=eng,
            )
