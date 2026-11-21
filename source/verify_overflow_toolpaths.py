# SPDX-License-Identifier: MIT
"""Verify restored source contours receive real front extrusion after the mat."""
import json,hashlib,os
from pathlib import Path
import numpy as np
from shapely.geometry import MultiLineString
from paths import ROOT,P
from build_floral_rococo import drawing,aperture_for,choose_geometry,petal_overlap
from verify_back_toolpaths import parse

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 designs=json.loads(Path(os.environ['BAROQUE_DESIGNS_FILE']).read_text());rows=[]
 for d in designs:
  project=P/(d['id']+'-Instax-Mini-3-Magnets.3mf');q=P/d['id'];gcode=q/'slice-final/plate_1.gcode'
  rgb,gold,solid,pix,cx,cy,f0=drawing(d);a=aperture_for(d);outer,_,_,_,_,f,_,join=choose_geometry(d,pix,f0,a)
  petals=petal_overlap(d,gold,cx,cy,f,a.buffer(6.5,join_style=join),a)
  layers=parse(gcode);assert [r['z'] for r in layers[:8]]==[.2,.28,.36,.44,.52,.6,.68,.76]
  first=layers[7];ink=MultiLineString(first['lines']).buffer(.27,quad_segs=4)
  components=list(petals.geoms) if hasattr(petals,'geoms') else [petals]
  coverage=[]
  for p in components:
   if p.area<.15:continue
   area=p.intersection(ink).area;ratio=area/p.area
   assert area>.02 and ratio>.4,(d['id'],'Missing restored petal paths',p.bounds,p.area,ratio)
   coverage.append(dict(bounds_mm=list(p.bounds),area_mm2=p.area,first_ornament_layer_coverage=ratio))
  assert coverage
  row=dict(id=d['id'],project_sha256=sha(project),geometry_report_sha256=sha(q/'validation.json'),gcode_sha256=sha(gcode),restored_overlap_area_mm2=petals.area,checked_layer=8,checked_layer_top_mm=.76,supported_from_mat_top_mm=.68,minimum_component_coverage=min(p['first_ornament_layer_coverage'] for p in coverage),components=coverage,missing_components=[],physical_test=False,method='Source-traced restored footprints intersected with actual linear extrusion paths buffered 0.27 mm; layer 8 immediately follows the seven-layer mat.',limitation='Checks path presence and support footprint, not physical surface quality, extrusion strength or exact deposited volume.')
  (P/'validation'/(d['id']+'-front-overflow-toolpaths.json')).write_text(json.dumps(row,indent=2)+'\n');rows.append(row)
  print('OVERFLOW PATH PASS',d['id'],len(coverage),row['minimum_component_coverage'],flush=True)
 (P/'validation/overflow-front-paths-summary.json').write_text(json.dumps(rows,indent=2)+'\n')
if __name__=='__main__':main()
