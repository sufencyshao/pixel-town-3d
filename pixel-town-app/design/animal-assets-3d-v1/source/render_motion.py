import bpy,json,math
from pathlib import Path
from mathutils import Vector
B=Path(__file__).resolve().parents[1];M=json.loads((B/'assets/manifest.json').read_text());targets={1:[('Walk',12),('Eat',18),('Rest',16)],7:[('Walk',10),('Wag',12),('Rest',16)],12:[('Fly',6),('Fly',18),('Eat',18)],16:[('Hop',12),('Eat',18),('Rest',16)],19:[('Walk',12),('Hide',12)],20:[('Eat',48),('Rest',16)]}
for e in M['animals']:
 ix=int(e['id'][:2])
 if ix not in targets:continue
 for acname,frame in targets[ix]:
  bpy.ops.wm.open_mainfile(filepath=str(B/'assets'/(e['id']+'.blend')));sc=bpy.context.scene;rig=next(o for o in sc.objects if o.type=='ARMATURE');rig.animation_data.action=bpy.data.actions[acname]
  if rig.animation_data.action.slots:rig.animation_data.action_slot=rig.animation_data.action.slots[0]
  for t in rig.animation_data.nla_tracks:t.mute=True
  sc.frame_set(frame);h=e['height'];l=e['length'];sz=max(h,l)*1.15;center=Vector((0,0,h*.45))
  def aim(o):o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
  bpy.ops.object.camera_add(location=center+Vector((1.3,-2,1))*sz);cam=bpy.context.object;aim(cam);cam.data.type='ORTHO';cam.data.ortho_scale=sz*1.3;sc.camera=cam
  for pos,power in [((2,-3,4),250),((-3,-1,2),130)]:
   bpy.ops.object.light_add(type='AREA',location=center+Vector(pos)*sz);light=bpy.context.object;aim(light);light.data.energy=power*sz*sz;light.data.size=sz*2
  sc.world=bpy.data.worlds.new('MotionQA');sc.world.color=(.45,.45,.45);sc.render.engine='CYCLES';sc.cycles.samples=12;sc.render.resolution_x=480;sc.render.resolution_y=480;sc.render.resolution_percentage=100;sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.filepath=str(B/'qa'/(e['id']+'-'+acname+'-'+str(frame)+'.png'));sc.view_settings.view_transform='AgX';bpy.ops.render.render(write_still=True)
