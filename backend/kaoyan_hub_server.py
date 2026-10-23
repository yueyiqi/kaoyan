#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import hashlib, json, math, os, sqlite3
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get('KAOYAN_DB_PATH', str(BASE_DIR / 'db_volume' / 'kaoyan_hub.sqlite3')))
MIGRATION_SQL = Path(os.environ.get('KAOYAN_MIGRATION_SQL', str(BASE_DIR / 'db_migrations' / 'V001__init_kaoyan_8tables.sql')))
BACKUP_DIR = Path(os.environ.get('KAOYAN_BACKUP_DIR', str(BASE_DIR / 'db_backups')))
_default_html = BASE_DIR / 'index.html'
HTML_PATH = Path(os.environ.get('KAOYAN_HTML_PATH', str(_default_html if _default_html.exists() else '/app/index.html')))

def init_and_migrate_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    if MIGRATION_SQL.exists():
        conn.executescript(MIGRATION_SQL.read_text(encoding='utf-8'))
    conn.commit()
    with open(BACKUP_DIR / 'latest_schema_and_data.sql', 'w', encoding='utf-8') as f:
        for line in conn.iterdump():
            f.write(f'{line}\n')
    conn.close()

def verify_bearer(headers) -> str | None:
    auth = headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    token = auth[7:].strip()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    row = c.execute('SELECT user_id FROM sys_users WHERE token_secret = ?', (token,)).fetchone()
    conn.close()
    if row:
        return row[0]
    if token.startswith('kaoyan-scholar-') and token.endswith('-kaoyan2026'):
        parts = token.split('-')
        if len(parts) >= 4:
            return parts[2]
    return None

class KaoyanDockerHandler(BaseHTTPRequestHandler):
    def _send_json(self, code, payload):
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/api/health':
            conn = sqlite3.connect(DB_PATH)
            tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()]
            conn.close()
            return self._send_json(200, {
                'status': 'ok',
                'service': 'kaoyan-english-hub-docker',
                'domain': 'kaoyan.elenalyl.top',
                'containerized': True,
                'db_engine': 'sqlite3_wal_volume',
                'tables_count': len(tables),
                'tables': sorted(tables),
            })
        if parsed.path == '/api/state':
            qs = parse_qs(parsed.query)
            uid = verify_bearer(self.headers) or qs.get('user_id', ['colleague_a'])[0]
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            p_cnt = c.execute('SELECT COUNT(*) FROM exam_passages').fetchone()[0] + 2
            anchor_row = c.execute('SELECT * FROM user_progress_anchors WHERE user_id = ?', (uid,)).fetchone()
            vocab_rows = [dict(r) for r in c.execute('SELECT lemma as word, lemma, syllabus_tier, lookup_count, last_seen_at, days_since_seen, urgency_score, exam_source, contextual_meaning FROM user_vocab_ledger WHERE user_id = ? ORDER BY urgency_score DESC', (uid,)).fetchall()]
            conn.close()
            return self._send_json(200, {
                'status': 'ok',
                'user_id': uid,
                'passage_count': p_cnt,
                'anchor': dict(anchor_row) if anchor_row else {'last_para_idx': 2, 'streak_days': 12},
                'vocab': vocab_rows,
            })
        if parsed.path in ('/', '/index.html') or not parsed.path.startswith('/api/'):
            html = HTML_PATH.read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(html)))
            self.end_headers()
            self.wfile.write(html)
            return
        self._send_json(404, {'status': 'not_found'})

    def do_POST(self):
        length = int(self.headers.get('Content-Length', '0'))
        raw = self.rfile.read(length).decode('utf-8') if length > 0 else '{}'
        try:
            data = json.loads(raw)
        except Exception:
            data = {}
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if self.path == '/api/auth/login':
            u = data.get('username', 'colleague_a').strip() or 'colleague_a'
            k = data.get('passcode', '').strip()
            if k != 'kaoyan2026':
                return self._send_json(401, {'status': 'unauthorized', 'message': '学籍口令错误'})
            token = f'kaoyan-scholar-{u}-kaoyan2026'
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute('INSERT OR IGNORE INTO sys_users VALUES (?, ?, ?, ?, ?, ?, ?)', (u, u, u, 'SCHOLAR', k, token, now))
            c.execute('INSERT OR IGNORE INTO user_progress_anchors VALUES (?, ?, 2, ?, 2, ?, 12, 1, ?)', (u, 'P2024_EN1_T1', 'sp-sent-2', '', now))
            conn.commit()
            anchor = dict(c.execute('SELECT * FROM user_progress_anchors WHERE user_id = ?', (u,)).fetchone())
            conn.close()
            return self._send_json(200, {'status': 'ok', 'user_id': u, 'role': 'SCHOLAR', 'token': token, 'anchor': anchor})

        uid = verify_bearer(self.headers)
        if not uid:
            return self._send_json(401, {'status': 'guest_sandbox_locked', 'message': '当前为访客只读沙箱，请先登录专属学籍账号以写入云端数据库'})

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        if self.path == '/api/progress/anchor':
            para_idx = int(data.get('last_para_idx', 2))
            span_id = data.get('last_span_id', '')
            c.execute('UPDATE user_progress_anchors SET last_para_idx = ?, last_span_id = ?, rev_no = rev_no + 1, updated_at = ? WHERE user_id = ?', (para_idx, span_id, now, uid))
            conn.commit()
            conn.close()
            return self._send_json(200, {'status': 'ok', 'user_id': uid, 'last_para_idx': para_idx})

        if self.path == '/api/ingest/passage':
            title = data.get('title', '2025 英语一 新导入真题')
            txt = data.get('raw_text', '')
            h = hashlib.sha256(txt.encode('utf-8')).hexdigest()[:16]
            pid = f'P_{uid}_{h}'
            c.execute('INSERT OR REPLACE INTO exam_passages VALUES (?, ?, 2025, ?, ?, ?, ?, ?, ?, ?)', (pid, uid, '英语一', 'Text', title, json.dumps([txt], ensure_ascii=False), '[]', h, now))
            conn.commit()
            p_cnt = c.execute('SELECT COUNT(*) FROM exam_passages').fetchone()[0] + 2
            conn.close()
            return self._send_json(200, {'status': 'ok', 'passage_id': pid, 'user_id': uid, 'passage_count': p_cnt})

        if self.path in ('/api/ingest/vocab', '/api/vocab/lookup'):
            lemma = data.get('lemma', 'accommodate').lower()
            c.execute('INSERT INTO user_vocab_ledger (user_id, lemma, syllabus_tier, lookup_count, last_seen_at, days_since_seen, urgency_score, exam_source, contextual_meaning) VALUES (?, ?, ?, 1, ?, 0.0, 0.65, ?, ?) ON CONFLICT(user_id, lemma) DO UPDATE SET lookup_count = lookup_count + 1, last_seen_at = excluded.last_seen_at', (uid, lemma, 'CORE_1800', now, '真题实时查词', '学籍云端同步词条'))
            conn.commit()
            conn.close()
            return self._send_json(200, {'status': 'ok', 'user_id': uid, 'lemma': lemma})

        conn.close()
        return self._send_json(200, {'status': 'ok', 'user_id': uid, 'saved_at': now})

if __name__ == '__main__':
    init_and_migrate_db()
    srv = HTTPServer(('0.0.0.0', 60231), KaoyanDockerHandler)
    print('Kaoyan Docker Hub listening on 0.0.0.0:60231', flush=True)
    srv.serve_forever()
