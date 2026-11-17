# SPDX-License-Identifier: MIT
"""Compare local back-plate extrusion paths to CAD at every sliced layer.

This checks for omitted cross-section islands and missing fork/magnet/spring
regions; it does not establish strength or exact volumetric extrusion quality.
"""
import argparse
import json
import hashlib
import os
import re
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import shapely
from shapely.geometry import Polygon, MultiLineString, box
import trimesh as tm

from paths import P, ROOT


def parse(path, xy_offset=(128., 128.)):
    """Read linear extrusion paths, honoring coordinate and extrusion modes.

    The default remains the native projects' [128, 128] plate placement.
    A different placement must be supplied explicitly; a wrong placement fails
    the CAD/path overlap checks rather than silently aligning itself to them.
    """
    layers = []
    xy = np.zeros(2)
    printing = False
    feature = 'Custom'
    width = .42
    relative_xy = False
    relative_e = True
    e_position = 0.
    for line in path.read_text().splitlines():
        if line.startswith('; Z_HEIGHT:'):
            layers.append(dict(z=float(line.split(':')[1]), lines=[], widths=[]))
            printing = True
        elif line.startswith('; FEATURE:'):
            feature = line.split(':',1)[1].strip()
        elif line.startswith('; LINE_WIDTH:'):
            width = float(line.split(':')[1])
        code = line.split(';',1)[0].strip()
        command = code.split(maxsplit=1)[0] if code else ''
        if command in ('G90', 'G91'):
            relative_xy = command == 'G91'
            continue
        if command in ('M82', 'M83'):
            relative_e = command == 'M83'
            continue
        values = {k:float(v) for k,v in re.findall(r'([XYEIJ])(-?[0-9]*\.?[0-9]+)', code)}
        if command == 'G92':
            for index, axis in enumerate(('X', 'Y')):
                if axis in values:
                    xy[index] = values[axis]
            e_position = values.get('E', e_position)
            continue
        if command not in ('G0', 'G1', 'G2', 'G3'):
            continue
        new = np.array([values.get('X',0), values.get('Y',0)]) + xy if relative_xy else np.array([values.get('X',xy[0]), values.get('Y',xy[1])])
        extrusion = values.get('E', 0.) if relative_e else values.get('E', e_position)-e_position
        if 'E' in values:
            e_position = e_position + values['E'] if relative_e else values['E']
        if printing and feature != 'Custom' and extrusion > 0 and np.linalg.norm(new-xy) > .001:
            assert command not in ('G2', 'G3'), 'Arc extrusion requires a sampled arc parser'
            layers[-1]['lines'].append(np.array([xy,new])-np.asarray(xy_offset))
            layers[-1]['widths'].append(width)
        xy = new
    return layers


def section(mesh, z):
    path = mesh.section(plane_origin=[0,0,z], plane_normal=[0,0,1])
    assert path is not None
    shape = Polygon()
    for loop in path.discrete:
        shape = shape.symmetric_difference(Polygon(loop[:,:2]).buffer(0))
    return shape


def polygons(shape):
    return [p for p in (list(shape.geoms) if hasattr(shape, 'geoms') else [shape])
            if p.geom_type == 'Polygon' and not p.is_empty]


def functional_regions(mesh, geometry):
    """Get world-space features from validated data and actual moat geometry.

    Design JSON snap positions can be canonical/pre-rotation coordinates.
    Finished validation.json positions are therefore required instead.
    """
    regions = []
    head = geometry.get('snap_head_width_mm', 3.88)
    depth = geometry.get('snap_stem_mm', [3.5, 2.])[1]
    half = (head/2+.36, depth/2+1.5)
    if geometry['orientation'] == 'portrait':
        half = half[::-1]
    for i, (x, y) in enumerate(geometry['snap_positions_mm'], 1):
        regions.append((f'fork {i} ({x:g},{y:g})', box(x-half[0], y-half[1], x+half[0], y+half[1])))
    boss_radius = geometry.get('magnet_boss_radius_mm', geometry['magnet_pockets_mm'][0]/2+1.45)
    for i, (x, y) in enumerate(geometry['magnet_centers_mm'], 1):
        regions.append((f'magnet {i} ({x:g},{y:g})', shapely.Point(x,y).buffer(boss_radius)))

    # A future mechanism may supply explicit world-space spring bounds. For
    # the existing four-spring carrier, discover its long, narrow moat holes
    # in an actual section. This works after either orientation and cropping.
    explicit = geometry.get('spring_regions_mm')
    if explicit is not None:
        springs = [box(*bounds) for bounds in explicit]
        spring_source = 'validation.json spring_regions_mm (world-space bounds)'
    else:
        expected_length = geometry['photo_spring_length_mm']
        probe = min(3.16, float(mesh.bounds[1, 2])*.4)
        springs = []
        for poly in polygons(section(mesh, probe)):
            for ring in poly.interiors:
                x0, y0, x1, y1 = ring.bounds
                width, height = x1-x0, y1-y0
                long, short = max(width,height), min(width,height)
                if short > 0 and long/short >= 3 and .5*expected_length <= long <= 1.5*expected_length:
                    # Include the beam alongside the void and its rounded tip,
                    # not the empty hole alone. Use bounds to include the beam
                    # even when the remaining hole is U-shaped.
                    springs.append(box(x0-1., y0-1., x1+1., y1+1.))
        spring_source = f'elongated moat-hole bounds in actual back section at {probe:.3f} mm, expanded 1 mm'
    expected_count = geometry.get('photo_spring_count', len(geometry['snap_positions_mm']))
    assert len(springs) == expected_count, (
        f"Expected {expected_count} spring moats, found {len(springs)}. "
        'Inspect the mechanism or supply spring_regions_mm in the geometry report.'
    )
    springs.sort(key=lambda p: (p.centroid.x, p.centroid.y))
    regions += [(f'spring {i}', region) for i, region in enumerate(springs, 1)]
    return regions, spring_source


def audit_layers(mesh, layers, regions):
    assert layers, 'No sliced layers found'
    prior = 0
    failures = []
    region_failures = []
    rows = []
    chosen = []
    for index, layer in enumerate(layers):
        z = (prior+layer['z'])/2
        prior = layer['z']
        shape = section(mesh, z)
        paths = MultiLineString(layer['lines'])
        ink = paths.buffer(.27, quad_segs=4)
        pieces = polygons(shape)
        for piece in pieces:
            if piece.area > .12 and piece.intersection(ink).area < .02:
                failures.append(dict(layer=index+1,z=layer['z'],area_mm2=piece.area,bounds=piece.bounds))
        # The narrow functional regions should receive substantial path
        # coverage, even when the carrier interior intentionally uses infill.
        ratios = []
        for name, region in regions:
            needed = shape.intersection(region)
            if needed.area > .2:
                ratio = needed.intersection(ink).area/needed.area
                ratios.append(ratio)
                if ratio < .15:
                    region_failures.append(dict(layer=index+1,z=layer['z'],region=name,coverage=ratio))
        rows.append(dict(layer=index+1,z=layer['z'],components=len(pieces),
                         extrusion_segments=len(layer['lines']),minimum_functional_coverage=min(ratios,default=1)))
        if any(abs(layer['z']-target)<.025 for target in (1.64,3.16,6.84,7.8)):
            chosen.append((layer,shape,paths))
    return failures, region_failures, rows, chosen


def audit_design(d, build_dir=P, output_dir=None, xy_offset=None, legacy_plot=False):
    build_dir = Path(build_dir)
    output_dir = Path(output_dir) if output_dir is not None else build_dir
    q = build_dir/d['id']
    geometry_path = q/'validation.json'
    if not geometry_path.is_file():
        geometry_path = build_dir/'validation'/(d['id']+'-geometry.json')
    geometry = json.loads(geometry_path.read_text())
    assert geometry['id'] == d['id'], 'Geometry report does not match selected design'
    mesh_path = q/'back.stl'
    gcode_path = q/'slice-final/plate_2.gcode'
    mesh = tm.load_mesh(mesh_path)
    offset = xy_offset if xy_offset is not None else geometry.get('back_plate_xy_offset_mm', [128.,128.])
    layers = parse(gcode_path, offset)
    regions, spring_source = functional_regions(mesh, geometry)
    failures, region_failures, rows, chosen = audit_layers(mesh, layers, regions)
    report = dict(id=d['id'],plate=2,layers_checked=len(layers),
                  gcode_sha256=hashlib.sha256(gcode_path.read_bytes()).hexdigest(),
                  back_stl_sha256=hashlib.sha256(mesh_path.read_bytes()).hexdigest(),
                  geometry_report_sha256=hashlib.sha256(geometry_path.read_bytes()).hexdigest(),
                  orientation=geometry['orientation'], xy_offset_mm=list(offset),
                  functional_regions=[dict(name=name,bounds_mm=list(region.bounds)) for name,region in regions],
                  spring_region_source=spring_source,
                  missing_cross_section_components=failures,missing_functional_regions=region_failures,
                  minimum_functional_coverage=min(r['minimum_functional_coverage'] for r in rows),
                  path_buffer_radius_mm=.27,component_area_threshold_mm2=.12,
                  source='Delivered plate_2.gcode compared with actual back.stl at each mid-layer height',
                  limitation='Checks omitted islands and functional-region path presence; not a strength or exact extrusion-volume test',
                  layers=rows)
    (output_dir/'validation').mkdir(parents=True, exist_ok=True)
    (output_dir/'renders').mkdir(parents=True, exist_ok=True)
    dest=output_dir/'validation'/(d['id']+'-back-toolpaths.json')
    dest.write_text(json.dumps(report,indent=2)+'\n')
    fig, axes = plt.subplots(2,2,figsize=(11,13),dpi=140)
    for ax,(layer,shape,paths) in zip(axes.flat,chosen):
        for poly in polygons(shape):
            ax.fill(*poly.exterior.xy,color='#dedbd5')
            for ring in poly.interiors:ax.fill(*ring.xy,color='white')
        for line in paths.geoms:ax.plot(*line.xy,color='#006f8a',lw=.35)
        ax.set_title(f"Back plate at {layer['z']:.2f} mm")
        ax.set_aspect('equal');ax.axis('off')
    for ax in list(axes.flat)[len(chosen):]:
        ax.axis('off')
    fig.suptitle('Actual CAD section (gray) and extrusion paths (blue)',fontsize=15)
    fig.tight_layout(rect=[0,0,1,.97])
    fig.savefig(output_dir/'renders'/(d['id']+'-Back-Toolpath-Sections.png'))
    if legacy_plot:
        fig.savefig(output_dir/'renders/Back-Toolpath-Sections.png')
    plt.close(fig)
    print(json.dumps({k:v for k,v in report.items() if k!='layers'}),flush=True)
    assert not failures and not region_failures, 'Inspect missing back extrusion regions'
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--designs-file', type=Path,
                        default=Path(os.environ.get('BAROQUE_DESIGNS_FILE', ROOT/'source/designs-period-portrait-oval.json')))
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument('--id', help='One exact design ID from the design JSON; default is the first design')
    selection.add_argument('--all', action='store_true', help='Audit all designs in the design JSON')
    parser.add_argument('--build-dir', type=Path, default=P)
    parser.add_argument('--output-dir', type=Path, help='Alternate root for validation/ and renders/ outputs')
    parser.add_argument('--xy-offset', type=float, nargs=2, metavar=('X','Y'),
                        help='Explicit back placement on the print plate; default is geometry data or native [128,128]')
    args = parser.parse_args()
    designs = json.loads(args.designs_file.read_text())
    assert designs, 'Design list is empty'
    if args.id:
        designs = [d for d in designs if d['id'] == args.id]
        assert len(designs) == 1, f'Design ID not uniquely found: {args.id}'
    elif not args.all:
        designs = designs[:1]
    for d in designs:
        audit_design(d, args.build_dir, args.output_dir, args.xy_offset, legacy_plot=len(designs)==1)


if __name__ == '__main__':
    main()
