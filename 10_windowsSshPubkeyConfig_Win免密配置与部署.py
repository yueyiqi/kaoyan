#!/usr/bin/env python3
"""10_windowsSshPubkeyConfig_Win免密配置与部署.py

Idempotently ensures `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFESj+nOVBhNImRjKod9BM+72uvv3Xf57mD+o9Ywnkkr cl-715-codeup`
is deployed to both `elena` and `root` on `8.163.29.42`, verifies permissions and fingerprints,
and checks current `elenalyl.top` DNS/RDAP status.
"""

from __future__ import annotations

import json
import subprocess
import sys

TARGET_PUBKEY = (
    "ssh-ed25519 "
    "AAAAC3NzaC1lZDI1NTE5AAAAIFESj+nOVBhNImRjKod9BM+72uvv3Xf57mD+o9Ywnkkr "
    "cl-715-codeup"
)
EXPECTED_FP = "SHA256:OFeU8L1Blc+ECOmWayawRMLIYace0UuxIVM+ojmTNiw"


def main() -> int:
    remote_cmd = f"""
set -e
PUBKEY="{TARGET_PUBKEY}"

for USER_HOME in "elena:/home/elena" "root:/root"; do
    U="${{USER_HOME%%:*}}"
    H="${{USER_HOME#*:}}"
    sudo mkdir -p "$H/.ssh"
    sudo touch "$H/.ssh/authorized_keys"
    if ! sudo grep -Fqx "$PUBKEY" "$H/.ssh/authorized_keys"; then
        sudo sed -i '/cl-715-codeup/d' "$H/.ssh/authorized_keys"
        echo "$PUBKEY" | sudo tee -a "$H/.ssh/authorized_keys" >/dev/null
    fi
    sudo chown -R "$U:$U" "$H/.ssh"
    sudo chmod 700 "$H/.ssh"
    sudo chmod 600 "$H/.ssh/authorized_keys"
done

echo "=== ELENA_AUTH_KEYS ==="
sudo grep "cl-715-codeup" /home/elena/.ssh/authorized_keys
sudo ssh-keygen -lf /home/elena/.ssh/authorized_keys | grep "cl-715-codeup"
sudo stat -c "%a %U:%G %n" /home/elena/.ssh /home/elena/.ssh/authorized_keys

echo "=== ROOT_AUTH_KEYS ==="
sudo grep "cl-715-codeup" /root/.ssh/authorized_keys
sudo ssh-keygen -lf /root/.ssh/authorized_keys | grep "cl-715-codeup"
sudo stat -c "%a %U:%G %n" /root/.ssh /root/.ssh/authorized_keys

echo "=== ELENALYL_DNS_CHECK ==="
dig @223.5.5.5 kaoyan.elenalyl.top A +short || true
"""
    proc = subprocess.run(
        ["ssh", "-o", "ConnectTimeout=8", "elena", remote_cmd],
        capture_output=True,
        text=True,
    )
    print(proc.stdout.strip())
    if proc.returncode != 0:
        print(proc.stderr, file=sys.stderr)
        return proc.returncode
    if EXPECTED_FP not in proc.stdout:
        print(f"Missing expected fingerprint {EXPECTED_FP}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
