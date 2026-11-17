# SPDX-License-Identifier: MIT
from render_utils import *
from build_catalog import peg,read_project_mesh,inter,box as cbox
from paths import P
fork=peg((0,0))
project=P/'PLA-Clip-Fit-Test.3mf'
w,k,b=[read_project_mesh(project,n) for n in [1,2,4]]
fig,ax=plt.subplots(1,3,figsize=(14,6),dpi=180)
render(ax[0],[(fork,WHITE)],0,-90,limits=([-4,-.5],[4,8.8]),width=800)
ax[0].set_title('New fork · front\nRound-ended slot and flared base',fontsize=11,weight='bold')
render(ax[1],[(fork,WHITE)],22,-65,width=800)
ax[1].set_title('8 mm tip · wider arms\nSmaller locking lip',fontsize=11,weight='bold')
parts=shifted([(w,WHITE),(k,BLACK)],13)+[(b,WHITE)]
render(ax[2],parts,30,-65,width=950)
ax[2].set_title('Fit coupon · two plates\nAbout1 g of material',fontsize=11,weight='bold')
fig.suptitle('MORE FORGIVING PLA CLIPS',fontsize=22,weight='bold',y=.98)
fig.text(.5,.035,'Actual geometry • 1.05 ×2mm arms • 0.7mm slot-end radius • 0.115mm nominal deflection per arm • Physical testing still needed',ha='center',fontsize=10)
fig.subplots_adjust(top=.84,bottom=.10,left=.03,right=.97,wspace=.2)
fig.savefig(O/'PLA-Clip-Details.png',facecolor=fig.get_facecolor());plt.close(fig)
