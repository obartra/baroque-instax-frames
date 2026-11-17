# SPDX-License-Identifier: MIT
"""Render the actual meshes, drawings, film concealment and redesigned clips."""
from render_utils import *
from paths import ROOT
from shapely import wkt
from build_catalog import read_project_mesh
from matplotlib.patches import Polygon as Patch
import sys
DS=json.loads((ROOT/'source/designs-final.json').read_text())
def load(d):
 q=P/d['id'];r=json.loads((q/'validation.json').read_text())
 project=P/(d['id']+'-Instax-Mini-3-Magnets.3mf')
 white,black,back=[read_project_mesh(project,n) for n in [1,2,4]]
 front=[(white,WHITE),(black,BLACK)];pic=picture(d['orientation']=='portrait')
 mags=[(cylinder(3,3,[x,y,1.5]),METAL) for x,y in r['magnet_centers_mm']]
 assembly=shifted(front,3.6)+pic+[(back,WHITE)]+mags
 return r,front,pic,[(back,WHITE)]+mags,assembly
def fit(ax,d):
 q=P/d['id'];outer=wkt.loads((q/'outer.wkt').read_text());a=wkt.loads((q/'aperture.wkt').read_text());r=json.loads((q/'validation.json').read_text())
 def patch(g,col,alpha=1,lw=1,edge=None):
  ax.add_patch(Patch(np.asarray(g.exterior.coords),closed=True,facecolor=col,edgecolor=edge or col,alpha=alpha,lw=lw))
 patch(outer,'#302e2b',.16,1,'#302e2b')
 portrait=d['orientation']=='portrait'
 film=np.array([[-27,-47],[27,-47],[27,39],[-27,39],[-27,-47]]) if portrait else np.array([[-47,-27],[39,-27],[39,27],[-47,27],[-47,-27]])
 image=np.array([[-23,-31],[23,-31],[23,31],[-23,31],[-23,-31]]) if portrait else np.array([[-31,-23],[31,-23],[31,23],[-31,23],[-31,-23]])
 ax.plot(*film.T,color='#c45e2b',lw=2,ls='--',label='Full uncut film · hidden')
 ax.plot(*image.T,color='#48738b',lw=1.1,ls=':',label='Image area behind mat')
 patch(a,'#82adc0',.7,1,'#48738b')
 for x,y in r['magnet_centers_mm']:
  ax.add_patch(plt.Circle((x,y),3,color='#9c8749',alpha=.8))
 ax.set_xlim(-68,68);ax.set_ylim(-66,70);ax.set_aspect('equal');ax.axis('off')
 ax.set_title(d['name']+'\n'+f"{r['image_area_visible_percent']:.1f}% image visible · no film exposed",fontsize=11,weight='bold')
 return ax
def individual(d):
 r,front,pic,rear,assembly=load(d)
 exploded=shifted(front,21)+shifted(pic,8)+rear
 fig,ax=plt.subplots(2,3,figsize=(17,11),dpi=170)
 for a,items,el,az,title in [(ax[0,0],assembly,90,-90,'Front · full film concealed'),(ax[0,1],assembly,35,-65,'Actual relief · assembled'),(ax[0,2],assembly,7,-80,'Low angle · layered profile'),(ax[1,0],rear,-90,90,'Back · three flush magnets'),(ax[1,1],exploded,35,-65,'Two parts · film between')]:
  render(a,items,el,az,width=900);a.set_title(title,fontsize=11,weight='bold')
 fit(ax[1,2],d)
 fig.suptitle(d['name'].upper()+' · ACTUAL PRINTABLE MODEL',fontsize=22,weight='bold',y=.98)
 fig.text(.5,.018,'Fresh drawing-guided relief • Even6.5mm white mat,0.36mm high • Longer rounded-root PLA clips • Not physically printed',ha='center',fontsize=10)
 fig.subplots_adjust(top=.91,bottom=.06,left=.025,right=.975,wspace=.12,hspace=.20)
 fig.savefig(O/(d['id']+'-actual-multiview.png'),facecolor=fig.get_facecolor());plt.close(fig)
 fig,ax=plt.subplots(1,3,figsize=(16,7),dpi=160)
 im=Image.open(ROOT/'concepts'/(d['id']+'-concept.png'));arr=np.asarray(im);ax[0].imshow(arr[:,:int(arr.shape[1]*.71)]);ax[0].axis('off');ax[0].set_title('Fresh front drawing · design target',fontsize=12,weight='bold')
 render(ax[1],assembly,width=950);ax[1].set_title('Actual mesh · front',fontsize=12,weight='bold')
 render(ax[2],assembly,35,-65,width=950);ax[2].set_title('Actual mesh · assembled',fontsize=12,weight='bold')
 fig.suptitle(d['name'].upper()+' · DRAWING TO MODEL',fontsize=20,weight='bold',y=.98)
 fig.text(.5,.028,'Concept shading is interpreted as printable bas-relief; mouldings, photo fit and clips are explicit CAD.',ha='center',fontsize=10)
 fig.subplots_adjust(top=.88,bottom=.09,left=.02,right=.98,wspace=.08)
 fig.savefig(O/(d['id']+'-drawing-to-model.png'),facecolor=fig.get_facecolor());plt.close(fig)
 print('Rendered',d['id'],flush=True)
def overview():
 fig,ax=plt.subplots(2,3,figsize=(17,12),dpi=180)
 for a,d in zip(ax.flat,DS):
  r,front,pic,rear,assembly=load(d)
  render(a,assembly,90,-90,limits=([-68,-66],[68,70]),width=1100)
  a.set_title(d['name']+'\n'+f"{r['image_area_visible_percent']:.1f}% of image visible",fontsize=13,weight='bold')
 fig.suptitle('SIX NEW INSTAX MINI FRAMES',fontsize=26,weight='bold',y=.98)
 fig.text(.5,.025,'Actual CAD meshes, common scale • Full uncut film hidden • White inner mats • Three concealed magnets • Redesigned PLA clips',ha='center',fontsize=11)
 fig.subplots_adjust(top=.90,bottom=.065,left=.02,right=.98,hspace=.13,wspace=.06)
 fig.savefig(O/'Six-new-frames-actual-fronts.png',facecolor=fig.get_facecolor());plt.close(fig)
 fig,ax=plt.subplots(2,3,figsize=(16,12),dpi=170)
 for a,d in zip(ax.flat,DS):fit(a,d)
 fig.suptitle('FULL INSTAX MINI SHEET · CONCEALMENT STUDY',fontsize=22,weight='bold',y=.98)
 fig.text(.5,.025,'Orange dashed outline = full film hidden behind frame • Blue = visible image aperture • Gold =6×3mm magnets',ha='center',fontsize=11)
 fig.subplots_adjust(top=.90,bottom=.065,left=.02,right=.98,hspace=.13,wspace=.06)
 fig.savefig(O/'Full-film-concealment.png',facecolor=fig.get_facecolor());plt.close(fig)
 print('Collection sheets complete',flush=True)
if __name__=='__main__':
 if len(sys.argv)>1 and sys.argv[1]=='overview':overview()
 else:
  for d in DS:
   if len(sys.argv)==1 or d['id'] in sys.argv[1:]:individual(d)
