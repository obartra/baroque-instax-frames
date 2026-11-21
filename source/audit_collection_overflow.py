# SPDX-License-Identifier: MIT
"""Stage source-traced, additive mat-overflow revisions without publishing.

Coordinates gate the unchanged source silhouette, separating flowers from the
adjacent moulding. Exact apertures, gray mats and matching backs are retained.
"""
import json
from pathlib import Path
import numpy as np
import shapely
from scipy import ndimage as ndi
from paths import ROOT
from build_floral_rococo import drawing,aperture_for,choose_geometry,sculpt,petal_overlap
import matplotlib.pyplot as plt

OUT=ROOT/'build/collection-overflow-audit'
STUDY=ROOT/'studies/collection-overflow-revision'
STUDY.mkdir(exist_ok=True);OUT.mkdir(exist_ok=True)
# Original artwork coordinates in millimetres, calibrated by drawing().
# Gates overlap the rail on the exterior side; gold segmentation still sets
# the actual contour wherever it is separated from the rail by dark ground.
SELECTIONS={
'12':dict(regions=[[-29,30,8],[38,24,10],[-38,-25,11],[37,-24,8],[-20,30,4],[20.5,30,4],[-38.5,19,4],[-23,-30,4],[25,-30,4]],polygons=[
[[-37,38],[-21,38],[-21,29],[-24,28.4],[-24.7,27.6],[-25.4,27],[-25.6,26],[-26.3,25.2],[-27.5,25.1],[-28.7,25.5],[-29.4,25.5],[-30.3,25.1],[-31.3,25.3],[-33,26]],
[[30,35],[49,35],[49,18],[41,18],[39.4,17.6],[37,17.6],[35.8,18.1],[35.1,19.2],[34.8,20.5],[34,21.1],[33,20.8],[32,21.1],[31.3,22],[30,22.5]],
[[-49,-17],[-37,-17],[-35.6,-20.8],[-34.7,-20.1],[-33.4,-19.9],[-32.4,-20.2],[-31.9,-21.2],[-30.8,-21.6],[-29.8,-22.1],[-29.2,-23],[-29,-23.7],[-29.4,-24.3],[-30.2,-24.6],[-30.4,-25.2],[-30,-26.1],[-30.2,-26.8],[-31,-27.4],[-32.4,-26.9],[-33,-26.5],[-33,-34],[-49,-34]],
[[32,-30],[45,-30],[45,-18],[38,-18],[37,-19],[36,-19.1],[35,-19.6],[34,-20.4],[33,-21.4],[32.5,-22.5],[31.9,-24.4],[31.9,-25.5]],
[[-24,35],[-16,35],[-16,29.4],[-18,29.4],[-18.5,28.6],[-19,28],[-19.6,27.8],[-20.1,28.1],[-20.4,28.4],[-20.8,28],[-21.4,27.8],[-21.9,28.2],[-22.2,29],[-24,29.5]],
[[16,35],[25,35],[25,29.2],[23,29.1],[22.8,28.4],[22.2,27.7],[21.6,27.4],[21,27.5],[20.7,28],[20.4,27.7],[20,27.3],[19.3,27.2],[18.7,27.6],[18.4,28.2],[18.5,29.1],[16,29.2]],
[[-43,23],[-38,23],[-37.5,21],[-36.7,21],[-36.2,20.6],[-35.5,20],[-35.3,19.2],[-35.7,18.5],[-36.5,18.3],[-36,17.8],[-35.7,17.1],[-35.8,16.5],[-36.3,15.9],[-37,15.7],[-38,16],[-43,16]],
[[-27,-35],[-19,-35],[-19,-29.2],[-21.8,-29.3],[-21.7,-28.6],[-22,-28],[-22.6,-27.6],[-23.3,-27.6],[-24,-27.8],[-24.4,-28.5],[-24.4,-29.1],[-27,-29]],
[[21,-35],[29,-35],[29,-29],[28,-28.6],[27.9,-28.1],[27.2,-27.8],[26.4,-27.8],[25.6,-28.1],[25.2,-27.7],[24.4,-27.5],[23.8,-27.7],[23.3,-28.2],[23.3,-29.1],[21,-29.4]]]),
'14':dict(regions=[[43,21,13],[-43,-23,13],[.5,29,4],[1,-29,5]],polygons=[
[[33,36],[56,36],[56,12],[38,12],[37,16.1],[36.1,16.5],[36.2,17.6],[37,18.3],[38,18.4],[39.8,16.8],[39,18.2],[38.3,19.1],[37,20.1],[36.2,20.3],[35,21],[34,21.3],[33.3,22.1],[33.1,23],[33.6,23.8],[32.5,24.9],[32,26],[32.3,27],[33,28]],
[[-55,-34],[-31,-34],[-31.7,-28],[-31.6,-26.8],[-32,-25.1],[-33,-24],[-34.2,-22.4],[-35.3,-22.1],[-35.5,-21.7],[-34.6,-21.2],[-34.6,-20.3],[-35.4,-19.5],[-35.7,-18.1],[-36.2,-17.6],[-36.1,-16],[-55,-16]],
[[-1.4,33],[3.2,33],[3.2,28.1],[1.9,28],[1.8,27.1],[1,26.7],[0,26.8],[-.6,27.3],[-.9,28],[-1.4,28.3]],
[[-3.5,-33],[5.4,-33],[5.2,-27.1],[4.3,-26.6],[3.2,-26.6],[2.4,-26.8],[1.5,-27.1],[.6,-26.6],[-.3,-26.2],[-1.1,-26.2],[-1.9,-26.6],[-2,-27],[-3,-27.2],[-3.5,-28]]]),
'15':dict(regions=[[-39,33,15],[43,30,13],[.5,-29,5]],polygons=[
[[-53,47],[-25,47],[-25,32],[-31,28],[-31.9,27],[-33,26.7],[-34.5,27.1],[-34.3,25.9],[-35,25.1],[-35.5,24.9],[-35.5,24.1],[-36.2,23.1],[-37,22.8],[-37.8,22.8],[-38.1,21.8],[-39,21.1],[-40,21.2],[-41,21.7],[-41.3,22.9],[-42,23.3],[-43,22.8],[-53,23]],
[[31,39],[55,39],[55,19],[43,19],[41,20],[39,20],[38,20.8],[37.5,21.7],[36.8,22.1],[36.6,23],[36.8,24.2],[37.5,25.2],[38,26.1],[38,26.7],[37.1,27.4],[35.7,27.5],[35,27.9],[34.7,28.4],[33.5,28.6],[33,29.1],[33,30]],
[[-4,-32],[5,-32],[4,-28.8],[3,-28.2],[1.5,-28],[.5,-27.6],[-1,-27.3],[-2.3,-27.5],[-3,-28],[-3.5,-28.7]]]),
'11':dict(regions=[[-34,2,16],[36,-1,16],[-28,-20,6]],polygons=[
[[-49,18],[-31,18],[-30,13],[-28.2,10],[-27.1,9.5],[-26.3,8.2],[-25.8,6.9],[-24.7,6.2],[-24.4,5.4],[-25.1,4.5],[-24.6,3.5],[-24.3,2.5],[-24.8,1.5],[-25.8,1],[-25.7,-.4],[-26.4,-2.4],[-27.1,-3.2],[-28.1,-3.5],[-28.6,-4.9],[-30,-5.5],[-33,-5.7],[-49,-6]],
[[27,12],[50,12],[50,-16],[31,-16],[30,-11.7],[28.5,-11.1],[27.6,-10.4],[27.2,-8.6],[27.5,-7],[26.5,-6.5],[25.8,-5.4],[25.3,-4],[24.6,-2.9],[24.5,-1.8],[25,-.6],[25.6,.7],[24.6,1.0],[24.5,1.8],[24.9,2.8],[25.6,3.3],[25.8,4.3],[25.6,5.5],[26.2,6.7],[26.8,7.4],[27.7,8.2]],
[[-34,-26],[-25,-26],[-25,-23.7],[-23.9,-22.3],[-23.4,-21.5],[-23.5,-20.4],[-24.2,-19.5],[-24.9,-19.2],[-24.5,-18.4],[-24.5,-17.6],[-25,-16.9],[-26,-16.2],[-27,-16],[-34,-15]]]),
'18':dict(regions=[[-35,22,17],[37,-23,15]],polygons=[
[[-56,40],[-20,40],[-20,25],[-24,23.5],[-25.3,22.5],[-26.3,22.4],[-27.1,23.2],[-28.2,23.6],[-29,23.3],[-29.6,22.1],[-29.4,21],[-29.5,19.9],[-30.1,18.9],[-31.5,17.7],[-32.9,17.3],[-33.9,17.8],[-34.5,17.9],[-35.3,17.6],[-35.8,16.6],[-35.7,15.7],[-36.1,14.4],[-37,13],[-38.5,12],[-40,11.7],[-56,12]],
[[23,-34],[56,-34],[56,-9],[37,-9],[36.4,-13],[35.4,-12.8],[34,-13],[32.6,-13.6],[32,-14.3],[32.2,-15.1],[32.1,-16.2],[31.4,-17.1],[30.1,-17.7],[29,-17.8],[28.3,-17.6],[27.6,-17.9],[26.2,-18.4],[25.9,-19.1],[25.6,-19.5],[24.6,-19.8],[24.4,-20.6],[23.8,-21.3],[22,-23.3]]])}
def smooth(x):
 x=np.clip(x,0,1);return x*x*(3-2*x)

def main():
 designs=json.loads((ROOT/'source/designs-reinforced-mats.json').read_text());revised=[];report=[]
 for source in designs:
  key=source['id'][:2]
  if key not in SELECTIONS:continue
  sel=SELECTIONS[key];d=dict(source);original_id=d['id'];d['id']+='-Mat-Overflow-v2'
  d['petal_overlap_regions_mm']=sel['regions'];d['petal_overlap_outline_regions_mm']=sel['polygons']
  if key=='11':d['relief_footprint_precision_mm']=.000001
  rgb,gold,solid,pix,cx,cy,initial=drawing(d);a=aperture_for(d)
  outer,positions,_,_,_,f,_,join=choose_geometry(d,pix,initial,a);inner=a.buffer(6.5,join_style=join)
  yy,xx=np.indices(gold.shape);x,y=(xx-cx)*f,(cy-yy)*f
  old=np.load(ROOT/d['final_surface_file']).astype(float)
  raw=dict(d);raw.pop('final_surface_file');raw.pop('authored_surface',None)
  intact=sculpt(raw,rgb,gold,solid,cx,cy,f,inner,outer,positions,height_only=True)
  # Restore original depth/normal relief in each complete motif, feathered on
  # its exterior edge. The saved final field was flattened by the mat blend.
  w=np.zeros(old.shape)
  for px,py,r in sel['regions']:w=np.maximum(w,smooth((r-np.hypot(x-px,y-py))/2))
  # Do not alter distant rail details; fade into the existing outer surface.
  di=shapely.distance(shapely.points(x[::4,::4].ravel(),y[::4,::4].ravel()),inner).reshape(x[::4,::4].shape)
  di=ndi.zoom(di,(x.shape[0]/di.shape[0],x.shape[1]/di.shape[1]),order=1)[:x.shape[0],:x.shape[1]]
  w*=smooth((2.1-di)/.6)
  height=np.maximum(old,old+(intact-old)*w)
  height[shapely.contains_xy(a.buffer(.85,join_style=join),x,y)]=old[shapely.contains_xy(a.buffer(.85,join_style=join),x,y)]
  assert np.isfinite(height).all() and height.max()<12
  target=STUDY/(d['id']+'-final-height.npy');np.save(target,height.astype('float32'));d['final_surface_file']=str(target.relative_to(ROOT))
  petals=petal_overlap(d,gold,cx,cy,f,inner,a)
  assert not petals.is_empty
  fig,ax=plt.subplots(figsize=(10,10),dpi=140);ax.imshow(rgb.astype('uint8'),extent=(-cx*f,(rgb.shape[1]-cx)*f,(cy-rgb.shape[0])*f,cy*f))
  for poly in ([petals] if petals.geom_type=='Polygon' else petals.geoms):
   ax.fill(*poly.exterior.xy,color='magenta',alpha=.55)
  for p,col in [(inner,'red'),(a,'cyan')]:ax.plot(*p.exterior.xy,color=col,lw=.7)
  ax.set_xlim(outer.bounds[0]-2,outer.bounds[2]+2);ax.set_ylim(outer.bounds[1]-2,outer.bounds[3]+2);ax.set_aspect('equal');ax.set_title(original_id+'\nMagenta: restored source silhouette over the mat');fig.tight_layout();fig.savefig(OUT/(d['id']+'-restoration-mask.png'));plt.close(fig)
  revised.append(d);report.append(dict(id=d['id'],original_id=original_id,area_mm2=petals.area,maximum_added_height_mm=float((height-old).max()),source=d['depth_file']))
 (ROOT/'source/designs-collection-mat-overflow-v2.json').write_text(json.dumps(revised,indent=2)+'\n')
 (OUT/'restoration-selections.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
