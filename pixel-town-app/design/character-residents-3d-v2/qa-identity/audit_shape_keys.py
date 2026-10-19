"""Read-only default-expression and Basis consistency audit of built .blend files."""
import bpy, json, hashlib, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
ids=sys.argv[sys.argv.index('--ids')+1].split(',') if '--ids' in sys.argv else None
results=[]
for p in sorted((ROOT/'assets').glob('*/character.blend')):
 if ids and p.parent.name not in ids:continue
 digest=hashlib.sha256(p.read_bytes()).hexdigest()
 bpy.ops.wm.open_mainfile(filepath=str(p))
 meshes=[]
 for o in bpy.context.scene.objects:
  if o.type!='MESH' or not o.data.shape_keys:continue
  keys=o.data.shape_keys.key_blocks;basis=keys[0]
  mismatch=max(((v.co-k.co).length for v,k in zip(o.data.vertices,basis.data)),default=0)
  shapes=[]
  for key in list(keys)[1:]:
   delta=max(((v.co-k.co).length for v,k in zip(key.data,basis.data)),default=0)
   shapes.append({'name':key.name,'defaultValue':key.value,'maxDeltaMetres':delta,
                  'defaultZero':abs(key.value)<1e-7,'boundedExpressionDelta':delta<.06})
  meshes.append({'object':o.name,'basisMatchesMesh':mismatch<1e-5,'maxBasisMeshDeltaMetres':mismatch,'shapes':shapes})
 results.append({'id':p.parent.name,'source':str(p),'sourceSha256':digest,
  'sourceHashUnchanged':hashlib.sha256(p.read_bytes()).hexdigest()==digest,'meshes':meshes,
  'passed':all(m['basisMatchesMesh'] and all(s['defaultZero'] and s['boundedExpressionDelta'] for s in m['shapes']) for m in meshes)})
out=ROOT/'qa-identity/shape-key-audit.json';out.write_text(json.dumps({'characters':results,'passed':sum(r['passed'] for r in results),'total':len(results)},ensure_ascii=False,indent=2)+'\n')
print('SHAPE_KEY_QA',sum(r['passed'] for r in results),len(results))
