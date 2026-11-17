# SPDX-License-Identifier: MIT
"""Render the current native meshes for the README, including fit overlays."""
import json
import os
import sys
import shutil
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as Patch, Circle
from paths import ROOT
from build_catalog import read_project_mesh
from render_utils import shifted,picture,cylinder
import render_floral_utils as renderer

GOLD=np.array([.76,.55,.23]);WHITE=np.array([.96,.95,.92]);METAL=np.array([.61,.65,.68])
BG=np.array([.965,.956,.934])
renderer.BG=BG
CAT=json.loads((ROOT/'catalog/current.json').read_text())
LIMITS=((-66,-66),(66,66))


def load(record):
    p=ROOT/record['model']
    mat,art,back=[read_project_mesh(p,i) for i in (1,2,4)]
    report=json.loads((ROOT/record['geometry']).read_text())
    rear=[(back,WHITE)]+[(cylinder(3,3,[x,y,1.5]),METAL) for x,y in report['magnet_centers_mm']]
    assembly=shifted([(mat,WHITE),(art,GOLD)],3.6)+picture(record['orientation']=='portrait')+rear
    return assembly,rear,report


def fit(ax,record,report):
    if record['orientation']=='portrait':
        film=[[-27,-47],[27,-47],[27,39],[-27,39]]
    else:film=[[-47,-27],[39,-27],[39,27],[-47,27]]
    ax.add_patch(Patch(film,closed=True,fill=False,edgecolor='#b94f3c',lw=1.65,ls=(0,(4,2.5))))
    for x,y in report['magnet_centers_mm']:
        ax.add_patch(Circle((x,y),3,facecolor='#edf2f2',edgecolor='#355d76',lw=1.2,alpha=.94))
        ax.add_patch(Circle((x,y),.65,color='#355d76'))


def single(record):
    assembly,rear,report=load(record)
    out=ROOT/'renders/current';out.mkdir(parents=True,exist_ok=True)
    # Side turn of 35 degrees from head-on; roll keeps the frame's Y axis
    # vertical on screen, as it would be when mounted on a vertical surface.
    for view,items,elev,azim in [('front',assembly,90,-90),('angle',assembly,55,0),('back',rear,-90,90),('fit',assembly,90,-90)]:
        if os.environ.get('BAROQUE_RENDER_VIEW') not in (None,view):continue
        renderer.BG=np.array([.72,.77,.81]) if view=='back' else BG
        fig,ax=plt.subplots(figsize=(6,6),dpi=150)
        fig.patch.set_facecolor(renderer.BG)
        renderer.render(ax,items,elev,azim,limits=LIMITS if view!='angle' else None,width=850,relief_shadows=True,camera_roll=90 if view=='angle' else 0)
        if view=='fit':fit(ax,record,report)
        titles={'front':'Front','angle':'Upright · 35° side view','back':'Back · three magnet pockets','fit':'Hidden film & magnet positions'}
        ax.set_title(record['name']+'\n'+titles[view],fontsize=15,weight='bold',pad=14)
        if view=='fit':fig.text(.5,.025,'Dashed = full uncut sheet behind the frame',ha='center',fontsize=10)
        fig.subplots_adjust(left=.02,right=.98,top=.88,bottom=.055)
        fig.savefig(ROOT/record['views'][view],facecolor=fig.get_facecolor())
        plt.close(fig)
    print('RENDERED',record['name'],flush=True)


def overview(concealment=False):
    fig,axes=plt.subplots(2,4,figsize=(18,11.3),dpi=170)
    fig.patch.set_facecolor(renderer.BG)
    for ax,r in zip(axes.flat,CAT['frames']):
        assembly,rear,report=load(r)
        renderer.render(ax,assembly,90,-90,limits=LIMITS,width=820,relief_shadows=True)
        if concealment:fit(ax,r,report)
        label=r['name']
        if concealment:label+=f"\n{r['image_visible_percent']:.1f}% of image visible"
        ax.set_title(label,fontsize=13,weight='bold',pad=9)
    title='WHOLE PHOTO, HIDDEN BEHIND THE FRAME' if concealment else 'EIGHT FLORAL INSTAX MINI FRAMES'
    fig.suptitle(title,fontsize=23,weight='bold',y=.975,color='#302c28')
    footer=('Dashed = full uncut 86 × 54 mm sheet · Circles = three concealed magnets\nOverlay shows hidden positions; none of these marks are printed.' if concealment else
            'Actual printable meshes at the same scale · Uncut Instax Mini · Two pieces · Three concealed magnets\nIllustration colors are examples — choose your own print materials.')
    fig.text(.5,.027,footer,ha='center',fontsize=11,color='#4d4943',linespacing=1.5)
    fig.subplots_adjust(left=.012,right=.988,top=.90,bottom=.09,wspace=.015,hspace=.08)
    target=ROOT/'renders'/('Full-film-concealment.png' if concealment else 'Eight-frames-current.png')
    fig.savefig(target,facecolor=fig.get_facecolor());plt.close(fig)
    if concealment:shutil.copy2(target,ROOT/'renders/Eight-frames-film-fit.png')
    if not concealment:shutil.copy2(target,ROOT/'renders/Six-new-frames-actual-fronts.png')
    print('WROTE',target,flush=True)


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='overview':
        overview();overview(True)
    else:
        for r in CAT['frames']:
            if len(sys.argv)==1 or r['slug'] in sys.argv[1:]:single(r)
