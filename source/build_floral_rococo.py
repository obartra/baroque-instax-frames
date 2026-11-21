# SPDX-License-Identifier: MIT
"""Eight independent floral studies interpreted as printable bas-relief.

This is drawing-guided relief, not AI multi-view reconstruction. Exact photo,
mat, moulding and snap geometry is constructed separately from raster shading.
The prior release is not overwritten. Set BAROQUE_BUILD_DIR for outputs.
"""
from pathlib import Path
import json
import os
import sys

import numpy as np
import shapely
import trimesh as tm
from PIL import Image
from scipy import ndimage as ndi
from scipy.interpolate import RegularGridInterpolator
from shapely.affinity import scale
from shapely.geometry import Polygon, Point, box as rect

import build_catalog as b
from paths import ROOT, P

MAT = 6.5
UNDERLAY_INSET = .55
MAX_RELIEF = 12.0
DESIGNS = Path(os.environ.get("BAROQUE_DESIGNS_FILE", ROOT / "source/designs-current.json"))


def aperture_for(d):
    if d["shape"] == "oval":
        w, h = d["opening"]
        return scale(Point(0, 0).buffer(1, quad_segs=192), w / 2, h / 2)
    return b.aperture_for(d)


def largest(mask):
    labels, _ = ndi.label(mask)
    sizes = np.bincount(labels.ravel())
    sizes[0] = 0
    assert sizes.max() > 1000, "Drawing segmentation failed"
    return labels == sizes.argmax()


def drawing(d):
    """Analyze the front master only; never stretch or edit the saved artwork."""
    rgb = np.asarray(Image.open(ROOT / d.get("depth_file", d["concept_file"])).convert("RGB"), float)
    if not d.get("depth_file"):
        rgb = rgb[:, :int(rgb.shape[1] * .66)]
    r, g, blue = rgb.transpose(2, 0, 1)
    aperture_mask = largest((blue - r > 12) & (g - r > 5) & (blue > 90))
    yy, xx = np.nonzero(aperture_mask)
    cx, cy = (xx.min() + xx.max()) / 2, (yy.min() + yy.max()) / 2
    if d.get("depth_file"):
        # Warm plaster shading is still sculpture. A configurable chroma
        # tolerance prevents slightly warm petal shadows becoming false holes.
        neutral = d.get("neutral_chroma_tolerance",12)
        gold = largest((np.abs(r-g)<neutral) & (np.abs(r-blue)<neutral) & (r>28))
    else:
        gold = largest((r - blue > 64) & (g - blue > 24) & (r > 80))
    solid = ndi.binary_fill_holes(gold)
    holes = largest(solid & ~gold)
    hy, hx = np.nonzero(holes)
    # Match the source's inner moulding, not its approximate photo rectangle.
    # The final aperture and mat are independently specified exact CAD curves.
    aw, ah = d["opening"]
    if d.get("depth_file"):
        mm_per_pixel = max(aw/(xx.max()-xx.min()),ah/(yy.max()-yy.min()))
    else:
        mm_per_pixel = max((aw + 2 * MAT + .6) / (hx.max() - hx.min()),
                           (ah + 2 * MAT + .6) / (hy.max() - hy.min()))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    loops = ax.contour(solid.astype(float), levels=[.5]).allsegs[0]
    plt.close(fig)
    pix = max((Polygon(np.c_[q[:, 0] - cx, cy - q[:, 1]]).buffer(0)
               for q in loops if len(q) > 8), key=lambda p: p.area)
    # A uniform art-only adjustment can open the mat reserve without changing
    # the exact photo aperture or stretching the ornament along either axis.
    mm_per_pixel *= d.get("art_scale_multiplier", 1.0)
    return rgb, gold, solid, pix, cx, cy, mm_per_pixel


def choose_geometry(d, pix, initial_scale, aperture):
    portrait = d["orientation"] == "portrait"
    base_positions = d.get("snap_positions_mm", b.RECT_POS if d["shape"] == "rectangle" else b.POS)
    positions = [(-y, x) for x, y in base_positions] if portrait else base_positions
    film = rect(-27, -47, 27, 39) if portrait else rect(-47, -27, 39, 27)
    join = 2 if d["shape"] in ("rectangle", "octagon") else 1
    for growth in np.arange(1, 1.351, .005):
        factor = initial_scale * growth
        outer = scale(pix, factor, factor, origin=(0, 0)).buffer(.06).buffer(-.06).simplify(.035)
        needs = [film.buffer(.8), aperture.buffer(MAT + 5.5, join_style=join)]
        radius = d.get("socket_cover_radius_mm", 0)
        needs += [b.rounded_rect(x - 3.25, y - 3.0, x + 3.25, y + 3.0, radius)
                  if radius else rect(x - 3.25, y - 3.0, x + 3.25, y + 3.0) for x, y in positions]
        if d.get("local_cover_repair"):
            # Close small outline notches locally instead of enlarging every
            # flower, rail and crest to accommodate a few square millimeters.
            assert growth == 1, "Compact art must retain its calibrated scale"
            needs += [Point(x,y).buffer(4.9,quad_segs=32)
                      for x,y in d["magnet_centers_mm"]]
            required = shapely.union_all(needs)
            original = outer
            outer = outer.union(required).buffer(.15).buffer(-.15).buffer(.002)
            assert outer.difference(original).area < d["max_local_cover_area_mm2"]
            assert np.ptp(np.asarray(outer.bounds).reshape(2,2),axis=0).max() < d.get("max_outer_dimension_mm",111)
        if not all(outer.covers(n) for n in needs):
            continue
        centers = None
        if d.get("magnet_centers_mm"):
            proposed = d["magnet_centers_mm"]
            if all(outer.covers(Point(x,y).buffer(4.9,quad_segs=32)) for x,y in proposed):
                centers = proposed
        elif portrait:
            top = [float(y) for y in np.arange(47, 44.19, -.2)
                   if outer.covers(Point(0, y).buffer(4.9, quad_segs=32))]
            sides = [float(x) for x in np.arange(36, 32.19, -.2)
                     if all(outer.covers(Point(s * x, -27).buffer(4.9, quad_segs=32))
                            for s in (-1, 1))]
            if top and sides:
                centers = [(0, top[0]), (-sides[0], -27), (sides[0], -27)]
        else:
            top = [float(y) for y in np.arange(39, 32.19, -.2)
                   if outer.covers(Point(0, y).buffer(4.9, quad_segs=32))]
            low = [float(y) for y in np.arange(37, 32.19, -.2)
                   if all(outer.covers(Point(x, -y).buffer(4.9, quad_segs=32))
                          for x in (-27, 27))]
            if top and low:
                centers = [(0, top[0]), (-27, -low[0]), (27, -low[0])]
        if centers is not None:
            return outer, positions, base_positions, centers, film, factor, float(growth), join
    raise AssertionError((d["id"], "concealment requires excessive growth"))


def petal_overlap(d, gold, cx, cy, factor, inner, aperture):
    """Selected real petal contours may cover the mat, never the image opening."""
    if not d.get("petal_overlap_regions_mm"):
        return Polygon()
    yy, xx = np.indices(gold.shape)
    x, y = (xx-cx)*factor, (cy-yy)*factor
    region = np.zeros(gold.shape, bool)
    for px,py,radius in d["petal_overlap_regions_mm"]:
        region |= ((x-px)**2+(y-py)**2) < radius**2
    # Optional source-traced gates separate a crossing petal from the nearby
    # moulding. A circular height-edit region alone must not extend a strip
    # of that moulding onto the mat alongside the flower.
    if d.get("petal_overlap_outline_regions_mm"):
        outlines = shapely.union_all([
            Polygon(points).buffer(0) for points in d["petal_overlap_outline_regions_mm"]
        ])
        region &= shapely.contains_xy(outlines, x, y)
    mask = gold & region & shapely.contains_xy(inner,x,y)
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    loops = ax.contour(mask.astype(float),levels=[.5]).allsegs[0]
    plt.close(fig)
    pieces = [Polygon(np.c_[(q[:,0]-cx)*factor,(cy-q[:,1])*factor]).buffer(0)
              for q in loops if len(q)>8]
    pieces = [p for p in pieces if p.area>.15]
    assert pieces, "No petal overlap found in selected corner regions"
    petals = shapely.union_all(pieces).buffer(.10).buffer(-.10).simplify(.025)
    # Extend by one source pixel so raster contour rounding cannot leave an
    # artificial hairline gap between a crossing petal and its parent rail.
    petals = petals.buffer(.12).intersection(inner).difference(aperture.buffer(.85,join_style=2))
    parts = list(petals.geoms) if hasattr(petals,'geoms') else [petals]
    return shapely.union_all([p for p in parts if p.distance(inner.boundary)<.001])


def sculpt(d, rgb, gold, solid, cx, cy, factor, inner, outer, positions, height_only=False, petals=None):
    """Separate broad volume, motif relief and fine surface articulation."""
    yy, xx = np.indices(solid.shape)
    x, y = (xx - cx) * factor, (cy - yy) * factor
    lum = np.dot(rgb, [.2126, .7152, .0722])
    nearest = ndi.distance_transform_edt(~gold, return_distances=False, return_indices=True)
    lum = ndi.gaussian_filter(lum[tuple(nearest)], 1.0)
    lo, hi = np.percentile(lum[gold], [3, 98])
    light = np.clip((lum - lo) / (hi - lo), 0, 1)
    middle = ndi.gaussian_filter(light, 3.1)
    broad = ndi.gaussian_filter(light, 9.0)
    points = shapely.points(x[::4, ::4].ravel(), y[::4, ::4].ravel())
    shape = x[::4, ::4].shape
    din = shapely.distance(points, inner).reshape(shape)
    dout = shapely.distance(points, outer.boundary).reshape(shape)
    def upsample(v):
        return ndi.zoom(v, (x.shape[0] / v.shape[0], x.shape[1] / v.shape[1]), order=1)[:x.shape[0], :x.shape[1]]
    din, dout = upsample(din), upsample(dout)
    # An actual convex rail envelope beneath the ornament, rather than a flat
    # photographic plaque; shell/flower macro masses rise independently.
    across = np.clip(din / np.maximum(din + dout, .01), 0, 1)
    curved_rail = .65 * np.sin(np.pi * across) ** .8
    if d.get("surface_file"):
        h=np.load(ROOT/d["surface_file"]).astype(float)
        assert h.shape==x.shape
        h=np.maximum(h,1.301+1.0*np.sin(np.pi*across)**.8)
    elif d.get("depth_file"):
        # Rejected direct-brightness comparison, retained for reproducibility.
        height_signal = ndi.gaussian_filter(np.mean(rgb,axis=2),.55)/255
        h = np.maximum(1.301 + 1.0*np.sin(np.pi*across)**.8,
                       1.301 + 10.5*np.clip(height_signal,0,1)**1.7)
    else:
        h = 1.8 + curved_rail + 2.65 * middle ** .8 + 1.2 * broad ** .8 + .32 * (light - middle)
        for px, py, radius, amplitude in d.get("flower_masses_px", []):
            h += amplitude * np.exp(-2 * (((xx - px) / radius) ** 2 + ((yy - py) / radius) ** 2))
    if d.get("flower_center_regions_mm"):
        # Broad low centers replace fine inferred pollen peaks. All relief
        # remains a continuous column-supported field, never wire stamens.
        smooth = ndi.gaussian_filter(h,d.get("center_smoothing_mm",.35)/factor)
        for px,py,radius in d["flower_center_regions_mm"]:
            w = np.clip((radius-np.hypot(x-px,y-py))/.8,0,1)
            w = w*w*(3-2*w)
            h = h*(1-w)+smooth*w
    blend = np.clip((din - d.get("ornament_blend_start_mm", 4.6)) / d.get("ornament_blend_span_mm", 2.1), 0, 1)
    blend = blend * blend * (3 - 2 * blend)
    for px,py,radius in d.get("petal_overlap_regions_mm", []):
        # Keep the volume of the whole flower as it crosses the moulding;
        # only the selected petal silhouette below may extend over the mat.
        w = np.clip((radius-np.hypot(x-px,y-py))/2,0,1)
        blend = np.maximum(blend,w*w*(3-2*w))
    h = 1.301 + (h - 1.301) * blend
    edge = np.clip(ndi.distance_transform_edt(solid) * factor / 1.1, 0, 1)
    h = 1.301 + (h - 1.301) * edge * edge * (3 - 2 * edge)
    if d.get("local_cover_repair"):
        # Tiny closed silhouette notches also need a real socket roof.
        # Reset the inferred field first, then form the same rounded roof
        # envelope across the locally repaired outline, rather than erase it.
        h[~solid] = 1.301
    for px, py in positions:
        if d.get("integrated_socket_roofs"):
            # Lift the existing local carving over a smooth oval support
            # envelope. Preserve its folds instead of replacing a low flower
            # or leaf with a flat rectangular maximum-height socket cap.
            core = (np.abs(x-px)<=2.9) & (np.abs(y-py)<=2.7)
            lift = max(0., 5.6-float(h[core].min()))
            rho = np.sqrt(((x-px)/7.5)**2+((y-py)/7.0)**2)
            support = np.clip((1-rho)/.45,0,1)
            h += lift*support*support*(3-2*support)
            continue
        # Rounded hidden socket roof lands. Avoid the previous visibly square
        # mechanical caps on curved frames; feather roofs into carved masses.
        dd = np.maximum(np.abs(x - px) - 2.85, np.abs(y - py) - 2.65)
        w = np.clip(1 - dd / 2.8, 0, 1)
        w = w * w * (3 - 2 * w)
        roof = 5.35 + .2 * light
        h = np.maximum(h, h * (1 - w) + roof * w)
    # Smoothly limit extreme inferred peaks without making clipped flat caps.
    ceiling = d.get("max_relief_mm", MAX_RELIEF)
    if d.get("authored_surface") and not d.get("final_surface_file"):
        # Hand-authored geometric layers have specified heights, unlike the
        # uncalibrated inferred field. Preserve their petal/lip separation.
        assert h.max() < ceiling, ("authored relief exceeds envelope", h.max())
    else:
        excess=np.maximum(h-1.301,0)
        h=1.301+(ceiling-1.301)*np.tanh(excess/(ceiling-1.301))
    h = ndi.gaussian_filter(h, .6)
    if d.get("seeded_center_regions_mm"):
        # Sunflower-like texture is shallow relief on a continuous bowl,
        # never an array of stalks or large ball-shaped pollen projections.
        for px,py,radius in d["seeded_center_regions_mm"]:
            dx,dy=x-px,y-py
            rho=np.hypot(dx,dy)/radius
            inside=rho<1
            if not inside.any():continue
            dome=np.clip(1-rho*rho,0,1)**1.6
            texture=np.zeros(h.shape)
            count=max(7,int(np.pi*radius*radius/.62))
            golden_angle=np.pi*(3-np.sqrt(5))
            for i in range(count):
                angle=i*golden_angle
                rr=radius*.90*np.sqrt((i+.5)/count)
                ex,ey=dx-rr*np.cos(angle),dy-rr*np.sin(angle)
                radial=ex*np.cos(angle)+ey*np.sin(angle)
                tangent=-ex*np.sin(angle)+ey*np.cos(angle)
                # Broad, very low elliptical scales. Maximum prominence is
                # .64 mm including the disk; fine texture may soften in FDM.
                seed=.14*np.exp(-2*((radial/.43)**2+(tangent/.31)**2))
                texture=np.maximum(texture,seed)
            fade=np.clip((1-rho)/.15,0,1)
            fade=fade*fade*(3-2*fade)
            h += .50*dome+texture*fade
    if d.get("final_surface_file"):
        final_height = np.load(ROOT/d["final_surface_file"]).astype(float)
        assert final_height.shape == h.shape and np.all(np.isfinite(final_height))
        assert final_height.max() < ceiling
        h = final_height
    if not d.get("local_cover_repair"):
        h[~solid] = 1.301
    if height_only:
        return h
    sy, sx = np.nonzero(gold)
    step = .21 / factor
    xs = np.arange(max(0, sx.min() - 2), min(rgb.shape[1] - 1, sx.max() + 3), step)
    ys = np.arange(max(0, sy.min() - 2), min(rgb.shape[0] - 1, sy.max() + 3), step)
    xp, yp = np.meshgrid(xs, ys)
    z = RegularGridInterpolator((np.arange(h.shape[0]), np.arange(h.shape[1])), h)(np.c_[yp.ravel(), xp.ravel()])
    v = np.c_[((xp - cx) * factor).ravel(), ((cy - yp) * factor).ravel(), z]
    ny, nx = xp.shape
    ids = np.arange(nx * ny).reshape(ny, nx)
    a, bb, c, dd = (q.ravel() for q in (ids[:-1, :-1], ids[:-1, 1:], ids[1:, 1:], ids[1:, :-1]))
    ff = np.vstack([np.c_[a, bb, c], np.c_[a, c, dd]])
    bottom = v.copy()
    bottom[:, 2] = 1.29
    n = len(v)
    faces = [ff, ff[:, ::-1] + n]
    rim = list(ids[0]) + list(ids[1:, -1]) + list(ids[-1, -2::-1]) + list(ids[-2:0:-1, 0])
    for a, bb in zip(rim, rim[1:] + rim[:1]):
        faces.append(np.array([[a, bb, bb + n], [a, bb + n, a + n]]))
    raw = tm.Trimesh(np.vstack([v, bottom]), np.vstack(faces))
    raw.fix_normals()
    assert raw.is_volume
    footprint = outer.difference(inner)
    if petals is not None and not petals.is_empty:
        footprint = footprint.union(petals)
    if d.get("relief_footprint_precision_mm"):
        # Source contours can meet the curved inner rail at almost identical
        # coordinates. Snap only this extrusion footprint to a microscopic
        # grid so its cap triangulates as a closed volume.
        footprint = shapely.set_precision(footprint, d["relief_footprint_precision_mm"])
    return b.check(b.inter(raw, b.extrude(footprint, 1.3, ceiling + 1)), "floral relief")


def finalize_and_validate(d, outer, aperture, white, black, back, loaded, positions, centers, filmshape):
    portrait = d["orientation"] == "portrait"
    cavities = [b.box(2.4, 4.3, 1.7, 3, p) if portrait else b.box(4.3, 2.4, 1.7, 3, p) for p in positions]
    black = b.check(b.diff(black, b.union(cavities)), "final socket cavities")
    for p in positions:
        roof = b.box(2, 3.9, .15, 4.85, p) if portrait else b.box(3.9, 2, .15, 4.85, p)
        assert abs(b.inter(black, roof).volume - roof.volume) < .002, ("closed roof", p)
    mounted = [m.copy() for m in (white, black)]
    for m in mounted:
        m.apply_translation([0, 0, b.MATE])
    interference = sum(abs(b.inter(m, back).volume) for m in mounted)
    assert interference < .015, ("assembly interference", interference)
    pulled = [m.copy() for m in mounted]
    for m in pulled:
        m.apply_translation([0, 0, .5])
    for x, y in positions:
        region = b.box(8, 8, 12, -.1, (x, y))
        contact = sum(abs(b.inter(b.inter(m, back), region).volume) for m in pulled)
        assert contact > .005, ("snap retention", x, y, contact)
    film = b.box(54.2, 86.2, 1.16, 2.42, (0, -4)) if portrait else b.box(86.2, 54.2, 1.16, 2.42, (-4, 0))
    assert abs(b.inter(loaded, film).volume) < .02, "film channel interference"
    assert sum(abs(b.inter(m, film).volume) for m in mounted) < .005
    for amount in np.linspace(0, 94, 28):
        q = film.copy()
        q.apply_translation([0, -amount, 0] if portrait else [-amount, 0, 0])
        assert abs(b.inter(loaded, q).volume) < .02, ("insertion interference", amount)
    for x, y in centers:
        assert abs(b.inter(back, b.cyl(x, y, 3, 0, 3)).volume) < .001
        floor = b.cyl(x, y, 2.9, 3.15, .4)
        assert abs(b.inter(back, floor).volume - floor.volume) < .001
    assert abs(b.inter(white, black).volume) < .001
    assert filmshape.buffer(.6).difference(outer).area < .001
    for sx in (-.6, 0, .6):
        for sy in (-.6, 0, .6):
            image = rect(-23 + sx, -31 + sy, 23 + sx, 31 + sy) if portrait else rect(-31 + sx, -23 + sy, 31 + sx, 23 + sy)
            assert image.covers(aperture), ("image overlap", sx, sy)
    triangles = back.triangles[np.abs(back.face_normals[:, 2]) > 1e-8, :, :2]
    projection = shapely.union_all(shapely.polygons(triangles), grid_size=1e-5)
    assert projection.difference(outer.buffer(-.489)).area < .02, "visible back projection"
    # White underlay stays inset at the exterior, independently of the back.
    assert outer.buffer(-UNDERLAY_INSET + .002).covers(shapely.union_all(
        shapely.polygons(white.triangles[np.abs(white.face_normals[:, 2]) > 1e-8, :, :2]), grid_size=1e-5
    )), "visible white exterior fringe"
    return black, interference


def build(d):
    q = P / d["id"]
    q.mkdir(exist_ok=True)
    mat_height = float(d.get("mat_height_mm", .36))
    assert .36 <= mat_height < 1.3, "Mat must remain below the ornament foundation"
    rgb, gold, solid, pix, cx, cy, initial_scale = drawing(d)
    aperture = aperture_for(d)
    outer, positions, base_positions, centers, filmshape, factor, growth, join = choose_geometry(d, pix, initial_scale, aperture)
    print("BUILD", d["id"], "scale", factor, "growth", growth, "bounds", outer.bounds, flush=True)
    inner = aperture.buffer(MAT, join_style=join)
    petals = petal_overlap(d,gold,cx,cy,factor,inner,aperture)
    art = sculpt(d, rgb, gold, solid, cx, cy, factor, inner, outer, positions, petals=petals)
    white = b.extrude(outer.buffer(-UNDERLAY_INSET).difference(aperture), 0, mat_height)
    layers = []
    zz = np.linspace(mat_height, 1.3, 13)
    for z0, z1 in zip(zz[:-1], zz[1:]):
        inset = UNDERLAY_INSET * (1 - (z0 - mat_height) / (1.3 - mat_height))
        layers.append(b.extrude(outer.buffer(-inset).difference(inner), z0, z1 - z0 + .00002))
    if not petals.is_empty:
        # The black petals grow directly from the printed light layer, with
        # no floating air gap and no circular pad around their contours.
        layers.append(b.extrude(petals, mat_height, 1.3 - mat_height + .00002))
        assert petals.intersection(aperture.buffer(.84,join_style=join)).area < .001
    if d.get("sculpted_moulding"):
        from refine_shell_acanthus import sculpted_moulding
        moulding = sculpted_moulding(aperture, outer, join)
    else:
        moulding = b.moulding(aperture, join, profile=d.get("moulding_profile"))
    black = b.union([art, moulding] + layers)
    portrait = d["orientation"] == "portrait"
    cuts = b.union([b.rotate_mesh(b.socket((y, -x)), True) if portrait else b.socket((x, y)) for x, y in positions])
    black = b.check(b.diff(black, cuts), "socketed ornament")
    white = b.diff(white, cuts)
    if d.get("allow_underlay_islands"):
        # An inset underlay can split under narrow, irregular outer petals.
        # These all start on the bed and fuse into the single black front.
        # Validate the actual printed assembly rather than inventing visible
        # white bridges between otherwise hidden first-layer islands.
        assert white.is_watertight and white.is_volume
        b.check(b.union([white,black]), "fused multicolor front")
    else:
        white = b.check(white, "white mat")
    back, loaded = b.back_geometry(portrait, outer, centers, base_positions)
    black, interference = finalize_and_validate(d, outer, aperture, white, black, back, loaded, positions, centers, filmshape)
    for name, mesh in (("white-mat.stl", white), ("black-ornament.stl", black), ("back.stl", back), ("loaded-back.stl", loaded)):
        mesh.export(q / name)
    report = dict(id=d["id"], name=d["name"], orientation=d["orientation"], shape=d["shape"],
        front_dimensions_mm=np.ptp(black.bounds, axis=0).tolist(), front_bounds_mm=black.bounds.tolist(),
        back_dimensions_mm=np.ptp(back.bounds, axis=0).tolist(), assembled_depth_mm=float(b.MATE + black.bounds[1, 2]),
        mat_width_mm=MAT, mat_height_mm=mat_height, mat_perpendicular_offset=True, white_exterior_inset_mm=UNDERLAY_INSET,
        film_uncut_mm=[54, 86] if portrait else [86, 54], aperture_bounds_mm=list(aperture.bounds),
        image_area_visible_percent=100 * aperture.area / (62 * 46), full_film_concealed=True,
        nominal_edge_overlap_mm=1.0, misalignment_checked_mm=.6, magnet_centers_mm=centers,
        magnet_pockets_mm=[6.3, 3.1], magnet_floor_mm=.5, snap_positions_mm=positions,
        snap_tip_height_mm=8, snap_stem_mm=[3.5, 2], snap_slot_radius_mm=.7,
        snap_head_width_mm=3.88, socket_neck_width_mm=3.65, snap_arm_section_mm=[1.05, 2.0],
        snap_axial_relaxation_mm=.15, snap_per_arm_deflection_mm=.115, photo_spring_length_mm=15,
        front_print_color_changes=1, watertight_parts=True, insertion_positions_checked=28,
        closed_socket_roofs_checked=True, back_projection_hidden=True, assembly_interference_mm3=interference,
        physical_test=False, ornament_source=d["concept_file"],
        provenance=d.get("provenance", "Independent generated concepts; no original MakerWorld mesh or photo input"),
        relief_method="Estimated sculpture depth with integrated surface normals and exact CAD mouldings; not multi-view reconstruction" if d.get("surface_file") else "Rejected direct-brightness relief experiment",
        drawing_uniform_growth=growth, drawing_mm_per_pixel=factor, drawing_center_px=[float(cx), float(cy)])
    if not petals.is_empty:
        report.update(petal_overlap_area_mm2=petals.area,petal_overlap_supported_from_layer_mm=mat_height,
                      clear_aperture_preserved=True,local_cover_repair=True)
    if d.get("allow_underlay_islands"):
        report.update(hidden_underlay_components=len(white.split()),fused_front_single_volume=True)
    if d.get("flower_center_regions_mm"):
        report.update(flower_centers_smoothed_mm=d.get("center_smoothing_mm",.35),
                      ornament_is_supported_heightfield=True,freestanding_flower_stalks=False)
    if d.get("seeded_center_regions_mm"):
        report.update(center_method="Explicit shallow disk with phyllotactic low seed scales over the saved petal surface",
                      seeded_center_regions_mm=d["seeded_center_regions_mm"],center_added_prominence_max_mm=.64,
                      seed_scale_half_axes_mm=[.43,.31],seed_texture_height_max_mm=.14)
    if d.get("refinement_record"):
        report.update(refinement_record=d["refinement_record"], authored_surface=d.get("authored_surface",False),
                      relief_method=d.get("relief_method", "Contour-following petal-lip/groove refinement, shell articulation and swept rail section over the independent drawing-guided relief"))
    (q / "validation.json").write_text(json.dumps(report, indent=2) + "\n")
    (q / "aperture.wkt").write_text(aperture.wkt)
    (q / "outer.wkt").write_text(outer.wkt)
    (P / "validation" / (d["id"] + "-geometry.json")).write_text(json.dumps(report, indent=2) + "\n")
    project = b.write_project(d, white, black, back)
    print("COMPLETE", d["id"], "project", project, "depth", report["assembled_depth_mm"], flush=True)


if __name__ == "__main__":
    for design in json.loads(DESIGNS.read_text()):
        if len(sys.argv) == 1 or design["id"] in sys.argv[1:]:
            build(design)
