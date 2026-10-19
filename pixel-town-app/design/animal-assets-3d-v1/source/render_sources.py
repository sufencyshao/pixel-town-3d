import bpy,math
from mathutils import Vector
from pathlib import Path
base=Path(__file__).resolve().parents[1]
def aim(o,pt):o.rotation_euler=(Vector(pt)-o.location).to_track_quat('-Z','Y').to_euler()
for f in ['cat','ShibaInu','Husky','Horse']:
 bpy.ops.wm.open_mainfile(filepath=str(base/'source'/f'{f}.blend'))
 for o in list(bpy.context.scene.objects):
  if o.type=='MESH' and not any(m.type=='ARMATURE' for m in o.modifiers):bpy.data.objects.remove(o,do_unlink=True)
 arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');arm.animation_data.action=None
 for t in arm.animation_data.nla_tracks:t.mute=True
 mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH')
 for p in mesh.data.polygons:p.use_smooth=True
 bounds=[mesh.matrix_world@Vector(c) for c in mesh.bound_box];lo=Vector([min(v[i] for v in bounds) for i in range(3)]);hi=Vector([max(v[i] for v in bounds) for i in range(3)]);center=(lo+hi)/2;size=(hi-lo).length
 bpy.ops.object.camera_add(location=center+Vector((1.0,-1.6,.9))*size*.7);cam=bpy.context.object;aim(cam,center);bpy.context.scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=size*.95
 for xyz,power,size2 in [((3,-4,6),1400,5),((-4,-1,4),700,4)]:
  bpy.ops.object.light_add(type='AREA',location=center+Vector(xyz));l=bpy.context.object;l.data.energy=power;l.data.shape='DISK';l.data.size=size2;aim(l,center)
 bpy.context.scene.world=bpy.data.worlds.new('World');bpy.context.scene.world.color=(.6,.6,.6)
 sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=12;sc.render.resolution_x=640;sc.render.resolution_y=640;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.render.filepath=str(base/'qa'/f'{f}-source.png');sc.view_settings.view_transform='Standard';bpy.ops.render.render(write_still=True)
