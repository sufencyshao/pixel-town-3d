"""Read-only Blender studio review of built residents.
Run Blender --background --python this.py -- --ids 02_hero_female
No .blend source is saved. Every output is inside qa-identity.
"""
import bpy, bmesh, json, math, sys, hashlib, time
from pathlib import Path
from mathutils import Vector

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
ids=sys.argv[sys.argv.index('--ids')+1].split(',') if '--ids' in sys.argv else ['02_hero_female']
identity_rows=json.loads((ROOT/'identity/identities.json').read_text())['characters']
design_heights={c['id']:c['design']['height'] for c in identity_rows}
if '--all' in sys.argv:ids=[c['id'] for c in identity_rows]
source_mode='glb' if '--glb' in sys.argv else 'blend'
static_only='--static-only' in sys.argv
SHOTS=[
 ('Idle',0,'front',(0,-5,1),(.0,0,.83),2.02),
 ('Idle',0,'quarter',(3,-5,2.4),(0,0,.85),2.08),
 ('Idle',0,'side',(5,0,1.25),(0,0,.83),2.02),
 ('Idle',0,'face',(.7,-5,1.55),(0,0,1.445),.52),
 ('Walk',.28,'front',(0,-5,1),(0,0,.83),2.02),
 ('Walk',.28,'side',(5,0,1.25),(0,0,.83),2.02),
 ('Sit',.5,'front',(0,-5,1.0),(0,0,.65),1.75),
 ('Sit',.5,'side',(5,0,1.1),(0,0,.65),1.75),
 ('Wave',.57,'quarter',(3,-5,2.4),(0,0,.85),2.08),
 ('Wave',.57,'side',(5,0,1.25),(0,0,.83),2.02),
 ('Wave',.85,'front',(0,-5,1),(0,0,.83),2.02),
]

def aim(obj,target):
 obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()

def light(name,location,energy,size):
 data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.shape='DISK';data.size=size
 o=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(o);o.location=location;aim(o,(0,0,.8))

def pose(rig,action,phase):
 for track in rig.animation_data.nla_tracks:track.mute=True
 for b in rig.pose.bones:b.matrix_basis.identity()
 a=bpy.data.actions.get(action) or next((a for a in bpy.data.actions if a.name.startswith(action+'_')),None)
 if a:
  rig.animation_data.action=a
  if a.slots:rig.animation_data.action_slot=a.slots[0]
  f=a.frame_range[0]+(a.frame_range[1]-a.frame_range[0])*phase
  bpy.context.scene.frame_set(int(f),subframe=f-int(f))
 else:rig.animation_data.action=None;f=0
 bpy.context.view_layer.update()
 return f

for cid in ids:
 source=ROOT/'assets'/cid/('character.'+source_mode)
 if not source.exists():continue
 out=HERE/cid if source_mode=='blend' else HERE/cid/'glb-reimport'
 out.mkdir(parents=True,exist_ok=True)
 if source_mode=='blend':bpy.ops.wm.open_mainfile(filepath=str(source))
 else:
  bpy.ops.wm.read_factory_settings(use_empty=True)
  bpy.ops.import_scene.gltf(filepath=str(source))
 scene=bpy.context.scene;rig=next(o for o in scene.objects if o.type=='ARMATURE')
 input_hash=hashlib.sha256(source.read_bytes()).hexdigest()
 pose(rig,'Idle',0)
 report={'id':cid,'sourceMode':source_mode,'source':str(source),'sourceSha256':input_hash,'meshes':[],'shots':[]}
 for o in list(scene.objects):
  if o.type!='MESH':continue
  bm=bmesh.new();bm.from_mesh(o.data)
  report['meshes'].append({'name':o.name,'meshDataName':o.data.name,'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),
   'boundaryEdges':sum(e.is_boundary for e in bm.edges),'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges),
   'materials':[m.name for m in o.data.materials], 'worldBounds':[[min((o.matrix_world@v.co)[k] for v in o.data.vertices) for k in range(3)],[max((o.matrix_world@v.co)[k] for v in o.data.vertices) for k in range(3)]]})
  bm.free()
 scene.render.engine='CYCLES';scene.cycles.samples=16
 scene.cycles.use_denoising=True
 scene.render.resolution_x=512;scene.render.resolution_y=640;scene.render.resolution_percentage=100
 scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
 scene.world=bpy.data.worlds.new('QA studio world');scene.world.use_nodes=True
 scene.world.node_tree.nodes.clear()
 bg=scene.world.node_tree.nodes.new('ShaderNodeBackground');wo=scene.world.node_tree.nodes.new('ShaderNodeOutputWorld');scene.world.node_tree.links.new(bg.outputs['Background'],wo.inputs['Surface'])
 bg.inputs['Color'].default_value=(.71,.76,.67,1)
 bg.inputs['Strength'].default_value=.45
 scene.view_settings.view_transform='AgX'
 mat=bpy.data.materials.new('QA studio floor');mat.diffuse_color=(.64,.68,.59,1);mat.use_nodes=True
 mat.node_tree.nodes.clear()
 shader=mat.node_tree.nodes.new('ShaderNodeBsdfPrincipled');mo=mat.node_tree.nodes.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(shader.outputs['BSDF'],mo.inputs['Surface'])
 shader.inputs['Base Color'].default_value=(.64,.68,.59,1)
 shader.inputs['Roughness'].default_value=.9
 bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.012));plane=bpy.context.object;plane.name='QA-only floor';plane.data.materials.append(mat)
 light('QA key',(-3,-4,5),450,4);light('QA fill',(3,-1,3),180,3);light('QA rim',(1,3,4),250,3)
 camdata=bpy.data.cameras.new('QA camera');cam=bpy.data.objects.new('QA camera',camdata);bpy.context.collection.objects.link(cam);scene.camera=cam
 camdata.type='ORTHO';camdata.lens=60
 for action,phase,view,location,target,size in SHOTS:
  if static_only and action!='Idle':continue
  f=pose(rig,action,phase)
  # Scale generic camera heights for independently designed residents.
  height=design_heights.get(cid,rig.get('newDesignHeight',1.62));scale=height/1.62
  cam.location=tuple(v*scale for v in location);aim(cam,tuple(v*scale for v in target));camdata.ortho_scale=size*scale
  filename=f'{action}-{round(phase*100):02d}-{view}.png';scene.render.filepath=str(out/filename)
  bpy.ops.render.render(write_still=True)
  report['shots'].append({'action':action,'phase':phase,'frame':f,'view':view,'path':str(out/filename)})
 report['sourceHashUnchanged']=hashlib.sha256(source.read_bytes()).hexdigest()==input_hash
 (out/'render-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print('IDENTITY_QA_RENDERED',cid,flush=True)
