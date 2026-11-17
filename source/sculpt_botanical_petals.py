# SPDX-License-Identifier: MIT
"""Trace two existing flowers into explicit, supported CAD petal surfaces.

No raster artwork is edited. Unequal traced outlines, curved short overlap
channels, variable petal heights and low seed disks replace inferred relief
only inside the selected blooms. The outline and mechanical CAD are retained.
"""
import json
import argparse
import numpy as np
from scipy import ndimage as ndi
from scipy.interpolate import splprep, splev, CubicSpline
import shapely

from paths import ROOT
from build_floral_rococo import drawing, aperture_for, choose_geometry

REV = ROOT / 'studies/botanical-sculpture-v3'
PARENT = '16-Rocaille-Botanical-Garland'
ID = PARENT + '-Sculpted-v3'


def smooth(t):
    t = np.clip(t, 0, 1)
    return t*t*(3-2*t)


def angle_delta(a, b):
    return np.arctan2(np.sin(a-b), np.cos(a-b))


FLOWERS = [
    dict(name='upper-left principal open bloom', center=[201, 280],
         outline=[[112,296],[109,277],[118,252],[132,230],[130,218],
                  [143,208],[149,188],[170,170],[189,173],[215,163],
                  [237,168],[253,189],[254,209],[275,220],[292,236],
                  [304,253],[318,266],[323,289],[314,313],[298,332],
                  [276,339],[259,330],[252,353],[238,374],[219,388],
                  [200,392],[188,378],[188,358],[168,367],[145,365],
                  [127,353],[112,343],[109,324],[124,303]],
         # Angles in the drawing's y-down coordinates: five unequal petals.
         seams=[-2.18,-.72,.73,1.76,2.88],
         heights=[2.55,2.25,2.00,1.70,2.20],
         curls=[.94,.75,.90,.65,.82],
         twists=[.08,-.12,.11,-.06,.10],
         base=5.48, seed=[3.0,2.48], seed_lift=.78, phase=.4),
    dict(name='lower-right turned open bloom', center=[1120,846],
         outline=[[1016,813],[1034,793],[1055,797],[1061,774],
                  [1073,751],[1085,743],[1100,750],[1116,746],
                  [1133,751],[1150,774],[1149,795],[1172,786],
                  [1192,788],[1210,794],[1222,811],[1215,825],
                  [1231,843],[1225,861],[1214,876],[1193,881],
                  [1171,871],[1166,890],[1152,903],[1150,915],
                  [1130,922],[1116,927],[1097,920],[1085,900],
                  [1065,893],[1054,872],[1033,873],[1015,866],
                  [1009,848],[1016,827]],
         seams=[-2.50,-1.12,.43,1.99,2.82],
         heights=[2.03,1.60,1.90,2.25,1.76],
         curls=[.76,.68,1.00,.83,.60],
         twists=[-.10,.12,-.08,.10,-.07],
         base=4.98, seed=[2.82,1.92], seed_lift=.70, phase=1.3),
]


def flower_surface(f, xx, yy, old, factor):
    """Continuous petal bowl; all relief is column-supported, no undercuts."""
    xc, yc = f['center']
    points = np.array(f['outline'], float)
    spline, _ = splprep(points.T, s=.15, per=True)
    boundary = np.array(splev(np.linspace(0, 1, 2200, endpoint=False), spline)).T
    theta = np.arctan2(boundary[:,1]-yc, boundary[:,0]-xc)
    radius = np.hypot(boundary[:,0]-xc, boundary[:,1]-yc)*factor
    order = np.argsort(theta)
    theta, radius = theta[order], radius[order]
    # The traced outlines are star-shaped about their seed disks. Work in
    # drawing coordinates to retain each petal's specific pose and silhouette.
    theta = np.r_[theta[-1]-2*np.pi, theta, theta[0]+2*np.pi]
    radius = np.r_[radius[-1], radius, radius[0]]
    a = np.arctan2(yy-yc, xx-xc)
    r = np.hypot(xx-xc, yy-yc)*factor
    R = np.interp(a, theta, radius)
    u = r/np.maximum(R,.01)
    seams = np.array(f['seams'])
    extended = np.r_[seams, seams[0]+2*np.pi]
    ap = (a-seams[0])%(2*np.pi)+seams[0]
    sector = np.clip(np.searchsorted(extended,ap,side='right')-1,0,len(seams)-1)
    lo, hi = extended[sector], extended[sector+1]
    # Bow the overlap grooves. Their roots and outer tips disappear into the
    # surface, avoiding five long radial cuts or a geometric star motif.
    twist = np.array(f['twists'])[sector]
    local = np.clip((ap-lo)/(hi-lo)+twist*np.sin(np.pi*np.clip(u,0,1)),0,1)
    centers=(extended[:-1]+extended[1:])/2
    def periodic_values(values):
        knots=np.r_[centers,centers[0]+2*np.pi]
        return CubicSpline(knots,np.r_[values,values[0]],bc_type='periodic')(
            (a-centers[0])%(2*np.pi)+centers[0])
    amp = periodic_values(f['heights'])
    curl = periodic_values(f['curls'])
    arch = np.sin(np.pi*local)**.65
    bowl = smooth((u-.26)/.66)
    # Broad shoulder, rounded turned lip, then a smooth roll back into the
    # original edge; no thin raised outline or mounting pad is added.
    surface = f['base'] + amp*bowl*(.78+.22*arch)
    surface += curl*np.exp(-((u-(.83+.045*np.cos(np.pi*local)))/.125)**2)*(.55+.45*arch)
    surface -= .70*smooth((u-.91)/.14)
    surface += .17*np.sin(np.pi*local)*np.sin(np.pi*np.clip(u,0,1))
    grooves = np.zeros_like(old)
    for k, seam in enumerate(seams):
        curve = seam + (.08 if k%2 else -.10)*np.sin(np.pi*np.clip((u-.25)/.8,0,1))
        dist = r*np.abs(angle_delta(a,curve))
        taper = smooth((u-.46)/.17)*smooth((1.0-u)/.18)
        grooves += (.38+.06*(k%3))*np.exp(-(dist/.36)**2)*taper
    surface -= grooves
    # Very quiet residual organic grain, not the source's inferred seed spikes.
    grain = ndi.gaussian_filter(old,.15/factor)-ndi.gaussian_filter(old,.55/factor)
    surface += np.clip(grain,-.18,.18)*.32*smooth((u-.38)/.2)
    # Keep one actual outer lip in the flagged sectors. The first test's
    # authored inner crest plus old edge read as nested complete outlines.
    flagged=[(1.0,1.8)] if f['center'][0]<500 else [(-1.8,-.9)]
    rim_cleanup=np.zeros_like(old)
    for left,right in flagged:
        center=(left+right)/2;half=(right-left)/2
        angular=smooth((half+.22-np.abs(angle_delta(a,center)))/.30)
        rim_cleanup=np.maximum(rim_cleanup,angular*smooth((u-.71)/.13))
    edge_old=ndi.gaussian_filter(old,.25/factor)
    surface=surface*(1-rim_cleanup*.86)+edge_old*rim_cleanup*.86
    # A low, continuously joined seed disk with shallow coarse granulation.
    sx,sy=f['seed']
    dx,dy=(xx-xc)*factor,(yy-yc)*factor
    rho=np.sqrt((dx/sx)**2+(dy/sy)**2)
    irregular_rho=rho*(1+.04*np.sin(3*a+f['phase'])+.027*np.cos(5*a-.7))
    seedmask=1-smooth((irregular_rho-.45)/.72)
    # Shallow jittered scales share one connected low mass: no separate balls,
    # wire stamens, rigid spiral or machined crosshatched surface.
    seeds=np.zeros_like(old)
    rng=np.random.default_rng(int(f['center'][0]))
    for j,py in enumerate(np.arange(-sy*.82,sy*.83,.73)):
        for px in np.arange(-sx*.85,sx*.86,.79):
            px+=.35*(j%2)+rng.uniform(-.17,.17)
            pyj=py+rng.uniform(-.15,.15)
            if (px/sx)**2+(pyj/sy)**2>.77:continue
            angle=rng.uniform(-np.pi,np.pi)
            ex,ey=dx-px,dy-pyj
            ex,ey=ex*np.cos(angle)+ey*np.sin(angle),-ex*np.sin(angle)+ey*np.cos(angle)
            scale=rng.uniform(.08,.16)*np.exp(-2*((ex/.39)**2+(ey/.29)**2))
            seeds=np.maximum(seeds,scale)
    seed=f['base']+.36+f['seed_lift']*np.clip(1-(rho*.82)**2,0,1)
    seed+=seeds*smooth((1.03-irregular_rho)/.28)
    surface=surface*(1-seedmask)+seed*seedmask
    weight=smooth((R-r+.30)/1.05)
    return surface,weight,dict(name=f['name'],center_px=f['center'],
        outline_px=f['outline'],unequal_petals=5,base_height_mm=f['base'],
        maximum_authored_height_mm=float(surface[weight>.99].max()),
        seed_disk_diameters_mm=[2*sx,2*sy],groove_width_mm=.72,
        construction='Continuous supported bowl with rounded petal shoulders, curved short channels, low textured disk; no true undercuts')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent-config',default='source/designs-period-eight.json')
    args=parser.parse_args()
    REV.mkdir(parents=True,exist_ok=True)
    original=next(d for d in json.loads((ROOT/args.parent_config).read_text()) if d['id']==PARENT)
    rgb,gold,solid,pix,cx,cy,initial=drawing(original)
    aperture=aperture_for(original)
    outer,positions,_,_,_,factor,_,join=choose_geometry(original,pix,initial,aperture)
    old=np.load(ROOT/original['final_surface_file']).astype(float)
    yy,xx=np.indices(old.shape)
    x,y=(xx-cx)*factor,(cy-yy)*factor
    # The entire mechanically authored inner rail/mat zone is locked.
    rail=aperture.buffer(6.5+1.85,join_style=join)
    protected=shapely.contains_xy(rail,x,y)
    out=old.copy();weights=np.zeros_like(old);features=[]
    for f in FLOWERS:
        new,w,record=flower_surface(f,xx,yy,old,factor)
        w[protected|~gold]=0
        out=out*(1-w)+new*w
        weights=np.maximum(weights,w)
        features.append(record)
    # Mild rounding of the authored geometry at sub-nozzle scale. Preserve
    # everything outside the named patches byte-for-byte in the saved field.
    delta=ndi.gaussian_filter(out-old,.12/factor)
    out=old+delta*smooth(weights/.20)
    out[protected|~gold]=old[protected|~gold]
    # Keep the exact pre-existing roof height wherever it is mechanically
    # required; this is local to the existing four snap lands.
    for px,py in positions:
        core=(np.abs(x-px)<3.0)&(np.abs(y-py)<2.8)
        out[core]=np.maximum(out[core],np.minimum(old[core],5.65))
    assert np.isfinite(out).all() and out.min()>=1.3009 and out.max()<12
    final=REV/(ID+'-final-height.npy')
    np.save(final,out.astype(np.float32))
    report=dict(id=ID,parent=PARENT,method='Explicit traced unequal petal bowls and curved overlap channels in CAD height geometry',
        historical_scope='Modern miniature French Louis XV-inspired composition, ca.1735–1750; not a documented replica',
        features=features,max_height_mm=float(out.max()),
        delta_bounds_mm=[float((out-old).min()),float((out-old).max())],
        changed_surface_area_mm2=float(np.count_nonzero(np.abs(out-old)>.01)*factor**2),
        locked=['outer footprint','60×44 mm photo aperture','6.5 mm even mat','0.36 mm mat thickness',
                'inner moulding','photo channel and four clips','three-magnet back geometry','uncut 86×54 mm film concealment'],
        physical_test=False,glued_clips='Designed for one assembly, then adhesive; repeated snap fatigue is not a release claim',
        iteration='v3: low irregular seed scales with blended edges; quieter duplicate crests in upper-left lower petals and lower-right upper petal')
    record=REV/'refinement.json';record.write_text(json.dumps(report,indent=2)+'\n')
    d=dict(original,id=ID,name='Botanical Garland · Sculpted Petals v3',
           final_surface_file=str(final.relative_to(ROOT)),refinement_record=str(record.relative_to(ROOT)),
           relief_method=report['method'],front_material_label='Black frame / gray mat')
    config=ROOT/'source/designs-botanical-sculpture-v3.json'
    config.write_text(json.dumps([d],indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':main()
