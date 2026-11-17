# SPDX-License-Identifier: MIT
"""Fresh text-drawn ornament, exact photo geometry and redesigned PLA clips.
No ornamental mesh or reference photograph from the earlier collection is read.
Only a resolved Bambu printer/process/filament settings snapshot is reused.
"""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from lxml import etree as E
import json,sys,uuid
import numpy as np, trimesh as tm, shapely
from PIL import Image
from scipy import ndimage as ndi
from scipy.interpolate import RegularGridInterpolator
from shapely.geometry import Polygon,Point,box as rect,LineString
from shapely.affinity import rotate as protate
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from paths import ROOT, P
NS='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
PROD='http://schemas.microsoft.com/3dmanufacturing/production/2015/06'
REL='http://schemas.openxmlformats.org/package/2006/relationships'
POS=[(x,y) for x in [-40.,40.] for y in [-32.5,32.5]]
RECT_POS=[(x,y) for x in [-44.,44.] for y in [-36.,36.]]
MATE=3.6
def box(x,y,z,z0=0,xy=(0,0)):
 m=tm.creation.box([x,y,z]);m.apply_translation([*xy,z0+z/2]);return m
def union(ms):return tm.boolean.union(ms,engine='manifold')
def diff(a,b):return tm.boolean.difference([a,b],engine='manifold')
def inter(a,b):
 if not len(a.faces) or not len(b.faces):return tm.Trimesh()
 return tm.boolean.intersection([a,b],engine='manifold')
def check(m,name):
 parts=[q for q in m.split(only_watertight=False) if abs(q.volume)>1e-6]
 assert len(parts)==1,(name,'components',len(parts))
 m=parts[0];assert m.is_watertight and m.is_volume,name;return m
def extrude(p,z,h):
 if hasattr(p,'geoms'):return union([extrude(q,z,h) for q in p.geoms if q.area>1e-6])
 m=tm.creation.extrude_polygon(p,h,engine='earcut');m.apply_translation([0,0,z]);return m
def cyl(x,y,r,z,h):
 m=tm.creation.cylinder(r,h,sections=96);m.apply_translation([x,y,z+h/2]);return m
def taper(w0,w1,depth,z0,z1,xy):
 m=box(1,depth,z1-z0,z0);m.vertices[:,0]*=w0+(w1-w0)*(m.vertices[:,2]-z0)/(z1-z0);m.apply_translation([*xy,0]);return m
def rounded_rect(x0,y0,x1,y1,r):
 return rect(x0+r,y0+r,x1-r,y1-r).buffer(r,quad_segs=24)
def rotate_mesh(m,portrait):
 m=m.copy()
 if portrait:m.apply_transform(tm.transformations.rotation_matrix(np.pi/2,[0,0,1]))
 return m
def peg(p):
 # Wider fork, longer flex arms, shallower retention lip; round-ended slot.
 stem=union([box(3.5,2,6.75,0,p),box(3.88,2,.25,6.75,p),taper(3.88,2.85,2,7,8,p),taper(4.5,3.5,2.6,.4,1.2,p)])
 end=tm.creation.cylinder(.7,3.2,sections=64)
 end.apply_transform(tm.transformations.rotation_matrix(np.pi/2,[1,0,0]));end.apply_translation([*p,1.7])
 slot=union([end,box(1.4,3.2,6.5,1.7,p)])
 return diff(stem,slot)
def socket(p):
 return union([taper(4.1,3.65,2.4,-.02,.4,p),box(3.65,2.4,2.62,.38,p),box(4.3,2.4,1.7,3,p)])
def aperture_for(d):
 w,h=d['opening'];a,b=w/2,h/2
 if d['shape']=='octagon':
  c=5.;return Polygon([(-a+c,-b),(a-c,-b),(a,-b+c),(a,b-c),(a-c,b),(-a+c,b),(-a,b-c),(-a,-b+c)])
 if d['shape']=='cushion':return rounded_rect(-a,-b,a,b,7.0)
 if d['shape']=='arch':
  # Shallow circular segment; only upper corners are masked.
  rise=3.5;R=(a*a+rise*rise)/(2*rise);yc=b-R
  xs=np.linspace(a,-a,257);ys=yc+np.sqrt(R*R-xs*xs)
  return Polygon([(-a,-b),(a,-b),(a,b-rise)]+list(zip(xs,ys))+[(-a,b-rise)])
 return rect(-a,-b,a,b)
def get_drawing(d):
 rgb=np.asarray(Image.open(ROOT/'concepts'/(d['id']+'-concept.png')).convert('RGB'),float)
 # Geometry preprocessing only: isolate the master front, leaving the sheet intact.
 rgb=rgb[:,:int(rgb.shape[1]*.71)]
 r,g,b=rgb.transpose(2,0,1);blue=(b-r>15)&(g-r>8)&(r>90)&(r<230)&(b>150)
 lab,_=ndi.label(blue);sz=np.bincount(lab.ravel());sz[0]=0;blue=lab==sz.argmax()
 ys,xs=np.nonzero(blue);cx=(xs.min()+xs.max())/2;cy=(ys.min()+ys.max())/2
 dark=(rgb.max(2)<165)&(np.abs(b-r)<22)
 lab,_=ndi.label(dark);sz=np.bincount(lab.ravel());sz[0]=0;dark=lab==sz.argmax()
 solid=ndi.binary_fill_holes(dark)
 fig,ax=plt.subplots();loops=ax.contour(solid.astype(float),levels=[.5]).allsegs[0];plt.close(fig)
 poly=max([Polygon(np.c_[q[:,0]-cx,cy-q[:,1]]).buffer(0) for q in loops if len(q)>8],key=lambda q:q.area)
 return rgb,dark,solid,poly,cx,cy
def moulding(aperture,join_style=1,profile=None):
 # Same polar rays for every parallel offset, so profiles follow each aperture.
 N=1024;t=np.linspace(0,2*np.pi,N,endpoint=False)
 rays=[LineString([(0,0),(250*np.cos(a),250*np.sin(a))]) for a in t]
 if profile is None:profile=[(0,1.8),(.35,1.8),(.7,2.35),(1.1,2.65),(1.5,2.35),(1.9,1.95),(2.3,1.95),(2.7,2.4),(3.2,3.15),(3.7,3.55),(4.25,3.25),(4.8,2.45),(5.4,1.301)]
 vv=[]
 for off,z in profile:
  shape=aperture.buffer(6.5+off,join_style=join_style)
  pts=[list(shape.boundary.intersection(ray).coords)[0] for ray in rays]
  vv.extend(np.c_[pts,np.full(N,z)])
 vv.extend(np.c_[np.asarray(vv[:N])[:,:2],np.full(N,1.3)])
 vv.extend(np.c_[np.asarray(vv[(len(profile)-1)*N:len(profile)*N])[:,:2],np.full(N,1.3)])
 ff=[]
 def strip(i,j):
  for k in range(N):
   l=(k+1)%N;ff.extend([[i*N+k,i*N+l,j*N+l],[i*N+k,j*N+l,j*N+k]])
 for i in range(len(profile)-1):strip(i,i+1)
 strip(len(profile),0);strip(len(profile)-1,len(profile)+1);strip(len(profile)+1,len(profile))
 m=tm.Trimesh(np.asarray(vv),np.asarray(ff));m.fix_normals();return check(m,'moulding')
def back_geometry(portrait,outer,centers,base_positions=None):
 # Fresh CAD from primitives. Only functional measurements carry forward.
 carrier=rect(-47.15,-35,43.15,35)
 channel=rect(-55,-27.15,39.15,27.15)
 lip=carrier.difference(rect(-55,-25.55,35.8,25.55))
 wall=carrier.difference(channel)
 base_positions=POS if base_positions is None else base_positions
 tabs=[extrude(rounded_rect(x-3.6,y-3.8,x+3.6,y+3.8,1.5),0,3.6) for x,y in base_positions]
 base=union([extrude(lip,0,2.4),extrude(wall,0,3.6)]+tabs)
 base=diff(base,union([box(5.6,3.25,2.5,1.2,p) for p in base_positions]))
 base=union([base]+[peg(p) for p in base_positions])
 moats=[];springs=[]
 for sx in [-1,1]:
  for sy in [-1,1]:
   area=rounded_rect(sx*18.25-7.55,sy*28.1-1.9,sx*18.25+7.55,sy*28.1+1.9,.85)
   moats.append(extrude(area,-.02,3.65))
   beam=box(15,.95,3.4,0,(sx*18.5,sy*27.9))
   tip=Point(sx*11.5,sy*27.65).buffer(1,quad_segs=32)
   from shapely.affinity import scale
   tip=scale(tip,1.15,.8,origin=(sx*11.5,sy*27.65))
   springs.append((sx,sy,union([beam,extrude(tip,0,3.4)])))
 body=check(diff(base,union(moats)),'back body')
 body=rotate_mesh(body,portrait);springs=[(sx,sy,rotate_mesh(m,portrait)) for sx,sy,m in springs]
 def connect(p):
  x,y=p
  if portrait:
   if y>40:return rect(-4.6,39.15,4.6,y)
   return rect(min(x,0),y-4.6,max(x,0),y+4.6)
  return rect(x-4.6,min(y,0),x+4.6,max(y,0))
 # Connect only to carrier edge, never across the image channel at film height.
 for x,y in centers:
  if portrait:
   strap=rect(-4.6,39.15,4.6,y) if y>40 else (rect(x,y-4.6,-27.15,y+4.6) if x<0 else rect(27.15,y-4.6,x,y+4.6))
  else:
   strap=rect(x-4.6,27.15,x+4.6,y) if y>0 else rect(x-4.6,y,x+4.6,-27.15)
  body=union([body,extrude(strap.union(Point(x,y).buffer(4.6,quad_segs=48)),0,3.6)])
  body=diff(body,cyl(x,y,3.15,-.02,3.12))
 # Bosses and compact snap lands must not refill the sliding film channel.
 # Keep their supporting lip below the film, in both orientations. The fork
 # stems themselves remain outside this channel and retain their full roots.
 filmchannel=rect(-27.15,-55,27.15,39.15) if portrait else rect(-55,-27.15,39.15,27.15)
 body=diff(body,extrude(filmchannel,2.4,1.21))
 clip=extrude(outer.buffer(-.5),-.05,10)
 body=check(inter(body,clip),'concealed body')
 back=check(union([body]+[inter(m,clip) for _,_,m in springs]),'back')
 loaded=[]
 for sx,sy,m in springs:
  q=rotate_mesh(m,False);v=q.vertices.copy()
  if portrait:v[:,[0,1]]=np.c_[v[:,1],-v[:,0]]
  t=np.clip((25.8-np.abs(v[:,0]))/14.3,0,1);v[:,1]+=sy*.26*t*t*(3-2*t)
  if portrait:v[:,[0,1]]=np.c_[-v[:,1],v[:,0]]
  q.vertices=v;loaded.append(inter(q,clip))
 loaded=check(union([body]+loaded),'loaded back')
 return back,loaded
def write_mesh(m,num):
 root=E.Element('model',nsmap={None:NS},unit='millimeter');res=E.SubElement(root,'resources');o=E.SubElement(res,'object',id=str(num),type='model');mesh=E.SubElement(o,'mesh')
 vs=E.SubElement(mesh,'vertices');fs=E.SubElement(mesh,'triangles')
 for v in m.vertices:E.SubElement(vs,'vertex',**dict(zip(['x','y','z'],[f'{q:.9g}' for q in v])))
 for f in m.faces:E.SubElement(fs,'triangle',**dict(zip(['v1','v2','v3'],map(str,f))))
 E.SubElement(root,'build')
 return E.tostring(root,xml_declaration=True,encoding='UTF-8')
def read_project_mesh(path,num):
 with ZipFile(path) as z:root=E.fromstring(z.read(f'3D/Objects/object_{num}.model'))
 vs=[[float(v.get(k)) for k in ['x','y','z']] for v in root.findall('.//{'+NS+'}vertex')]
 fs=[[int(f.get(k)) for k in ['v1','v2','v3']] for f in root.findall('.//{'+NS+'}triangle')]
 return tm.Trimesh(vs,fs,process=False)
def write_project(d,white,black,back):
 uid=lambda:str(uuid.uuid4())
 root=E.Element('model',nsmap={None:NS,'p':PROD,'BambuStudio':'http://schemas.bambulab.com/package/2021'},unit='millimeter',requiredextensions='p')
 for name,value in [('Application','BambuStudio-02.09.01.70'),('BambuStudio:3mfVersion','1'),('Title',d.get('project_title',d['name']+' — independent Instax Mini frame')),('Description',d.get('project_description','Fresh AI concept drawing interpreted as relief; original custom CAD photo channel and rounded-root PLA forks. Uncut Instax Mini,3 concealed magnets.')),('Provenance',d.get('project_provenance','No original MakerWorld mesh or collection photograph used for this design. Historical descriptive vocabulary and fresh drawings. See PROVENANCE.txt.'))]:
  E.SubElement(root,'metadata',name=name).text=value
 res=E.SubElement(root,'resources');build=E.SubElement(root,'build');config=E.Element('config');rel=E.Element('Relationships',nsmap={None:REL})
 for objid,parts,title,tx,plate in [(3,[(1,white,1,'White internal mat'),(2,black,2,'Black floral ornament')],d['name']+' — multicolor front',128,1),(5,[(4,back,1,'White flexible-clip back')],d['name']+' — three-magnet back',435.2,2)]:
  obj=E.SubElement(res,'object',id=str(objid),type='model');obj.set('{'+PROD+'}UUID',uid());comps=E.SubElement(obj,'components')
  co=E.SubElement(config,'object',id=str(objid));E.SubElement(co,'metadata',key='name',value=title);E.SubElement(co,'metadata',key='extruder',value='1');E.SubElement(co,'metadata',face_count=str(sum(len(m.faces) for _,m,_,_ in parts)))
  for num,m,ext,nm in parts:
   c=E.SubElement(comps,'component',objectid=str(num),transform='1 0 0 0 1 0 0 0 1 0 0 0');c.set('{'+PROD+'}path',f'/3D/Objects/object_{num}.model');c.set('{'+PROD+'}UUID',uid())
   pa=E.SubElement(co,'part',id=str(num),subtype='normal_part',uuid=uid())
   for k,v in [('name',nm),('extruder',str(ext)),('matrix','1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1'),('source_file',d['id']+'-'+str(num)+'.stl'),('source_object_id','0'),('source_volume_id','0'),('source_offset_x','0'),('source_offset_y','0'),('source_offset_z','0')]:E.SubElement(pa,'metadata',key=k,value=v)
   E.SubElement(pa,'mesh_stat',face_count=str(len(m.faces)),edges_fixed='0',degenerate_facets='0',facets_removed='0',facets_reversed='0',backwards_edges='0')
   E.SubElement(rel,'Relationship',Target=f'/3D/Objects/object_{num}.model',Id=f'rel-{num}',Type='http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel')
  it=E.SubElement(build,'item',objectid=str(objid),transform=f'1 0 0 0 1 0 0 0 1 {tx} 128 0',printable='1');it.set('{'+PROD+'}UUID',uid())
  pl=E.SubElement(config,'plate')
  for k,v in [('plater_id',str(plate)),('plater_name','White mat then black front' if plate==1 else 'White back — 3 magnets — gentler PLA clips'),('locked','false'),('filament_map_mode','Auto For Flush'),('filament_maps','1 2'),('filament_volume_maps','0')]:E.SubElement(pl,'metadata',key=k,value=v)
  mi=E.SubElement(pl,'model_instance')
  for k,v in [('object_id',str(objid)),('instance_id','0'),('identify_id',str(100+objid))]:E.SubElement(mi,'metadata',key=k,value=v)
 assemble=E.SubElement(config,'assemble')
 for objid,tx in [(3,128),(5,435.2)]:E.SubElement(assemble,'assemble_item',object_id=str(objid),instance_id='0',transform=f'1 0 0 0 1 0 0 0 1 {tx} 128 0',offset='0 0 0')
 types='<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>'
 relationships='<Relationships xmlns="'+REL+'"><Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>'
 out=P/(d['id']+'-Instax-Mini-3-Magnets.3mf')
 with ZipFile(out,'w',ZIP_DEFLATED) as z:
  for num,m in [(1,white),(2,black),(4,back)]:z.writestr(f'3D/Objects/object_{num}.model',write_mesh(m,num))
  for name,xml in [('3D/3dmodel.model',root),('Metadata/model_settings.config',config),('3D/_rels/3dmodel.model.rels',rel)]:z.writestr(name,E.tostring(xml,xml_declaration=True,encoding='UTF-8'))
  z.writestr('[Content_Types].xml',types);z.writestr('_rels/.rels',relationships);z.writestr('Metadata/project_settings.config',(ROOT/'source/printer-settings.json').read_bytes())
 return out
def build(d):
 portrait=d['orientation']=='portrait';Q=P/d['id'];Q.mkdir(exist_ok=True)
 rgb,dark,solid,pix,cx,cy=get_drawing(d);r,g,b=rgb.transpose(2,0,1)
 scale0=d['width']/(pix.bounds[2]-pix.bounds[0])
 base_positions=RECT_POS if d['shape']=='rectangle' else POS
 positions=[(-y,x) for x,y in base_positions] if portrait else base_positions
 centers=None
 filmshape=rect(-27,-47,27,39) if portrait else rect(-47,-27,39,27)
 from shapely.affinity import scale
 for growth in np.arange(1,1.251,.005):
  outer=scale(pix,scale0*growth,scale0*growth,origin=(0,0)).buffer(.035).buffer(-.035).simplify(.025)
  needs=[filmshape.buffer(.65)]+[rect(x-3.1,y-2.8,x+3.1,y+2.8) for x,y in positions]
  if not all(outer.covers(n) for n in needs):continue
  # Fit magnet pockets to the carving before enlarging the entire design.
  # Every candidate stays outside the photo channel, with triangular spread.
  if portrait:
   top=[float(y) for y in np.arange(47,44.19,-.2) if outer.covers(Point(0,y).buffer(4.9,quad_segs=32))]
   sides=[float(x) for x in np.arange(36,32.19,-.2) if all(outer.covers(Point(s*x,-27).buffer(4.9,quad_segs=32)) for s in [-1,1])]
   if top and sides:centers=[(0,top[0]),(-sides[0],-27),(sides[0],-27)]
  else:
   top=[float(y) for y in np.arange(38,32.19,-.2) if outer.covers(Point(0,y).buffer(4.9,quad_segs=32))]
   low=[float(y) for y in np.arange(36,32.19,-.2) if all(outer.covers(Point(x,-y).buffer(4.9,quad_segs=32)) for x in [-27,27])]
   if top and low:centers=[(0,top[0]),(-27,-low[0]),(27,-low[0])]
  if centers is not None:break
 else:raise AssertionError((d['id'],'needs excessive growth',outer.bounds))
 SCALE=scale0*growth;aperture=aperture_for(d);join=2 if d['shape'] in ['rectangle','octagon'] else 1
 inner=aperture.buffer(6.5,join_style=join);footprint=outer.difference(inner)
 assert outer.covers(aperture.buffer(12,join_style=join))
 print(d['name'],'scale',SCALE,'growth',growth,'outer',outer.bounds,flush=True)
 yy,xx=np.indices(solid.shape);x=(xx-cx)*SCALE;y=(cy-yy)*SCALE
 lum=.2126*r+.7152*g+.0722*b
 nearest=ndi.distance_transform_edt(~dark,return_distances=False,return_indices=True);lum=ndi.gaussian_filter(lum[tuple(nearest)],1.6)
 lo,hi=np.percentile(lum[dark],[3,98]);light=np.clip((lum-lo)/(hi-lo),0,1)
 mid=ndi.gaussian_filter(light,3.2);broad=ndi.gaussian_filter(light,8.0)
 h=1.9+2.7*mid**.8+1.05*broad**.8+.27*(light-mid)
 # Shape distance fields blend the tonal sculpt to exact architectural moulding.
 # Downsampled exact boundary distances, interpolated back to raster.
 ds=4;gx=x[::ds,::ds];gy=y[::ds,::ds]
 pp=shapely.points(gx.ravel(),gy.ravel());dist=shapely.distance(pp,inner.boundary).reshape(gx.shape);inside=shapely.contains_xy(inner,gx,gy);dist[inside]=0
 dist=ndi.zoom(dist,(h.shape[0]/dist.shape[0],h.shape[1]/dist.shape[1]),order=1)[:h.shape[0],:h.shape[1]]
 u=np.clip((dist-4.6)/2.0,0,1);u=u*u*(3-2*u)
 h=1.301+(h-1.301)*u
 edge=np.clip(ndi.distance_transform_edt(solid)*SCALE/.95,0,1);h=1.301+(h-1.301)*edge*edge*(3-2*edge)
 for px,py in positions:
  if d['shape']=='rectangle':
   rho=((x-px)/6.)**2+((y-py)/5.)**2
   dome=1.3+np.exp(-.7*rho)*(4.4+light)
   # Convex relief, rather than a flat rectangular mechanical cap.
   h=np.maximum(h,dome)
  else:
   dd=np.maximum(np.abs(x-px)-2.7,np.abs(y-py)-2.5);w=np.clip(1-dd/2.2,0,1);w=w*w*(3-2*w)
   h=h*(1-w)+np.maximum(h,5.3+.2*(h-1.3))*w
 h=np.minimum(h,6.65);h=ndi.gaussian_filter(h,.65);h[~solid]=1.301
 sy,sx=np.nonzero(dark);step=.22/SCALE
 xs=np.arange(max(0,sx.min()-2),min(rgb.shape[1]-1,sx.max()+3),step);ys=np.arange(max(0,sy.min()-2),min(rgb.shape[0]-1,sy.max()+3),step)
 xp,yp=np.meshgrid(xs,ys);v=np.c_[((xp-cx)*SCALE).ravel(),((cy-yp)*SCALE).ravel(),RegularGridInterpolator((np.arange(h.shape[0]),np.arange(h.shape[1])),h)(np.c_[yp.ravel(),xp.ravel()])]
 ny,nx=xp.shape;ids=np.arange(nx*ny).reshape(ny,nx);a=ids[:-1,:-1].ravel();b=ids[:-1,1:].ravel();c=ids[1:,1:].ravel();dd=ids[1:,:-1].ravel();ff=np.vstack([np.c_[a,b,c],np.c_[a,c,dd]])
 bot=v.copy();bot[:,2]=1.29;N=len(v);faces=[ff,ff[:,::-1]+N];rim=list(ids[0])+list(ids[1:,-1])+list(ids[-1,-2::-1])+list(ids[-2:0:-1,0])
 for a,b in zip(rim,rim[1:]+rim[:1]):faces.append(np.array([[a,b,b+N],[a,b+N,a+N]]))
 raw=tm.Trimesh(np.vstack([v,bot]),np.vstack(faces));raw.fix_normals();assert raw.is_volume
 art=check(inter(raw,extrude(footprint,1.3,7)),'relief')
 white=extrude(outer.buffer(-.18).difference(aperture),0,.36)
 layers=[]
 zz=np.linspace(.36,1.3,13)
 for z0,z1 in zip(zz[:-1],zz[1:]):layers.append(extrude(outer.buffer(-.18*(1-(z0-.36)/.94)).difference(inner),z0,z1-z0+.00002))
 posts=[] if d['shape']=='rectangle' else [box(5.5,5.1,4,1.3,p) for p in positions]
 black=union([art,moulding(aperture,join)]+layers+posts)
 cuts=union([rotate_mesh(socket((y,-x)),True) if portrait else socket((x,y)) for x,y in positions])
 black=check(diff(black,cuts),'black');white=check(diff(white,cuts),'white')
 back,loaded=back_geometry(portrait,outer,centers,base_positions)
 mounted=[m.copy() for m in [white,black]]
 for m in mounted:m.apply_translation([0,0,MATE])
 assert sum(abs(inter(m,back).volume) for m in mounted)<.015,('assembled interference',sum(abs(inter(m,back).volume) for m in mounted))
 pulled=[m.copy() for m in mounted]
 for m in pulled:m.apply_translation([0,0,.5])
 for px,py in positions:
  region=box(8,8,12,-.1,(px,py));contact=sum(abs(inter(inter(m,back),region).volume) for m in pulled)
  assert contact>.005,('snap engagement',px,py,contact)
 film=box(54.2,86.2,1.16,2.42,(0,-4)) if portrait else box(86.2,54.2,1.16,2.42,(-4,0))
 assert abs(inter(loaded,film).volume)<.02,('film channel',inter(loaded,film).volume)
 for m in mounted:assert abs(inter(m,film).volume)<.005
 for a in np.linspace(0,94,28):
  q=film.copy();q.apply_translation([0,-a,0] if portrait else [-a,0,0]);assert abs(inter(loaded,q).volume)<.02,('insertion',a,inter(loaded,q).volume)
 for px,py in centers:
  assert abs(inter(back,cyl(px,py,3,0,3)).volume)<.001,'magnet fit'
  floor=cyl(px,py,2.9,3.15,.4);assert abs(inter(back,floor).volume-floor.volume)<.001,'magnet floor'
 assert abs(inter(white,black).volume)<.001
 assert filmshape.difference(outer).area<.001
 for sx in [-.4,0,.4]:
  for sy in [-.4,0,.4]:
   pic=rect(-23+sx,-31+sy,23+sx,31+sy) if portrait else rect(-31+sx,-23+sy,31+sy,23+sy)
   assert pic.covers(aperture),'image overlap'
 for name,m in [('white-mat.stl',white),('black-ornament.stl',black),('back.stl',back),('loaded-back.stl',loaded)]:m.export(Q/name)
 report=dict(id=d['id'],name=d['name'],orientation=d['orientation'],shape=d['shape'],front_dimensions_mm=np.ptp(black.bounds,axis=0).tolist(),front_bounds_mm=black.bounds.tolist(),back_dimensions_mm=np.ptp(back.bounds,axis=0).tolist(),assembled_depth_mm=float(3.6+black.bounds[1,2]),mat_width_mm=6.5,mat_height_mm=.36,mat_perpendicular_offset=True,film_uncut_mm=[54,86] if portrait else [86,54],aperture_bounds_mm=aperture.bounds,image_area_visible_percent=100*aperture.area/(62*46),full_film_concealed=True,nominal_edge_overlap_mm=.6,misalignment_checked_mm=.4,magnet_centers_mm=centers,magnet_pockets_mm=[6.3,3.1],magnet_floor_mm=.5,snap_positions_mm=positions,snap_tip_height_mm=8,snap_stem_mm=[3.5,2],snap_slot_radius_mm=.7,snap_head_width_mm=3.88,socket_neck_width_mm=3.65,photo_spring_length_mm=15,front_print_color_changes=1,watertight_parts=True,insertion_positions_checked=28,physical_test=False,ornament_source='fresh AI drawing from historical descriptions, no original MakerWorld mesh or collection reference photo',relief_method='drawing-guided tonal bas-relief with explicit CAD mouldings; not full multi-view reconstruction',drawing_uniform_growth=float(growth),drawing_mm_per_pixel=SCALE,drawing_center_px=[cx,cy])
 (Q/'validation.json').write_text(json.dumps(report,indent=2));(Q/'aperture.wkt').write_text(aperture.wkt);(Q/'outer.wkt').write_text(outer.wkt)
 write_project(d,white,black,back)
 print('COMPLETE',d['id'],json.dumps(report),flush=True)
if __name__=='__main__':
 ds=json.loads((ROOT/'source/designs-final.json').read_text())
 for d in ds:
  if len(sys.argv)==1 or d['id'] in sys.argv[1:]:build(d)
