# SPDX-License-Identifier: MIT
from pathlib import Path
import subprocess,sys
from concurrent.futures import ThreadPoolExecutor
from paths import ROOT, P
def run(script,args,log):
 with (P/log).open('w') as f:
  p=subprocess.run([sys.executable,str(ROOT/'source'/script)]+args,stdout=f,stderr=subprocess.STDOUT)
 assert p.returncode==0,(script,log,p.returncode)
 print('PASS',script,args,flush=True)
run('finalize_projects.py',[],'finalize.log')
with ThreadPoolExecutor(max_workers=3) as pool:
 futures=[pool.submit(run,'validate_slices.py',[],'slice-final.log'),pool.submit(run,'render_catalog.py',[],'render-final.log'),pool.submit(run,'render_catalog.py',['overview'],'render-overview.log')]
 for f in futures:f.result()
