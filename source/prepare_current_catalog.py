# SPDX-License-Identifier: MIT
"""Promote checked native projects into a versioned, documented current catalog.

Keep the original six released models and their integrity records unchanged.
This adds the eight current prototypes under models/current/.
"""
import hashlib
import json
import os
import shutil
from pathlib import Path
from paths import ROOT


def main():
    designs=json.loads(Path(os.environ.get('BAROQUE_DESIGNS_FILE',ROOT/'source/designs-period-eight.json')).read_text())
    revised=json.loads((ROOT/'source/designs-botanical-sculpture-v3.json').read_text())[0]
    records=[];current=[]
    def copy(f,relative):
        to=ROOT/relative;to.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,to)
    for original in designs:
        is_new=original['id'].startswith('16-')
        single_build=os.environ.get('BAROQUE_CATALOG_BUILD_DIR')
        d=original if single_build else (revised if is_new else original)
        build=Path(single_build).resolve() if single_build else ROOT/'build'/('botanical-sculpture-v3' if is_new else 'period-catalog-six')
        did=d['id'];q=build/did
        report=json.loads((q/'validation.json').read_text())
        sliced=json.loads((build/'validation'/(did+'-slicer.json')).read_text())
        native=build/sliced['file']
        digest=hashlib.sha256(native.read_bytes()).hexdigest()
        assert digest==sliced['sha256'] and sliced['return_code']==0
        assert report['full_film_concealed'] and report['watertight_parts'] and report['closed_socket_roofs_checked']
        assert report['assembly_interference_mm3']<.015 and sliced['filament_changes']==[1,0]
        model='models/current/'+native.name
        geo='validation/current/'+did+'-geometry.json'
        sl='validation/current/'+did+'-slicer.json'
        back='validation/current/'+did+'-back-toolpaths.json'
        copy(native,model);copy(q/'validation.json',geo)
        copy(build/'validation'/(did+'-slicer.json'),sl)
        copy(build/'validation'/(did+'-back-toolpaths.json'),back)
        if is_new:
            name='Botanical Garland';slug='botanical-garland'
        else:
            name=original['name'].replace('Rocaille ','').replace('Period Floral ','')
            slug=name.lower().replace(' ','-')
        records.append(dict(id=did,name=name,slug=slug,model=model,sha256=digest,
            geometry=geo,slicer=sl,back_toolpaths=back,orientation=d['orientation'],
            dimensions_mm=report['front_dimensions_mm'],depth_mm=report['assembled_depth_mm'],
            image_visible_percent=report['image_area_visible_percent'],
            mat_height_mm=report['mat_height_mm'],mat_layers=round((report['mat_height_mm']-.2)/.08)+1,
            front_minutes=sliced['estimated_minutes'][0],back_minutes=sliced['estimated_minutes'][1],
            revision=('Reinforced mat · ' if report['mat_height_mm']>.36 else '')+('Sculpted petals v3' if is_new else 'Period floral catalog'),
            views={v:f'renders/current/{slug}-{"side-perspective-v2" if v=="angle" else "rear-fit" if v=="fit" else v}.png' for v in ['front','angle','back','fit']}))
        current.append(d)
    catalog=dict(title='Eight floral Instax Mini frames',schema_version=1,
        status='Digital prototypes; physical fit and surface detail need testing',
        film_mm=[86,54],magnets_mm=[6,3],magnets_per_frame=3,
        illustration_palette_is_example=True,frames=records)
    (ROOT/'catalog').mkdir(exist_ok=True)
    (ROOT/'catalog/current.json').write_text(json.dumps(catalog,indent=2)+'\n')
    (ROOT/'source/designs-current.json').write_text(json.dumps(current,indent=2)+'\n')
    print('Prepared eight checked current projects; original release retained',flush=True)


if __name__=='__main__':main()
