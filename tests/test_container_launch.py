"""A missing mounted production volume must never bootstrap a fresh database."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ContainerLaunchTests(unittest.TestCase):
    def test_missing_production_volumes_fail_before_initialization(self):
        for mode, key in [('worker', 'database'), ('gateway', 'state')]:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temp:
                base = Path(temp)
                config = base/'runtime.json'
                missing = base/'absent'/'production.sqlite3'
                config.write_text(json.dumps({'mode': mode, key: str(missing),
                                              'require_existing_data': True}))
                config.chmod(0o400)
                result = subprocess.run([sys.executable, str(ROOT/'kaoyan_cluster_launch.py'), str(config)],
                    env=dict(os.environ, KAOYAN_LOG_STDIO='1'), capture_output=True, text=True, timeout=10)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('restore the authoritative backup first', result.stderr)
                self.assertFalse(missing.parent.exists())
                self.assertFalse(config.with_suffix('.log').exists())

    def test_metadata_first_sync_and_readonly_fastpath(self):
        sys.path.insert(0, str(ROOT))
        for stray in (ROOT / 'db_volume').glob('kaoyan_hub.sqlite3.*'):
            if stray.name.endswith(('.fence.json', '.worker.lock')):
                stray.unlink(missing_ok=True)
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            old_db, old_bk, old_pg = os.environ.get('KAOYAN_DB_PATH'), os.environ.get('KAOYAN_BACKUP_DIR'), os.environ.get('KAOYAN_PG_DSN')
            try:
                os.environ['KAOYAN_DB_PATH'] = str(base / 'w.db')
                os.environ['KAOYAN_BACKUP_DIR'] = str(base / 'bk')
                os.environ['KAOYAN_PG_DSN'] = ''
                import importlib, kaoyan_runtime, kaoyan_repository, kaoyan_cluster_worker
                importlib.reload(kaoyan_runtime)
                importlib.reload(kaoyan_repository)
                importlib.reload(kaoyan_cluster_worker)
                w = kaoyan_cluster_worker.Worker({'node': 'W1', 'token': 't', 'port': 0})
                try:
                    snap = w.command({'op': 'snapshot', 'epoch': 1})
                    meta = {k: v for k, v in snap.items() if k != 'database'}
                    res_ok = w.command({'op': 'install', 'epoch': 2, 'snapshot': meta, 'role': 'leader'})
                    self.assertFalse(res_ok.get('need_snapshot', False))
                    self.assertEqual(res_ok['role'], 'leader')
                    self.assertEqual(res_ok['epoch'], 2)
                    meta_diff = dict(meta, version=999)
                    res_need = w.command({'op': 'install', 'epoch': 3, 'snapshot': meta_diff, 'role': 'replica'})
                    self.assertTrue(res_need.get('need_snapshot', False))
                finally:
                    w.process_lock.close()
            finally:
                for k, v in [('KAOYAN_DB_PATH', old_db), ('KAOYAN_BACKUP_DIR', old_bk), ('KAOYAN_PG_DSN', old_pg)]:
                    if v is None:
                        os.environ.pop(k, None)
                    else:
                        os.environ[k] = v


if __name__ == '__main__':
    unittest.main()
