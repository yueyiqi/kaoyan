"""One config-based launcher for Windows Task Scheduler, systemd and launchd."""
import json
import os
from pathlib import Path
import sys


if __name__ == '__main__':
    config_path = str(Path(sys.argv[1]).resolve())
    config = json.loads(Path(config_path).read_text(encoding='utf-8-sig'))
    # Containers mount credentials read-only and let Docker bound/rotate stdout.
    if os.environ.get('KAOYAN_LOG_STDIO') != '1':
        log = open(Path(config_path).with_suffix('.log'), 'a', encoding='utf-8', buffering=1)
        sys.stdout = sys.stderr = log
    os.environ['KAOYAN_PG_DSN'] = ''
    if config.get('mode', 'worker') == 'worker':
        if config.get('require_existing_data') and not Path(config['database']).is_file():
            raise RuntimeError('Production database is absent; restore the authoritative backup first')
        os.environ['KAOYAN_DB_PATH'] = config['database']
        os.environ['KAOYAN_BACKUP_DIR'] = config['backups']
        from kaoyan_cluster_worker import main
    else:
        if config.get('require_existing_data') and not Path(config['state']).is_file():
            raise RuntimeError('Coordinator state is absent; restore the authoritative backup first')
        from kaoyan_cluster_gateway import main
    main(config_path)
