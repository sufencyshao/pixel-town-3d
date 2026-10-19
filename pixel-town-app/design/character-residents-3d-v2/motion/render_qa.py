import bpy,math,json
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
O=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(O/'qa/actor-motion.blend'));sc=bpy.context.scene;rig=next(o for o in sc.objects if o.type=='ARMATURE')
for ob in list(sc.objects):
 if ob.type in ['CAMERA','LIGHT']:bpy.data.objects.remove(ob,do_unlink=True)
sc.render.engine='BLENDER_WORKBENCH';sc.render.resolution_x=480;sc.render.resolution_y=420;sc.render.resolution_percentage=100
sc.world=sc.world or bpy.data.worlds.new('QA world')
sc.display.shading.light='STUDIO';sc.display.shading.studiolight_rotate_z=.3;sc.display.shading.color_type='MATERIAL';sc.display.shading.show_shadows=True;sc.display.shading.show_cavity=True;sc.display.shading.cavity_type='BOTH';sc.display.shading.background_type='WORLD';sc.world.color=(.84,.84,.82);sc.render.image_settings.file_format='PNG';sc.render.film_transparent=False
sc.view_settings.view_transform='Standard';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8'
def mat(n,c):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);return m
blue=mat('QA blue ceramic',(.16,.40,.53));paper=mat('QA warm paper',(.91,.85,.68));dark=mat('QA dark screen',(.04,.075,.09));silver=mat('QA utensil',(.67,.70,.70));cover=mat('QA book green',(.13,.29,.22));coffee=mat('QA water',(.22,.43,.51));screen=mat('QA phone lit screen',(.35,.63,.68))
props={}
def cube(n,loc,dim,m,parent=None):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);ob=bpy.context.object;ob.name=n;ob.dimensions=dim;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);ob.data.materials.append(m)
 if parent:ob.parent=parent
 return ob
def group(n):
 ob=bpy.data.objects.new('QA_'+n,None);sc.collection.objects.link(ob);props[n]=ob;return ob
def ringvessel(n,radius,depth,parent,m):
 vertices=[];faces=[];segments=36
 for r,z in [(radius*.72,-depth*.5),(radius,depth*.5),(radius*.89,depth*.5),(radius*.60,-depth*.30)]:
  for j in range(segments):vertices.append((r*math.cos(j*math.tau/segments),r*math.sin(j*math.tau/segments),z))
 for row in range(3):
  for j in range(segments):a=row*segments+j;b=row*segments+(j+1)%segments;faces.append((a,b,b+segments,a+segments))
 faces.append(tuple(range(3*segments,4*segments)))
 me=bpy.data.meshes.new(n);me.from_pydata(vertices,[],faces);me.materials.append(m);ob=bpy.data.objects.new(n,me);sc.collection.objects.link(ob);ob.parent=parent
 return ob
p=group('bowl');ringvessel('QA_Bowl',.11,.08,p,blue)
p=group('cup');ringvessel('QA_Cup',.039,.105,p,blue);cube('QA_Water',(0,0,.034),(.053,.053,.002),coffee,p)
p=group('spoon');cube('QA_SpoonHandle',(0,.015,0),(.009,.13,.007),silver,p);bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=1,location=(0,.095,0));ob=bpy.context.object;ob.name='QA_SpoonBowl';ob.scale=(.014,.022,.004);ob.data.materials.append(silver);ob.parent=p
p=group('phone');cube('QA_PhoneBody',(0,0,0),(.075,.145,.012),dark,p);cube('QA_PhoneScreen',(0,0,-.0065),(.063,.121,.001),screen,p)
p=group('open-book');cube('QA_BookCover',(0,0,-.012),(.21,.255,.007),cover,p)
for sign in [-1,1]:
 page=cube('QA_BookPages',(0,sign*.064,-.002),(.20,.122,.014),paper,p);page.rotation_euler.x=math.radians(-sign*5)
 for k in range(5):cube('QA_BookText',(-.025+k*.014,sign*.064,.006),(.002,.080,.001),dark,p)
# Optional low pillow solely shows the intended head-support area in LieRest.
pillow=cube('QA_OptionalLowPillow',(-.75*rig.scale.x,.02*rig.scale.x,.064*rig.scale.x),(.31*rig.scale.x,.22*rig.scale.x,.13*rig.scale.x),mat('QA pillow',(.77,.70,.58)))
bev=pillow.modifiers.new('QA softened pillow','BEVEL');bev.width=.035;bev.segments=3
pillow.hide_render=True
floor=cube('QA_Floor',(0,0,-.025),(200,200,.04),mat('QA floor',(.83,.84,.80)))
bpy.ops.object.camera_add();camera=bpy.context.object;camera.data.type='ORTHO';sc.camera=camera
manifest=json.loads((O/'actions.json').read_text());met={a['name']:a for a in manifest['actions']}
OUT=O/'qa/frames';OUT.mkdir(exist_ok=True)
actions=['Wave','Eat','Drink','Read','Phone','Stretch','LieDown','LieRest','GetUp']
shots=[]
for name in actions:
 for p in [0,.28,.57,.85]:
  a=bpy.data.actions[name];rig.animation_data.action=a;start,end=a.frame_range;f=start+(end-start)*p;sc.frame_set(int(f),subframe=f-int(f));bpy.context.view_layer.update()
  for prop in props.values():
   prop.hide_render=True
   for ch in prop.children:ch.hide_render=True
  active=[]
  for socket in met[name]['propSockets']:
   prop=props[socket['prop']];prop.hide_render=False
   for ch in prop.children:ch.hide_render=False
   q=Quaternion(socket['rotationQuaternionWXYZ']);prop.matrix_world=rig.matrix_world@rig.pose.bones[socket['bone']].matrix@Matrix.LocRotScale(Vector(socket['position']),q,Vector((1,1,1)));active+=list(prop.children)
  pillow.hide_render=not(name=='LieRest')
  actor=[ob for ob in sc.objects if ob.type=='MESH' and ob not in [floor,pillow] and not ob.name.startswith('QA_')]+active
  deps=bpy.context.evaluated_depsgraph_get();coords=[]
  for ob in actor:
   ev=ob.evaluated_get(deps);coords += [ev.matrix_world@Vector(co) for co in ev.bound_box]
  low=Vector([min(v[k] for v in coords) for k in range(3)]);high=Vector([max(v[k] for v in coords) for k in range(3)]);center=(low+high)/2
  for view,direction in [('front',Vector((0,-7,2.1))),('side',Vector((7,-.35,1.5)))]:
   camera.location=center+direction;camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler();bpy.context.view_layer.update()
   inv=camera.matrix_world.inverted();pc=[inv@v for v in coords];width=max(v.x for v in pc)-min(v.x for v in pc);height=max(v.y for v in pc)-min(v.y for v in pc);camera.data.ortho_scale=max(width,height*480/420)*1.30
   filename=f'{name}-{round(p*100):02}-{view}.png';sc.render.filepath=str(OUT/filename);bpy.ops.render.render(write_still=True)
   shots.append({'action':name,'phase':p,'frame':f,'view':view,'file':'frames/'+filename})
(O/'qa/render-shots.json').write_text(json.dumps(shots,indent=2));print('MOTION_QA_RENDERED',len(shots))
