import bpy, json, math
from mathutils import Vector
from pathlib import Path
base=Path(__file__).resolve().parents[1]
result={}
for f in ['cat.glb','ShibaInu.gltf','Husky.gltf','Horse.gltf']:
 bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.ops.import_scene.gltf(filepath=str(base/'vendor'/f))
 print('\nSOURCE',f)
 rec={'objects':[],'bones':[],'actions':[]}
 for o in bpy.context.scene.objects:
  d={'name':o.name,'type':o.type,'loc':list(o.location),'rot':list(o.rotation_euler),'scale':list(o.scale)}
  if o.type=='MESH':
   c=[o.matrix_world@Vector(v) for v in o.bound_box];d.update(bounds=[[min(v[i] for v in c) for i in range(3)],[max(v[i] for v in c) for i in range(3)]],mats=[m.name for m in o.data.materials],vertices=len(o.data.vertices))
  if o.type=='ARMATURE':
   for b in o.data.bones:rec['bones'].append({'name':b.name,'head':list(o.matrix_world@b.head_local),'tail':list(o.matrix_world@b.tail_local),'parent':b.parent.name if b.parent else None})
  rec['objects'].append(d)
 for a in bpy.data.actions:rec['actions'].append({'name':a.name,'range':list(a.frame_range)})
 result[f]=rec
 bpy.ops.wm.save_as_mainfile(filepath=str(base/'source'/f.replace('.glb','.blend').replace('.gltf','.blend')))
print(json.dumps(result,indent=2))
(base/'qa'/'source-inspect.json').write_text(json.dumps(result,indent=2))
