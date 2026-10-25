"""Native OS acceptance; no OS identity overrides, no production DB writes."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import importlib.util
import json
import os
from pathlib import Path
import platform
import sqlite3
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from kaoyan_schema import ensure_schema, inspect_schema, reference_schema
from kaoyan_portable import export_snapshot, restore_snapshot, inventory


class SchemaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="kaoyan-native-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.db = self.base / "目录 with spaces" / "source.db"
        self.db.parent.mkdir()

    def initialized(self):
        conn = sqlite3.connect(self.db)
        self.addCleanup(conn.close)
        ensure_schema(conn)
        return conn

    def sample(self, conn):
        conn.execute("CREATE TABLE extra_future_table (id INTEGER PRIMARY KEY, text_value TEXT, binary_value BLOB)")
        conn.execute("INSERT INTO extra_future_table VALUES (1, ?, ?)", ("考研 /ə/\r\nC:\\学习\\draft\n", b"\x00\xff"))
        conn.commit()

    def test_empty_and_repeat_are_idempotent(self):
        conn = self.initialized()
        first = inventory(conn)
        self.assertEqual(ensure_schema(conn)["changes"], [])
        self.assertEqual(first, inventory(conn))
        self.assertEqual(len(first), 14)

    def test_v1_upgrade_preserves_rows(self):
        with closing(sqlite3.connect(self.db)) as conn:
            conn.executescript((ROOT / "db_migrations/V001__init_kaoyan_8tables.sql").read_text(encoding="utf-8"))
            before = conn.execute("SELECT user_id,passcode_hash,token_secret FROM sys_users ORDER BY user_id").fetchall()
            ensure_schema(conn)
            self.assertEqual(before, conn.execute("SELECT user_id,passcode_hash,token_secret FROM sys_users ORDER BY user_id").fetchall())
            self.assertTrue(inspect_schema(conn)["ready"])

    def test_every_missing_table_recreated_without_other_row_loss(self):
        conn = self.initialized()
        self.sample(conn)
        tables, _, _ = reference_schema()
        for name in tables:
            with self.subTest(table=name):
                conn.execute('DROP TABLE "' + name + '"')
                conn.commit()
                self.assertFalse(inspect_schema(conn)["ready"])
                self.assertTrue(ensure_schema(conn)["ready"])
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM extra_future_table").fetchone()[0], 1)

    def test_missing_optional_column_repaired(self):
        conn = self.initialized()
        conn.execute("ALTER TABLE sys_users DROP COLUMN last_login_at")
        conn.commit()
        result = ensure_schema(conn)
        self.assertIn("add:sys_users.last_login_at", result["changes"])

    def test_incompatible_primary_key_rolls_back_all_ddl(self):
        with closing(sqlite3.connect(self.db)) as conn:
            conn.execute("CREATE TABLE sys_users (user_id TEXT)")
            conn.commit()
            before = conn.execute("SELECT name FROM sqlite_master").fetchall()
            with self.assertRaisesRegex(RuntimeError, "primary key"):
                ensure_schema(conn)
            self.assertEqual(before, conn.execute("SELECT name FROM sqlite_master").fetchall())

    def test_checksum_drift_rejected_and_ddl_rolled_back(self):
        conn = self.initialized()
        conn.execute("UPDATE schema_migrations SET checksum_sha256='wrong' WHERE version_id='V005'")
        conn.execute("DROP TABLE annotation_spans")
        conn.commit()
        with self.assertRaisesRegex(RuntimeError, "checksum"):
            ensure_schema(conn)
        self.assertIn("annotation_spans", inspect_schema(conn)["missing_tables"])

    def test_missing_asset_fails_before_creating_tables(self):
        with closing(sqlite3.connect(self.db)) as conn:
            with patch.dict(os.environ, {"KAOYAN_MIGRATIONS_DIR": str(self.base / "absent")}):
                with self.assertRaisesRegex(RuntimeError, "asset missing"):
                    ensure_schema(conn)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()[0], 0)

    def test_concurrent_initializers_serialize(self):
        def initialize(_):
            with closing(sqlite3.connect(self.db, timeout=10)) as conn:
                return ensure_schema(conn)["ready"]
        with ThreadPoolExecutor(max_workers=4) as workers:
            self.assertEqual(list(workers.map(initialize, range(4))), [True] * 4)

    def test_live_wal_full_snapshot_retains_unicode_blobs_and_extra_tables(self):
        conn = self.initialized()
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA wal_autocheckpoint=0")
        self.sample(conn)
        package, target = self.base / "package", self.base / "target.db"
        self.assertTrue(Path(str(self.db) + "-wal").exists())
        expected = inventory(conn)
        export_snapshot(self.db, package)
        with closing(sqlite3.connect(package / "database.sqlite3")) as snapshot:
            self.assertEqual(snapshot.execute("PRAGMA journal_mode").fetchone()[0], "delete")
        self.assertFalse(Path(str(package / "database.sqlite3") + "-wal").exists())
        restore_snapshot(package, target)
        with closing(sqlite3.connect(target)) as restored:
            self.assertEqual(inventory(restored), expected)

    def test_corrupt_file_rejected_before_target_exists(self):
        self.initialized()
        package, target = self.base / "package", self.base / "target.db"
        export_snapshot(self.db, package)
        with (package / "database.sqlite3").open("ab") as stream:
            stream.write(b"corruption")
        with self.assertRaisesRegex(ValueError, "checksum"):
            restore_snapshot(package, target)
        self.assertFalse(target.exists())

    def test_corrupt_inventory_rejected_before_target_exists(self):
        self.initialized()
        package, target = self.base / "package", self.base / "target.db"
        export_snapshot(self.db, package)
        manifest = json.loads((package / "manifest.json").read_text())
        manifest["tables"]["sys_users"]["rows"] = 999
        (package / "manifest.json").write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "inventory"):
            restore_snapshot(package, target)
        self.assertFalse(target.exists())

    def test_restore_never_overwrites_existing_target(self):
        conn = self.initialized()
        before = inventory(conn)
        with self.assertRaises(FileExistsError):
            restore_snapshot(self.base / "absent", self.db)
        self.assertEqual(before, inventory(conn))

    def test_server_bootstrap_and_honest_health(self):
        with patch.dict(os.environ, {"KAOYAN_DB_PATH": str(self.db), "KAOYAN_BACKUP_DIR": str(self.base / "backups"), "KAOYAN_PG_DSN": ""}):
            spec = importlib.util.spec_from_file_location("test_server", ROOT / "kaoyan_hub_server.py")
            server = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(server)
        server.REPO.init_and_migrate_both_engines()
        with closing(sqlite3.connect(self.db)) as conn:
            conn.execute("UPDATE sys_users SET role='SCHOLAR', account_status='DISABLED', passcode_hash='legacy-custom', token_secret='custom-token' WHERE user_id='admin'")
            conn.execute("UPDATE sys_roles SET description='operator description', created_at='original-time'")
            conn.execute("UPDATE sys_permissions SET description='operator permission'")
            conn.execute("UPDATE sys_role_permissions SET granted_at='original-time', granted_by='operator'")
            conn.execute("UPDATE schema_migrations SET applied_at='original-time' WHERE version_id='V003'")
            conn.commit()
            before_restart = inventory(conn)
        server.REPO.init_and_migrate_both_engines()
        with closing(sqlite3.connect(self.db)) as conn:
            self.assertEqual(inventory(conn), before_restart)
            self.assertEqual(conn.execute("SELECT role,account_status,passcode_hash,token_secret FROM sys_users WHERE user_id='admin'").fetchone(),
                             ('SCHOLAR', 'DISABLED', 'legacy-custom', 'custom-token'))
        http = server.ThreadingHTTPServer(("127.0.0.1", 0), server.KaoyanModularHandler)
        thread = threading.Thread(target=http.serve_forever, daemon=True)
        thread.start()
        try:
            url = "http://127.0.0.1:" + str(http.server_port)
            with urllib.request.urlopen(url + "/api/health") as response:
                self.assertEqual(response.status, 200)
                self.assertEqual(json.load(response)["tables_count"], 14)
            with closing(sqlite3.connect(self.db)) as conn:
                token = conn.execute("SELECT token_secret FROM sys_users WHERE user_id='colleague_a'").fetchone()[0]
            # The separate account dispatcher must retain the admin boundary.
            request = urllib.request.Request(url + "/api/admin/users",
                data=b'{"username":"forbidden-test-user","passcode":"test-only"}',
                headers={"Content-Type": "application/json", "Authorization": "Bearer " + token})
            with self.assertRaises(urllib.error.HTTPError) as forbidden:
                urllib.request.urlopen(request)
            self.assertEqual(forbidden.exception.code, 403)
            forbidden.exception.close()
            with closing(sqlite3.connect(self.db)) as conn:
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM sys_users WHERE username='forbidden-test-user'").fetchone()[0], 0)
                admin_token = conn.execute("SELECT token_secret FROM sys_users WHERE user_id='commander'").fetchone()[0]
            # Verify /api/admin/db/drilldown rejects non-admin SCHOLAR with 403 and returns 100% fields for ADMIN
            drill_forbidden_req = urllib.request.Request(
                url + "/api/admin/db/drilldown?table=sys_users",
                headers={"Authorization": "Bearer " + token},
            )
            with self.assertRaises(urllib.error.HTTPError) as drill_forbidden:
                urllib.request.urlopen(drill_forbidden_req)
            self.assertEqual(drill_forbidden.exception.code, 403)
            drill_forbidden.exception.close()
            drill_admin_req = urllib.request.Request(
                url + "/api/admin/db/drilldown?table=sys_users&user_id=colleague_a",
                headers={"Authorization": "Bearer " + admin_token},
            )
            with urllib.request.urlopen(drill_admin_req) as drill_resp:
                self.assertEqual(drill_resp.status, 200)
                drill_body = json.load(drill_resp)
                self.assertEqual(drill_body["field_coverage_pct"], 100.0)
                self.assertEqual(drill_body["total_tables_count"], 14)
                self.assertEqual(drill_body["total_columns_count"], 118)
                self.assertEqual(drill_body["selected_table"]["column_count"], 13)
                self.assertIn("••••掩码脱敏", drill_body["selected_table"]["rows"][0]["passcode_hash"])
                self.assertTrue({"sys_users", "user_progress_anchors", "annotation_spans",
                                 "user_vocab_ledger", "essay_corpus_snippets", "sys_rbac_audit_log",
                                 "api_idempotency_keys", "exam_passages", "sys_role_permissions"}
                                <= set(drill_body["user_cascade"]["tables"]))
            for _ in range(2):
                request = urllib.request.Request(url + "/api/vocab/lookup",
                    data=json.dumps({"lemma": "portability", "contextual_meaning": "跨系统迁移 /ə/"}).encode(),
                    headers={"Content-Type": "application/json", "Authorization": "Bearer " + token,
                             "X-Idempotency-Key": "native-portable-request"})
                with urllib.request.urlopen(request) as response:
                    self.assertEqual(response.status, 200)
            with closing(sqlite3.connect(self.db)) as conn:
                self.assertEqual(conn.execute("SELECT lookup_count FROM user_vocab_ledger WHERE lemma='portability'").fetchone()[0], 1)
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM api_idempotency_keys WHERE idempotency_key='native-portable-request'").fetchone()[0], 1)
                self.assertGreater(conn.execute("SELECT COUNT(*) FROM ha_sync_wal_journal").fetchone()[0], 0)
            with closing(sqlite3.connect(self.db)) as conn:
                conn.execute("DROP TABLE annotation_spans")
                conn.commit()
            with self.assertRaises(urllib.error.HTTPError) as raised:
                urllib.request.urlopen(url + "/api/health")
            self.assertEqual(raised.exception.code, 503)
            self.assertFalse(json.load(raised.exception)["sqlite_standby_online"])
            raised.exception.close()
            with closing(sqlite3.connect(self.db)) as conn:
                self.assertIn("annotation_spans", inspect_schema(conn)["missing_tables"])
        finally:
            http.shutdown()
            http.server_close()
            thread.join()


if __name__ == "__main__":
    print(json.dumps({"actual_os": platform.system(), "release": platform.release(),
                      "machine": platform.machine(), "python": platform.python_version(),
                      "sqlite": sqlite3.sqlite_version}, ensure_ascii=False), flush=True)
    unittest.main(verbosity=2)
