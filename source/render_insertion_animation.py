# SPDX-License-Identifier: MIT
"""Actual-mesh photo insertion demo; a cached render/depth buffer per camera.

Only the full film sheet translates. It is depth-tested against the unchanged
assembled frame. The last tiny camera pulse is editorial motion, not a latch.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from paths import ROOT
from build_catalog import read_project_mesh
from render_utils import shifted, cylinder
import render_floral_utils as renderer

OUT=ROOT/'assets/demo'
CACHE=ROOT/'build/insertion-animation'
FPS=30
SECONDS=6.4
SIZE=720
BG=np.array([246,244,238])/255


def ease(x):
    x=np.clip(x,0,1)
    return x*x*(3-2*x)


def main():
    OUT.mkdir(parents=True,exist_ok=True);CACHE.mkdir(parents=True,exist_ok=True)
    frames=CACHE/'frames';frames.mkdir(exist_ok=True)
    record=next(r for r in json.loads((ROOT/'catalog/current.json').read_text())['frames'] if r['slug']=='segmental-arch')
    native=ROOT/record['model'];digest=hashlib.sha256(native.read_bytes()).hexdigest()
    assert digest==record['sha256']
    mat,art,back=[read_project_mesh(native,n) for n in (1,2,4)]
    report=json.loads((ROOT/record['geometry']).read_text())
    white=np.array([.96,.95,.92]);gold=np.array([.76,.55,.23]);metal=np.array([.61,.65,.68])
    objects=shifted([(mat,white),(art,gold)],3.6)+[(back,white)]
    objects += [(cylinder(3,3,[x,y,1.5]),metal) for x,y in report['magnet_centers_mm']]
    renderer.BG=BG
    cache=CACHE/'static-buffers.npz'
    cache_key=hashlib.sha256((digest+'|70,0,90|1200|-140,-190|140,110|'+hashlib.sha256((ROOT/'source/render_floral_utils.py').read_bytes()).hexdigest()).encode()).hexdigest()
    if cache.exists() and (CACHE/'cache-key.txt').exists() and (CACHE/'cache-key.txt').read_text()==cache_key:
        data=dict(np.load(cache))
    else:
        fig,ax=plt.subplots()
        data=renderer.render(ax,objects,70,0,limits=((-140,-190),(140,110)),width=1200,
                             relief_shadows=True,camera_roll=90,return_buffers=True)
        plt.close(fig);np.savez_compressed(cache,**data);(CACHE/'cache-key.txt').write_text(cache_key)
    static=data['rgb'];depth=data['depth'];lo=data['lo'];hi=data['hi']
    height,width=depth.shape
    x=lo[0]+(np.arange(width)+.5)*(hi[0]-lo[0])/width
    y=lo[1]+(np.arange(height)+.5)*(hi[1]-lo[1])/height
    U,V=np.meshgrid(x,y)
    # Camera roll makes V coincide with world Y; the photo's front plane is
    # at the same Z as the other real-mesh catalog renders.
    sin=math.sin(math.radians(20));cos=math.cos(math.radians(20));z=3.505
    X=(U+sin*z)/cos
    photo_depth=sin*X+cos*z
    in_front=photo_depth>=depth-1e-6
    texture=np.asarray(Image.open(ROOT/'assets/brand/simulated-coastal-photo.png').convert('RGB'))
    photo_x=np.clip(((X+23)/46*texture.shape[1]).astype(int),0,texture.shape[1]-1)
    paper_color=np.array([.99,.985,.97])*.846+.035
    shots={}

    def compose(offset):
        local_y=V-offset
        paper=(np.abs(X)<=27)&(local_y>=-47)&(local_y<=39)&in_front
        image=(np.abs(X)<=23)&(np.abs(local_y)<=31)&paper
        rgb=static.copy();rgb[paper]=paper_color
        rows=np.clip(((31-local_y[image])/62*texture.shape[0]).astype(int),0,texture.shape[0]-1)
        rgb[image]=np.clip(texture[rows,photo_x[image]]/255*.846+.035,0,1)
        return Image.fromarray(np.rint(np.flipud(rgb)*255).astype('uint8'))

    first=compose(-105)
    final=compose(0)

    def crop(image,t):
        zoom=float(ease((t-3.0)/.8))
        center_y=-40*(1-zoom)+4*zoom
        half=125*(1-zoom)+70*zoom
        # Small camera-only pulse after arrival; film never overshoots its stop.
        dt=t-3.08
        pulse=.012*math.exp(-dt*7)*math.sin(dt*22) if 0<dt<.55 else 0
        half/=1+pulse
        bbox=(((-half-lo[0])/(hi[0]-lo[0]))*width,
              ((hi[1]-(center_y+half))/(hi[1]-lo[1]))*height,
              (((half)-lo[0])/(hi[0]-lo[0]))*width,
              ((hi[1]-(center_y-half))/(hi[1]-lo[1]))*height)
        return image.resize((SIZE,SIZE),Image.Resampling.LANCZOS,box=bbox)

    for i in range(round(FPS*SECONDS)):
        t=i/FPS
        offset=-105*(1-float(ease((t-.6)/2.45)))
        if t<.6: im=first
        elif t>=3.05: im=final
        else: im=compose(offset)
        result=crop(im,t)
        # Dissolve the view reset instead of showing the film being pulled out.
        if t>5.9:
            result=Image.blend(result,crop(first,0),float(ease((t-5.9)/.5)))
        # YUV video rounding can darken a flat canvas by a level. A slightly
        # brighter encoding matte, blended down with CSS darken, keeps the
        # displayed canvas exactly equal to the page paper.
        encoded=np.asarray(result).copy()
        canvas=np.all(encoded==np.array([246,244,238]),axis=2)
        encoded[canvas]=[249,247,241]
        Image.fromarray(encoded).save(frames/f'{i:04}.png')
        if i in (0,45,75,105,150): shots[i]=result.copy()
        if i%30==0:print(f'Rendered {i}/{round(FPS*SECONDS)}',flush=True)
    crop(final,4.5).save(OUT/'photo-insertion-poster.png')
    strip=Image.new('RGB',(SIZE*len(shots),SIZE),tuple((BG*255).astype(int)))
    for n,(_,im) in enumerate(sorted(shots.items())):strip.paste(im,(n*SIZE,0))
    strip.resize((1800,360),Image.Resampling.LANCZOS).save(CACHE/'contact-sheet.png')
    ffmpeg=os.environ.get('FFMPEG') or shutil.which('ffmpeg') or '/opt/homebrew/bin/ffmpeg'
    common=[ffmpeg,'-y','-hide_banner','-loglevel','error','-framerate',str(FPS),'-i',str(frames/'%04d.png'),'-an']
    subprocess.run(common+['-c:v','libx264','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'photo-insertion.mp4')],check=True)
    subprocess.run(common+['-c:v','libvpx-vp9','-crf','28','-b:v','0','-pix_fmt','yuv420p',str(OUT/'photo-insertion.webm')],check=True)
    assert hashlib.sha256(native.read_bytes()).hexdigest()==digest
    provenance={'model':record['model'],'model_sha256':digest,'geometry_changes':False,'frame_camera':{'elevation':70,'azimuth':0,'roll':90,'projection':'orthographic'},
                'film_mm':[54,86],'photo_plane_z_mm':z,'entry':'from below, narrow border first; wide border trails below','film_y_translation_mm':[-105,0],
                'display_canvas_rgb':[246,244,238],'video_encoding_matte_rgb':[249,247,241],'video_css_blend':'darken against page paper',
                'duration_seconds':SECONDS,'fps':FPS,'image_material':'assets/brand/simulated-coastal-photo.png','render_source':'source/render_insertion_animation.py',
                'occlusion':'Photo plane depth-tested against actual assembled front and matching back meshes',
                'settling_motion':'A 1.2% damped camera pulse is an editorial effect, not a model deformation or a photo latch',
                'outputs':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*') if p.suffix in ('.mp4','.webm','.png')}}
    (OUT/'render-record.json').write_text(json.dumps(provenance,indent=2)+'\n')
    print('Wrote actual-mesh insertion demo:',OUT,flush=True)


if __name__=='__main__':main()
