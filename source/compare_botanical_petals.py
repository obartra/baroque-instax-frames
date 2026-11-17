# SPDX-License-Identifier: MIT
"""Identical cameras for old and new actual project meshes, including blooms."""
import numpy as np
import os
from paths import ROOT, P
from build_catalog import read_project_mesh
from render_utils import plt, picture, shifted
from render_floral_utils import render

OLD='16-Rocaille-Botanical-Garland'
NEW=os.environ.get('BAROQUE_COMPARE_ID',OLD+'-Sculpted-v3')
GOLD=np.array([.82,.57,.22]);BLACK=np.array([.22,.23,.24]);GRAY=np.full(3,.69)


def items(root,did,color):
    f=root/(did+'-Instax-Mini-3-Magnets.3mf')
    gray,black=[read_project_mesh(f,i) for i in (1,2)]
    return shifted([(gray,GRAY),(black,color)],3.6)+picture(False)


def main():
    out=P/'renders';out.mkdir(exist_ok=True)
    before=ROOT/'build/period-catalog-six'
    fig,axes=plt.subplots(3,2,figsize=(13,17),dpi=160)
    views=[(BLACK,90,-90,([-60,-49],[61,54]),'Full frame · black / gray'),
           (GOLD,90,-90,([-51,21],[-24,48]),'Upper-left bloom · inspection material'),
           (GOLD,90,-90,([33,-32],[58,-9]),'Lower-right bloom · inspection material')]
    for col,(root,did,label) in enumerate([(before,OLD,'Previous'),(P,NEW,'Sculpted petals')]):
        for row,(color,elev,azim,limits,title) in enumerate(views):
            render(axes[row,col],items(root,did,color),elev,azim,limits=limits,width=1150,relief_shadows=True)
            axes[row,col].set_title(label+' · '+title,fontsize=12,weight='bold')
    fig.suptitle('BOTANICAL GARLAND · ACTUAL CAD BEFORE / AFTER',fontsize=20,weight='bold',y=.98)
    fig.text(.5,.017,'Same scale, cameras and lighting per row · Height geometry edited, artwork unchanged · No physical test yet',ha='center',fontsize=10)
    fig.subplots_adjust(top=.947,bottom=.04,left=.025,right=.975,wspace=.06,hspace=.08)
    fig.savefig(out/'Botanical-Garland-Before-After.png',facecolor=fig.get_facecolor())
    plt.close(fig)
    print('COMPARISON COMPLETE',flush=True)


if __name__=='__main__':main()
