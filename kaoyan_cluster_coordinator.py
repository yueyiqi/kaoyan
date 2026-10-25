"""Single durable authority; bounded synchronous snapshots and fenced promotion.

Availability deliberately depends on this coordinator. It is not a Raft election.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sqlite3
import threading
import time

from kaoyan_cluster_common import process_lock, rpc


class Coordinator:
    def __init__(self, config):
        self.config, self.lock = config, threading.RLock()
        path = Path(config['state'])
        path.parent.mkdir(parents=True, exist_ok=True)
        self.process_lock = process_lock(str(path) + '.lock')
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.execute('CREATE TABLE IF NOT EXISTS coordinator (singleton INTEGER PRIMARY KEY CHECK(singleton=1), state TEXT NOT NULL)')
        row = self.db.execute('SELECT state FROM coordinator WHERE singleton=1').fetchone()
        self.state = json.loads(row[0]) if row else None
        self.last_acks = {}

    def save(self):
        with self.db:
            self.db.execute('INSERT OR REPLACE INTO coordinator VALUES (1,?)', (json.dumps(self.state),))

    def call(self, node, data):
        return rpc(self.config['workers'][node], self.config['token'], data,
                   timeout=self.config.get('rpc_timeout', 15))

    def initialize(self, primary):
        with self.lock:
            if self.state is not None:
                raise ValueError('Coordinator already initialized')
            package = self.call(primary, {'op': 'snapshot', 'epoch': 1})
            self.state = {'primary': primary, 'epoch': 1, 'snapshot': package, 'pending': None}
            self.save()
            return self.synchronize()

    def synchronize(self, replace=False):
        full_snap = self.state['snapshot']
        meta_snap = {k: v for k, v in full_snap.items() if k != 'database'}
        def send(node):
            try:
                role = 'leader' if node == self.state['primary'] else 'replica'
                ack = self.last_acks.get(node, {})
                use_meta = bool(ack.get('ok') and ack.get('version') == full_snap['version'])
                result = self.call(node, {'op': 'install', 'epoch': self.state['epoch'],
                    'snapshot': meta_snap if use_meta else full_snap,
                    'replace_unacknowledged': replace, 'role': role})
                if result.get('need_snapshot'):
                    result = self.call(node, {'op': 'install', 'epoch': self.state['epoch'],
                        'snapshot': full_snap, 'replace_unacknowledged': replace, 'role': role})
                if result['tables'] != full_snap['tables'] or result['schema_sha256'] != full_snap['schema_sha256']:
                    raise ValueError('Replica content differs')
                return node, {'ok': True, 'version': result['version']}
            except Exception as exc:
                return node, {'ok': False, 'error': type(exc).__name__}
        with ThreadPoolExecutor(max_workers=len(self.config['workers'])) as pool:
            self.last_acks = dict(pool.map(send, self.config['workers']))
        if sum(bool(v['ok']) for v in self.last_acks.values()) < 2:
            raise RuntimeError('Fewer than two durable worker acknowledgements')
        if not self.last_acks[self.state['primary']]['ok']:
            raise RuntimeError('Primary unavailable; explicit switchover required')
        return self.status()

    def recover(self):
        """Resume the persisted input/result before allowing any later operation."""
        pending = self.state['pending']
        unmodified_read = False
        if pending and pending['stage'] == 'execute':
            result = self.call(self.state['primary'], {'op': 'execute', 'epoch': self.state['epoch'],
                'version': self.state['snapshot']['version'], 'request': pending['request']})
            if result.get('snapshot') is not None:
                self.state['snapshot'] = result['snapshot']
                self.last_acks[self.state['primary']] = {'ok': True, 'version': result['snapshot']['version']}
            else:
                unmodified_read = bool(result.get('unmodified'))
            pending.update(stage='replicate', response=result['response'])
            self.save()  # Authoritative result is durable before replica ACK or client reply.
        if not unmodified_read:
            self.synchronize()
        if pending:
            response = pending['response']
            self.state['pending'] = None
            self.save()
            return response

    def request(self, request):
        with self.lock:
            if self.state is None:
                raise RuntimeError('Cluster has not been initialized')
            if self.state['pending']:
                self.recover()
            # Also revalidates restarted workers before each write/read and repairs drift.
            self.synchronize()
            self.state['pending'] = {'stage': 'execute', 'request': request}
            self.save()
            return self.recover()

    def switch(self, target):
        with self.lock:
            if self.state is None or target not in self.config['workers']:
                raise ValueError('Unknown target or uninitialized cluster')
            start = time.monotonic()
            # Persist new authority first: restart cannot revive the previous primary.
            self.state['primary'] = target
            self.state['epoch'] += 1
            self.save()
            self.synchronize(replace=True)
            if self.state['pending']:
                self.recover()
            return {**self.status(), 'switch_ms': round((time.monotonic() - start) * 1000, 2)}

    def status(self):
        if self.state is None:
            return {'initialized': False}
        return {'initialized': True, 'primary': self.state['primary'], 'epoch': self.state['epoch'],
                'version': self.state['snapshot']['version'], 'pending': bool(self.state['pending']),
                'acks': self.last_acks, 'tables': self.state['snapshot']['tables']}

    def control(self, command):
        with self.lock:
            if command['op'] == 'initialize':
                return self.initialize(command['primary'])
            if command['op'] == 'switch':
                return self.switch(command['target'])
            if command['op'] == 'recover':
                self.recover()
                return self.status()
            if command['op'] == 'status':
                return self.status()
            raise ValueError('Unsupported coordinator operation')
