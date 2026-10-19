import bpy,sys,json,math,hashlib
from mathutils import Vector
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));from hair_builder import create_hair,create_facial_hair
D=json.loads((R.parent/'identity/identities.json').read_text())['characters']

def mat(name,color,rough=.8):
 if isinstance(color,str):color=tuple((lambda c:c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4)(int(color.lstrip('#')[i:i+2],16)/255) for i in (0,2,4))
 m=bpy.data.materials.new(name);m.diffuse_color=(*color[:3],1);m.use_nodes=True
 p=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
 if p is None:
  p=m.node_tree.nodes.new('ShaderNodeBsdfPrincipled');out=next((n for n in m.node_tree.nodes if n.type=='OUTPUT_MATERIAL'),None) or m.node_tree.nodes.new('ShaderNodeOutputMaterial');m.node_tree.links.new(p.outputs['BSDF'],out.inputs['Surface'])
 p.inputs['Base Color'].default_value=(*color[:3],1);p.inputs['Roughness'].default_value=rough;return m

report=[]
for i,who in enumerate(D):
 # Sex is resolved in the identity dataset; partner entries have female designs.
 female=('female' in who['id'] or who['id'] in ['hai-qin-yan','kanna','rui','xin','xin-fragrance'])
 bpy.ops.wm.open_mainfile(filepath=str(R/('female-seed.blend' if female else 'male-seed.blend')))
 scene=bpy.context.scene;rig=bpy.data.objects['Resident_Base_Rig'];body=bpy.data.objects['Body']
 base=rig.data.bones['Head'].head_local.z-.035
 verts=[v.co for v in body.data.vertices if v.co.z>=base]
 bounds={'min':[min(p[k] for p in verts) for k in range(3)],'max':[max(p[k] for p in verts) for k in range(3)]}
 def bind(ob,bone):
  ob.parent=rig;vg=ob.vertex_groups.new(name=bone);vg.add(list(range(len(ob.data.vertices))),1,'REPLACE');modifier=ob.modifiers.new('Head skin','ARMATURE');modifier.object=rig
 objects=create_hair(rig,who['features'],bounds,mat,bind)+create_facial_hair(rig,who['features'],bounds,mat,bind)
 assert objects and all(o.type=='MESH' for o in objects)
 assert all(o.vertex_groups.get('Head') and all(len(v.groups)>0 for v in o.data.vertices) for o in objects)
 import bmesh
 cap=next(o for o in objects if o.name.startswith('Continuous scalp cap'));bm=bmesh.new();bm.from_mesh(cap.data);boundary=sum(e.is_boundary for e in bm.edges);nonmanifold=sum(not e.is_manifold for e in bm.edges);bm.free()
 assert boundary==0 and nonmanifold==0,(who['id'],boundary,nonmanifold)
 record={'id':who['id'],'name':who['name'],'hairStyle':who['features']['hairStyle'],'headBounds':bounds,'meshCount':len(objects),'vertices':sum(len(o.data.vertices) for o in objects),'allHeadWeighted':True,'scalpBoundaryEdges':boundary,'scalpNonManifoldEdges':nonmanifold}
 report.append(record)
 scene.render.engine='CYCLES';scene.cycles.samples=8;scene.cycles.use_denoising=True;scene.render.resolution_x=360;scene.render.resolution_y=420;scene.render.resolution_percentage=100
 scene.world=bpy.data.worlds.new('Portrait QA World');scene.world.color=(.18,.18,.18);scene.view_settings.view_transform='AgX'
 for name,loc,power,size in [('Key',(-2,-3,4),220,4),('Fill',(2,-2,2),140,3),('Rim',(0,2,3),220,3)]:
  bpy.ops.object.light_add(type='AREA',location=loc);ob=bpy.context.object;ob.data.energy=power;ob.data.shape='DISK';ob.data.size=size;ob.rotation_euler=(Vector((0,0,1.6))-ob.location).to_track_quat('-Z','Y').to_euler()
 bpy.ops.object.camera_add();camera=bpy.context.object;scene.camera=camera;camera.data.type='ORTHO';camera.data.ortho_scale=.62
 top=bounds['max'][2];target=Vector((0,0,top-.18));camera.location=(.14,-3,top-.13);camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
 scene.render.filepath=str(R/'qa'/f'hair-{i+1:02d}.png');bpy.ops.render.render(write_still=True)
 if i in [11,12,15,16,18,19,32,35,38]:
  camera.location=(.3,3,top-.1);camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(R/'qa'/f'hair-{i+1:02d}-back.png');bpy.ops.render.render(write_still=True)
(R/'qa/hair-validation.json').write_text(json.dumps({'status':'passed','count':len(report),'identities':report,'source':'Quaternius CC0 mature mesh topology + bespoke closed scalp, solid fringe/tails/braids/curls. Long hair currently rigid Head-bound.'},indent=2,ensure_ascii=False))
print('HAIR QA PASSED',len(report))
