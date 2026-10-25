"""Public HTTPS read-only acceptance; passwords only come from the caller's environment."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import ssl
import urllib.error
import urllib.parse
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="https://kaoyan-elena.duckdns.org")
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    checks, token = {}, ""
    expected = json.loads(args.schema.read_text())
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}),
                                         urllib.request.HTTPSHandler(context=ssl.create_default_context()))

    def request(path, body=None, auth=True):
        headers = {"Content-Type": "application/json"}
        if auth and token:
            headers["Authorization"] = "Bearer " + token
        req = urllib.request.Request(args.base + path, headers=headers,
            data=json.dumps(body).encode() if body is not None else None)
        try:
            response = opener.open(req, timeout=60)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            raw = response.read()
            return response.status, json.loads(raw) if "json" in response.headers.get("Content-Type","") else raw.decode()

    def check(name, passed):
        checks[name] = bool(passed)
        if not passed:
            print("FAIL", name, flush=True)

    code, _ = request("/api/admin/db/drilldown", auth=False)
    check("unauthenticated_401", code == 401)
    code, login = request("/api/auth/login", {"username": os.environ.get("KAOYAN_TEST_USER","admin"),
                                             "passcode": os.environ["KAOYAN_TEST_PASSWORD"]}, auth=False)
    check("admin_login", code == 200 and login.get("role") == "ADMIN" and bool(login.get("token")))
    if not checks["admin_login"]:
        raise RuntimeError("Administrator login not confirmed")
    token = login["token"]
    _, health = request("/api/ha/status")
    version = health["version"]
    code, inventory = request("/api/admin/db/drilldown?table=sys_users")
    check("inventory_status", code == 200)
    check("tables_match_physical", set(inventory["tables"]) == set(expected))
    check("fields_match_physical", all([c["name"] for c in inventory["tables"][name]["columns"]] == cols
                                      for name, cols in expected.items()))
    check("catalog_total_computed", inventory["summary"]["total_columns"] == sum(map(len,expected.values())))
    check("domains_complete", {t for d in inventory["domains"] for t in d["tables"]} == set(expected))
    page_counts = {}
    for name, columns in expected.items():
        offset, seen, expected_count, pages = 0, set(), None, 0
        while True:
            code, payload = request("/api/admin/db/drilldown?" + urllib.parse.urlencode(
                {"table":name,"limit":17,"offset":offset}))
            table = payload["selected_table"]
            check(name + "_column_metadata", code == 200 and [c["name"] for c in table["columns"]] == columns)
            check(name + "_all_row_fields_page_" + str(pages), all(set(row) == set(columns) for row in table["rows"]))
            dump = json.dumps(payload, ensure_ascii=False)
            raw_login = base64.b64encode(json.dumps(login, ensure_ascii=False).encode()).decode()
            check(name + "_credentials_masked_page_" + str(pages), token not in dump and raw_login not in dump)
            if expected_count is None:
                expected_count = table["row_count"]
            check(name + "_count_stable_page_" + str(pages), table["row_count"] == expected_count)
            for row in table["rows"]:
                identity = {key:row[key] for key in table["pk_columns"]} if table["pk_columns"] else row
                digest = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
                check(name + "_unique_" + str(offset), digest not in seen)
                seen.add(digest)
                offset += 1
            pages += 1
            if not table.get("has_next"):
                break
            if pages > 300:
                raise RuntimeError("Bounded live probe page limit reached")
        check(name + "_every_row_reachable", len(seen) == expected_count)
        page_counts[name] = {"rows":len(seen),"pages":pages,"columns":len(columns)}
    code, empty = request("/api/admin/db/drilldown?table=sys_users&user_id=nonexistent-regression-user")
    check("no_match_is_empty", code == 200 and empty["selected_table"]["rows"] == [] and empty["selected_table"]["row_count"] == 0)
    code, exact = request("/api/admin/db/drilldown?table=sys_users&filter_column=user_id&filter_value=commander")
    check("foreign_key_exact_value", code == 200 and [r["user_id"] for r in exact["selected_table"]["rows"]] == ["commander"])
    code, _ = request("/api/admin/db/drilldown?table=sys_users&filter_column=missing&filter_value=x")
    check("invalid_filter_400", code == 400)
    _, health = request("/api/ha/status")
    check("authorized_browse_readonly", health["version"] == version)
    check("three_replicas_confirmed", health["replicas_confirmed"] == 3)
    code, html = request("/")
    check("https_page", code == 200 and "loginStatus" in html and "adminPageInfo" in html)
    for name in ["kaoyan_login.js","kaoyan_admin.js","kaoyan_admin_view.js","kaoyan_admin_accounts.js"]:
        code, source = request("/" + name)
        check(name + "_release_bytes", code == 200 and source.encode() == (Path(__file__).parents[1]/name).read_bytes())
    result = {"status":"PASS" if all(checks.values()) else "FAIL",
              "scope":"HTTPS API and served assets; browser interactions reported separately",
              "checks":checks,"assertions":len(checks),"passed":sum(checks.values()),"tables":page_counts,
              "failed":[key for key,value in checks.items() if not value],"base":args.base}
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps({key:result[key] for key in ["status","assertions","passed","failed"]}))
    return int(not all(checks.values()))


if __name__ == "__main__":
    raise SystemExit(main())
