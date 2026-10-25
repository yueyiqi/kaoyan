"""Behavioral contract: live schema, complete paging, exact filters and redaction."""
import base64
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
TEMP = tempfile.TemporaryDirectory(prefix="kaoyan-admin-test-")
os.environ["KAOYAN_DB_PATH"] = str(Path(TEMP.name) / "unused.db")
os.environ["KAOYAN_BACKUP_DIR"] = str(Path(TEMP.name) / "backups")
os.environ["KAOYAN_PG_DSN"] = ""
from kaoyan_auth import build_admin_db_drilldown_payload, build_eids_lineage_payload, mask_sensitive_row_fields


class DrilldownTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.addCleanup(self.db.close)
        self.db.executescript((ROOT / "db_migrations/V005__complete_portable_schema.sql").read_text())
        self.db.executemany(
            "INSERT INTO sys_users (user_id,username,display_name,role,passcode_hash,token_secret,created_at) VALUES (?,?,?,'SCHOLAR','test-hash','test-token','now')",
            [(f"user-{i:03}", f"user-{i:03}", f"Name {i}") for i in range(63)])
        self.db.executescript("""
            CREATE TABLE extra_records(id INTEGER PRIMARY KEY, user_id TEXT REFERENCES sys_users(user_id), payload_json TEXT, nullable TEXT, empty TEXT DEFAULT '');
            CREATE TABLE empty_records(id INTEGER PRIMARY KEY, note TEXT);
            CREATE TABLE ha_request_receipts(request_key TEXT PRIMARY KEY, fingerprint TEXT, response TEXT);
        """)
        self.db.executemany("INSERT INTO extra_records(id,user_id,payload_json) VALUES (?,?,'{}')",
                            [(i, "user-062") for i in range(67)])
        self.db.commit()

    def query(self, **qs):
        return build_admin_db_drilldown_payload(self.db, {k: [str(v)] for k, v in qs.items()}, "admin")

    def test_pagination_reaches_every_row_once(self):
        ids = []
        for offset in range(0, 63, 17):
            table = self.query(table="sys_users", limit=17, offset=offset)["selected_table"]
            self.assertEqual(table["row_count"], 63)
            self.assertLessEqual(len(table["rows"]), 17)
            ids.extend(r["user_id"] for r in table["rows"])
        self.assertEqual(ids, [f"user-{i:03}" for i in range(63)])

    def test_zero_matches_never_fall_back_to_unfiltered_data(self):
        t = self.query(table="sys_users", user_id="absent")["selected_table"]
        self.assertEqual(t["row_count"], 0)
        self.assertEqual(t["rows"], [])

    def test_empty_table_contains_no_synthetic_row(self):
        t = self.query(table="empty_records")["selected_table"]
        self.assertEqual(t["row_count"], 0)
        self.assertEqual(t["rows"], [])
        self.assertEqual([c["name"] for c in t["columns"]], ["id", "note"])

    def test_exact_field_target_beyond_first_page(self):
        t = self.query(table="extra_records", filter_column="id", filter_value="65")["selected_table"]
        self.assertEqual([r["id"] for r in t["rows"]], [65])
        self.assertEqual(t["row_count"], 1)

    def test_schema_is_exact_and_domains_include_new_tables(self):
        data = self.query(table="extra_records")
        actual = {r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        self.assertEqual(set(data["tables"]), actual)
        self.assertEqual(set(t for d in data["domains"] for t in d["tables"]), actual)
        for name in actual:
            expected = [r[1] for r in self.db.execute('PRAGMA table_info("' + name + '")')]
            self.assertEqual([c["name"] for c in data["tables"][name]["columns"]], expected)
        self.assertEqual(data["summary"]["total_columns"], sum(len(t["columns"]) for t in data["tables"].values()))
        self.assertTrue(all(not t.get("rows") for n, t in data["tables"].items() if n != "extra_records"))

    def test_runtime_constraints_nulls_and_generated_fields(self):
        self.db.execute("CREATE TABLE generated_records(a INTEGER NOT NULL DEFAULT 0, doubled INTEGER GENERATED ALWAYS AS (a*2) VIRTUAL)")
        self.db.execute("INSERT INTO generated_records(a) VALUES (3)")
        data = self.query(table="generated_records")["selected_table"]
        self.assertEqual([c["name"] for c in data["columns"]], ["a", "doubled"])
        self.assertEqual(data["columns"][0]["default_value"], "0")
        self.assertTrue(data["columns"][0]["notnull"])
        self.assertEqual(data["rows"][0]["doubled"], 6)
        row = self.query(table="extra_records", filter_column="id", filter_value="0")["selected_table"]["rows"][0]
        self.assertIsNone(row["nullable"])
        self.assertEqual(row["empty"], "")

    def test_runtime_foreign_key_and_cascade_count_not_limited(self):
        data = self.query(table="extra_records", user_id="user-062", limit=10)
        col = next(c for c in data["selected_table"]["columns"] if c["name"] == "user_id")
        self.assertEqual(col["fk_target"], "sys_users.user_id")
        self.assertEqual(data["selected_table"]["row_count"], 67)
        self.assertEqual(data["user_cascade"]["tables"]["extra_records"]["matched_count"], 67)
        self.assertEqual(len(data["selected_table"]["rows"]), 10)

    def test_audit_cascade_includes_target_as_well_as_actor(self):
        self.db.execute("INSERT INTO sys_rbac_audit_log(audit_id,actor_user_id,actor_role,target_user_id,action,detail_json,client_ip,created_at) VALUES ('audit','admin','ADMIN','user-062','UPDATE','{}','test','now')")
        table = self.query(table="sys_rbac_audit_log", user_id="user-062")["selected_table"]
        self.assertEqual([r["audit_id"] for r in table["rows"]], ["audit"])

    def test_nested_and_encoded_credentials_are_redacted_without_mutation(self):
        secret = "secret-known-test-value"
        nested = {"status": "ok", "token": secret, "nested": [{"passcode": secret, "safe": "keep"}]}
        encoded = base64.b64encode(json.dumps(nested).encode()).decode()
        response = json.dumps({"code": 200, "body": encoded, "headers": {"Authorization": "Bearer " + secret}})
        self.db.execute("INSERT INTO ha_request_receipts VALUES ('r','fingerprint',?)", (response,))
        out = self.query(table="ha_request_receipts")["selected_table"]["rows"][0]["response"]
        self.assertNotIn(secret, out)
        self.assertNotIn(encoded, out)
        self.assertIn("keep", out)
        self.assertEqual(self.db.execute("SELECT response FROM ha_request_receipts").fetchone()[0], response)
        redacted = mask_sensitive_row_fields("anything", {"payload_json": json.dumps(nested), "token_secret": secret})
        self.assertNotIn(secret, json.dumps(redacted))
        self.assertIn("safe", redacted["payload_json"])

    def test_invalid_filters_are_rejected_and_values_are_bound(self):
        for qs in [{"table": "no_table"}, {"table": "sys_users", "limit": 0},
                   {"table": "sys_users", "offset": -1}, {"table": "sys_users", "limit": "bad"},
                   {"table": "sys_users", "filter_column": "no_column", "filter_value": "x"},
                   {"table": "sys_users", "filter_column": "user_id"}]:
            with self.subTest(qs=qs), self.assertRaises(ValueError):
                self.query(**qs)
        t = self.query(table="sys_users", filter_column="user_id", filter_value="' OR 1=1 --")["selected_table"]
        self.assertEqual(t["rows"], [])

    def test_identifier_quoting_readonly_and_no_default_user(self):
        self.db.execute('CREATE TABLE "quoted""table"("value""name" TEXT)')
        self.db.execute('INSERT INTO "quoted""table" VALUES (?)', ("<tag>'value",))
        before = self.db.total_changes
        data = self.query(table='quoted"table', filter_column='value"name', filter_value="<tag>'value")
        self.assertEqual(data["selected_table"]["rows"], [{'value"name': "<tag>'value"}])
        self.assertEqual(self.db.total_changes, before)
        self.assertEqual(data["selected_user_cascade"], "")

    def test_eids_keyword_search_highlight_col_and_rbac_lineage(self):
        data = self.query(table="sys_users", q="Name 42", highlight_col="display_name")
        self.assertEqual(data["selected_table"]["row_count"], 1)
        self.assertEqual(data["selected_table"]["rows"][0]["user_id"], "user-042")
        self.assertEqual(data["selected_table"]["highlight_col"], "display_name")
        self.assertTrue(len(data["table_exposure_matrix"]) >= 10)
        with self.assertRaises(ValueError):
            self.query(table="sys_users", highlight_col="nonexistent_col")
        guest_data = build_eids_lineage_payload(self.db, {"table": ["sys_users"]}, None)
        self.assertEqual(guest_data["auth_tier"], "GUEST_TEASER")
        self.assertEqual(guest_data["selected_table"]["rows"], [])
        scholar_data = build_eids_lineage_payload(self.db, {"table": ["extra_records"]}, {"user_id": "user-062", "role": "SCHOLAR"})
        self.assertEqual(scholar_data["auth_tier"], "SCHOLAR_SCOPED")
        self.assertEqual(scholar_data["selected_table"]["rows"], [])
        admin_data = build_eids_lineage_payload(self.db, {"table": ["sys_users"], "q": ["user-005"]}, {"user_id": "admin", "role": "ADMIN"})
        self.assertEqual(admin_data["auth_tier"], "ADMIN_FULL")
        self.assertEqual(admin_data["selected_table"]["row_count"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
