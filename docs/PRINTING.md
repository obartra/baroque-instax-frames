# Printing and assembly details

Follow the [five-step illustrated guide](../README.md#print-and-assemble). The examples use actual silhouettes from the released Floral Corners and Segmental Arch projects. The same assembly sequence applies to the matching two-piece designs; keep each front with its own back. The illustrations show different mat and frame colors; a single filament also works.

## Materials and profile

| Item | Supplied project setting or requirement |
| --- | --- |
| 3MF printer profile | Supplied Bambu P2S, 0.4 mm nozzle settings |
| STL printer setup | Use profiles for your own printer, nozzle and filament |
| Build surface | Textured PEI |
| Filament | Your chosen filament; supplied profiles use PLA |
| Supplied 3MF layer heights | 0.08 mm; first layer 0.20 mm |
| Mat and ornament | Assign the same filament, or optional separate colors |
| Plate 1 | One fused front: reinforced mat, then ornament |
| Plate 2 | Matching back; choose its material separately |
| Supports / prime tower | Disabled in the supplied profile |
| Magnets | Three round magnets, 6 mm diameter × 3 mm thick |
| Adhesive | Suitable for both your printed material and magnets; follow its preparation and curing instructions |

Open the `.3mf` **as a project** in Bambu Studio so its plates, parts and color assignments are retained. For another printer, choose the appropriate machine and review the resulting slice and clearances. Set a profile for your filament. For a single-color front, assign the mat and ornament to the same filament before slicing. Separate colors require a filament change; check the resulting purge requirements.

The mat is **0.68 mm high**: a 0.20 mm first layer plus six 0.08 mm layers (seven total). This reinforcement replaces the earlier three-layer mat after prints showed bending and stress during removal. Preserve the full 0.68 mm mat thickness when choosing other layer heights. With separate colors, the front then changes to the ornament filament. With one filament, that color change is unnecessary. The front is one fused piece, so there is no separate mat to glue or assemble.

## Using the STL downloads

Each catalog entry also offers an **STL ZIP**, exported directly from its current
reinforced-mat 3MF. Dimensions are in **millimeters**. Extract the ZIP first.

1. Import `mat.stl` and `front-ornament.stl` together as **parts of one object**.
   Preserve their shared origin; do not center, arrange or drop them separately.
   The ornament starts above the 0.68 mm mat and prints onto it.
2. Assign the same filament to both regions for a single-color front, or assign
   separate colors. Slice them together as **one physical front**, not as two
   separately printed pieces.
3. Import `back.stl` on a separate plate, flat side down and clips up.
   Use the settings above and check the slice for your printer and filament.

STL does not retain units, material assignments, plate layouts or print profiles.
The 3MF project preserves these and is the simpler option for Bambu Studio.
Each ZIP contains an export record tying its meshes to the checked 3MF revision.

### Changing colors with STLs

STL files contain geometry, not color instructions. `mat.stl` and
`front-ornament.stl` identify the two regions: the mat ends at **0.68 mm** and
the ornament begins there. Keep both aligned as one object.

- **Multicolor setup:** assign a filament to each part. The slicer schedules
  the change from the geometry; no additional pause or manual layer selection
  is needed.
- **Manual filament swap:** with a **0.20 mm first layer and 0.08 mm subsequent
  layers**, finish the mat through **layer 7, Z = 0.68 mm**, then pause/change
  **before layer 8, Z = 0.76 mm**, the first ornament layer. Use your printer's
  supported pause or filament-change feature and confirm the placement in the
  sliced preview before printing.
- **Single color:** assign both parts the same filament; no change is needed.

The layer-8 instruction applies only to those layer heights and the supplied
flat print orientation. If you change layer heights or use adaptive layers,
locate the first ornament toolpath in the preview and put the change immediately
before it. For a clean manual color boundary, use a layer schedule that finishes
a layer at 0.68 mm; do not blindly reuse layer 8 with another profile.
The separately printed back uses one chosen filament.

## 1. Print the matching pair

Print both plates from the same frame project. Plate 1 is the front; plate 2 is its matching back. Assign the materials you want for each. Earlier backs have different clips: do not mix generations or pair parts from different frame projects.

Let the plate cool, then flex the plate away from the frame. Avoid lifting the print by pulling on the inner mat. The reinforcement still needs a physical print check.

## 2. Glue the magnets

On the rear of the back piece, apply a small amount of suitable adhesive in each magnet pocket. The pockets are **6.3 mm diameter × 3.1 mm deep**, with a **0.5 mm closed floor**. Seat all three exposed magnet faces evenly at the rear plane, following your adhesive's instructions. Keep adhesive out of the photo channel, springs and snaps.

Let the adhesive cure fully **before assembly or inserting film**. Keep loose magnets away from children and pets. Do not use a part with an unsecured magnet.

## 3. Snap together while empty

Put the ornamental front face down on a soft cloth, with its socket side facing upward. Lower the matching back with its **four forks pointing down toward the sockets**. Align all four before pressing near each corner in turn. Support the part nearby rather than pushing on a projecting flower or leaf.

The photograph goes in **after** the front and back are joined. There are three guide sides and compliant edge fingers to locate the sheet inside the assembled channel.

The clips only need to engage once. Glue the seated joints if needed, keeping adhesive out of the photo channel, and let it cure before loading the photo. Repeated snap fatigue is not a requirement of this glued assembly.

## 4. Slide in the whole photo

The frame holds a complete **86 × 54 mm Instax Mini sheet**; its nominal image is 62 × 46 mm. Keep the instant film whole and do not force it.

| Orientation | Enter from | Leading edge | Wide caption border ends up |
| --- | --- | --- | --- |
| Landscape | Left | Narrow border | Left |
| Portrait | Bottom | Narrow border | Bottom |

Slide gently until the sheet reaches the firm stop. If it binds before reaching the stop, remove it and inspect the channel, adhesive and print quality. The paper border should sit behind the surround. Shaped openings deliberately mask parts of the image; their visible area is recorded in each design's geometry report.

These projects are for Instax Mini, not Polaroid Go, full-size Polaroid, Instax Square or Instax Wide film.

## 5. Place and change

Place the magnet side against a magnet-attracting surface, such as a fridge, locker or display board. To change the picture, gently slide it out through the same entry side. Adhesive hold, real film fit and initial clip seating still need physical validation for these prototypes.

## Illustration sources

[Editable diagrams and source records](assembly/README.md) · [Geometry reports](../validation/current/) · [Build instructions](CURRENT-CATALOG.md#rebuild)
