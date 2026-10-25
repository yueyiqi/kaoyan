"""Session, permission, and Admin 5-layer full-DB drill-down helpers shared by HTTP routes."""
from __future__ import annotations
from kaoyan_runtime import CORE_TABLES, RBAC_ROLE_PERMS_MAP, json, math, now_str, psycopg2, uuid
from kaoyan_repository import REPO

from kaoyan_admin_catalog import build_admin_db_drilldown_payload
from kaoyan_admin_redaction import mask_sensitive_row_fields


def calc_ebbinghaus_urgency(lookup_count: int, days_since_seen: float, syllabus_tier: str) -> float:
    freq_term = 0.35 * math.log(1.0 + max(1, lookup_count))
    decay_term = 0.45 * (1.0 - math.exp(-max(0.1, days_since_seen) / 3.0))
    tier_bonus = 0.20 if "CORE" in syllabus_tier.upper() else 0.10
    return round(min(1.0, freq_term + decay_term + tier_bonus), 4)


def generate_cloze_pattern(content_en: str) -> str:
    words = content_en.split()
    if len(words) >= 4:
        words[1] = f"[KEY: {words[1]}]"
        if len(words) >= 7:
            words[4] = f"[KEY: {words[4]}]"
        return " ".join(words)
    return f"[______] ({content_en})"


def get_role_permissions(role_code: str) -> list[str]:
    rc = (role_code or "GUEST").upper()
    try:
        sconn = REPO.get_sqlite_conn()
        rows = sconn.execute("SELECT perm_code FROM sys_role_permissions WHERE role_code = ? ORDER BY perm_code ASC", (rc,)).fetchall()
        sconn.close()
        if rows:
            return [r["perm_code"] for r in rows]
    except Exception:
        pass
    return list(RBAC_ROLE_PERMS_MAP.get(rc, RBAC_ROLE_PERMS_MAP["GUEST"]))


def record_rbac_audit(actor_uid: str, actor_role: str, target_uid: str, action: str, detail: dict, client_ip: str = "127.0.0.1", sim_down: bool = False) -> str:
    aud_id = f"aud-{uuid.uuid4().hex[:14]}"
    ts = now_str()
    d_json = json.dumps(detail, ensure_ascii=False)
    try:
        sconn = REPO.get_sqlite_conn()
        sconn.execute(
            "INSERT INTO sys_rbac_audit_log (audit_id, actor_user_id, actor_role, target_user_id, action, detail_json, client_ip, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (aud_id, actor_uid, actor_role, target_uid, action, d_json, client_ip, ts),
        )
        sconn.commit()
        sconn.close()
    except Exception:
        pass
    pconn = REPO.get_pg_conn(simulate_down=sim_down)
    if pconn is not None:
        try:
            with pconn:
                with pconn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO sys_rbac_audit_log (audit_id, actor_user_id, actor_role, target_user_id, action, detail_json, client_ip, created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (audit_id) DO NOTHING",
                        (aud_id, actor_uid, actor_role, target_uid, action, d_json, client_ip, ts),
                    )
        except Exception:
            pass
        finally:
            pconn.close()
    return aud_id


def get_session_user(headers, simulate_pg_down: bool = False) -> dict | None:
    auth = headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth[7:].strip()
    if not token:
        return None
    sconn = REPO.get_sqlite_conn()
    row = sconn.execute(
        "SELECT user_id, username, display_name, role, account_status, last_login_at, password_updated_at, created_at FROM sys_users WHERE token_secret = ?",
        (token,),
    ).fetchone()
    sconn.close()
    if row is None:
        pconn = REPO.get_pg_conn(simulate_down=simulate_pg_down)
        if pconn is not None:
            try:
                with pconn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(
                        "SELECT user_id, username, display_name, role, account_status, last_login_at, password_updated_at, created_at FROM sys_users WHERE token_secret = %s",
                        (token,),
                    )
                    prow = cur.fetchone()
                    if prow:
                        row = dict(prow)
            finally:
                pconn.close()
    if row is None:
        return None
    u_dict = dict(row)
    if str(u_dict.get("account_status", "ACTIVE")).upper() != "ACTIVE":
        return None
    role_code = str(u_dict.get("role", "SCHOLAR")).upper()
    u_dict["role"] = role_code
    u_dict["permissions"] = get_role_permissions(role_code)
    return u_dict


def verify_bearer(headers, simulate_pg_down: bool = False) -> str | None:
    ctx = get_session_user(headers, simulate_pg_down=simulate_pg_down)
    return ctx["user_id"] if ctx else None


def require_admin(headers, client_ip: str = "127.0.0.1", endpoint: str = "", simulate_pg_down: bool = False) -> tuple[dict | None, int, str]:
    ctx = get_session_user(headers, simulate_pg_down=simulate_pg_down)
    if ctx is None:
        record_rbac_audit("guest", "GUEST", endpoint or "admin_api", "UNAUTHORIZED_BLOCKED", {"reason": "missing_or_invalid_bearer"}, client_ip, sim_down=simulate_pg_down)
        return None, 401, "未登录或会话已失效，请先使用管理员账号登录"
    if ctx["role"] != "ADMIN":
        record_rbac_audit(ctx["user_id"], ctx["role"], endpoint or "admin_api", "UNAUTHORIZED_BLOCKED", {"reason": "insufficient_role_requires_admin"}, client_ip, sim_down=simulate_pg_down)
        return None, 403, f"RBAC 权限拦截：当前账号 ({ctx['user_id']}) 角色为 {ctx['role']}，无权执行管理员操作 (需 ADMIN 角色)"
    return ctx, 200, "OK"


