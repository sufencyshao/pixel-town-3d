import bpy,json,math,struct
from pathlib import Path
R=Path(__file__).resolve().parent.parent;checks=[]
def check(name,ok,info=None):
 assert ok,(name,info)
 checks.append({'name':name,'pass':True,'info':info});print('PASS',name,info or '')
for folder in sorted((R/'assets').iterdir()):
 if not folder.is_dir():continue
 bpy.ops.wm.open_mainfile(filepath=str(folder/'Ache.blend'));rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
 check(folder.name+' native bones',len(rig.data.bones)==65)
 check(folder.name+' native actions',{'Idle','Walk','Wave'}==set(bpy.data.actions.keys()))
 for track in rig.animation_data.nla_tracks:track.mute=True
 for name in ['Idle','Walk','Wave']:
  rig.animation_data.action=bpy.data.actions[name]
  for frame in [0,12,24,36]:
   bpy.context.scene.frame_set(frame);bpy.context.view_layer.update();check(folder.name+' '+name+' finite pose '+str(frame),all(math.isfinite(x) for p in rig.pose.bones for row in p.matrix for x in row))
 rig.animation_data.action=bpy.data.actions['Idle'];bpy.context.scene.frame_set(0);bpy.ops.file.pack_all();check(folder.name+' textures portable',all(img.packed_file or img.source=='GENERATED' for img in bpy.data.images if img.type!='RENDER_RESULT'))
 bpy.ops.wm.save_as_mainfile(filepath=str(folder/'Ache.blend'),compress=True)
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(folder/'Ache.glb'))
 rigs=[o for o in bpy.context.scene.objects if o.type=='ARMATURE'];check(folder.name+' GLB roundtrip skeleton',len(rigs)==1 and len(rigs[0].data.bones)==65)
 check(folder.name+' GLB roundtrip actions',{'Idle','Walk','Wave'}==set(bpy.data.actions.keys()))
 blob=(folder/'Ache.glb').read_bytes();n=struct.unpack_from('<I',blob,12)[0];data=json.loads(blob[20:20+n]);check(folder.name+' all GLB mesh nodes declare skins',all('skin' in node for node in data['nodes'] if 'mesh' in node))
 # Blender's material-import helper creates a small Icosphere that is not an asset node.
 asset_names={node.get('name') for node in data['nodes'] if 'mesh' in node}
 check(folder.name+' GLB bound meshes',all(any(m.type=='ARMATURE' for m in o.modifiers) for o in bpy.context.scene.objects if o.type=='MESH' and o.name in asset_names))
(R/'qa/model-validation.json').write_text(json.dumps({'date':'2026-10-17','checks':checks},ensure_ascii=False,indent=2));print('PASSED',len(checks))
