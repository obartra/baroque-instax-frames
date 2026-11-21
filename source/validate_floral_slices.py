# SPDX-License-Identifier: MIT
"""Slice the exact eight projects locally; never submit or start a print."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
import subprocess
import sys
from zipfile import ZipFile

from paths import ROOT, P

APP = os.environ.get('BAMBU_STUDIO', '/Applications/BambuStudio.app/Contents/MacOS/BambuStudio')
assert Path(APP).is_file(), 'Set BAMBU_STUDIO to your local slicer executable.'
DESIGNS = json.loads(Path(os.environ.get('BAROQUE_DESIGNS_FILE', ROOT/'source/designs-current.json')).read_text())


def one(d):
    project=P/(d['id']+'-Instax-Mini-3-Magnets.3mf')
    out=P/d['id']/'slice-final';out.mkdir(exist_ok=True)
    digest=hashlib.sha256(project.read_bytes()).hexdigest()
    cmd=[APP,'--debug','1','--arrange','0','--orient','0','--slice','0',
         '--export-3mf',d['id']+'-P2S-Sliced.3mf','--outputdir',str(out),str(project)]
    with (out.parent/'slicer-final.log').open('w') as log:
        process=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
    result=json.loads((out/'result.json').read_text())
    assert process.returncode==0 and result['return_code']==0,(d['id'],process.returncode,result.get('error_string'))
    plates=result['sliced_plates']
    assert len(plates)==2,(d['id'],'expected matching front/back on two plates')
    changes=[p['filament_change_times'] for p in plates]
    assert changes==[1,0],(d['id'],'unexpected color transitions',changes)
    warnings=[p.get('warning_message','') for p in plates]
    assert not any(warnings),(d['id'],warnings)
    for plate in (1,2):
        assert (out/f'plate_{plate}.gcode').stat().st_size>1000
    sliced=out/(d['id']+'-P2S-Sliced.3mf')
    with ZipFile(sliced) as z:
        assert z.testzip() is None
        assert sum(name.endswith('.gcode') for name in z.namelist())==2
    assert hashlib.sha256(project.read_bytes()).hexdigest()==digest,'Project changed during slicing'
    report=dict(id=d['id'],file=project.name,sha256=digest,slicer='BambuStudio local CLI',
        printer='Bambu P2S 0.4 mm',return_code=0,plates=2,filament_changes=changes,
        warning_messages=warnings,estimated_minutes=[round(p['total_predication']/60,1) for p in plates],
        material_g=[round(sum(f['total_used_g'] for f in p['filaments']),2) for p in plates],
        sliced_project=str(sliced.relative_to(P)),sliced_sha256=hashlib.sha256(sliced.read_bytes()).hexdigest(),
        print_submitted=False,print_started=False,physical_test=False)
    (P/'validation'/(d['id']+'-slicer.json')).write_text(json.dumps(report,indent=2)+'\n')
    print('SLICE PASS',json.dumps(report),flush=True)
    return report


if __name__=='__main__':
    chosen=[d for d in DESIGNS if len(sys.argv)==1 or d['id'] in sys.argv[1:]]
    with ThreadPoolExecutor(max_workers=2) as pool:
        reports=list(pool.map(one,chosen))
    (P/'validation/floral-slicer-summary.json').write_text(json.dumps(reports,indent=2)+'\n')
