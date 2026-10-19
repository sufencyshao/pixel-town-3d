import bpy, json, math, hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path('/Users/summerwindy/Desktop/AI Chat/pixel-town-app/design/cafe-3d-v1')
OUT=ROOT/'blender-validation'
bpy.ops.wm.read_factory_settings(use_empty=True)
result=bpy.ops.import_scene.gltf(filepath=str(ROOT/'H01-cafe.glb'))
model_objects=list(bpy.context.scene.objects)
meshes=[o for o in model_objects if o.type=='MESH']
tri=0; invalid=[]; degenerate=0; no_material=[]
coords=[]
for o in meshes:
 o.data.calc_loop_triangles();tri+=len(o.data.loop_triangles)
 if not o.data.materials:no_material.append(o.name)
 for v in o.data.vertices:
  if not all(math.isfinite(x) for x in v.co):invalid.append(o.name)
  coords.append(o.matrix_world@v.co)
 for t in o.data.loop_triangles:
  a,b,c=[o.data.vertices[i].co for i in t.vertices]
  if (b-a).cross(c-a).length<1e-10:degenerate+=1
lo=[min(c[i] for c in coords) for i in range(3)];hi=[max(c[i] for c in coords) for i in range(3)]
images=[]
for im in bpy.data.images:
 images.append({'name':im.name,'width':im.size[0],'height':im.size[1],'has_data':im.has_data,'packed':bool(im.packed_file)})
 if im.has_data and not im.packed_file:im.pack()
report={'blender':bpy.app.version_string,'source_sha256':hashlib.sha256((ROOT/'H01-cafe.glb').read_bytes()).hexdigest(),'import_result':list(result),'objects':len(model_objects),'meshes':len(meshes),'triangles':tri,'materials':len(bpy.data.materials),'images':images,'nonfinite_vertices':invalid,'degenerate_triangles':degenerate,'meshes_without_material':no_material,'bounds_xyz_metres':[hi[i]-lo[i] for i in range(3)],'bounds_min':lo,'bounds_max':hi}
# Organize editable subassemblies as collections; keep imported parenting.
scene=bpy.context.scene;scene.name='01 Exterior'
colnames=['01 Building','02 Roof','03 FrontFacade','04 EastFacade','05 Furniture','06 Terrace','07 Planters','08 Studio']
cols={n:bpy.data.collections.new(n) for n in colnames}
for c in cols.values():scene.collection.children.link(c)
def ancestors(o):
 while o:
  yield o.name;o=o.parent
for o in model_objects:
 chain=list(ancestors(o))
 dest='01 Building'
 if 'RemovableRoof' in chain:dest='02 Roof'
 elif 'FrontFacade' in chain:dest='03 FrontFacade'
 elif 'EastFacade' in chain:dest='04 EastFacade'
 elif 'Interior' in chain:dest='05 Furniture'
 elif 'Terrace' in chain:dest='06 Terrace'
 elif 'Landscape' in chain:dest='07 Planters'
 for c in list(o.users_collection):c.objects.unlink(o)
 cols[dest].objects.link(o)
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
# Studio additions are separate from imported model.
def studio(o):
 for c in list(o.users_collection):c.objects.unlink(o)
 cols['08 Studio'].objects.link(o)
def material(n,c):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True;m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(*c,1);return m
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.31));ground=bpy.context.object;ground.name='Studio Ground';ground.data.materials.append(material('Studio Ivory',(.69,.69,.62)));studio(ground)
world=bpy.data.worlds.new('Cafe Studio World');world.use_nodes=True;world.node_tree.nodes.get('Background').inputs[0].default_value=(.78,.85,.92,1);world.node_tree.nodes.get('Background').inputs[1].default_value=.6;scene.world=world
def light(n,kind,loc,energy,size=None):
 data=bpy.data.lights.new(n,kind);data.energy=energy
 if size is not None:data.shape='DISK';data.size=size
 ob=bpy.data.objects.new(n,data);cols['08 Studio'].objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector((0,0,0))-ob.location).to_track_quat('-Z','Y').to_euler();return ob
sun=light('Sun','SUN',(-12,-17,23),2.3);sun.data.angle=.12
light('Large Softbox','AREA',(1,-8,14),1900,10)
light('Rear Fill','AREA',(4,10,9),1300,8)
def camera(n,loc,target):
 d=bpy.data.cameras.new(n);d.lens=48;d.clip_end=300;o=bpy.data.objects.new(n,d);cols['08 Studio'].objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
cam=camera('Camera Exterior',(25,-31,14),(0,-.7,1.6));scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True;scene.cycles.device='CPU'
scene.render.resolution_x=1400;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.view_settings.view_transform='AgX'
interior=scene.copy();interior.name='02 Interior Cutaway';interior.use_fake_user=True;interior.camera=camera('Camera Interior',(21,-27,24),(0,0,.65))
for n in ['02 Roof','03 FrontFacade','04 EastFacade']:interior.view_layers[0].layer_collection.children[n].exclude=True
# Render choices remain in two scenes, cameras in the studio collection.
for sc in [scene,interior]:
 sc.render.resolution_x=1400;sc.render.resolution_y=1000
# Select model root, establish useful material viewport.
bpy.context.window.scene=scene
bpy.ops.object.select_all(action='DESELECT')
root=bpy.data.objects.get('H01_Creekside_Cafe');root.select_set(True);bpy.context.view_layer.objects.active=root
for scr in bpy.data.screens:
 for area in scr.areas:
  if area.type=='VIEW_3D':
   space=area.spaces.active;space.shading.type='SOLID';space.shading.color_type='MATERIAL';space.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'H01-Cafe.blend'))
(OUT/'import-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('IMPORT_AUDIT',json.dumps(report,ensure_ascii=False),flush=True)
for sc,filename in [(scene,'blender-exterior.png'),(interior,'blender-interior.png')]:
 sc.render.filepath=str(OUT/filename);bpy.ops.render.render(write_still=True,scene=sc.name);print('RENDER_COMPLETE',filename,flush=True)
print('BLENDER_VALIDATION_COMPLETE',flush=True)
