import bpy,os
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent.parent
for key in os.environ.get('RESIDENTIAL_KEYS','courtyard,hero,apartment-5').split(','):
 p=ROOT/key;bpy.ops.wm.open_mainfile(filepath=str(p/(key+'.blend')));sc=bpy.data.scenes['01 Exterior'];bpy.context.window.scene=sc
 target=Vector((3 if key=='hero' else 5,-4.5 if key!='apartment-5' else -5.6,3.4));location=target+Vector((10,-13,4))
 d=bpy.data.cameras.new('Joint review camera');d.type='ORTHO';d.ortho_scale=9 if key!='apartment-5' else 11;o=bpy.data.objects.new('Joint review camera',d);sc.collection.objects.link(o);o.location=location;o.rotation_euler=(target-location).to_track_quat('-Z','Y').to_euler();sc.camera=o;sc.render.filepath=str(p/'joint-detail.png');bpy.ops.render.render(write_still=True)
