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

def garden(hero=False):
 W,D=(24,24) if hero else (20,18)
 if hero:
  for x,y,w,d in [(-3.25,0,17.5,24),(11.25,0,1.5,24),(8,-8,5,8),(8,8,5,8)]:box('Garden base',x,y,-.15,w,d,.30,'grass','Landscape')
 else:box('Garden base',0,0,-.15,W,D,.30,'grass','Landscape',.08)
 # broken boundary hedge and pedestrian entry, never a solid slab across pool
 for x in [-W/2+.35,W/2-.35]:
  for y in [(-D/2+.7)+i*1.25 for i in range(int((D-1)/1.25))]:leaf('Boundary hedge',x,y,.46,(.42,.75,.48),'leaf')
 for x in [-W/2+.8+i*1.3 for i in range(int((W-1)/1.3))]:
  leaf('Rear hedge',x,D/2-.35,.46,(.78,.4,.48),'leaf')
  if abs(x-(-2 if hero else 0)) >1.5:leaf('Front hedge',x,-D/2+.35,.46,(.78,.4,.48),'leaf')
 hx=-2 if hero else 0
 box('Entry path',hx,-D/2+2.7,.035,1.7,5.4,.07,'stone','Landscape')
 box('Front terrace',hx,-5.75,.10,12.7,2.1,.20,'stone','Landscape',.03)
 for x in [hx-5.0,hx+5]:plant(x,-6.0,.85)
 # garden dining pergola outside the building footprint
 px=-8 if hero else -7.8;py=7.0 if hero else 6.2
 box('Garden deck',px,py,.08,3.1,3.0,.16,'lightwood','Landscape')
 for dx in [-1.35,1.35]:
  for dy in [-1.3,1.3]:box('Pergola post',px+dx,py+dy,1.37,.09,.09,2.65,'wood','Landscape')
 for i in range(7):box('Pergola lath',px-1.45+i*.48,py,2.71,.07,3.1,.08,'wood','Landscape')
 cyl('Garden table',px,py,.88,.58,.08,'wood','Landscape');cyl('Garden table foot',px,py,.47,.10,.8,'wood','Landscape')
 for dx in [-.95,.95]:box('Garden stool',px+dx,py,.45,.45,.45,.55,'sage','Landscape',.04)
 for x,y in ([(-9,8.6),(8.6,8.8)] if hero else [(-7.8,-3),(7.7,5.8)]):tree(x,y,1.15)
 if hero:
  # Recessed water basin on the east garden; no lawn mesh under the visible water.
  x,y=8,0
  for xx,yy,w,d in [(x-2,y,1,8),(x+2,y,1,8),(x,y-3.5,3,1),(x,y+3.5,3,1)]:box('Pool deck',xx,yy,.13,w,d,.26,'stone','Landscape')
  # Four coping bands with an open center, basin mesh below a separate water surface.
  for xx in [x-1.75,x+1.75]:box('Pool coping',xx,y,.33,.5,7,.16,'white','Landscape')
  for yy in [y-3.25,y+3.25]:box('Pool coping',x,yy,.33,3.0,.5,.16,'white','Landscape')
  box('Pool basin floor',x,y,-1.18,3.0,6.0,.12,'blue','Landscape')
  for xx in [x-1.50,x+1.50]:box('Pool basin side',xx,y,-.46,.14,6.14,1.44,'tile','Landscape')
  for yy in [y-3.0,y+3.0]:box('Pool basin end',x,yy,-.46,2.86,.14,1.44,'tile','Landscape')
  box('Pool water',x,y,.21,2.85,5.85,.018,'water','Landscape')
  for xx in [x-1.0,x+1.0]:
   cyl('Pool ladder grip',xx,y-2.7,.67,.026,.7,'metal','Landscape')
  for zz in [.35,.49]:box('Pool ladder rung',x,y-2.7,zz,2.0,.035,.035,'metal','Landscape')
  for yy in [6.3,8.2]:
   box('Sun lounger',8,yy,.48,1.9,.65,.13,'wood','Landscape',.04);o=box('Lounger back',8.64,yy,.71,.55,.63,.11,'fabric','Landscape',.03);o.rotation_euler.y=-.55
  # Back garden: three modest raised beds with paths between them.
  for bi,cx in enumerate([-4,-1,2]):
   cy=8.5;box('Vegetable soil bed',cx,cy,.24,1.90,3.3,.30,'earth','Landscape')
   for xx in [cx-1,cx+1]:box('Vegetable timber edging',xx,cy,.29,.10,3.5,.40,'wood','Landscape')
   for yy in [cy-1.7,cy+1.7]:box('Vegetable bed end',cx,yy,.29,1.9,.10,.40,'wood','Landscape')
   for row in range(4):
    for dx in [-.45,.45]:
     x,y=cx+dx,cy-1.1+row*.72
     if bi==0:
      for ang in [0,1.5,3,4.5]:leaf('Cabbage leaves',x+.12*math.cos(ang),y+.12*math.sin(ang),.52,(.20,.18,.15),'leafLight')
      leaf('Cabbage centre',x,y,.59,(.16,.16,.17),'sage')
     elif bi==1:
      for ang in [0,1.3,2.6,3.9,5.2]:leaf('Leafy vegetable',x+.08*math.cos(ang),y+.08*math.sin(ang),.64,(.09,.13,.27),'leaf')
     else:
      cyl('Tomato stake',x,y,.94,.02,1.30,'wood','Landscape')
      for dz in [.56,.80,1.03]:
       leaf('Tomato foliage',x,y,dz,(.22,.18,.19),'leaf');leaf('Tomato fruit',x+.15,y-.12,dz-.05,(.066,.066,.066),'tomato')
   sign(['青菜','香草','番茄'][bi],cx,cy-1.77,.58,.58,'Landscape')
  box('Vegetable garden approach',-1,5.8,.035,8.4,1.25,.07,'stone','Landscape')
  # Informal front planting: lawn, soft shrubs and mixed flowers, no rectangular beds.
  for gi,cx in enumerate([-6.15,2.15]):
   cy=-9.2
   leaf('Front garden planting mound',cx,cy,.035,(2.62,1.77,.075),'grass')
   for dx,dy,r in [(-1.6,.85,.48),(-.5,1.04,.55),(.8,.9,.43),(1.75,.55,.40),(-1.9,-.40,.36),(.8,-1.04,.29)]:
    leaf('Garden shrub',cx+dx,cy+dy,.25+r*.4,(r,r*.8,r*.75),'leaf' if dx>0 else 'leafLight')
   # Small clusters follow a loose curved border; deterministic jitter avoids crop-like rows.
   for cluster,(dx,dy) in enumerate([(-1.55,-.94),(-.50,-.64),(.62,-.42),(1.65,-.68),(-1.23,.22),(.0,.45),(1.66,.22)]):
    for j in range(4):
     ang=j*2.37+cluster*.71+gi*.3;r=.16+.055*(j%3)
     x=cx+dx+math.cos(ang)*r;y=cy+dy+math.sin(ang)*r;species=(cluster+gi)%4
     z=.42+.11*species+.045*(j%2)
     cyl('Flower stem',x,y,(.10+z)/2,.012,z-.10,'leaf','Landscape')
     leaf('Flower ground foliage',x,y,.22,(.16,.13,.15),'leafLight')
     if species==3:
      for k in range(4):leaf('Lavender blossom',x+.015*(k%2),y,z-.16+k*.07,(.055,.06,.07),'lavender')
     else:
      mat=['white','flowerPink','flowerYellow'][species]
      for k in range(6 if species==0 else 5):
       a=k*math.tau/(6 if species==0 else 5);leaf('Mixed flower petals',x+.082*math.cos(a),y+.082*math.sin(a),z,(.085,.085,.048),mat)
      leaf('Mixed flower centre',x,y,z+.025,(.042,.042,.04),'flowerYellow')
   for dx,dy in [(-2.03,.32),(.27,-1.18),(1.95,.92)]:
    for k in range(5):
     a=k*1.3;o=leaf('Ornamental grass',cx+dx+.06*math.cos(a),cy+dy+.06*math.sin(a),.33,(.055,.065,.31),'sage');o.rotation_euler=(math.cos(a)*.28,math.sin(a)*.28,a)
  # Extend the west front garden into the previously empty lawn, keeping the entry clear.
  tree(-10.0,-9.35,.92)
  for i,(x,y) in enumerate([(-10.45,-5.9),(-10.2,-6.8),(-10.45,-7.7),(-9.4,-10.7),(-8.35,-10.9),(-7.3,-10.85)]):
   leaf('West garden shrub',x,y,.43,(.58,.49,.48),'leaf' if i%2 else 'leafLight')
   for j in range(5):
    a=j*2.4+i;r=.36
    xx,yy=x+r*math.cos(a),y+r*math.sin(a);zz=.57+.09*(j%3)
    cyl('West flower stem',xx,yy,zz/2,.012,zz,'leaf','Landscape')
    for k in range(5):
     t=k*math.tau/5;leaf('West flower petals',xx+.09*math.cos(t),yy+.09*math.sin(t),zz,(.095,.09,.045),['flowerPink','flowerYellow','white'][i%3])
  box('West garden bench seat',-9.6,-7.9,.53,.55,1.6,.12,'wood','Landscape')
  box('West garden bench back',-9.86,-7.9,.9,.09,1.6,.62,'sage','Landscape')
  for yy in [-8.5,-7.3]:box('West bench leg',-9.6,yy,.28,.44,.09,.44,'darkgreen','Landscape')
  for i in range(4):cyl('West garden stepping stone',-8.98,-6.95-i*.62,.03,.27,.06,'stone','Landscape',8)
  # Southeast front lawn: a broad informal flower garden around a clear pool route.
  tree(9.65,-9.25,.82)
  for i,(x,y,r) in enumerate([(4.9,-10.6,.45),(6.0,-10.65,.58),(7.2,-10.65,.52),(8.45,-10.7,.55),(9.7,-10.65,.50),(10.65,-9.9,.50),(10.65,-8.6,.56),(10.45,-7.4,.47),(9.1,-7.25,.50),(7.65,-7.55,.42),(5.6,-8.2,.43)]):
   leaf('Southeast garden shrub',x,y,.24+r*.4,(r,r*.82,r*.83),'leafLight' if i%3 else 'leaf')
  # Large irregular drifts link the old east flower bed to the far corner.
  for i,(cx,cy) in enumerate([(4.9,-9.6),(5.4,-8.8),(6.3,-10.0),(6.55,-8.25),(7.4,-9.55),(8.2,-10.1),(8.55,-8.0),(10.35,-10.5),(10.55,-9.0),(10.4,-7.85),(9.55,-7.25)]):
   for j in range(7):
    a=j*2.4+i*.63;r=.20+.11*(j%3);x=cx+r*math.cos(a);y=cy+r*math.sin(a);z=.44+.1*(i%4)+.035*(j%2)
    cyl('Southeast flower stem',x,y,z/2,.012,z,'leaf','Landscape')
    leaf('Southeast flower foliage',x,y,.22,(.17,.15,.18),'leafLight')
    if i%4==3:
     for k in range(4):leaf('Southeast lavender',x,y,z-.15+k*.065,(.06,.065,.075),'lavender')
    else:
     for k in range(5):
      a=k*math.tau/5;leaf('Southeast mixed petals',x+.087*math.cos(a),y+.087*math.sin(a),z,(.095,.09,.05),['white','flowerPink','flowerYellow'][i%3])
     leaf('Southeast flower centre',x,y,z+.025,(.045,.045,.04),'flowerYellow')
  for cx,cy in [(5.0,-7.7),(7.45,-10.95),(8.85,-8.35),(10.85,-6.7)]:
   for k in range(7):
    a=k*2.2;o=leaf('Southeast ornamental grass',cx+.10*math.cos(a),cy+.1*math.sin(a),.35,(.06,.07,.38),'sage');o.rotation_euler=(math.cos(a)*.3,math.sin(a)*.3,a)
  # One miter-joined strip: 1.25 m wide, flush with terrace and pool-deck ends.
  pts=[Vector((4.35,-6.15)),Vector((6.25,-6.15)),Vector((8,-5.1)),Vector((8,-4))]
  dirs=[(b-a).normalized() for a,b in zip(pts,pts[1:])];norms=[Vector((-d.y,d.x)) for d in dirs];half=.625
  left=[];right=[];dist=[0]
  for a,b in zip(pts,pts[1:]):dist.append(dist[-1]+(b-a).length)
  for i,p in enumerate(pts):
   if i==0:off=norms[0]*half
   elif i==len(pts)-1:off=norms[-1]*half
   else:
    m=(norms[i-1]+norms[i]).normalized();off=m*(half/m.dot(norms[i]))
   zz=.20+.06*dist[i]/dist[-1];left.append((p.x+off.x,p.y+off.y,zz));right.append((p.x-off.x,p.y-off.y,zz))
  vs=[]
  for a,b in zip(left,right):vs.extend([a,b,(a[0],a[1],a[2]-.10),(b[0],b[1],b[2]-.10)])
  fs=[]
  for i in range(len(pts)-1):
   a=4*i;b=a+4;fs.extend([(a,a+1,b+1,b),(a+2,b+2,b+3,a+3),(a,b,b+2,a+2),(a+1,a+3,b+3,b+1)])
  fs.extend([(0,2,3,1),(12,13,15,14)])
  me=bpy.data.meshes.new('Pool garden path');me.from_pydata(vs,[],fs);me.materials.append(M['stone']);me.update();o=bpy.data.objects.new('Pool garden path',me);col('Landscape').objects.link(o)
  sign('主 角 的 家',-2,-4.63,2.78,2.0,'L01_Front')
 else:sign('庭 院 宅',0,-4.63,2.78,1.65,'L01_Front')

def villa(hero=False):
 global FLOOR,Z,OX
 H=3.25;OX=-2 if hero else 0
 for f in [1,2]:
  FLOOR=f;Z=(f-1)*H
  if f==1:box('Ground floor slab',0,0,.09,12.24,9.24,.18,'stone',group('Floor'))
  else:
   # stair hole x[-5.8,-3.5] y[-2.7,2.25]
   for x,y,w,d in [(1.15,0,9.3,8.60),(-4.65,-3.50,2.3,1.60),(-4.65,3.255,2.3,2.09)]:box('Upper floor slab',x,y,.055,w,d,.25,'lightwood',group('Floor'))
   slab_ring(12.24,9.24,11.60,8.60,.055,.25,'white',group('Floor'))
  if f==1:box('Oak floor finish',0,0,.192,11.65,8.65,.025,'lightwood',group('Floor'))
  front=[(-3.5,2.2,.9,2.55),(0,1.5,0,2.35),(3.4,2.4,.6,2.55)] if f==1 else [(-3.8,1.7,.9,2.55),(-1.1,1.2,0,2.35),(3.4,2.1,.8,2.55)]
  wall_y('Front wall',-4.5,-6,6,front,group('Front'))
  wall_y('Rear wall',4.5,-6,6,[(-4.5,1.3,1.2,2.55),(0,1.3,1.5,2.55),(3.5,2.4,.8,2.55)],group('Back'))
  wall_x('West wall',-5.91,-4.41,4.41,[(-1,2.2,1,2.55)],group('Back'))
  wall_x('East wall',5.91,-4.41,4.41,[(-2.4,2.3,.8,2.55),(2.3,2.3,.8,2.55)],group('East'))
  for x in [-5.82,5.82]:box('Front timber column',x,-4.63,1.68,.18,.15,3.0,'wood',group('Front'))
  if f==1:
   sofa(3,-1.75,2.55);table(2.5,2.15);kitchen(2.1,4.00,2.9)
   desk(-1.45,-.20)
   wall_y('Guest WC wall',1.95,-3.1,-.15,[(-1.3,.85,0,2.25)],group('Interior'),.12,2.85)
   wall_x('Guest WC side',-3.1,1.95,4.4,[],group('Interior'),.12,2.85);wall_x('Guest WC side',-.15,1.95,4.4,[],group('Interior'),.12,2.85);bath(-1.62,3.12)
   # One real flight to the second floor; 18 risers reach the floor surface.
   for i in range(18):
    top=.18+(i+1)*H/18;box('Stair tread %02d'%(i+1),-4.70,-2.65+(i+.5)*.27,top-.065,1.85,.27,.13,'wood',group('Stairs'))
   for x in [-5.48,-3.92]:beam('Stair stringer',(x,-2.6,.21),(x,2.16,3.33),.14,'sage',group('Stairs'))
   for x in [-5.66,-3.74]:
    for i in [0,4,8,12,17]:box('Stair post',x,-2.65+(i+.5)*.27,.18+(i+1)*H/18+.46,.035,.035,.92,'darkgreen',group('Stairs'))
    beam('Stair handrail',(x,-2.515,.18+H/18+.94),(x,2.075,3.43+.94),.05,'wood',group('Stairs'))
   plant(5.2,-3.5,.65,group('Interior'))
  else:
   wall_x('Bedroom corridor wall',1.3,-4.4,4.4,[(-1.3,.9,0,2.25),(.9,.9,0,2.25)],group('Interior'),.12,2.85)
   wall_y('Bedroom divider',.15,1.36,5.82,[],group('Interior'),.12,2.85)
   bed(3.9,2.6,1.6);wardrobe(2.25,3.93,1.3)
   bed(4.1,-1.70,1.4);desk(2.25,-3.2)
   wall_y('Bathroom wall',1.95,-1.65,1.2,[(-.2,.85,0,2.25)],group('Interior'),.12,2.85)
   wall_x('Bathroom side',-1.65,1.95,4.4,[],group('Interior'),.12,2.85);bath(-.2,3.12)
   rail_x(-3.48,-.23,.18,4.9,group('Interior'));rail_y(-4.63,-2.72,.18,2.30,group('Interior'))
   box('Balcony slab',2,-5.37,.055,7.7,1.5,.25,'stone',group('Front'));rail_y(2,-6.12,.18,7.7,group('Front'));rail_x(5.85,-5.37,.18,1.5,group('Front'));rail_x(-1.85,-5.37,.18,1.5,group('Front'))
   plant(5.25,-5.3,.55,group('Front'))
 Z=0;pitched_roof(12,9,6.52,'darkgreen' if hero else 'roof');OX=0;garden(hero)
 return {'key':'hero' if hero else 'courtyard','title':'主角泳池别墅' if hero else '庭院花园别墅','floors':2,'floorHeight':H,'slabThickness':.25,'units':1,'building':[12,9],'plot':[24,24] if hero else [20,18],'pool':[3,6] if hero else None,'poolWaterDepth':1.33 if hero else None,'poolGardenPathWidth':1.25 if hero else None,'southeastGarden':'tree, mixed shrubs, flower drifts and ornamental grasses' if hero else None,'vegetableBeds':3 if hero else 0,'frontGardenAreas':2 if hero else 0,'frontGardenStyle':'informal lawn, shrubs and mixed flowers; no rectangular beds' if hero else None,'program':['一层：客厅、餐厨、书桌、卫生间','二层：主卧、客卧兼书房、卫生间、阳台','花园、露台、廊架'+('、小泳池、后院菜园、入户道路两侧花园' if hero else '')],'stairsPerFlight':18,'sceneTarget':[OX,0,2.8],'scale':30 if hero else 27}

def apartment_floor(f,N):
 global FLOOR,Z
 FLOOR=f;Z=(f-1)*3.2
 if f==1:box('Ground slab',0,0,.08,22.28,11.28,.20,'stone',group('Floor'))
 else:
  for x,y,w,d in [(-6.535,0,8.57,10.64),(6.535,0,8.57,10.64),(0,-2.71,4.5,5.22),(0,4.64,4.5,1.36)]:box('Apartment floor slab',x,y,.08,w,d,.20,'lightwood',group('Floor'))
  slab_ring(22.28,11.28,21.64,10.64,.08,.20,'white',group('Floor'))
 for side in [-1,1]:
  sx=side*6.7
  # each suite has its own front balcony and bedroom to the quiet rear
  wall_y('Suite front',-5.5,sx-4.3,sx+4.3,[(sx-.8,1.3,0,2.3),(sx+2.0,1.9,.8,2.5)],group('Front'))
  wall_y('Suite rear',5.5,sx-4.3,sx+4.3,[(sx+side*1.4,2.8,.9,2.5),(sx-side*2.6,.8,1.6,2.5)],group('Back'))
  wall_x('Suite external',side*10.91,-5.41,5.41,[(-2.8,2.1,.9,2.5),(3.3,1.8,.9,2.5)],group('East' if side==1 else 'Back'))
  wall_x('Suite entry wall',side*2.4,-5.4,5.4,[(-3.4,1.0,0,2.3)],group('Interior'),.16,3.0)
  # rear private zone accessed from living room through an actual opening
  wall_y('Bedroom front divider',1.55,sx-4.16,sx+4.16,[(sx+side*3.4,.95,0,2.25),(sx-side*2.8,.85,0,2.25)],group('Interior'),.12,2.85)
  bx=sx-side*2.8
  wall_x('Bath side wall',sx-side*1.3,1.61,5.4,[],group('Interior'),.12,2.85)
  # Bathroom entered from a small private hall, rather than through the bedroom furniture.
  wall_y('Bathroom door wall',2.80,min(bx-1.4,bx+1.4),max(bx-1.4,bx+1.4),[(bx,.85,0,2.25)],group('Interior'),.12,2.85)
  bath(bx,4.05);bed(sx+side*1.3,3.92,1.65);wardrobe(sx-side*.45,4.90,1.0)
  sofa(sx+side*1.35,-3.15,2.25);table(sx-side*1.60,-.25)
  before=set(col(group('Interior')).objects);kx=sx+side*.55;kitchen(kx,.99,2.2)
  if side<0:
   for o in set(col(group('Interior')).objects)-before:o.location.x=2*kx-o.location.x
  # Side-facing work desk uses its own zone clear of the entry.
  desk(sx+side*3.0,-.80)
  box('Balcony slab',sx,-6.44,.08,7.6,1.6,.20,'stone',group('Front'));rail_y(sx,-7.24,.18,7.6,group('Front'))
  for x in [sx-3.8,sx+3.8]:rail_x(x,-6.44,.18,1.6,group('Front'))
  plant(sx+side*3.0,-6.25,.55,group('Front'))
  sign('%d0%d'%(f,1 if side<0 else 2),side*2.31,-3.98,2.56,.64,group('Interior'))
 # core front opens at the ground; upper levels use a tall window
 wall_y('Stair core front',-5.5,-2.4,2.4,[(0,1.9,0 if f==1 else .85,2.5)],group('Front'))
 wall_y('Stair core rear',5.5,-2.4,2.4,[(0,2.0,.8,2.5)],group('Back'))
 # Return stair: two 9-step flights and half-landing. Upper stairwell slab has a real opening.
 if f<N:
  for i in range(9):
   top=.18+(i+1)*3.2/18;box('Stair west %02d'%(i+1),-1.15,-.1+(i+.5)*.27,top-.07,1.65,.27,.14,'wood',group('Stairs'))
   top=.18+(i+10)*3.2/18;box('Stair east %02d'%(i+1),1.15,2.33-(i+.5)*.27,top-.07,1.65,.27,.14,'wood',group('Stairs'))
  box('Stair half landing',0,3.145,1.71,4.12,1.63,.14,'stone',group('Stairs'))
  for x in [-2.01,-.30]:
   beam('West handrail',(x,.035,1.30),(x,2.195,2.72),.045,'wood',group('Stairs'))
   for i in [0,4,8]:box('West stair post',x,-.1+(i+.5)*.27,.18+(i+1)*3.2/18+.47,.035,.035,.94,'darkgreen',group('Stairs'))
  for x in [.30,2.01]:
   beam('East handrail',(x,2.195,2.90),(x,.035,4.32),.045,'wood',group('Stairs'))
   for i in [0,4,8]:box('East stair post',x,2.33-(i+.5)*.27,.18+(i+10)*3.2/18+.47,.035,.035,.94,'darkgreen',group('Stairs'))
 if f>1:
  rail_y(0,3.99,.18,4.35,group('Interior'))
  # split front guard leaves east flight arrival clear
  if f==N:rail_y(-1.15,-.17,.18,2.1,group('Interior'))
 sign('河 畔 公 寓' if f==1 else '%d F'%f,0,-5.63,2.86,2.5 if f==1 else .8,group('Front'))

def apartment(N):
 global Z,FLOOR
 for f in range(1,N+1):apartment_floor(f,N)
 Z=0;FLOOR=1;flat_roof(22,11,N*3.2+.08)
 box('Apartment garden base',0,-.2,-.18,25,17,.26,'grass','Landscape',.08)
 box('Entrance path',0,-6.8,.015,2.2,2.6,.08,'stone','Landscape')
 for x in [-11.75,11.75]:tree(x,4.3,.85);plant(x,-4.9,.7)
 return {'key':'apartment-'+str(N),'title':'河畔公寓 · '+str(N)+'层','floors':N,'floorHeight':3.2,'slabThickness':.20,'units':N*2,'unitsPerFloor':2,'building':[22,11],'plot':[25,17],'stairsPerFlight':18,'program':['每层左右各一套独立住宅','每套：客餐厅、厨房、卧室、卫浴、书桌、阳台','中央公共门厅与双跑楼梯'],'sceneTarget':[0,-.4,N*1.4],'scale':30+N*1.5}

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

def finish(meta):
 key=meta['key'];out=ROOT/key;out.mkdir(exist_ok=True);scene=bpy.context.scene;scene.name='01 Exterior';scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
 # Bake only bevel modifiers, preserving named independent model parts.
 for o in list(bpy.data.objects):
  if o.type=='MESH' and o.modifiers:
   o.data=o.data.copy()
   bpy.context.view_layer.objects.active=o
   for m in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=m.name)
 for n,c in list(C.items()):
  root=bpy.data.objects.new(n,None);c.objects.link(root)
  for o in list(c.objects):
   if o!=root:o.parent=root
 bpy.ops.object.select_all(action='DESELECT')
 for o in bpy.data.objects:
  if o.type in ['MESH','EMPTY']:o.select_set(True)
 asset=out/(key+'.glb');bpy.ops.export_scene.gltf(filepath=str(asset),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False)
 meshes=[o for o in bpy.data.objects if o.type=='MESH'];tri=0;degen=0;coords=[]
 for o in meshes:
  o.data.calc_loop_triangles();tri+=len(o.data.loop_triangles)
  for v in o.data.vertices:
   assert all(math.isfinite(x) for x in v.co);coords.append(o.matrix_world@v.co)
  for t in o.data.loop_triangles:
   a,b,c=[o.data.vertices[j].co for j in t.vertices]
   if (b-a).cross(c-a).length<1e-10:degen+=1
 meta.update({'meshObjects':len(meshes),'triangles':tri,'degenerateTriangles':degen,'bounds':[max(v[i] for v in coords)-min(v[i] for v in coords) for i in range(3)],'unit':'metres','sha256':hashlib.sha256(asset.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'status':'design-review','sourceAxes':{'up':'+Z','front':'-Y'},'glbAxes':{'up':'+Y','front':'+Z'}})
 assert degen==0
 (out/'manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
 studio(scene);target=Vector(meta['sceneTarget']);dist=meta['scale'];scene.camera=camera('Exterior camera',(dist*.9,-dist*1.20,target.z+dist*.8),target)
 renders=[(scene,'exterior.png')]
 for f in range(1,meta['floors']+1):
  sf=scene.copy();sf.name='%02d Floor %d Interior'%(f+1,f);sf.use_fake_user=True
  for child in sf.view_layers[0].layer_collection.children:
   n=child.name
   if n=='Roof':child.exclude=True
   elif n.startswith('L') and len(n)>3 and n[1:3].isdigit():
    level=int(n[1:3]);part=n[4:];child.exclude=level>f or (level==f and part in ['Front','East'])
  z=(f-1)*meta['floorHeight'];sf.camera=camera('Floor %d cutaway camera'%f,(dist*.75,-dist*.90,z+dist*.85),(0,0,z+1))
  sp=sf.copy();sp.name='%02d Floor %d Plan'%(f+meta['floors']+1,f);sp.use_fake_user=True;sp.camera=camera('Floor %d plan camera'%f,(0,-.001,z+45),(0,0,z),35 if key=='hero' else meta['scale'])
  if f==1 or key in ['courtyard','hero']:renders.extend([(sf,'floor-%d-interior.png'%f),(sp,'floor-%d-plan.png'%f)])
 bpy.context.window.scene=scene
 for scr in bpy.data.screens:
  for ar in scr.areas:
   if ar.type=='VIEW_3D':ar.spaces.active.shading.type='MATERIAL';ar.spaces.active.overlay.show_overlays=False;ar.spaces.active.region_3d.view_perspective='CAMERA'
 bpy.ops.wm.save_as_mainfile(filepath=str(out/(key+'.blend')))
 for sc,file in renders:
  sc.render.filepath=str(out/file);bpy.ops.render.render(write_still=True,scene=sc.name);print('RENDERED',key,file,flush=True)
 print('COMPLETE',key,json.dumps(meta,ensure_ascii=False),flush=True)

keys=os.environ.get('RESIDENTIAL_KEYS','courtyard,hero,apartment-3,apartment-4,apartment-5').split(',')
for key in keys:
 init();meta=villa(key=='hero') if key in ['courtyard','hero'] else apartment(int(key[-1]));finish(meta)
