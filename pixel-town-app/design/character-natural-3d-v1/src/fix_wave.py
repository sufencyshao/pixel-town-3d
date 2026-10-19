"""Patch only Wave in the delivered native model; retain the other 18 clips."""
import bpy,json,sys
from pathlib import Path
root=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(root/'src'))
from wave_pose import bake_wave
from wave_fingerprint import fingerprints

bpy.ops.wm.open_mainfile(filepath=str(root/'assets/01-Ache.blend'))
before=fingerprints(bpy);rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
for track in rig.animation_data.nla_tracks:track.mute=True
bake_wave(bpy,rig,bpy.context.scene)
after=fingerprints(bpy)
assert before==after,'Geometry or an unrelated animation changed'
assert len(bpy.data.actions)==19
(root/'qa/wave-preservation.json').write_text(json.dumps({'date':'2026-10-17','meshes_unchanged':True,'other_18_actions_unchanged':True,'fingerprints':after},ensure_ascii=False,indent=2))
rig.animation_data.action=bpy.data.actions['Idle'];bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
bpy.ops.object.select_all(action='DESELECT')
for obj in bpy.context.scene.objects:
 if obj.type in ['ARMATURE','MESH']:obj.select_set(True)
bpy.context.view_layer.objects.active=rig;bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(root/'assets/01-Ache.blend'),compress=True)
bpy.ops.export_scene.gltf(filepath=str(root/'assets/01-Ache.glb'),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_nla_strips=False,export_frame_range=False,export_force_sampling=True,export_morph=True,export_morph_animation=False)
meta=json.loads((root/'assets/manifest.json').read_text());meta['wave_revision']='1.1 shoulder roll and elbow hinge correction';(root/'assets/manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
print('Wave corrected; all mesh data and other 18 clips unchanged')
