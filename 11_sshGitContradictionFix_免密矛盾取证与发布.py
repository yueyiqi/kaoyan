#!/usr/bin/env python3
"""11_sshGitContradictionFix_免密矛盾取证与发布.py

1. Extracts forensic evidence from `8.163.29.42` (`/var/log/auth.log` & `/home/elena/.bash_history`)
   proving whether and how `cl-715-codeup` (`SHA256:OFeU8L1Blc+ECOmWayawRMLIYace0UuxIVM+ojmTNiw`)
   logged in and what commands were executed.
2. Upgrades `/home/elena/kaoyan_english_hub` on `8.163.29.42` into a Git-aligned working tree
   tracking `https://github.com/yueyiqi/kaoyan.git` (`main` branch), with:
   - `receive.denyCurrentBranch = updateInstead`
   - `.git/hooks/post-receive` auto-sync (`frontend/index.html` <-> `index.html`, `backend/kaoyan_hub_server.py` <-> `kaoyan_hub_server.py`) + service restart + health probe
   - `/usr/local/bin/deploy-kaoyan` one-command GitHub pull + restart + health probe
"""

from __future__ import annotations

import json
import subprocess
import sys


def run_ssh(script: str, timeout: int = 25) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["ssh", "-o", "ConnectTimeout=8", "elena", script],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def main() -> int:
    remote_setup = r"""
set -e

echo "=== 1. FORENSIC AUDIT OF /var/log/auth.log FOR cl-715-codeup ==="
sudo grep -E "183\.238\.79\.28|OFeU8L1Blc|52849|52931" /var/log/auth.log || true
echo "=== 2. FORENSIC AUDIT OF /home/elena/.bash_history ==="
sudo cat /home/elena/.bash_history 2>/dev/null || true

echo "=== 3. WIRE GIT REPO & AUTO-DEPLOY HOOKS IN /home/elena/kaoyan_english_hub ==="
rm -rf /tmp/kaoyan_gh_sync
git clone -q https://github.com/yueyiqi/kaoyan.git /tmp/kaoyan_gh_sync

# Copy .git and repo structure into /home/elena/kaoyan_english_hub without losing runtime dirs
cp -a /tmp/kaoyan_gh_sync/.git /home/elena/kaoyan_english_hub/
cp -a /tmp/kaoyan_gh_sync/.gitignore /tmp/kaoyan_gh_sync/README.md /tmp/kaoyan_gh_sync/frontend /tmp/kaoyan_gh_sync/backend /tmp/kaoyan_gh_sync/docs /home/elena/kaoyan_english_hub/
cp -a /tmp/kaoyan_gh_sync/index.html /home/elena/kaoyan_english_hub/index.html
cp -a /tmp/kaoyan_gh_sync/kaoyan_hub_server.py /home/elena/kaoyan_english_hub/kaoyan_hub_server.py
rm -rf /tmp/kaoyan_gh_sync

cd /home/elena/kaoyan_english_hub
git config receive.denyCurrentBranch updateInstead
git config user.name "elena-deploy"
git config user.email "elena@elenalyl.top"

cat << 'EOF' > /home/elena/kaoyan_english_hub/.git/info/exclude
db_backups/
db_volume/
elena_cold_offload_to_t2.py
*.sqlite3*
EOF

cat << 'EOF' > /home/elena/kaoyan_english_hub/.git/hooks/post-receive
#!/usr/bin/env bash
set -e
cd /home/elena/kaoyan_english_hub
if [ -f frontend/index.html ] && [ frontend/index.html -nt index.html ]; then
    cp -f frontend/index.html index.html
elif [ -f index.html ] && [ -d frontend ]; then
    cp -f index.html frontend/index.html
fi
if [ -f backend/kaoyan_hub_server.py ] && [ backend/kaoyan_hub_server.py -nt kaoyan_hub_server.py ]; then
    cp -f backend/kaoyan_hub_server.py kaoyan_hub_server.py
elif [ -f kaoyan_hub_server.py ] && [ -d backend ]; then
    cp -f kaoyan_hub_server.py backend/kaoyan_hub_server.py
fi
sudo systemctl restart kaoyan-english-hub
sleep 1
curl -fsS http://127.0.0.1:60231/api/health
echo ""
echo "[OK] kaoyan-english-hub auto-deployed and restarted via git push!"
EOF
chmod +x /home/elena/kaoyan_english_hub/.git/hooks/post-receive

cat << 'EOF' | sudo tee /usr/local/bin/deploy-kaoyan >/dev/null
#!/usr/bin/env bash
set -e
cd /home/elena/kaoyan_english_hub
echo "[1/3] Pulling latest main from https://github.com/yueyiqi/kaoyan.git ..."
git fetch origin main
git reset --hard origin/main
if [ -f frontend/index.html ] && ! cmp -s frontend/index.html index.html; then
    # Keep root index.html and frontend/index.html synchronized with the commit that changed
    CHANGED=$(git diff-tree --no-commit-id --name-only -r HEAD)
    if echo "$CHANGED" | grep -q "^frontend/index.html$"; then
        cp -f frontend/index.html index.html
    elif echo "$CHANGED" | grep -q "^index.html$"; then
        cp -f index.html frontend/index.html
    fi
fi
if [ -f backend/kaoyan_hub_server.py ] && ! cmp -s backend/kaoyan_hub_server.py kaoyan_hub_server.py; then
    CHANGED=$(git diff-tree --no-commit-id --name-only -r HEAD)
    if echo "$CHANGED" | grep -q "^backend/kaoyan_hub_server.py$"; then
        cp -f backend/kaoyan_hub_server.py kaoyan_hub_server.py
    elif echo "$CHANGED" | grep -q "^kaoyan_hub_server.py$"; then
        cp -f kaoyan_hub_server.py backend/kaoyan_hub_server.py
    fi
fi
echo "[2/3] Restarting kaoyan-english-hub.service ..."
sudo systemctl restart kaoyan-english-hub
sleep 1
echo "[3/3] Verifying live health endpoint ..."
curl -fsS http://127.0.0.1:60231/api/health
echo ""
echo "[SUCCESS] Kaoyan English Hub deployed and active on 8.163.29.42!"
EOF
sudo chmod +x /usr/local/bin/deploy-kaoyan
sudo chown -R elena:elena /home/elena/kaoyan_english_hub

echo "=== 4. VERIFY GIT STATUS AND DEPLOY-KAOYAN COMMAND ==="
cd /home/elena/kaoyan_english_hub
git status -s
git remote -v
/usr/local/bin/deploy-kaoyan
"""
    res = run_ssh(remote_setup)
    print(res.stdout)
    if res.returncode != 0:
        print(res.stderr, file=sys.stderr)
        return res.returncode
    assert "Accepted publickey for elena from 183.238.79.28" in res.stdout
    assert "[SUCCESS] Kaoyan English Hub deployed and active on 8.163.29.42!" in res.stdout
    return 0


if __name__ == "__main__":
    sys.exit(main())
