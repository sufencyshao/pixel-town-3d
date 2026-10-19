import bpy,math,json,hashlib,os,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent.parent
M={};C={};CACHE={};OX=0;FLOOR=1;Z=0
PALETTE={'cream':'e9e0ce','white':'f5f0e4','sage':'7b917a','darkgreen':'50695b','wood':'b58b60','lightwood':'d5b68c','roof':'b47b61','stone':'ccc7b7','grass':'a5b38d','leaf':'728e66','leafLight':'99ac7a','earth':'897c61','blue':'75b5bd','water':'59aeb9','fabric':'c5cbb5','pink':'c9907f','dark':'465147','metal':'9aa7a0','gold':'bda16b','book':'8598a0','tile':'c5d8d2','flowerPink':'ce8090','flowerYellow':'ebc65c','tomato':'bf6251','lavender':'9a8eb9'}
def col(n):
 if n not in C:
  c=bpy.data.collections.new(n);bpy.context.scene.collection.children.link(c);C[n]=c
 return C[n]
def group(part):return 'L%02d_%s'%(FLOOR,part)
def init():
 global M,C,CACHE,OX,FLOOR,Z,FONT
 bpy.ops.wm.read_factory_settings(use_empty=True);M={};C={};CACHE={};OX=0;FLOOR=1;Z=0
 for n,h in PALETTE.items():
  rgb=[int(h[i:i+2],16)/255 for i in (0,2,4)];rgb=[((v+.055)/1.055)**2.4 if v>.04045 else v/12.92 for v in rgb]
  m=bpy.data.materials.new(n);m.diffuse_color=(*rgb,1);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*rgb,1);b.inputs['Roughness'].default_value=.72
  if n in ['gold','metal']:b.inputs['Metallic'].default_value=.55
  if n=='water':b.inputs['Roughness'].default_value=.2
  M[n]=m
 m=bpy.data.materials.new('glass');m.diffuse_color=(.66,.80,.77,.18);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=m.diffuse_color;b.inputs['Alpha'].default_value=.18;b.inputs['Roughness'].default_value=.15;m.surface_render_method='DITHERED';M['glass']=m
 FONT=bpy.data.fonts.load('/System/Library/Fonts/STHeiti Medium.ttc')
def box(n,x,y,z,w,d,h,mat='cream',c=None,bev=0):
 c=c or group('Interior');key=(w,d,h,mat,bev)
 if key not in CACHE:
  vs=[(a*w/2,b*d/2,k*h/2) for a,b,k in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]
  fs=[(0,2,6,4),(1,5,7,3),(0,4,5,1),(2,3,7,6),(0,1,3,2),(4,6,7,5)]
  me=bpy.data.meshes.new(n);me.from_pydata(vs,[],fs);me.materials.append(M[mat]);me.update();CACHE[key]=me
 o=bpy.data.objects.new(n,CACHE[key]);col(c).objects.link(o);o.location=(x+OX,y,z+Z)
 if bev:
  mod=o.modifiers.new('Rounded edge','BEVEL');mod.width=bev;mod.segments=2
 return o
def cyl(n,x,y,z,r,h,mat='wood',c=None,vertices=16):
 c=c or group('Interior');key=('cyl',r,h,mat,vertices)
 if key not in CACHE:
  vs=[(r*math.cos(i*math.tau/vertices),r*math.sin(i*math.tau/vertices),zz) for zz in [-h/2,h/2] for i in range(vertices)]
  fs=[tuple(range(vertices-1,-1,-1)),tuple(range(vertices,vertices*2))]+[(i,(i+1)%vertices,(i+1)%vertices+vertices,i+vertices) for i in range(vertices)]
  me=bpy.data.meshes.new(n);me.from_pydata(vs,[],fs);me.materials.append(M[mat]);me.update();CACHE[key]=me
 o=bpy.data.objects.new(n,CACHE[key]);col(c).objects.link(o);o.location=(x+OX,y,z+Z);return o
def leaf(n,x,y,z,s,mat='leaf',c='Landscape'):
 key=('leaf',mat)
 if key not in CACHE:
  bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1);o=bpy.context.object;me=o.data;me.materials.append(M[mat]);CACHE[key]=me;bpy.data.objects.remove(o,do_unlink=True)
 o=bpy.data.objects.new(n,CACHE[key]);col(c).objects.link(o);o.location=(x+OX,y,z+Z);o.scale=s;return o
def text(n,t,x,y,z,size=.2,mat='white',c=None):
 c=c or group('Interior');cu=bpy.data.curves.new(n,'FONT');cu.body=t;cu.font=FONT;cu.size=size;cu.align_x='CENTER';cu.align_y='CENTER';cu.extrude=.002;cu.resolution_u=3
 o=bpy.data.objects.new(n,cu);col(c).objects.link(o);o.location=(x+OX,y,z+Z);o.rotation_euler=(math.pi/2,0,0);cu.materials.append(M[mat]);bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o.select_set(False);return o
def sign(t,x,y,z,w=1.3,c=None):
 box('Name plaque',x,y,z,w,.06,.36,'darkgreen',c);text('Label '+t,t,x,y-.038,z,.18,c=c)
def beam(n,a,b,w,mat,c):
 av,bv=Vector(a),Vector(b);o=box(n,*((av+bv)/2),w,w,(bv-av).length,mat,c);o.rotation_euler=(bv-av).to_track_quat('Z','Y').to_euler();return o
def plant(x,y,s=.8,c='Landscape'):
 cyl('Terracotta planter',x,y,.22*s,.28*s,.44*s,'roof',c)
 for dx,dy,dz in [(0,0,.7),(.2,0,.59),(-.18,.08,.62),(0,-.2,.63)]:leaf('Plant foliage',x+dx*s,y+dy*s,dz*s,(.33*s,.32*s,.27*s),'leaf' if dx else 'leafLight',c)
def tree(x,y,s=1):
 cyl('Tree trunk',x,y,1.1*s,.12*s,2.2*s,'wood','Landscape')
 for dx,dy,dz in [(0,0,2.3),(.5,0,2.0),(-.5,.25,2.15),(0,-.5,2.0)]:leaf('Tree crown',x+dx*s,y+dy*s,dz*s,(.85*s,.8*s,.85*s),'leaf' if dx else 'leafLight')
def wall_y(n,y,start,end,openings,c,th=.18,height=3.0):
 # Every opening is real geometry: (centre,width,sill,top).
 intervals=sorted(openings,key=lambda a:a[0]);cursor=start
 for center,width,sill,top in intervals:
  lo,hi=center-width/2,center+width/2
  if lo>cursor:box(n,cursor+(lo-cursor)/2,y,.18+height/2,lo-cursor,th,height,'cream',c)
  if sill>0:box(n+' sill',center,y,.18+sill/2,width,th,sill,'cream',c)
  if top<height:box(n+' lintel',center,y,.18+(top+height)/2,width,th,height-top,'cream',c)
  if sill>0:
   box('Window glass',center,y,.18+(sill+top)/2,width-.08,.025,top-sill-.06,'glass',c)
   for xx in [lo+.035,hi-.035]:box('Window jamb',xx,y-.015,.18+(sill+top)/2,.07,th+.04,top-sill,'wood',c)
   for zz in [sill+.025,top-.025]:box('Window rail',center,y-.015,.18+zz,width,.22,.05,'wood',c)
   box('Window mullion',center,y-.025,.18+(sill+top)/2,.045,.07,top-sill,'wood',c)
  else:
   for xx in [lo+.03,hi-.03]:box('Door jamb',xx,y,.18+top/2,.06,th+.04,top,'wood',c)
  cursor=hi
 if end>cursor:box(n,cursor+(end-cursor)/2,y,.18+height/2,end-cursor,th,height,'cream',c)
def wall_x(n,x,start,end,openings,c,th=.18,height=3.0):
 before=set(col(c).objects);wall_y(n,0,start,end,openings,c,th,height)
 for o in set(col(c).objects)-before:
  xx=o.location.x-OX;yy=o.location.y;o.location.x=OX+x-yy;o.location.y=xx;o.rotation_euler.z+=math.pi/2

def chair(x,y,rot=0,mat='sage'):
 before=set(col(group('Interior')).objects)
 box('Chair cushion',x,y,.60,.50,.50,.12,mat,bev=.04)
 for dx in [-.19,.19]:
  for dy in [-.19,.19]:box('Chair leg',x+dx,y+dy,.34,.045,.045,.46,'wood')
 box('Chair back',x,y+.22,.90,.49,.07,.48,'wood',bev=.025)
 for o in set(col(group('Interior')).objects)-before:
  dx=o.location.x-OX-x;dy=o.location.y-y;o.location.x=OX+x+math.cos(rot)*dx-math.sin(rot)*dy;o.location.y=y+math.sin(rot)*dx+math.cos(rot)*dy;o.rotation_euler.z=rot

def bed(x,y,w=1.6):
 box('Bed frame',x,y,.39,w+.12,2.15,.36,'wood',bev=.05);box('Mattress',x,y,.68,w,2.02,.26,'white',bev=.09)
 box('Bed blanket',x,y-.26,.827,w-.06,1.38,.045,'sage',bev=.02);box('Headboard',x,y+1.04,.82,w+.15,.12,1.18,'wood',bev=.04)
 for dx in [-w*.25,w*.25]:box('Pillow',x+dx,y+.65,.86,w*.42,.45,.16,'white',bev=.07)
 box('Bedside table',x+w/2+.45,y+.60,.57,.58,.57,.77,'lightwood',bev=.025);cyl('Bedside lamp',x+w/2+.45,y+.6,1.08,.13,.25,'white')
def sofa(x,y,w=2.5):
 box('Sofa base',x,y,.4,w,.96,.50,'sage',bev=.10);box('Sofa back',x,y+.38,.89,w,.23,.67,'sage',bev=.08)
 for dx in [-w/2+.10,w/2-.10]:box('Sofa arm',x+dx,y,.69,.22,.97,.58,'sage',bev=.08)
 for dx in [-w/4,w/4]:box('Sofa cushion',x+dx,y-.06,.71,w/2-.16,.67,.18,'fabric',bev=.065)
 box('Coffee table',x,y-1.30,.59,1.28,.69,.12,'lightwood',bev=.06)
 for dx in [-.42,.42]:box('Coffee table support',x+dx,y-1.3,.32,.08,.48,.42,'wood')
 box('Living rug',x,y-.85,.208,w+1,2.35,.018,'fabric')
def table(x,y):
 box('Dining tabletop',x,y,.97,1.55,.88,.12,'lightwood',bev=.04)
 for dx in [-.60,.60]:
  for dy in [-.30,.30]:box('Dining leg',x+dx,y+dy,.53,.065,.065,.80,'wood')
 for dx in [-.44,.44]:chair(x+dx,y+.84);chair(x+dx,y-.84,math.pi)
 plant(x,y,.25,group('Interior'))
def kitchen(x,y,w=3):
 box('Kitchen cabinets',x,y,.67,w,.62,.96,'sage',bev=.025);box('Kitchen worktop',x,y,1.18,w+.04,.67,.07,'white')
 for dx in [-w/3,0,w/3]:box('Cabinet door',x+dx,y-.326,.67,w/3-.025,.02,.80,'sage');box('Cabinet handle',x+dx,y-.349,.93,.20,.025,.025,'gold')
 box('Sink basin',x-.55,y,1.225,.60,.40,.015,'metal');cyl('Kitchen tap',x-.6,y+.17,1.36,.022,.27,'metal')
 box('Cooktop',x+.65,y,1.225,.62,.46,.018,'dark')
 for dx in [.45,.85]:
  for dy in [-.11,.11]:cyl('Hob ring',x+dx,y+dy,1.24,.073,.008,'metal')
 box('Upper cabinets',x,y,2.30,w,.34,.73,'white',bev=.02)
 box('Fridge',x+w/2+.44,y-.03,1.17,.70,.68,1.98,'white',bev=.035);box('Fridge pull',x+w/2+.67,y-.39,1.55,.03,.04,.40,'metal')
def bath(x,y):
 # compact fixtures within a 2.5 x 2.1 m bathroom footprint
 box('Bath tile',x,y,.205,2.3,1.95,.02,'tile')
 cyl('Toilet base',x-.67,y+.1,.43,.25,.42,'white');box('Toilet cistern',x-.67,y+.54,.84,.5,.20,.65,'white',bev=.05)
 box('Basin unit',x+.6,y+.53,.70,.72,.5,1.02,'wood');box('Basin',x+.6,y+.53,1.23,.76,.53,.09,'white',bev=.025)
 box('Bath mirror',x+.6,y+.83,1.91,.70,.035,.90,'metal')
 box('Shower tray',x+.53,y-.42,.26,.86,.77,.13,'white',bev=.04);box('Shower screen',x+.06,y-.42,1.25,.025,.80,1.85,'glass');cyl('Shower rail',x+.88,y-.12,1.55,.015,1.55,'metal')
def desk(x,y):
 box('Study desk',x,y,.98,1.4,.66,.09,'lightwood')
 for dx in [-.55,.55]:box('Desk support',x+dx,y,.57,.08,.50,.77,'wood')
 box('Laptop keyboard',x,y,1.04,.48,.32,.025,'dark');box('Laptop display',x,y+.13,1.22,.48,.035,.34,'dark');chair(x,y-.73,math.pi)
def wardrobe(x,y,w=1.5):
 box('Wardrobe',x,y,1.35,w,.60,2.32,'lightwood',bev=.03)
 for dx in [-w/4,w/4]:box('Wardrobe front',x+dx,y-.315,1.35,w/2-.025,.03,2.2,'white');box('Wardrobe handle',x+dx,y-.344,1.35,.025,.025,.27,'gold')
def rail_y(x,y,z,w,c):
 for i in range(int(w/.6)+1):box('Railing post',x-w/2+i*w/int(w/.6),y,z+.50,.035,.035,1.0,'darkgreen',c)
 box('Railing cap',x,y,z+1.02,w+.06,.06,.055,'wood',c)
def rail_x(x,y,z,d,c):
 for i in range(int(d/.6)+1):box('Railing post',x,y-d/2+i*d/int(d/.6),z+.50,.035,.035,1.0,'darkgreen',c)
 box('Railing cap',x,y,z+1.02,.06,d+.06,.055,'wood',c)

def slab_ring(W,D,innerW,innerD,z,h,mat,c):
 for yy in [-1,1]:box('Continuous floor edge',0,yy*(D+innerD)/4,z,W,(D-innerD)/2,h,mat,c)
 for xx in [-1,1]:box('Continuous floor edge',xx*(W+innerW)/4,0,z,(W-innerW)/2,innerD,h,mat,c)


def pitched_roof(W,D,top,mat):
 half=D/2+.40;rise=1.65;sl=math.hypot(half,rise);angle=math.atan2(rise,half)
 box('Continuous eaves slab',0,0,top-.02,W+.24,D+.24,.14,'white','Roof')
 for side in [-1,1]:
  o=box('Pitched roof',0,side*half/2,top+rise/2,W+.9,sl,.14,mat,'Roof');o.rotation_euler.x=-side*angle
  for i in range(int((W+.7)/.55)):
   o=box('Roof batten',-W/2-.30+i*.55,side*half/2,top+rise/2+.085,.025,sl,.027,mat,'Roof');o.rotation_euler.x=-side*angle
 box('Ridge cap',0,0,top+rise+.055,W+1.0,.17,.16,mat,'Roof')
 for side in [-1,1]:
  profile=[(-D/2,top+.05),(D/2,top+.05),(D/2,top+rise*(1-D/2/half)-.055),(0,top+rise-.055),(-D/2,top+rise*(1-D/2/half)-.055)]
  vs=[(side*W/2+dx+OX,y,z) for dx in ([-.18,0] if side>0 else [0,.18]) for y,z in profile]
  fs=[tuple(range(4,-1,-1)),tuple(range(5,10))]+[(i,(i+1)%5,(i+1)%5+5,i+5) for i in range(5)]
  me=bpy.data.meshes.new('Solid gable');me.from_pydata(vs,[],fs);me.materials.append(M['cream']);me.update();o=bpy.data.objects.new('Solid gable',me);col('Roof').objects.link(o)

def flat_roof(W,D,z):
 box('Flat roof',0,0,z,W+.5,D+.5,.20,'white','Roof')
 for x in [-W/2-.10,W/2+.10]:box('Parapet side',x,0,z+.35,.18,D+.38,.52,'cream','Roof');box('Parapet side coping',x,0,z+.64,.26,D-.06,.06,'sage','Roof')
 for y in [-D/2-.10,D/2+.10]:box('Parapet end',0,y,z+.35,W+.02,.18,.52,'cream','Roof');box('Parapet coping',0,y,z+.64,W+.46,.26,.06,'sage','Roof')


def camera(n,loc,target,ortho=None):
 d=bpy.data.cameras.new(n);d.lens=48;d.clip_end=500
 if ortho:d.type='ORTHO';d.ortho_scale=ortho
 o=bpy.data.objects.new(n,d);col('Studio').objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
def studio(scene):
 global Z,OX
 Z=0;OX=0;box('Studio ground',0,0,-.44,300,300,.12,'stone','Studio')
 world=bpy.data.worlds.new('Garden daylight');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.82,.89,.98,1);world.node_tree.nodes['Background'].inputs[1].default_value=.5;scene.world=world
 for n,kind,loc,e in [('Sun','SUN',(-16,-23,35),2.1),('Softbox','AREA',(0,-10,22),2300),('Fill','AREA',(14,9,16),1800)]:
  d=bpy.data.lights.new(n,kind);d.energy=e
  if kind=='AREA':d.shape='DISK';d.size=14
  else:d.angle=.15
  o=bpy.data.objects.new(n,d);col('Studio').objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,3))-o.location).to_track_quat('-Z','Y').to_euler()
 scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.resolution_x=1280;scene.render.resolution_y=960;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'

