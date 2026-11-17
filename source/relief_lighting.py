# SPDX-License-Identifier: MIT
"""Cast shadows and horizon occlusion from the actual 2.5D mesh surface.

The geometry remains unchanged. This is a terrain-style lighting approximation
for front relief views, not a replacement for a full path-tracing renderer.
"""
import numpy as np
from scipy import ndimage as ndi

_CACHE = {}


def terrain(items, width=850):
    key=tuple((len(m.vertices),len(m.faces),tuple(m.bounds.ravel()),float(m.vertices.sum())) for m,_ in items)
    if _CACHE.get('key')==key:
        return _CACHE['terrain']
    vertices=np.concatenate([m.vertices for m,_ in items])
    lo=vertices[:,:2].min(0)-.5;hi=vertices[:,:2].max(0)+.5
    height=max(20,int(width*(hi[1]-lo[1])/(hi[0]-lo[0])))
    zbuf=np.full(width*height,-1e4)
    for m,_ in items:
        t=m.triangles[m.face_normals[:,2]>.0001]
        xy=(t[:,:,:2]-lo)/(hi-lo)*[width,height]
        for first in range(0,len(t),250):
            q=xy[first:first+250];zz=t[first:first+250,:,2]
            mins=np.maximum(np.floor(q.min(1)).astype(int),0)
            maxs=np.minimum(np.ceil(q.max(1)).astype(int),[width-1,height-1])
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
            flat=(py*width+px)[inside]
            dep=(w0*zz[idx,0]+w1*zz[idx,1]+w2*zz[idx,2])[inside]
            np.maximum.at(zbuf,flat,dep)
    z=zbuf.reshape(height,width)
    spacing=(hi-lo)/[width,height]
    # Horizon test over eight directions: deeper cups see less sky.
    occ=np.zeros_like(z)
    for angle in np.linspace(0,2*np.pi,8,endpoint=False):
        horizon=np.zeros_like(z)
        for distance in (.5,1.,2.,4.,8.):
            shift=[-np.sin(angle)*distance/spacing[1],-np.cos(angle)*distance/spacing[0]]
            neighbor=ndi.shift(z,shift,order=1,mode='constant',cval=-1e4,prefilter=False)
            rise=np.maximum(neighbor-z,0)
            horizon=np.maximum(horizon,rise/np.sqrt(distance**2+rise**2))
        occ+=horizon/8
    ao=1-.65*occ
    result=z,lo,hi,spacing,ao
    _CACHE.clear();_CACHE.update(key=key,terrain=result)
    return result


def sampler(items,light):
    z,lo,hi,spacing,ao=terrain(items)
    horizontal=np.linalg.norm(light[:2])
    shadow=np.zeros_like(z)
    if horizontal>.01 and light[2]>.01:
        direction=light[:2]/horizontal
        slope=light[2]/horizontal
        for distance in (.35,.7,1.2,2.,3.5,5.,8.,12.):
            shift=[-direction[1]*distance/spacing[1],-direction[0]*distance/spacing[0]]
            neighbor=ndi.shift(z,shift,order=1,mode='constant',cval=-1e4,prefilter=False)
            shadow=np.maximum(shadow,(neighbor>z+slope*distance+.12).astype(float))
    visibility=1-.86*ndi.gaussian_filter(shadow,1.2)
    def sample(points):
        ix=(points[:,0]-lo[0])/spacing[0]-.5
        iy=(points[:,1]-lo[1])/spacing[1]-.5
        return (ndi.map_coordinates(ao,[iy,ix],order=1,mode='nearest'),
                ndi.map_coordinates(visibility,[iy,ix],order=1,mode='nearest'))
    return sample
