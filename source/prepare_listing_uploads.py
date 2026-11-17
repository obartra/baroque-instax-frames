# SPDX-License-Identifier: MIT
"""Prepare named, unchanged current models for model-library uploads."""
from pathlib import Path
import hashlib,json,shutil,zipfile
from paths import ROOT
r=ROOT; p=r/'publishing'; media=p/'media'; stage=Path.home()/'Downloads/Floral-Instax-Publishing'; stage.mkdir(parents=True,exist_ok=True)
for src,dst in [('renders/Eight-frames-current.png','02-eight-designs.png'),('renders/current/botanical-garland-side-perspective-v2.png','03-angle-and-depth.png'),('renders/Eight-frames-rear-film-fit.png','04-whole-film-fit.png'),('docs/assembly/01-print-and-magnets-v3.png','05-print-and-magnets.png'),('docs/assembly/02-snap-and-load-v3.png','06-snap-and-load.png'),('docs/assembly/03-magnetic-display-v3.png','07-magnetic-display.png')]: shutil.copy2(r/src,media/dst)
copy=(p/'listing-description.txt').read_text()
(p/'listing-description.txt').write_text(copy)
(stage/'START-HERE.txt').write_text(copy)
cat=json.loads((r/'catalog/current.json').read_text())
with zipfile.ZipFile(stage/'Eight-Rococo-Instax-Mini-Frames.zip','w',zipfile.ZIP_DEFLATED,compresslevel=1) as out:
 out.writestr('START-HERE.txt',copy)
 for f in cat['frames']:
  folder=f['slug']; model=r/f['model']
  assert hashlib.sha256(model.read_bytes()).hexdigest()==f['sha256']
  shutil.copy2(model,stage/model.name)
  out.write(model,folder+'/'+model.name)
  with zipfile.ZipFile(r/f['stl']['archive']) as z:
   for n in z.namelist():
    if n.endswith('.stl'): out.writestr(folder+'/'+folder+'-'+Path(n).name,z.read(n))
    elif n=='README.txt': out.writestr(folder+'/STL-import-guide.txt',z.read(n))
shutil.copytree(media,stage/'media',dirs_exist_ok=True)
print(stage)
print((stage/'Eight-Rococo-Instax-Mini-Frames.zip').stat().st_size)
