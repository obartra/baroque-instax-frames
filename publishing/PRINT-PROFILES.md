# MakerWorld profile preparation

Updated 2026-11-18. Botanical Garland remains the only published print profile.
The other seven designs now have locally prepared and sliced upload candidates,
saved as seven unpublished MakerWorld drafts with their descriptions and two
plate previews. They are awaiting matching physical-print photographs.

The complete [two-color P2S project pack is publicly downloadable](https://github.com/obartra/baroque-instax-frames/releases/download/v0.2.0/Floral-Instax-Frames-v0.2.0-Two-Color-P2S.zip),
including all eight editable projects, two plate previews per frame, assembly
illustrations, licenses and a SHA-256 manifest. It is also live under Other Files
on the Printables listing. The same pack was submitted as an additional open
raw-model download on MakerWorld; that model edit entered review. These public
file downloads are distinct from MakerWorld's photo-dependent app profiles.

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
4. Use the complete `MakerWorld-Upload.3mf` Bambu export, with editable geometry and two plate previews; never use a front-only or back-only G-code job.
5. Verify the published design name, plates, photographs and download. Record its profile URL here.

No new profile was published in this pass. Automatic security verification
eventually cleared, and all seven drafts were saved. The Segmental Arch draft
was reloaded to verify the full Bambu export and two plates persisted. The final
Landscape Oval draft was also reloaded and checked. All other saves navigated
to distinct draft URLs with the expected filename and two plates visible.
Private draft links are saved with the local delivery, alongside the complete
files and descriptions; no draft state is required to recover the candidates.

On the subsequent publication attempt, MakerWorld rejected the Landscape Oval
profile with “Please select or upload pictures.” No render was presented as a
real photograph and no claim of full guideline compliance was submitted.
All seven app drafts remain unpublished; the public pack makes their files
available meanwhile. See [publication records](two-color-publication.json).

## Rebuild

On a Mac with the official Bambu Studio application installed:

```sh
python tools/prepare_makerworld_profiles.py --output /path/to/profile-candidates
```

Optionally append design slugs to re-slice selected candidates. The tool only
prepares files and invokes the local slicer. It never uploads files, sends jobs
to a printer or starts a print. Generated large files and user photographs are
kept outside the source repository.
