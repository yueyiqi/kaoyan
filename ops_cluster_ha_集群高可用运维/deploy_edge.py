"""Publish only whitelisted frontend assets and replace only the requested vhost."""
import hashlib
import json
import shlex
import zipfile
from remote import BASE, PROJECT, ssh, copy, python_remote

names = ['index.html', 'kaoyan_network.js', 'kaoyan_admin.js', 'kaoyan_admin_view.js',
         'kaoyan_admin_accounts.js', 'kaoyan_login.js']
hashes = {n: hashlib.sha256((PROJECT/n).read_bytes()).hexdigest() for n in names}
release = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()[:12]
archive = BASE/'scratchpad/edge.zip'
assert sum((PROJECT/n).stat().st_size for n in names) < 2 * 1024 * 1024
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
    for name in names:
        z.writestr(name, (PROJECT/name).read_bytes())
copy('elena', archive, 'kaoyan-edge-release.zip')
code = """from pathlib import Path
import hashlib,json,shutil,zipfile
base=Path('/srv/kaoyan-edge/releases')
base.mkdir(parents=True,exist_ok=True)
target=base/RELEASE
target.mkdir(exist_ok=True)
z=zipfile.ZipFile(Path('/home/elena/kaoyan-edge-release.zip'))
assert set(z.namelist())==set(HASHES)
z.extractall(target)
for name,digest in HASHES.items():
 assert hashlib.sha256((target/name).read_bytes()).hexdigest()==digest
dirs=sorted([d for d in base.iterdir() if d.is_dir() and d.name!=RELEASE],key=lambda p:p.stat().st_mtime,reverse=True)
pruned=[]
for old_dir in dirs[4:]:
 shutil.rmtree(old_dir,ignore_errors=True);pruned.append(old_dir.name)
total_bytes=sum(p.stat().st_size for p in base.rglob('*') if p.is_file())
assert total_bytes < 16*1024*1024, 'Edge storage budget exceeded'
print(json.dumps({'status':'static release verified','active_release':RELEASE,'retained_releases':len([d for d in base.iterdir() if d.is_dir()]),'pruned_releases':pruned,'total_bytes':total_bytes}))
""".replace('RELEASE', repr(release)).replace('HASHES', repr(hashes))
print(ssh('elena', 'sudo -n python3 -c '+shlex.quote(code)).strip())
original = ssh('elena', 'sudo -n cat /etc/caddy/Caddyfile')
marker = 'https://kaoyan-elena.duckdns.org {'
start = original.index(marker)
depth, end = 0, None
for i in range(start + marker.index('{'), len(original)):
    depth += (original[i] == '{') - (original[i] == '}')
    if depth == 0:
        end = i + 1
        break
assert end is not None
block = '''https://kaoyan-elena.duckdns.org {
    tls {
        issuer acme {
            disable_http_challenge
        }
    }
    encode gzip
    header {
        X-Content-Type-Options "nosniff"
        X-Frame-Options "SAMEORIGIN"
        Strict-Transport-Security "max-age=31536000"
        Cache-Control "no-store"
    }
    handle /api/* {
        reverse_proxy https://kaoyan.liuzengyu.top {
            header_up Host kaoyan.liuzengyu.top
        }
    }
    @frontend path / /index.html ASSETS
    handle @frontend {
        root * /srv/kaoyan-edge/releases/RELEASE
        header X-Kaoyan-Frontend "ecs-static"
        file_server
    }
    handle {
        redir * / 302
    }
}'''.replace('ASSETS', ' '.join('/'+n for n in names if n != 'index.html')).replace('RELEASE', release)
candidate = original[:start] + block + original[end:]
path = BASE/'scratchpad/Caddyfile.edge-next'
path.write_text(candidate)
copy('elena', path, 'Caddyfile.edge-next')
print(ssh('elena', 'sudo -n caddy validate --config /home/elena/Caddyfile.edge-next --adapter caddyfile').strip())
code = """from pathlib import Path
p=Path('/etc/caddy/Caddyfile');backup=p.with_name('Caddyfile.before-w1-docker-20261024')
if not backup.exists(): backup.write_bytes(p.read_bytes())
p.write_bytes(Path('/home/elena/Caddyfile.edge-next').read_bytes())
"""
ssh('elena', 'sudo -n python3 -c '+shlex.quote(code))
try:
    ssh('elena', 'sudo -n systemctl reload caddy')
except Exception:
    ssh('elena', "sudo -n cp /etc/caddy/Caddyfile.before-w1-docker-20261024 /etc/caddy/Caddyfile && sudo -n systemctl reload caddy")
    raise
(BASE/'edge_release.json').write_text(json.dumps({'release': release, 'files': hashes,
    'public': 'https://kaoyan-elena.duckdns.org', 'frontend_host': 'ECS',
    'api_origin': 'https://kaoyan.liuzengyu.top', 'api_cache': 'disabled'}, indent=2))
print('ECS frontend published', release)
