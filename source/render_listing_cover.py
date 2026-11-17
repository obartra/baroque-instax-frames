# SPDX-License-Identifier: MIT
"""Render the actual Segmental Arch for model-library covers."""
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
    r=next(r for r in json.loads((ROOT/'catalog/current.json').read_text())['frames'] if r['slug']=='segmental-arch')
    p=ROOT/r['model']
    assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256']
    mat,art,back=[read_project_mesh(p,n) for n in (1,2,4)]
    white=np.array([.96,.95,.92]);gold=np.array([.76,.55,.23])
    items=shifted([(mat,white),(art,gold)],3.6)
    items += [(back,white),(box([54,86,1.02],[0,-4,2.99]),np.array([.99,.985,.97]))]
    items += list(photo_material(ROOT/'assets/brand/simulated-coastal-photo.png'))
    renderer.BG=np.array([246,244,238])/255
    fig=plt.figure(figsize=(8,8),dpi=180,facecolor=renderer.BG)
    ax=fig.add_axes([.08,.09,.84,.79])
    renderer.render(ax,items,78,0,limits=((-61,-61),(61,64)),width=1400,
                    relief_shadows=True,camera_roll=90,perspective_distance=400)
    fig.text(.5,.955,'ROCOCO INSTAX MINI FRAMES',ha='center',fontsize=23,
             fontweight='bold',color='#292f2c')
    fig.text(.5,.916,'8 designs  ·  Whole photos  ·  Three concealed magnets',
             ha='center',fontsize=12,color='#62675f')
    fig.text(.5,.042,'CAD render · simulated photo · example colors',ha='center',
             fontsize=10,color='#62675f')
    out=ROOT/'publishing/media';out.mkdir(parents=True,exist_ok=True)
    fig.savefig(out/'01-cover.png',facecolor=renderer.BG)
    fig.set_size_inches(10.6666667,8)
    fig.savefig(out/'01-cover-landscape.png',facecolor=renderer.BG)
    fig.set_size_inches(8,10.6666667)
    fig.savefig(out/'01-cover-portrait.png',facecolor=renderer.BG)
    plt.close(fig)
    assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256']
    print('Rendered listing cover from current native mesh',flush=True)


if __name__=='__main__':main()
