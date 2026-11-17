# SPDX-License-Identifier: MIT
"""Render the unchanged Segmental Arch mesh with a simulated photo texture.

The photograph is a material on a flat plane inside the real assembly. It
does not generate, edit, stretch or replace any of the printable geometry.
"""
import hashlib
import json
import numpy as np
import trimesh as tm
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from paths import ROOT
from build_catalog import read_project_mesh
from render_utils import box, shifted
import render_floral_utils as renderer


def photo_material(path):
    # Use a palette of constant-color triangles as a photo material, allowing
    # the existing actual-mesh renderer to preserve depth and occlusion.
    width=360; height=round(width*62/46)
    image=Image.open(path).convert('RGB').resize((width,height),Image.Resampling.LANCZOS)
    image=image.quantize(colors=256,dither=Image.Dither.NONE)
    pixels=np.asarray(image).ravel(); palette=np.asarray(image.getpalette()).reshape(-1,3)/255.
    xx,yy=np.meshgrid(np.linspace(-23,23,width+1),np.linspace(31,-31,height+1))
    vertices=np.c_[xx.ravel(),yy.ravel(),np.full(xx.size,3.505)]
    row,col=np.indices((height,width));a=(row*(width+1)+col).ravel()
    b=a+1;c=a+width+1;d=c+1
    for color in np.unique(pixels):
        ids=np.flatnonzero(pixels==color)
        faces=np.vstack([np.c_[a[ids],c[ids],b[ids]],np.c_[b[ids],c[ids],d[ids]]])
        mesh=tm.Trimesh(vertices=vertices,faces=faces,process=False)
        mesh.remove_unreferenced_vertices()
        yield mesh,palette[color]


def main():
    record=next(r for r in json.loads((ROOT/'catalog/current.json').read_text())['frames'] if r['slug']=='segmental-arch')
    project=ROOT/record['model'];digest=hashlib.sha256(project.read_bytes()).hexdigest()
    assert digest==record['sha256']
    mat,art,back=[read_project_mesh(project,n) for n in (1,2,4)]
    white=np.array([.96,.95,.92]);gold=np.array([.76,.55,.23])
    items=shifted([(mat,white),(art,gold)],3.6)
    items+=[(back,white),(box([54,86,1.02],[0,-4,2.99]),np.array([.99,.985,.97]))]
    items+=list(photo_material(ROOT/'assets/brand/simulated-coastal-photo.png'))
    renderer.BG=np.array([.965,.956,.934])
    fig,ax=plt.subplots(figsize=(7,7),dpi=180)
    fig.patch.set_facecolor(renderer.BG)
    renderer.render(ax,items,78,0,limits=((-66,-65),(66,70)),width=1400,
                    relief_shadows=True,camera_roll=90,perspective_distance=400)
    fig.subplots_adjust(left=.015,right=.985,bottom=.015,top=.985)
    target=ROOT/'assets/brand/project-icon.png'
    fig.savefig(target,facecolor=fig.get_facecolor());plt.close(fig)
    assert hashlib.sha256(project.read_bytes()).hexdigest()==digest
    print('Rendered actual Segmental Arch mesh:',target,flush=True)


if __name__=='__main__':main()
