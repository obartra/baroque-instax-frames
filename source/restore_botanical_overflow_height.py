# SPDX-License-Identifier: MIT
"""Continue the existing authored petal bowls through the formerly locked mat zone."""
import json
import numpy as np
import shapely
from scipy import ndimage as ndi
from paths import ROOT
from build_floral_rococo import drawing,aperture_for,choose_geometry
from sculpt_botanical_petals import FLOWERS,flower_surface,smooth
config=ROOT/'source/designs-botanical-mat-overflow-v4.json'
d=json.loads(config.read_text())[0]
base=ROOT/'studies/botanical-sculpture-v3/16-Rocaille-Botanical-Garland-Sculpted-v3-final-height.npy'
old=np.load(base).astype(float)
rgb,gold,solid,pix,cx,cy,initial=drawing(d)
a=aperture_for(d);outer,positions,_,_,_,factor,_,join=choose_geometry(d,pix,initial,a)
yy,xx=np.indices(old.shape);x,y=(xx-cx)*factor,(cy-yy)*factor
# Prior authoring explicitly froze this entire zone. Restore within it,
# blending from the preserved exterior surface over 1.5 mm.
rail=a.buffer(6.5+1.85,join_style=join)
inside=shapely.contains_xy(rail,x,y)
dist=ndi.distance_transform_edt(inside)*factor
zone=smooth(dist/1.5)
out=old.copy()
for f in FLOWERS:
 surface,w,record=flower_surface(f,xx,yy,old,factor)
 w*=zone*gold
 candidate=old+(surface-old)*w
 out=np.maximum(out,candidate)
# Original aperture stays completely clear, with .85 mm minimum reserve.
clear=shapely.contains_xy(a.buffer(.85,join_style=join),x,y)
out[clear]=old[clear]
assert np.isfinite(out).all() and out.max()<12
p=ROOT/'studies/botanical-mat-overflow-v4/16-Botanical-Garland-Mat-Overflow-v4-final-height.npy'
np.save(p,out.astype(np.float32));d['final_surface_file']=str(p.relative_to(ROOT));config.write_text(json.dumps([d],indent=2)+'\n')
r=ROOT/'studies/botanical-mat-overflow-v4/revision.json';rec=json.loads(r.read_text());rec.update(additional_root_cause='sculpt_botanical_petals.py also freezes the full inner rail/mat zone, leaving formerly clipped petal regions flat in the saved height field.',height_repair='Restore the same traced v3 petal bowls within the locked region, blend over 1.5 mm, retain existing outside geometry and avoid cutting original ornament.',height_changed_area_mm2=float(np.count_nonzero(out-old>.01)*factor**2),maximum_height_added_mm=float((out-old).max()));r.write_text(json.dumps(rec,indent=2)+'\n');print(rec)
