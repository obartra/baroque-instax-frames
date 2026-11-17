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
        rows.append(f'| [<img src="{angle}" width="200" alt="{r["name"]} angled view">]({angle}) | **{r["name"]}**<br>{r["orientation"].title()} · {w:.1f} × {h:.1f} mm<br>**[Download 3MF]({r["model"]})** · [STL ZIP]({r["stl"]["archive"]}) | [Front]({front}) · [Angled]({angle})<br>[Back]({back}) · [Photo fit]({fit}) |')
    table='\n'.join(rows)
    text=f'''# Floral Instax Frames

<p align="center">
  <img src="assets/brand/project-icon.png" width="240" alt="Segmental Arch frame, rendered from its actual mesh with a simulated coastal photo">
  <br><sub>Segmental Arch · actual frame mesh, simulated photo</sub>
</p>

Eight floral frames for **whole, [uncut Instax Mini photos](https://www.instaxus.com/film/mini-white-film/)**. Print a front and
matching back, slide in your photo, and display it on a magnetic surface.
Each frame holds **[three Ø6 × 3 mm magnets](https://www.amazon.com/s?k=6x3mm+neodymium+disc+magnets)**.

**[Explore the collection on the website →](https://obartra.github.io/baroque-instax-frames/)**

[Frames](#choose-a-frame) · [Assembly](#print-and-assemble) · [Photo fit](#how-the-whole-photo-fits) · [Print setup](#before-you-print) · [Source & license](#design-source-and-license)

![All eight current frames, rendered from their actual printable meshes at the same scale](renders/Eight-frames-current.png)

[Download on Printables](https://www.printables.com/model/1920140-rococo-instax-mini-magnetic-frames-8-designs) · [Read the design story](https://github.com/obartra/notes/tree/master/baroqueInstaxFrames)

<a name="choose-a-frame"></a>

## 🖼️ Choose a frame

Each **3MF includes both matching parts on two plates**. Open it as a project
in Bambu Studio to retain the assembly and material assignments. The previews
use example materials; the model dimensions and geometry are the actual files.
The previews show each frame upright, viewed from the side in perspective to show the
carving and depth. Click to enlarge, or use the view links for straight-on, rear
and photo-fit views.

For other slicers, download the **STL ZIP**: ornament, mat and matching back.
Keep the mat and ornament aligned as one front, and choose your own print
settings. [STL import and color-change guide](docs/PRINTING.md#using-the-stl-downloads).

| Preview | Design & files | More views |
| --- | --- | --- |
{table}

The Botanical Garland includes the latest sculpted petal and flower-center
revision. Its preceding matching three-magnet back remains compatible.
Always keep each of the other designs with its own matching back.

<a name="print-and-assemble"></a>

## 🧩 Print and assemble

You need filament, **[three Ø6 × 3 mm magnets](https://www.amazon.com/s?k=6x3mm+neodymium+disc+magnets)**, and suitable glue.
Use one filament for the whole frame, or choose separate mat and frame colors.
The back prints separately. The reinforced inner mat is **0.68 mm thick**—seven layers at the supplied settings.

![Steps 1–2: print the matching front and back on two plates, then glue three magnets into the rear pockets and let cure.](docs/assembly/01-print-and-magnets-v3.png)

![Steps 3–4: snap the empty frame together, glue joints if needed, then slide in the full photo, narrow border first.](docs/assembly/02-snap-and-load-v3.png)

![Step 5: place on a magnet-attracting surface. The frame is shown at realistic relative size on the fridge; a separate enlarged detail shows it clearly.](docs/assembly/03-magnetic-display-v3.png)

Landscape photos enter from the **left**; portrait photos enter from the
**bottom**. The wide caption border trails behind. Keep the instant film whole.
The joints only need to engage once and may be glued after seating; let adhesive
cure before loading the photo. [Print settings and assembly details](docs/PRINTING.md)
· [Editable diagrams](docs/assembly/README.md).

<a name="how-the-whole-photo-fits"></a>

## 📷 How the whole photo fits

The whole **86 × 54 mm sheet** and back are concealed **when viewed from the
front**; the carrier can be visible at shallow angles. The opening deliberately
masks a little of the image; the ovals mask more.

These **rear views** show the retaining supports, three magnets and full sheet.
The dashed outline follows the uncut film beneath the retaining edges; arrows
show how it slides in. Viewed from behind, landscape entry appears on the
**right** (the left when seen from the front); portrait entry stays below.

![Rear views of all eight frames, showing the full uncut sheet, retaining carrier, three magnets and photo insertion direction](renders/Eight-frames-rear-film-fit.png)

These fit **Instax Mini**, rather than Polaroid Go, full-size Polaroid, Instax
Square or Instax Wide. [Dimensions, crop percentages and checks](catalog/current.json).

<a name="before-you-print"></a>

## 🖨️ Before you print

| Check | Included setting / what you need |
| --- | --- |
| **Printer settings** | **3MF:** supplied Bambu P2S · 0.4 mm profile. **STL:** use your own printer, nozzle and filament profiles |
| **Filament** | Up to two colors: one for the mat, one for the frame and back |
| **Layer height** | Supplied 3MF: 0.20 mm first layer, then 0.08 mm |
| **Reinforced mat** | 0.68 mm · seven layers with the supplied settings |
| **Magnets** | Three discs per frame: **[6 mm diameter × 3 mm thick](https://www.amazon.com/s?k=6x3mm+neodymium+disc+magnets)** |

**Open as a project** to keep the matching parts, plates and material assignments.
Use profiles for your printer and filament before slicing. For a single-color
front, assign the mat and ornament to the same filament.

**Two-color STL front:** assign filaments to the aligned mat and ornament parts,
or use a manual swap. With the supplied layer heights, finish **layer 7 at
0.68 mm**, then change filament **before layer 8 at 0.76 mm**. Different layer
heights need a different layer number; check the first ornament layer in the
preview. [Color-change instructions](docs/PRINTING.md#changing-colors-with-stls).

**Let the plate cool**, then flex it away from the frame. Avoid pulling on the
inner mat or projecting flowers.

<a name="design-source-and-license"></a>

## 🌿 Design, source and license

**French floral Rococo, made miniature.** New compositions informed by Louis XV
frames, approximately **1735–1750**, adapted to supported printable relief and
whole Instax Mini sheets. [Historical references & design notes](docs/CURRENT-CATALOG.md#historical-basis).

**Make them yours:** use, modify, share, and sell your prints.

| What | License |
| --- | --- |
| **Models, renders & documentation** | [CC0-1.0](LICENSES/CC0-1.0.txt) |
| **Code** | [MIT](LICENSES/MIT.txt) |

CC0 applies to the rights we can waive. [License scope & third-party materials](LICENSING.md).

<details>
<summary>🛠️ Explore the source and earlier releases</summary>

- [Current CAD inputs](source/designs-current.json)
- [Build and review notes](docs/CURRENT-CATALOG.md)
- [Geometry and slicer records](validation/current/)
- [Rebuild the frames](docs/CURRENT-CATALOG.md#rebuild)
- [Creation and provenance record](PROVENANCE.txt)
- [Project icon & simulated photo](assets/brand/README.md)

The earlier six-frame release remains in the repository history and original
model paths. The table above links to the current eight prototypes.

</details>

Catalog views use a drawn photo placeholder; the project icon uses an AI-simulated
photo. Share your own print photos with a [permission record](photos/README.md).
'''
    (ROOT/'README.md').write_text(text)
    print('Wrote eight-frame visual README',flush=True)


if __name__=='__main__':main()
