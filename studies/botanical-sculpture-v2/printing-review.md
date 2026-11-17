# Botanical Garland sculpted petals v2 — printing review

AI review of the actual printable mesh, not a physical print or independent human certification. Reviewed 2026-11-17 against the released Botanical Garland baseline and its neutral carving master.

## Verdict

The two authored flower bowls are a useful sculptural improvement and show no new blocking printability problem. Retain them. Before treating v2 as the final visual improvement, make one targeted seed-center revision: the regular crosshatching and sharply bounded circular disks currently read as textured buttons. Use shallow connected irregular or staggered seed scales, and soften the continuous disk rim into the inner petal bowl. Preserve the continuous seed mass; do not introduce separate balls or pistils.

## Actual-mesh observations

- The upper-left bloom now has a stronger broad concavity and distinct rolled shoulders, rather than relying mainly on shallow radial texture. The lower-right bloom also reads more clearly from the front and oblique view. Their different poses preserve the diagonal composition.
- No new circular flower mounting pad is visible. The supported bowl/lip transitions remain integrated with the existing carving. These are still column-supported relief surfaces, not freestanding curled petals or true undercuts.
- The lower-right bloom's upper petal has a slightly nested, horseshoe-like double shoulder. A small local reduction of the duplicate outer crest would improve naturalism; this does not justify flattening or globally smoothing the other lips.
- Broad folds and short nominal 0.72 mm grooves are a sensible scale for the supplied 0.4 mm nozzle. Exact groove shape and seed granulation still require inspection of the physical print. A 0.08 mm layer height improves vertical contours but does not establish lateral reproduction of every surface mark.
- The higher upper-left lip remains a supported mass in the low-angle view. No newly thin unsupported shelf is apparent. The unchanged exterior leaf tips remain handling-sensitive ornamental features; use the rails rather than petals when assembling.

## Mechanical and slicing evidence

Independently compared the baseline and revised files: `outer.wkt`, `aperture.wkt`, `white-mat.stl`, `back.stl`, and `loaded-back.stl` are byte-identical. The new geometry report passes watertight and single-volume front checks, closed socket roofs, zero assembly interference, 28 insertion positions and preserved clear aperture. This supports the claim that the sculpture pass did not change the footprint, mat, carrier or film path.

Local slicing of the exact v2 project succeeds with two plates, expected [1, 0] filament changes and empty per-plate warning fields. The raw log retains T65535 processor diagnostics; empty warning fields do not mean a diagnostic-free log. The front estimate is 168.6 minutes and 16.64 g, versus 166.5 minutes and 16.41 g for the baseline.

The user intends one snap assembly followed by adhesive. Repeated snap fatigue is therefore not a release requirement. Clean initial seating and free photo sliding still need a physical check; unchanged CAD does not establish actual extrusion tolerance or bridge quality. No print was started for this review.

## Next gate

Review the localized center revision in actual mesh renders, then slice the exact final project and verify its identity. Test the first assembly at the four snap locations while supporting the rails, and slide in the full uncut photo. No broader geometry redesign is indicated by the present evidence.

Reviewed images: `build/botanical-sculpture-v2/renders/16-Rocaille-Botanical-Garland-Sculpted-v2-actual-detail.png`, `...-actual-multiview.png`, and `Botanical-Garland-Before-After.png`.
