# SPDX-License-Identifier: MIT
"""Actual-mesh product renders with a fixed-size illustrative Instax sheet."""
from pathlib import Path
import json
import numpy as np,trimesh as tm
from shapely.geometry import Polygon
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from paths import P
O=P/'renders';O.mkdir(exist_ok=True)
BG=np.array([.9294,.9098,.8745]);BLACK=np.array([.16,.17,.18]);WHITE=np.array([.95,.945,.925]);PAPER=np.array([.99,.985,.97]);METAL=np.array([.60,.65,.69])
plt.rcParams.update({'font.family':'DejaVu Sans','figure.facecolor':'#ede8df','axes.facecolor':'#ede8df','text.color':'#302c27'})
def box(ext,center):
 m=tm.creation.box(ext);m.apply_translation(center);return m
def cylinder(r,h,center):
 m=tm.creation.cylinder(r,h,sections=128);m.apply_translation(center);return m
def poly(points,z,col):
 m=tm.creation.extrude_polygon(Polygon(points),.002,engine='earcut');m.apply_translation([0,0,z]);return m,np.array(col)
def photo():
 # Same full paper sheet and same undistorted landscape illustration in all
 # four frames. Its edges are physically occluded by each real mat/ornament.
 items=[(box([86,54,1.02],[-4,0,2.99]),PAPER),(box([62,46,.01],[0,0,3.505]),np.array([.46,.65,.76]))]
 items.append(poly([(-31,-23),(-31,-7),(-18,8),(-3,-8),(8,3),(31,-16),(31,-23)],3.511,[.24,.43,.36]))
 items.append((cylinder(4,.002,[18,12,3.515]),np.array([.93,.77,.46])))
 return items
def shifted(items,amount):
 out=[]
 for m,c in items:
  q=m.copy();q.apply_translation([0,0,amount]);out.append((q,c))
 return out
def camera(elev,azim):
 e,a=np.radians(elev),np.radians(azim)
 eye=np.array([np.cos(e)*np.cos(a),np.cos(e)*np.sin(a),np.sin(e)])
 u=np.array([-np.sin(a),np.cos(a),0]);v=np.cross(eye,u)
 return eye,u,v,np.vstack([u,v,eye]).T
def extent(items,elev,azim):
 T=camera(elev,azim)[3];p=np.concatenate([m.vertices@T for m,_ in items])[:,:2]
 return p.min(0),p.max(0)
def render(ax,items,elev=90,azim=-90,limits=None,width=1200):
 eye,u,v,T=camera(elev,azim);light=-.36*u+.48*v+.80*eye;light/=np.linalg.norm(light);half=(light+eye);half/=np.linalg.norm(half)
 triangles=[];colors=[]
 for m,base in items:
  n=m.face_normals;keep=n@eye>.0001;t=m.triangles[keep]@T;n=n[keep]
  diffuse=.23+.77*np.maximum(0,n@light)
  spec=np.maximum(0,n@half)**30
  specular=.12 if np.allclose(base,METAL) else .035
  c=np.clip(base[None,:]*diffuse[:,None]+.035+specular*spec[:,None],0,1)
  triangles.append(t);colors.append(c)
 t=np.concatenate(triangles);c=np.concatenate(colors)
 if limits is None:
  pts=t[:,:,:2].reshape(-1,2);lo=pts.min(0)-1;hi=pts.max(0)+1
 else:lo=np.array(limits[0],float);hi=np.array(limits[1],float)
 height=max(20,int(width*(hi[1]-lo[1])/(hi[0]-lo[0])))
 xy=(t[:,:,:2]-lo)/(hi-lo)*np.array([width,height])
 zbuf=np.full(width*height,-np.inf);rgb=np.tile(BG,(width*height,1))
 for first in range(0,len(t),350):
  q=xy[first:first+350];zz=t[first:first+350,:,2];cc=c[first:first+350]
  mins=np.maximum(np.floor(q.min(1)).astype(int),0);maxs=np.minimum(np.ceil(q.max(1)).astype(int),[width-1,height-1])
  dims=np.maximum(maxs-mins+1,0);counts=dims[:,0]*dims[:,1]
  starts=np.cumsum(counts)-counts;idx=np.repeat(np.arange(len(q)),counts)
  if not len(idx):continue
  offsets=np.arange(len(idx))-np.repeat(starts,counts)
  px=mins[idx,0]+offsets%dims[idx,0];py=mins[idx,1]+offsets//dims[idx,0]
  x=px+.5;y=py+.5;v=q[idx]
  den=(v[:,1,1]-v[:,2,1])*(v[:,0,0]-v[:,2,0])+(v[:,2,0]-v[:,1,0])*(v[:,0,1]-v[:,2,1])
  safe=np.where(abs(den)<1e-12,1e-12,den)
  w0=((v[:,1,1]-v[:,2,1])*(x-v[:,2,0])+(v[:,2,0]-v[:,1,0])*(y-v[:,2,1]))/safe
  w1=((v[:,2,1]-v[:,0,1])*(x-v[:,2,0])+(v[:,0,0]-v[:,2,0])*(y-v[:,2,1]))/safe
  w2=1-w0-w1;inside=(np.minimum(np.minimum(w0,w1),w2)>=-1e-8)&(abs(den)>1e-12)
  flat=(py*width+px)[inside];dep=(w0*zz[idx,0]+w1*zz[idx,1]+w2*zz[idx,2])[inside];ids=idx[inside]
  np.maximum.at(zbuf,flat,dep);nearest=abs(dep-zbuf[flat])<1e-8;rgb[flat[nearest]]=cc[ids[nearest]]
 ax.imshow(rgb.reshape(height,width,3),extent=(lo[0],hi[0],lo[1],hi[1]),origin='lower',interpolation='none')
 ax.set_aspect('equal');ax.axis('off')

from PIL import Image
def picture(portrait):
 if not portrait:return photo()
 a=[(box([54,86,1.02],[0,-4,2.99]),PAPER),(box([46,62,.01],[0,0,3.505]),np.array([.46,.65,.76]))]
 a.append(poly([(-23,-31),(-23,-4),(-12,9),(-2,-6),(8,3),(23,-15),(23,-31)],3.511,[.24,.43,.36]))
 a.append((cylinder(4,.002,[10,18,3.515]),np.array([.93,.77,.46])))
 return a
