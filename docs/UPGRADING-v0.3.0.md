# Upgrade to v0.3.0

Six fronts restore flowers and ornaments that should overflow onto the mat. The earlier shared clipping boundary removed these details during printable geometry construction. The new relief is supported from the mat; it does not hang in midair or cover the photo opening.

| Design | Upgrade action | Extent |
| --- | --- | --- |
| Botanical Garland | Reprint front; reuse matching back | More visible missing petals |
| Portrait Oval | Reprint front; reuse matching back | More visible missing petals |
| Canted Octagon | Reprint front; reuse matching back | More visible missing petals |
| Floral Corners | Reprint front; reuse matching back | More visible missing petals |
| Cushion Cartouche | Reprint front; reuse matching back | Small edge details |
| Landscape Oval | Reprint front; reuse matching back | Small edge details |
| Segmental Arch | No change for this issue | Geometry unchanged |
| Acanthus Gallery | No change for this issue | Geometry unchanged |

Reprinting is needed only if you want the restored ornament; the earlier fronts remain usable. No back, mat-only or hardware replacement is needed. Keep each front with its own design's matching back. Unchanged geometry does not establish unlimited clip reuse: the PLA clips are intended for one assembly and may be glued. If a previous assembly was glued or a clip breaks during separation, do not force it; print that design's supplied matching back again as needed.

## Download and identify the revision

Use the [v0.3.0 release](https://github.com/obartra/baroque-instax-frames/releases/tag/v0.3.0). All packs contain all eight designs; the Two-Color P2S pack is the easiest Bambu Studio starting point. Its mat uses slot 1, and ornament/back use slot 2. Standard native projects retain a third example material slot for the back.

For each affected design, the native filename contains `Mat-Overflow-v2`, except Botanical Garland, which contains `Mat-Overflow-v4`. The manifest identifies the release as v0.3.0. Segmental Arch and Acanthus Gallery retain their preceding filenames and geometry. Check `SHA256SUMS` against your downloaded archive if you need exact identity.

Print **plate 1 only** when reusing a back. Plate 2 remains included for new frames and replacements. Check your actual printer, plate and filament assignments before sending. Supplied settings are P2S, 0.4 mm nozzle, PLA, 0.20 mm first layer then 0.08 mm, with a 0.68 mm mat. The reviewed slices use no supports or brim. Select your machine/material and re-slice if different.

For STLs, import `mat.stl` and `front-ornament.stl` together as aligned parts of one object. Preserve their coordinates and heights. They form one physical front; do not print the ornament by itself. See the [printing guide](PRINTING.md#using-the-stl-downloads).

## Actual-mesh comparisons

The comparisons use the exact preceding and revised CAD meshes, with identical cameras and lighting. Gold in the detail panels reveals the carving; it does not prescribe a material or depict a real print.

- [Botanical Garland](revisions/v0.3.0/botanical-garland-before-after.png)
- [Portrait Oval](revisions/v0.3.0/portrait-oval-before-after.png)
- [Canted Octagon](revisions/v0.3.0/canted-octagon-before-after.png)
- [Floral Corners](revisions/v0.3.0/floral-corners-before-after.png)
- [Cushion Cartouche](revisions/v0.3.0/cushion-cartouche-before-after.png)
- [Landscape Oval](revisions/v0.3.0/landscape-oval-before-after.png)

## Checks and limits

Exact-model comparisons show unchanged mat and back volumes, preserved existing ornament within numerical tolerance, clear photo apertures and supported restored contours. The native projects and two-color exports pass two-plate slicing with one front material change, none on the back and no per-plate warnings. Layer-path checks verify that restored contours receive extrusion and that the backs retain their functional paths.

These are digital checks. The revised fronts have not yet been physically tested. Earlier real-print photographs document pre-v0.3.0 Botanical Garland; they are not evidence for this revision. Real photographs will accompany revised app profiles after matching prints are checked. The full editable projects can be downloaded and sliced now.

The [changelog](../CHANGELOG.md) records the release scope. Earlier [v0.2.0 downloads](https://github.com/obartra/baroque-instax-frames/releases/tag/v0.2.0) remain available and are not silently replaced.
