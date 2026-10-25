"""Exercise the real gateway and three workers, including HTTP guards and asset routes."""
import json
from pathlib import Path
import sys
import unittest
import urllib.request
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).parent))
from test_live_cluster import ClusterTests, SEED_USERS


class AdminHttpTests(ClusterTests):
    def test_admin_routes_through_coordinator(self):
        # Isolated fixture credentials, never a deployed account.
        admin = "Bearer " + next(row[6] for row in SEED_USERS if row[0] == "commander")
        path = "/api/admin/db/drilldown"
        self.assertEqual(self.http(path)[0], 401)
        self.assertEqual(self.http(path, auth=self.auth)[0], 403)
        self.assertEqual(self.http(path, auth="Bearer expired")[0], 401)
        status = self.control("status")
        before = status["version"]
        code, data = self.http(path, auth=admin)
        self.assertEqual(code, 200)
        expected = set(status["tables"])
        self.assertEqual(set(data["tables"]), expected)
        for name in expected:
            query = urlencode({"table": name, "limit": 2})
            code, page = self.http(path + "?" + query, auth=admin)
            self.assertEqual(code, 200)
            selected = page["selected_table"]
            columns = {c["name"] for c in selected["columns"]}
            self.assertTrue(all(set(row) == columns for row in selected["rows"]))
            self.assertLessEqual(len(selected["rows"]), 2)
        code, empty = self.http(path + "?table=sys_users&user_id=absent", auth=admin)
        self.assertEqual(code, 200)
        self.assertEqual(empty["selected_table"]["rows"], [])
        self.assertEqual(self.http(path + "?table=sys_users&limit=bad", auth=admin)[0], 400)
        self.assertEqual(self.http(path + "?table=missing", auth=admin)[0], 400)
        self.assertEqual(self.http(path + "?table=sys_users&filter_column=nope&filter_value=x", auth=admin)[0], 400)
        # Every served script must be a script, not a page with a misleading HTTP 200.
        for name in ["kaoyan_admin.js", "kaoyan_admin_view.js", "kaoyan_login.js", "kaoyan_admin_accounts.js"]:
            with urllib.request.urlopen(self.url + "/" + name, timeout=15) as response:
                self.assertEqual(response.status, 200)
                self.assertIn("javascript", response.headers["Content-Type"])
                self.assertEqual(response.read(), (Path(__file__).parents[1] / name).read_bytes())
        after = self.control("status")
        self.assertEqual(after["version"], before, "all authorized drilldown GETs must remain read-only")
        self.assertTrue(all(item["ok"] for item in after["acks"].values()))


if __name__ == "__main__":
    suite = unittest.TestSuite([AdminHttpTests("test_admin_routes_through_coordinator")])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
