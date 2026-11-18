# SPDX-License-Identifier: MIT
"""Render a closed camera journey from the poster pose back to that pose.

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
SECONDS=16
SIZE=720
BG=np.array([246,244,238])/255
FRONT_ANGLE=15.0
REAR_ANGLE=150.0
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


def pose(t):
    """Hold, pull back, turn, unload/reload, turn forward, and move closer."""
    if t < 3:
        angle=FRONT_ANGLE
    elif t < 5:
        angle=FRONT_ANGLE+(REAR_ANGLE-FRONT_ANGLE)*ease((t-3)/2)
    elif t < 10.5:
        angle=REAR_ANGLE
    else:
        angle=REAR_ANGLE+(FRONT_ANGLE-REAR_ANGLE)*ease((t-10.5)/2)
    if t < 5.4:
        offset=0
    elif t < 7.4:
        offset=-105*ease((t-5.4)/2)
    elif t < 7.8:
        offset=-105
    elif t < 10:
        offset=-105*(1-ease((t-7.8)/2.2))
    else:
        offset=0
    zoom=1-ease((t-1.2)/1.8) if t < 3 else ease((t-12.5)/2)
    return round(angle,4),offset,zoom


def crop(image,t):
    _,_,zoom=pose(t)
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
    rear_cache=cameras/'rear.npz'
    if rear_cache.exists():data=dict(np.load(rear_cache))
    else:data=buffers(REAR_ANGLE);np.savez_compressed(rear_cache,**data)
    angles={}
    for i in range(round(FPS*SECONDS)):
        t=i/FPS
        angle,_,_=pose(t)
        angles[angle]=cameras/f'angle-{angle:.4f}.png'
    jobs=[(angle,path) for angle,path in angles.items() if not path.exists()]
    print(f'Rendering {len(jobs)} actual-mesh orbit views',flush=True)
    with ProcessPoolExecutor(max_workers=3,initializer=init_scene) as pool:
        for n,future in enumerate(as_completed([pool.submit(orbit_view,job) for job in jobs]),1):
            future.result()
            if n%10==0 or n==len(jobs):print(f'Orbit {n}/{len(jobs)}',flush=True)
    shots={}
    for i in range(round(FPS*SECONDS)):
        t=i/FPS
        angle,offset,_=pose(t)
        if offset:
            im=compose(data,REAR_ANGLE,offset)
        else:
            im=Image.open(angles[angle]).convert('RGB')
        result=crop(im,t)
        result.save(frames/f'{i:04}.png')
        if i in (0,90,162,228,285,360,479):shots[i]=result.copy()
        if i%30==0:print(f'Composited {i}/{round(FPS*SECONDS)}',flush=True)
    # One exact source image supplies the poster and both animation endpoints.
    first=Image.open(frames/'0000.png').convert('RGB')
    last=Image.open(frames/f'{round(FPS*SECONDS)-1:04}.png').convert('RGB')
    assert np.array_equal(np.asarray(first),np.asarray(last))
    first.save(OUT/'photo-insertion-poster.png')
    strip=Image.new('RGB',(SIZE*len(shots),SIZE),(246,244,238))
    for n,(_,im) in enumerate(sorted(shots.items())):strip.paste(im,(n*SIZE,0))
    strip.resize((2160,360),Image.Resampling.LANCZOS).save(CACHE/'contact-sheet.png')
    ffmpeg=os.environ.get('FFMPEG') or shutil.which('ffmpeg') or '/opt/homebrew/bin/ffmpeg'
    common=[ffmpeg,'-y','-hide_banner','-loglevel','error','-framerate',str(FPS),'-i',str(frames/'%04d.png'),'-frames:v',str(round(FPS*SECONDS)),'-an']
    subprocess.run(common+['-c:v','libx264','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'photo-insertion.mp4')],check=True)
    subprocess.run(common+['-c:v','libvpx-vp9','-crf','28','-b:v','0','-pix_fmt','yuv420p',str(OUT/'photo-insertion.webm')],check=True)
    assert hashlib.sha256(native.read_bytes()).hexdigest()==digest
    provenance={'model':record['model'],'model_sha256':digest,'geometry_changes':False,
                'camera':{'projection':'orthographic','upright_y_axis':True,'initial_yaw_degrees':FRONT_ANGLE,'rear_yaw_degrees':REAR_ANGLE,'final_yaw_degrees':FRONT_ANGLE,'zoom_out_seconds':[1.2,3],'turn_back_seconds':[3,5],'turn_front_seconds':[10.5,12.5],'zoom_in_seconds':[12.5,14.5]},
                'film_mm':[54,86,1.02],'film_z_bounds_mm':[2.485,3.505],'film_y_translation_mm':[-105,0],
                'entry':'from below, narrow border first; wide border trails below','film_removal_seconds':[5.4,7.4],'film_insertion_seconds':[7.8,10],'film_fully_seated_seconds':10,
                'display_canvas_rgb':[246,244,238],'video_encoding_matte_rgb':[246,244,238],'video_css_blend':'darken against page paper',
                'poster_matches_first_and_last_source_frames':True,
                'duration_seconds':SECONDS,'fps':FPS,'image_material':'assets/brand/simulated-coastal-photo.png','render_source':'source/render_insertion_animation.py',
                'occlusion':'Full-thickness film box depth-tested against actual assembled meshes at every orbit view',
                'motion':'Start at the poster pose, move back, turn to the rear, remove and reinsert the film, turn forward and move closer to the identical poster pose. No deformation, overshoot or invented latch.',
                'outputs':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*') if p.suffix in ('.mp4','.webm','.png')}}
    (OUT/'render-record.json').write_text(json.dumps(provenance,indent=2)+'\n')
    print('Wrote actual-mesh rear-to-front insertion demo:',OUT,flush=True)


if __name__=='__main__':main()
