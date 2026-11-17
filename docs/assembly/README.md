# Illustrated assembly guide

The six steps are grouped into three sheets. Each SVG is editable; its PNG preview is used in the main README.

| Steps | SVG | PNG |
| --- | --- | --- |
| 1–2: coupon and two plates | [Print](01-print.svg) | [Preview](01-print.png) |
| 3–4: magnets and empty-frame assembly | [Assemble](02-assemble.svg) | [Preview](02-assemble.png) |
| 5–6: uncut film and fridge mounting | [Load and display](03-load-and-display.svg) | [Preview](03-load-and-display.png) |

The front and back outlines come from native meshes in the released **Floral Corners** 3MF; the portrait silhouette comes from the released **Segmental Arch** 3MF. The photo/mat geometry, magnet count and fork locations follow their geometry records. Outlines are simplified by 0.10 mm for illustration only. Exploded sections, clip close-ups and tools are schematic, rather than manufacturing drawings. The sample photos are drawn placeholders.

The sequence matters: **join the empty frame, then slide in the whole film**. The wide caption border trails behind the narrow leading edge: left in landscape, below in portrait. No film is trimmed or enclosed between separated parts.

To rebuild the diagrams, use the project's CAD Python environment and an installed `rsvg-convert`:

```sh
python source/make_assembly_instructions.py
```

[Geometry sources, hashes and sequence record](sources.json) · [Detailed printing instructions](../PRINTING.md)

The repository's CC0-1.0 dedication applies to these diagrams and documentation; the generator uses MIT.
