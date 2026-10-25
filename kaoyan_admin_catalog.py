"""Read-only, live-schema drilldown with complete bounded pagination."""
from kaoyan_admin_redaction import MASK, mask_sensitive_row_fields, sensitive

DOMAIN_DEFS = [
    ("DOM_01_RBAC_AUTH", "账号与权限 (Accounts)", ["sys_users", "sys_roles", "sys_permissions", "sys_role_permissions", "sys_rbac_audit_log"]),
    ("DOM_02_CORE_CONTENT", "真题与词典 (Content)", ["exam_passages", "syllabus_5500_lexicon"]),
    ("DOM_03_SCHOLAR_STUDY", "学习资产 (Study)", ["user_progress_anchors", "annotation_spans", "user_vocab_ledger", "essay_corpus_snippets"]),
    ("DOM_04_HA_INFRA", "存储与同步 (Storage)", ["schema_migrations", "ha_sync_wal_journal", "api_idempotency_keys"]),
    ("DOM_05_CLUSTER_ROAMING", "服务协调 (Coordination)", ["ha_cluster_meta", "ha_request_receipts", "ha_cluster_roaming_state", "ha_roaming_wal_stream"]),
    ("DOM_OTHER", "其他数据 (Other data)", []),
]
FK_TARGETS = {
    "user_id": "sys_users.user_id", "owner_user_id": "sys_users.user_id",
    "actor_user_id": "sys_users.user_id", "target_user_id": "sys_users.user_id",
    "created_by": "sys_users.user_id", "granted_by": "sys_users.user_id",
    "role": "sys_roles.role_code", "role_code": "sys_roles.role_code",
    "actor_role": "sys_roles.role_code", "perm_code": "sys_permissions.perm_code",
    "passage_id": "exam_passages.passage_id", "last_passage_id": "exam_passages.passage_id",
    "lemma": "syllabus_5500_lexicon.lemma", "promoted_snippet_id": "essay_corpus_snippets.snippet_id",
    "last_span_id": "annotation_spans.span_id", "tx_uuid": "ha_sync_wal_journal.tx_uuid",
}
USER_COLUMNS = {"user_id", "owner_user_id", "actor_user_id", "target_user_id", "created_by", "granted_by"}


def quoted(identifier):
    return '"' + identifier.replace('"', '""') + '"'


def parameter(qs, key, default=""):
    return qs.get(key, [default])[0]


def bounded_int(qs, key, default, minimum, maximum):
    value = int(parameter(qs, key, str(default)))
    if not minimum <= value <= maximum:
        raise ValueError("Invalid " + key)
    return value


def build_admin_db_drilldown_payload(conn, qs, admin_uid):
    # SQLite owns the inventory; a documentation-only table can never appear here.
    names = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()]
    limit = bounded_int(qs, "limit", 50, 1, 100)
    offset = bounded_int(qs, "offset", 0, 0, 2147483647)
    selected = parameter(qs, "table", "sys_users" if "sys_users" in names else (names[0] if names else ""))
    if selected not in names:
        raise ValueError("Unknown table")
    user = parameter(qs, "user_id")
    filter_column = parameter(qs, "filter_column")
    if filter_column and "filter_value" not in qs:
        raise ValueError("Missing filter value")
    filter_value = parameter(qs, "filter_value")
    domain_map = {table: (did, label) for did, label, tables in DOMAIN_DEFS for table in tables}
    tables, fields, associations = {}, [], {}
    for index, name in enumerate(names, 1):
        rows = conn.execute("PRAGMA table_xinfo(" + quoted(name) + ")").fetchall()
        declared_fks = conn.execute("PRAGMA foreign_key_list(" + quoted(name) + ")").fetchall()
        fk_map = {r[3]: r[2] + "." + r[4] for r in declared_fks if r[4]}
        columns = []
        domain, label = domain_map.get(name, ("DOM_OTHER", "其他数据 (Other data)"))
        for r in rows:
            cid, col, dtype, notnull, default, pk = r[:6]
            fk = fk_map.get(col, FK_TARGETS.get(col, ""))
            if fk == name + "." + col:
                fk = ""
            meta = {"cid": cid, "name": col, "column_name": col, "type": dtype, "data_type": dtype,
                    "notnull": bool(notnull), "not_null": bool(notnull),
                    "default_value": MASK if sensitive(col) and default is not None else default,
                    "pk": pk, "hidden": r[6] if len(r) > 6 else 0, "fk_target": fk,
                    "is_json": col.endswith("_json") or col == "response",
                    "is_sensitive_masked": sensitive(col)}
            columns.append(meta)
            fields.append({"field_seq": len(fields) + 1, "table_name": name,
                           "domain_id": domain, "domain_name": label, **meta})
        count = conn.execute("SELECT COUNT(*) FROM " + quoted(name)).fetchone()[0]
        tables[name] = {"table_no": f"T{index:02}", "table_name": name, "domain_id": domain,
                        "domain_name": label, "column_count": len(columns), "columns_count": len(columns),
                        "row_count": count, "live_row_count": count, "columns": columns,
                        "pk_columns": [c["name"] for c in sorted(columns, key=lambda c: c["pk"]) if c["pk"]]}
        associations[name] = [c["name"] for c in columns if c["name"] in USER_COLUMNS or c["fk_target"] == "sys_users.user_id"]
    selected_meta = tables[selected]
    if filter_column and filter_column not in {c["name"] for c in selected_meta["columns"]}:
        raise ValueError("Unknown filter column")
    clauses, values, cascade = [], [], {}
    # A user can be an actor, target or owner. OR is required within a table.
    if user:
        for name, cols in associations.items():
            if not cols:
                continue
            condition = "(" + " OR ".join(quoted(c) + " = ?" for c in cols) + ")"
            args = [user] * len(cols)
            count = conn.execute("SELECT COUNT(*) FROM " + quoted(name) + " WHERE " + condition, args).fetchone()[0]
            cascade[name] = {"filter_columns": cols, "matched_count": count,
                             "column_count": tables[name]["column_count"]}
            if name == selected:
                clauses.append(condition)
                values.extend(args)
        if selected not in cascade:
            clauses.append("0")  # An unrelated table cannot silently ignore a user filter.
    if filter_column:
        clauses.append(quoted(filter_column) + " = ?")
        values.append(filter_value)
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    count = conn.execute("SELECT COUNT(*) FROM " + quoted(selected) + where, values).fetchone()[0]
    # PKs make pages stable. All columns provide deterministic ordering for keyless tables.
    order = selected_meta["pk_columns"] or [c["name"] for c in selected_meta["columns"]]
    cols = ", ".join(quoted(c["name"]) for c in selected_meta["columns"])
    sql = "SELECT " + cols + " FROM " + quoted(selected) + where
    sql += " ORDER BY " + ", ".join(quoted(c) for c in order) + " LIMIT ? OFFSET ?"
    result_rows = [mask_sensitive_row_fields(selected, dict(r)) for r in conn.execute(sql, [*values, limit, offset]).fetchall()]
    page = {**selected_meta, "rows": result_rows, "row_count": count, "offset": offset, "limit": limit,
            "has_previous": offset > 0, "has_next": offset + len(result_rows) < count,
            "filter_column": filter_column, "filter_value": filter_value}
    domains = []
    for did, label, _ in DOMAIN_DEFS:
        members = [name for name in names if tables[name]["domain_id"] == did]
        if members:
            ncols = sum(tables[name]["column_count"] for name in members)
            domains.append({"domain_id": did, "domain_name": label, "tables": members,
                            "table_count": len(members), "tables_count": len(members),
                            "column_count": ncols, "columns_count": ncols,
                            "total_rows": sum(tables[name]["row_count"] for name in members)})
    return {"status": "ok", "admin_actor": admin_uid, "selected_table_name": selected,
            "selected_table": page, "selected_user_cascade": user,
            "total_tables_count": len(tables), "total_columns_count": len(fields), "field_coverage_pct": 100.0,
            "summary": {"total_tables": len(tables), "total_columns": len(fields),
                        "field_coverage_pct": 100.0, "drilldown_layers": 5},
            "layer1_domains": domains, "domains": domains, "layer2_tables": list(tables.values()),
            "tables": tables, "user_cascade": {"user_id": user, "tables": cascade},
            "field_catalog_100pct": fields}
