"""Read-only liveness for Docker; no recovery, credential output or database writes."""
import json
from pathlib import Path
import sys
import urllib.request


def healthy(path):
    cfg = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    worker = cfg.get('mode', 'worker') == 'worker'
    route = '/_cluster/rpc' if worker else '/_cluster/control'
    req = urllib.request.Request('http://127.0.0.1:' + str(cfg['port']) + route,
        data=b'{"op":"status"}', headers={'Authorization': 'Bearer ' + cfg['token'],
                                           'Content-Type': 'application/json'})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(req, timeout=5) as response:
        result = json.load(response)
    return bool(result.get('ready' if worker else 'initialized'))


if __name__ == '__main__':
    try:
        ok = healthy(sys.argv[1])
    except Exception:
        ok = False
    raise SystemExit(0 if ok else 1)
