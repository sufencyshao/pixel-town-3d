import bpy,bmesh,math,json,sys
from pathlib import Path
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(R/'src'))
from wave_pose import bake_wave
bpy.ops.wm.open_mainfile(filepath=str(R/'reference/selected-C.blend'));scene=bpy.context.scene;scene.render.fps=30
rig=next(o for o in scene.objects if o.type=='ARMATURE');rig.name='Ache_Rig';rig.animation_data.action=None
for tr in rig.animation_data.nla_tracks:tr.mute=True
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
body=next(o for o in scene.objects if o.type=='MESH' and o.name=='SuperHero_Male')
def mat(name,color,rough=.7):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;p=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
 if not p:
  p=m.node_tree.nodes.new('ShaderNodeBsdfPrincipled');out=next((n for n in m.node_tree.nodes if n.type=='OUTPUT_MATERIAL'),None) or m.node_tree.nodes.new('ShaderNodeOutputMaterial');m.node_tree.links.new(p.outputs['BSDF'],out.inputs['Surface'])
 p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;return m
skin=body.data.materials[0]
def strip_faces(obj,keep):
 bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.delete(bm,geom=[f for f in bm.faces if not keep(f)],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(obj.data);bm.free();obj.data.update()
# A continuous garment surface avoids jagged triangle selection at the neckline.
def skin_object(o,weights):
 o.parent=rig
 for bone,ids in weights.items():
  g=o.vertex_groups.new(name=bone)
  for index,w in ids:g.add([index],w,'REPLACE')
 mod=o.modifiers.new('Character skin','ARMATURE');mod.object=rig
shirt_mat=mat('Cotton knit',(.016,.020,.022),.9)
# Use the body's continuous shoulder topology and original skin weights.
# A detached cylinder sleeve cannot deform reliably through raised-arm poses.
o=body.copy();o.data=body.data.copy();o.name='Cotton_T_Shirt';bpy.context.collection.objects.link(o)
strip_faces(o,lambda f:f.material_index==1)
bm=bmesh.new();bm.from_mesh(o.data);boundary={v for edge in bm.edges if edge.is_boundary for v in edge.verts}
for iteration in range(8):
 positions={v:sum((edge.other_vert(v).co for edge in v.link_edges if edge.is_boundary),Vector())/sum(1 for edge in v.link_edges if edge.is_boundary) for v in boundary}
 for v,point in positions.items():v.co=v.co.lerp(point,.35)
for v in boundary:
 if v.co.z<1.10:v.co.z=1.008
 elif abs(v.co.x)>.30:v.co.x=math.copysign(.382,v.co.x)
 elif v.co.z>1.40 and abs(v.co.x)<.14:
  angle=math.atan2((v.co.y-.025)/.067,v.co.x/.080);v.co=Vector((.080*math.cos(angle),.025+.067*math.sin(angle),1.535))
bm.to_mesh(o.data);bm.free();o.data.update()
for v in o.data.vertices:v.co+=v.normal*.009
for v in o.data.vertices:
 if v.co.z>1.50 and abs(v.co.x)<.115 and abs(v.co.y-.025)<.09:
  v.co.z=min(v.co.z,1.537)
for p in o.data.polygons:p.material_index=0;p.use_smooth=True
o.data.materials.clear();o.data.materials.append(shirt_mat)
if hasattr(o.data,'normals_split_custom_set'):o.data.normals_split_custom_set([(0,0,0)]*len(o.data.loops))
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
solid=o.modifiers.new('Cloth thickness','SOLIDIFY');solid.thickness=.003;solid.offset=0;bpy.ops.object.modifier_apply(modifier=solid.name)
for name,index,color in [('Denim_Trousers',2,(.06,.16,.30))]:
 o=body.copy();o.data=body.data.copy();o.name=name;bpy.context.collection.objects.link(o);strip_faces(o,lambda f:f.material_index==index)
 for v in o.data.vertices:
  p=v.co
  if index==2:
   hip=min(1,max(0,(p.z-.77)/.16));cx=(1 if p.x>=0 else -1)*.114*(1-hip);cy=.09-.05*min(1,max(0,p.z/.97));factor=1.12 if p.z<.8 else 1.09;p.x=cx+(p.x-cx)*factor;p.y=cy+(p.y-cy)*factor
  else:
   cx=(1 if p.x>=0 else -1)*.114;p.x=cx+(p.x-cx)*1.055;p.y=-.02+(p.y+.02)*1.04;p.z=.04+(p.z-.04)*1.04
 o.data.materials.clear();o.data.materials.append(mat(name,color,.92 if index==2 else .8))
 for p in o.data.polygons:p.material_index=0;p.use_smooth=True
 # Clear imported custom normals after altering the garment shape.
 if hasattr(o.data,'normals_split_custom_set'):o.data.normals_split_custom_set([(0,0,0)]*len(o.data.loops))
# A clean waistband covers the inherited polygonal jeans cut.
verts=[];fs=[]
for z in [.96,1.0]:
 for k in range(48):verts.append((.184*math.cos(k*math.tau/48),.025+.16*math.sin(k*math.tau/48),z))
for k in range(48):fs.append((k,(k+1)%48,48+(k+1)%48,48+k))
me=bpy.data.meshes.new('Waistband mesh');me.from_pydata(verts,[],fs);me.materials.append(mat('Denim waistband',(.055,.145,.275),.9));band=bpy.data.objects.new('Denim_Waistband',me);bpy.context.collection.objects.link(band);skin_object(band,{'pelvis':[(i,1) for i in range(len(verts))]})
for f in me.polygons:f.use_smooth=True
for p in body.data.polygons:
 if p.center.z>1.50 and abs(p.center.x)<.14 and abs(p.center.y-.02)<.12:p.material_index=0
strip_faces(body,lambda f:f.material_index!=3)

# A subtle smile/open-mouth shape, kept separate from body animation.
body.shape_key_add(name='Basis');smile=body.shape_key_add(name='Smile');talk=body.shape_key_add(name='Talk')
for i,v in enumerate(body.data.vertices):
 p=v.co;x=abs(p.x)
 if p.y<-.045 and 1.59<p.z<1.67 and x<.06:
  w=math.exp(-((p.z-1.635)/.018)**2-((p.y+.084)/.042)**2)
  smile.data[i].co.z+=.010*w*min(1,x/.03);smile.data[i].co.y-=.0015*w
  low=math.exp(-((p.z-1.623)/.018)**2-(x/.04)**2);talk.data[i].co.z-=.012*low;talk.data[i].co.y-=.002*low
# Relax the stern brow while keeping the adult face.
for o in list(scene.objects):
 if o.type!='MESH':continue
 if o.name.startswith('Eyebrows'):
  for v in o.data.vertices:
   v.co.z=1.710+(v.co.z-1.710)*.70+.004*max(0,1-abs(v.co.x)/.055)
 if o.name.startswith('Hair_SimpleParted'):
  for v in o.data.vertices:
   if v.co.z>1.73:v.co.z=1.73+(v.co.z-1.73)*.84
   if v.co.y<-.01:v.co.x+=.003*math.sin(v.co.z*90+v.co.x*40)
# The eyelid skin patches expand from the upper lid to cover each eyeball.
eyes=next(o for o in scene.objects if o.type=='MESH' and o.name=='Eyes');lids=eyes.copy();lids.data=eyes.data.copy();lids.name='Eyelids';bpy.context.collection.objects.link(lids);lids.data.materials.clear();lids.data.materials.append(skin)
for p in lids.data.polygons:p.material_index=0
coords=[v.co.copy() for v in lids.data.vertices];groups={sign:[i for i,p in enumerate(coords) if p.x*sign>0] for sign in [-1,1]};closed={}
for sign,ids in groups.items():
 center=sum((coords[i] for i in ids),Vector())/len(ids);miny=min(coords[i].y for i in ids);maxz=max(coords[i].z for i in ids)
 for i in ids:
  p=coords[i].copy();p.y=miny-.0015+(p.y-center.y)*.015;p.z=center.z+(p.z-center.z)*1.06;closed[i]=p
  lids.data.vertices[i].co=Vector((p.x,miny-.001,maxz+.001+(p.z-center.z)*.015))
lids.shape_key_add(name='Basis');blink=lids.shape_key_add(name='Blink')
for i,p in closed.items():blink.data[i].co=p
blink.value=0
# Belt buckle and shoe toe caps are independent weighted details.
def bind(obj,bone):
 obj.parent=rig;g=obj.vertex_groups.new(name=bone);g.add(list(range(len(obj.data.vertices))),1,'REPLACE');m=obj.modifiers.new('Character skin','ARMATURE');m.object=rig
bpy.ops.mesh.primitive_torus_add(major_radius=.080,minor_radius=.006,major_segments=48,minor_segments=10,location=(0,.025,1.535));collar=bpy.context.object;collar.name='Ribbed_Collar';collar.scale=(1,.84,1);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);collar.data.materials.append(mat('Ribbed cotton',(.012,.016,.018),.9));bind(collar,'spine_03')
# Reuse the finished casual sneaker mesh from Quaternius Modular Men.
# Keep the artist's toe/heel/sole topology and fit it to this character's feet.
shoe_source=json.loads((R/'reference/casual-shoes.json').read_text())
shoe_mats=[mat('Rubber ivory',(.76,.74,.68),.9),mat('Canvas sage',(.43,.47,.42),.84)]
for sign,side in [(1,'l'),(-1,'r')]:
 ids=[i for i,v in enumerate(shoe_source['vertices']) if v[0]*sign>0];source_points=[Vector(shoe_source['vertices'][i]) for i in ids]
 low=[min(v[k] for v in source_points) for k in range(3)];high=[max(v[k] for v in source_points) for k in range(3)]
 positions={i:((shoe_source['vertices'][i][0]-(low[0]+high[0])/2)/(high[0]-low[0])*.145+sign*.1143,(shoe_source['vertices'][i][1]-low[1])/(high[1]-low[1])*.30-.156,(shoe_source['vertices'][i][2]-low[2])/(high[2]-low[2])*.142-.009) for i in ids}
 for material_index,suffix in [(0,'Sole'),(1,'Upper')]:
  polygons=[f for f,mi in zip(shoe_source['faces'],shoe_source['material_indices']) if mi==material_index and all(i in positions for i in f)];used=sorted({i for f in polygons for i in f});lookup={old:i for i,old in enumerate(used)}
  me=bpy.data.meshes.new('Casual sneaker '+side+' '+suffix);me.from_pydata([positions[i] for i in used],[],[[lookup[i] for i in f] for f in polygons]);me.materials.append(shoe_mats[material_index]);shoe=bpy.data.objects.new('Sneakers_'+side+'_'+suffix,me);bpy.context.collection.objects.link(shoe);bind(shoe,'foot_'+side)
 foot_ids=sorted(positions);mapping={old:i for i,old in enumerate(foot_ids)};polygons=[[mapping[i] for i in f] for f in shoe_source['faces'] if all(i in mapping for i in f)];shoe_surface=BVHTree.FromPolygons([Vector(positions[i]) for i in foot_ids],polygons)
 for row,y in enumerate([-.045,-.02,.005,.03]):
  points=[]
  for dx in [-.025,0,.025]:
   x=sign*.1143+dx;hit=shoe_surface.ray_cast(Vector((x,y,.5)),Vector((0,0,-1)))[0]
   if hit:points.append((x,y,hit.z+.0025))
  if len(points)==3:
   curve=bpy.data.curves.new('Lace','CURVE');curve.dimensions='3D';curve.bevel_depth=.0018;curve.bevel_resolution=2;spline=curve.splines.new('POLY');spline.points.add(2)
   for point,co in zip(spline.points,points):point.co=(*co,1)
   lace=bpy.data.objects.new('Shoelace_'+side+'_'+str(row),curve);bpy.context.collection.objects.link(lace);curve.materials.append(shoe_mats[1]);bpy.ops.object.select_all(action='DESELECT');lace.select_set(True);bpy.context.view_layer.objects.active=lace;bpy.ops.object.convert(target='MESH');bind(bpy.context.object,'foot_'+side)
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,-.126,1.008));buckle=bpy.context.object;buckle.name='Belt_Buckle';buckle.dimensions=(.044,.009,.026);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);buckle.data.materials.append(mat('Brushed buckle',(.38,.37,.31),.4));bind(buckle,'pelvis')
# Preserve the three reviewed clips, add only relevant UAL1 clips.
original_actions={name:bpy.data.actions[name] for name in ['Idle','Walk','Wave']}
base_objects=set(scene.objects)
bpy.ops.import_scene.gltf(filepath=str(R/'reference/UAL1_Standard.glb'));source=next(o for o in scene.objects if o.type=='ARMATURE' and o!=rig);source.animation_data_create()
for tr in source.animation_data.nla_tracks:tr.mute=True
src_actions={a.name:a for a in bpy.data.actions if a.name not in original_actions}
add=[('Talk','Idle_Talking_Loop'),('Run','Jog_Fwd_Loop'),('Crouch','Crouch_Idle_Loop'),('CrouchWalk','Crouch_Fwd_Loop'),('SitDown','Sitting_Enter'),('Sit','Sitting_Idle_Loop'),('StandUp','Sitting_Exit'),('PickUp','PickUp_Table'),('Work','Fixing_Kneeling'),('Dance','Dance_Loop'),('Swim','Swim_Fwd_Loop'),('JumpStart','Jump_Start'),('JumpLoop','Jump_Loop'),('JumpLand','Jump_Land'),('Nod','Idle_Loop'),('ShakeHead','Idle_Loop')]
for target,src in add:
 action=bpy.data.actions.new(target);original_actions[target]=action;src_action=src_actions[src];start,end=src_action.frame_range;duration=(end-start)/scene.render.fps;frames=max(24,round(duration*30))
 for frame in range(frames+1):
  rig.animation_data.action=None;source.animation_data.action=src_action;t=start+(end-start)*frame/frames;scene.frame_set(int(t),subframe=t-int(t))
  for pb in rig.pose.bones:
   sb=source.pose.bones.get(pb.name)
   if sb:pb.rotation_mode='QUATERNION';pb.rotation_quaternion=sb.rotation_quaternion.copy();pb.location=sb.location.copy();pb.scale=(1,1,1)
  if target in ['Nod','ShakeHead']:
   pb=rig.pose.bones['Head'];axis=(1,0,0) if target=='Nod' else (0,1,0);angle=math.radians(13 if target=='Nod' else 22)*math.sin(frame/frames*math.tau*2);pb.rotation_quaternion=pb.rotation_quaternion@Quaternion(axis,angle)
  rig.animation_data.action=action
  for pb in rig.pose.bones:pb.keyframe_insert('rotation_quaternion',frame=frame);pb.keyframe_insert('location',frame=frame)
 action.use_fake_user=True
for o in list(scene.objects):
 if o not in base_objects:bpy.data.objects.remove(o,do_unlink=True)
original_actions['Wave']=bake_wave(bpy,rig,scene)
for a in list(bpy.data.actions):
 if a.name not in original_actions:bpy.data.actions.remove(a)
rig.animation_data.action=original_actions['Idle'];scene.frame_set(0);bpy.context.view_layer.update()
bpy.ops.object.select_all(action='DESELECT')
for o in scene.objects:
 if o.type in ['ARMATURE','MESH']:o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.outliner.orphans_purge(do_local_ids=True,do_linked_ids=False,do_recursive=True);bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(R/'assets/01-Ache.blend'),compress=True)
bpy.ops.export_scene.gltf(filepath=str(R/'assets/01-Ache.glb'),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_nla_strips=False,export_frame_range=False,export_force_sampling=True,export_morph=True,export_morph_animation=False)
meta={'id':'01_hero_male','name':'阿澈','style':'C-natural','bones':len(rig.data.bones),'animations':list(original_actions),'morphs':['Blink','Smile','Talk'],'source':'selected C sample + Quaternius UAL1 + Modular Men Casual sneakers','status':'first character refinement, pending visual feedback','wave_revision':'1.1 shoulder roll and elbow hinge correction'}
(R/'assets/manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2));print('CHARACTER',meta)
