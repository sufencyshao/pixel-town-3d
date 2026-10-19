import bpy,math,json
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
R=Path(__file__).resolve().parent.parent;V=R/'vendor/quaternius'
STYLES=[('A-chibi','大头 Q 版',.56,2.65,.85,1.35),('B-cartoon','修长卡通',.82,1.65,.95,1.12),('C-natural','偏写实比例',1.,1.,1.,1.)]

def mat(name,color,rough=.65):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;return m

def collect_action(rig,name,frame_count,source=None,wave=False,vertical_scale=1):
 rig.animation_data_create();rig.animation_data.action=None
 for tr in rig.animation_data.nla_tracks:tr.mute=True
 action=bpy.data.actions.new(name);rig.animation_data.action=action
 for frame in range(frame_count+1):
  phase=frame/frame_count
  rig.animation_data.action=None
  if source:
   src,src_action=source;src.animation_data.action=src_action;start,end=src_action.frame_range;sample=start+(end-start)*phase;bpy.context.scene.frame_set(int(sample),subframe=sample-int(sample))
   for pb in rig.pose.bones:
    sb=src.pose.bones.get(pb.name)
    if sb:
     pb.rotation_mode='QUATERNION';pb.rotation_quaternion=sb.rotation_quaternion.copy();pb.location=sb.location.copy();pb.scale=(1,1,1)
     # Translation in each bone's local axes. The pelvis bob scales with the torso.
     pb.location*=vertical_scale
  bpy.context.view_layer.update()
  if wave:
   pb=rig.pose.bones['upperarm_l'];s=pb.head.copy();length=(pb.bone.tail_local-pb.bone.head_local).length
   direction=Vector((.95,-.10,.30)).normalized();q=(pb.bone.tail_local-pb.bone.head_local).normalized().rotation_difference(direction)@pb.bone.matrix_local.to_quaternion();pb.matrix=Matrix.LocRotScale(s,q,Vector((1,1,1)));bpy.context.view_layer.update()
   pb=rig.pose.bones['lowerarm_l'];s=pb.head.copy();direction=Vector((.20+.30*math.sin(phase*math.tau*2),-.18,.98)).normalized();q=(pb.bone.tail_local-pb.bone.head_local).normalized().rotation_difference(direction)@pb.bone.matrix_local.to_quaternion();pb.matrix=Matrix.LocRotScale(s,q,Vector((1,1,1)));bpy.context.view_layer.update()
   pb=rig.pose.bones['hand_l'];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=Quaternion((0,1,0),math.pi/2)@Quaternion((0,0,1),math.radians(12)*math.sin(phase*math.tau*2))
   for finger in rig.pose.bones:
    if finger.name.endswith('_l') and finger.name.startswith(('index_','middle_','pinky_','ring_','thumb_')):finger.rotation_quaternion=Quaternion()
   pb=rig.pose.bones['Head'];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=pb.rotation_quaternion@Quaternion((0,1,0),math.radians(4)*math.sin(phase*math.tau))
  rig.animation_data.action=action
  for pb in rig.pose.bones:
   pb.keyframe_insert('rotation_quaternion',frame=frame);pb.keyframe_insert('location',frame=frame)
 action.use_fake_user=True;rig.animation_data.action=None
 track=rig.animation_data.nla_tracks.new();track.name=name;strip=track.strips.new(name,0,action);strip.action_frame_start=0;strip.action_frame_end=frame_count
 return action

def stylized_head(rig,base,skin,hair_mat):
 body=next(o for o in base if o.name=='SuperHero_Male')
 import bmesh
 bm=bmesh.new();bm.from_mesh(body.data);bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.co.z>1.555],context='VERTS');bm.to_mesh(body.data);bm.free();body.data.update()
 for o in list(base):
  if o.name.startswith(('Eyes','Eyebrows','Hair_')):base.remove(o);bpy.data.objects.remove(o,do_unlink=True)
 white=mat('Warm eye whites',(.94,.91,.85));brown=mat('Brown iris',(.22,.085,.018));dark=mat('Eye and lash',(.013,.009,.006));pink=mat('Soft cheek',(.74,.31,.22));mouth=mat('Smile',(.17,.034,.021))
 def bind(o):
  o.parent=rig;vg=o.vertex_groups.new(name='Head');vg.add(list(range(len(o.data.vertices))),1,'REPLACE');mod=o.modifiers.new('Head skin','ARMATURE');mod.object=rig;base.append(o);return o
 def ellipsoid(name,loc,size,material):
  bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,location=loc);o=bpy.context.object;o.name=name;o.scale=size;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);o.data.materials.append(material)
  for f in o.data.polygons:f.use_smooth=True
  return bind(o)
 ellipsoid('Round face',(0,.008,1.695),(.121,.099,.125),skin)
 for sign in [-1,1]:
  ellipsoid('Ear',(sign*.121,.007,1.677),(.019,.019,.030),skin)
  ellipsoid('Lash outline',(sign*.049,-.085,1.704),(.030,.010,.036),dark)
  ellipsoid('Eye white',(sign*.049,-.093,1.705),(.028,.011,.034),white)
  ellipsoid('Brown iris',(sign*.049,-.103,1.703),(.018,.005,.026),brown)
  ellipsoid('Pupil',(sign*.049,-.107,1.703),(.008,.0025,.018),dark)
  ellipsoid('Eye catchlight',(sign*.049-.005,-.110,1.714),(.0045,.0015,.006),white)
  ellipsoid('Cheek',(sign*.078,-.073,1.662),(.015,.004,.008),pink)
  o=ellipsoid('Brow',(sign*.049,-.084,1.752),(.028,.006,.0045),hair_mat)
 ellipsoid('Button nose',(0,-.093,1.672),(.011,.013,.014),skin)
 ellipsoid('Open smile',(0,-.0835,1.637),(.028,.008,.014),mouth)
 ellipsoid('Smile teeth',(0,-.091,1.643),(.023,.003,.004),white)
 # A curved crown plus a loose, uneven fringe makes a short black hairstyle.
 bpy.ops.mesh.primitive_uv_sphere_add(segments=28,ring_count=16,location=(0,.014,1.707));cap=bpy.context.object;cap.name='Short hair crown';cap.scale=(.130,.106,.129);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 bm=bmesh.new();bm.from_mesh(cap.data);bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.co.z<1.742 and v.co.y<.045 or v.co.z<1.668],context='VERTS');bm.to_mesh(cap.data);bm.free();cap.data.materials.append(hair_mat)
 for f in cap.data.polygons:f.use_smooth=True
 bind(cap)
 for i in range(7):
  x=-.106+i*.033;z=1.785+.023*(1-(x/.13)**2);tip=x-.020+.014*math.sin(i);bottom=1.737+.020*((i+2)%3)/2
  vertices=[(x-.025,-.042,z),(x+.026,-.042,z+.006),(x+.022,-.083,z-.022),(tip,-.104,bottom),(x-.024,-.083,z-.022)]
  me=bpy.data.meshes.new('Fringe lock');me.from_pydata(vertices,[],[(0,1,2),(0,2,4),(4,2,3)]);me.materials.append(hair_mat);o=bpy.data.objects.new('Fringe lock',me);bpy.context.collection.objects.link(o);bind(o)
 return base

results=[]
for key,title,body_scale,head_scale,width,eye_scale in STYLES:
 bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;scene.render.fps=30
 bpy.ops.import_scene.gltf(filepath=str(V/'base/Superhero_Male_FullBody.gltf'))
 rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');rig.name='Ache_Rig';base=[o for o in scene.objects if o.type=='MESH' and o.name!='Icosphere']
 for o in list(scene.objects):
  if o.name=='Icosphere':bpy.data.objects.remove(o,do_unlink=True)
 bpy.ops.import_scene.gltf(filepath=str(V/'hair/Hair_SimpleParted.gltf'));hair=next(o for o in scene.objects if o.name.startswith('Hair_SimpleParted'));base.append(hair)
 vg=hair.vertex_groups.new(name='Head');vg.add(list(range(len(hair.data.vertices))),1,'REPLACE');mod=hair.modifiers.new('Follow head','ARMATURE');mod.object=rig;hair.parent=rig
 # The reference uses a short tousled fringe; add small asymmetry to the base hair.
 for v in hair.data.vertices:
  if v.co.y<-.015 and v.co.z>1.73:v.co.x+=.018*math.sin(v.co.z*85+v.co.x*30)
 # Body-topology material regions make a simple tee, trousers and shoes.
 skin=mat('Skin',(.74,.48,.32));tee=mat('Black cotton tee',(.014,.017,.019));jeans=mat('Blue denim',(.055,.15,.29));shoe=mat('Warm white sneakers',(.74,.70,.59));belt=mat('Dark belt',(.045,.035,.026));hair_mat=mat('Black short hair',(.016,.014,.012))
 body=next(o for o in base if o.name=='SuperHero_Male');body.data.materials.clear()
 for m in [skin,tee,jeans,shoe,belt]:body.data.materials.append(m)
 for p in body.data.polygons:
  c=p.center
  if c.z<.11:p.material_index=3
  elif c.z<.98:p.material_index=2
  elif c.z<1.025 and abs(c.x)<.22:p.material_index=4
  elif c.z<1.56 and abs(c.x)<.39:p.material_index=1
  elif 1.37<c.z<1.49 and abs(c.x)<.39:p.material_index=1
  else:p.material_index=0
 for o in base:
  if o is hair or o.name.startswith('Eyebrows'):o.data.materials.clear();o.data.materials.append(hair_mat)
  if o.name.startswith('Eyes'):
   for m in o.data.materials:
    if m and m.use_nodes:
     bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.32
   # Enlarge both eyes around their own centres, without altering interocular spacing.
   for sign in [-1,1]:
    vs=[v for v in o.data.vertices if v.co.x*sign>0]
    center=sum((v.co for v in vs),Vector())/len(vs)
    for v in vs:v.co=center+(v.co-center)*eye_scale
 if key!='C-natural':base=stylized_head(rig,base,skin,hair_mat)
 neck=1.56;neck_y=.017
 def remap(v,head_factor=None):
  p=v.copy();t=max(0,min(1,(p.z-1.49)/.09));t=t*t*(3-2*t) if head_factor is None else head_factor;scale=width+(head_scale-width)*t
  p.x*=scale;p.y=neck_y+(p.y-neck_y)*scale
  p.z=p.z*body_scale if p.z<=neck else neck*body_scale+(p.z-neck)*head_scale
  return p
 # Geometry and bind skeleton are transformed together. Skin weights remain genuine.
 for o in base:
  for v in o.data.vertices:
   influence=sum(g.weight for g in v.groups if o.vertex_groups[g.group].name=='Head') if o is body else 1.
   v.co=remap(v.co,influence)
 bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
 for b in rig.data.edit_bones:
  head=remap(b.head);tail=remap(b.tail);b.head=head;b.tail=tail
 bpy.ops.object.mode_set(mode='OBJECT')
 # Normalize only the object scale, keeping the three proportions at equal display height.
 height=max((o.matrix_world@v.co).z for o in base for v in o.data.vertices);rig.scale=(1.65/height,)*3
 # Add a flat cloth collar as a mesh attached to upper chest with real weights.
 bpy.ops.import_scene.gltf(filepath=str(V/'UAL1_Standard.glb'));source=next(o for o in scene.objects if o.type=='ARMATURE' and o!=rig)
 source_actions={a.name:a for a in bpy.data.actions};source_meshes=[o for o in scene.objects if o.type=='MESH' and o not in base]
 # Preserve source clips as reference, export only three bounded sample actions.
 source.animation_data_create()
 for tr in source.animation_data.nla_tracks:tr.mute=True
 clips=[]
 clips.append(collect_action(rig,'Idle',60,(source,source_actions['Idle_Loop']),vertical_scale=body_scale))
 clips.append(collect_action(rig,'Walk',32,(source,source_actions['Walk_Loop']),vertical_scale=body_scale))
 clips.append(collect_action(rig,'Wave',72,(source,source_actions['Idle_Loop']),wave=True,vertical_scale=body_scale))
 for o in source_meshes+[source]:bpy.data.objects.remove(o,do_unlink=True)
 for a in list(bpy.data.actions):
  if a not in clips:bpy.data.actions.remove(a)
 for tr in rig.animation_data.nla_tracks:tr.mute=True
 rig.animation_data.action=clips[0];scene.frame_set(0);bpy.context.view_layer.update()
 # Skinning and weighted vertices are checked before exporting.
 assert len(rig.data.bones)==65
 assert all(o.vertex_groups for o in base)
 bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
 for o in base:o.select_set(True)
 out=R/'assets'/key;out.mkdir(exist_ok=True)
 rig.animation_data.action=clips[0];scene.frame_set(0)
 for tr in rig.animation_data.nla_tracks:tr.mute=True
 bpy.ops.outliner.orphans_purge(do_local_ids=True,do_linked_ids=False,do_recursive=True)
 bpy.ops.file.pack_all()
 bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ache.blend'),compress=True)
 bpy.ops.export_scene.gltf(filepath=str(out/'Ache.glb'),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_nla_strips=False,export_frame_range=False,export_force_sampling=True,export_morph=False,export_materials='EXPORT')
 result={'id':key,'name':title,'bones':len(rig.data.bones),'meshes':len(base),'clips':['Idle','Walk','Wave'],'height':1.65,'bodyScale':body_scale,'headScale':head_scale,'eyeScale':eye_scale,'glbBytes':(out/'Ache.glb').stat().st_size};results.append(result);print('SAMPLE',result)
(R/'assets/manifest.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
