# SPDX-License-Identifier: MIT
"""Generate editable, CAD-outline-based assembly diagrams and PNG previews.

Run with the project's CAD Python environment. Uses released 3MF geometry,
not an AI image or a private build directory. Exploded sections are schematic.
"""
from pathlib import Path
from zipfile import ZipFile
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

import numpy as np
from shapely.geometry import Polygon, box
from shapely import union_all

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'assembly'
NS = '{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}'
INK = '#24282b'
MUTED = '#5a6368'
ACTION = '#b96329'
TEAL = '#538997'
PAPER = '#f5f3ed'
GOLD = '#ba8832'
PANEL = '#e7edf2'
PLATE = '#c7d2dc'
APERTURE_HALF = (30.4,22.4)


def path(poly):
    def loop(coords):
        return 'M' + 'L'.join(f'{x:.3f},{y:.3f}' for x, y in list(coords)[:-1]) + 'Z'
    if poly.geom_type == 'MultiPolygon':
        return ''.join(path(p) for p in poly.geoms)
    return loop(poly.exterior.coords) + ''.join(loop(r.coords) for r in poly.interiors)


def bottom_shape(project, object_id):
    """Project horizontal underside faces, preserving the real carrier opening."""
    with ZipFile(project) as z:
        model = ET.fromstring(z.read(f'3D/Objects/object_{object_id}.model'))
    vv = np.array([[float(e.get(k)) for k in ('x', 'y', 'z')]
                   for e in model.iter(NS + 'vertex')])
    ff = np.array([[int(e.get(k)) for k in ('v1', 'v2', 'v3')]
                   for e in model.iter(NS + 'triangle')])
    tri = vv[ff]
    flat = tri[np.max(np.abs(tri[:, :, 2] - vv[:, 2].min()), axis=1) < 1e-4]
    shape = union_all([Polygon(t[:, :2]) for t in flat]).buffer(0)
    # Polygon simplification affects only illustration edges, never the models.
    return shape.simplify(.10, preserve_topology=True)


def text(x, y, label, cls='label', anchor='start', fill=INK):
    return f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}" fill="{fill}">{escape(str(label))}</text>'


def line(x1, y1, x2, y2, color=INK, width=3, dash=''):
    return f'<path d="M{x1},{y1}L{x2},{y2}" fill="none" stroke="{color}" stroke-width="{width}" stroke-dasharray="{dash}"/>'


def arrow(x1, y1, x2, y2):
    return f'<path d="M{x1},{y1}L{x2},{y2}" fill="none" stroke="{ACTION}" stroke-width="5" marker-end="url(#arrow)"/>'


def circle(x, y, r, fill, stroke=INK, width=2):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>'


def rect(x, y, w, h, fill, stroke='none', radius=0, width=2):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>'


def check(x, y):
    return f'<path d="M{x-14},{y}l10,12l25,-30" stroke="#417159" stroke-width="7" stroke-linecap="round" fill="none"/>'


def aperture(portrait=False):
    if not portrait:
        a,b=APERTURE_HALF
        return box(-a,-b,a,b)
    b,a=APERTURE_HALF
    rise=3.5
    radius = (a*a + rise*rise)/(2*rise)
    yc = b-radius
    xs = np.linspace(a, -a, 128)
    return Polygon([(-a, -b), (a, -b), (a, b-rise)] +
                   [(x, yc + np.sqrt(radius*radius-x*x)) for x in xs] + [(-a, b-rise)])


def scene_photo(x, y, w, h):
    return rect(x, y, w, h, '#8ab6c4') + f'<path d="M{x},{y+h}V{y+h*.65}L{x+w*.30},{y+h*.30}L{x+w*.53},{y+h*.72}L{x+w*.72},{y+h*.50}L{x+w},{y+h*.82}V{y+h}Z" fill="#4d7465"/>' + circle(x+w*.80, y+h*.25, min(w,h)*.095, '#e6bd70', 'none')


def front(cx, cy, scale, portrait=False, image=True):
    ap = aperture(portrait)
    mat = ap.buffer(6.5)
    shape = PORTRAIT if portrait else FRONT
    art = f'<path d="{path(shape)}" fill="{GOLD}" stroke="#795b26" stroke-width=".3"/>'
    art += f'<path d="{path(mat.buffer(2.3))}" fill="none" stroke="#795b26" stroke-width=".65"/>'
    art += f'<path d="{path(mat)}" fill="#fff" stroke="#59646e" stroke-width=".3"/>'
    art += f'<path d="{path(ap)}" fill="{TEAL if image else PLATE}"/>'
    # Keep photo placeholders inside the real aperture, including the arch.
    if image:
        clip = 'portrait-aperture' if portrait else 'landscape-aperture'
        px, py, pw, ph = (-23, -31, 46, 62) if portrait else (-31, -23, 62, 46)
        art += f'<g clip-path="url(#{clip})"><g transform="scale(1,-1)">' + scene_photo(px, py, pw, ph) + '</g></g>'
    return f'<g transform="translate({cx},{cy}) scale({scale},{-scale})">{art}</g>'


def back(cx, cy, scale, rear=False, pegs=False):
    sx = -scale if rear else scale
    body = f'<path d="{path(BACK)}" fill="#fff" stroke="#778087" stroke-width=".55" fill-rule="evenodd"/>'
    for x, y in REPORT['magnet_centers_mm']:
        body += circle(x, y, 3.15, '#9daab0' if rear else '#e4e7e7', '#778087', .45)
        if rear:
            body += line(x-1.8, y+1.5, x+1.8, y+1.5, '#e7eff1', .45)
    if pegs:
        for x, y in REPORT['snap_positions_mm']:
            body += rect(x-1.9, y-1, 3.8, 2, '#fff', '#566068', .35, .4)
            body += line(x, y-1, x, y+1, '#566068', .35)
    return f'<g transform="translate({cx},{cy}) scale({sx},{-scale})">{body}</g>'


def film(x, y, scale, portrait=False):
    # The wide caption border trails: landscape left, portrait bottom.
    w, h = (54,86) if portrait else (86,54)
    out = rect(x, y, w*scale, h*scale, '#fff', '#70797e', 1, 2)
    if portrait:
        out += rect(x+2*scale, y+66*scale, 50*scale, 18*scale, '#fbebce')
        out += scene_photo(x+4*scale, y+4*scale, 46*scale, 62*scale)
    else:
        out += rect(x+2*scale, y+2*scale, 18*scale, 50*scale, '#fbebce')
        out += scene_photo(x+20*scale, y+4*scale, 62*scale, 46*scale)
    return out


def panel(number, title, subtitle, body, height=620):
    return rect(0,0,755,height,PANEL, '#c6cfd6', 24) + circle(55,58,26,ACTION,'none') + text(55,68,str(number),'step','middle','#fff') + text(102,68,title,'title') + text(40,112,subtitle,'small',fill=MUTED) + body


def canvas(name, title, left, right, height=760, description=''):
    defs = f'''<defs>
      <marker id="arrow" viewBox="0 0 12 12" refX="10" refY="6" markerWidth="9" markerHeight="9" orient="auto-start-reverse"><path d="M1,1L11,6L1,11Z" fill="{ACTION}"/></marker>
      <clipPath id="landscape-aperture"><path d="{path(aperture())}"/></clipPath>
      <clipPath id="portrait-aperture"><path d="{path(aperture(True))}"/></clipPath>
      <style>text{{font-family:Arial,Helvetica,sans-serif}}.heading{{font-size:35px;font-weight:700}}.title{{font-size:29px;font-weight:700}}.step{{font-size:30px;font-weight:700}}.label{{font-size:25px;font-weight:600}}.small{{font-size:22px}}.tiny{{font-size:19px}}</style>
    </defs>'''
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="{height}" viewBox="0 0 1600 {height}" role="img"><title>{escape(title)}</title><desc>{escape(description)}</desc>{defs}'
    svg += rect(0,0,1600,height,PAPER) + text(35,50,title,'heading')
    svg += f'<g transform="translate(30,80)">{left}</g><g transform="translate(815,80)">{right}</g>'
    svg += text(35,height-22,'CAD-based silhouettes · exploded details schematic · use each frame’s matching parts','tiny',fill=MUTED) + '</svg>'
    target = OUT / (name+'.svg')
    target.write_text(svg)
    subprocess.run(['rsvg-convert', str(target), '-o', str(target.with_suffix('.png'))], check=True)


def main():
    import sys
    from assembly_steps import draw
    catalog=ROOT/'catalog/current.json'
    if catalog.is_file():
        frames=json.loads(catalog.read_text())['frames']
        landscape=next(r for r in frames if r['slug']=='floral-corners')
        portrait=next(r for r in frames if r['slug']=='segmental-arch')
        args=(ROOT/landscape['model'],ROOT/portrait['model'],ROOT/landscape['geometry'])
    else:
        args=(ROOT/'models/04-Floral-Corners-Instax-Mini-3-Magnets.3mf',
              ROOT/'models/02-Segmental-Arch-Instax-Mini-3-Magnets.3mf',
              ROOT/'validation/04-Floral-Corners-geometry.json')
    draw(sys.modules[__name__],*args,OUT)


if __name__ == '__main__':main()
