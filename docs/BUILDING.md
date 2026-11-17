# Building and rendering

The distributed projects are in `models/`. Generated work goes into ignored
`build/`, leaving those validated release files untouched.

The archived CAD environment used Python **3.15.2** and the pinned versions
below. Use a Python version supported by those packages (3.15 is the tested
environment):

```sh
git clone https://github.com/obartra/baroque-instax-frames.git
cd baroque-instax-frames
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r source/requirements.txt
python source/build_catalog.py
python source/finalize_projects.py
python source/render_catalog.py
python source/render_catalog.py overview
python source/render_clips.py
```

Build all six designs before finalization: it reads their generated validation
and outline files. A single study can be built with, for example,
`python source/build_catalog.py 04-Floral-Corners`. Finalization checks the
assembled parts and creates the clip coupon. These operations can take time
and substantial memory; they include mesh booleans and raster-derived relief.

No image-generation service or API key is needed to rebuild. The six master
drawings are included in `concepts/`; prompts and input records are in
`source/designs-final.json`. The build interprets the master front drawing as
tonal bas-relief and adds explicit CAD geometry. It does not reconstruct a
solid from all concept views.

The builder exports intermediate STL files as well as native indexed 3MF
projects. Finalization reads the indexed 3MF meshes directly. Avoid an STL
round trip when modifying the release pipeline: automatic vertex merging
can change topology in fine ornament.

## Slicer verification

Install Bambu Studio separately. The archived results were produced with
version **02.09.01.70**, using the settings in `source/printer-settings.json`.
The script uses `BAMBU_STUDIO`, an executable on PATH, or the standard macOS
application path, in that order.

```sh
export BAMBU_STUDIO='/path/to/BambuStudio'
python source/validate_slices.py
```

This slices both plates of all six generated projects and the coupon, then
checks the return codes, plate warnings, G-code outputs and one/zero material
transitions. Results, G-code and logs stay in `build/`. Check the log for your
actual slicer version. Different slicer releases or machines may need profile
adjustments; successful slicing does not establish physical print quality.

After a full build, `python source/verify_and_render.py` combines finalization,
slicing and catalog rendering. Run `python source/render_clips.py` separately
for the mechanical detail sheet. To choose a different output directory, set
`BAROQUE_BUILD_DIR` to an absolute path **before every pipeline command**.

The archived reports in `validation/` describe the exact distributed files
in `models/`. Rebuilding creates new project UUIDs and may reflect source
refinements, so byte-identical output is not promised. Do not overwrite the
archived reports with new runs unless releasing the matching new models.

## Release integrity and packaging

```sh
python3 tools/verify_release.py
python3 tools/package_release.py
```

The first command needs only the Python standard library. The second checks
the collection, then writes a complete ZIP and its SHA-256 to ignored `dist/`.
The ZIP contains the models, drawings, renders, source, reports and licenses.
Keep this large ZIP as a release attachment instead of committing it to Git.
