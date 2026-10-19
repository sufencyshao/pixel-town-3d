import bpy,json
from pathlib import Path
R=Path('/Users/summerwindy/Desktop/AI Chat/pixel-town-app/design/character-residents-3d-v2');bpy.ops.wm.open_mainfile(filepath=str(R/'assets/02_hero_female/character.blend'))
rig=bpy.data.objects['Resident_Rig'];out={}
def bounds(vs):return [[round(min(v.co[k] for v in vs),4) for k in range(3)],[round(max(v.co[k] for v in vs),4) for k in range(3)]] if vs else []
for state in ['Idle','REST']:
 rig.animation_data.action=bpy.data.actions.get('Idle') if state=='Idle' else None
 if state=='Idle' and rig.animation_data.action.slots:rig.animation_data.action_slot=rig.animation_data.action.slots[0]
 for b in rig.pose.bones:b.matrix_basis.identity()
 bpy.context.scene.frame_set(0);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();items=[]
 for name in ['Skin','Eyes','Continuous scalp cap','Top_dress','Shoe_l_Upper','MaryJane strap']:
  o=bpy.data.objects.get(name)
  if not o:continue
  eo=o.evaluated_get(deps);me=eo.to_mesh();d={'object':name,'raw':bounds(o.data.vertices),'eval':bounds(me.vertices),'shapeKeys':{key.name:{'value':key.value,'bounds':bounds(key.data)} for key in o.data.shape_keys.key_blocks} if o.data.shape_keys else {},'matrixWorld':[list(row) for row in o.matrix_world]};items.append(d);eo.to_mesh_clear()
 out[state]={'meshes':items,'bones':{name:{'head':list(rig.pose.bones[name].head),'tail':list(rig.pose.bones[name].tail),'basis':[list(r) for r in rig.pose.bones[name].matrix_basis]} for name in ['Head','upperarm_l','lowerarm_l','hand_l']}}
(R/'qa-identity/02_hero_female/geometry-inspection.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out))
