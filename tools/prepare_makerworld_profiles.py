#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Prepare two-color profile candidates and slice locally; never start a print.

These are upload candidates, not a claim of successful physical printing.
Keep each profile unpublished until its matching print photographs are available.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
from pathlib import Path
import re
import shutil
import subprocess
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent.parent
SLICER = '/Applications/BambuStudio.app/Contents/MacOS/BambuStudio'
# Normalized settings of the existing, locally sliced Botanical Garland profile.
PUBLISHED_SETTINGS_SHA256 = '548b4d8024e8c7f4961cab94cf422646905f0539c1dae53f1e1a8d44fd6cf67e'


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def prepare(frame, output):
    source = ROOT / frame['model']
    assert digest(source) == frame['sha256'], frame['slug']
    folder = output / frame['slug']
    folder.mkdir(parents=True, exist_ok=True)
    project = folder / (frame['slug'] + '-P2S-2-Color.3mf')
    with ZipFile(source) as original:
        settings = json.loads(original.read('Metadata/project_settings.config'))
        assert len(settings['filament_colour']) == 3
        # All three supplied material slots are the same PLA. Preserve the two
        # front slots; reassign the back to slot 2 and remove the unused slot.
        for key, value in list(settings.items()):
            if isinstance(value, list) and len(value) == 3:
                settings[key] = value[:2]
            elif (isinstance(value, list) and len(value) > 3 and len(value) % 3 == 0
                  and (len(value) == 9 or key.startswith('filament_'))):
                # Nine-value material/nozzle arrays and explicitly named
                # material blocks. Preserve six-value machine limit arrays.
                size = len(value) // 3
                settings[key] = value[:2*size]
        settings['filament_colour'] = ['#B5B5B5', '#181818']
        settings['flush_volumes_matrix'] = ['0', '170', '170', '0']
        settings['flush_volumes_vector'] = settings['flush_volumes_vector'][:4]
        settings_digest = sha256(json.dumps(settings, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        assert settings_digest == PUBLISHED_SETTINGS_SHA256, 'Unexpected settings change; review before slicing'
        config = ET.fromstring(original.read('Metadata/model_settings.config'))
        for node in config.iter('metadata'):
            if node.get('key') == 'extruder' and node.get('value') == '3':
                node.set('value', '2')
            if node.get('key') == 'filament_maps':
                node.set('value', '1 2')
            if node.get('key') in ('name', 'plater_name') and 'White' in node.get('value', ''):
                node.set('value', node.get('value').replace('White', 'Black'))
        replacements = {
            'Metadata/project_settings.config': json.dumps(settings, indent=2).encode(),
            'Metadata/model_settings.config': ET.tostring(config, encoding='utf-8', xml_declaration=True),
        }
        with ZipFile(project, 'w', ZIP_DEFLATED) as target:
            for info in original.infolist():
                target.writestr(info, replacements.get(info.filename, original.read(info.filename)))
    with ZipFile(source) as original, ZipFile(project) as target:
        assert target.testzip() is None
        assert original.namelist() == target.namelist()
        for name in original.namelist():
            if name not in replacements:
                assert original.read(name) == target.read(name), name
    sliced = folder / 'sliced'
    sliced.mkdir(exist_ok=True)
    with (folder / 'slicer.log').open('w') as log:
        run = subprocess.run([SLICER, '--debug', '1', '--arrange', '0', '--orient', '0',
            '--slice', '0', '--export-3mf', frame['slug'] + '-P2S-Sliced.3mf',
            '--outputdir', str(sliced), str(project)], stdout=log, stderr=subprocess.STDOUT)
    assert run.returncode == 0, (frame['slug'], run.returncode, 'See slicer.log')
    result = json.loads((sliced / 'result.json').read_text())
    assert run.returncode == result['return_code'] == 0, frame['slug']
    plates = result['sliced_plates']
    assert len(plates) == 2
    assert [p['filament_change_times'] for p in plates] == [1, 0]
    assert not any(p.get('warning_message') for p in plates)
    for index in (1, 2):
        gcode = (sliced / f'plate_{index}.gcode').read_text()
        heights = [float(z) for z in re.findall(r'^; Z_HEIGHT: ([\d.]+)', gcode, re.M)]
        assert heights[:8] == [0.2, 0.28, 0.36, 0.44, 0.52, 0.6, 0.68, 0.76]
    # Bambu's full exported project contains editable geometry plus plate
    # thumbnails and slicing metadata that MakerWorld can display immediately.
    upload = folder / (frame['slug'] + '-MakerWorld-Upload.3mf')
    shutil.copyfile(sliced / (frame['slug'] + '-P2S-Sliced.3mf'), upload)
    with ZipFile(upload) as archive:
        assert len([name for name in archive.namelist() if name.endswith('.gcode')]) == 2
        model = ET.fromstring(archive.read('3D/3dmodel.model'))
        ns = {'m': 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
        assert len(model.findall('m:build/m:item', ns)) == 2
    shutil.copyfile(ROOT / frame['views']['front'], folder / 'CAD-preview-not-print-photo.png')
    record = {
        'slug': frame['slug'], 'name': frame['name'], 'source': frame['model'],
        'source_sha256': frame['sha256'], 'project': str(project.relative_to(output)),
        'project_sha256': digest(project), 'geometry_and_placement_unchanged': True,
        'upload_project': str(upload.relative_to(output)), 'upload_sha256': digest(upload),
        'printer': 'Bambu P2S 0.4 mm', 'plates': 2, 'filament_changes': [1, 0],
        'warnings': [], 'estimated_minutes': [round(p['total_predication']/60, 1) for p in plates],
        'material_g': [round(sum(f['total_used_g'] for f in p['filaments']), 2) for p in plates],
        'sliced_sha256': digest(sliced / (frame['slug'] + '-P2S-Sliced.3mf')),
        'settings_match_published_botanical_profile': True,
        'publication_status': ('existing Botanical Garland profile is published; this rebuild not uploaded'
            if frame['slug'] == 'botanical-garland' else 'awaiting matching physical-print photos'),
        'physical_print_verified_by_this_run': False,
        'print_submitted': False,
    }
    (folder / 'validation.json').write_text(json.dumps(record, indent=2) + '\n')
    direction = 'left edge, viewed from the front' if frame['orientation'] == 'landscape' else 'bottom edge'
    description = f"""{frame['name']} · 2 plates · 0.08 mm · reinforced mat

Matching front and three-magnet back for a full, uncut 86 × 54 mm Instax Mini photo.
Plate 1: gray mat, then black ornament; one color change. Plate 2: black back.
Bambu P2S, 0.4 mm nozzle; 0.20 mm first layer, then 0.08 mm; no supports.
The mat is 0.68 mm thick (seven layers). Colors are examples and may be reassigned.
Glue three 6 × 3 mm magnets into the back. Snap together once; optional glue.
Load from the {direction}, narrow-border edge first, wide caption border trailing.
About {frame['image_visible_percent']:.0f}% of the image area remains visible; the film border is hidden from the front.

BEFORE PUBLISHING: add original photos of this exact design printed with these settings,
confirm the two parts assemble and the full film slides in, then remove this preparation note.
The included CAD preview is not physical-print evidence.
"""
    (folder / 'profile-description.txt').write_text(description)
    print('PASS', frame['slug'], record['estimated_minutes'], flush=True)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('slugs', nargs='*', help='Optionally retry specific designs')
    args = parser.parse_args()
    args.output = args.output.resolve()
    frames = json.loads((ROOT / 'catalog/current.json').read_text())['frames']
    chosen = [frame for frame in frames if not args.slugs or frame['slug'] in args.slugs]
    assert chosen, 'No matching catalog design'
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda f: prepare(f, args.output), chosen))
    records = [json.loads((args.output / f['slug'] / 'validation.json').read_text()) for f in frames]
    for record in records:
        assert digest(args.output / record['project']) == record['project_sha256']
    (args.output / 'profile-validation.json').write_text(json.dumps(records, indent=2) + '\n')
    print('Prepared and sliced eight candidates. No uploads or prints started.', flush=True)


if __name__ == '__main__':
    main()
