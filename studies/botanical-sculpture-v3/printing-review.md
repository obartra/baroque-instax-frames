# Botanical Garland sculpted petals v3 — final printing review

AI assessment of actual CAD renders and digital verification, dated 2026-11-17. This is not a physical print test or independent human certification.

## Verdict

Accept v3 for a physical prototype. The exact final back toolpath audit has passed. No further sculptural iteration is requested before that prototype.

The two principal blooms retain the useful improvement over the released baseline: broad concave bowls, unequal petal shoulders and rolled lips that are easier to distinguish than shallow inferred surface texture. The v3 centers are lower and less precisely circular, with irregular connected granulation. They blend into the bowls and no longer read as v2's crosshatched buttons. The localized lip reductions retain the flower shapes without a conspicuous added mounting ring.

The full-frame view preserves the diagonal hierarchy, smaller subordinate blooms, acanthus flow and quiet crisp mat. The low-angle view shows continuous supported relief rather than newly thin, suspended petals. Some local stepped folds remain, especially on the lower-right upper petal, but these do not constitute a new printability blocker or justify another global smoothing pass.

## Evidence checked

- Compared the v3 actual-detail and actual-multiview renders, plus `Botanical-Garland-Before-After.png`, with the released baseline and v2 review.
- Independently compared the baseline and revised files: `outer.wkt`, `aperture.wkt`, `white-mat.stl`, `back.stl` and `loaded-back.stl` are byte-identical. Footprint, exact mat, photo aperture and carrier are preserved.
- The new geometry report passes watertight and single-volume front checks, closed socket roofs, zero mated interference, 28 insertion positions and preserved clear aperture. Maximum front Z is approximately 9.03 mm, versus 8.40 mm for the baseline.
- The exact v3 local slicer report succeeds for both plates with expected [1, 0] filament changes and empty per-plate warning fields. Front: 167.9 minutes / 16.59 g. Back: 56.3 minutes / 6.62 g. Empty warning fields are not a claim of a diagnostic-free raw log.
- The exact final back audit passes all 98 layers, with zero missing cross-section components or functional regions and minimum buffered functional-region path coverage of 84.32%. Independently verified its STL, geometry-report and final G-code hashes against the current files. This is evidence of toolpath presence, not strength or exact extrusion-volume certification.

## Physical checks still needed

The supplied 0.4 mm nozzle and 0.08 mm layers should be judged on the printed broad flower curves first. Fine seed granulation and short grooves may soften or merge; the low continuous centers remain readable masses even if individual scales are not reproduced. Digital renders do not establish surface finish or nozzle-scale detail reproduction.

The user intends one snap assembly followed by adhesive. Repeated clip fatigue is not a requirement or a claim. Test clean initial seating at all four snaps, actual bridge/roof fit and free sliding of the full uncut photo; support the rails while assembling rather than loading the flower tips. Digital clearance and toolpath-presence checks do not establish actual extrusion tolerance or bonding strength. No print was submitted or started for this review.

## Recommendation

Keep this geometry for the first prototype. Its exact final slice and back audit pass; inspect the physical petal lips, low seed centers and first assembly next. Make any subsequent adjustment from that evidence rather than continuing speculative smoothing or adding unsupported detail.
