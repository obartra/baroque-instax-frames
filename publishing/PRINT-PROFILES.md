# MakerWorld profiles and current raw projects

Updated 2026-11-20 for v0.3.0. All eight current editable two-color projects are included in the [release pack](https://github.com/obartra/baroque-instax-frames/releases/download/v0.3.0/Floral-Instax-Frames-v0.3.0-Two-Color-P2S.zip). Each contains two plates, previews, gray-mat slot 1 and black-ornament/back slot 2. Colors are examples.

| Design | Front / back estimate | Revised state |
| --- | --- | --- |
| Canted Octagon | 136.7 / 54.7 min | Restored front; revised print evidence pending |
| Segmental Arch | 206.8 / 58.9 min | Geometry unchanged from v0.2.0 |
| Cushion Cartouche | 179.5 / 56.3 min | Restored front; revised print evidence pending |
| Floral Corners | 182.6 / 56.3 min | Restored front; revised print evidence pending |
| Botanical Garland | 170.8 / 56.3 min | Restored front; revised print evidence pending |
| Acanthus Gallery | 170.5 / 56.3 min | Geometry unchanged from v0.2.0 |
| Portrait Oval | 200.1 / 55.2 min | Restored front; revised print evidence pending |
| Landscape Oval | 161.5 / 54.7 min | Restored front; revised print evidence pending |

Fresh local Bambu Studio slicing passed for the exact eight current candidates: two plates, one front material change, none on the back and no per-plate warnings. First-layer and mat-boundary heights were checked. [Hashes and per-design results](profile-candidates-validation.json) bind these exports to the current canonical models. This run did not submit a print or establish physical print quality.

## App-profile migration

The published Botanical Garland profile [4170210](https://makerworld.com/en/models/3636176-rococo-instax-mini-magnetic-frames-8-designs#profileId-4170210) and its real photos document **legacy v0.2.0 geometry**. Its photographs do not verify the restored v0.3.0 front. Use the versioned v0.3.0 raw project for the correction.

The seven previously saved drafts were also prepared from v0.2.0. Replace affected draft files and descriptions with these current candidates before publishing them. The raw download release is separate from claiming a revised app profile is physically tested. No new matching real-print photographs were supplied during this release.

Before publishing a revised app profile, check its actual printed front with its matching back and an uncut film sheet; add original matching result photographs; use the full exported `MakerWorld-Upload.3mf` with two plates and previews; and record the final public profile URL. CAD previews remain labeled as renders. Earlier drafts and the legacy profile are not recorded as new v0.3.0 app-profile publications.

## Rebuild

```sh
python tools/prepare_makerworld_profiles.py --output /path/to/current-profile-candidates
python tools/package_two_color_profiles.py --candidates /path/to/current-profile-candidates --output /path/to/Floral-Instax-Frames-v0.3.0-Two-Color-P2S.zip
```

These tools prepare, check and package files. They never upload or start a print.
