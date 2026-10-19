import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
results={}
for sex in ['Male','Female']:
 bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.ops.import_scene.gltf(filepath=str(R/'vendor/base'/f'Superhero_{sex}_FullBody.gltf'))
 rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
 results[sex]={'rig':rig.name,'scale':list(rig.scale),'bones':[b.name for b in rig.data.bones], 'boneGeometry':{b.name:{'head':list(b.head_local),'tail':list(b.tail_local),'matrix':[list(row) for row in b.matrix_local]} for b in rig.data.bones}, 'meshes':[]}
 for o in bpy.context.scene.objects:
  if o.type!='MESH': continue
  pts=[o.matrix_world@v.co for v in o.data.vertices]
  results[sex]['meshes'].append({'name':o.name,'verts':len(o.data.vertices),'polys':len(o.data.polygons),'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'shape_keys':[x.name for x in o.data.shape_keys.key_blocks] if o.data.shape_keys else [],'mats':[m.name if m else None for m in o.data.materials],'bounds':[[min(p[i] for p in pts),max(p[i] for p in pts)] for i in range(3)],'weighted':len(o.vertex_groups)})
(R/'qa/source-inspection.json').write_text(json.dumps(results,indent=2))
print(json.dumps({sex:{k:v for k,v in value.items() if k not in ['boneGeometry','bones']} for sex,value in results.items()},indent=2))
