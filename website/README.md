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

The theme and navigation live here. The hero uses a small pre-rendered actual-mesh
video: the photo loads at a rear angle, then the frame turns to a close front view.
It plays once when visible and holds the finished frame. Reduced-motion visitors
get a still poster. There are no animation buttons or native video controls.
JavaScript turns the README's individual view links into one shared selector
above the collection. Front, Angled, Back and Photo fit update all eight previews
and their enlargement links together. Native radio controls support keyboard
navigation. Without JavaScript, the individual image links and downloads remain
available. JavaScript also starts the intro animation.

## Search and sharing

The collection has a descriptive Instax Mini search title, a canonical URL,
Open Graph and large-card sharing metadata, and CollectionPage / ItemList
structured data. The wide sharing preview is rendered from the unchanged
Segmental Arch model by `source/render_social_preview.py`.

Eight static design pages under `frames/<slug>/` are generated from
`catalog/current.json` and the design-specific notes in `frame-notes.json`.
Dimensions, depth, print-time estimates, file links and views come from the
catalog. These pages have distinct titles, descriptions and CreativeWork file
metadata; they do not claim commercial offers or review ratings. The catalog
links to them, and `sitemap.xml` includes all nine canonical URLs. The build
checks metadata, JSON-LD, internal page/asset links, downloads and the sitemap.

The Google Search Console verification meta tag lives in the home template and
must remain present after verification. The site's project-directory
`robots.txt` is not the host-root robots file; submit the sitemap in Search
Console to make discovery explicit. The site adds no visitor-tracking script.
3MF downloads always point to `models/current/` on `main`; the matching STL ZIPs
point to `models/current/stl/`. Both use direct file links. Source and detailed
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
Image, video, CSS and JavaScript filenames include their content hashes to avoid
serving an older cached version after a new deployment.
Only the used image assets are packaged, as lossless WebP derivatives; original
renders and model files remain unchanged. The page paper is the same
`#f6f4ee` as the front/angled render canvases. Rear and rear-fit views use that same canvas; assembly illustrations
have their own matching surrounds. No image is recolored to match the theme.

## Automatic publishing

[The Pages workflow](../.github/workflows/pages.yml) builds on every push to
`main` and deploys the static output to
<https://obartra.github.io/baroque-instax-frames/>. Pull requests build and check
the page without publishing. GitHub Pages must use the GitHub Actions build type.
The deployment environment exposes the live URL in GitHub Actions.

Code and theme: [MIT](../LICENSES/MIT.txt). Project images and documentation:
[CC0](../LICENSES/CC0-1.0.txt), within the project's [license scope](../LICENSING.md).
