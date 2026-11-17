# SPDX-License-Identifier: MIT
"""Build a smooth geometric relief field from estimated depth and normals.

Generated grayscale sculpture images are *not* calibrated height maps. A local
monocular depth model supplies broad volumes; screened Poisson integration of
generated normals supplies petal/leaf shape. This remains an estimated 2.5D
surface with explicit CAD construction, not a multi-view 3D reconstruction.
"""
import json
import sys
import os
from pathlib import Path
import numpy as np
from scipy import ndimage as ndi
from PIL import Image
from build_floral_rococo import drawing, aperture_for, choose_geometry
from paths import ROOT


def reconstruct(d):
    rgb, mask, solid, pix, cx, cy, initial_scale = drawing(d)
    outer, _, _, _, _, factor, _, _ = choose_geometry(d, pix, initial_scale, aperture_for(d))
    depth_path = (ROOT/d['depth_file']).with_name(d['id']+'-estimated-depth.npy')
    depth = np.load(depth_path).astype(float)
    assert depth.shape == mask.shape
    yy, xx = np.indices(mask.shape)
    x, y = (xx-cx)*factor, (cy-yy)*factor
    lum = rgb.mean(2)/255
    # Correct low-frequency scene tilt using the dark, low foundation zones.
    ground = mask & (lum>.14) & (lum<.48)
    points = np.c_[np.ones(x.size),x.ravel()/65,y.ravel()/65,
                   (x.ravel()/65)**2,(y.ravel()/65)**2,(x.ravel()*y.ravel()/65**2)]
    eligible = np.flatnonzero(ground.ravel())[::12]
    assert len(eligible)>50
    a, target = points[eligible], depth.ravel()[eligible]
    weights = np.ones(len(target))
    for _ in range(5):
        coeff = np.linalg.lstsq(a*weights[:,None],target*weights,rcond=None)[0]
        residual = target-a@coeff
        sigma = max(np.median(np.abs(residual-np.median(residual)))*1.4826,.02)
        weights = np.minimum(1,1.5*sigma/np.maximum(np.abs(residual),1e-6))
    plane = (points@coeff).reshape(mask.shape)
    relative = ndi.gaussian_filter(depth-plane,.7)
    low, high = np.percentile(relative[mask],[6,99.5])
    signal = np.clip((relative-low)/max(high-low,.01),0,1)
    prior = 1.3 + 9.7*signal**.9
    prior = ndi.gaussian_filter(prior,max(.6,.20/factor))
    prior[~solid] = 0
    if d.get('normal_file'):
        normals = np.asarray(Image.open(ROOT/d['normal_file']).convert('RGB'),float)
        if normals.shape[:2] != mask.shape:
            normals = ndi.zoom(normals,(mask.shape[0]/normals.shape[0],mask.shape[1]/normals.shape[1],1),order=1)
        baseline = np.median(normals[~solid],axis=0)
        n = (normals-127.5)/127.5
        n[:,:,:2] -= (baseline[:2]-127.5)/127.5
        n /= np.maximum(np.linalg.norm(n,axis=2,keepdims=True),1e-5)
        nz = np.maximum(n[:,:,2],.32)
        p = np.clip(-n[:,:,0]/nz,-2.5,2.5)
        q = np.clip(n[:,:,1]/nz,-2.5,2.5)
        p[~mask]=0;q[~mask]=0
        p=ndi.gaussian_filter(p,.7);q=ndi.gaussian_filter(q,.7)
        ky = 2*np.pi*np.fft.fftfreq(mask.shape[0],d=factor)[:,None]
        kx = 2*np.pi*np.fft.fftfreq(mask.shape[1],d=factor)[None,:]
        regularizer = .06
        field = (-1j*kx*np.fft.fft2(p)-1j*ky*np.fft.fft2(q)+regularizer*np.fft.fft2(prior))/(kx*kx+ky*ky+regularizer)
        height = np.fft.ifft2(field).real
    else:
        # A small local emboss term supplies fine veins only; it cannot replace
        # the separately estimated broad flower and scroll geometry.
        detail=ndi.gaussian_filter(lum,.7)-ndi.gaussian_filter(lum,max(1,.6/factor))
        height=prior+.45*detail
    height = ndi.gaussian_filter(height,max(.65,.10/factor))
    height = np.maximum(height,1.301)
    height[~solid] = 1.301
    out=(ROOT/d['depth_file']).with_name(d['id']+'-surface-height.npy')
    np.save(out,height.astype(np.float32))
    report=dict(id=d['id'],method='Estimated relative depth with screened-Poisson normal integration' if d.get('normal_file') else 'Estimated relative depth plus fine vein detail',
        uncalibrated=True,mm_per_pixel=factor,height_percentiles_mm=np.percentile(height[mask],[0,10,50,90,99,100]).tolist(),
        normal_file=d.get('normal_file'),depth_file=str(depth_path.relative_to(ROOT)),
        source_file=d['depth_file'],height_file=str(out.relative_to(ROOT)))
    out.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)


if __name__=='__main__':
    for d in json.loads(Path(os.environ.get('BAROQUE_DESIGNS_FILE',ROOT/'source/designs-floral-rococo.json')).read_text()):
        if len(sys.argv)==1 or d['id'] in sys.argv[1:]:
            reconstruct(d)
