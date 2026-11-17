# GitHub Pages

A small static site built from the root [README](../README.md), using the
[Segmental Arch project icon](../assets/brand/README.md) and the current catalog
images. It has no framework, hosted database, tracking or external fonts.

## One source of content

`tools/build_pages.py` reads the README on every build. The frame table, model
links, print settings, illustrated steps, photo-fit explanation and license
sections are not copied into a second set of page content. Edit
`source/write_current_readme.py` and regenerate the README when changing this
project's generated documentation; a direct README edit is also reflected in
the next site build.

The theme and navigation live here. JavaScript only enhances the frame-view
links; without it the links still open their images and the downloads work.
3MF downloads always point to `models/current/` on `main`. Source and detailed
documentation links open the corresponding repository files.

## Build locally

```sh
python -m venv .venv-pages
.venv-pages/bin/pip install -r website/requirements.txt
.venv-pages/bin/python tools/build_pages.py
python -m http.server 8000 --directory dist
```

Open `http://localhost:8000`. The generated `dist/` folder is ignored by Git.
The build validates image files, section anchors and all eight model links.
Only the used image assets are packaged, as lossless WebP derivatives; original
renders and model files remain unchanged. The page paper is the same
`#f6f4ee` as the front/angled render canvases. Assembly and rear-fit illustrations
have their own matching surrounds. No image is recolored to match the theme.

## Automatic publishing

[The Pages workflow](../.github/workflows/pages.yml) builds on every push to
`main` and deploys the static output to
<https://obartra.github.io/baroque-instax-frames/>. Pull requests build and check
the page without publishing. GitHub Pages must use the GitHub Actions build type.
The deployment environment exposes the live URL in GitHub Actions.

Code and theme: [MIT](../LICENSES/MIT.txt). Project images and documentation:
[CC0](../LICENSES/CC0-1.0.txt), within the project's [license scope](../LICENSING.md).
