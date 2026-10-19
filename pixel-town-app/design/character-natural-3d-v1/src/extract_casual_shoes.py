import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parent.parent
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(R/'reference/Quaternius-Casual.glb'))
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');rig.animation_data.action=None
for t in rig.animation_data.nla_tracks:t.mute=True
for p in rig.pose.bones:p.matrix_basis.identity()
bpy.context.view_layer.update();o=bpy.data.objects['Casual2_Feet'];points=[o.matrix_world@v.co for v in o.data.vertices]
print('REST SHOE',[(min(v[k] for v in points),max(v[k] for v in points)) for k in range(3)])
print('TRANSFORM',o.matrix_world)
data={'source':'Quaternius Ultimate Modular Men / Casual2_Feet','vertices':[list(v) for v in points],'faces':[list(p.vertices) for p in o.data.polygons],'material_indices':[p.material_index for p in o.data.polygons],'materials':[m.name for m in o.data.materials]}
(R/'reference/casual-shoes.json').write_text(json.dumps(data));print(len(points),len(o.data.polygons))
