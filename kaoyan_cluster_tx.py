"""Execute unchanged application routes in one SQLite transaction and capture reply."""
from __future__ import annotations
import base64
from email.message import Message
import hashlib
import io
import json
import sqlite3

from kaoyan_hub_server import KaoyanModularHandler
from kaoyan_repository import REPO, REQUEST_TRANSACTION


def initialize(conn):
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS ha_cluster_meta
          (singleton INTEGER PRIMARY KEY CHECK(singleton=1), version INTEGER NOT NULL);
        INSERT OR IGNORE INTO ha_cluster_meta VALUES (1,0);
        CREATE TABLE IF NOT EXISTS ha_request_receipts
          (request_key TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, response TEXT NOT NULL);
    ''')


class TransactionConnection:
    """Legacy commit/close calls cannot split the request's atomic transaction."""
    def __init__(self, conn):
        self.conn, self.failed = conn, False

    def execute(self, *args):
        try:
            return self.conn.execute(*args)
        except sqlite3.Error:
            self.failed = True
            raise

    def commit(self):
        pass

    def close(self):
        pass


class CapturedHandler(KaoyanModularHandler):
    def _send_json(self, code, payload, **kwargs):
        if 'engine' in payload:
            payload['engine'] = 'portable_sqlite'
        kwargs['engine_hdr'] = 'portable_sqlite'
        return super()._send_json(code, payload, **kwargs)

    def send_response(self, code, message=None):
        self.code = code

    def send_header(self, key, value):
        self.output_headers[key] = value

    def end_headers(self):
        pass


def dispatch(request):
    handler = CapturedHandler.__new__(CapturedHandler)
    handler.command, handler.path = request['method'], request['path']
    handler.request_version = 'HTTP/1.1'
    handler.close_connection = True
    handler.client_address = (request.get('client_ip', '127.0.0.1'), 0)
    handler.headers = Message()
    for k, v in request['headers'].items():
        handler.headers[k] = v
    body = base64.b64decode(request['body'], validate=True)
    if 'Content-Length' in handler.headers:
        del handler.headers['Content-Length']
    handler.headers['Content-Length'] = str(len(body))
    handler.rfile, handler.wfile = io.BytesIO(body), io.BytesIO()
    handler.output_headers, handler.code = {}, 500
    getattr(handler, 'do_' + handler.command)()
    return {'code': handler.code, 'headers': handler.output_headers,
            'body': base64.b64encode(handler.wfile.getvalue()).decode()}


def execute(request, expected_version):
    # Fingerprint includes authentication so a key cannot replay another user's data.
    headers = {k.lower(): v for k, v in request['headers'].items()}
    fingerprint = hashlib.sha256(json.dumps(
        [request['method'], request['path'], headers.get('authorization', ''), request['body']],
        ensure_ascii=False).encode()).hexdigest()
    key = headers.get('x-idempotency-key') or request['request_id']
    conn = REPO.get_sqlite_conn()
    conn.execute('PRAGMA synchronous=FULL')
    try:
        conn.execute('BEGIN IMMEDIATE')
        row = conn.execute('SELECT fingerprint,response FROM ha_request_receipts WHERE request_key=?', (key,)).fetchone()
        if row:
            if row[0] != fingerprint:
                return {'code': 409, 'headers': {'Content-Type': 'application/json'},
                        'body': base64.b64encode(b'{"status":"idempotency_conflict"}').decode()}
            return json.loads(row[1])
        version = conn.execute('SELECT version FROM ha_cluster_meta WHERE singleton=1').fetchone()[0]
        if version != expected_version:
            raise ValueError('Worker version differs from coordinator')
        transaction = TransactionConnection(conn)
        REQUEST_TRANSACTION.connection = transaction
        before = conn.total_changes
        try:
            response = dispatch(request)
        except (ValueError, TypeError, OverflowError):
            # Deterministic bad input must not poison the coordinator's pending queue.
            # Discard every partial route write before recording its rejected outcome.
            conn.rollback()
            conn.execute('BEGIN IMMEDIATE')
            transaction.failed = False
            response = {'code': 422, 'headers': {'Content-Type': 'application/json'},
                        'body': base64.b64encode(b'{"status":"validation_error"}').decode()}
        if transaction.failed or response['code'] >= 500:
            raise RuntimeError('Application transaction failed; no partial writes committed')
        # Read-only pages need no durable receipt or replication version increment.
        if conn.total_changes != before or request['method'] == 'POST':
            conn.execute('INSERT INTO ha_request_receipts VALUES (?,?,?)',
                         (key, fingerprint, json.dumps(response, ensure_ascii=False)))
            conn.execute('UPDATE ha_cluster_meta SET version=version+1 WHERE singleton=1')
        conn.commit()
        return response
    finally:
        REQUEST_TRANSACTION.connection = None
        conn.close()
