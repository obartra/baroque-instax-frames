# SPDX-License-Identifier: MIT
"""Relief renderer with actual-mesh terrain shadows; legacy renderer unchanged."""
from render_utils import *
def render(ax,items,elev=90,azim=-90,limits=None,width=1200,relief_shadows=False,camera_roll=0,perspective_distance=None,return_buffers=False):
 eye,u,v,T=camera(elev,azim)
 if camera_roll:
  r=np.radians(camera_roll);u,v=np.cos(r)*u-np.sin(r)*v,np.sin(r)*u+np.cos(r)*v
  T=np.vstack([u,v,eye]).T
 light=-.36*u+.48*v+.80*eye;light/=np.linalg.norm(light);half=(light+eye);half/=np.linalg.norm(half)
 shade=None
 if relief_shadows and elev>0:
  from relief_lighting import sampler
  shade=sampler(items,light)
 triangles=[];colors=[]
 for m,base in items:
  n=m.face_normals
  if perspective_distance is None:keep=n@eye>.0001
  else:
   toward_camera=eye*perspective_distance-m.triangles_center
   keep=np.einsum('ij,ij->i',n,toward_camera)>.0001
  t=m.triangles[keep]@T;n=n[keep]
  diffuse=.23+.77*np.maximum(0,n@light)
  ornamental=(np.ptp(base)<.06 and np.mean(base)<.4) or (base[0]>.75 and base[1]<.7 and base[2]<.3)
  if shade is not None and ornamental:
   ao,visibility=shade(m.triangles[keep].mean(1))
   diffuse=.23*ao+.77*np.maximum(0,n@light)*visibility
  spec=np.maximum(0,n@half)**30
  specular=.12 if np.allclose(base,METAL) else .035
  c=np.clip(base[None,:]*diffuse[:,None]+.035+specular*spec[:,None],0,1)
  triangles.append(t);colors.append(c)
 t=np.concatenate(triangles);c=np.concatenate(colors)
 if perspective_distance is not None:
  # Pinhole projection with reciprocal camera distance for the depth buffer.
  # Geometry and assembly thickness remain at their real proportions.
  depth=perspective_distance-t[:,:,2]
  if np.any(depth<=0):raise ValueError('Camera intersects the rendered geometry')
  t[:,:,:2]*=(perspective_distance/depth)[:,:,None]
  t[:,:,2]=1/depth
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

 if return_buffers:
  return dict(rgb=rgb.reshape(height,width,3),depth=zbuf.reshape(height,width),lo=lo,hi=hi,camera=T)
