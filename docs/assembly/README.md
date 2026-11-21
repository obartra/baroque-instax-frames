# Illustrated assembly guide

The five steps are grouped into three sheets. Each SVG is editable; its PNG preview is used in the main README. The illustrations show contrasting mat and frame colors; a single filament also works.

| Steps | SVG | PNG |
| --- | --- | --- |
| 1–2: print two plates and glue magnets | [Print and prepare](01-print.svg) | [Preview](01-print-and-magnets-v2.png) |
| 3–4: snap the empty frame and slide in the photo | [Assemble and load](02-assemble.svg) | [Preview](02-snap-and-load-v2.png) |
| 5: place on a magnet-attracting surface | [Display](03-load-and-display.svg) | [Preview](03-magnetic-display-v2.png) |

The front and back outlines come from native meshes in the released **Floral Corners** 3MF; the portrait silhouette comes from the released **Segmental Arch** 3MF. The photo/mat geometry, magnet count and fork locations follow their geometry records. Outlines are simplified by 0.10 mm for illustration only. Exploded sections, clip close-ups and tools are schematic, rather than manufacturing drawings. The sample photos are drawn placeholders.

The sequence matters: **join the empty frame, then slide in the whole film**. The wide caption border trails behind the narrow leading edge: left in landscape, below in portrait. No film is trimmed or enclosed between separated parts.

There is no preliminary snap-fit test. The joints can be glued after their single assembly. Let adhesive cure before loading the photo. The last sheet calibrates the frame's actual footprint against a representative 600 × 1700 mm fridge; its separate close-up is labeled as enlarged. A fridge is one example of a magnet-attracting surface.

To rebuild the diagrams, use the project's CAD Python environment and an installed `rsvg-convert`:

```sh
python source/make_assembly_instructions.py
```

[Geometry sources, hashes and sequence record](sources.json) · [Detailed printing instructions](../PRINTING.md)

The repository's CC0-1.0 dedication applies to these diagrams and documentation; the generator uses MIT.

The v0.3.0 guide was regenerated from the current Floral Corners and unchanged
Segmental Arch projects. These are simplified assembly silhouettes, not
photographs or detailed surface previews. See [revision comparisons](../UPGRADING-v0.3.0.md)
for the restored ornament.
