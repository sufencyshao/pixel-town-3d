import bpy,json,hashlib,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];N=R.parents[1]/'character-natural-3d-v1/reference';library={}
for key in ['Casual','Worker']:
 bpy.ops.wm.read_factory_settings(use_empty=True);path=N/f'Quaternius-{key}.glb';bpy.ops.import_scene.gltf(filepath=str(path));rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
 if rig.animation_data:
  rig.animation_data.action=None
  for tr in rig.animation_data.nla_tracks:tr.mute=True
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update();items=[]
 for o in bpy.context.scene.objects:
  if o.type!='MESH' or not o.vertex_groups:continue
  points=[o.matrix_world@v.co for v in o.data.vertices]
  record={'name':o.name,'sourceCategory':key,'vertices':[list(v) for v in points],'faces':[list(f.vertices) for f in o.data.polygons],'materialIndices':[f.material_index for f in o.data.polygons],'materials':[{'name':m.name,'diffuseColor':list(m.diffuse_color)} for m in o.data.materials],'bounds':[[min(v[i] for v in points),max(v[i] for v in points)] for i in range(3)],'sourceWeights':[{o.vertex_groups[g.group].name:g.weight for g in v.groups} for v in o.data.vertices]}
  items.append(record);print(key,o.name,len(points),record['bounds'])
 library[key]={'source':str(path),'sourceSha256':hashlib.sha256(path.read_bytes()).hexdigest(),'rigBones':[b.name for b in rig.data.bones],'meshes':items,'note':'Mature finished modular parts, frozen in their own rest world space. Not normalized to Universal Base, and bone names differ. Use anatomical fit plus canonical reweighting; do not copy source rig actions.'}
(R/'clothing-library.json').write_text(json.dumps(library,separators=(',',':')))
shutil.copyfile(N/'modular-men-source.json',R/'reference/modular-men-source.json');shutil.copyfile(N/'License_Modular_Men_CC0.txt',R/'reference/License_Modular_Men_CC0.txt')
