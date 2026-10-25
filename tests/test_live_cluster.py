"""Real process/RPC fault tests. Local processes are not claimed as native OS evidence."""
from concurrent.futures import ThreadPoolExecutor
import base64
from contextlib import closing
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from kaoyan_cluster_common import rpc
from kaoyan_runtime import SEED_USERS


def port():
    with closing(socket.socket()) as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


class ClusterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='kaoyan-live-')
        self.base, self.processes, self.logs = Path(self.temp.name), {}, []
        self.token, self.urls, self.commands = uuid.uuid4().hex, {}, {}
        self.addCleanup(self.cleanup)
        for node in ('alpha', 'beta', 'gamma'):
            cfg = {'node': node, 'token': self.token, 'port': port()}
            path = self.base / (node + '.json')
            path.write_text(json.dumps(cfg))
            env = dict(os.environ, KAOYAN_DB_PATH=str(self.base / (node + '.db')),
                       KAOYAN_BACKUP_DIR=str(self.base / 'backups'), KAOYAN_PG_DSN='')
            self.commands[node] = ([sys.executable, str(ROOT / 'kaoyan_cluster_worker.py'), str(path)], env)
            self.start(node)
            self.urls[node] = 'http://127.0.0.1:' + str(cfg['port'])
            self.wait_worker(node)
        cfg = {'token': self.token, 'workers': self.urls, 'port': port(),
               'state': str(self.base / 'coordinator.db'), 'rpc_timeout': 1}
        path = self.base / 'gateway.json'
        path.write_text(json.dumps(cfg))
        self.commands['gateway'] = ([sys.executable, str(ROOT / 'kaoyan_cluster_gateway.py'), str(path)], os.environ.copy())
        self.url = 'http://127.0.0.1:' + str(cfg['port'])
        self.start('gateway')
        for _ in range(100):
            try:
                self.control('status')
                break
            except OSError:
                time.sleep(.03)
        self.control('initialize', primary='alpha')
        self.auth = 'Bearer ' + next(r[6] for r in SEED_USERS if r[0] == 'colleague_a')

    def start(self, node):
        argv, env = self.commands[node]
        log = (self.base / (node + '.log')).open('ab')
        self.logs.append(log)
        self.processes[node] = subprocess.Popen(argv, env=env, stdout=log, stderr=log)

    def stop(self, node):
        proc = self.processes.pop(node)
        proc.kill()
        proc.wait(timeout=5)

    def cleanup(self):
        for node in list(self.processes):
            self.stop(node)
        for log in self.logs:
            log.close()
        self.temp.cleanup()

    def wait_worker(self, node):
        for _ in range(100):
            try:
                return rpc(self.urls[node], self.token, {'op': 'status'})
            except OSError:
                time.sleep(.03)
        self.fail('worker did not start')

    def http(self, path, data=None, key=None, auth=None):
        headers = {'Content-Type': 'application/json'}
        if auth:
            headers['Authorization'] = auth
        if key:
            headers['X-Idempotency-Key'] = key
        req = urllib.request.Request(self.url + path, data=json.dumps(data).encode() if data is not None else None, headers=headers)
        try:
            response = urllib.request.urlopen(req, timeout=30)
        except urllib.error.HTTPError as exc:
            response = exc
        with response:
            return response.status, json.loads(response.read())

    def control(self, op, **kwargs):
        code, data = self.http('/_cluster/control', {'op': op, **kwargs}, auth='Bearer ' + self.token)
        if code != 200:
            raise RuntimeError((code, data))
        return data

    def write(self, key='once', lemma='portable'):
        return self.http('/api/vocab/lookup', {'lemma': lemma}, key, self.auth)

    def count(self, node, lemma='portable'):
        with closing(sqlite3.connect(self.base / (node + '.db'))) as conn:
            row = conn.execute('SELECT lookup_count FROM user_vocab_ledger WHERE lemma=?', (lemma,)).fetchone()
            return row[0] if row else 0

    def test_concurrent_writes_and_live_switches(self):
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(self.write, 'parallel-' + str(i)) for i in range(12)]
            self.control('switch', target='beta')
            self.control('switch', target='gamma')
            self.assertTrue(all(f.result()[0] == 200 for f in futures))
        state = self.control('recover')
        self.assertEqual(state['primary'], 'gamma')
        for node in self.urls:
            self.assertEqual(self.count(node), 12)
            self.assertEqual(rpc(self.urls[node], self.token, {'op': 'status'})['tables'], state['tables'])

    def test_replay_conflict_permissions_and_fencing(self):
        first = self.write()
        self.assertEqual(first[0], 200)
        self.control('switch', target='beta')
        self.assertEqual(self.write(), first)
        self.assertEqual(self.write(lemma='different')[0], 409)
        self.assertEqual(self.count('beta'), 1)
        code, _ = self.http('/api/admin/users', {'username': 'forbidden', 'passcode': 'dummy'}, 'deny', self.auth)
        self.assertEqual(code, 403)
        with self.assertRaises(urllib.error.HTTPError):
            rpc(self.urls['alpha'], self.token, {'op': 'execute', 'epoch': 1, 'version': 0, 'request': {}})
        with self.assertRaises(urllib.error.HTTPError):
            rpc(self.urls['beta'], 'wrong-token', {'op': 'status'})

    def test_replica_loss_pending_restart_and_repair(self):
        self.stop('gamma')
        self.assertEqual(self.write()[0], 200)
        self.stop('beta')
        self.assertEqual(self.write('blocked')[0], 503)
        self.assertEqual(self.count('alpha'), 1)  # no quorum: no new execution
        self.stop('gateway')
        self.start('beta')
        self.wait_worker('beta')
        self.start('gateway')
        time.sleep(.3)
        self.assertEqual(self.write('blocked')[0], 200)
        self.start('gamma')
        self.wait_worker('gamma')
        self.control('recover')
        self.assertTrue(all(self.count(n) == 2 for n in self.urls))

    def test_primary_crash_and_native_missing_table_restore(self):
        self.assertEqual(self.write()[0], 200)
        self.stop('alpha')
        self.control('switch', target='beta')
        self.assertEqual(self.write('second')[0], 200)
        self.start('alpha')
        self.wait_worker('alpha')
        with closing(sqlite3.connect(self.base / 'gamma.db')) as conn:
            conn.execute('DROP TABLE user_vocab_ledger')
            conn.commit()
        self.assertFalse(rpc(self.urls['gamma'], self.token, {'op': 'status'})['ready'])
        self.control('recover')
        self.assertTrue(list(self.base.glob('gamma.db.damaged-*')))
        self.assertTrue(all(self.count(n) == 2 for n in self.urls))

    def test_internal_rpc_ignores_broken_system_proxy(self):
        try:
            with patch.dict(os.environ, {'http_proxy': 'http://127.0.0.1:9', 'HTTP_PROXY': 'http://127.0.0.1:9', 'no_proxy': '', 'NO_PROXY': ''}):
                urllib.request.install_opener(urllib.request.build_opener())
                self.assertTrue(rpc(self.urls['alpha'], self.token, {'op': 'status'})['ready'])
        finally:
            urllib.request.install_opener(urllib.request.build_opener())

    def test_invalid_numbers_cannot_poison_durable_queue(self):
        for i, data in enumerate([{'lemma': 'bad', 'days_since_seen': 'invalid'}, {'lemma': 'bad', 'days_since_seen': 'nan'}, {'lemma': 'bad', 'lookup_count': None}]):
            code, _ = self.http('/api/vocab/lookup', data, 'invalid-' + str(i), self.auth)
            self.assertIn(code, (400, 422))
        self.assertEqual(self.write()[0], 200)
        self.assertFalse(self.control('status')['pending'])

    def test_cross_user_note_and_essay_ids_are_isolated(self):
        other = 'Bearer ' + next(r[6] for r in SEED_USERS if r[0] == 'scholar_b')
        self.assertEqual(self.http('/api/notes', {'span_id': 'owned-note', 'selected_text': 'private note', 'user_comment': 'private'}, 'owner-note', self.auth)[0], 200)
        self.assertEqual(self.http('/api/notes', {'span_id': 'owned-note', 'selected_text': 'attacker', 'user_comment': 'overwritten'}, 'attacker-note', other)[0], 403)
        self.assertEqual(self.http('/api/annotations/promote', {'span_id': 'owned-note'}, 'attacker-promote', other)[0], 403)
        self.assertEqual(self.http('/api/essay', {'snippet_id': 'owned-essay', 'content_en': 'private essay'}, 'owner-essay', self.auth)[0], 200)
        self.assertEqual(self.http('/api/essay', {'snippet_id': 'owned-essay', 'content_en': 'attacker'}, 'attacker-essay', other)[0], 403)
        with closing(sqlite3.connect(self.base / 'alpha.db')) as conn:
            self.assertEqual(conn.execute("SELECT user_comment FROM annotation_spans WHERE span_id='owned-note'").fetchone()[0], 'private')

    def test_schema_only_changes_replicate(self):
        with closing(sqlite3.connect(self.base / 'alpha.db')) as conn:
            conn.execute('CREATE INDEX custom_display_name ON sys_users(display_name)')
            conn.commit()
        self.stop('gateway')
        for suffix in ('', '-wal', '-shm'):
            (self.base / ('coordinator.db' + suffix)).unlink(missing_ok=True)
        self.start('gateway')
        time.sleep(.3)
        self.control('initialize', primary='alpha')
        for node in self.urls:
            with closing(sqlite3.connect(self.base / (node + '.db'))) as conn:
                self.assertIsNotNone(conn.execute("SELECT name FROM sqlite_master WHERE name='custom_display_name'").fetchone())

    def test_committed_worker_reply_lost_before_coordinator_save(self):
        self.stop('gateway')
        request = {'method': 'POST', 'path': '/api/vocab/lookup', 'request_id': 'lost-reply',
                   'headers': {'Authorization': self.auth, 'X-Idempotency-Key': 'lost-reply'},
                   'body': base64.b64encode(json.dumps({'lemma': 'portable'}).encode()).decode()}
        with closing(sqlite3.connect(self.base / 'coordinator.db')) as conn:
            state = json.loads(conn.execute('SELECT state FROM coordinator').fetchone()[0])
            state['pending'] = {'stage': 'execute', 'request': request}
            conn.execute('UPDATE coordinator SET state=?', (json.dumps(state),))
            conn.commit()
        rpc(self.urls['alpha'], self.token, {'op': 'execute', 'epoch': state['epoch'],
            'version': state['snapshot']['version'], 'request': request})
        self.assertEqual(self.count('alpha'), 1)
        self.start('gateway')
        time.sleep(.3)
        self.assertEqual(self.write('lost-reply')[0], 200)
        self.assertTrue(all(self.count(n) == 1 for n in self.urls))

    def test_transaction_rollback_on_swallowed_audit_error(self):
        # Add a failing audit trigger to authority, then reboot coordinator from that DB.
        with closing(sqlite3.connect(self.base / 'alpha.db')) as conn:
            conn.execute("CREATE TRIGGER reject_audit BEFORE INSERT ON sys_rbac_audit_log BEGIN SELECT RAISE(ABORT,'audit failure'); END")
            conn.commit()
        self.stop('gateway')
        for suffix in ('', '-wal', '-shm'):
            (self.base / ('coordinator.db' + suffix)).unlink(missing_ok=True)
        self.start('gateway')
        time.sleep(.3)
        self.control('initialize', primary='alpha')
        admin = 'Bearer ' + next(r[6] for r in SEED_USERS if r[0] == 'admin')
        code, _ = self.http('/api/admin/users', {'username': 'atomic_user', 'passcode': 'dummy'}, 'atomic', admin)
        self.assertEqual(code, 503)
        with closing(sqlite3.connect(self.base / 'alpha.db')) as conn:
            self.assertEqual(conn.execute("SELECT count(*) FROM sys_users WHERE user_id='atomic_user'").fetchone()[0], 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
