# SPDX-License-Identifier: MIT
"""Render loading at a rear angle, then orbit to a close front view.

Every orbit view is rasterized from the actual unchanged front/back meshes.
The translating film is a 54 x 86 x 1.02 mm box, depth-tested against them.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
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
CACHE=ROOT/'build/insertion-animation/rear-orbit'
FPS=30
SECONDS=7.2
SIZE=720
BG=np.array([246,244,238])/255
INITIAL_ANGLE=150.0
FINAL_ANGLE=15.0
SCENE=None


def ease(x):
    x=float(np.clip(x,0,1));return x*x*(3-2*x)


def init_scene():
    global SCENE
    record=next(r for r in json.loads((ROOT/'catalog/current.json').read_text())['frames'] if r['slug']=='segmental-arch')
    native=ROOT/record['model'];digest=hashlib.sha256(native.read_bytes()).hexdigest()
    assert digest==record['sha256']
    mat,art,back=[read_project_mesh(native,n) for n in (1,2,4)]
    report=json.loads((ROOT/record['geometry']).read_text())
    white=np.array([.96,.95,.92]);gold=np.array([.76,.55,.23]);metal=np.array([.61,.65,.68])
    objects=shifted([(mat,white),(art,gold)],3.6)+[(back,white)]
    objects += [(cylinder(3,3,[x,y,1.5]),metal) for x,y in report['magnet_centers_mm']]
    texture=np.asarray(Image.open(ROOT/'assets/brand/simulated-coastal-photo.png').convert('RGB'))
    SCENE=(record,native,digest,objects,texture)
    renderer.BG=BG


def buffers(angle):
    fig,ax=plt.subplots()
    data=renderer.render(ax,SCENE[3],90-angle,0,limits=((-140,-190),(140,110)),width=1200,
                         relief_shadows=True,camera_roll=90,return_buffers=True)
    plt.close(fig)
    return data


def compose(data,angle,offset=0):
    static=data['rgb'];depth=data['depth'];lo=data['lo'];hi=data['hi']
    height,width=depth.shape
    xx=lo[0]+(np.arange(width)+.5)*(hi[0]-lo[0])/width
    yy=lo[1]+(np.arange(height)+.5)*(hi[1]-lo[1])/height
    U,Y=np.meshgrid(xx,yy)
    theta=math.radians(angle);sn=math.sin(theta);cs=math.cos(theta)
    # Upright orthographic camera rays, parameterized by distance toward camera.
    origin_x=U*cs;origin_z=-U*sn
    safe_sn=math.copysign(max(abs(sn),1e-10),sn)
    safe_cs=math.copysign(max(abs(cs),1e-10),cs)
    tx1=(-27-origin_x)/safe_sn;tx2=(27-origin_x)/safe_sn
    tz1=(2.485-origin_z)/safe_cs;tz2=(3.505-origin_z)/safe_cs
    near=np.minimum(np.maximum(tx1,tx2),np.maximum(tz1,tz2))
    far=np.maximum(np.minimum(tx1,tx2),np.minimum(tz1,tz2))
    local_y=Y-offset
    visible=(far<=near)&(local_y>=-47)&(local_y<=39)&(near>=depth-1e-6)
    X=origin_x+near*sn;Z=origin_z+near*cs
    front=np.isclose(Z,3.505,atol=1e-6)&visible
    back=np.isclose(Z,2.485,atol=1e-6)&visible
    side=visible&~front&~back
    eye=data['camera'][:,2];u=data['camera'][:,0];v=data['camera'][:,1]
    light=-.36*u+.48*v+.80*eye;light/=np.linalg.norm(light)
    paper=np.array([.99,.985,.97])
    rgb=static.copy()
    front_factor=.23+.77*max(0,float(light[2]))
    for mask,factor in [(front,front_factor),(back,.23+.77*max(0,float(-light[2]))),(side,.23+.77*max(0,float(light[0]*math.copysign(1,sn))))]:
        rgb[mask]=np.clip(paper*factor+.035,0,1)
    image=front&(np.abs(X)<=23)&(np.abs(local_y)<=31)
    texture=SCENE[4]
    rows=np.clip(((31-local_y[image])/62*texture.shape[0]).astype(int),0,texture.shape[0]-1)
    cols=np.clip(((X[image]+23)/46*texture.shape[1]).astype(int),0,texture.shape[1]-1)
    rgb[image]=np.clip(texture[rows,cols]/255*front_factor+.035,0,1)
    return Image.fromarray(np.rint(np.flipud(rgb)*255).astype('uint8'))


def orbit_view(job):
    angle,path=job
    if not path.exists():
        compose(buffers(angle),angle).save(path)
    return path


def crop(image,t):
    zoom=ease((t-3.15)/2.45)
    center_y=-40*(1-zoom)+4*zoom
    half=125*(1-zoom)+67*zoom
    width,height=image.size
    lo=np.array([-140,-190]);hi=np.array([140,110])
    bbox=(((-half-lo[0])/(hi[0]-lo[0]))*width,
          ((hi[1]-(center_y+half))/(hi[1]-lo[1]))*height,
          ((half-lo[0])/(hi[0]-lo[0]))*width,
          ((hi[1]-(center_y-half))/(hi[1]-lo[1]))*height)
    return image.resize((SIZE,SIZE),Image.Resampling.LANCZOS,box=bbox)


def main():
    OUT.mkdir(parents=True,exist_ok=True);CACHE.mkdir(parents=True,exist_ok=True)
    frames=CACHE/'frames';frames.mkdir(exist_ok=True)
    init_scene();record,native,digest,_,_=SCENE
    script_digest=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    key=hashlib.sha256((digest+script_digest+hashlib.sha256((ROOT/'source/render_floral_utils.py').read_bytes()).hexdigest()).encode()).hexdigest()[:16]
    cameras=CACHE/key;cameras.mkdir(exist_ok=True)
    initial_cache=cameras/'initial.npz'
    if initial_cache.exists():data=dict(np.load(initial_cache))
    else:data=buffers(INITIAL_ANGLE);np.savez_compressed(initial_cache,**data)
    angles={}
    for i in range(round(FPS*SECONDS)):
        t=i/FPS
        if t>=3.1:
            angle=round(INITIAL_ANGLE+(FINAL_ANGLE-INITIAL_ANGLE)*ease((t-3.1)/2),4)
            angles[angle]=cameras/f'angle-{angle:.4f}.png'
    jobs=[(angle,path) for angle,path in angles.items() if not path.exists()]
    print(f'Rendering {len(jobs)} actual-mesh orbit views',flush=True)
    with ProcessPoolExecutor(max_workers=3,initializer=init_scene) as pool:
        for n,future in enumerate(as_completed([pool.submit(orbit_view,job) for job in jobs]),1):
            future.result()
            if n%10==0 or n==len(jobs):print(f'Orbit {n}/{len(jobs)}',flush=True)
    first=compose(data,INITIAL_ANGLE,-105)
    loaded=compose(data,INITIAL_ANGLE,0)
    shots={}
    for i in range(round(FPS*SECONDS)):
        t=i/FPS
        if t<.45:im=first
        elif t<2.8:im=compose(data,INITIAL_ANGLE,-105*(1-ease((t-.45)/2.35)))
        elif t<3.1:im=loaded
        else:
            angle=round(INITIAL_ANGLE+(FINAL_ANGLE-INITIAL_ANGLE)*ease((t-3.1)/2),4)
            im=Image.open(angles[angle]).convert('RGB')
        result=crop(im,t)
        encoded=np.asarray(result).copy()
        encoded[np.all(encoded==np.array([246,244,238]),axis=2)]=[249,247,241]
        Image.fromarray(encoded).save(frames/f'{i:04}.png')
        if i in (0,45,87,114,132,180):shots[i]=result.copy()
        if i%30==0:print(f'Composited {i}/{round(FPS*SECONDS)}',flush=True)
    final=Image.open(angles[FINAL_ANGLE]).convert('RGB')
    crop(final,SECONDS).save(OUT/'photo-insertion-poster.png')
    strip=Image.new('RGB',(SIZE*len(shots),SIZE),(246,244,238))
    for n,(_,im) in enumerate(sorted(shots.items())):strip.paste(im,(n*SIZE,0))
    strip.resize((2160,360),Image.Resampling.LANCZOS).save(CACHE/'contact-sheet.png')
    ffmpeg=os.environ.get('FFMPEG') or shutil.which('ffmpeg') or '/opt/homebrew/bin/ffmpeg'
    common=[ffmpeg,'-y','-hide_banner','-loglevel','error','-framerate',str(FPS),'-i',str(frames/'%04d.png'),'-frames:v',str(round(FPS*SECONDS)),'-an']
    subprocess.run(common+['-c:v','libx264','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'photo-insertion.mp4')],check=True)
    subprocess.run(common+['-c:v','libvpx-vp9','-crf','28','-b:v','0','-pix_fmt','yuv420p',str(OUT/'photo-insertion.webm')],check=True)
    assert hashlib.sha256(native.read_bytes()).hexdigest()==digest
    provenance={'model':record['model'],'model_sha256':digest,'geometry_changes':False,
                'camera':{'projection':'orthographic','upright_y_axis':True,'initial_yaw_degrees':INITIAL_ANGLE,'final_yaw_degrees':FINAL_ANGLE,'orbit_start_seconds':3.1,'orbit_end_seconds':5.1,'zoom_end_seconds':5.6},
                'film_mm':[54,86,1.02],'film_z_bounds_mm':[2.485,3.505],'film_y_translation_mm':[-105,0],
                'entry':'from below, narrow border first; wide border trails below','film_fully_seated_seconds':2.8,
                'display_canvas_rgb':[246,244,238],'video_encoding_matte_rgb':[249,247,241],'video_css_blend':'darken against page paper',
                'duration_seconds':SECONDS,'fps':FPS,'image_material':'assets/brand/simulated-coastal-photo.png','render_source':'source/render_insertion_animation.py',
                'occlusion':'Full-thickness film box depth-tested against actual assembled meshes at every orbit view',
                'motion':'Load at a rear three-quarter angle, then turn to the front and move closer. No deformation, overshoot or invented latch.',
                'outputs':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*') if p.suffix in ('.mp4','.webm','.png')}}
    (OUT/'render-record.json').write_text(json.dumps(provenance,indent=2)+'\n')
    print('Wrote actual-mesh rear-to-front insertion demo:',OUT,flush=True)


if __name__=='__main__':main()
