#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Verify current-file identity, project structure, source paths and README links.

Uses the standard library. Does not rerun CAD or slicing or start a print.
"""
import hashlib
import json
from pathlib import Path
import re
import struct
from xml.etree import ElementTree as E
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[1]
NS={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}


def require(ok,message):
    if not ok:raise ValueError(message)


def main():
    catalog=json.loads((ROOT/'catalog/current.json').read_text())
    designs=json.loads((ROOT/'source/designs-current.json').read_text())
    require(len(catalog['frames'])==len(designs)==8,'Expected eight current frames')
    require({r['id'] for r in catalog['frames']}=={d['id'] for d in designs},'Model/source IDs differ')
    for r in catalog['frames']:
        project=ROOT/r['model'];digest=hashlib.sha256(project.read_bytes()).hexdigest()
        geo=json.loads((ROOT/r['geometry']).read_text())
        sliced=json.loads((ROOT/r['slicer']).read_text())
        back=json.loads((ROOT/r['back_toolpaths']).read_text())
        require(digest==r['sha256']==sliced['sha256'],r['name']+': native file differs from its checked slice')
        require(r['id']==geo['id']==sliced['id']==back['id'],r['name']+': record identity mismatch')
        require(r['mat_height_mm']==geo['mat_height_mm']==.68 and r['mat_layers']==7,r['name']+': reinforced mat missing')
        require(sliced['return_code']==0 and sliced['plates']==2 and sliced['filament_changes']==[1,0],r['name']+': missing two-plate slice result')
        require(not any(sliced['warning_messages']),r['name']+': per-plate warning')
        require(geo['watertight_parts'] and geo['fused_front_single_volume'] and geo['full_film_concealed'] and geo['closed_socket_roofs_checked'],r['name']+': missing geometry gate')
        require(geo['assembly_interference_mm3']<.015 and len(geo['magnet_centers_mm'])==3,r['name']+': mechanics record')
        require(back['layers_checked']>0 and not back['missing_cross_section_components'] and not back['missing_functional_regions'],r['name']+': missing back paths')
        require(hashlib.sha256((ROOT/r['geometry']).read_bytes()).hexdigest()==back['geometry_report_sha256'],r['name']+': audit belongs to another geometry report')
        with ZipFile(project) as z:
            require(z.testzip() is None,r['name']+': corrupt 3MF')
            model=E.fromstring(z.read('3D/3dmodel.model'))
            settings=json.loads(z.read('Metadata/project_settings.config'))
            config=E.fromstring(z.read('Metadata/model_settings.config'))
            require(model.get('unit')=='millimeter' and len(model.findall('m:build/m:item',NS))==2,r['name']+': units/two pieces')
            require(len(config.findall('plate'))==2 and len(settings['filament_colour'])==3,r['name']+': plates/material slots')
            mat=E.fromstring(z.read('3D/Objects/object_1.model'))
            mat_top=max(float(v.get('z')) for v in mat.findall('.//m:vertex',NS))
            require(abs(mat_top-geo['mat_height_mm'])<1e-6,r['name']+': actual mat mesh height differs')
            parts={p.get('id'):{m.get('key'):m.get('value') for m in p.findall('metadata')} for p in config.findall('object/part')}
            require({n:parts[n]['extruder'] for n in ('1','2','4')}=={'1':'1','2':'2','4':'3'},r['name']+': mat/ornament/back roles')
        for view,p in r['views'].items():
            data=(ROOT/p).read_bytes()
            require(data[:8]==b'\x89PNG\r\n\x1a\n' and min(struct.unpack('>II',data[16:24]))>=400,r['name']+': missing/undersized '+view)
        stl=ROOT/r['stl']['archive']
        require(hashlib.sha256(stl.read_bytes()).hexdigest()==r['stl']['sha256'],r['name']+': STL archive hash')
        with ZipFile(stl) as z:
            require(z.testzip() is None,r['name']+': corrupt STL archive')
            record=json.loads(z.read('export-record.json'))
            require(record['source_sha256']==digest and record['source_3mf']==r['model'],r['name']+': stale STL export')
            require(set(record['parts'])=={'mat.stl','front-ornament.stl','back.stl'},r['name']+': STL parts')
            for name,part in record['parts'].items():
                data=z.read(name)
                require(hashlib.sha256(data).hexdigest()==part['sha256'],r['name']+': STL part hash '+name)
                count=struct.unpack_from('<I',data,80)[0]
                require(count==part['triangles'] and len(data)==84+50*count,r['name']+': STL triangles '+name)
            require(abs(record['parts']['mat.stl']['bounds_mm'][1][2]-.68)<1e-6,r['name']+': STL mat reinforcement')
        print('PASS',r['name'])
    for d in designs:
        for key in ('concept_file','depth_file','normal_file','surface_file','final_surface_file','refinement_record'):
            if d.get(key):require((ROOT/d[key]).is_file(),d['id']+': missing '+key)
    sources=json.loads((ROOT/'catalog/source-files.json').read_text())['files']
    for path,digest in sources.items():
        require(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,'Source/input hash mismatch: '+path)
    steps=[]
    for path in sorted((ROOT/'docs/assembly').glob('*.svg')):
        svg=E.parse(path)
        texts=[n.text or '' for n in svg.iter() if n.tag.endswith('text')]
        require(not any(re.search(r'\b(white|black|gray|grey|gold|coupon|test)\b',s,re.I) for s in texts),'Prescribed color or fit-test label: '+path.name)
        steps.extend(n.text for n in svg.iter() if n.get('class')=='step')
    require(steps==['1','2','3','4','5'],'Assembly must have five steps')
    source=json.loads((ROOT/'docs/assembly/sources.json').read_text())
    require(.1<source['context_frame_width_px']/source['context_appliance_width_px']<.25,'Frame/context proportion')
    for doc in [ROOT/'README.md',ROOT/'docs/CURRENT-CATALOG.md',ROOT/'docs/PRINTING.md',ROOT/'docs/assembly/README.md']:
        contents=doc.read_text()
        targets=re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',contents)+re.findall(r'<img[^>]+src="([^"]+)"',contents)
        for target in targets:
            if '://' in target or target.startswith('#'):continue
            require((doc.parent/target.split('#',1)[0]).exists(),str(doc.relative_to(ROOT))+': missing '+target)
    print('PASS current source paths, five illustrated steps, context scale and documentation links')
    print('Digital identity checks only; no physical test or print start.')


if __name__=='__main__':main()
