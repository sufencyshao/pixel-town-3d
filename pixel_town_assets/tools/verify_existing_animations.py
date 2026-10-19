#!/usr/bin/env python3
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image
from animate_existing import ACTIONS
ROOT=Path(__file__).resolve().parents[1]
errors=[];rows=[]
for p in sorted((ROOT/'characters').glob('[012][0-9]_*')):
 if not p.is_dir() or int(p.name[:2])>20:continue
 mf=json.loads((p/'animation-manifest.json').read_text())
 for name,expected in mf['sourceSHA256'].items():
  if hashlib.sha256((p/name).read_bytes()).hexdigest()!=expected:errors.append(f'{p.name}/{name}: source changed')
 for action,a in mf['animations'].items():
  # New daily clips intentionally include held/repeated key poses. Their own
  # verifier checks those sequences; the original motion-uniqueness gate below
  # remains scoped to the original eleven actions.
  if action not in ACTIONS:continue
  atlas=Image.open(p/a['atlas']);ar=np.array(atlas)
  if atlas.mode!='RGBA' or atlas.size!=(256*a['frames'],256):errors.append(f'{p.name}/{action}: bad atlas')
  if set(np.unique(ar[:,:,3]))!={0,255}:errors.append(f'{p.name}/{action}: nonbinary alpha')
  fs=[ar[:,i*256:(i+1)*256] for i in range(a['frames'])]
  unique=len({hashlib.sha256(f.tobytes()).hexdigest() for f in fs})
  diffs=[float(np.mean(np.any(fs[i]!=fs[(i+1)%len(fs)],axis=2))) for i in range(len(fs))]
  with Image.open(p/a['gif']) as gif:
   duration=0;transparent=True
   if gif.info.get('loop')!=0:errors.append(f'{p.name}/{action}: not looped')
   if gif.n_frames!=a['frames']:errors.append(f'{p.name}/{action}: GIF frame mismatch {gif.n_frames}')
   for i in range(gif.n_frames):
    gif.seek(i);duration+=gif.info.get('duration',0);transparent=transparent and gif.convert('RGBA').getpixel((0,0))[3]==0
  if not transparent:errors.append(f'{p.name}/{action}: no GIF alpha')
  if duration!=a['frames']*a['frameMs']:errors.append(f'{p.name}/{action}: wrong duration')
  if unique<12:errors.append(f'{p.name}/{action}: low motion uniqueness {unique}')
  # The wrap step is part of the same continuous trajectory, and must not pop.
  if diffs[-1]>max(diffs[:-1])*1.2:errors.append(f'{p.name}/{action}: loop discontinuity')
  clipped=any(np.any(f[0,:,3]) or np.any(f[-1,:,3]) or np.any(f[:,0,3]) or np.any(f[:,-1,3]) for f in fs)
  if clipped:errors.append(f'{p.name}/{action}: clipped by canvas edge')
  rows.append({'role':p.name,'action':action,'uniqueFrames':unique,'frameCount':len(fs),'durationMs':duration,'gifTransparent':transparent,'wrapChangedPixelFraction':round(diffs[-1],6),'maximumAdjacentChangedPixelFraction':round(max(diffs),6),'canvasClipped':bool(clipped)})
result={'roles':len({r['role'] for r in rows}),'actions':len(rows),'renderedFrames':sum(r['frameCount'] for r in rows),'errors':errors,'checks':rows}
(ROOT/'tools'/'existing-animation-validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))
raise SystemExit(bool(errors))
