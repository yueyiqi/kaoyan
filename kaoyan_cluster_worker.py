"""Native OS worker: no public business writes; authenticated coordinator RPC only."""
from __future__ import annotations
from contextlib import closing
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import platform
import sqlite3
import sys
import threading
import time

from kaoyan_cluster_common import MAX_RPC_BYTES, atomic_json, install, process_lock, schema_digest, snapshot
from kaoyan_portable import backup, inventory, validate
from kaoyan_repository import REPO
from kaoyan_runtime import PG_DSN
from kaoyan_cluster_tx import execute, initialize


class Worker:
    def __init__(self, config):
        if PG_DSN:
            raise ValueError('Cluster mode requires one authoritative SQLite engine')
        self.config, self.lock = config, threading.Lock()
        self.database = REPO.sqlite_path
        self.database.parent.mkdir(parents=True, exist_ok=True)
        self.process_lock = process_lock(str(self.database) + '.worker.lock')
        self.fence_path = self.database.with_suffix('.fence.json')
        self.epoch = json.loads(self.fence_path.read_text()).get('epoch', 0) if self.fence_path.exists() else 0
        self.role = 'replica'  # Restart never grants write authority by itself.
        if not self.database.exists():
            REPO.init_and_migrate_both_engines()
        with closing(sqlite3.connect(self.database)) as conn:
            try:
                validate(conn)
                initialize(conn)
            except (RuntimeError, sqlite3.Error):
                pass  # Damaged existing DB stays fenced until full snapshot repair.

    def status(self):
        structure = None
        with closing(sqlite3.connect(self.database)) as conn:
            try:
                validate(conn)
                tables = inventory(conn)
                version = conn.execute('SELECT version FROM ha_cluster_meta').fetchone()[0]
                structure = schema_digest(conn)
                ready = True
            except (RuntimeError, sqlite3.Error):
                ready, version, tables = False, None, {}
        return {'node': self.config['node'], 'os': platform.system(), 'machine': platform.machine(),
                'python': platform.python_version(), 'sqlite': sqlite3.sqlite_version, 'pid': os.getpid(),
                'database': str(self.database), 'ready': ready, 'version': version,
                'role': self.role, 'epoch': self.epoch, 'tables': tables, 'schema_sha256': structure}

    def command(self, data):
        with self.lock:
            op = data.get('op')
            if op == 'status':
                return self.status()
            epoch = int(data['epoch'])
            if epoch < self.epoch:
                raise ValueError('Stale epoch rejected')
            if op == 'install':
                self.role = 'replica'
                atomic_json(self.fence_path, {'epoch': epoch})
                self.epoch = epoch
                current = self.status()
                package = data['snapshot']
                if current['ready'] and epoch == data.get('previous_epoch', epoch) and current['version'] > package['version']:
                    # A higher epoch explicitly discards an unacknowledged old-primary branch.
                    if not data.get('replace_unacknowledged', False):
                        raise ValueError('Snapshot would roll version backwards')
                need_install = (not current['ready'] or current['tables'] != package['tables']
                                or current['schema_sha256'] != package['schema_sha256']
                                or current['version'] != package['version'])
                if need_install and 'database' not in package:
                    return {'need_snapshot': True, **current}
                if not current['ready']:
                    saved = self.database.with_name(self.database.name + '.damaged-' + str(time.time_ns()))
                    with closing(sqlite3.connect(self.database)) as conn:
                        backup(conn, saved)
                if need_install:
                    install(package, self.database)
                self.role = data.get('role', 'replica')
                if self.role not in ('replica', 'leader'):
                    self.role = 'replica'
                    raise ValueError('Invalid worker role')
                result = self.status() if need_install else {**current, 'role': self.role, 'epoch': self.epoch}
                if result['tables'] != package['tables'] or result['schema_sha256'] != package['schema_sha256'] or not result['ready']:
                    raise RuntimeError('Installed replica does not match')
                return result
            if op == 'snapshot':
                return snapshot(self.database)
            if op == 'execute':
                if epoch != self.epoch or self.role != 'leader':
                    raise ValueError('Write authority fenced')
                before_ver = int(data['version'])
                response = execute(data['request'], before_ver)
                if data['request'].get('method') in ('GET', 'HEAD'):
                    with closing(sqlite3.connect(self.database)) as conn:
                        after_ver = conn.execute('SELECT version FROM ha_cluster_meta WHERE singleton=1').fetchone()[0]
                    if after_ver == before_ver:
                        return {'response': response, 'snapshot': None, 'unmodified': True}
                return {'response': response, 'snapshot': snapshot(self.database)}
            raise ValueError('Unsupported cluster operation')


class WorkerHandler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_GET(self):
        self.send_error(404)

    def do_POST(self):
        if self.path != '/_cluster/rpc' or not hmac.compare_digest(
                self.headers.get('Authorization', ''), 'Bearer ' + self.server.worker.config['token']):
            self.send_error(403)
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= MAX_RPC_BYTES:
                raise ValueError('Invalid RPC size')
            data = json.loads(self.rfile.read(length))
            result, code = self.server.worker.command(data), 200
        except Exception as exc:
            result, code = {'error': type(exc).__name__ + ': ' + str(exc)}, 409
        body = json.dumps(result, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main(config_path):
    config = json.loads(Path(config_path).read_text(encoding='utf-8-sig'))
    server = ThreadingHTTPServer(('127.0.0.1', config['port']), WorkerHandler)
    server.worker = Worker(config)
    print(json.dumps({'listening': server.server_address, 'node': config['node'], 'pid': os.getpid()}), flush=True)
    server.serve_forever()


if __name__ == '__main__':
    main(sys.argv[1])
