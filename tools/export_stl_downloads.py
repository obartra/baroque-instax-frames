#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Export aligned STL regions directly from the checked current 3MFs.

Run with the CAD environment (source/requirements.txt), then regenerate README.
No rescaling, remeshing, centering or changes to native projects.
"""
import hashlib
import io
import json
from pathlib import Path
import sys
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'source'))
from build_catalog import read_project_mesh


def export(catalog):
    for frame in catalog['frames']:
        project = ROOT / frame['model']
        assert hashlib.sha256(project.read_bytes()).hexdigest() == frame['sha256']
        files = {}
        parts = {}
        for number, name in [(1, 'mat.stl'), (2, 'front-ornament.stl'), (4, 'back.stl')]:
            mesh = read_project_mesh(project, number)
            data = mesh.export(file_type='stl')
            facets = np.frombuffer(data, offset=84, dtype=np.dtype([
                ('normal', '<f4', (3,)), ('vertices', '<f4', (3, 3)), ('attribute', '<u2')]))
            assert np.array_equal(facets['vertices'], mesh.triangles.astype('<f4')), name
            files[name] = data
            parts[name] = dict(sha256=hashlib.sha256(data).hexdigest(),
                               triangles=len(mesh.faces), bounds_mm=mesh.bounds.tolist())
        record = dict(frame=frame['name'], source_3mf=frame['model'],
                      source_sha256=frame['sha256'], units='millimeter', parts=parts)
        files['export-record.json'] = (json.dumps(record, indent=2) + '\n').encode()
        files['README.txt'] = f'''{frame['name']} — STL files

Units: millimeters. Exported from the matching current reinforced-mat 3MF.

Import mat.stl and front-ornament.stl together as parts of ONE object.
Keep their original coordinates; do not center, arrange or drop them separately.
Assign the same filament or separate colors. These regions print as ONE front.
The ornament starts above the 0.68 mm mat; it is not a separate physical piece.

TWO COLORS
STL stores geometry, not colors. Assign a filament to each aligned front part
in a multicolor slicer; it schedules the change automatically.
For a manual swap with 0.20 mm first layer, then 0.08 mm layers:
finish layer 7 at Z=0.68 mm, then change BEFORE layer 8 at Z=0.76 mm.
Use your printer's supported pause/change feature. With different or adaptive
layer heights, find the first ornament layer in the preview instead of reusing
layer 8. Use a layer schedule that ends a layer at the 0.68 mm boundary.
For one color, assign both parts the same filament; no swap is needed.

Print back.stl separately, flat side down, with the clips pointing up.
The finished assembly has two physical pieces: front and matching back.
STLs do not store units, colors, plates or slicer settings. Use the project 3MF
to retain those settings, or consult docs/PRINTING.md in the repository.

Source: https://github.com/obartra/baroque-instax-frames
Models: CC0-1.0, within the repository's LICENSING.md scope.
'''.encode()
        buffer = io.BytesIO()
        with ZipFile(buffer, 'w', compression=ZIP_DEFLATED, compresslevel=6) as archive:
            for name, data in files.items():
                info = ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
                info.compress_type = ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                archive.writestr(info, data)
        data = buffer.getvalue()
        relative = f'models/current/stl/{frame["slug"]}-stl.zip'
        target = ROOT / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        frame['stl'] = dict(archive=relative, sha256=hashlib.sha256(data).hexdigest())
        print(f'EXPORTED {frame["name"]}: {len(data)/1024**2:.1f} MiB', flush=True)


if __name__ == '__main__':
    path = ROOT / 'catalog/current.json'
    catalog = json.loads(path.read_text())
    export(catalog)
    path.write_text(json.dumps(catalog, indent=2) + '\n')
