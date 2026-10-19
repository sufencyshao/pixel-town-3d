import bpy,math,json
from pathlib import Path
from mathutils import Vector
B=Path(__file__).resolve().parents[1];mf=B/'assets/manifest.json';M=json.loads(mf.read_text())
for ent in M['animals']:
 bpy.ops.wm.open_mainfile(filepath=str(B/'assets'/(ent['id']+'.blend')));sc=bpy.context.scene;rig=next(o for o in sc.objects if o.type=='ARMATURE');meshes=[o for o in sc.objects if o.type=='MESH'];baseLoc=rig.location.copy();old=list(bpy.data.actions);clips=[]
 for t in list(rig.animation_data.nla_tracks):rig.animation_data.nla_tracks.remove(t)
 for ac in old:
  name=ac.name;rig.animation_data.action=ac
  if ac.slots:rig.animation_data.action_slot=ac.slots[0]
  stop=ac.frame_range[1];count=math.ceil(stop);samples=[]
  for f in range(count+1):
   time=f*stop/count if count else 0;sc.frame_set(int(time),subframe=time-int(time));samples.append({b.name:(b.location.copy(),b.rotation_quaternion.copy(),b.scale.copy()) for b in rig.pose.bones})
  ac.name='SOURCE_'+name;rig.animation_data.action=None;new=bpy.data.actions.new(name);rig.animation_data.action=new
  root=rig.pose.bones.get('MotionRoot') or rig.pose.bones.get('Body') or rig.pose.bones.get('body');q=root.bone.matrix_local.to_quaternion()
  for f,poses in enumerate(samples):
   rig.location=baseLoc
   for n,(l,r,s) in poses.items():b=rig.pose.bones[n];b.location=l;b.rotation_mode='QUATERNION';b.rotation_quaternion=r;b.scale=s
   if name in ['Walk','Run','Hop']:v=rig.matrix_world.to_3x3()@(q@root.location);v.x=0;v.y=0;root.location=q.inverted()@(rig.matrix_world.to_3x3().inverted()@v)
   bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();mn=min((o.evaluated_get(dg).matrix_world@v.co).z for o in meshes for v in o.evaluated_get(dg).data.vertices)
   if mn<0:
    off=Vector((0,0,-mn));rig.location+=rig.parent.matrix_world.to_3x3().inverted()@off if rig.parent else off
   rig.keyframe_insert('location',frame=f)
   for b in rig.pose.bones:b.keyframe_insert('location',frame=f);b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('scale',frame=f)
  new.use_fake_user=True;clips.append(new);rig.animation_data.action=None;bpy.data.actions.remove(ac)
 rig.location=baseLoc
 for ac in clips:
  t=rig.animation_data.nla_tracks.new();t.name=ac.name;st=t.strips.new(ac.name,0,ac)
  if hasattr(st,'action_slot') and ac.slots:st.action_slot=ac.slots[0]
  t.mute=True
 for b in rig.pose.bones:b.matrix_basis.identity()
 bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(B/'assets'/(ent['id']+'.blend')))
 for t in rig.animation_data.nla_tracks:t.mute=False
 bpy.ops.export_scene.gltf(filepath=str(B/ent['glb']),export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_nla_strips=True,export_force_sampling=True,export_anim_slide_to_zero=True,export_materials='EXPORT',export_extras=True,export_cameras=False,export_lights=False)
 ent['bakedFps']=24;ent['locomotion']='in-place; wrapper moves in world';print('FINALIZED',ent['id'],flush=True)
tmp=mf.with_suffix('.json.tmp');tmp.write_text(json.dumps(M,ensure_ascii=False,indent=2));tmp.replace(mf)
