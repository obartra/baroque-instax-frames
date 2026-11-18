#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Package checked two-color Bambu projects for public file downloads."""
import argparse
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
NS = {'m': 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidates', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    frames = json.loads((ROOT / 'catalog/current.json').read_text())['frames']
    records = json.loads((args.candidates / 'profile-validation.json').read_text())
    by_slug = {record['slug']: record for record in records}
    assert len(frames) == len(by_slug) == 8
    args.output.parent.mkdir(parents=True, exist_ok=True)
    manifest = []
    with ZipFile(args.output, 'w', ZIP_DEFLATED) as archive:
        for frame in frames:
            record = by_slug[frame['slug']]
            assert record['source_sha256'] == frame['sha256']
            assert sha256((ROOT / frame['model']).read_bytes()).hexdigest() == frame['sha256']
            assert record['filament_changes'] == [1, 0] and not record['warnings']
            data = (args.candidates / record['upload_project']).read_bytes()
            assert sha256(data).hexdigest() == record['upload_sha256']
            with ZipFile(BytesIO(data)) as project:
                assert project.testzip() is None
                model = ET.fromstring(project.read('3D/3dmodel.model'))
                assert len(model.findall('m:build/m:item', NS)) == 2
                settings = json.loads(project.read('Metadata/project_settings.config'))
                assert len(settings['filament_colour']) == 2
                assert len([n for n in project.namelist() if n.endswith('.gcode')]) == 2
                for name in project.namelist():
                    if name.endswith(('.xml', '.model', '.config', '.json')):
                        content = project.read(name)
                        assert b'/Users/' not in content and b'/tmp/' not in content, name
            filename = f"projects/{frame['slug']}.3mf"
            archive.writestr(filename, data)
            direction = 'left' if frame['orientation'] == 'landscape' else 'bottom'
            archive.writestr(f"projects/{frame['slug']}.txt", f"""{frame['name']}

Plate 1: integrated mat and floral front. Plate 2: matching three-magnet back.
Slot 1: mat. Slot 2: ornament and back. Colors can be reassigned.
Photo entry: {direction}, viewed from the front; narrow-border edge first.
Keep the complete 86 × 54 mm Instax Mini sheet uncut.
About {frame['image_visible_percent']:.0f}% of the image area remains visible.
Slicer estimate: {record['estimated_minutes'][0]} min front; {record['estimated_minutes'][1]} min back.
These are local slicing checks, not a claim that every design was physically tested.
""")
            manifest.append({
                'name': frame['name'], 'file': filename, 'sha256': sha256(data).hexdigest(),
                'source_model': frame['model'], 'source_sha256': frame['sha256'],
                'geometry_and_placement_unchanged': True,
                'plates': 2, 'filament_changes': [1, 0], 'warnings': [],
                'estimated_minutes': record['estimated_minutes'],
            })
        archive.writestr('START-HERE.txt', """Eight floral Instax Mini frames — two-color Bambu Studio projects

Open a project from the projects folder in Bambu Studio as a project.
Each contains both matching pieces on two named plates, with previews.
Mat: filament slot 1. Frame and back: filament slot 2.
The default examples use a gray mat and black ornament/back.

Supplied machine/material settings: Bambu P2S, 0.4 mm nozzle, PLA.
For a different printer or material, select its settings and re-slice.
First layer 0.20 mm, then 0.08 mm; mat thickness 0.68 mm / seven layers.
The front has one color change; the back has none. No supports.

Print the two plates. Glue three 6 × 3 mm magnets into the rear pockets.
Align and snap the two pieces together; glue the joints if needed.
After adhesive cures, slide in the whole uncut Instax Mini photo.
Display on a magnetic surface. See the included illustrated instructions.

Geometry and placement match the current reinforced-mat models. This pack
assigns the ornament and back to the same filament slot instead of a third slot.
All eight passed local slicing with no warnings. These checks do not establish
successful physical printing of every design. Original photos are being added
as matching prints are completed; the previews are CAD renders.

Website: https://obartra.github.io/baroque-instax-frames/
Source, STL downloads and licenses: https://github.com/obartra/baroque-instax-frames
Models, project artwork and documentation: CC0 within LICENSING.md scope.
Code: MIT. Personal photographs are not included in this pack.
""")
        for relative in ['LICENSING.md', 'LICENSES/CC0-1.0.txt', 'LICENSES/MIT.txt',
                         'docs/assembly/01-print-and-magnets-v3.png',
                         'docs/assembly/02-snap-and-load-v3.png',
                         'docs/assembly/03-magnetic-display-v3.png']:
            archive.write(ROOT / relative, relative)
        archive.writestr('manifest.json', json.dumps(manifest, indent=2) + '\n')
    with ZipFile(args.output) as archive:
        assert archive.testzip() is None
        assert len([n for n in archive.namelist() if n.endswith('.3mf')]) == 8
        assert not any('draft' in n.lower() for n in archive.namelist())
    print('PASS public pack:', args.output, sha256(args.output.read_bytes()).hexdigest())


if __name__ == '__main__':
    main()
