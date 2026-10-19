"""Cover preserved upper trapezius skin with weighted fabric; keep all30 baked actions."""
import bpy,bmesh,json,sys
from pathlib import Path
R=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(R/'src'))
from build_residents import normalize_glb_quaternions
for p in sorted((R/'assets').glob('*/manifest.json')):
 c=json.loads(p.read_text());bpy.ops.wm.open_mainfile(filepath=str(p.parent/'character.blend'));old=bpy.data.objects.get('Shoulder fabric')
 if old:bpy.data.objects.remove(old,do_unlink=True)
 skin=bpy.data.objects['Skin'];rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');top=next(o for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith('Top_'))
 o=skin.copy();o.data=skin.data.copy();o.name='Shoulder fabric';bpy.context.collection.objects.link(o);o.shape_key_clear();neck=c['dimensions']['verticalMap'][-2][1];bm=bmesh.new();bm.from_mesh(o.data)
 keep=[]
 for f in bm.faces:
  v=f.calc_center_median()
  if neck-.015<v.z<neck+.055 and .072*c['design']['headScale']<abs(v.x)<c['design']['shoulder']*.60:keep.append(f)
 bmesh.ops.delete(bm,geom=[f for f in bm.faces if f not in keep],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00002);bm.to_mesh(o.data);bm.free();o.data.update()
 for v in o.data.vertices:v.co+=v.normal*.004
 o.data.materials.clear();o.data.materials.append(top.data.materials[0])
 for f in o.data.polygons:f.material_index=0;f.use_smooth=True
 # Same planar fabric UV contract as the selected top.
 for uv in list(o.data.uv_layers):o.data.uv_layers.remove(uv)
 uv=o.data.uv_layers.new(name='GarmentUV')
 for f in o.data.polygons:
  for i in f.loop_indices:
   v=o.data.vertices[o.data.loops[i].vertex_index].co;uv.data[i].uv=((v.x*1.65+.5)*2.6,v.z*1.45*2.6)
 o['residentId']=c['id'];o['part']=o.name
 rig.animation_data.action=next(a for a in bpy.data.actions if a.name=='Idle');bpy.context.scene.frame_set(0);bpy.context.view_layer.update();bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(p.parent/'character.blend'),compress=True)
 bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
 for item in bpy.context.scene.objects:
  if item.type=='MESH':item.select_set(True)
 bpy.context.view_layer.objects.active=rig
 bpy.ops.export_scene.gltf(filepath=str(p.parent/'character.glb'),export_format='GLB',use_selection=True,export_extras=True,export_animations=True,export_animation_mode='ACTIONS',export_nla_strips=False,export_frame_range=False,export_force_sampling=False,export_morph=True,export_morph_animation=False,export_optimize_animation_size=True)
 normalize_glb_quaternions(p.parent/'character.glb')
 bpy.ops.export_scene.gltf(filepath=str(p.parent/'runtime.glb'),export_format='GLB',use_selection=True,export_extras=True,export_animations=False,export_morph=True)
 c['meshes']=sum(o.type=='MESH' for o in bpy.context.scene.objects);(p.parent/'manifest.json').write_text(json.dumps(c,ensure_ascii=False,indent=2));print('SHOULDER_FINISHED',c['id'],flush=True)
records=[json.loads(p.read_text()) for p in sorted((R/'assets').glob('*/manifest.json'))];order={c['id']:i for i,c in enumerate(json.loads((R/'identity/identities.json').read_text())['characters'])};records.sort(key=lambda c:order[c['id']]);m=json.loads((R/'assets/manifest.json').read_text());m['characters']=records;(R/'assets/manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2))
