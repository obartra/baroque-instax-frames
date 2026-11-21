# SPDX-License-Identifier: MIT
"""Package the current eight checked designs, without changing any models."""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from paths import ROOT


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--version',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    assert args.version.startswith('v') and '/' not in args.version
    args.output.mkdir(parents=True,exist_ok=True)
    frames=json.loads((ROOT/'catalog/current.json').read_text())['frames']
    assert len(frames)==8
    guide=(ROOT/'publishing/listing-description.txt').read_text()
    guide+='\n\nSOURCE AND UPDATES\nhttps://github.com/obartra/baroque-instax-frames\n'
    guide+='\nIllustrated instructions: https://obartra.github.io/baroque-instax-frames/#print-and-assemble\n'
    bundles={}
    for kind in ('3MF','STL','Complete'):
        filename=f'Floral-Instax-Frames-{args.version}-{kind}.zip'
        bundles[kind]=args.output/filename
        with ZipFile(bundles[kind],'w',ZIP_DEFLATED,compresslevel=1) as out:
            out.writestr('START-HERE.txt',guide)
            for name in ('LICENSE','LICENSING.md','PROVENANCE.txt','CHANGELOG.md','docs/UPGRADING-v0.3.0.md'):
                out.write(ROOT/name,name)
            for p in sorted((ROOT/'LICENSES').glob('*.txt')):out.write(p,p.relative_to(ROOT).as_posix())
            for p in sorted((ROOT/'docs/assembly').glob('*-v3.png')):out.write(p,'assembly/'+p.name)
            out.write(ROOT/'docs/PRINTING.md','docs/PRINTING.md')
            for p in sorted((ROOT/'docs/revisions/v0.3.0').glob('*.png')):out.write(p,p.relative_to(ROOT).as_posix())
            for frame in frames:
                model=ROOT/frame['model'];stl=ROOT/frame['stl']['archive']
                assert hashlib.sha256(model.read_bytes()).hexdigest()==frame['sha256']
                assert hashlib.sha256(stl.read_bytes()).hexdigest()==frame['stl']['sha256']
                folder=frame['slug']+'/'
                if kind in ('3MF','Complete'):out.write(model,folder+model.name)
                if kind in ('STL','Complete'):
                    with ZipFile(stl) as source:
                        for name in source.namelist():out.writestr(folder+name,source.read(name))
                if kind=='Complete':
                    for view,path in frame['views'].items():out.write(ROOT/path,folder+'views/'+view+'.png')
            out.writestr('release-manifest.json',json.dumps({'version':args.version,'format':kind,
                'catalog':frames,'source':'https://github.com/obartra/baroque-instax-frames'},indent=2)+'\n')
        with ZipFile(bundles[kind]) as check:
            assert check.testzip() is None
            for frame in frames:
                folder=frame['slug']+'/'
                if kind in ('3MF','Complete'):
                    assert hashlib.sha256(check.read(folder+Path(frame['model']).name)).hexdigest()==frame['sha256']
                if kind in ('STL','Complete'):
                    with ZipFile(ROOT/frame['stl']['archive']) as source:
                        for name in ('mat.stl','front-ornament.stl','back.stl'):
                            assert check.read(folder+name)==source.read(name)
        print('PACKAGE PASS',filename,bundles[kind].stat().st_size,flush=True)
    sums=''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in bundles.values())
    (args.output/'SHA256SUMS').write_text(sums)
    print('All eight native 3MFs and 24 STL parts match the current catalog.',flush=True)


if __name__=='__main__':main()
