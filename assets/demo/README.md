# Photo insertion demo

[![Actual Segmental Arch with simulated coastal photo](photo-insertion-poster.png)](https://obartra.github.io/baroque-instax-frames/#top)

[Watch on the project website](https://obartra.github.io/baroque-instax-frames/#top)
· [MP4](photo-insertion.mp4) · [WebM](photo-insertion.webm)

This is a render of the actual current Segmental Arch and its matching back.
The complete 54 × 86 mm film sheet translates upward through the bottom entry;
its front plane is depth-tested against the assembled model. The narrow border
leads and the wide border trails. The photograph is the cached
[AI-simulated coastal image](../brand/README.md).

The camera starts 30° away from a straight rear view. The full-thickness sheet
is fully seated before the frame turns to a front three-quarter view and the
camera moves closer. Each orbit view is rendered from the actual model, with
the front photo, paper back and sheet edges depth-tested against the assembly.
The motion has no deformation, overshoot or invented photo latch.

The website plays once when visible and holds the final view. Reduced-motion
visitors see a still poster. There are no animation buttons or native video
controls. The video has no audio.

Rebuild in the project's CAD Python environment, with FFmpeg installed:

```sh
python source/render_insertion_animation.py
```

Run this from the repository root. `FFMPEG` can specify another executable path.
Actual mesh/depth views are cached under ignored `build/`; the moving film
box is composited using those depth buffers. The original model hash is checked
before and after rendering. [Camera, motion and output hashes](render-record.json).

Render assets and documentation: [CC0](../../LICENSES/CC0-1.0.txt), within the
project's [license scope](../../LICENSING.md). Rendering code: [MIT](../../LICENSES/MIT.txt).
