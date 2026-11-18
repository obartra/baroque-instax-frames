# SPDX-License-Identifier: MIT
"""Render a wide sharing card from the unchanged current Segmental Arch CAD."""
import hashlib
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from paths import ROOT
from build_catalog import read_project_mesh
from render_utils import box, shifted
from render_project_icon import photo_material
import render_floral_utils as renderer


def main():
    frame = next(f for f in json.loads((ROOT/'catalog/current.json').read_text())['frames']
                 if f['slug'] == 'segmental-arch')
    project = ROOT/frame['model']
    assert hashlib.sha256(project.read_bytes()).hexdigest() == frame['sha256']
    mat, ornament, back = [read_project_mesh(project, n) for n in (1, 2, 4)]
    white = np.array([.96, .95, .92])
    items = shifted([(mat, white), (ornament, np.array([.76, .55, .23]))], 3.6)
    items += [(back, white), (box([54, 86, 1.02], [0, -4, 2.99]), white)]
    items += list(photo_material(ROOT/'assets/brand/simulated-coastal-photo.png'))
    renderer.BG = np.array([246, 244, 238])/255
    fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=renderer.BG)
    ax = fig.add_axes([.51, .055, .47, .90])
    renderer.render(ax, items, 78, 0, limits=((-61, -63), (61, 66)), width=1000,
                    relief_shadows=True, camera_roll=90, perspective_distance=400)
    fig.text(.055, .81, 'FLORAL INSTAX FRAMES', fontsize=12, color='#796039')
    fig.text(.055, .61, 'Instax Mini\nmagnetic frames', fontsize=35,
             fontfamily='DejaVu Serif', color='#292f2c', linespacing=1.3, va='top')
    fig.text(.055, .25, '8 free designs · STL + 3MF', fontsize=18, color='#292f2c')
    fig.text(.055, .17, 'Whole film. Three hidden magnets.', fontsize=14, color='#62675f')
    fig.text(.055, .065, 'Actual CAD render · simulated photo · example colors',
             fontsize=10, color='#62675f')
    target = ROOT/'assets/brand/social-preview.png'
    fig.savefig(target, facecolor=renderer.BG)
    plt.close(fig)
    assert hashlib.sha256(project.read_bytes()).hexdigest() == frame['sha256']
    print('Rendered 1200 × 630 sharing preview:', target, flush=True)


if __name__ == '__main__':
    main()
