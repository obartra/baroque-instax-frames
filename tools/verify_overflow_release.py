#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check v0.3.0 compatibility and restored-path evidence with the stdlib."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
REVISED={'Canted Octagon','Cushion Cartouche','Floral Corners','Botanical Garland','Portrait Oval','Landscape Oval'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def require(ok,message):
 if not ok:raise ValueError(message)
def main():
 cat=json.loads((ROOT/'catalog/current.json').read_text());audit=json.loads((ROOT/'validation/overflow-v0.3.0.json').read_text())
 require(cat['release']==audit['release']=='v0.3.0','Release identity mismatch')
 require({r['name'] for r in audit['revised']}==REVISED,'Expected six specifically audited revisions')
 frames={r['name']:r for r in cat['frames']}
 for r in audit['revised']:
  f=frames[r['name']];geo_path=ROOT/f['geometry'];geo=json.loads(geo_path.read_text());proof=json.loads((ROOT/r['front_toolpaths']).read_text())
  require(sha(ROOT/f['model'])==r['project_sha256']==proof['project_sha256'],r['name']+': restored-path proof belongs to another project')
  require(sha(geo_path)==proof['geometry_report_sha256'],r['name']+': restored-path proof belongs to another geometry report')
  require(proof['id']==geo['id']==f['id'],r['name']+': identity mismatch')
  require(geo['mat_symmetric_difference_mm3']<.002 and geo['back_symmetric_difference_mm3']<.002,r['name']+': previous matching parts changed')
  require(geo['ornament_removed_mm3']<.02 and geo['petal_overlap_area_mm2']>1,r['name']+': missing additive-restoration evidence')
  require(geo['clear_aperture_preserved'] and geo['fused_front_single_volume'],r['name']+': aperture/support geometry gate')
  require(proof['minimum_component_coverage']>.4 and not proof['missing_components'] and proof['components'],r['name']+': restored contours missing extrusion')
  require(proof['checked_layer']==8 and proof['checked_layer_top_mm']==.76 and proof['supported_from_mat_top_mm']==.68,r['name']+': restored detail not supported directly after mat')
  require(not geo['physical_test'] and not proof['physical_test'],r['name']+': unsupported revised physical-test claim')
  print('PASS restored overlap and compatibility:',r['name'])
 require({r['name'] for r in audit['unchanged']}=={'Segmental Arch','Acanthus Gallery'},'Expected two unchanged designs')
 for r in audit['unchanged']:require(sha(ROOT/frames[r['name']]['model'])==r['v0.2.0_project_sha256'],r['name']+': supposedly unchanged project changed')
 print('PASS unchanged models and v0.3.0 evidence. Digital checks, not physical testing.')
if __name__=='__main__':main()
