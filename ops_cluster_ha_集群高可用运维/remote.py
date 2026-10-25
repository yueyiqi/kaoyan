"""Bounded SSH helpers; credentials are never printed or embedded in artifacts."""
from pathlib import Path
import base64, json, shlex, subprocess, time
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'.bz').is_dir())
BASE=Path(__file__).resolve().parent
PROJECT=next((ROOT/'.bz').glob('*/95_kaoyan*'))
RESOLVER=ROOT/'scripts/1_identity_身份探测/node_ip_resolver.py'
_RESOLVED=set()
def _warm_host(host):
 h=host.split('@')[-1].split(':')[0].lower()
 if h in {'hp','t2','cvm','s1'} and h not in _RESOLVED and RESOLVER.exists():
  subprocess.run(['python3',str(RESOLVER),h],capture_output=True,timeout=5)
  _RESOLVED.add(h)
def run(argv,timeout=90,input=None):
 r=subprocess.run(argv,input=input,capture_output=True,text=True,timeout=timeout)
 if r.returncode: raise RuntimeError(str(r.returncode)+': '+r.stdout[-3000:]+r.stderr[-3000:])
 return r.stdout
def ssh(host,command,timeout=90,input=None):
 _warm_host(host)
 for attempt in range(3):
  extra=['-o','ControlMaster=no','-o','ControlPath=none'] if attempt==2 else []
  try:
   return run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=8',*extra,host,command],timeout,input)
  except RuntimeError as e:
   if attempt<2 and ('port 65535' in str(e) or 'mux_client' in str(e) or '255:' in str(e)):
    time.sleep(0.4*(attempt+1));continue
   raise
def ps(code):
 text="$ProgressPreference='SilentlyContinue'; $ErrorActionPreference='Stop'; "+code
 return 'powershell -NoProfile -EncodedCommand '+base64.b64encode(text.encode('utf-16le')).decode()
def win(code,timeout=90):return ssh('w1',ps(code),timeout)
def win_python(code,timeout=90):
 encoded=base64.b64encode(code.encode()).decode()
 # Windows PowerShell strips embedded double quotes in native -c arguments.
 return win("& (Join-Path $env:USERPROFILE 'kaoyan_live_20261024/python/python.exe') -c \"exec(__import__('base64').b64decode('"+encoded+"'))\"; exit $LASTEXITCODE",timeout)
def wsl(code,timeout=90):
 # Encode shell content to avoid PowerShell/native argument quoting differences.
 encoded=base64.b64encode(code.encode()).decode()
 return win("wsl -d Ubuntu-26.04 -u root -- bash -c \"echo "+encoded+" | base64 -d | bash\"; exit $LASTEXITCODE",timeout)
def python_remote(host,code):
 return ssh(host,'python3 -c '+shlex.quote(code))
def copy(host,source,target):
 _warm_host(host)
 for attempt in range(3):
  extra=['-o','ControlMaster=no','-o','ControlPath=none'] if attempt==2 else []
  try:
   return run(['scp','-q',*extra,str(source),host+':'+target])
  except RuntimeError as e:
   if attempt<2 and ('port 65535' in str(e) or '255:' in str(e)):
    time.sleep(0.4*(attempt+1));continue
   raise
