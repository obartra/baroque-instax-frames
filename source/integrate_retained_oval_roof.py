# SPDX-License-Identifier: MIT
"""Correct only the retained portrait oval's exposed upper-left socket cap."""
import json
import os
from pathlib import Path
import numpy as np
from paths import ROOT
from build_floral_rococo import drawing,aperture_for,choose_geometry,sculpt


def main():
    source=Path(os.environ['BAROQUE_DESIGNS_FILE'])
    ds=json.loads(source.read_text())
    d=next(d for d in ds if d['id']=='11-Period-Floral-Portrait-Oval')
    original=json.loads((ROOT/'source/designs-period-portrait-oval.json').read_text())[0]
    old=np.load(ROOT/original['final_surface_file']).astype(float)
    raw=dict(original,integrated_socket_roofs=True)
    raw.pop('final_surface_file',None);raw.pop('authored_surface',None)
    rgb,gold,solid,pix,cx,cy,initial=drawing(raw)
    aperture=aperture_for(raw)
    outer,positions,_,_,_,factor,_,join=choose_geometry(raw,pix,initial,aperture)
    new=sculpt(raw,rgb,gold,solid,cx,cy,factor,aperture.buffer(6.5,join_style=join),outer,positions,height_only=True)
    yy,xx=np.indices(old.shape);x,y=(xx-cx)*factor,(cy-yy)*factor
    rho=np.sqrt(((x+30)/8.5)**2+((y-38.5)/9.0)**2)
    w=np.clip((1-rho)/.35,0,1);w=w*w*(3-2*w)
    out=old*(1-w)+new*w
    out[~solid]=old[~solid]
    assert np.isfinite(out).all() and out.max()<12
    assert np.array_equal(out[rho>=1],old[rho>=1])
    study=ROOT/'studies/period-catalog-six'
    target=study/(d['id']+'-final-height.npy')
    np.save(target,out.astype(np.float32))
    report=dict(id=d['id'],method='Replace the single exposed upper-left flat socket cap with existing leaf/scroll folds over a smooth oval support envelope; preserve all other final sculpture',
                region_center_mm=[-30,38.5],region_radii_mm=[8.5,9.0],
                original_height_file=original['final_surface_file'],outside_region_unchanged=True,
                delta_bounds_mm=[float((out-old).min()),float((out-old).max())],
                preserved=['approved outer silhouette','exact oval aperture','constant mat','all flower positions','three magnet centers','four snap positions','fork cross section','other final carving'])
    record=study/(d['id']+'-roof-refinement.json')
    record.write_text(json.dumps(report,indent=2)+'\n')
    d.update(final_surface_file=str(target.relative_to(ROOT)),refinement_record=str(record.relative_to(ROOT)),
             relief_method=report['method'],integrated_socket_roofs=True)
    source.write_text(json.dumps(ds,indent=2)+'\n')
    print(json.dumps(report),flush=True)


if __name__=='__main__':main()
