# SPDX-License-Identifier: MIT
"""Optional local relative-depth inference for generated sculpture masters.

Install source/requirements-depth.txt into a separate Python 3.13 environment.
Weights are downloaded from the model authors, Apache-2.0; not redistributed.
Depth is an estimate, not a dimensionally calibrated or guaranteed surface.
"""
import json
import sys
import os
from pathlib import Path
import numpy as np
import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForDepthEstimation

ROOT = Path(__file__).resolve().parent.parent
MODEL = 'depth-anything/Depth-Anything-V2-Small-hf'
processor = AutoImageProcessor.from_pretrained(MODEL, use_fast=False)
model = AutoModelForDepthEstimation.from_pretrained(MODEL)
device = 'mps' if torch.backends.mps.is_available() else 'cpu'
model.to(device).eval()
print('MODEL READY', MODEL, device, flush=True)
for d in json.loads(Path(os.environ.get('BAROQUE_DESIGNS_FILE',ROOT/'source/designs-floral-rococo.json')).read_text()):
    if len(sys.argv)>1 and d['id'] not in sys.argv[1:]:
        continue
    if not d.get('depth_file'):
        continue
    source = ROOT/d['depth_file']
    image = Image.open(source).convert('RGB')
    inputs = processor(images=image, return_tensors='pt',size={'height':1036,'width':1036})
    with torch.inference_mode():
        output = model(**{k:v.to(device) for k,v in inputs.items()}).predicted_depth
        prediction = torch.nn.functional.interpolate(output.unsqueeze(1),size=image.size[::-1],mode='bicubic',align_corners=False)
    out = source.with_name(d['id']+'-estimated-depth.npy')
    np.save(out,prediction.squeeze().cpu().numpy().astype(np.float32))
    out.with_suffix('.json').write_text(json.dumps(dict(model=MODEL,revision=getattr(model.config,'_commit_hash',None),
        model_license='Apache-2.0',source=str(source.relative_to(ROOT)),device=device,
        semantics='relative inverse depth, not calibrated millimeters',size=list(image.size)),indent=2)+'\n')
    print('DEPTH SAVED',out,flush=True)
