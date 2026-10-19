import bpy,json,math,struct
from pathlib import Path
R=Path(__file__).resolve().parent.parent;meta=json.loads((R/'assets/manifest.json').read_text());checks=[]
def check(name,ok,info=None):
 assert ok,(name,info);checks.append({'name':name,'pass':True,'info':info});print('PASS',name)
bpy.ops.wm.open_mainfile(filepath=str(R/'assets/01-Ache.blend'));rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
check('native skeleton has 65 bones',len(rig.data.bones)==65);check('native 19 actions',set(bpy.data.actions)==set(bpy.data.actions[name] for name in meta['animations']) and len(meta['animations'])==19)
check('separate weighted clothes',all(bpy.data.objects.get(n) and any(m.type=='ARMATURE' for m in bpy.data.objects[n].modifiers) for n in ['Cotton_T_Shirt','Denim_Trousers','Sneakers_l_Upper','Sneakers_l_Sole','Sneakers_r_Upper','Sneakers_r_Sole','Denim_Waistband','Ribbed_Collar']))
for track in rig.animation_data.nla_tracks:track.mute=True
for name in meta['animations']:
 action=bpy.data.actions[name];rig.animation_data.action=action
 for fraction in [0,.5,1]:
  start,end=action.frame_range;t=start+(end-start)*fraction;bpy.context.scene.frame_set(int(t),subframe=t-int(t));bpy.context.view_layer.update();check(name+' finite skeleton '+str(fraction),all(math.isfinite(v) for p in rig.pose.bones for row in p.matrix for v in row))
keys={k.name for o in bpy.context.scene.objects if o.type=='MESH' and o.data.shape_keys for k in o.data.shape_keys.key_blocks};check('Blink Smile Talk shape targets',{'Blink','Smile','Talk'}<=keys)
check('native textures packed',all(img.packed_file or img.source=='GENERATED' for img in bpy.data.images if img.type!='RENDER_RESULT'))
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(R/'assets/01-Ache.glb'));rigs=[o for o in bpy.context.scene.objects if o.type=='ARMATURE'];check('GLB roundtrip skeleton',len(rigs)==1 and len(rigs[0].data.bones)==65);check('GLB roundtrip 19 actions',set(meta['animations'])==set(bpy.data.actions.keys()))
b=(R/'assets/01-Ache.glb').read_bytes();n=struct.unpack_from('<I',b,12)[0];data=json.loads(b[20:20+n]);check('all GLB mesh nodes skinned',all('skin' in o for o in data['nodes'] if 'mesh' in o));check('GLB facial morph names',{'Blink','Smile','Talk'}<={name for m in data['meshes'] for name in m.get('extras',{}).get('targetNames',[])})
(R/'qa/model-validation.json').write_text(json.dumps({'date':'2026-10-17','checks':checks},ensure_ascii=False,indent=2));print('PASSED',len(checks))
