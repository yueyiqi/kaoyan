"""Bounded behavioral preflight; source strings cannot prove browser or data coverage."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

BASE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['audit', 'drilldown-spec', 'full-report'], default='audit')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    result = {'scope': 'Local database and UI-state contract tests; live browser acceptance is separate',
              'inventory_source': 'SQLite table_xinfo; counts are computed, never hardcoded',
              'status': 'NOT_RUN', 'checks': []}
    if args.mode != 'drilldown-spec':
        node = shutil.which('node')
        if not node:
            raise SystemExit('Node is required')
        for command in [[sys.executable, str(BASE/'tests/test_admin_drilldown.py')],
                        [node, str(BASE/'tests/test_admin_ui.js')]]:
            process = subprocess.run(command, capture_output=True, text=True, timeout=60)
            result['checks'].append({'command': command, 'exit': process.returncode})
            if process.returncode:
                print(process.stdout + process.stderr, file=sys.stderr)
        result['status'] = 'PASS' if all(c['exit'] == 0 for c in result['checks']) else 'FAIL'
    if args.out:
        args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return int(result['status'] == 'FAIL')


if __name__ == '__main__':
    raise SystemExit(main())
