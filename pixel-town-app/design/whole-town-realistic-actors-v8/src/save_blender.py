import bpy,json,math
from mathutils import Vector
from pathlib import Path
R=Path(__file__).resolve().parent.parent
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(R/'Town-with-original-actors.glb'))
actors=json.loads((R/'actors.json').read_text());missing=[a['id'] for a in actors if not bpy.data.objects.get(a['id'])];assert not missing,missing
bpy.context.scene.unit_settings.system='METRIC'
bpy.context.scene['scope']='Static placement snapshot: original town + 45 people + 16 animals. Full original GLBs and separate source motion clips accompany the HTML runtime.'
# Provide an opening overview without altering the imported models or materials.
camera_data=bpy.data.cameras.new('Overview');camera=bpy.data.objects.new('Overview',camera_data);bpy.context.collection.objects.link(camera);camera.location=(285,-345,285);camera.rotation_euler=((Vector((5,0,0))-camera.location).to_track_quat('-Z','Y').to_euler());camera_data.type='ORTHO';camera_data.ortho_scale=440;bpy.context.scene.camera=camera
light_data=bpy.data.lights.new('Daylight','SUN');light_data.energy=2.2;light=bpy.data.objects.new('Daylight',light_data);bpy.context.collection.objects.link(light);light.rotation_euler=(math.radians(25),math.radians(-25),math.radians(-20))
bpy.context.scene.world=bpy.data.worlds.new('Town Day');bpy.context.scene.world.color=(.55,.6,.65)
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':area.spaces.active.region_3d.view_distance=360;area.spaces.active.region_3d.view_location=(0,0,0);area.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(R/'Town-with-original-actors.blend'),compress=True)
report={'actorsPresent':len(actors),'people':45,'animals':16,'objects':len(bpy.data.objects),'armatures':sum(o.type=='ARMATURE' for o in bpy.data.objects),'meshes':sum(o.type=='MESH' for o in bpy.data.objects),'missingActors':missing,'externalImages':len([i for i in bpy.data.images if i.source=='FILE' and not i.packed_file]),'animationActions':len(bpy.data.actions),'scope':'Static placement snapshot; runtime animations are provided by offline HTML and separate source clips.'}
(R/'qa/blender-import.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report))
