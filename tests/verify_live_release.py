"""Release gate: meaningful schema, protocol, and browser request tests."""
from pathlib import Path
import shutil
import subprocess
import sys

base=Path(__file__).resolve().parent
for name in ['test_portable_schema.py','test_live_cluster.py','test_admin_drilldown.py','test_admin_http.py']:
    subprocess.run([sys.executable,str(base/name)],check=True)
node=shutil.which('node')
if not node:
    raise SystemExit('Node is required for the browser request regression')
subprocess.run([node,str(base/'test_network_retry.js')],check=True)
subprocess.run([node,str(base/'test_admin_ui.js')],check=True)
