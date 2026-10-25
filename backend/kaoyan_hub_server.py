#!/usr/bin/env python3
"""Canonical server entry point for native hosts and the container image."""
from kaoyan_runtime import BaseHTTPRequestHandler, ThreadingHTTPServer, PG_DSN, HAS_PG, Path, os
from kaoyan_repository import REPO, DualEngineHARepository
from kaoyan_http_read import ReadHandlerMixin
from kaoyan_http_write import WriteHandlerMixin
from kaoyan_http_accounts import AccountHandlerMixin

if "KAOYAN_DB_PATH" in os.environ:
    REPO.sqlite_path = Path(os.environ["KAOYAN_DB_PATH"]).expanduser().resolve()
    REPO.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
if "KAOYAN_PG_DSN" in os.environ:
    REPO.pg_dsn = os.environ["KAOYAN_PG_DSN"]


class KaoyanModularHandler(ReadHandlerMixin, WriteHandlerMixin, AccountHandlerMixin, BaseHTTPRequestHandler):
    """Compose routes around one repository and one response contract."""


if __name__ == "__main__":
    if PG_DSN and not HAS_PG:
        raise RuntimeError("KAOYAN_PG_DSN requires the psycopg2 driver")
    port = int(os.environ["KAOYAN_PORT"])
    REPO.init_and_migrate_both_engines()
    srv = ThreadingHTTPServer((os.environ.get("KAOYAN_BIND_HOST", "127.0.0.1"), port), KaoyanModularHandler)
    print(f"Kaoyan Hub listening on {srv.server_address}", flush=True)
    srv.serve_forever()
