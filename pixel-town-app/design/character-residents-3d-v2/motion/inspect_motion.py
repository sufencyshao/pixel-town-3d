import bpy,json
from pathlib import Path
R=Path('/Users/summerwindy/Desktop/AI Chat/pixel-town-app/design');OUT=R/'character-residents-3d-v2/motion'
bpy.ops.wm.open_mainfile(filepath=str(R/'whole-town-animals-3d-v6/assets/people/Ache-caretaker.blend'))
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
data={'rig':rig.name,'rig_matrix':[list(v) for v in rig.matrix_world],'actions':[(a.name,list(a.frame_range),len(a.layers)) for a in bpy.data.actions],'bones':[{ 'name':b.name,'parent':b.parent.name if b.parent else None,'head':list(b.head_local),'tail':list(b.tail_local),'matrix':[list(v) for v in b.matrix_local]} for b in rig.data.bones]}
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(R/'character-natural-3d-v1/reference/UAL1_Standard.glb'))
data['source_actions']=[(a.name,list(a.frame_range)) for a in bpy.data.actions]
(OUT/'qa/source-inspection.json').write_text(json.dumps(data,indent=2));print('MOTION_INSPECTION',json.dumps(data))
