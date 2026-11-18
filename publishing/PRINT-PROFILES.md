# MakerWorld profile preparation

Updated 2026-11-18. Botanical Garland remains the only published print profile.
The other seven designs now have locally prepared and sliced upload candidates.
They are awaiting matching physical-print photographs, not additional CAD work.

## Prepared candidates

| Design | Front / back estimate | Status |
| --- | --- | --- |
| Canted Octagon | 129.2 / 54.7 min | Awaiting matching print photos |
| Segmental Arch | 206.8 / 58.9 min | Awaiting matching print photos |
| Cushion Cartouche | 175.3 / 56.3 min | Awaiting matching print photos |
| Floral Corners | 180.1 / 56.3 min | Awaiting matching print photos |
| Botanical Garland | 168.5 / 56.3 min | Existing profile already published; no duplicate uploaded |
| Acanthus Gallery | 170.5 / 56.3 min | Awaiting matching print photos |
| Portrait Oval | 193.7 / 55.2 min | Awaiting matching print photos |
| Landscape Oval | 160.7 / 54.7 min | Awaiting matching print photos |

These are slicer estimates, not measured print durations. Each candidate contains
both parts on two named plates, with gray mat in slot 1 and black ornament/back
in slot 2. The settings match the existing Botanical Garland profile exactly.
All model data, placement and transforms match the current canonical projects.
No geometry, ornament, clips, film clearance or mat thickness was changed.

Fresh local Bambu Studio slicing passed for all eight: two plates, one front
color change, no back color changes and no warnings. The first eight layer
heights were checked, including the seven-layer 0.68 mm mat. Per-design source,
candidate and sliced-file hashes are in
[the validation record](profile-candidates-validation.json).

## Publication gate

[MakerWorld's current upload guidance](https://wiki.bambulab.com/en/makerworld/tutorials/print-profile-upload)
requires original photographs of the completed printed result, showing the
parts and color regions represented by the profile. A CAD preview cannot meet
that requirement. The user's upcoming prints and photographs will supply this
evidence; no new photos are requested urgently.

Before publishing each candidate:

1. Confirm its printed front and matching back assemble and accept an uncut film sheet.
2. Add original matching print photos, including both parts. Keep the CAD preview identified as a render.
3. Remove the preparation note from the supplied description.
4. Upload the complete editable two-plate native project, not a front-only or back-only G-code job.
5. Verify the published design name, plates, photographs and download. Record its profile URL here.

No new profile was published in this pass. The Segmental Arch upload reached
draft URL `10630376`, but the subsequent page stalled at automatic security
verification, so its saved contents have not been independently confirmed.
The complete files and descriptions are also saved locally; no draft state is
required to recover them.

## Rebuild

On a Mac with the official Bambu Studio application installed:

```sh
python tools/prepare_makerworld_profiles.py --output /path/to/profile-candidates
```

Optionally append design slugs to re-slice selected candidates. The tool only
prepares files and invokes the local slicer. It never uploads files, sends jobs
to a printer or starts a print. Generated large files and user photographs are
kept outside the source repository.
