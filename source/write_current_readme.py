# SPDX-License-Identifier: MIT
"""Build the public visual catalog from the same checked model manifest."""
import json
from paths import ROOT


def main():
    c=json.loads((ROOT/'catalog/current.json').read_text())
    rows=[]
    for r in c['frames']:
        front,angle,back,fit=[r['views'][v] for v in ('front','angle','back','fit')]
        w,h=r['dimensions_mm'][:2]
        rows.append(f'| [<img src="{angle}" width="200" alt="{r["name"]} angled view">]({angle}) | **{r["name"]}**<br>{r["orientation"].title()} · {w:.1f} × {h:.1f} mm<br>**[Download 3MF]({r["model"]})** | [Front]({front}) · [Angled]({angle})<br>[Back]({back}) · [Photo fit]({fit}) |')
    table='\n'.join(rows)
    text=f'''# Floral Instax Frames

Eight floral frames for **whole, uncut Instax Mini photos**. Print a front and
matching back, slide in your photo, and display it on a magnetic surface.
Each frame holds **three Ø6 × 3 mm magnets**. Choose your own print colors.

![All eight current frames, rendered from their actual printable meshes at the same scale](renders/Eight-frames-current.png)

## Choose a frame

Each **3MF includes both matching parts on two plates**. Open it as a project
in Bambu Studio to retain the assembly and material assignments. The previews
use example materials; the model dimensions and geometry are the actual files.
The angled previews show the carving and depth. Click to enlarge, or use the
view links for straight-on, rear and photo-fit views.

| Preview | Design & files | More views |
| --- | --- | --- |
{table}

The Botanical Garland includes the latest sculpted petal and flower-center
revision. Its preceding matching three-magnet back remains compatible.
Always keep each of the other designs with its own matching back.

## Print and assemble

You need PLA, two contrasting materials for the front, a multicolor-capable
setup, **three Ø6 × 3 mm magnets**, and suitable glue. The back prints separately,
so its material is your choice. The inner mat is only **0.36 mm thick**.

![Steps 1–2: print the matching front and back on two plates, then glue three magnets into the rear pockets and let cure.](docs/assembly/01-print-and-magnets-v2.png)

![Steps 3–4: snap the empty frame together, glue joints if needed, then slide in the full photo, narrow border first.](docs/assembly/02-snap-and-load-v2.png)

![Step 5: place on a magnet-attracting surface. The frame is shown at realistic relative size on the fridge; a separate enlarged detail shows it clearly.](docs/assembly/03-magnetic-display-v2.png)

Landscape photos enter from the **left**; portrait photos enter from the
**bottom**. The wide caption border trails behind. Keep the instant film whole.
The joints only need to engage once and may be glued after seating; let adhesive
cure before loading the photo. [Print settings and assembly details](docs/PRINTING.md)
· [Editable diagrams](docs/assembly/README.md).

## How the whole photo fits

The whole **86 × 54 mm sheet** and back are concealed **when viewed from the
front**; the carrier can be visible at shallow angles. The opening deliberately
masks a little of the image; the ovals mask
more. In the diagram below, the dashed outline traces the hidden sheet and
the circles mark the three magnets behind the frame.

![All eight latest complete frame meshes, with the full uncut film footprint and hidden magnet positions overlaid](renders/Eight-frames-film-fit.png)

These fit **Instax Mini**, rather than Polaroid Go, full-size Polaroid, Instax
Square or Instax Wide. [Dimensions, crop percentages and checks](catalog/current.json).

## Before you print

The supplied projects were checked and sliced for **Bambu P2S, 0.4 mm nozzle,
PLA and textured PEI**, using a 0.20 mm first layer and 0.08 mm following layers.
Reslice for your printer and assign your actual materials. No print is started
by opening these files.

These are **prototypes**. Digital checks cover closed meshes, four clip/socket
engagements, photo clearance, front-view concealment and three magnet pockets. All back
layers have extrusion-path checks. Physical fit, adhesive hold and fine surface
detail still need testing. [Current build and review notes](docs/CURRENT-CATALOG.md)
· [Geometry and slicer records](validation/current/).

## Design, source and license

Modern miniatures informed by French Louis XV floral Rococo, approximately
1735–1750. They use supported printable relief rather than full carved undercuts
and are new compositions, rather than replicas of documented antique frames.
[Historical sources and design limits](docs/CURRENT-CATALOG.md#historical-basis).

**Models, renders and documentation: CC0-1.0**, to the extent rights exist.
**Code: MIT.** Use, modify, share and sell your prints.
[License scope](LICENSING.md) · [Current CAD inputs](source/designs-current.json)
· [Rebuild instructions](docs/CURRENT-CATALOG.md#rebuild).

The earlier six-frame release remains available in the repository history and
original model paths. The table above links to the current eight prototypes.
Renders use a drawn photo placeholder; contributed print photos can be added
with their [permission record](photos/README.md).
'''
    (ROOT/'README.md').write_text(text)
    print('Wrote eight-frame visual README',flush=True)


if __name__=='__main__':main()
