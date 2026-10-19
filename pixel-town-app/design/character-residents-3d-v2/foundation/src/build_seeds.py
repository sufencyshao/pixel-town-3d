import bpy,bmesh,json,math,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[1]
source_manifest=json.loads((R/'reference/source-manifest.json').read_text())

def mat(name,color,rough=.7):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 p=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
 if p is None:
  p=m.node_tree.nodes.new('ShaderNodeBsdfPrincipled');out=next((n for n in m.node_tree.nodes if n.type=='OUTPUT_MATERIAL'),None)
  if out is None:out=m.node_tree.nodes.new('ShaderNodeOutputMaterial')
  m.node_tree.links.new(p.outputs['BSDF'],out.inputs['Surface'])
 p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough
 return m

def bounds(o):
 pts=[o.matrix_world@v.co for v in o.data.vertices]
 return [[min(v[i] for v in pts),max(v[i] for v in pts)] for i in range(3)]

def topo(o):
 bm=bmesh.new();bm.from_mesh(o.data)
 raw={'vertices':len(bm.verts),'faces':len(bm.faces),'boundaryEdges':sum(e.is_boundary for e in bm.edges)}
 bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00002)
 todo=set(bm.verts);comps=[]
 while todo:
  first=todo.pop();q=[first];size=0
  while q:
   v=q.pop();size+=1
   for e in v.link_edges:
    w=e.other_vert(v)
    if w in todo:todo.remove(w);q.append(w)
  comps.append(size)
 raw['weldedQAOnly']={'vertices':len(bm.verts),'boundaryEdges':sum(e.is_boundary for e in bm.edges),'components':sorted(comps,reverse=True)}
 bm.free();return raw

# Compare with the already-delivered C rig rather than assuming that an upstream label proves compatibility.
bpy.ops.wm.open_mainfile(filepath=str(R.parents[1]/'character-natural-3d-v1/assets/01-Ache.blend'))
reference_rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
canonical_names=[b.name for b in reference_rig.data.bones]
manifest={'schemaVersion':1,'date':'2026-10-18','status':'FROZEN','coordinateSystem':{'units':'meters','up':'+Z','front':'-Y','rigScale':[1,1,1],'meshCoordinates':'rig local; all mesh and rig matrix_world are identity','restPose':'T-pose, unanimated'},'source':{'author':'Quaternius','pack':'Universal Base Characters Standard','license':'CC0-1.0','official':'https://quaternius.com/packs/universalbasecharacters.html','github':source_manifest['repo'],'commit':source_manifest['commit'],'scope':'Standard contains Superhero Male and Female only; Regular and Teen are not claimed or supplied'},'canonicalBones':canonical_names,'seeds':[]}
for sex in ['Male','Female']:
 key=sex.lower();bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.ops.import_scene.gltf(filepath=str(R/'vendor/base'/f'Superhero_{sex}_FullBody.gltf'))
 scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.render.fps=30
 rig=next(o for o in scene.objects if o.type=='ARMATURE');rig.name='Resident_Base_Rig'
 body=next(o for o in scene.objects if o.type=='MESH' and 'superhero' in o.name.lower());body.name='Body'
 eyes=bpy.data.objects.get('Eyes');brows=bpy.data.objects.get('Eyebrows')
 for o in list(scene.objects):
  if o not in [rig,body,eyes,brows]:bpy.data.objects.remove(o,do_unlink=True)
 for a in list(bpy.data.actions):bpy.data.actions.remove(a)
 rig.animation_data_clear();rig.data.pose_position='POSE'
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 dz=-min(v.co.z for v in body.data.vertices)
 for o in [body,eyes,brows]:
  for v in o.data.vertices:v.co.z+=dz
  o.data.update()
 bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
 for b in rig.data.edit_bones:b.head.z+=dz;b.tail.z+=dz
 bpy.ops.object.mode_set(mode='OBJECT')
 body.data.materials.clear();body.data.materials.append(mat('Skin_Neutral',(.64,.45,.34),.76))
 for p in body.data.polygons:p.material_index=0
 brows.data.materials.clear();brows.data.materials.append(mat('Eyebrow_Neutral',(.035,.025,.02),.8))
 for p in brows.data.polygons:p.material_index=0
 # The source eyes remain the mature, genuinely UV-textured separate eye mesh.
 for m in eyes.data.materials:
  if m and m.use_nodes:
   p=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
   if p:p.inputs['Roughness'].default_value=.36
 bpy.context.view_layer.update()
 assert [b.name for b in rig.data.bones]==canonical_names,(sex,'canonical bones changed')
 assert len(rig.data.bones)==65
 for o in [rig,body,eyes,brows]:assert max(abs(o.matrix_world[i][j]-(1 if i==j else 0)) for i in range(4) for j in range(4))<1e-6,(sex,o.name)
 for o in [body,eyes,brows]:
  assert all(sum(g.weight for g in v.groups)>0.99 for v in o.data.vertices)
  assert all(sum(g.weight for g in v.groups)<1.01 for v in o.data.vertices)
  assert any(m.type=='ARMATURE' and m.object==rig for m in o.modifiers)
 result={'base':f'Quaternius Superhero {sex}','sex':key,'gltf':f'vendor/base/Superhero_{sex}_FullBody.gltf','blend':f'{key}-seed.blend','glb':f'{key}-seed.glb','rigName':rig.name,'bodyObject':body.name,'eyeObject':eyes.name,'browObject':brows.name,'height':bounds(body)[2][1],'floorTranslationZ':dz,'bodyBounds':bounds(body),'source':manifest['source'],'materials':{o.name:[m.name for m in o.data.materials] for o in [body,eyes,brows]},'meshAudit':{o.name:topo(o) for o in [body,eyes,brows]},'matrixWorld':{o.name:[list(row) for row in o.matrix_world] for o in [rig,body,eyes,brows]},'bodyRegionCoordinates':{'space':'rig local','head':{'anchorBone':'Head','neckBaseZ':rig.data.bones['neck_01'].head_local.z,'headBaseZ':rig.data.bones['Head'].head_local.z,'topZ':bounds(body)[2][1]},'torso':{'pelvisZ':rig.data.bones['pelvis'].head_local.z,'waistZ':rig.data.bones['spine_01'].head_local.z,'chestZ':rig.data.bones['spine_03'].head_local.z},'limbs':{name:{'head':list(rig.data.bones[name].head_local),'tail':list(rig.data.bones[name].tail_local)} for name in ['upperarm_l','lowerarm_l','hand_l','thigh_l','calf_l','foot_l','ball_l']},'note':'Full source body is continuous and uncut. No clothing is faked by skin material regions. Garment generation and hidden skin removal happen downstream.'},'canonicalBones':canonical_names,'restBones':{b.name:{'head':list(b.head_local),'tail':list(b.tail_local),'parent':b.parent.name if b.parent else None,'matrixLocal':[list(row) for row in b.matrix_local],'useDeform':b.use_deform} for b in rig.data.bones}}
 bpy.ops.object.select_all(action='SELECT');bpy.context.view_layer.objects.active=rig
 bpy.ops.outliner.orphans_purge(do_local_ids=True,do_linked_ids=False,do_recursive=True)
 bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(R/result['blend']),compress=True)
 bpy.ops.export_scene.gltf(filepath=str(R/result['glb']),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_materials='EXPORT')
 result['sha256']={name:hashlib.sha256((R/result[name]).read_bytes()).hexdigest() for name in ['blend','glb']}
 (R/f'{key}-seed.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
 manifest['seeds'].append(result)
(R/'seed-manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False))
print('FOUNDATION SEEDS FROZEN',[(s['sex'],s['height']) for s in manifest['seeds']])
