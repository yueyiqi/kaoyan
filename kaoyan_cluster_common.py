"""Bounded, authenticated loopback transport and durable deployment primitives."""
from __future__ import annotations
import base64
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import urllib.request
from urllib.parse import urlsplit

from kaoyan_portable import backup, inventory, validate

MAX_RPC_BYTES = 64 * 1024 * 1024


def digest(value):
    return hashlib.sha256(value).hexdigest()


def schema_digest(conn):
    rows = conn.execute('SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name').fetchall()
    return digest(json.dumps([tuple(row) for row in rows], ensure_ascii=False).encode())


def snapshot(database):
    with tempfile.TemporaryDirectory(prefix='kaoyan-snapshot-') as temp:
        dest = Path(temp) / 'database.sqlite3'
        with closing(sqlite3.connect(database)) as source:
            backup(source, dest)
        raw = dest.read_bytes()
        with closing(sqlite3.connect(dest)) as conn:
            validate(conn)
            tables = inventory(conn)
            structure = schema_digest(conn)
            version = conn.execute('SELECT version FROM ha_cluster_meta WHERE singleton=1').fetchone()[0]
    return {'database': base64.b64encode(raw).decode(), 'sha256': digest(raw),
            'tables': tables, 'schema_sha256': structure, 'version': version}


def install(package, database):
    raw = base64.b64decode(package['database'], validate=True)
    if len(raw) > MAX_RPC_BYTES // 2 or digest(raw) != package['sha256']:
        raise ValueError('Invalid snapshot checksum or size')
    with tempfile.TemporaryDirectory(prefix='kaoyan-install-') as temp:
        source_path = Path(temp) / 'database.sqlite3'
        source_path.write_bytes(raw)
        with closing(sqlite3.connect(source_path)) as source:
            validate(source)
            if inventory(source) != package['tables']:
                raise ValueError('Snapshot table content mismatch')
            if schema_digest(source) != package['schema_sha256']:
                raise ValueError('Snapshot structure mismatch')
            if source.execute('SELECT version FROM ha_cluster_meta').fetchone()[0] != package['version']:
                raise ValueError('Snapshot version mismatch')
            # Backup API atomically replaces the target; no open application connections.
            with closing(sqlite3.connect(database)) as target:
                target.execute('PRAGMA synchronous=FULL')
                source.backup(target)
                validate(target)
                if inventory(target) != package['tables']:
                    raise ValueError('Installed database content mismatch')
                if schema_digest(target) != package['schema_sha256']:
                    raise ValueError('Installed database structure mismatch')


def rpc(url, token, payload, timeout=15):
    endpoint = urlsplit(url)
    if endpoint.scheme != 'http' or endpoint.hostname not in ('127.0.0.1', 'localhost', '::1') or endpoint.username:
        raise ValueError('Internal RPC must use a loopback endpoint over the managed SSH transport')
    data = json.dumps(payload, ensure_ascii=False).encode()
    request = urllib.request.Request(url + '/_cluster/rpc', data=data,
        headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request, timeout=timeout) as response:
        result = json.loads(response.read(MAX_RPC_BYTES + 1))
    if result.get('error'):
        raise RuntimeError(result['error'])
    return result


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name, dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(value, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def process_lock(path):
    stream = open(path, 'a+b')
    if os.name == 'nt':
        import msvcrt
        stream.seek(0)
        if not stream.read(1):
            stream.write(b'0')
            stream.flush()
        stream.seek(0)
        msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        import fcntl
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
    return stream
