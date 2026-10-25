"""Operator CLI; credentials are read on the deployment host, never pasted by users."""
import argparse
import json
from pathlib import Path
import shlex
import subprocess
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['status', 'recover', 'switch'])
    parser.add_argument('target', nargs='?', choices=['HP', 'W1', 'S1'])
    parser.add_argument('--ssh', dest='ssh_host')
    parser.add_argument('--include-tables', action='store_true')
    parser.add_argument('--config', type=Path, default=Path.home()/'kaoyan_live_20261024/gateway.json')
    args = parser.parse_args()
    if args.operation == 'switch' and not args.target:
        parser.error('switch requires HP, W1 or S1')
    if args.ssh_host:
        command = 'python3 ~/kaoyan_live_20261024/app/kaoyan_cluster_admin.py ' + shlex.quote(args.operation)
        if args.target:
            command += ' ' + shlex.quote(args.target)
        if args.include_tables:
            command += ' --include-tables'
        raise SystemExit(subprocess.call(['ssh', '-o', 'BatchMode=yes', args.ssh_host, command]))
    config = json.loads(args.config.read_text(encoding='utf-8-sig'))
    request = urllib.request.Request('http://127.0.0.1:' + str(config['port']) + '/_cluster/control',
        data=json.dumps({'op': args.operation, 'target': args.target}).encode(),
        headers={'Authorization': 'Bearer ' + config['token'], 'Content-Type': 'application/json'})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request, timeout=90) as response:
        result = json.loads(response.read())
    # A compact operating summary avoids dumping credentials or application contents unless requested.
    out = result if args.include_tables else {k: v for k, v in result.items() if k != 'tables'}
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
