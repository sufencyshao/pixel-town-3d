import bpy,math,json
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
R=Path(__file__).resolve().parent.parent;source=(R/'reference/Ache-source.blend') if (R/'reference/Ache-source.blend').exists() else R.parent/'character-natural-3d-v1/assets/01-Ache.blend';out=R/'assets/people';out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene;scene.render.fps=30;rig=next(o for o in scene.objects if o.type=='ARMATURE')
for tr in rig.animation_data.nla_tracks:tr.mute=True
for name in ['Pet','Feed']:
 src=bpy.data.actions['Work'];rig.animation_data.action=src;scene.frame_set(18);bpy.context.view_layer.update()
 pose={b.name:(b.location.copy(),b.rotation_quaternion.copy(),b.scale.copy()) for b in rig.pose.bones}
 action=bpy.data.actions.new(name);action.use_fake_user=True;rig.animation_data.action=action
 for frame in range(61):
  phase=2*math.pi*frame/60
  for b in rig.pose.bones:
   loc,rot,scale=pose[b.name];b.location=loc;b.rotation_quaternion=rot;b.scale=scale
   if b.name=='neck_01':b.rotation_quaternion=rot@Quaternion((0,0,1),math.sin(phase)*.018)
   b.keyframe_insert('rotation_quaternion',frame=frame);b.keyframe_insert('location',frame=frame);b.keyframe_insert('scale',frame=frame)
base=bpy.data.actions['Talk'];action=bpy.data.actions.new('ThrowBall');action.use_fake_user=True;start,end=base.frame_range
for frame in range(43):
 p=frame/42;rig.animation_data.action=base;t=start+(end-start)*p;scene.frame_set(int(t),subframe=t-int(t));bpy.context.view_layer.update();upper=rig.pose.bones['upperarm_l'];old_upper=upper.rotation_quaternion.copy();old_lower=rig.pose.bones['lowerarm_l'].rotation_quaternion.copy();old_hand=rig.pose.bones['hand_l'].rotation_quaternion.copy();d=(upper.bone.tail_local-upper.bone.head_local).normalized();phase=min(1,p/.45);target=Vector((.94*(1-phase)+.25*phase,-.15*(1-phase)-.95*phase,.3)).normalized();swing=d.rotation_difference(target);rotation=swing@Quaternion(d,math.radians(-90))@upper.bone.matrix_local.to_quaternion();upper.matrix=Matrix.LocRotScale(upper.head.copy(),rotation,Vector((1,1,1)));bpy.context.view_layer.update();weight=1 if p<.62 else max(0,1-(p-.62)/.38);upper.rotation_quaternion=old_upper.slerp(upper.rotation_quaternion,weight);rig.pose.bones['lowerarm_l'].rotation_quaternion=old_lower.slerp(Quaternion((1,0,0),math.radians(85-62*phase)),weight);rig.pose.bones['hand_l'].rotation_quaternion=old_hand.slerp(Quaternion((1,0,0),math.radians(-12*phase)),weight)
 for b in rig.pose.bones:
  if b.name.endswith('_l') and b.name.startswith(('index_','middle_','ring_','pinky_','thumb_')):b.rotation_quaternion=b.rotation_quaternion.slerp(Quaternion(),weight)
 rig.animation_data.action=action
 for b in rig.pose.bones:b.keyframe_insert('rotation_quaternion',frame=frame);b.keyframe_insert('location',frame=frame)
rig.animation_data.action=bpy.data.actions['Idle'];scene.frame_set(0);bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT')
for o in scene.objects:
 if o.type in ['ARMATURE','MESH']:o.select_set(True)
bpy.context.view_layer.objects.active=rig;bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ache-caretaker.blend'),compress=True);bpy.ops.export_scene.gltf(filepath=str(out/'Ache-caretaker.glb'),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_nla_strips=False,export_frame_range=False,export_force_sampling=True,export_morph=True,export_morph_animation=False)
(out/'manifest.json').write_text(json.dumps({'name':'阿澈','source':'C方向首版V1.1副本','actions':[a.name for a in bpy.data.actions],'notes':'Pet/Feed复用跪姿作业循环并在运行中对准动物，ThrowBall为本轮制作；动作接触由互动系统校正。'},ensure_ascii=False,indent=2))
print('Caretaker ready',len(bpy.data.actions))
