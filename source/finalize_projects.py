# SPDX-License-Identifier: MIT
from pathlib import Path
import json
import numpy as np,trimesh as tm,shapely
from shapely import wkt
import build_catalog as b
from paths import ROOT, P
DS=json.loads((ROOT/'source/designs-final.json').read_text())
for d in DS:
 q=P/d['id'];r=json.loads((q/'validation.json').read_text())
 project=P/(d['id']+'-Instax-Mini-3-Magnets.3mf')
 white,black,back=[b.read_project_mesh(project,n) for n in [1,2,4]]
 assert all(m.is_volume and m.is_watertight for m in [white,black,back]),d['id']
 portrait=d['orientation']=='portrait'
 cavities=[b.box(2.4,4.3,1.7,3,p) if portrait else b.box(4.3,2.4,1.7,3,p) for p in r['snap_positions_mm']]
 black=b.check(b.diff(black,b.union(cavities)),'final front')
 for p in r['snap_positions_mm']:
  roof=b.box(2,3.9,.15,4.85,p) if portrait else b.box(3.9,2,.15,4.85,p)
  assert abs(b.inter(black,roof).volume-roof.volume)<.002,('closed socket roof',d['id'],p)
 black.export(q/'black-ornament.stl')
 mounted=[]
 for m in [white,black]:
  z=m.copy();z.apply_translation([0,0,3.6]);mounted.append(z)
 assert sum(abs(b.inter(m,back).volume) for m in mounted)<.015
 for x,y in r['snap_positions_mm']:
  assert sum(abs(b.inter(b.inter(m,back),b.box(8,8,12,-.1,(x,y))).volume) for m in mounted)<.015
  pulls=[]
  for m in mounted:
   z=m.copy();z.apply_translation([0,0,.5]);pulls.append(z)
  assert sum(abs(b.inter(b.inter(m,back),b.box(8,8,12,-.1,(x,y))).volume) for m in pulls)>.005
 outer=wkt.loads((q/'outer.wkt').read_text())
 tris=back.triangles[np.abs(back.face_normals[:,2])>1e-8,:,:2]
 projection=shapely.union_all(shapely.polygons(tris),grid_size=1e-5)
 assert projection.difference(outer.buffer(-.489)).area<.02
 r.update(snap_axial_relaxation_mm=.15,snap_per_arm_deflection_mm=.115,snap_arm_section_mm=[1.05,2.0],closed_socket_roofs_checked=True,back_projection_hidden=True,print_profile_filaments=2)
 r['front_dimensions_mm'][2]=float(black.bounds[1,2])
 (q/'validation.json').write_text(json.dumps(r,indent=2))
 (P/'validation'/(d['id']+'-geometry.json')).write_text(json.dumps(r,indent=2))
 b.write_project(d,white,black,back)
 print('Finalized',d['id'],flush=True)
# A low-material coupon uses precisely the same fork, socket and mating stops.
Q=P/'PLA-Clip-Fit-Test';Q.mkdir(exist_ok=True)
cut=b.socket((0,0))
w=b.check(b.diff(b.box(12,12,.36),cut),'coupon white')
k=b.check(b.diff(b.box(12,12,4.94,.36),cut),'coupon socket')
base=b.box(12,12,1.2)
stops=[b.box(2,2,3.6,0,(x,y)) for x in [-4.5,4.5] for y in [-4.5,4.5]]
rear=b.check(b.union([base,b.peg((0,0))]+stops),'coupon fork')
mounted=[]
for m in [w,k]:
 z=m.copy();z.apply_translation([0,0,3.6]);mounted.append(z)
assert sum(abs(b.inter(m,rear).volume) for m in mounted)<.001
pulled=[]
for m in mounted:
 z=m.copy();z.apply_translation([0,0,.5]);pulled.append(z)
assert sum(abs(b.inter(m,rear).volume) for m in pulled)>.01
for n,m in [('white-mat.stl',w),('black-ornament.stl',k),('back.stl',rear)]:m.export(Q/n)
out=b.write_project(dict(id='PLA-Clip-Fit-Test',name='PLA clip fit coupon'),w,k,rear)
# This coupon has neither a photograph nor magnets; label it accordingly.
from zipfile import ZipFile,ZIP_DEFLATED
from lxml import etree as E
target=P/'PLA-Clip-Fit-Test.3mf'
with ZipFile(out) as zi,ZipFile(target,'w',ZIP_DEFLATED) as zo:
 for info in zi.infolist():
  data=zi.read(info.filename)
  if info.filename=='3D/3dmodel.model':
   root=E.fromstring(data)
   for md in root.findall('{'+b.NS+'}metadata'):
    if md.get('name')=='Description':md.text='Low-material coupon for the rounded-root PLA fork and matching socket. No magnets or photo. Print both plates and test before a full frame.'
   data=E.tostring(root,xml_declaration=True,encoding='UTF-8')
  if info.filename=='Metadata/model_settings.config':
   root=E.fromstring(data)
   for md in root.findall('.//metadata'):
    if md.get('key')=='name':
     value=md.get('value','')
     if value=='White flexible-clip back':md.set('value','Coupon fork and mating stops')
     elif value=='Black floral ornament':md.set('value','Coupon socket body')
     elif value=='White internal mat':md.set('value','Thin white first layers')
     elif 'three-magnet back' in value:md.set('value',value.replace('three-magnet back','fork coupon'))
    if md.get('key')=='plater_name':md.set('value','Socket coupon' if md.get('value')=='White mat then black front' else 'Fork coupon')
   data=E.tostring(root,xml_declaration=True,encoding='UTF-8')
  zo.writestr(info,data)
out.unlink()
print('Clip coupon complete',flush=True)
