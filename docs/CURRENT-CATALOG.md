# Current eight-frame catalog

The [visual catalog](../README.md#choose-a-frame) links to the current native
projects in [models/current/](../models/current/). Each has its own matching front
and back on two plates. The original six files at the top level of `models/`
remain the earlier release; their integrity records are unchanged.

The current set comprises Canted Octagon, Segmental Arch, Cushion Cartouche,
Floral Corners, Botanical Garland, Acanthus Gallery, Portrait Oval and Landscape
Oval. Botanical Garland uses the latest explicit sculpted-petal v3 revision.
The mat reinforcement preserves each design's preceding matching back geometry.
Keep fronts and backs paired by design.

## Fit and manufacturing

Every design accepts a full uncut 86 × 54 mm Instax Mini sheet. Landscape entry
is from the left; portrait entry is from the bottom. The narrow border leads,
with the wide caption border trailing. The inner mat has a 6.5 mm normal offset
and is 0.68 mm thick (a 0.20 mm first layer plus six 0.08 mm layers). Shaped openings mask more of the nominal 62 × 46 mm image;
per-design visible-area percentages are in the [manifest](../catalog/current.json).

The editable projects retain example material assignments. Assign your own
spools. Plate 1 has a mat-to-ornament material change; plate 2 is the back.
The supplied slice records use Bambu P2S / 0.4 mm nozzle / PLA / textured PEI,
0.20 mm first layer and 0.08 mm following layers, two walls, 15% gyroid and no
supports. Reslice for other equipment. Opening a project does not start a print.

All eight current projects have a reinforced mat: 0.68 mm instead of 0.36 mm.
The wider mat had shown bending and stress during plate removal; four additional
mat layers address that observation without changing the artwork, aperture,
photo channel or matching back. The visible mat rises 0.32 mm toward the viewer;
the maximum frame depth stays the same. Physical improvement still needs testing.

Three Ø6 × 3 mm magnets glue into Ø6.3 × 3.1 mm rear pockets with closed floors.
The four rounded-root fork clips only need to engage once for the intended
glued assembly. Glue the seated joints if needed, keep the channel clear, and
let adhesive cure before inserting film. The magnetic surface can be a fridge,
locker, display board or another surface that attracts magnets.

The individual upright previews share one 60° side camera, 220 mm camera distance,
upright vertical axis, lighting and fixed viewport. They use a common physical
scale and photo-center position; no per-frame auto-fit or recentering is applied.
Photo-fit diagrams are rear views. Their carrier outlines follow actual CAD
underside edges, and entry arrows are mirrored appropriately from the front view.

## Checks and reviews

Each current native file's SHA-256 matches its successful two-plate slicer
record. [Per-design reports](../validation/current/) record watertight parts,
a single fused front, four closed socket roofs, clip engagement, zero mated
interference within tolerance, 28 insertion positions, ±0.6 mm image alignment,
three magnet-pocket floors and front-view concealment. Actual extrusion paths
were compared with CAD sections at every back layer; the records bind the
checked back mesh, geometry report and final G-code hashes.

The reports confirm digital geometry and path presence, rather than physical
fit, exact extrusion volume, strength, adhesive hold or magnetic stability.
Empty per-plate warning fields do not imply diagnostic-free raw slicer logs.
Some source logs include nonfatal slicer/processor diagnostics. The native
files are intended to be reviewed and sliced locally before printing.

Independent historian-role and product-design-role AI reviews covered the
period-catalog masters and actual meshes. Botanical Garland underwent another
actual-sculpture pass: v2 clarified the petal bowls but introduced button-like
centers; v3 lowered and blended irregular seed relief and softened doubled
petal margins. Both reviewers accepted v3 for a physical prototype. The
[before/after comparison](../renders/current/Botanical-Garland-Before-After.png)
uses identical cameras, scale and lighting. These are AI design assessments,
not human historical authentication or physical test results.

## Historical basis

The current compositions use French Louis XV floral Rococo vocabulary,
approximately 1735–1750: floral groups, folded acanthus, tapering C/S scrolls,
shells and recessed grounds. Research included The Met's
[1971.206.34, *Picture frame (cadre)*](https://www.metmuseum.org/art/collection/search/209073),
design attributed to Juste Aurèle Meissonnier, ca. 1735, and the Getty's
[*Louis Style: French Frames 1610–1792*](https://www.getty.edu/art/exhibitions/french_frames/LFF_Online_Gallery_Graphics.pdf).
The Met photograph is identified as public domain; it informed carving
vocabulary rather than a literal copy of that large frame's design.

The complete compositions, miniature photo format, mat, clips, magnets and
supported relief are modern. They are historically informed new designs,
rather than replicas of eight documented antique frames. The closed relief
omits true carved undercuts, and some petal forms remain simplified. Fine
seed granulation can soften in a 0.4 mm-nozzle print. No MakerWorld mesh or
personal photograph is used in this catalog.

New model/assets/documentation are CC0-1.0 to the extent rights exist; code is
MIT. Third-party software and historical research retain their own rights.
See [provenance](../PROVENANCE.txt) and [license scope](../LICENSING.md).

## Rebuild

Install [the CAD requirements](../source/requirements.txt), then run from the
repository root:

```sh
export BAROQUE_BUILD_DIR="$PWD/build/current-catalog"
export BAROQUE_DESIGNS_FILE="$PWD/source/designs-current.json"
python source/build_floral_rococo.py
python source/finalize_period_catalog.py
python source/validate_floral_slices.py
python source/verify_back_toolpaths.py --all
```

Cached final height fields and master drawings are referenced in the
[current design inputs](../source/designs-current.json). They rebuild without
new image generation, depth inference or API credentials. The slicer step needs
local Bambu Studio; set `BAMBU_STUDIO` if its executable has another path.

Regenerate the aligned STL downloads from the checked current 3MFs with the CAD
environment, then refresh the catalog links:

```sh
python tools/export_stl_downloads.py
python source/write_current_readme.py
```

To check the distributed current projects, STL exports and documentation:

```sh
python tools/verify_current_catalog.py
```

The earlier release has a separate `python tools/verify_release.py` integrity
check. Neither command proves physical fit or starts a print.
