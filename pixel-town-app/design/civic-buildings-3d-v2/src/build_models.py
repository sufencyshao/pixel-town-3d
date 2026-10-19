import bpy, math, json, random, hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent.parent
random.seed(12)
M={};C={};model=[]
def init():
 global M,C,model
 bpy.ops.wm.read_factory_settings(use_empty=True);M={};C={};model=[]
 for n in ['Structure','Roof','FrontFacade','EastFacade','Interior','Landscape','UpperFloor','UpperStructure','UpperFront','UpperEast','UpperInterior','Studio']:
  c=bpy.data.collections.new(n);bpy.context.scene.collection.children.link(c);C[n]=c
 for n,h in {'plaster':'e5dec8','ivory':'eee8d8','sage':'637c6d','sageLight':'a7b6a0','roof':'697f72','oak':'ad7d50','oakLight':'c89e6a','stone':'c6c5b7','brass':'bda36a','dark':'364943','steel':'aab8b6','fabric':'b9c8be','white':'f5f0e3','blue':'819ea4','leaf':'718a54','leaf2':'93a36c','terra':'ba8267','book0':'7b8c70','book1':'b8876c','book2':'d2bd8c','book3':'638590','book4':'a8bba7','rug':'d0b58c','medicalRed':'cf3439'}.items():
  rgb=[int(h[i:i+2],16)/255 for i in (0,2,4)];rgb=[((v+.055)/1.055)**2.4 if v>.04045 else v/12.92 for v in rgb]
  m=bpy.data.materials.new(n);m.diffuse_color=(*rgb,1);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*rgb,1);bs.inputs['Roughness'].default_value=.72
  if n in ['brass','steel']:bs.inputs['Metallic'].default_value=.65;bs.inputs['Roughness'].default_value=.3
  M[n]=m
 for n,alpha in [('glass',.20),('frosted',.55)]:
  m=bpy.data.materials.new(n);m.diffuse_color=(.68,.81,.78,alpha);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=m.diffuse_color;bs.inputs['Alpha'].default_value=alpha;bs.inputs['Roughness'].default_value=.20 if n=='glass' else .6;m.surface_render_method='DITHERED';M[n]=m
 global font
 font=bpy.data.fonts.load('/System/Library/Fonts/STHeiti Medium.ttc')
def put(o,n,mat,col):
 o.name=n;o.data.materials.append(M[mat]);
 for c in list(o.users_collection):c.objects.unlink(o)
 C[col].objects.link(o)
 if col!='Studio':model.append(o)
 return o
def box(n,x,y,z,w,d,h,mat,col='Interior',bev=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=(x,y,z));o=bpy.context.object;o.dimensions=(w,d,h);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);put(o,n,mat,col)
 if bev:
  mod=o.modifiers.new('Soft edges','BEVEL');mod.width=bev;mod.segments=2;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
 return o
def cyl(n,x,y,z,r,h,mat,col='Interior',r2=None,vertices=20):
 bpy.ops.mesh.primitive_cone_add(vertices=vertices,radius1=r if r2 is None else r2,radius2=r,depth=h,location=(x,y,z));return put(bpy.context.object,n,mat,col)
def ball(n,x,y,z,r,mat,col='Interior',scale=(1,1,1)):
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=r,location=(x,y,z));o=put(bpy.context.object,n,mat,col);o.scale=scale;return o
def text(n,t,x,y,z,size,mat='ivory',col='Interior',rot=(math.pi/2,0,0)):
 cu=bpy.data.curves.new(n,'FONT');cu.body=t;cu.font=font;cu.size=size;cu.align_x='CENTER';cu.align_y='CENTER';cu.extrude=.002;cu.resolution_u=4;o=bpy.data.objects.new(n,cu);C[col].objects.link(o);o.location=(x,y,z);o.rotation_euler=rot;cu.materials.append(M[mat]);bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o=bpy.context.object;model.append(o);o.select_set(False);return o
def sign(t,x,y,z,w,col='Interior',size=.23):
 box('Sign backing',x,y,z,w,.08,.48,'sage',col,.025);text('Sign '+t,t,x,y-.048,z,size,col=col)
def chair(x,y,angle=0,mat='sageLight',col='Interior'):
 # zero rotation faces south (-Y), back at +Y
 parts=[]
 def b(n,dx,dy,z,w,d,h,m):
  o=box(n,x+dx,y+dy,z,w,d,h,m,col,.025 if n=='Chair seat' else 0);parts.append(o)
 b('Chair seat',0,0,.64,.52,.52,.09,mat)
 for dx in [-.20,.20]:
  for dy in [-.20,.20]:b('Chair leg',dx,dy,.385,.045,.045,.42,'oak')
 for dx in [-.22,.22]:b('Chair back post',dx,.22,.88,.05,.06,.65,'oak')
 b('Chair back',0,.22,1.12,.51,.06,.23,'oak')
 for o in parts:
  dx=o.location.x-x;dy=o.location.y-y;o.location.x=x+math.cos(angle)*dx-math.sin(angle)*dy;o.location.y=y+math.sin(angle)*dx+math.cos(angle)*dy;o.rotation_euler.z=angle

def desk(x,y,w=1.8,d=.8):
 box('Work desk',x,y,.98,w,d,.10,'oakLight',bev=.035)
 for dx in [-w/2+.12,w/2-.12]:
  for dy in [-d/2+.12,d/2-.12]:box('Desk leg',x+dx,y+dy,.59,.07,.07,.70,'oak')
 box('Monitor foot',x+.30,y+.12,1.06,.3,.25,.025,'dark');box('Monitor stem',x+.30,y+.18,1.25,.055,.05,.34,'dark');box('Monitor',x+.30,y+.18,1.40,.58,.055,.36,'dark',bev=.015);box('Monitor screen',x+.30,y+.145,1.40,.52,.008,.29,'blue');box('Keyboard',x+.25,y-.17,1.05,.48,.16,.025,'ivory');box('Notes',x-.45,y-.12,1.045,.30,.4,.02,'ivory')
def plant(x,y,s=1,col='Landscape'):
 cyl('Plant pot',x,y,.18+.26*s,.27*s,.52*s,'terra',col,r2=.20*s)
 for i in range(6):
  a=i*2.4;ball('Leaves',x+math.cos(a)*.25*s,y+math.sin(a)*.25*s,.78*s+(i%3)*.14,.34*s,'leaf' if i%2 else 'leaf2',col,scale=(1,.7,.6))
def shell(W,D,label,clinic=False):
 box('Foundation',0,0,-.01,W+.35,D+.35,.32,'stone','Structure',.06)
 # seamless checker or plank floor
 if clinic:
  for i in range(int(W)):
   for j in range(int(D)):box('Floor tile',-W/2+.5+i,-D/2+.5+j,.175,.99,.99,.035,'ivory' if (i+j)%5 else 'sageLight','Interior')
 else:
  for i in range(int(W*2)):box('Oak plank',-W/2+.25+i*.5,0,.175,.49,D-.12,.035,'oakLight' if i%6 else 'oak','Interior')
 # rear wall + raised frosted clinic windows
 box('Rear wall base',0,D/2-.10,1.0,W,.2,1.65,'plaster','Structure')
 box('Rear wall header',0,D/2-.10,3.38,W,.2,.65,'plaster','Structure')
 for x in [-W/2+.1,-W*.25,0,W*.25,W/2-.1]:box('Rear mullion',x,D/2-.10,2.48,.18,.23,1.32,'oak','Structure')
 box('Rear glazing',0,D/2-.10,2.46,W-.3,.03,1.30,'frosted' if clinic else 'glass','Structure')
 # west/east full-height window bays
 for x,c in [(-W/2+.1,'Structure'),(W/2-.1,'EastFacade')]:
  box('Side base',x,0,.63,.2,D,.90,'sage',c);box('Side header',x,0,3.42,.2,D,.58,'plaster',c)
  for y in [-D/2+.1,0,D/2-.1]:box('Side post',x,y,2,.24,.22,3.64,'oak',c)
  box('Side glass',x,0,2.10,.028,D-.2,2.0,'frosted' if clinic else 'glass',c)
 for x,w in [(-W/4-.62,W/2-1.25),(W/4+.62,W/2-1.25)]:
  box('Front base',x,-D/2+.1,.62,w,.22,.86,'sage','FrontFacade');box('Front glazing',x,-D/2+.1,2.06,w,.03,2.0,'glass','FrontFacade')
 for x in [-W/2+.1,-W*.25,-1.2,1.2,W*.25,W/2-.1]:box('Front post',x,-D/2+.08,1.95,.16,.24,3.6,'oak','FrontFacade')
 box('Front fascia',0,-D/2+.06,3.44,W,.25,.54,'sage','FrontFacade');text('Main name',label,0,-D/2-.08,3.45,.36,col='FrontFacade')
 box('Door lintel',0,-D/2+.06,2.91,2.4,.25,.14,'oak','FrontFacade')
 # open single leaf, offset to left so entry remains clear
 box('Open door stile',-1.13,-D/2+.65,1.45,.075,1.2,2.5,'oak','FrontFacade');box('Open door glass',-1.13,-D/2+.65,1.45,.02,1.1,2.37,'glass','FrontFacade')
 for z in [.20,2.71]:box('Door rail',-1.13,-D/2+.65,z,.075,1.2,.07,'oak','FrontFacade')
 box('Porch',0,-D/2-1.02,.02,W+1.4,2.04,.24,'stone','Landscape',.05)
 # gently sloped entry ramp
 verts=[(-1.15,-D/2-2.6,-.1),(1.15,-D/2-2.6,-.1),(-1.15,-D/2-1.6,.15),(1.15,-D/2-1.6,.15)]
 me=bpy.data.meshes.new('Ramp');me.from_pydata(verts,[],[(0,1,3,2)]);me.update();o=bpy.data.objects.new('Entrance ramp',me);C['Landscape'].objects.link(o);me.materials.append(M['stone']);model.append(o)
 for x in [-W/2+.9,W/2-.9]:plant(x,-D/2-1.0,.9)
 flat_roof(W,D,3.82 if clinic else 7.62,clinic)
 # front porch canopy distinct from cafe pergola
 box('Entry canopy',0,-D/2-.78,2.94,3.45,1.9,.14,'sage','FrontFacade',.035)
 for x in [-1.55,1.55]:box('Porch column',x,-D/2-1.52,1.58,.10,.10,2.85,'oak','FrontFacade')

def flat_roof(W,D,z,clinic):
 accent='sage' if clinic else 'terra'
 box('Flat roof slab',0,0,z,W+.6,D+.6,.24,'ivory','Roof',.035)
 box('Flat roof surface',0,0,z+.135,W+.08,D+.08,.025,'stone','Roof')
 for x in [-W/2-.12,W/2+.12]:
  box('Side parapet',x,0,z+.43,.22,D+.46,.62,'plaster','Roof')
  box('Side parapet coping',x,0,z+.76,.30,D-.06,.07,accent,'Roof')
 for y in [-D/2-.12,D/2+.12]:
  box('Front rear parapet',0,y,z+.43,W+.02,.22,.62,'plaster','Roof')
  box('Parapet coping',0,y,z+.76,W+.54,.30,.07,accent,'Roof')

def beam_between(n,a,b,width,mat,col):
 va,vb=Vector(a),Vector(b);mid=(va+vb)/2
 o=box(n,*mid,width,width,(vb-va).length,mat,col)
 o.rotation_euler=(vb-va).to_track_quat('Z','Y').to_euler();return o

def upper_library():
 level=3.8
 # Floor is built around a real stair opening, never a slab through the stairs.
 # Opening x[-9.25,-6.2], y[-2.55,3.93]. Main slab and south/north strips.
 for x,y,w,d in [(1.55,0,15.5,12),(-7.8,-4.275,3.2,3.45),(-7.8,4.965,3.2,2.07)]:
  box('Upper slab',x,y,3.87,w,d,.20,'ivory','UpperFloor')
  box('Upper oak finish',x,y,3.985,w-.02,d-.02,.025,'oakLight','UpperFloor')
 box('Upper west edge beam',-9.375,.69,3.85,.25,6.48,.26,'ivory','UpperFloor')
 # Continuous storey band and tall repeated window bays.
 for y,col in [(-5.90,'UpperFront'),(5.90,'UpperStructure')]:
  box('Upper facade sill',0,y,4.45,19,.2,.90,'plaster',col)
  box('Upper facade header',0,y,7.26,19,.24,.58,'sage',col)
  box('Upper facade glass',0,y,5.92,18.7,.028,2.03,'glass',col)
  for x in [-9.4,-6.3,-3.2,0,3.2,6.3,9.4]:box('Upper window mullion',x,y,5.9,.14,.25,2.1,'oak',col)
  box('Storey ribbon',0,y,3.89,19.25,.32,.20,'terra',col)
 for x,col in [(-9.4,'UpperStructure'),(9.4,'UpperEast')]:
  box('Upper side sill',x,0,4.45,.20,11.60,.90,'plaster',col)
  box('Upper side header',x,0,7.26,.24,11.56,.58,'sage',col)
  box('Upper side glass',x,0,5.92,.028,11.55,2.03,'glass',col)
  for y in [-3,0,3]:box('Upper side mullion',x,y,5.9,.25,.14,2.1,'oak',col)
 # Straight 22-step flight; landing connects to north aisle on the upper floor.
 for i in range(22):
  top=.1925+(i+1)*level/22;y=-2.45+(i+.5)*.29
  box('Stair tread %02d'%(i+1),-7.775,y,top-.075,2.3,.29,.15,'oakLight','Interior')
 beam_between('Stair stringer west',(-8.75,-2.40,.22),(-8.75,3.84,3.86),.16,'sage','Interior')
 beam_between('Stair stringer east',(-6.80,-2.40,.22),(-6.80,3.84,3.86),.16,'sage','Interior')
 for x in [-8.89,-6.66]:
  for i in [0,4,8,12,16,21]:
   top=.1925+(i+1)*level/22;y=-2.45+(i+.5)*.29
   box('Stair baluster',x,y,top+.48,.035,.035,.96,'brass','Interior')
  beam_between('Stair handrail',(x,-2.305,.1925+level/22+.98),(x,3.785,3.9925+.98),.055,'oak','Interior')
 # Guard around stair void; north end is intentionally open to landing.
 for y in [-2.48,-1.42,-.36,.70,1.76,2.82,3.87]:box('Void guard post',-6.18,y,4.53,.05,.05,1.06,'brass','UpperInterior')
 for z in [4.38,5.08]:box('Void guard rail',-6.18,.70,z,.065,6.40,.06,'oak','UpperInterior')
 for x in [-9.12,-8.16,-7.20,-6.22]:box('Void end post',x,-2.56,4.53,.05,.05,1.06,'brass','UpperInterior')
 for z in [4.38,5.08]:box('Void end rail',-7.67,-2.56,z,3.0,.06,.06,'oak','UpperInterior')
 sign('二 层 阅 读',-7.8,5.65,2.9,2.4,size=.22)
 # Reuse furniture dimensions at the raised floor; relocate each generated object.
 start=len(model)
 for y in [1.45,3.75]:
  for x in [-3.8,-.5]:shelf(x,y,2.1)
 for x,y in [(5.45,2.6),(5.45,-1.45),(-3.25,-4.05)]:reading_table(x,y,3.6)
 sign('安 静 阅 读',5.4,5.68,2.90,3.0,size=.25)
 for x,y in [(8.45,5.1),(8.45,-4.9),(-5.3,5.1)]:plant(x,y,.9,'Interior')
 for o in model[start:]:
  o.location.z+=level
  for c in list(o.users_collection):c.objects.unlink(o)
  C['UpperInterior'].objects.link(o)


def partition(y,start,end,door,width=1.05,height=2.75):
 a=door-width/2;b=door+width/2
 for l,r in [(start,a),(b,end)]:
  if r>l:box('Room partition',(l+r)/2,y,.18+height/2,r-l,.13,height,'plaster')
 box('Door header',door,y,2.68,width,.13,.5,'plaster')
 for x in [a,b]:box('Door frame',x,y-.015,1.32,.06,.19,2.30,'oak')
 # actual open leaf, hinges at left jamb and angled into room
 o=box('Open room door',a+.27,y+.43,1.31,.94,.07,2.18,'sageLight');o.rotation_euler.z=math.radians(60)
def exam_bed(x,y):
 box('Exam bed frame',x,y,.70,.94,2.05,.16,'steel',bev=.04);box('Exam mattress',x,y,.85,.90,2.0,.20,'fabric',bev=.07);box('Pillow',x,y+.66,1.0,.69,.43,.13,'white',bev=.055)
 for dx in [-.36,.36]:
  for dy in [-.72,.72]:box('Bed leg',x+dx,y+dy,.42,.055,.055,.43,'steel')
 box('Bed step',x+.67,y-.38,.32,.4,.62,.21,'sageLight',bev=.03)
def cabinet(x,y,w=1.3):
 box('Storage cabinet',x,y,1.35,w,.46,2.34,'ivory',bev=.025)
 for dx in [-w/4,w/4]:box('Cabinet panel',x+dx,y-.24,1.39,w/2-.025,.025,2.12,'sageLight');box('Cabinet pull',x+dx,y-.27,1.45,.025,.04,.24,'brass')
def clinic():
 shell(16,11,'溪 畔 诊 所',True)
 # Three private rooms behind shared transverse corridor.
 for x in [-2.6,2.7]:box('Room dividing wall',x,3.27,1.56,.14,4.14,2.76,'plaster')
 for start,end,door,title in [(-7.9,-2.67,-3.65,'诊 室 一'),(-2.53,2.63,1.30,'诊 室 二'),(2.77,7.9,3.7,'护理观察')]:
  partition(1.20,start,end,door);sign(title,door,1.08,2.80,1.5,size=.20)
 for x in [-6.45,-1.20]:
  exam_bed(x,3.53);desk(x+2.02,3.62,1.65,.75);chair(x+2.02,4.63);chair(x+2.02,2.59,math.pi)
  cabinet(x-.66,4.96,.8)
 exam_bed(4.60,3.8);exam_bed(6.65,3.8)
 # privacy screen between observation beds (not through bed footprints)
 for yy in [2.35,4.75]:cyl('Screen post',5.60,yy,1.1,.025,1.82,'steel');box('Screen foot',5.60,yy,.25,.42,.16,.08,'steel')
 box('Fabric screen',5.60,3.55,1.35,.035,2.40,1.18,'fabric')
 # Nurse reception; service face looks toward main entrance.
 box('Reception base',-3.3,-2.3,.77,2.65,.83,1.16,'sage',bev=.06);box('Reception top',-3.3,-2.3,1.39,2.79,.96,.10,'ivory',bev=.025)
 sign('接 待',-3.3,-2.76,.91,1.13,size=.19);box('Reception monitor',-3.4,-2.12,1.63,.53,.07,.37,'dark',bev=.01);chair(-3.4,-1.23)
 cabinet(-6.85,-.8,1.45);sign('用品柜',-6.85,-1.05,2.67,1.10,size=.18)
 # Waiting seats face the reception, clear central route stays x=-1 to +1.
 for x in [3.2,4.5,5.8]:
  chair(x,-4.15,math.pi);chair(x,-2.25,math.pi)
 box('Waiting side table',6.95,-3.15,.76,.62,.62,.08,'oakLight',bev=.04);cyl('Table pedestal',6.95,-3.15,.45,.09,.60,'oak');plant(7.12,-.35,.8,'Interior')
 sign('候 诊 区',5.0,-5.31,2.80,2.1,'FrontFacade',.20)
 # WC front west, with opaque outer wall to keep privacy.
 box('WC east wall',-5.3,-3.68,1.58,.13,3.44,2.8,'plaster');partition(-1.94,-7.9,-5.3,-6.1,width=.95)
 box('WC opaque front',-6.6,-5.32,1.85,2.62,.10,3.28,'plaster');box('WC opaque side',-7.77,-3.68,1.85,.08,3.44,3.28,'plaster')
 box('WC sign backing',-6.1,-1.845,2.7,.65,.08,.48,'sage');text('WC sign','WC',-6.1,-1.798,2.7,.20,rot=(math.pi/2,0,math.pi));cyl('Toilet bowl',-6.9,-4.5,.46,.31,.40,'white');box('Toilet tank',-6.9,-4.94,.91,.60,.25,.68,'white',bev=.025);box('WC basin',-5.70,-3.25,.98,.45,.62,.17,'white',bev=.03)
 # sink and hygienic handwash point in corridor alcove
 box('Handwash cabinet',7.25,.26,.69,.92,.46,1.0,'sageLight');box('Handwash bowl',7.25,.26,1.20,.9,.48,.09,'white');cyl('Tap',7.45,.37,1.36,.025,.29,'steel')
 # Raised white plaque and one continuous red-cross mesh on the front parapet.
 box('Medical emblem plaque',0,-5.66,4.22,1.0,.12,1.0,'white','Roof',.055)
 outline=[(-.12,.36),(.12,.36),(.12,.12),(.36,.12),(.36,-.12),(.12,-.12),(.12,-.36),(-.12,-.36),(-.12,-.12),(-.36,-.12),(-.36,.12),(-.12,.12)]
 verts=[(x,-5.74+dy,4.22+z) for dy in [0,-.045] for x,z in outline]
 faces=[tuple(range(11,-1,-1)),tuple(range(12,24))]+[(i,(i+1)%12,(i+1)%12+12,i+12) for i in range(12)]
 me=bpy.data.meshes.new('Medical red cross mesh');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new('Medical red cross',me);C['Roof'].objects.link(o);me.materials.append(M['medicalRed']);model.append(o)
 return {'id':'B03','title':'溪畔诊所','building':[16,11],'floors':1,'roof':'flat parapet','medicalEmblem':'red cross','plot':[19.5,15.5],'areas':['接待候诊','诊室一','诊室二','护理观察','用品储物','卫生间'],'residents':['许衡','余笙','苏晴'],'seats':6,'anchors':{'entrance':[0,-5.4,.2],'reception':[-3.3,-3.2,.2],'doctor1':[-4.43,4.63,.2],'doctor2':[.82,4.63,.2],'nurse':[3.7,2.0,.2]}}

def shelf(x,y,w=2.4,h=2.2,double=True):
 box('Bookcase back',x,y,.18+h/2,w,.055,h,'oak')
 for dx in [-w/2,w/2]:box('Bookcase side',x+dx,y,.18+h/2,.075,.62,h,'oak')
 for z in [.27,.77,1.27,1.77,2.27]:
  box('Bookshelf',x,y,z,w,.64,.065,'oakLight')
  if z>2:continue
  for side in ([-1,1] if double else [-1]):
   for k in range(9):
    bh=.26+random.random()*.14;bw=.12+random.random()*.08
    o=box('Book',x-w/2+.16+k*(w-.28)/9,y+side*.17,z+.035+bh/2,bw,.23,bh,'book'+str((k+int(z*10))%5));
    if k%4==0:box('Spine mark',o.location.x,o.location.y+side*.119,o.location.z-.04,bw*.75,.006,.018,'ivory')

def reading_table(x,y,w=3.5):
 box('Reading tabletop',x,y,1.01,w,1.4,.105,'oakLight',bev=.05)
 for dx in [-w/2+.22,w/2-.22]:
  for dy in [-.5,.5]:box('Reading leg',x+dx,y+dy,.58,.10,.10,.76,'oak')
 for dx in [-1.08,0,1.08]:
  chair(x+dx,y+.99);chair(x+dx,y-.99,math.pi)
  box('Open book left',x+dx-.08,y-.25,1.079,.18,.29,.02,'ivory');box('Open book right',x+dx+.11,y-.25,1.079,.18,.29,.02,'ivory')
 for dx in [-.85,.85]:
  cyl('Desk lamp foot',x+dx,y,1.10,.13,.035,'brass');cyl('Desk lamp stem',x+dx,y,1.33,.018,.45,'brass');cyl('Desk lamp shade',x+dx,y,1.55,.08,.16,'sage',r2=.23)

def library():
 shell(19,12,'溪 畔 图 书 馆')
 # Oak portal and small projecting entrance gable to distinguish civic library.
 for x in [-1.35,1.35]:box('Entry portal',x,-6.10,1.95,.22,.25,3.58,'oak','FrontFacade')
 # Rear rows; 1.5 m passage between shelf footprints.
 for y in [1.7,3.9]:
  for x in [-3.5,-.2]:shelf(x,y,2.1)
 # quiet reading eastern wing; daylight on east side
 reading_table(5.5,2.45,3.6);reading_table(5.5,-1.20,3.6)
 # Low open partitions provide zoning without obscuring overview.
 box('Reading divider',2.05,2.7,.73,.13,5.8,1.1,'sageLight')
 sign('静 心 阅 读',6.0,5.68,2.90,3.0,size=.25)
 # Front left borrowing/return desk, clear central entry route.
 box('Lending desk',-4.25,-3.9,.75,3.6,.95,1.12,'sage',bev=.065);box('Lending top',-4.25,-3.9,1.36,3.76,1.08,.10,'oakLight',bev=.035)
 sign('借 阅 / 归 还',-4.25,-4.42,.82,2.1,size=.22)
 box('Lending screen',-4.8,-3.68,1.63,.58,.07,.38,'dark',bev=.02);chair(-4.8,-2.67)
 for i in range(4):box('Return book',-3.3,-3.9,1.44+i*.045,.38,.50,.04,'book'+str(i))
 box('Book return cart',-6.83,-4.6,.74,.68,.70,.80,'oak',bev=.035)
 # Children nook front right, soft carpet and accessible low display.
 cyl('Children rug',5.55,-4.35,.206,1.35,.018,'rug',vertices=40)
 for x,y in [(4.65,-4.3),(6.4,-4.55),(5.6,-3.6)]:ball('Reading cushion',x,y,.47,.43,'sageLight' if x<6 else 'terra',scale=(1,1,.45))
 box('Low picture book shelf',7.7,-4.5,.67,.48,2.0,.94,'oak',bev=.025)
 for y in [-5.20,-4.75,-4.3,-3.85]:box('Picture book',7.43,y,.99,.055,.30,.38,'book'+str(int(abs(y)*3)%5))
 # book display, bulletin board and clock near entry, no fictitious shop.
 box('New books table',-.10,-1.72,.84,1.55,.9,.11,'oakLight',bev=.04)
 for dx in [-.6,.6]:box('Display trestle',dx-.1,-1.72,.50,.09,.64,.60,'oak')
 for i in range(4):box('New book',-.6+i*.30,-1.72,.95,.23,.33,.10,'book'+str(i))
 sign('新 书',-.1,-2.21,.70,.7,size=.17)
 for x,y in [(-5.3,5.1),(8.45,5.1),(8.45,-2.65),(-8.4,-5.15)]:plant(x,y,.95,'Interior')
 # sheltered outdoor bench on either side of the door
 for x in [-5.7,5.7]:
  box('Porch bench',x,-6.9,.62,2.1,.55,.11,'oakLight','Landscape',.04)
  for dx in [-.78,.78]:box('Bench foot',x+dx,-6.9,.36,.13,.42,.42,'sage','Landscape')
 upper_library()
 return {'id':'B02','title':'溪畔图书馆','building':[19,12],'floors':2,'floorToFloor':3.8,'roof':'flat parapet','stair':{'width':2.3,'steps':22,'riser':3.8/22,'tread':.29,'opening':[-9.25,-6.2,-2.55,3.93]},'plot':[23.75,15.5],'areas':['借还书台','八组双面书架','一层共享阅览','二层安静阅读','楼梯与楼板开口','儿童阅读角','新书展示'],'residents':['知秋','书衡'],'seats':30,'anchors':{'entrance':[0,-5.9,.2],'lending':[-4.25,-4.95,.2],'staff':[-4.8,-2.67,.2],'children':[5.55,-4.35,.2]}}

def camera(n,loc,target):
 d=bpy.data.cameras.new(n);d.lens=48;d.clip_end=300;o=bpy.data.objects.new(n,d);C['Studio'].objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
def studio(scene):
 box('Studio ground',0,0,-.35,200,200,.15,'stone','Studio')
 world=bpy.data.worlds.new('Soft daylight');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.82,.88,.96,1);world.node_tree.nodes['Background'].inputs[1].default_value=.55;scene.world=world
 for n,kind,loc,e,size in [('Sun','SUN',(-12,-17,23),2.4,None),('Softbox','AREA',(2,-9,15),2200,12),('Fill','AREA',(8,10,10),1500,9)]:
  d=bpy.data.lights.new(n,kind);d.energy=e
  if size:d.shape='DISK';d.size=size
  else:d.angle=.15
  o=bpy.data.objects.new(n,d);C['Studio'].objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,0))-o.location).to_track_quat('-Z','Y').to_euler()
 scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
 scene.render.resolution_x=1400;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'

def finish(key,meta):
 out=ROOT/key;scene=bpy.context.scene;scene.name='01 Exterior';scene.unit_settings.system='METRIC'
 # parent roots keep independent assembly names in GLB
 for name in ['Structure','Roof','FrontFacade','EastFacade','Interior','Landscape','UpperFloor','UpperStructure','UpperFront','UpperEast','UpperInterior']:
  root=bpy.data.objects.new(name,None);C[name].objects.link(root)
  for o in list(C[name].objects):
   if o!=root:o.parent=root
 bpy.ops.object.select_all(action='DESELECT')
 for name in ['Structure','Roof','FrontFacade','EastFacade','Interior','Landscape','UpperFloor','UpperStructure','UpperFront','UpperEast','UpperInterior']:
  for o in C[name].objects:o.select_set(True)
 asset=out/(meta['id']+'-'+key+'.glb');bpy.ops.export_scene.gltf(filepath=str(asset),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False)
 # source geometry audit; reimport performed in a separate process later
 invalid=[];degen=0;tri=0
 for o in model:
  if o.type!='MESH':continue
  o.data.calc_loop_triangles();tri+=len(o.data.loop_triangles)
  for v in o.data.vertices:
   if not all(math.isfinite(f) for f in v.co):invalid.append(o.name)
  for t in o.data.loop_triangles:
   a,b,c=[o.data.vertices[i].co for i in t.vertices]
   if (b-a).cross(c-a).length<1e-10:degen+=1
 meta.update({'units':'metres','sourceAxes':{'up':'+Z','front':'-Y'},'glbAxes':{'up':'+Y','front':'+Z'},'blenderVersion':bpy.app.version_string,'meshObjects':len([o for o in model if o.type=='MESH']),'triangles':tri,'nonfinite':invalid,'degenerateTriangles':degen,'asset':asset.name,'sha256':hashlib.sha256(asset.read_bytes()).hexdigest(),'status':'design-review','anchorsStatus':'proposed-not-pathfinding-tested'})
 (out/'manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
 studio(scene);scene.camera=camera('Camera Exterior',(26,-33,20),(0,-.6,2.7 if key=='library' else 1.7))
 interior=scene.copy();interior.name='02 Interior';interior.use_fake_user=True;interior.camera=camera('Camera Interior',(22,-29,28),(0,0,.8))
 for n in ['Roof','FrontFacade','EastFacade','UpperFloor','UpperStructure','UpperFront','UpperEast','UpperInterior']:interior.view_layers[0].layer_collection.children[n].exclude=True
 top=scene.copy();top.name='03 Plan';top.use_fake_user=True;top.camera=camera('Camera Plan',(0,-.01,35),(0,0,0));top.camera.data.type='ORTHO';top.camera.data.ortho_scale=26
 for n in ['Roof','FrontFacade','EastFacade','UpperFloor','UpperStructure','UpperFront','UpperEast','UpperInterior']:top.view_layers[0].layer_collection.children[n].exclude=True
 renders=[(scene,'exterior.png'),(interior,'interior.png'),(top,'plan.png')]
 if key=='library':
  up=scene.copy();up.name='04 Upper Interior';up.use_fake_user=True;up.camera=camera('Camera Upper Interior',(23,-30,29),(0,0,4.4))
  for n in ['Roof','UpperFront','UpperEast']:up.view_layers[0].layer_collection.children[n].exclude=True
  uptop=up.copy();uptop.name='05 Upper Plan';uptop.use_fake_user=True;uptop.camera=camera('Camera Upper Plan',(0,-.01,39),(0,0,3.8));uptop.camera.data.type='ORTHO';uptop.camera.data.ortho_scale=26
  renders.extend([(up,'upper-interior.png'),(uptop,'upper-plan.png')])
 bpy.context.window.scene=scene;bpy.ops.object.select_all(action='DESELECT')
 for scr in bpy.data.screens:
  for area in scr.areas:
   if area.type=='VIEW_3D':
    sp=area.spaces.active;sp.shading.type='MATERIAL';sp.overlay.show_overlays=False;sp.region_3d.view_perspective='CAMERA';sp.region_3d.view_camera_zoom=12
 bpy.ops.wm.save_as_mainfile(filepath=str(out/(meta['id']+'-'+key+'.blend')))
 for s,file in renders:
  s.render.filepath=str(out/file);bpy.ops.render.render(write_still=True,scene=s.name);print('RENDERED',key,file,flush=True)
 print('COMPLETE',key,json.dumps(meta,ensure_ascii=False),flush=True)

for key,build in [('clinic',clinic),('library',library)]:
 init();meta=build();finish(key,meta)
