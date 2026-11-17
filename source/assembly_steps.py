# SPDX-License-Identifier: MIT
"""Shared five-step illustration layout. Colors are demonstrative, never labels."""
import hashlib
import json
from shapely.geometry import Polygon


def draw(g, project, portrait_project, report, out):
    g.OUT=out;out.mkdir(parents=True,exist_ok=True)
    g.REPORT=json.loads(report.read_text())
    a=g.REPORT['aperture_bounds_mm']
    g.APERTURE_HALF=((a[2]-a[0])/2,(a[3]-a[1])/2)
    g.FRONT=Polygon(g.bottom_shape(project,2).exterior)
    g.BACK=g.bottom_shape(project,4)
    g.PORTRAIT=Polygon(g.bottom_shape(portrait_project,2).exterior)

    # 1: two plates, two pieces. Illustration colors have no prescribed meaning.
    body=g.rect(38,166,325,257,g.PLATE,'#7d8b96',10)+g.rect(393,166,325,257,g.PLATE,'#7d8b96',10)
    body+=g.front(200,291,2.24,image=False)+g.back(555,291,2.3,pegs=True)
    body+=g.text(200,465,'PLATE 1 · FRONT','label','middle')+g.text(555,465,'PLATE 2 · BACK','label','middle')
    body+=g.rect(85,518,235,21,g.GOLD,g.INK)+g.rect(85,539,235,6,'#fff',g.INK,0,1)
    mat_height=g.REPORT['mat_height_mm']
    body+=g.text(200,581,f'{mat_height:.2f} mm inner mat','small','middle')
    body+=g.text(555,534,'Matching back','small','middle')
    body+=g.text(555,575,'Two pieces in total','small','middle')
    p1=g.panel(1,'Print two plates','One multicolor front + its matching back.',body)

    # 2: magnets and adhesive, no preliminary coupon/fit-test stage.
    body=g.back(385,365,3.0,rear=True)
    body+=g.rect(65,155,62,77,'#fff',g.INK,8,3)+g.rect(83,132,26,27,'#fff',g.INK,3,3)
    body+=g.text(96,199,'GLUE','tiny','middle')+g.arrow(139,199,355,263)
    for x in (490,555,620):
        body+=g.rect(x-20,165,40,21,'#8597a2',g.INK,5,2)
        body+=f'<ellipse cx="{x}" cy="165" rx="20" ry="8" fill="#c9d6df" stroke="{g.INK}" stroke-width="2"/>'
    body+=g.text(555,212,'3 × Ø6 × 3 mm','small','middle')
    body+=g.text(385,515,'REAR SIDE','label','middle')
    body+=g.circle(95,565,23,'#fff',g.INK,2)+g.line(95,565,95,549,g.INK,2)+g.line(95,565,108,572,g.INK,2)
    body+=g.text(135,573,'Seat flush · let the glue cure','small')
    p2=g.panel(2,'Glue three magnets','Keep the photo channel clear.',body)
    g.canvas('01-print','PRINT & PREPARE · two pieces',p1,p2,760,
        '1 Print the multicolor front on one plate and its matching back on the other. 2 Glue three six by three millimeter magnets into the rear pockets, seat flush and let the adhesive cure.')

    # 3: supported empty-frame assembly; a permanent glued joint is permitted.
    body=g.text(70,178,'BACK · forks down','small')
    body+=g.rect(95,218,445,20,'#fff',g.INK,4,3)
    for x in (155,445):
        body+=g.rect(x-11,238,22,58,'#fff',g.INK,2,2)+g.rect(x-3,255,6,41,'#fff',g.INK,2,1.5)
        body+=g.arrow(x,309,x,355)
    body+=g.rect(105,393,425,43,g.GOLD,g.INK,9)
    for x in (155,445):body+=g.rect(x-15,391,30,25,g.PANEL,'none')
    body+='<path d="M88,445 Q116,430 144,446T200,446T256,446T312,446T368,446T424,446T480,446T536,446L550,468H88Z" fill="#c8d1d8" stroke="#82909b" stroke-width="2"/>'
    body+=g.text(102,500,'FRONT · ornament down on a soft cloth','small')
    body+=g.text(70,553,'Align all 4 forks; press near each joint.','small')
    body+=g.text(70,590,'Glue joints if needed; let cure before loading.','tiny')
    body+=g.text(618,175,'DETAIL','tiny','middle')
    body+=g.rect(588,218,72,22,'#fff',g.INK,3,2)+g.rect(604,240,40,67,'#fff',g.INK,3,2)
    body+=g.rect(617,254,14,53,g.PANEL,g.INK,6,1.5)+g.arrow(624,324,624,361)
    body+=g.rect(578,394,92,53,g.GOLD,g.INK,4,2)+g.rect(600,392,48,32,g.PANEL,'none')
    body+=g.text(621,480,'4 ×','label','middle')
    p3=g.panel(3,'Snap the empty frame together','Join the front and back before loading the photo.',body,820)

    # 4: full uncut film enters the already closed assembly, in either orientation.
    body=g.front(557,249,1.65)+g.film(121,203,1.65)+g.arrow(285,249,435,249)
    body+=g.text(116,344,'LANDSCAPE · from the left','small')
    body+=g.text(116,375,'Wide border trails at the left','tiny',fill=g.MUTED)
    body+=g.front(544,491,1.45,portrait=True)+g.film(505,648,1.45,portrait=True)
    body+=g.arrow(544,636,544,591)
    body+=g.text(80,535,'PORTRAIT','small')+g.text(80,567,'from the bottom ↑','small')
    body+=g.text(80,603,'Wide border trails below','tiny',fill=g.MUTED)
    body+=g.circle(91,694,29,'#fff','#a34e3e',3)
    body+=g.circle(80,698,6,'none',g.INK,2)+g.circle(95,708,6,'none',g.INK,2)
    body+=g.line(82,693,105,675,g.INK,2)+g.line(96,702,101,675,g.INK,2)
    body+=g.line(72,675,110,713,'#a34e3e',4)
    body+=g.text(138,703,'Keep the whole 86 × 54 mm sheet','small')
    p4=g.panel(4,'Slide in the uncut photo','Narrow border first, gently to the firm stop.',body,820)
    g.canvas('02-assemble','ASSEMBLE & LOAD · no trimming',p3,p4,960,
        '3 Snap the empty front and back together, supporting each of the four joints. Glue the joints if needed and let cure. 4 Slide the whole uncut Instax Mini sheet in from the left for landscape or the bottom for portrait. The wide caption border trails behind.')

    # 5: context is calibrated to a representative 600×1700 mm appliance.
    # The separate enlarged detail never pretends to share the context scale.
    sc=.335;fx,fy,fw,fh=190,160,600*sc,1700*sc
    body=g.rect(fx,fy,fw,fh,'#f6f8f9',g.INK,18,3)
    body+=g.line(fx,fy+165,fx+fw,fy+165,'#8b989f',2)
    body+=g.rect(fx+fw-23,fy+67,5,65,'#8e9ba3',g.INK,2,1)
    body+=g.rect(fx+fw-23,fy+193,5,104,'#8e9ba3',g.INK,2,1)
    cx,cy=fx+fw*.44,fy+fh*.50
    body+=g.front(cx,cy,sc)
    body+=g.text(fx+fw/2,780,'Shown at realistic relative size','small','middle')
    body+=g.rect(cx-25,cy-22,50,44,'none',g.ACTION,4,2)
    body+=g.line(cx+25,cy-22,825,275,g.ACTION,2,'7 7')
    body+=g.line(cx+25,cy+22,825,555,g.ACTION,2,'7 7')
    body+=g.rect(825,215,540,425,'#c8d3dc','#788994',18,2)
    body+=g.front(1095,425,3.05)
    body+=g.text(1095,175,'ENLARGED DETAIL','label','middle')
    body+=g.check(1413,429)
    body+=g.text(1095,703,'Magnet side against the surface','label','middle')
    body+=g.text(1095,746,'Slide the photo out through the same entry side.','small','middle')
    wide=g.rect(0,0,1540,820,g.PANEL,'#c6cfd6',24)+g.circle(55,58,26,g.ACTION,'none')
    wide+=g.text(55,68,'5','step','middle','#fff')+g.text(102,68,'Place on a magnetic surface','title')
    wide+=g.text(40,112,'A fridge, locker, board, or another surface that attracts magnets.','small',fill=g.MUTED)+body
    g.canvas('03-load-and-display','DISPLAY · any magnet-attracting surface',wide,'',960,
        '5 Place the magnet side against a surface that attracts magnets. The refrigerator context uses the actual frame footprint at the same scale as a representative six hundred by seventeen hundred millimeter appliance. A separate labeled enlarged detail shows the mounted frame clearly.')

    record=dict(generator='source/make_assembly_instructions.py + source/assembly_steps.py',
        source_projects=[dict(path=str(p.relative_to(g.ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in (project,portrait_project)],
        geometry='Actual native 3MF underside silhouettes, simplified by 0.10mm for illustration only; mechanics unchanged.',
        sequence=['print matching two plates','glue three magnets and cure','snap empty frame; glue joints if needed','slide in full uncut photo','place on a magnet-attracting surface'],
        film_mm=[86,54],mat_height_mm=mat_height,magnet_mm=[6,3],magnet_count=3,
        illustration_colors_are_examples=True,color_names_in_labels=False,
        context_reference_mm=[600,1700],context_pixels_per_mm=sc,
        context_frame_width_px=(g.FRONT.bounds[2]-g.FRONT.bounds[0])*sc,
        context_appliance_width_px=fw,detail_enlarged_and_labeled=True,
        landscape_insertion='left, narrow border first, caption border trailing left',
        portrait_insertion='bottom, narrow border first, caption border trailing below')
    (out/'sources.json').write_text(json.dumps(record,indent=2)+'\n')
    print('Wrote five steps across three SVG/PNG sheets:',out,flush=True)
