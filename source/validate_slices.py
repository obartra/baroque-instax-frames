# SPDX-License-Identifier: MIT
"""Slice every final project and verify the file actually delivered."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import subprocess,json,hashlib,os,shutil
from paths import P
APP=os.environ.get('BAMBU_STUDIO') or shutil.which('BambuStudio') or '/Applications/BambuStudio.app/Contents/MacOS/BambuStudio'
if not Path(APP).is_file():
 raise SystemExit('Set BAMBU_STUDIO to your Bambu Studio executable; see docs/BUILDING.md.')
files=sorted(P.glob('0*-Instax-Mini-3-Magnets.3mf'))+[P/'PLA-Clip-Fit-Test.3mf']
def one(f):
 key=f.name.removesuffix('-Instax-Mini-3-Magnets.3mf').removesuffix('.3mf')
 out=P/key/'slice-final';out.mkdir(parents=True,exist_ok=True)
 cmd=[APP,'--debug','1','--arrange','0','--orient','0','--slice','0','--export-3mf','validated.3mf','--outputdir',str(out),str(f)]
 with (out.parent/'slicer-final.log').open('w') as log:p=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
 r=json.loads((out/'result.json').read_text())
 assert p.returncode==0 and r['return_code']==0,(f.name,p.returncode,r.get('error_string'))
 assert len(r['sliced_plates'])==2
 changes=[x['filament_change_times'] for x in r['sliced_plates']]
 assert changes==[1,0],(f.name,changes)
 warnings=[x.get('warning_message','') for x in r['sliced_plates']]
 assert not any(warnings),(f.name,warnings)
 for plate in [1,2]:
  assert (out/f'plate_{plate}.gcode').stat().st_size>1000
 report=dict(file=f.name,sha256=hashlib.sha256(f.read_bytes()).hexdigest(),slicer='BambuStudio (local executable; see slicer logs for version)',return_code=0,plates=2,filament_changes=changes,warning_messages=warnings,physical_test=False,
   estimated_minutes=[round(x['total_predication']/60,1) for x in r['sliced_plates']],
   material_g=[round(sum(t['total_used_g'] for t in x['filaments']),2) for x in r['sliced_plates']])
 (P/'validation'/(key+'-slicer.json')).write_text(json.dumps(report,indent=2))
 print('SLICE PASS',f.name,json.dumps(report),flush=True)
 return report
with ThreadPoolExecutor(max_workers=2) as pool:reports=list(pool.map(one,files))
(P/'validation/slicer-summary.json').write_text(json.dumps(reports,indent=2))
