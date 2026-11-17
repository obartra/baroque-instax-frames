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
    return f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}" fill="{fill}">{label}</text>'


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
        return box(-30.4, -22.4, 30.4, 22.4)
    a, b, rise = 22.4, 30.4, 3.5
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
    art = f'<path d="{path(shape)}" fill="{INK}"/>'
    art += f'<path d="{path(mat.buffer(2.3))}" fill="none" stroke="#566068" stroke-width=".65"/>'
    art += f'<path d="{path(mat)}" fill="#fff"/>'
    art += f'<path d="{path(ap)}" fill="{TEAL if image else PAPER}"/>'
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
    return rect(0,0,755,height,'#fff', '#dddcd6', 24) + circle(55,58,26,ACTION,'none') + text(55,68,str(number),'step','middle','#fff') + text(102,68,title,'title') + text(40,112,subtitle,'small',fill=MUTED) + body


def canvas(name, title, left, right, height=760, description=''):
    defs = f'''<defs>
      <marker id="arrow" viewBox="0 0 12 12" refX="10" refY="6" markerWidth="9" markerHeight="9" orient="auto-start-reverse"><path d="M1,1L11,6L1,11Z" fill="{ACTION}"/></marker>
      <clipPath id="landscape-aperture"><path d="{path(aperture())}"/></clipPath>
      <clipPath id="portrait-aperture"><path d="{path(aperture(True))}"/></clipPath>
      <style>text{{font-family:Arial,Helvetica,sans-serif}}.heading{{font-size:35px;font-weight:700}}.title{{font-size:29px;font-weight:700}}.step{{font-size:30px;font-weight:700}}.label{{font-size:25px;font-weight:600}}.small{{font-size:22px}}.tiny{{font-size:19px}}</style>
    </defs>'''
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="{height}" viewBox="0 0 1600 {height}" role="img"><title>{title}</title><desc>{description}</desc>{defs}'
    svg += rect(0,0,1600,height,PAPER) + text(35,50,title,'heading')
    svg += f'<g transform="translate(30,80)">{left}</g><g transform="translate(815,80)">{right}</g>'
    svg += text(35,height-22,'CAD-based silhouettes · exploded details schematic · use each frame’s matching parts','tiny',fill=MUTED) + '</svg>'
    target = OUT / (name+'.svg')
    target.write_text(svg)
    subprocess.run(['rsvg-convert', str(target), '-o', str(target.with_suffix('.png'))], check=True)


def main():
    global FRONT, BACK, PORTRAIT, REPORT
    OUT.mkdir(parents=True, exist_ok=True)
    project = ROOT/'models'/'04-Floral-Corners-Instax-Mini-3-Magnets.3mf'
    portrait_project = ROOT/'models'/'02-Segmental-Arch-Instax-Mini-3-Magnets.3mf'
    REPORT = json.loads((ROOT/'validation'/'04-Floral-Corners-geometry.json').read_text())
    front_bottom = bottom_shape(project,2)
    FRONT = Polygon(front_bottom.exterior)
    BACK = bottom_shape(project,4)
    portrait_bottom = bottom_shape(portrait_project,2)
    PORTRAIT = Polygon(portrait_bottom.exterior)

    # 1: test the two coupon parts before committing to a full frame.
    body = text(215,176,'COUPON','label','middle')
    body += rect(140,205,150,72,'#fff',INK,8,3) + rect(182,232,66,48,'#fff',INK,4,3)
    body += rect(179,356,72,142,'#fff',INK,5,3) + rect(198,351,34,100,'#fff',INK,13,3)
    body += arrow(215,293,215,333)
    body += text(215,540,'Print both pieces','small','middle')
    body += rect(440,273,160,72,'#fff',INK,8,3) + rect(482,309,76,155,'#fff',INK,7,3)
    body += line(520,345,520,409,INK,3) + check(642,342)
    body += text(535,510,'Align · press evenly','small','middle')
    p1 = panel(1,'Test the snap fit','Print the small PLA coupon first.',body)

    # 2: two plates, two pieces; front is fused white and black.
    body = rect(47,166,328,257,'#edf0f0','#a5adb1',10) + rect(405,166,300,257,'#edf0f0','#a5adb1',10)
    body += front(212,291,2.35,image=False) + back(555,291,2.3,pegs=True)
    body += text(212,465,'PLATE 1 · FRONT','label','middle') + text(555,465,'PLATE 2 · BACK','label','middle')
    body += circle(88,513,13,'#fff',INK) + text(111,521,'1 White','small') + circle(238,513,13,INK,INK) + text(262,521,'2 Black','small')
    body += text(555,521,'1 White','small','middle')
    body += rect(80,552,232,19,INK) + rect(80,571,232,5,'#fff',INK,0,1)
    body += text(332,577,'0.36 mm white mat','tiny')
    body += text(40,606,'One fused front + its matching back','small')
    p2 = panel(2,'Print two plates','Open the 3MF as a project; keep its color assignments.',body)
    canvas('01-print','PRINT · 2 plates / 2 pieces',p1,p2,760,
           '1 Print both snap coupon pieces and test alignment. 2 Print the fused white and black front on plate one and the matching white back on plate two. The white mat is 0.36 millimeters thick.')

    # 3: rear face of back, adhesive in three pockets, then cure.
    body = back(385,365,3.0,rear=True)
    # Glue bottle and three separate cylindrical magnet symbols.
    body += rect(65,155,62,77,'#fff',INK,8,3) + rect(83,132,26,27,'#fff',INK,3,3)
    body += text(96,199,'GLUE','tiny','middle')
    body += arrow(139,199,355,263)
    for x in (490,555,620):
        body += rect(x-20,165,40,21,'#a9b7be',INK,5,2) + f'<ellipse cx="{x}" cy="165" rx="20" ry="8" fill="#e4edf1" stroke="{INK}" stroke-width="2"/>'
    body += text(555,212,'3 × Ø6 × 3 mm','small','middle')
    body += text(385,515,'MAGNET / REAR SIDE','label','middle')
    body += circle(95,565,23,'#fff',INK,2) + line(95,565,95,549,INK,2) + line(95,565,108,572,INK,2)
    body += text(135,573,'Seat flush · let the glue cure','small')
    p3 = panel(3,'Glue three magnets','Keep glue out of the photo channel and snaps.',body)

    # 4: exploded SIDE section. Front decoration points into the soft cloth.
    body = text(70,178,'BACK · forks down','small')
    body += rect(95,218,445,20,'#fff',INK,4,3)
    for x in (155,445):
        body += rect(x-11,238,22,58,'#fff',INK,2,2) + rect(x-3,255,6,41,'#fff',INK,2,1.5)
        body += arrow(x,309,x,355)
    body += rect(105,393,425,43,INK,INK,9)
    for x in (155,445):
        body += rect(x-15,391,30,25,'#fff','none')
    body += '<path d="M88,445 Q116,430 144,446T200,446T256,446T312,446T368,446T424,446T480,446T536,446L550,468H88Z" fill="#e3e0d7" stroke="#9c9c94" stroke-width="2"/>'
    body += text(102,500,'FRONT · ornament down on a soft cloth','small')
    body += text(102,545,'Align all 4 forks, then press at each corner.','small')
    body += text(618,175,'DETAIL','tiny','middle')
    # Magnified one-fork section, visually connected to the exploded view.
    body += rect(588,218,72,22,'#fff',INK,3,2) + rect(604,240,40,67,'#fff',INK,3,2)
    body += rect(617,254,14,53,'#fff',INK,6,1.5)
    body += arrow(624,324,624,361)
    body += rect(578,394,92,53,INK,INK,4,2) + rect(600,392,48,32,'#fff','none')
    body += text(621,480,'4 ×','label','middle')
    p4 = panel(4,'Snap the empty frame together','The photo goes in after the front and back are joined.',body)
    canvas('02-assemble','ASSEMBLE · glue, cure, then snap',p3,p4,760,
           '3 Glue three six by three millimeter magnets into the rear pockets, seat their exposed faces flush and let the adhesive cure. 4 Put the front ornament face down on a soft cloth, align all four downward-pointing back forks and press at each corner. Do not put the photo between separated parts.')

    # 5: correct real film direction in both orientations.
    body = front(557,249,1.65) + film(121,203,1.65)
    body += arrow(285,249,435,249)
    body += text(116,344,'LANDSCAPE · from the left','small')
    body += text(116,375,'Wide border trails at the left','tiny',fill=MUTED)
    body += front(544,491,1.45,portrait=True) + film(505,648,1.45,portrait=True)
    body += arrow(544,636,544,591)
    body += text(80,535,'PORTRAIT','small') + text(80,567,'from the bottom ↑','small')
    body += text(80,603,'Wide border trails below','tiny',fill=MUTED)
    body += circle(91,694,29,'#fff','#a34e3e',3)
    body += circle(80,698,6,'none',INK,2) + circle(95,708,6,'none',INK,2)
    body += line(82,693,105,675,INK,2) + line(96,702,101,675,INK,2)
    body += line(72,675,110,713,'#a34e3e',4)
    body += text(138,703,'Keep the whole 86 × 54 mm sheet','small')
    p5 = panel(5,'Slide in the uncut photo','Try a paper dummy first. Narrow edge enters first.',body,820)

    # 6: no exposed magnets, mounted decorative face outward.
    body = rect(204,175,350,520,'#f1f2ef',INK,24,3)
    body += line(204,318,554,318,'#929b9f',3)
    body += rect(514,235,9,61,'#a9b0b1',INK,3,1) + rect(514,342,9,100,'#a9b0b1',INK,3,1)
    body += front(375,449,2.0) + check(612,455)
    body += text(375,745,'Magnets face the fridge','label','middle')
    body += text(375,782,'Gently slide the photo out to change it.','small','middle')
    p6 = panel(6,'Place on the fridge','The magnets and photo border stay behind the frame.',body,820)
    canvas('03-load-and-display','LOAD · narrow edge first / no trimming',p5,p6,960,
           '5 Slide a whole uncut Instax Mini sheet into the already assembled frame, narrow border first. Enter from the left for a landscape frame, with the wide caption border trailing on the left. Enter from the bottom for a portrait frame, with the wide caption border trailing below. Do not cut the instant film. 6 Place the frame on the fridge, magnet side toward the fridge.')

    sources = {
        'generator': 'source/make_assembly_instructions.py',
        'source_projects': [
            {'path': str(p.relative_to(ROOT)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
            for p in (project,portrait_project)],
        'geometry': 'Flat underside silhouettes extracted from native 3MF mesh triangles; simplified by 0.10 mm for illustration only.',
        'schematic_details': 'Exploded fork/socket section, tools, plate icons and photograph placeholders are illustrative, not manufacturing drawings.',
        'sequence': ['coupon','print matching two plates','glue three magnets and cure','snap empty frame','slide full uncut film into assembled channel','mount on fridge'],
        'film_mm':[86,54], 'mat_height_mm':.36,
        'magnet_mm':[6,3], 'magnet_count':3,
        'landscape_insertion':'left, narrow border first, caption border trailing left',
        'portrait_insertion':'bottom, narrow border first, caption border trailing bottom',
    }
    (OUT/'sources.json').write_text(json.dumps(sources,indent=2)+'\n')
    print(f'Wrote three SVG diagrams and PNG previews to {OUT}')


if __name__ == '__main__':
    main()
