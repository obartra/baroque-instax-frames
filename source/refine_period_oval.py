# SPDX-License-Identifier: MIT
"""Articulate the approved oval's existing folds and recessed carved grounds.

This authors CAD surface geometry, not a bitmap. It keeps the drawing's motif
positions and photo boundary; no generic extra petal rims are superimposed.
"""
import json
import os
from pathlib import Path

import numpy as np
import shapely
from scipy import ndimage as ndi

from paths import ROOT
from build_floral_rococo import drawing, aperture_for, choose_geometry, sculpt


def smooth(t):
    t = np.clip(t, 0, 1)
    return t*t*(3-2*t)


def main():
    source = Path(os.environ['BAROQUE_DESIGNS_FILE'])
    designs = json.loads(source.read_text())
    for d in designs:
        raw = dict(d)
        raw.pop('final_surface_file', None)
        raw.pop('authored_surface', None)
        rgb, gold, solid, pix, cx, cy, initial = drawing(raw)
        aperture = aperture_for(raw)
        outer, positions, _, _, _, factor, _, join = choose_geometry(raw, pix, initial, aperture)
        inner = aperture.buffer(6.5, join_style=join)
        old = sculpt(raw, rgb, gold, solid, cx, cy, factor, inner, outer, positions, height_only=True)
        yy, xx = np.indices(old.shape)
        x, y = (xx-cx)*factor, (cy-yy)*factor
        # Amplify existing broad fold separations, leaving each flower's
        # distinctive attitude intact. This cannot invent a second outline.
        folds = ndi.gaussian_filter(old, .16/factor)-ndi.gaussian_filter(old, .85/factor)
        edit = np.zeros(old.shape)
        regions = [(480,480,100,.65,'left open flower'),
                   (1075,480,110,.65,'right open flower'),
                   (506,260,65,.45,'upper turned flower'),
                   (1020,650,72,.50,'lower nested flower'),
                   (785,100,125,.55,'curled upper shell'),
                   (787,880,125,.55,'lower shell and leaf response')]
        for px, py, radius, amount, label in regions:
            w = smooth((radius-np.hypot(xx-px, yy-py))/15)
            edit += np.clip(folds*amount, -.6, .7)*w
        # Selected existing ground reserves, identified on the approved master.
        # Round the transitions while keeping their fine inferred texture.
        grounds = [
            [(610,186),(650,173),(683,185),(662,212),(637,229),(617,213)],
            [(893,151),(922,148),(946,164),(937,187),(916,188),(900,172)],
            [(590,834),(613,828),(637,846),(634,866),(609,875),(589,855)],
        ]
        for points in grounds:
            polygon = shapely.Polygon(points)
            mask = shapely.contains_xy(polygon, xx, yy)
            distance = ndi.distance_transform_edt(mask)*factor
            edit -= .55*smooth(distance/.8)
        edit = ndi.gaussian_filter(edit, .12/factor)
        out = np.maximum(old+edit, 1.301)
        # A rolling sphere rounds only the identified lips and narrow outer
        # tips. Keep broad bowls, flutes and the recessed grounds unsmoothed.
        radius_mm = .72
        reach = int(np.ceil(radius_mm/factor))
        ky, kx = np.mgrid[-reach:reach+1, -reach:reach+1]*factor
        r2 = kx*kx+ky*ky
        footprint = r2 <= radius_mm*radius_mm
        ball = np.sqrt(np.maximum(0, radius_mm*radius_mm-r2))-radius_mm
        rolled = ndi.grey_opening(out, footprint=footprint, structure=ball)
        rolled = ndi.gaussian_filter(rolled, .20/factor)
        rounded_regions = [(480,472,92,95,'left flower rim'),
                           (1075,480,116,103,'right flower rim'),
                           (1020,650,78,68,'nested flower tips')]
        rounding = np.zeros(old.shape)
        for px, py, rx, ry, label in rounded_regions:
            rho = np.sqrt(((xx-px)/rx)**2+((yy-py)/ry)**2)
            w = smooth((1.08-rho)/.16)*smooth((rho-.58)/.14)
            rounding = np.maximum(rounding, w)
        shell_rho = np.sqrt(((xx-790)/125)**2+((yy-60)/63)**2)
        rounding = np.maximum(rounding, smooth((1.06-shell_rho)/.18))
        edge_distance = ndi.distance_transform_edt(solid)*factor
        rounding = np.maximum(rounding, smooth((1.2-edge_distance)/.55))
        rounding *= gold
        before_rounding = out.copy()
        out += np.clip(rolled-out, -1.15, .25)*rounding
        # Keep the tested closed socket roofs and their rounded support lands.
        for px, py in positions:
            dd = np.maximum(np.abs(x-px)-3.0, np.abs(y-py)-2.8)
            protect = smooth((.8-dd)/.8)
            out = np.maximum(out, out*(1-protect)+old*protect)
        out[~solid] = old[~solid]
        assert np.isfinite(out).all() and out.max() < 12
        study = ROOT/'studies/period-grounded-ovals'
        target = study/(d['id']+'-final-height.npy')
        np.save(target, out.astype(np.float32))
        report = dict(id=d['id'], method='Local geometric articulation of existing broad folds and recessed ground reserves over estimated depth/normal relief',
                      features=[dict(center_px=[a,b],radius_px=r,gain=g,feature=name) for a,b,r,g,name in regions],
                      ground_reserves_px=grounds, ground_recess_max_mm=.55,
                      maximum_edit_mm=[float((out-old).min()), float((out-old).max())],
                      local_roundover_radius_mm=radius_mm,
                      roundover_regions_px=rounded_regions,
                      roundover_delta_mm=[float((out-before_rounding).min()),float((out-before_rounding).max())],
                      height_bounds_mm=[float(out.min()),float(out.max())],
                      preserved=['exact 44x60 elliptical image aperture','clean 6.5mm mat boundary',
                                 'original flower and shell arrangement','closed socket roofs','rounded-root fork mechanics'],
                      construction='Closed column-supported relief; selective visible hollows, no free-standing stalks or true undercuts',
                      modern_compromises=['0.36mm mat layer','supported backs of sculptural motifs','hidden photo and magnet mechanics'])
        record = study/'sculpture-refinement.json'
        record.write_text(json.dumps(report, indent=2)+'\n')
        d.update(final_surface_file=str(target.relative_to(ROOT)), authored_surface=True,
                 refinement_record=str(record.relative_to(ROOT)),
                 relief_method=report['method'],max_relief_mm=12)
        print(json.dumps(report), flush=True)
    source.write_text(json.dumps(designs, indent=2)+'\n')


if __name__ == '__main__':
    main()
