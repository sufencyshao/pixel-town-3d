"""Individual C-natural residents. Inputs are frozen local licensed seeds and original identity audit.
Blender --background --python src/build_residents.py -- --ids 01_hero_male,02_hero_female
"""
import bpy,bmesh,math,json,sys,time,os,hashlib,random
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(R/'foundation'))
A=R/'assets';A.mkdir(exist_ok=True)
IDENTITIES=json.loads((R/'identity/identities.json').read_text())['characters']
SEEDS=json.loads((R/'foundation/seed-manifest.json').read_text())
MOTION=json.loads((R/'motion/actions.json').read_text())
FILTER=None
if '--ids' in sys.argv:FILTER=set(sys.argv[sys.argv.index('--ids')+1].split(','))

def color(value):
 if isinstance(value,str):
  s=value.lstrip('#');rgb=[int(s[i:i+2],16)/255 for i in [0,2,4]]
  # Blender shader and glTF baseColorFactor are linear, input audit colors are sRGB.
  return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb)
 return tuple(value)
def material(name,c,roughness=.8):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color(c),1);m.use_nodes=True
 p=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
 if not p:
  p=m.node_tree.nodes.new('ShaderNodeBsdfPrincipled');out=m.node_tree.nodes.new('ShaderNodeOutputMaterial');m.node_tree.links.new(p.outputs['BSDF'],out.inputs['Surface'])
 p.inputs['Base Color'].default_value=(*color(c),1);p.inputs['Roughness'].default_value=roughness
 return m

def mesh(name,vertices,faces,mat,rig=None,weights=None):
 me=bpy.data.meshes.new(name);me.from_pydata(vertices,[],faces);me.materials.append(mat);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o)
 for f in me.polygons:f.use_smooth=True
 uv=me.uv_layers.new(name='UVMap')
 for poly in me.polygons:
  for li in poly.loop_indices:
   v=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=((v.x*1.65+.5)*2.6,v.z*1.45*2.6)
 if rig:bind(o,rig,weights or 'spine_03')
 return o

def bind(o,rig,bone):
 o.parent=rig
 if isinstance(bone,str):weights={bone:[(i,1) for i in range(len(o.data.vertices))]}
 else:weights=bone
 for name,items in weights.items():
  g=o.vertex_groups.get(name) or o.vertex_groups.new(name=name)
  for i,w in items:
   if w>1e-6:g.add([i],w,'REPLACE')
 mod=next((m for m in o.modifiers if m.type=='ARMATURE'),None) or o.modifiers.new('Resident skin','ARMATURE');mod.object=rig
 return o

def ellipsoid(name,loc,size,mat,rig,bone='Head',segments=20,rings=12):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=loc);o=bpy.context.object;o.name=name;o.scale=size;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);o.data.materials.append(mat)
 for p in o.data.polygons:p.use_smooth=True
 return bind(o,rig,bone)

def box(name,loc,size,mat,rig,bone='spine_03',bevel=.004):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=size;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);o.data.materials.append(mat)
 if bevel:
  mod=o.modifiers.new('Soft edges','BEVEL');mod.width=bevel;mod.segments=2;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
 return bind(o,rig,bone)

def tube(name,points,radius,mat,rig,bone='Head',segments=8):
 # Transport a circular section along the path. Mesh output keeps offline GLB fully self-contained.
 verts=[];faces=[]
 for i,p in enumerate(points):
  p=Vector(p);tangent=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(0,i-1)])
  if tangent.length<1e-8:tangent=Vector((0,0,1))
  tangent.normalize();u=tangent.cross(Vector((0,0,1)))
  if u.length<.01:u=tangent.cross(Vector((0,1,0)))
  u.normalize();v=tangent.cross(u).normalized();rr=radius[i] if isinstance(radius,list) else radius
  for j in range(segments):verts.append(tuple(p+(u*math.cos(j*math.tau/segments)+v*math.sin(j*math.tau/segments))*rr))
 for i in range(len(points)-1):
  for j in range(segments):a=i*segments+j;b=i*segments+(j+1)%segments;faces.append((a,b,b+segments,a+segments))
 faces+=[tuple(range(segments-1,-1,-1)),tuple((len(points)-1)*segments+j for j in range(segments))]
 return mesh(name,verts,faces,mat,rig,bone)

def delete_faces(obj,keep):
 bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.delete(bm,geom=[f for f in bm.faces if not keep(f)],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(obj.data);bm.free();obj.data.update()

def clothing(body,rig,name,keep,mat,offset=.008,expand=1):
 o=body.copy();o.data=body.data.copy();o.name=name;bpy.context.collection.objects.link(o)
 # Source UV islands duplicate vertices; weld before smoothing the actual garment rim.
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00002);bm.to_mesh(o.data);bm.free();delete_faces(o,keep)
 if not o.data.vertices:bpy.data.objects.remove(o,do_unlink=True);return None
 # Smooth the actual cut boundary, while retaining source shoulder/arm/hip skin weights.
 bm=bmesh.new();bm.from_mesh(o.data);boundary={v for e in bm.edges if e.is_boundary for v in e.verts}
 for it in range(5):
  moves={v:sum((e.other_vert(v).co for e in v.link_edges if e.is_boundary),Vector())/sum(e.is_boundary for e in v.link_edges) for v in boundary if any(e.is_boundary for e in v.link_edges)}
  for v,p in moves.items():v.co=v.co.lerp(p,.22)
 bm.to_mesh(o.data);bm.free();o.data.update()
 for v in o.data.vertices:
  v.co+=v.normal*offset
  if expand!=1:
   cx=math.copysign(.114,v.co.x) if v.co.z<.94 else 0;v.co.x=cx+(v.co.x-cx)*expand;v.co.y=.04+(v.co.y-.04)*expand
 o.data.materials.clear();o.data.materials.append(mat)
 for p in o.data.polygons:p.material_index=0;p.use_smooth=True
 if hasattr(o.data,'normals_split_custom_set'):o.data.normals_split_custom_set([(0,0,0)]*len(o.data.loops))
 for old_uv in list(o.data.uv_layers):o.data.uv_layers.remove(old_uv)
 uv=o.data.uv_layers.new(name='GarmentUV');uv.active_render=True
 for poly in o.data.polygons:
  for li in poly.loop_indices:
   p=o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=((p.x*1.65+.5)*2.6,p.z*1.45*2.6)
 o.data.uv_layers.active=uv
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
 solid=o.modifiers.new('Fabric seam thickness','SOLIDIFY');solid.thickness=.003;solid.offset=0;bpy.ops.object.modifier_apply(modifier=solid.name)
 return o

def ring_garment(name,rig,mat,rings,leg_weight=False,pleat=0,front_open=False):
 verts=[];faces=[];weights={};n=48
 for j,(z,rx,ry,cy) in enumerate(rings):
  for k in range(n):
   t=k*math.tau/n;w=1+pleat*math.cos(t*12);p=(rx*math.cos(t)*w,cy+ry*math.sin(t)*w,z);idx=len(verts);verts.append(p)
   if z>=1.12:ws={'spine_02':.7,'spine_01':.3}
   elif z>=.94:ws={'pelvis':1}
   else:
    a=min(1,max(0,(.94-z)/.45));side='l' if p[0]>=0 else 'r';l=abs(p[0])/max(rx,.01);sym=max(0,.5-l*.7)
    ws={'pelvis':1-a,('thigh_'+side):a*(1-sym),('thigh_'+('r' if side=='l' else 'l')):a*sym}
    if leg_weight and z<.50:
     b=min(.8,(.50-z)/.5);ws={k:v*(1-b) for k,v in ws.items()};ws['calf_'+side]=b
   for bone,wgt in ws.items():weights.setdefault(bone,[]).append((idx,wgt))
 for j in range(len(rings)-1):
  for k in range(n):
   # Front seam split on coats permits hips and knees to flex.
   if front_open and k in [34,35,36,37]:continue
   faces.append((j*n+k,j*n+(k+1)%n,(j+1)*n+(k+1)%n,(j+1)*n+k))
 o=mesh(name,verts,faces,mat,rig,weights)
 for old_uv in list(o.data.uv_layers):o.data.uv_layers.remove(old_uv)
 uv=o.data.uv_layers.new(name='GarmentUV');uv.active_render=True
 for poly in o.data.polygons:
  for li in poly.loop_indices:
   p=o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=((p.x*1.65+.5)*2.6,p.z*1.45*2.6)
 solid=o.modifiers.new('Hem thickness','SOLIDIFY');solid.thickness=.003;solid.offset=0;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=solid.name)
 return o

def planar_patch(name,rig,mat,center,size,bone='spine_03'):
 x,y,z=center;w,h=size
 return mesh(name,[(x-w/2,y,z-h/2),(x+w/2,y,z-h/2),(x+w/2,y,z+h/2),(x-w/2,y,z+h/2)],[(0,1,2,3)],mat,rig,bone)

# Deterministic texture art for original garment motifs; no source raster is redrawn.
def make_patterns():
 folder=R/'reference/patterns';folder.mkdir(exist_ok=True)
 try:from PIL import Image,ImageDraw
 except ImportError:return
 for c in IDENTITIES:
  f=c['features'];pattern=f.get('pattern')
  if not pattern and c['id'].startswith('05_'):pattern='plaid'
  if not pattern and c['id'].startswith('23_'):pattern='plaid'
  if not pattern and c['id'].startswith('18_'):pattern='paint'
  if not pattern:continue
  img=Image.new('RGB',(256,256),f.get('topColor','#ddd'));d=ImageDraw.Draw(img)
  rng=random.Random(c['id'])
  if 'flower' in pattern:
   for x in range(24,256,64):
    for yy in range(24,256,64):
     y=yy+(32 if x%128 else 0);col=f.get('patternColor','#3a3530')
     for k in range(5):
      t=k*math.tau/5;px=x+math.cos(t)*7;py=y+math.sin(t)*7;d.ellipse((px-5,py-5,px+5,py+5),fill=col)
     d.ellipse((x-3,y-3,x+3,y+3),fill='#C1A36E')
  elif pattern=='plaid':
   for q in range(0,256,40):d.rectangle((q,0,q+13,256),fill='#392A29');d.rectangle((0,q,256,q+13),fill='#392A29')
   for q in range(10,256,40):d.line((q,0,q,256),fill='#B67A67',width=2);d.line((0,q,256,q),fill='#B67A67',width=2)
  elif pattern=='paint':
   for k in range(70):
    x,y=rng.randrange(256),rng.randrange(256);rr=rng.randrange(4,17);d.ellipse((x-rr,y-rr,x+rr,y+rr),fill=rng.choice(['#C7443B','#D8B81E','#3A81A3','#E88DAA','#75A46D']))
  img.save(folder/(c['id']+'.png'))

def patterned(mat,c):
 p=R/'reference/patterns'/(c['id']+'.png')
 if p.exists():
  img=bpy.data.images.load(str(p),check_existing=True);tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=img;tex.extension='REPEAT';shader=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');mat.node_tree.links.new(tex.outputs['Color'],shader.inputs['Base Color']);img.pack()
 return mat

def create_wardrobe(c,body,rig,seed):
 f=c['features'];top=f['topType'];bottom=f['bottomType'];hm=seed['bodyRegionCoordinates']['head'];neck=hm['neckBaseZ'];hip=seed['bodyRegionCoordinates']['torso']['pelvisZ'];elbow=rig.data.bones['lowerarm_l'].head_local.x;wrist=rig.data.bones['hand_l'].head_local.x
 # Distinct garments retain the source continuous deformation topology.
 long=top in ['coat','jacket','hoodie','chefcoat','uniform'] and f.get('sleeveLength') not in ['short','rolled-elbow']
 if c['id'].startswith(('06_','07_','21_','31_')):long=True
 if c['id'].startswith(('24_','34_','38_','39_','19_')):long=False
 sleeve= wrist-.015 if long else elbow-.025 if f.get('sleeveLength')=='rolled-elbow' else .36
 shirt_bottom=hip+.02
 def in_top(p):return shirt_bottom<p.z<neck+.005 and abs(p.x)<sleeve
 tshirtColor=f.get('underlayerColor',f['topColor']) if top in ['apron','vest','overalls'] else f['topColor']
 mat_top=material('Garment '+top,tshirtColor)
 if top not in ['apron','overalls','vest'] or c['id'].startswith('23_'):patterned(mat_top,c)
 garment=clothing(body,rig,'Top_'+top,lambda poly:in_top(poly.calc_center_median()),mat_top,offset=.009)
 ring_garment('Neckline binding',rig,mat_top,[(neck-.016,.067,.061,.025),(neck+.010,.066,.060,.025)])
 hem=.59
 if bottom=='dress' or top=='dress':
  hem=.14 if c['id']=='rui' else .60 if c['kind']=='codexmini' else .54
  if c['id']=='hai-qin-yan':hem=.61
  fabric=patterned(material('Dress skirt',f['bottomColor']),c)
  ring_garment('Dress_Skirt',rig,fabric,[(hip+.07,.195,.15,.035),(.86,.24,.17,.035),(.72,.275,.19,.035),(hem,.32,.215,.035)],leg_weight=True,pleat=.025 if c['id']=='rui' else .055)
  for z in [hem+.015,.76] if c['id'] in ['02_hero_female','xin','hai-qin-yan'] else [hem+.015]:
   rr=.32-(z-hem)*.28;ring_garment('Dress_Hem',rig,material('Hem',f.get('hemColor',f['bottomColor'])),[(z,rr,.215-(z-hem)*.18,.035),(z+.012,rr-.004,.21-(z-hem)*.18,.035)],leg_weight=True)
  if c['id']=='hai-qin-yan':
   for k in range(10):
    t=k*math.tau/10;ellipsoid('Petal',(.29*math.cos(t),.035+.20*math.sin(t),.68),(.07,.025,.13),material('Petal pale','#DCEBFF'),rig,'pelvis',16,10)
 elif bottom=='skirt':
  hem=.61 if c['id'] in ['20_student_female','xin-fragrance'] else .50
  fabric=material('Skirt fabric',f['bottomColor']);ring_garment('Skirt',rig,fabric,[(hip+.05,.192,.152,.035),(.81,.238,.177,.035),(hem,.276,.202,.035)],leg_weight=True,pleat=.06)
 else:
  hem=.58 if bottom=='shorts' else .075
  clothing(body,rig,'Bottom_'+bottom,lambda poly:hem<poly.calc_center_median().z<hip+.065,material('Bottom fabric',f['bottomColor']),offset=.010,expand=1.07 if bottom in ['jeans','uniform','overalls'] else 1.04)
 # Clean waist seam covers mesh selection rim.
 if bottom not in ['dress'] and top!='dress':ring_garment('Waist seam',rig,material('Waist',f['bottomColor']),[(hip+.02,.19,.149,.035),(hip+.06,.19,.149,.035)])
 # White socks and actual footwear; never turn feet into block placeholders.
 if f['shoeType'] in ['sneakers','maryjane','flats']:
  clothing(body,rig,'Socks',lambda poly:.08<poly.calc_center_median().z<(.27 if c['id']=='kanna' else .19),material('Socks','#EEEDE4'),offset=.005)
 shoe_src=json.loads((R/'reference/casual-shoes.json').read_text());foot_z=rig.data.bones['foot_l'].head_local.z
 for sign,side in [(1,'l'),(-1,'r')]:
  ids=[i for i,p in enumerate(shoe_src['vertices']) if p[0]*sign>0];ps=[shoe_src['vertices'][i] for i in ids];lo=[min(p[k] for p in ps) for k in range(3)];hi=[max(p[k] for p in ps) for k in range(3)];cx=rig.data.bones['foot_'+side].head_local.x
  mapping={old:j for j,old in enumerate(ids)};boot=f['shoeType'] in ['boots','workboots'];mary=f['shoeType']=='maryjane';length=.285 if not mary else .255;width=.135 if not mary else .128;shoeheight=.12 if not mary else .083
  verts=[((shoe_src['vertices'][i][0]-(lo[0]+hi[0])/2)/(hi[0]-lo[0])*width+cx,(shoe_src['vertices'][i][1]-lo[1])/(hi[1]-lo[1])*length-.16,(shoe_src['vertices'][i][2]-lo[2])/(hi[2]-lo[2])*shoeheight+.008) for i in ids]
  for mi,part in [(0,'Sole'),(1,'Upper')]:
   fs=[[mapping[i] for i in poly] for poly,mat_index in zip(shoe_src['faces'],shoe_src['material_indices']) if mat_index==mi and all(i in mapping for i in poly)]
   shoeColor='#DDDCD5' if mi==0 and f['shoeType']=='sneakers' else '#302E29' if mi==0 else f['shoeColor'];mesh('Shoe_'+side+'_'+part,verts,fs,material('Shoe '+part,shoeColor,.72),rig,'foot_'+side)
  if mary:box('MaryJane strap',(cx,-.015,.083),(.125,.026,.018),material('Shoe strap',f['shoeColor']),rig,'foot_'+side,.004)
  elif boot:
   ring_garment('Boot_'+side,rig,material('Boot leather',f['shoeColor']),[(.085,.075,.075,.04),(.29,.070,.066,.04)]) if False else None
   # Calf cuff follows lower leg, separate shoe follows foot so the ankle can flex.
   n=24;vs=[(cx+.074*math.cos(t*math.tau/n),.065+.072*math.sin(t*math.tau/n),z) for z in [.11,.29] for t in range(n)];fs=[(k,(k+1)%n,n+(k+1)%n,n+k) for k in range(n)];mesh('Boot_Shaft_'+side,vs,fs,material('Boot shaft',f['shoeColor']),rig,'calf_'+side)
  elif f['shoeType']=='sneakers':
   for y in [-.035,-.01,.015,.04]:tube('Shoelace_'+side,[(cx-.030,y,.104),(cx,y-.004,.114),(cx+.030,y,.104)],.0018,material('Laces','#DDDCD5'),rig,'foot_'+side,6)
 # Collar and original tailored details.
 if top in ['shirt','uniform','chefcoat','coat','vest','apron','overalls']:
  collar=material('Collar',f.get('underlayerColor',f['topColor']))
  for sign in [-1,1]:mesh('Collar point',[(sign*.014,-.085,neck-.016),(sign*.093,-.075,neck-.025),(sign*.074,-.135,neck-.13),(sign*.028,-.14,neck-.08)],[(0,1,2,3)],collar,rig,'spine_03')
  for z in [hip+.12,hip+.24,hip+.36]:ellipsoid('Button',(0,-.148,z),(.007,.004,.007),material('Button','#D5CBB7'),rig,'spine_02',12,8)
 if top=='hoodie':
  ellipsoid('Hood back',(0,.14,neck-.12),(.16,.08,.13),material('Hood',f['topColor']),rig,'spine_03')
  for x in [-.045,.045]:tube('Hood drawstring',[(x,-.10,neck-.05),(x,-.16,neck-.20)],.003,material('Cord','#E0D6CF'),rig,'spine_03')
  box('Kangaroo pocket',(0,-.157,hip+.19),(.22,.016,.10),material('Pocket',f['topColor']),rig,'spine_01')
 if top in ['coat','jacket']:
  if top=='coat':ring_garment('Coat tails',rig,material('Coat tails',f['topColor']),[(hip+.03,.205,.166,.035),(.74,.234,.18,.035),(.55,.248,.183,.035)],leg_weight=True,front_open=True)
  for sign in [-1,1]:mesh('Lapels',[(sign*.03,-.15,neck-.06),(sign*.16,-.12,neck-.12),(sign*.08,-.173,hip+.22)],[(0,1,2)],material('Lapels',f.get('coatTrimColor',f['topColor'])),rig,'spine_03')
  for x in [-.12,.12]:box('Coat pocket',(x,-.168,hip-.05),(.085,.015,.085),material('Coat pocket',f['topColor']),rig,'pelvis')
 if top=='vest':
  clothing(body,rig,'Waistcoat',lambda p:hip+.02<p.calc_center_median().z<neck-.04 and abs(p.calc_center_median().x)<.22,material('Waistcoat',f['topColor']),offset=.020)
 if top in ['apron','overalls']:
  cloth=patterned(material('Apron bib',f['topColor']),c);front=-.178
  verts=[(-.115,front,hip+.44),(.115,front,hip+.44),(.17,front-.025,hip+.03),(-.17,front-.025,hip+.03)]
  mesh('Bib',verts,[(0,1,2,3)],cloth,rig,{'spine_03':[(0,1),(1,1)],'pelvis':[(2,1),(3,1)]})
  if top=='apron':
   mesh('Apron skirt',[(-.17,front-.025,hip+.04),(.17,front-.025,hip+.04),(.235,front-.025,.54),(-.235,front-.025,.54)],[(0,1,2,3)],cloth,rig,{'pelvis':[(0,1),(1,1)],'thigh_l':[(2,1)],'thigh_r':[(3,1)]})
  for x in [-.10,.10]:tube('Bib strap',[(x,front,hip+.40),(x,-.06,neck-.025),(x,.12,neck-.05),(x,.15,hip+.10)],.018,cloth,rig,'spine_03',8)
  box('Apron pocket',(0,front-.04,hip+.03),(.15,.012,.09),material('Pocket',f['topColor']),rig,'pelvis')
 # Remove only skin fully covered by real garment meshes, including clothing beneath skirt.
 def visible_skin(poly):
  p=poly.calc_center_median()
  if in_top(p):return False
  if .075<p.z<hip+.035 and p.z>hem:return False
  if p.z<.105:return False
  return True
 delete_faces(body,visible_skin)
 return {'hip':hip,'neck':neck,'hem':hem,'top':top,'sleeve':sleeve}

def make_accessories(c,rig,body,head,landmarks):
 f=c['features'];acc=set(f.get('accessories',[]));hip=landmarks['hip'];neck=landmarks['neck'];top=head['max'][2];cx=0;eyez=top-.115;facefront=min(v.co.y for v in bpy.data.objects['Eyes'].data.vertices);eyez=sum(v.co.z for v in bpy.data.objects['Eyes'].data.vertices)/len(bpy.data.objects['Eyes'].data.vertices);front=facefront-.006
 gold=material('Brass','#C7A13E',.4);dark=material('Charcoal','#25262B');white=material('Warm white','#EFECE4');accent=material('Accent',f.get('trimColor',f.get('gemColor','#D9B12D')))
 # Structured occupation caps and soft baking hats.
 if any('cap_' in a for a in acc):
  capcolor='#10253D' if 'cap_police' in acc or 'cap_driver' in acc else '#216140';cap=material('Cap crown',f.get('hatColor',capcolor));ellipsoid('Cap crown',(0,.014,top+.035),(.153,.13,.052),cap,rig)
  ring_garment('Cap band',rig,dark,[(top-.012,.132,.108,.016),(top+.012,.135,.111,.016)])
  # Hat band must follow Head, not a torso/leg skin rule.
  o=bpy.context.scene.objects.get('Cap band')
  if o:
   o.vertex_groups.clear();bind(o,rig,'Head')
  ellipsoid('Cap brim',(0,-.111,top-.015),(.13,.082,.012),dark,rig,segments=24,rings=8)
  ellipsoid('Cap badge',(0,-.113,top+.035),(.022,.005,.027),gold,rig,segments=16,rings=10)
 if 'bakerhat' in acc or 'bakerhat_pink' in acc or 'chefhat' in acc:
  col=f.get('hatColor','#F1F0E9' if 'bakerhat_pink' not in acc else '#EDAEC8');hm=material('Baking cap',col)
  if 'chefhat' in acc:
   ring_garment('Tall chef hat',rig,hm,[(top-.01,.127,.11,.012),(top+.11,.133,.12,.012),(top+.20,.17,.135,.012)])
   o=bpy.context.scene.objects.get('Tall chef hat');o.vertex_groups.clear();bind(o,rig,'Head');ellipsoid('Chef crown',(0,.012,top+.20),(.177,.14,.065),hm,rig)
  else:ellipsoid('Soft baker cap',(0,.013,top+.045),(.174,.144,.07),hm,rig)
  tube('Baker band',[(.13*math.cos(t*math.tau/48),.014+.112*math.sin(t*math.tau/48),top-.006) for t in range(49)],.012,hm,rig)
 if 'nursehat' in acc:
  box('Nurse cap',(0,.012,top+.026),(.25,.12,.055),white,rig,'Head',.012);red=material('Medical red','#B44956');box('Cap cross vertical',(0,-.051,top+.032),(.012,.004,.036),red,rig,'Head');box('Cap cross horizontal',(0,-.053,top+.032),(.034,.004,.011),red,rig,'Head')
 if 'strawhat' in acc:
  straw=material('Woven straw',f.get('hatColor','#C8AA68'));ellipsoid('Straw hat brim',(0,.015,top-.005),(.245,.21,.018),straw,rig,segments=32,rings=8);ellipsoid('Straw hat crown',(0,.015,top+.052),(.135,.117,.075),straw,rig)
  for z in [top+.012,top+.025]:tube('Straw woven band',[(.137*math.cos(t*math.tau/48),.015+.118*math.sin(t*math.tau/48),z) for t in range(49)],.006,material('Hat band',f.get('hatBandColor','#8B6436')),rig)
 if 'beret' in acc:ellipsoid('Artist beret',(-.02,.025,top+.025),(.16,.135,.047),dark,rig)
 # Glasses use open frames and bridge, not opaque disks covering the eyes.
 if any('glasses' in a for a in acc):
  gm=material('Frames',f.get('glassesColor','#302C2C'),.5);rounds='round' in f.get('glassesShape','') or 'glasses_round' in acc
  for sign in [-1,1]:
   x=sign*.052;rrx=.037 if rounds else .041;rrz=.031 if rounds else .032
   if rounds:pts=[(x+rrx*math.cos(t*math.tau/32),front,eyez+rrz*math.sin(t*math.tau/32)) for t in range(33)]
   else:
    pts=[]
    for i in range(33):
     t=i*math.tau/32;ct,st=math.cos(t),math.sin(t);pts.append((x+rrx*math.copysign(abs(ct)**.5,ct),front,eyez+rrz*math.copysign(abs(st)**.5,st)))
   tube('Glasses frame',pts,.0035 if 'large' not in f.get('glassesShape','') else .005,gm,rig)
   tube('Glasses temple',[(sign*.092,front+.008,eyez+.01),(sign*.119,-.012,eyez+.01),(sign*.118,.045,eyez-.004)],.0025,gm,rig)
  tube('Glasses bridge',[(-.015,front,eyez+.006),(0,front-.003,eyez+.012),(.015,front,eyez+.006)],.003,gm,rig)
 if 'earrings' in acc or 'earrings_hoop' in acc or 'earring' in acc:
  for sign in [-1,1]:tube('Earring',[(sign*(.123+.013*math.cos(t*math.tau/24)),.003,eyez-.08+.023*math.sin(t*math.tau/24)) for t in range(25)],.003,gold,rig)
 if 'stethoscope' in acc:
  rubber=material('Stethoscope rubber','#48525A');tube('Stethoscope neck',[(-.09,-.07,neck-.035),(-.105,-.15,neck-.15),(-.075,-.185,neck-.28),(0,-.19,neck-.31),(.073,-.18,neck-.23),(.084,-.11,neck-.08)],.005,rubber,rig,'spine_03');ellipsoid('Stethoscope chestpiece',(.074,-.19,neck-.26),(.024,.008,.025),material('Steel','#AAB1AF',.3),rig,'spine_03')
 if 'tie' in acc:
  tm=material('Tie',f.get('tieColor','#623239'));mesh('Tie',[(0,-.128,neck-.09),(-.027,-.165,neck-.17),(-.022,-.18,hip+.20),(0,-.185,hip+.16),(.022,-.18,hip+.20),(.027,-.165,neck-.17)],[(0,1,2,3,4,5)],tm,rig,'spine_03')
 if 'scarf_red' in acc:
  red=material('Red neckerchief','#A72F32');tube('Neckerchief',[(-.085,-.03,neck-.055),(0,-.104,neck-.075),(.085,-.03,neck-.055)],.016,red,rig,'spine_03');mesh('Scarf tails',[(0,-.12,neck-.06),(-.045,-.16,neck-.22),(.004,-.17,neck-.18),(.05,-.15,neck-.20)],[(0,1,2),(0,2,3)],red,rig,'spine_03')
 if 'belt' in acc or c['id'].startswith(('05_','07_','09_','21_','24_','28_','31_','39_')):
  ring_garment('Belt',rig,dark,[(hip+.01,.204,.163,.035),(hip+.055,.204,.163,.035)]);box('Belt buckle',(0,-.139,hip+.032),(.05,.014,.028),material('Buckle','#A8A6A0',.4),rig,'pelvis')
 if 'badge' in acc or 'cap_police' in acc or 'cap_postal' in acc:
  box('Service badge',(-.10,-.157,neck-.24),(.034,.006,.034),gold,rig,'spine_03');box('Name plate',(.09,-.160,neck-.25),(.048,.006,.013),white,rig,'spine_03')
 if 'reflective_stripes' in acc:
  hi=material('Reflective yellow','#EEC820',.45)
  for z in [hip+.10,hip+.145]:ring_garment('Torso reflective band',rig,hi,[(z,.214,.165,.035),(z+.025,.214,.165,.035)])
  for sign,side in [(1,'l'),(-1,'r')]:
   n=24;cx=rig.data.bones['calf_'+side].head_local.x
   for z in [.35,.39]:
    vs=[(cx+.082*math.cos(t*math.tau/n),.058+.078*math.sin(t*math.tau/n),zz) for zz in [z,z+.025] for t in range(n)];mesh('Leg reflective band',vs,[(k,(k+1)%n,n+(k+1)%n,n+k) for k in range(n)],hi,rig,'calf_'+side)
   # On the T-pose sleeves the stripe is a ring around the X axis.
   x=sign*.51;vs=[(xx,.073+.074*math.cos(t*math.tau/n),1.46+.074*math.sin(t*math.tau/n)) for xx in [x-.022,x+.022] for t in range(n)];mesh('Arm reflective band',vs,[(k,(k+1)%n,n+(k+1)%n,n+k) for k in range(n)],hi,rig,'lowerarm_'+side)
 if 'pouch' in acc or 'backpack' in acc:
  bag=material('Bag',f.get('bagColor','#C5A13D'));isback='backpack' in acc
  if isback:
   box('Backpack',(0,.204,hip+.24),(.24,.13,.31),bag,rig,'spine_02',.025)
   for x in [-.10,.10]:tube('Backpack shoulder strap',[(x,.20,hip+.35),(x,.05,neck-.04),(x,-.135,neck-.16),(x,-.155,hip+.12)],.014,bag,rig,'spine_03')
  else:
   box('Satchel',(.25,-.03,hip+.04),(.18,.12,.19),bag,rig,'pelvis',.015);tube('Cross body strap',[(-.16,.10,neck-.10),(-.16,-.08,neck-.08),(.24,-.19,hip+.13),(.26,-.01,hip+.10)],.016,bag,rig,'spine_03')
 if 'toolbelt' in acc or c['id'].startswith(('05_','37_')):
  leather=material('Toolbelt','#9E783A')
  for x in [-.20,.20]:
   box('Tool pouch',(x,-.04,hip-.04),(.11,.10,.15),leather,rig,'pelvis',.008);box('Tool handle',(x,-.08,hip+.085),(.022,.025,.17),gold,rig,'pelvis',.003)
 if 'guitar' in acc:
  wood=material('Guitar walnut','#704832');ellipsoid('Guitar body',(.15,.22,hip+.15),(.16,.055,.20),wood,rig,'spine_02');o=box('Guitar neck',(.29,.24,hip+.48),(.055,.04,.55),wood,rig,'spine_03');
 if 'crown' in acc:
  silver=material('Crown silver',f.get('crownColor','#D9DCE6'),.3);gem=material('Azure jewel',f.get('gemColor','#287DE1'),.3)
  tube('Crown circlet',[(.135*math.cos(t*math.tau/48),.012+.115*math.sin(t*math.tau/48),top+.006) for t in range(49)],.008,silver,rig)
  for k,x in enumerate([-.105,-.055,0,.055,.105]):
   z=top+.055+(.035 if x==0 else 0);y=-.09+abs(x)*.2;tube('Crown point',[(x-.025,y,top+.004),(x,y,z),(x+.025,y,top+.004)],.004,silver,rig);ellipsoid('Crown jewel',(x,y-.005,z-.015),(.012,.008,.018),gem,rig)
 if 'pointed_ears' in acc:
  sk=material('Elven ear',f['skinColor'])
  for sign in [-1,1]:mesh('Elven ear',[(sign*.10,.016,eyez-.03),(sign*.206,.018,eyez+.025),(sign*.133,.018,eyez-.082),(sign*.126,-.008,eyez-.035)],[(0,1,3),(1,2,3),(2,0,3),(0,2,1)],sk,rig,'Head')
 if 'neck_jewel' in acc:ellipsoid('Neck jewel',(0,-.11,neck-.04),(.019,.009,.024),accent,rig,'spine_03')
 if 'horns' in acc:
  horn=material('Pearl horn',f.get('hornColor','#EDF4FA'))
  for sign in [-1,1]:tube('Horn',[(sign*.105,.015,top-.03),(sign*.16,.018,top+.025),(sign*.17,.014,top+.085),(sign*.145,-.005,top+.135)], [.033,.030,.020,.001],horn,rig,'Head',12)
 if 'hair_beads' in acc:
  hm=material('Hair beads',f.get('hairbeadsColor','#353B78'))
  for sign in [-1,1]:
   for i in range(4):ellipsoid('Hair bead',(sign*.14,.03,top-.13-i*.055),(.034,.032,.033),hm,rig)
 if 'bow' in acc or 'ribbon' in acc:
  bm=material('Ribbon',f.get('hairbeadsColor','#353B78'))
  for sign in [-1,1]:ellipsoid('Ribbon bow',(sign*.036,-.016,top+.004),(.040,.018,.026),bm,rig)
 if 'tail' in acc:
  tail=material('Lilac tail',f.get('tailColor','#AC87D5'));pts=[(0,.13,hip-.02),(.12,.24,hip-.18),(.26,.21,hip-.18),(.34,.10,hip-.09),(.35,.07,hip+.035)];tube('Companion tail',pts,[.025,.022,.018,.015,.012],tail,rig,'pelvis',12);ellipsoid('Tail tip',pts[-1],(.045,.035,.05),tail,rig,'pelvis')
 # Original personality cues: moustaches/beards, grey brows, shirt graphic and floral emblem.
 age=c['design']['ageStyle'];hairmat=material('Facial hair',f['hairColor'])
 if c['id'].startswith(('23_','24_','29_')):
  for sign in [-1,1]:ellipsoid('Moustache',(sign*.025,front-.008,eyez-.088),(.032,.015,.013),hairmat,rig)
 if c['id'].startswith('28_'):ellipsoid('Short beard',(0,front+.018,eyez-.14),(.066,.026,.042),hairmat,rig)
 if 'graphic_tee' in acc:
  red=material('Graphic vermilion','#CB472F');yellow=material('Graphic gold','#DAAA37');box('Shirt graphic stem',(0,-.16,neck-.27),(.024,.008,.11),yellow,rig);mesh('Shirt graphic red',[(0,-.17,neck-.18),(-.045,-.17,neck-.24),(.045,-.17,neck-.24)],[(0,1,2)],red,rig)
 if c['id'].startswith('30_'):
  for k in range(5):t=k*math.tau/5;ellipsoid('Apron flower',(.022*math.cos(t),-.22,hip+.25+.022*math.sin(t)),(.014,.006,.018),material('Flower pink','#E798A8'),rig,'spine_02',12,8)
 if c['id'].startswith('36_'):
  cup=material('Coffee emblem','#E5E8DA');box('Apron cup',(0,-.221,hip+.24),(.060,.006,.050),cup,rig,'spine_02');tube('Emblem handle',[(.034+.014*math.cos(t*math.tau/20),-.223,hip+.24+.016*math.sin(t*math.tau/20)) for t in range(21)],.003,cup,rig,'spine_02')
 for o in bpy.context.scene.objects:
  if o.type=='MESH' and any(k in o.name for k in ['hat','Hat','Cap','cap','Crown','crown','beret']):o['removableForRest']=True

def deform_person(c,rig,body,seed):
 d=c['design'];regs=seed['bodyRegionCoordinates'];neck=regs['head']['neckBaseZ'];base_top=seed['height'];hip=regs['torso']['pelvisZ'];knee=rig.data.bones['calf_l'].head_local.z;ankle=rig.data.bones['foot_l'].head_local.z
 height=d['height'];head_height=(base_top-neck)*d['headScale'];dest_neck=height-head_height;dest_hip=height*d['legRatio']+.045;dest_ankle=.085*height/1.75;dest_knee=dest_ankle+(dest_hip-dest_ankle)*.52
 z_from=[0,ankle,knee,hip,neck,base_top];z_to=[0,dest_ankle,dest_knee,dest_hip,dest_neck,height]
 shoulder_z=rig.data.bones['upperarm_l'].head_local.z;shoulder_x=rig.data.bones['upperarm_l'].head_local.x
 def zmap(z):
  for i in range(len(z_from)-1):
   if z<=z_from[i+1]:return z_to[i]+(z-z_from[i])/(z_from[i+1]-z_from[i])*(z_to[i+1]-z_to[i])
  return height+(z-base_top)*d['headScale']
 def shape(p):
  p=p.copy();z=p.z;ax=abs(p.x);sign=1 if p.x>=0 else -1;head_t=max(0,min(1,(z-neck+.02)/.09));head_t=head_t*head_t*(3-2*head_t)
  # Individual transverse dimensions are absolute design widths, independent of height.
  if z<hip:
   xscale=d['hip']/(.38 if seed['sex']=='male' else .39)
  else:
   t=(z-hip)/max(.1,shoulder_z-hip);waist_t=math.exp(-((t-.26)/.26)**2);xscale=(d['hip']/(.38 if seed['sex']=='male' else .39))*(1-t)+d['shoulder']/.46*t;xscale=xscale*(1-waist_t*.25)+(d['waist']/.34)*waist_t*.25
  xscale=max(.55,min(1.45,xscale));arm_w=max(0,min(1,(ax-shoulder_x*.70)/(.12)));arm_w=arm_w*arm_w*(3-2*arm_w)*math.exp(-((z-shoulder_z)/.22)**4)
  anchor=d['shoulder']*.43;arm_scale=height/base_top*(1+(d['shoulder']-.43)*.6)
  body_x=p.x*(xscale*(1-head_t)+d['headScale']*d['faceWidth']*head_t);arm_x=sign*(anchor+(ax-shoulder_x)*arm_scale);p.x=body_x*(1-arm_w)+arm_x*arm_w
  thickness=d['waist']/.32;thickness=max(.72,min(1.43,thickness));cy=.035
  p.y=cy+(p.y-cy)*(thickness*(1-head_t)+d['headScale']*.98*head_t)
  arm_y=.065+(p.y-.065)*max(.72,min(1.23,(d['shoulder']/.455+d['waist']/.32)/2));p.y=p.y*(1-arm_w)+arm_y*arm_w
  if c['kind']=='codexmini' and height<1.5 and z>hip and z<neck-.03:p.y=.035+(p.y-.035)*.72
  if d['build'] in ['rounded','round-stocky','compact-stocky','stocky','sturdy'] and p.y<.03 and hip<z<neck-.15:p.y-=.025*math.exp(-((z-(hip+.14))/.18)**2)
  if seed['sex']=='female' and hip+.15<z<neck-.04 and abs(p.x)<.24:
   bell=math.exp(-((z-(neck-.20))/.13)**2);p.y=.035+(p.y-.035)*(1-.16*bell)
  if c['id'] in ['kanna','hai-qin-yan'] and z>neck:
   mid=base_top-.145;low=max(0,min(1,(mid-z)/.13));p.x*=1-.13*low;p.y=.02+(p.y-.02)*(1-.20*low);z+=.020*low
  p.z=zmap(z)
  return p
 meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
 for o in meshes:
  if o.data.shape_keys:
   for key in o.data.shape_keys.key_blocks:
    for v in key.data:v.co=shape(v.co)
   for v,p0 in zip(o.data.vertices,o.data.shape_keys.key_blocks[0].data):v.co=p0.co
  else:
   for v in o.data.vertices:v.co=shape(v.co)
  if hasattr(o.data,'normals_split_custom_set'):o.data.normals_split_custom_set([(0,0,0)]*len(o.data.loops))
 bpy.context.view_layer.objects.active=rig;bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
 for b in rig.data.edit_bones:b.head=shape(b.head);b.tail=shape(b.tail)
 bpy.ops.object.mode_set(mode='OBJECT');bpy.context.view_layer.update()
 return {'height':height,'hipScale':dest_hip/.95861,'legScale':(dest_hip-dest_ankle)/(hip-ankle),'verticalMap':list(zip(z_from,z_to))}

def make_face(c,body,rig,head):
 f=c['features'];body.name='Skin';skin=material('Skin',f['skinColor'],.82);body.data.materials.clear();body.data.materials.append(skin)
 for p in body.data.polygons:p.material_index=0;p.use_smooth=True
 eyes=bpy.data.objects.get('Eyes');brows=bpy.data.objects.get('Eyebrows')
 # Actual mature source eyes keep shape/UV; their iris material has a tint, not opaque eyeball disks.
 if brows:
  brows.data.materials.clear();brows.data.materials.append(material('Brows',f['hairColor']))
  center=sum((v.co.z for v in brows.data.vertices))/len(brows.data.vertices)
  for v in brows.data.vertices:v.co.z=center+(v.co.z-center)*.72+.003
 if eyes:
  # Source eye texture includes white and iris; a small packed texture recolours iris only.
  img_path=R/'reference/eyes'/(c['id']+'.png')
  if img_path.exists():
   em=material('Eyes', '#FFFFFF',.3);tex=em.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(img_path),check_existing=True);tex.image.pack();node=next(n for n in em.node_tree.nodes if n.type=='BSDF_PRINCIPLED');em.node_tree.links.new(tex.outputs['Color'],node.inputs['Base Color']);eyes.data.materials.clear();eyes.data.materials.append(em)
  if c['kind']=='codexmini' and c['design']['height']<1.5:
   for sign in [-1,1]:
    vs=[v for v in eyes.data.vertices if v.co.x*sign>0];center=sum((v.co for v in vs),Vector())/len(vs)
    for v in vs:v.co=center+(v.co-center)*1.13
  lids=eyes.copy();lids.data=eyes.data.copy();lids.name='Eyelids';bpy.context.collection.objects.link(lids);lids.data.materials.clear();lids.data.materials.append(skin)
  for p in lids.data.polygons:p.material_index=0
  coords=[v.co.copy() for v in lids.data.vertices];closed={}
  for sign in [-1,1]:
   ids=[i for i,p in enumerate(coords) if p.x*sign>0];center=sum((coords[i] for i in ids),Vector())/len(ids);miny=min(coords[i].y for i in ids);maxz=max(coords[i].z for i in ids)
   for i in ids:
    p=coords[i].copy();p.y=miny-.0012+(p.y-center.y)*.015;p.z=center.z+(p.z-center.z)*1.04;closed[i]=p;lids.data.vertices[i].co=Vector((p.x,miny-.001,maxz+.001+(p.z-center.z)*.01))
  lids.shape_key_add(name='Basis');key=lids.shape_key_add(name='Blink')
  for i,p in closed.items():key.data[i].co=p
 body.shape_key_add(name='Basis');smile=body.shape_key_add(name='Smile');talk=body.shape_key_add(name='Talk');mouth_z=head['max'][2]-.177
 for i,v in enumerate(body.data.vertices):
  p=v.co;x=abs(p.x)
  if p.y<-.035 and abs(p.z-mouth_z)<.06 and x<.075:
   w=math.exp(-((p.z-mouth_z)/.018)**2);smile.data[i].co.z+=.009*w*min(1,x/.035);talk.data[i].co.z-=.011*math.exp(-((p.z-mouth_z+.012)/.017)**2-(x/.042)**2)

def support_data(rig,objects):
 import numpy as np
 bones=list(rig.pose.bones);lookup={b.name:i for i,b in enumerate(bones)};rest_inv=[b.bone.matrix_local.inverted() for b in bones];points=[];weights=[];indices=[]
 for o in objects:
  if o.get('removableForRest'):continue
  verts=o.data.vertices
  if not verts:continue
  chosen=set(range(len(verts)))
  for k in range(3):chosen.add(min(range(len(verts)),key=lambda i:verts[i].co[k]));chosen.add(max(range(len(verts)),key=lambda i:verts[i].co[k]))
  if o.name.startswith('Shoe_'):chosen=set(range(len(verts)))
  for i in chosen:
   v=verts[i];groups=[(lookup[o.vertex_groups[g.group].name],g.weight) for g in v.groups if o.vertex_groups[g.group].name in lookup and g.weight>1e-5];groups=sorted(groups,key=lambda g:-g[1])[:4]
   if not groups:continue
   total=sum(w for _,w in groups);groups=[(n,w/total) for n,w in groups];ids=[n for n,w in groups];ws=[w for n,w in groups];ids+=[ids[0]]*(4-len(ids));ws+=[0]*(4-len(ws));points.append([*v.co,1]);indices.append(ids);weights.append(ws)
 return bones,np.asarray(points,dtype=np.float32),np.asarray(indices,dtype=np.int32),np.asarray(weights,dtype=np.float32),rest_inv

def minimum_z(data):
 import numpy as np
 bones,points,indices,weights,rest_inv=data;mats=np.asarray([list(map(list,b.matrix@inv)) for b,inv in zip(bones,rest_inv)],dtype=np.float32);z=np.einsum('ni,nki->nk',points,mats[indices,:, :][:,:,2,:]);return float((z*weights).sum(axis=1).min())

def all_curves(action):
 for layer in action.layers:
  for strip in layer.strips:
   if hasattr(strip,'channelbags'):
    for bag in strip.channelbags:
     for fc in bag.fcurves:yield fc

def bake_actions(c,rig,dimensions):
 import numpy as np
 with bpy.data.libraries.load(str(R/'motion/shared-motion.blend'),link=False) as (data,target):target.actions=[a['name'] for a in MOTION['actions']]
 sources={a.name:a for a in target.actions if a}
 for name,action in sources.items():action.name='_SOURCE_'+name
 rig.animation_data_create();scene=bpy.context.scene;scene.render.fps=24
 objects=[o for o in scene.objects if o.type=='MESH'];support=support_data(rig,objects);names=[b.name for b in rig.pose.bones];result=[];summaries=[]
 for meta in MOTION['actions']:
  name=meta['name'];src=sources[name];start,end=src.frame_range;count=max(2,round(meta['duration']*24));times=np.linspace(0,count,count+1,dtype=np.float32);records={bone:{'rotation_quaternion':[],'location':[]} for bone in names};lastq={};minmax=[]
  for j in range(count+1):
   rig.animation_data.action=src
   if len(src.slots):rig.animation_data.action_slot=src.slots[0]
   sample=start+(end-start)*j/count;scene.frame_set(int(sample),subframe=sample-int(sample));bpy.context.view_layer.update();pose={b.name:(b.rotation_quaternion.copy().normalized(),b.location.copy()) for b in rig.pose.bones};rig.animation_data.action=None
   for b in rig.pose.bones:
    q,loc=pose[b.name]
    if b.name in ['pelvis','root']:loc*=dimensions['hipScale']
    b.rotation_mode='QUATERNION';b.rotation_quaternion=q;b.location=loc;b.scale=(1,1,1)
   bpy.context.view_layer.update()
   floor=minimum_z(support)
   if name not in ['JumpStart','JumpLoop','JumpLand','Swim']:
    rig.pose.bones['root'].location.z-=floor;bpy.context.view_layer.update()
   minmax.append(floor)
   for b in rig.pose.bones:
    q=b.rotation_quaternion.copy().normalized()
    if b.name in lastq and q.dot(lastq[b.name])<0:q=-q
    lastq[b.name]=q.copy();records[b.name]['rotation_quaternion'].append(tuple(q));records[b.name]['location'].append(tuple(b.location))
  action=bpy.data.actions.new(name);action.use_fake_user=True;rig.animation_data.action=action
  for b in rig.pose.bones:
   for prop in ['rotation_quaternion','location']:
    values=records[b.name][prop];setattr(b,prop,values[0]);b.keyframe_insert(prop,frame=0,group=b.name)
  for fc in all_curves(action):
   bone=fc.data_path.split('"')[1];prop=fc.data_path.rsplit('.',1)[-1];values=np.asarray(records[bone][prop],dtype=np.float32)[:,fc.array_index]
   flat=bool(float(values.max()-values.min())<1e-7);xx=times[:1] if flat else times;yy=values[:1] if flat else values
   fc.keyframe_points.add(len(xx)-1);fc.keyframe_points.foreach_set('co',np.column_stack((xx,yy)).flatten())
   for kp in fc.keyframe_points:kp.interpolation='LINEAR'
   fc.update()
  result.append(action);summaries.append({'name':name,'samples':count+1,'fps':24,'rawGroundMinimum':min(minmax),'rawGroundMaximum':max(minmax)})
 for a in sources.values():bpy.data.actions.remove(a)
 rig.animation_data.action=next(a for a in result if a.name=='Idle');scene.frame_set(0);bpy.context.view_layer.update()
 return result,summaries

def normalize_glb_quaternions(path):
 import struct,numpy as np
 raw=bytearray(path.read_bytes());size,kind=struct.unpack_from('<II',raw,12);g=json.loads(raw[20:20+size]);binary_start=20+size+8;changed=0
 for a in g.get('animations',[]):
  for ch in a['channels']:
   if ch['target']['path']!='rotation':continue
   acc=g['accessors'][a['samplers'][ch['sampler']]['output']];bv=g['bufferViews'][acc['bufferView']];offset=binary_start+bv.get('byteOffset',0)+acc.get('byteOffset',0);stride=bv.get('byteStride',16)
   arr=np.ndarray((acc['count'],4),dtype='<f4',buffer=raw,offset=offset,strides=(stride,4))
   for i in range(1,len(arr)):
    if float(np.dot(arr[i-1],arr[i]))<0:arr[i]*=-1;changed+=1
 path.write_bytes(raw);print('GLB_QUATERNION_HEMISPHERES',changed,flush=True)

def build(c):
 started=time.time();sex='male' if c['sex'] in ['male','男'] else 'female';seed=next(s for s in SEEDS['seeds'] if s['sex']==sex)
 bpy.ops.wm.open_mainfile(filepath=str(R/'foundation'/seed['blend']));scene=bpy.context.scene;rig=bpy.data.objects[seed['rigName']];body=bpy.data.objects[seed['bodyObject']]
 rig.animation_data_create();rig.animation_data.action=None
 for p in rig.pose.bones:p.rotation_mode='QUATERNION';p.matrix_basis.identity()
 bpy.context.view_layer.update()
 headpoints=[v.co.copy() for v in body.data.vertices if v.co.z>=rig.data.bones['Head'].head_local.z-.035];head={'min':[min(p[k] for p in headpoints) for k in range(3)],'max':[max(p[k] for p in headpoints) for k in range(3)]}
 wardrobe=create_wardrobe(c,body,rig,seed);make_face(c,body,rig,head)
 try:
  from hair_builder import create_hair
  create_hair(rig,c['features'],head,material,lambda o,bone:bind(o,rig,bone))
 except ImportError:
  ellipsoid('Hair temporary',(0,.035,head['max'][2]-.08),(.13,.11,.12),material('Hair',c['features']['hairColor']),rig)
 make_accessories(c,rig,body,head,wardrobe)
 dimensions=deform_person(c,rig,body,seed);rig.name='Resident_Rig';rig['identity']=c['id'];rig['nameChinese']=c['name'];rig['newDesignHeight']=c['design']['height']
 for o in scene.objects:
  if o.type=='MESH':o['residentId']=c['id'];o['part']=o.name
 actions,ground=bake_actions(c,rig,dimensions)
 # Every displayed vertex is genuinely attached to the skeleton.
 for o in scene.objects:
  if o.type=='MESH':
   assert o.vertex_groups,o.name+' has no skin weights'
   for v in o.data.vertices:
    total=sum(g.weight for g in v.groups);assert total>.99,o.name+' has unweighted vertex'
 bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
 for o in scene.objects:
  if o.type=='MESH':o.select_set(True)
 bpy.context.view_layer.objects.active=rig;bpy.ops.file.pack_all()
 out=A/c['id'];out.mkdir(exist_ok=True)
 bpy.context.preferences.filepaths.save_version=0
 bpy.ops.wm.save_as_mainfile(filepath=str(out/'character.blend'),compress=True)
 bpy.ops.export_scene.gltf(filepath=str(out/'character.glb'),export_format='GLB',use_selection=True,export_extras=True,export_animations=True,export_animation_mode='ACTIONS',export_nla_strips=False,export_frame_range=False,export_force_sampling=False,export_morph=True,export_morph_animation=False,export_optimize_animation_size=True)
 normalize_glb_quaternions(out/'character.glb')
 bpy.ops.export_scene.gltf(filepath=str(out/'runtime.glb'),export_format='GLB',use_selection=True,export_extras=True,export_animations=False,export_morph=True)
 result={**c,'base':seed['base'],'glb':f'assets/{c["id"]}/character.glb','runtimeGlb':f'assets/{c["id"]}/runtime.glb','blend':f'assets/{c["id"]}/character.blend','bones':len(rig.data.bones),'actions':[a.name for a in actions],'dimensions':dimensions,'groundSamples':ground,'meshes':sum(o.type=='MESH' for o in scene.objects),'elapsedSeconds':round(time.time()-started,2)}
 (out/'manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print('RESIDENT_COMPLETE',c['id'],c['name'],result['elapsedSeconds'],flush=True)
 return result

if __name__=='__main__':
 make_patterns()
 for c in IDENTITIES:
  if FILTER and c['id'] not in FILTER:continue
  build(c)
 records=[json.loads(p.read_text()) for p in sorted(A.glob('*/manifest.json'))]
 records.sort(key=lambda p:next(i for i,c in enumerate(IDENTITIES) if c['id']==p['id']))
 tmp=A/'manifest.tmp';tmp.write_text(json.dumps({'version':'2.0.0','date':'2026-10-18','characters':records,'actions':MOTION['actions']},ensure_ascii=False,indent=2));os.replace(tmp,A/'manifest.json')
