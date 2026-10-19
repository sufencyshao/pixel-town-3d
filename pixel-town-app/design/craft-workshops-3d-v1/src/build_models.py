import sys,math,json,hashlib,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import model_helpers as h
import bpy
from mathutils import Vector
R=Path(__file__).resolve().parent.parent
h.ROOT=R
h.PALETTE.update({'gravel':'d3c5ab','clay':'ba7f65','bluegrey':'7d9eab','canvas':'f4e4bf','ochre':'d4aa54','rust':'a35e4b','rubber':'3e4744','acoustic':'89947d','leafDark':'5c7558'})
h.init();box,cyl,leaf,beam=h.box,h.cyl,h.leaf,h.beam
BUILDINGS=[{'id':'D01','name':'木工坊','center':[-18.75,10],'size':[27.5,15],'door':'s','roof':'pitch','people':['大森','榆棠']},{'id':'D02','name':'修理铺','center':[17,10],'size':[30,15],'door':'s','roof':'pitch','people':['罗栓']},{'id':'D03','name':'共享画室','center':[-18.75,-14.125],'size':[27.5,13.25],'door':'n','roof':'flat','people':['鹿眠']},{'id':'D04','name':'排练室','center':[17,-14.125],'size':[30,13.25],'door':'n','roof':'flat','people':['迟野']}]

def label(t,x,y,z,w,c,face='s'):
 before=set(h.col(c).objects);box('Facade sign',x,y,z,w,.085,.42,'darkgreen',c);h.text('Sign '+t,t,x,y-.05,z,.26,'white',c)
 if face=='n':
  for o in set(h.col(c).objects)-before:o.location.y=2*y-o.location.y;o.rotation_euler.z+=math.pi

def bench(x,y,c='Street_Furniture',facing='s'):
 box('Outdoor bench seat',x,y,.52,2.6,.70,.13,'lightwood',c)
 yy=y+.30 if facing=='s' else y-.30
 box('Outdoor bench back',x,yy,.90,2.6,.10,.65,'sage',c)
 for dx in [-.9,.9]:box('Bench support',x+dx,y,.27,.13,.58,.50,'darkgreen',c)

def tabletop(n,x,y,w,d,c,z=1.02):
 box(n,x,y,z,w,d,.14,'lightwood',c)
 for dx in [-w/2+.22,w/2-.22]:
  for dy in [-d/2+.20,d/2-.20]:box(n+' leg',x+dx,y+dy,(z-.07+.18)/2,.12,.12,z-.07-.18,'wood',c)
 box(n+' lower shelf',x,y,.43,w-.3,d-.3,.09,'wood',c)

def shelf(x,y,w,c,kind='boxes'):
 for z in [.48,1.3,2.12]:
  box('Stock shelf',x,y,z,w,.85,.08,'lightwood',c)
  for j in range(int(w/.85)):
   xx=x-w/2+.45+j*.85
   if kind=='pots':cyl('Paint tin',xx,y,z+.24,.23,.4,['bluegrey','ochre','clay'][j%3],c)
   else:
    box('Labelled parts bin',xx,y,z+.26,.68,.64,.44,'sage',c)
    box('Parts bin label',xx,y-.327,z+.29,.3,.015,.1,'white',c)
 for xx in [x-w/2+.06,x+w/2-.06]:box('Shelf frame',xx,y,1.45,.085,.8,2.6,'darkgreen',c)

def torus(n,x,y,z,r,t,c,mat='rubber',rot=(math.pi/2,0,0)):
 bpy.ops.mesh.primitive_torus_add(major_segments=24,minor_segments=6,location=(x,y,z),major_radius=r,minor_radius=t,rotation=rot)
 o=bpy.context.object;o.name=n;o.data.materials.append(h.M[mat])
 for col in list(o.users_collection):col.objects.unlink(o)
 h.col(c).objects.link(o);return o

def bicycle(x,y,c,color='sage'):
 for dx in [-.86,.86]:
  torus('Bicycle tire',x+dx,y,.79,.54,.048,c)
  torus('Bicycle rim',x+dx,y,.79,.49,.018,c,'metal')
  for a in range(0,360,60):
   a=math.radians(a);beam('Bicycle spoke',(x+dx,y,.79),(x+dx+.48*math.cos(a),y,.79+.48*math.sin(a)),.018,'metal',c)
 for a,b in [((-.86,0,.79),(-.12,0,.80)),((-.86,0,.79),(-.4,0,1.48)),((-.4,0,1.48),(-.12,0,.80)),((-.4,0,1.48),(.55,0,1.50)),((-.12,0,.80),(.55,0,1.50)),((.55,0,1.50),(.86,0,.79))]:
  beam('Bicycle frame',(x+a[0],y+a[1],a[2]),(x+b[0],y+b[1],b[2]),.055,color,c)
 beam('Seat post',(x-.4,y,1.48),(x-.45,y,1.65),.05,'metal',c)
 box('Bicycle saddle',x-.46,y,1.67,.36,.2,.075,'rubber',c)
 beam('Handle stem',(x+.55,y,1.5),(x+.6,y,1.78),.04,'metal',c);box('Handlebar',x+.6,y,1.78,.05,.56,.04,'metal',c)
 cyl('Bicycle workstand',x,y+.28,.74,.04,1.1,'metal',c);box('Stand feet',x,y+.28,.25,.65,.6,.06,'metal',c)

def flower(x,y,col,s=1):
 z=.6*s;c='Landscape';cyl('Flower stem',x,y,z/2,.015*s,z,'leaf',c)
 for k in range(5):
  a=k*math.tau/5;leaf('Mixed flower petal',x+.09*s*math.cos(a),y+.09*s*math.sin(a),z,(.10*s,.08*s,.05*s),col,c)
 leaf('Flower pollen',x,y,z+.02,(.035,.035,.03),'ochre',c)

def tree(x,y,s=1):
 cyl('Courtyard tree trunk',x,y,1.2*s,.17*s,2.4*s,'wood','Landscape')
 for dx,dy,z in [(0,0,3),(-.7,.15,2.6),(.6,.2,2.8),(0,-.6,2.6)]:leaf('Courtyard tree canopy',x+dx*s,y+dy*s,z*s,(1.1*s,1.0*s,1.1*s),'leafLight' if dx==0 else 'leaf','Landscape')

def pitched(b,mat):
 x,y=b['center'];w,d=b['size'];c=b['id']+'_Roof';eave=4.18;half=d/2+.5;rise=2.0
 # A ceiling slab closes the wall/roof junction and hides with the roof.
 box('Continuous eaves ceiling',x,y,4.25,w+.20,d+.20,.14,'white',c)
 for side in [-1,1]:
  ang=-side*math.atan2(rise,half);sl=math.hypot(half,rise)
  o=box('Pitched metal roof',x,y+side*half/2,eave+rise/2+.16,w+1,sl,.15,mat,c);o.rotation_euler.x=ang
  for i in range(int(w/.85)+1):
   o=box('Standing roof seam',x-w/2+i*.85,y+side*half/2,eave+rise/2+.25,.025,sl,.03,mat,c);o.rotation_euler.x=ang
 box('Roof ridge cap',x,y,eave+rise+.18,w+1.1,.22,.18,mat,c)
 # Solid gable infill, closed at the ceiling slab instead of single sided triangles.
 for side in [-1,1]:
  underside=eave+.16-.075/math.cos(math.atan2(rise,half))
  profile=[(y-d/2,4.30),(y+d/2,4.30),(y+d/2,underside+rise*(1-d/2/half)),(y,underside+rise),(y-d/2,underside+rise*(1-d/2/half))]
  vs=[(x+side*w/2+dx,yy,zz) for dx in [-.08,.08] for yy,zz in profile]
  fs=[tuple(range(4,-1,-1)),tuple(range(5,10))]+[(i,(i+1)%5,(i+1)%5+5,i+5) for i in range(5)]
  me=bpy.data.meshes.new('Solid gable');me.from_pydata(vs,[],fs);me.materials.append(h.M['cream']);me.update();o=bpy.data.objects.new('Solid gable',me);h.col(c).objects.link(o)
 for yy in [y-half,y+half]:box('Eaves gutter',x,yy,4.27,w+.6,.18,.14,'darkgreen',c)

def flat(b,mat):
 x,y=b['center'];w,d=b['size'];c=b['id']+'_Roof'
 if b['id']=='D03':
  # Real roof opening under the clerestory, with four non-overlapping perimeter slabs.
  for ww,dd,z,th,material in [(w+.35,d+.35,4.30,.24,'white'),(w-.2,d-.2,4.44,.035,mat),(12.1,3.1,4.60,.25,'white')]:
   for sy in [-1,1]:box('Lantern opening ring',x,y+sy*(dd+2.8)/4,z,ww,(dd-2.8)/2,th,material,c)
   for sx in [-1,1]:box('Lantern opening side',x+sx*(ww+11.8)/4,y,z,(ww-11.8)/2,2.8,th,material,c)
 else:
  box('Continuous flat roof',x,y,4.30,w+.35,d+.35,.24,'white',c)
  box('Roof surface',x,y,4.44,w-.2,d-.2,.035,mat,c)
 for yy in [y-d/2,y+d/2]:box('Roof parapet',x,yy,4.67,w+.35,.18,.5,'cream',c);box('Parapet coping',x,yy,4.94,w+.45,.28,.065,'sage',c)
 for xx in [x-w/2,x+w/2]:box('Roof parapet side',xx,y,4.67,.18,d-.18,.5,'cream',c);box('Side coping',xx,y,4.94,.28,d-.05,.065,'sage',c)
 if b['id']=='D03':
  # Raised glazed daylight lantern. Purely architectural, not animated ventilation.
  for xx in [x-6,x+6]:box('Lantern end',xx,y,5.18,.10,3,1,'sage',c)
  for yy in [y-1.5,y+1.5]:
   box('Lantern glazing',x,yy,5.18,12,.035,.9,'glass',c)
   for dx in [-6,-3,0,3,6]:box('Lantern mullion',x+dx,yy,5.18,.07,.10,1,'sage',c)
  box('Lantern cap',x,y,5.76,12.4,3.4,.16,'sage',c)
 else:
  for xx in [x-10,x+10]:
   box('Acoustic ventilation unit',xx,y+2,4.87,2.2,1.3,.8,'sage',c)
   for j in range(5):box('Vent louver',xx-.8+j*.4,y+1.33,4.87,.15,.04,.55,'darkgreen',c)

def shell(b):
 x,y=b['center'];w,d=b['size'];bid=b['id'];front=y-d/2 if b['door']=='s' else y+d/2
 box(bid+' foundation',x,y,.09,w,d,.18,'stone',bid+'_Floor')
 box(bid+' floor finish',x,y,.185,w-.22,d-.22,.01,'lightwood' if bid in ['D03','D04'] else 'stone',bid+'_Floor')
 h.OX=x
 for side in [-1,1]:
  frontside=(side==-1 and b['door']=='s') or (side==1 and b['door']=='n')
  opens=[(-w*.32,4.2,1.05,3.35),(w*.32,4.2,1.05,3.35)]
  if frontside:opens.append((0,2.8,0,3.15))
  elif bid=='D02':opens=[(-8.2,4,1.05,3.35),(8,4.2,0,3.5)]
  elif bid=='D01':opens=[(0,3.8,1.3,3.35),(-8.8,4.2,2.65,3.55)]
  elif bid=='D04':opens=[]
  elif bid=='D03':opens=[(0,3.8,1.3,3.35)]
  else:opens.append((0,3.8,1.3,3.35))
  h.wall_y(bid+' facade',y+side*d/2,-w/2,w/2,opens,bid+'_Front' if frontside else bid+'_Shell',.22,4)
 for side in [-1,1]:
  opens=[(y,2.6,0,3.15)] if bid=='D01' and side==-1 else [(y,4.2,1.15,3.35)]
  if bid=='D04' and side==1:opens=[]
  h.wall_x(bid+' side wall',side*w/2,y-d/2+.11,y+d/2-.11,opens,bid+'_Shell',.22,4)
 h.OX=0
 c=bid+'_Front';signy=front+(-.17 if b['door']=='s' else .17)
 label(bid+'  '+b['name'],x,signy,3.94,7.2,c,b['door'])
 # Front canopy sits above doorway, clear of the 3.15 m opening.
 canopy_y=front+(-.75 if b['door']=='s' else .75)
 box('Entry canopy',x,canopy_y,3.48,5.5,1.45,.14,'wood' if bid=='D01' else 'sage',c)
 for dx in [-2.45,2.45]:beam('Canopy brace',(x+dx,front,2.72),(x+dx,canopy_y,3.4),.065,'wood',c)
 if b['roof']=='pitch':pitched(b,'clay' if bid=='D01' else 'darkgreen')
 else:flat(b,'sage' if bid=='D03' else 'acoustic')

box('D site',0,0,-.18,75,55,.36,'grass','Ground')
# Central visitor lane, a north-south pedestrian spine and a west/north service lane.
PATH_RECTS=[(-37.5,37.5,-4.5,-.5,'gravel'),(-3.0,0,-27.5,27.5,'gravel'),(-37.5,-33.2,-27.5,27.5,'stone'),(-37.5,35.0,20,24.5,'stone')]
for b in BUILDINGS:
 x,y=b['center'];w,d=b['size'];front=y-d/2 if b['door']=='s' else y+d/2
 PATH_RECTS.append((x-1.7,x+1.7,min(front,-2.5),max(front,-2.5),'gravel'))
# Rear receiving doors, shaded waiting areas and separated loading pads.
PATH_RECTS += [(-35.4,-32.5,8.5,11.5,'stone'),(22.6,27.4,17.5,22.5,'stone'),(-29,-24,-.5,1.5,'gravel'),(6,11,-.5,1.5,'gravel'),(-29,-24,-6.5,-4.5,'gravel'),(24,29,-6.5,-4.5,'gravel')]
for b in BUILDINGS:shell(b)
# D01: four maker benches, wood storage, tool wall and machines.
c='D01_Interior'
for i,(x,y) in enumerate([(-26,6.8),(-11.5,6.8),(-26,13.2),(-11.5,13.2)]):
 tabletop('Carpenter workbench',x,y,4.8,1.8,c,1.15)
 box('Woodworking vise body',x-1.85,y-.95,1.03,.5,.26,.36,'darkgreen',c)
 beam('Vise screw',(x-1.85,y-1.15,1.05),(x-1.85,y-1.6,1.05),.04,'metal',c)
 box('Workpiece board',x,y,1.28,2.8,.68,.10,'wood',c)
 box('Hand plane sole',x+.65,y,1.40,.40,.15,.12,'metal',c);box('Plane grip',x+.65,y,1.49,.18,.09,.10,'wood',c)
 for dx in [-.65,.65]:box('Clamp jaw',x+dx,y+.32,1.35,.08,.65,.08,'darkgreen',c)
# Material rack along west-north corner, stored timbers supported at three levels.
for z in [.55,1.3,2.05]:
 box('Lumber rack shelf',-28,16.3,z,6.5,1.15,.12,'darkgreen',c)
 for j in range(5):box('Stored timber',-28,15.85+j*.22,z+.16,5.9,.15,.18,'wood' if j%2 else 'lightwood',c)
for x in [-30.6,-25.4]:box('Lumber rack upright',x,16.3,1.45,.15,.95,2.65,'darkgreen',c)
box('Wall tool board',-11,17.29,2.25,8,.09,2.0,'wood',c)
for i in range(9):
 x=-14.4+i*.85;box('Hanging tool handle',x,17.13,2.15,.06,.07,.67,'lightwood',c)
 box('Tool steel head',x,17.1,2.52,.30,.10,.14,'metal',c)
tabletop('Lathe bench',-20.4,15.8,3.1,1.1,c)
box('Lathe machine rail',-20.4,15.8,1.26,2.6,.42,.16,'sage',c)
for x in [-21.4,-19.4]:box('Lathe headstock',x,15.8,1.52,.38,.55,.45,'sage',c)
o=cyl('Lathe wood blank',-20.4,15.8,1.55,.17,1.5,'wood',c);o.rotation_euler.y=math.pi/2
box('Dust collector base',-6.4,15.9,.65,1.0,1.0,.9,'sage',c);cyl('Dust collector drum',-6.4,15.9,1.64,.43,1.1,'fabric',c)
box('Finished furniture display',-28,3.8,.55,2.8,.7,.74,'sage',c)
for dx in [-.95,.95]:box('Display stool',-28+dx,3.8,1.1,.55,.5,.38,'wood',c)
# D02: repair reception, two cycle service bays, electronics diagnostics and stocked spares.
c='D02_Interior'
box('Repair reception counter',9,5.0,.83,6,1.05,1.3,'bluegrey',c);box('Service countertop',9,5,1.52,6.1,1.15,.10,'lightwood',c)
box('Intake terminal',10,5,1.72,.55,.12,.33,'dark',c)
for x in [8,14]:
 tabletop('Electronics repair bench',x,15.65,4.3,1.3,c)
 box('Anti static work mat',x,15.65,1.10,2.5,.8,.025,'darkgreen',c)
 box('Bench test meter',x-.75,15.8,1.38,.58,.32,.5,'bluegrey',c);box('Meter display',x-.75,15.625,1.4,.38,.02,.24,'dark',c)
 box('Appliance casing',x+.5,15.5,1.4,.7,.6,.55,'white',c)
 box('Bench task light',x+1.7,15.8,1.55,.04,.04,.9,'metal',c);box('Task light head',x+1.4,15.8,1.98,.65,.14,.08,'white',c)
for i,y in enumerate([7,12.7]):
 box('Cycle repair bay pad',25,y,.215,5.5,3.5,.035,'bluegrey',c)
 bicycle(25,y,c,'sage' if i else 'clay')
 box('Mobile tool trolley',28.3,y, .78,.85,.72,1.1,'clay',c)
 for z in [.42,.69,.96]:box('Trolley drawer',28.3,y-.37,z,.71,.02,.21,'rust',c)
shelf(7.2,11.7,6.5,c)
for y in [6,11,15]:
 for z in [.5,1.3,2.1]:box('Side parts shelf',31,y,z,1.0,3.3,.08,'lightwood',c)
 for z in [.85,1.65]:
  for yy in [y-.8,y+.8]:box('Spare parts crate',31,yy,z,.7,.65,.52,'sage',c)
# Raised open shutter at the rear loading doorway (keeps the opening free).
for z in [3.76,3.9,4.04]:box('Raised service shutter',25,17.59,z,4.15,.10,.11,'metal','D02_Shell')
# D03: six easels, shared art tables, supply shelves, wash-up sink and wall gallery.
c='D03_Interior'
def easel(x,y,variant):
 before=set(h.col(c).objects)
 for dx in [-.48,.48]:beam('Easel front leg',(x+dx,y,.2),(x+dx*.5,y+.15,2.3),.075,'wood',c)
 beam('Easel rear support',(x,y+.65,.2),(x,y+.1,2.2),.07,'wood',c)
 box('Easel crossbar',x,y,1.0,1.4,.16,.09,'wood',c)
 box('Canvas frame',x,y-.04,1.75,1.23,.09,1.40,'wood',c)
 box('Canvas painting',x,y-.10,1.75,1.08,.025,1.24,'canvas',c)
 # Relief color shapes form small landscape studies, all actual colored mesh.
 box('Painted horizon',x,y-.119,1.50,1.02,.012,.35,'sage' if variant%2 else 'bluegrey',c)
 leaf('Painted sun',x+.26,y-.137,2.03,(.14,.012,.14),'ochre',c)
 leaf('Painted hill',x-.20,y-.14,1.67,(.34,.012,.22),'leafDark' if variant%2 else 'clay',c)
 for o in set(h.col(c).objects)-before:
  o.location.x=2*x-o.location.x;o.location.y=2*y-o.location.y;o.rotation_euler.z+=math.pi
for i,(x,y) in enumerate([(-28,-12),(-23,-12),(-12,-12),(-8,-12),(-28,-17),(-23,-17)]):easel(x,y,i)
for x in [-13,-8]:
 tabletop('Shared art table',x,-17,3.3,1.9,c,1.02)
 for dx in [-.9,0,.9]:
  box('Drawing sheet',x+dx,-17,1.10,.6,.85,.01,'white',c)
  cyl('Brush cup',x+dx,-16.4,1.27,.09,.30,'clay',c)
  for k in [-.04,.04]:beam('Paint brush',(x+dx+k,-16.4,1.3),(x+dx+k+.04,-16.4,1.65),.018,'wood',c)
shelf(-28,-19.7,6.2,c,'pots')
box('Studio wash cabinet',-20.8,-19.9,.77,3,.75,1.16,'sage',c);box('Studio sink rim',-20.8,-19.9,1.4,3.05,.82,.10,'metal',c)
box('Wash basin recess',-20.8,-19.9,1.459,1.6,.50,.015,'darkgreen',c)
beam('Sink tap upright',(-20.8,-19.6,1.45),(-20.8,-19.6,1.87),.04,'metal',c);beam('Sink tap spout',(-20.8,-19.6,1.87),(-20.8,-19.95,1.87),.04,'metal',c)
for i,x in enumerate([-29,-25,-12,-8]):
 box('Gallery frame',x,-20.58,3.2,2.2,.10,.90,'wood',c);box('Gallery canvas',x,-20.51,3.2,2.02,.035,.74,'canvas',c)
 leaf('Gallery artwork',x-.3,-20.48,3.17,(.6,.015,.24),['bluegrey','clay','sage','ochre'][i],c)
# D04: entry lobby, small lounge, rehearsal deck, keyboard, drum kit and guitars.
c='D04_Interior'
for x in [14.6,19.4]:box('Rehearsal entry vestibule side',x,-9.0,1.9,.16,2.8,3.4,'cream',c)
box('Rehearsal stage deck',22,-17.9,.34,16,4.6,.30,'wood',c)
box('Stage front step',22,-15.28,.26,5.0,.65,.16,'lightwood',c)
# Upright piano and keyboard with alternating keys.
box('Upright piano body',10,-18.8,1.11,3,.72,1.75,'darkgreen',c)
box('Piano key shelf',10,-18.30,1.08,3,.62,.16,'wood',c)
for i in range(28):box('Piano white key',8.57+i*.105,-18.20,1.18,.10,.42,.07,'white',c)
for i in range(27):
 if i%7 not in [2,6]:box('Piano black key',8.625+i*.105,-18.35,1.235,.06,.24,.06,'dark',c)
box('Piano stool',10,-17.30,.55,1.3,.5,.50,'wood',c)
# Bass drum horizontal and toms; cymbals on slim tripods.
dx,dy=26,-18.0
o=cyl('Bass drum shell',dx,dy,1.14,.65,.62,'clay',c,24);o.rotation_euler.x=math.pi/2
for yy in [dy-.33,dy+.33]:
 o=cyl('Bass drum head',dx,yy,1.14,.62,.025,'white',c,24);o.rotation_euler.x=math.pi/2
for xx,yy,z,r in [(dx-.5,dy,1.86,.35),(dx+.45,dy,1.9,.34),(dx-1.1,dy-.45,1.17,.40)]:
 cyl('Tom drum shell',xx,yy,z,r,.40,'clay',c,20);cyl('Tom drum skin',xx,yy,z+.21,r,.025,'white',c,20)
for xx in [dx-.5,dx+.45]:beam('Tom mounting arm',(dx,dy,1.75),(xx,dy,1.67),.04,'metal',c)
for a in [0,2.1,4.2]:beam('Floor tom support',(dx-1.1+.27*math.cos(a),dy-.45+.27*math.sin(a),1.0),(dx-1.1+.33*math.cos(a),dy-.45+.33*math.sin(a),.50),.03,'metal',c)
for xx,yy in [(dx-1.4,dy+.5),(dx+1.25,dy-.6)]:
 cyl('Cymbal stand',xx,yy,1.375,.025,1.75,'metal',c);cyl('Brass cymbal',xx,yy,2.24,.5,.025,'gold',c,24)
 for a in [0,2.1,4.2]:beam('Cymbal tripod',(xx,yy,.9),(xx+.45*math.cos(a),yy+.45*math.sin(a),.50),.025,'metal',c)
cyl('Drummer stool',dx,dy-1,.85,.32,.12,'dark',c)
cyl('Drum stool support',dx,dy-1,.64,.07,.30,'metal',c)
cyl('Drum stool foot',dx,dy-1,.52,.28,.06,'metal',c)
for x in [17,20]:
 before=set(h.col(c).objects)
 leaf('Guitar lower body',x,-18.2,1.03,(.43,.16,.5),'clay',c);leaf('Guitar upper body',x,-18.2,1.48,(.30,.14,.35),'wood',c)
 box('Guitar neck',x,-18.2,2.0,.12,.11,1.1,'wood',c);box('Guitar headstock',x,-18.2,2.60,.18,.12,.25,'lightwood',c)
 o=cyl('Guitar sound hole',x,-18.37,1.33,.13,.015,'dark',c);o.rotation_euler.x=math.pi/2
 for d in [-.03,0,.03]:beam('Guitar string',(x+d,-18.40,.99),(x+d,-18.28,2.5),.005,'metal',c)
 for d in [-.3,.3]:beam('Guitar stand',(x,-18.2,.95),(x+d,-18.45,.5),.035,'dark',c)
 for o in set(h.col(c).objects)-before:o.location.x=2*x-o.location.x;o.location.y=-36.4-o.location.y;o.rotation_euler.z+=math.pi
for x in [15,29]:
 box('Stage speaker',x,-19.1,1.03,1.2,.7,1.05,'dark',c);o=cyl('Speaker woofer',x,-19.46,.98,.33,.02,'metal',c);o.rotation_euler.x=math.pi/2
for x in [18,23]:
 cyl('Microphone stand',x,-16.3,1.32,.025,1.65,'metal',c)
 beam('Microphone boom',(x,-16.3,2.14),(x+.5,-16.3,2.35),.025,'metal',c)
 for a in [0,2.1,4.2]:beam('Mic tripod',(x,-16.3,.7),(x+.4*math.cos(a),-16.3+.4*math.sin(a),.5),.025,'metal',c)
# Acoustic wall treatment as visual equipment; no real isolation simulation.
for x in [4,6,8,10,12,16,18,20,22,24,26,28,30]:
 box('South acoustic panel',x,-20.55,2.6,1.25,.12,1.7,'acoustic' if int(x)%4 else 'wood',c)
for y in [-10,-12.5,-15,-17.5]:box('East acoustic panel',31.79,y,2.4,.12,1.3,1.8,'acoustic',c)
for x in [6,9]:
 box('Rehearsal lounge seat',x,-10.2,.6,2.4,1.0,.75,'sage',c);box('Lounge back',x,-9.74,1.06,2.4,.12,.70,'sage',c)
box('Lounge table',7.5,-12,.69,2,.85,.12,'wood',c)
for x in [6.8,8.2]:box('Lounge table leg',x,-12,.42,.08,.5,.5,'wood',c)
shelf(27.6,-8.5,5.8,c)
# Green pockets along the display lane, plus trees and planted buffers at the boundary.
for x,y in [(-26.5,.5),(8.5,.5),(-26.5,-5.5),(26.5,-5.5)]:bench(x,y,facing='s' if y>.0 else 'n')
for x,y,s in [(-30.5,-1.7,1.0),(30.5,-3.0,1.0),(-8,24.9,.65),(8,25.6,.65),(-28,25.7,.60),(28,25.7,.60),(-29,-24.9,.75),(-9,-24.9,.75),(8,-24.9,.75),(29,-24.9,.75)]:
 # Trees beside the walk, never in its continuous central 4 m carriage.
 if y==-1.7:y=1.0
 if y==-3.0:y=-5.9
 tree(x,y,s)
for i in range(55):
 x=-31.0+(i%28)*2.3;y=(26.4 if i<28 else -26.1)+.35*math.sin(i*2.4)
 if abs(x+1.5)<3 or x>33:continue
 leaf('Mixed shrub',x,y,.45,(.72,.60,.5),'leaf' if i%2 else 'leafLight','Landscape')
 for j in range(3):flower(x+.55*math.cos(j*2+i),y+.48*math.sin(j*2+i),['white','flowerPink','lavender','flowerYellow'][(i+j)%4],.65+.12*j)
# Southern art sculpture garden, low plinths and two small abstract sculptures.
for x in [-24,-14]:
 box('Outdoor sculpture plinth',x,-23.5,.34,1.3,1.3,.68,'stone','Street_Furniture')
 o=leaf('Abstract carved sculpture',x,-23.5,1.42,(.48,.45,.95),'clay' if x==-24 else 'sage','Street_Furniture');o.rotation_euler.y=.25
# Receiving yard: hand cart, timber pallet and recycling bins outside visitor circulation.
for x in [-27,-19]:
 box('Delivery pallet',x,19.0,.25,3,1.0,.25,'wood','Logistics')
 for z in [.5,.7,.9]:box('Pallet timber bundle',x,19.0,z,2.6,.72,.16,'lightwood','Logistics')
box('Handcart platform',31.6,19.2,.4,1.7,1.0,.13,'sage','Logistics')
for x in [31,32.2]:
 for y in [18.85,19.55]:
  o=cyl('Cart wheel',x,y,.24,.14,.1,'dark','Logistics');o.rotation_euler.x=math.pi/2
beam('Handcart push handle',(32.45,18.8,.43),(32.45,18.8,1.3),.055,'metal','Logistics');beam('Cart handle grip',(32.45,18.8,1.3),(32.45,19.6,1.3),.055,'metal','Logistics')
for i,x in enumerate([-31,-28.5]):
 box('Recycling station',x,-22.7,.61,1.3,.9,1.22,'sage' if i else 'bluegrey','Logistics');box('Bin lid',x,-22.7,1.25,1.4,1.0,.1,'darkgreen','Logistics')
# Lighting and signs stay on the green margins, with clear east and south exits.
for x,y in [(-6.3,.8),(1.1,.8),(-6.3,-5.8),(1.1,-5.8)]:
 cyl('Pedestrian lamp post',x,y,1.72,.05,3.44,'darkgreen','Street_Furniture');box('Lamp lantern',x,y,3.38,.38,.38,.50,'canvas','Street_Furniture');box('Lamp cap',x,y,3.65,.48,.48,.08,'darkgreen','Street_Furniture')
for x,y,t in [(34.4,1.0,'D  手作小巷'),(2.2,-24.0,'南往田园'),(-8,19.0,'后勤收货')]:
 box('Wayfinding post',x,y,.95,.09,.09,1.9,'wood','Wayfinding');h.sign(t,x,y,1.8,3.0,'Wayfinding')
# Tile the path union: horizontal surfaces never occupy the same area twice.
xs=sorted({v for r in PATH_RECTS for v in r[:2]});ys=sorted({v for r in PATH_RECTS for v in r[2:4]})
for ya,yb in zip(ys,ys[1:]):
 runs=[]
 for xa,xb in zip(xs,xs[1:]):
  xc,yc=(xa+xb)/2,(ya+yb)/2;hits=[r for r in PATH_RECTS if r[0]<xc<r[1] and r[2]<yc<r[3]]
  if hits:
   mat=hits[-1][4]
   if runs and runs[-1][2]==mat and abs(runs[-1][1]-xa)<1e-5:runs[-1]=(runs[-1][0],xb,mat)
   else:runs.append((xa,xb,mat))
 for xa,xb,mat in runs:box('Continuous walk paving',(xa+xb)/2,(ya+yb)/2,.045,xb-xa,yb-ya,.09,mat,'Paths')
# Package named collections with parents for consistent Blender and GLB visibility.
scene=bpy.context.scene;scene.name='01 Whole district';scene.unit_settings.system='METRIC'
for name,c in list(h.C.items()):
 parent=bpy.data.objects.new(name,None);c.objects.link(parent)
 for o in list(c.objects):
  if o!=parent:o.parent=parent
bpy.context.view_layer.update()
meshes=[o for o in bpy.data.objects if o.type=='MESH'];tri=0
for o in meshes:
 o.data.calc_loop_triangles();tri+=len(o.data.loop_triangles)
 for v in o.data.vertices:assert all(math.isfinite(a) for a in v.co)
 for t in o.data.loop_triangles:
  a,b,c=[o.data.vertices[i].co for i in t.vertices];assert (b-a).cross(c-a).length>1e-10,o.name
bpy.ops.object.select_all(action='SELECT');glb=R/'D-craft-workshops.glb'
bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_cameras=False,export_lights=False)
meta={'title':'D 区 · 手作工作区','plot':[75,55],'buildings':BUILDINGS,'units':'metres','sourceAxes':'Z up, north +Y','glbAxes':'Y up, north -Z','meshObjects':len(meshes),'triangles':tri,'degenerateTriangles':0,'groups':list(h.C),'sha256':hashlib.sha256(glb.read_bytes()).hexdigest(),'status':'design-review','blender':bpy.app.version_string,'portals':{'east':[37.5,-2.5],'west':[-37.5,-2.5],'north':[-1.5,27.5],'south':[-1.5,-27.5],'serviceNorth':[-35.35,27.5],'serviceSouth':[-35.35,-27.5]}}
(R/'manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
h.studio(scene);scene.cycles.samples=24;scene.render.resolution_x=1600;scene.render.resolution_y=1200
scene.camera=h.camera('Whole district camera',(86,-108,100),(0,0,0),103)
views=[(scene,'overview.png')]
roofnames=[b['id']+'_Roof' for b in BUILDINGS]
settings=[('02 Floor plan',(0,-.001,110),(0,0,0),85,roofnames,'plan.png'),('03 Woodworking',(-1,-18,29),(-18.75,10,1),35,['D01_Roof','D01_Front'],'wood-interior.png'),('04 Repair',(44,-19,29),(17,10,1),38,['D02_Roof','D02_Front'],'repair-interior.png'),('05 Art studio',(-1,14,29),(-18.75,-14.125,1),35,['D03_Roof','D03_Front'],'art-interior.png'),('06 Rehearsal',(44,14,29),(17,-14.125,1),38,['D04_Roof','D04_Front'],'music-interior.png'),('07 Makers lane',(52,-15,23),(0,-2.5,1),81,[],'makers-lane.png')]
for name,loc,target,scale,hide,file in settings:
 sc=scene.copy();sc.name=name;sc.use_fake_user=True;sc.camera=h.camera(name+' camera',loc,target,scale)
 for n in hide:sc.view_layers[0].layer_collection.children[n].exclude=True
 views.append((sc,file))
bpy.context.window.scene=scene
for scr in bpy.data.screens:
 for ar in scr.areas:
  if ar.type=='VIEW_3D':ar.spaces.active.shading.type='MATERIAL';ar.spaces.active.overlay.show_overlays=False;ar.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(R/'D-craft-workshops.blend'))
for sc,file in views:
 if os.getenv('D_RENDER') and file not in os.getenv('D_RENDER').split(','):continue
 sc.render.filepath=str(R/file);bpy.ops.render.render(write_still=True,scene=sc.name);print('RENDERED',file,flush=True)
print('COMPLETE',json.dumps(meta,ensure_ascii=False),flush=True)
