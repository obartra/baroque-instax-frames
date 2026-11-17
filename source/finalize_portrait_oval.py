# SPDX-License-Identifier: MIT
"""Set the new oval's three PLA colors and render its actual checked meshes.

Run after build_floral_rococo.py with the portrait-oval build/design variables.
This changes project material assignments only; no print is submitted.
"""
import json
import os
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

import numpy as np
from lxml import etree as E

from paths import P
import render_floral_rococo as render
import build_catalog as b


def palette(project):
    with ZipFile(project) as z:
        files = {name: z.read(name) for name in z.namelist()}
    settings = json.loads(files['Metadata/project_settings.config'])
    # The resolved P2S snapshot has two filament rows. Some filament options
    # have three nozzle-variant entries or four/eight drying entries per row.
    # Hardware arrays, notably extruder_ams_count, must keep their own sizes.
    assert len(settings['filament_colour']) == 2
    for key, value in list(settings.items()):
        if not isinstance(value, list):
            continue
        filament_rows = key.startswith('filament_') and len(value) >= 2 and len(value) % 2 == 0
        simple_rows = len(value) == 2 and key not in ('extruder_ams_count', 'start_end_points')
        variant_rows = key in ('nozzle_temperature', 'nozzle_temperature_initial_layer',
                               'slow_down_min_speed', 'volumetric_speed_coefficients')
        if filament_rows or simple_rows or variant_rows:
            settings[key] = value + value[:len(value)//2]
    settings['filament_colour'] = ['#B5B5B5', '#181818', '#F5F2EA']
    settings['filament_self_index'] = ['1'] * 3 + ['2'] * 3 + ['3'] * 3
    settings['flush_volumes_matrix'] = [str(0 if a == c else 170) for a in range(3) for c in range(3)]
    settings['flush_volumes_vector'] = ['140'] * 6
    config = E.fromstring(files['Metadata/model_settings.config'])
    for obj in config.findall('object'):
        if obj.get('id') == '5':
            obj.find("metadata[@key='extruder']").set('value', '3')
        for part in obj.findall('part'):
            if part.get('id') == '1':
                height=max(b.read_project_mesh(project,1).vertices[:,2])
                part.find("metadata[@key='name']").set('value', f'Internal mat, {height:.2f} mm')
            elif part.get('id') == '4':
                part.find("metadata[@key='extruder']").set('value', '3')
    for plate in config.findall('plate'):
        index = plate.find("metadata[@key='plater_id']").get('value')
        plate.find("metadata[@key='plater_name']").set('value',
            'Gray mat then black front' if index == '1' else 'White back, three magnets')
        plate.find("metadata[@key='filament_maps']").set('value', '1 2 3')
    files['Metadata/project_settings.config'] = json.dumps(settings, indent=2).encode()
    files['Metadata/model_settings.config'] = E.tostring(config, xml_declaration=True, encoding='UTF-8')
    temp = project.with_suffix('.palette.3mf')
    with ZipFile(temp, 'w', ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data)
    with ZipFile(temp) as z:
        assert z.testzip() is None
    temp.replace(project)


def main():
    for design in render.DS:
        project = P / (design['id'] + '-Instax-Mini-3-Magnets.3mf')
        palette(project)
        white, black, back = [b.read_project_mesh(project, n) for n in (1, 2, 4)]
        fused = b.check(b.union([white, black]), 'single multicolor front')
        assert fused.is_volume
        report = json.loads((P / design['id'] / 'validation.json').read_text())
        report.update(clear_aperture_preserved=True, fused_front_single_volume=True,
                      print_profile_filaments=3, colors=['gray mat', 'black ornament', 'white back'])
        for path in (P/design['id']/'validation.json', P/'validation'/(design['id']+'-geometry.json')):
            path.write_text(json.dumps(report, indent=2)+'\n')
        if os.environ.get('BAROQUE_SKIP_RENDER')=='1':
            print('FINALIZED', project, flush=True)
            continue
        original_load = render.load
        def gray_mat(d):
            report, front, pic, rear, assembly, gilt = original_load(d)
            gray = np.array([.69, .69, .69])
            front[0] = (front[0][0], gray)
            assembly = render.shifted(front, b.MATE) + pic + rear
            gilt = render.shifted([(front[0][0], gray), (front[1][0], render.GOLD)], b.MATE) + pic + rear
            return report, front, pic, rear, assembly, gilt
        render.load = gray_mat
        render.individual(design)
        render.load = original_load
        print('FINALIZED', project, flush=True)


if __name__ == '__main__':
    main()
