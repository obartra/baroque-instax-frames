# SPDX-License-Identifier: MIT
"""Refine each catalog relief using its own explicitly selected motif regions.

This operates on CAD height fields, never edits raster artwork. Dimensions,
photo openings and hardware remain independently constructed CAD geometry.
"""
import json
import os
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

from paths import ROOT
from build_floral_rococo import drawing, aperture_for, choose_geometry, sculpt


def smooth(t):
    t = np.clip(t, 0, 1)
    return t*t*(3-2*t)


def refine(d):
    raw = dict(d)
    raw.pop('final_surface_file', None)
    raw.pop('authored_surface', None)
    rgb, gold, solid, pix, cx, cy, initial = drawing(raw)
    aperture = aperture_for(raw)
    outer, positions, _, _, _, factor, _, join = choose_geometry(raw, pix, initial, aperture)
    old = sculpt(raw, rgb, gold, solid, cx, cy, factor,
                 aperture.buffer(6.5, join_style=join), outer, positions, height_only=True)
    yy, xx = np.indices(old.shape)
    x, y = (xx-cx)*factor, (cy-yy)*factor
    folds = ndi.gaussian_filter(old, .16/factor)-ndi.gaussian_filter(old, .85/factor)
    edit = np.zeros(old.shape)
    rounding = np.zeros(old.shape)
    regions = d.get('refine_regions', [])
    assert regions, 'Identify the existing flower/shell regions on each master first'
    # Region coordinates are fractions of the complete, unchanged master.
    for region in regions:
        px, py, rx, ry = region['ellipse']
        px *= old.shape[1]; rx *= old.shape[1]
        py *= old.shape[0]; ry *= old.shape[0]
        rho = np.sqrt(((xx-px)/rx)**2+((yy-py)/ry)**2)
        edit += np.clip(folds*region.get('fold_gain', .35), -.45, .55)*smooth((1-rho)/.15)
        rounding = np.maximum(rounding, smooth((1.08-rho)/.16)*smooth((rho-.55)/.18))
    out = np.maximum(old+ndi.gaussian_filter(edit, .12/factor), 1.301)
    # A rolling sphere softens sharp selected petal lips and narrow outer tips.
    # It does not add rims, duplicate petals or globally blur the carving.
    radius = d.get('local_roundover_radius_mm', .65)
    reach = int(np.ceil(radius/factor))
    ky, kx = np.mgrid[-reach:reach+1, -reach:reach+1]*factor
    r2 = kx*kx+ky*ky
    ball = np.sqrt(np.maximum(0, radius*radius-r2))-radius
    rolled = ndi.grey_opening(out, footprint=r2<=radius*radius, structure=ball)
    rolled = ndi.gaussian_filter(rolled, .16/factor)
    edge_distance = ndi.distance_transform_edt(solid)*factor
    rounding = np.maximum(rounding, smooth((1.15-edge_distance)/.55))*gold
    before = out.copy()
    out += np.clip(rolled-out, -.95, .20)*rounding
    # Retain closed snap socket roofs at their exact independently set height.
    for px, py in positions:
        dd = np.maximum(np.abs(x-px)-3.0, np.abs(y-py)-2.8)
        w = smooth((.8-dd)/.8)
        out = np.maximum(out, out*(1-w)+old*w)
    out[~solid] = old[~solid]
    assert np.isfinite(out).all() and out.max()<d['max_relief_mm']
    study = (ROOT/d['depth_file']).parent
    target = study/(d['id']+'-final-height.npy')
    np.save(target, out.astype(np.float32))
    record = study/(d['id']+'-sculpture-refinement.json')
    report = dict(id=d['id'], method='Local articulation of existing folds and rolling-sphere roundover of selected petal/shell lips and exterior tips over depth/normal relief',
                  features=regions, local_roundover_radius_mm=radius,
                  edit_bounds_mm=[float((out-old).min()),float((out-old).max())],
                  roundover_bounds_mm=[float((out-before).min()),float((out-before).max())],
                  height_bounds_mm=[float(out.min()),float(out.max())],
                  construction='Closed column-supported relief; no free-standing stamens or true undercuts',
                  preserved=['exact photo aperture','constant 6.5mm mat offset','motif arrangement','closed socket roofs','rounded-root fork mechanics'])
    record.write_text(json.dumps(report,indent=2)+'\n')
    d.update(final_surface_file=str(target.relative_to(ROOT)), authored_surface=True,
             refinement_record=str(record.relative_to(ROOT)), relief_method=report['method'])
    print('REFINED', d['id'], report['height_bounds_mm'], flush=True)


if __name__ == '__main__':
    source = Path(os.environ['BAROQUE_DESIGNS_FILE'])
    designs = json.loads(source.read_text())
    for d in designs:
        if len(sys.argv)==1 or d['id'] in sys.argv[1:]:
            refine(d)
    source.write_text(json.dumps(designs,indent=2)+'\n')
