import bpy,sys,math,json,hashlib,os
from pathlib import Path
from mathutils import Vector,Matrix
sys.path.insert(0,str(Path(__file__).parent));import model_helpers as h
from fixtures import label,table,chair,toilet,ramp
R=Path(__file__).resolve().parent.parent;S=R/'reference/cafe'
h.PALETTE.update({'clay':'bd8168','bluegrey':'7d9eaa','ochre':'ceab6a','gravel':'d6ccba','red':'c76763','bread':'c89156','crust':'a86f3e','icing':'f0d8c7','mint':'b7cfb4','berry':'ba6175','canvas':'f0e4ca'})
h.init();box,cyl,leaf,beam=h.box,h.cyl,h.leaf,h.beam
BUILDINGS=[
 {'id':'H01','name':'溪畔咖啡厅','center':[-26.5,11.5],'size':[18,9],'door':'s','source':'cafe','floors':1,'people':['林屿','沈知','闻豆'],'areas':['18座室内','4座露台','咖啡吧','备餐储物','卫生间']},
 {'id':'H02','name':'麦香烘焙坊','center':[1.75,11.5],'size':[21,10],'door':'s','roof':'pitch','color':'clay','floors':1,'people':['麦麦','陶麦','糖糖'],'areas':['面包与蛋糕展示','4座品尝角','烘烤间','揉面台','洗涤','卫生间']},
 {'id':'H03','name':'小锅家常食堂','center':[28.125,11.5],'size':[17,10],'door':'s','roof':'flat','color':'ochre','floors':1,'people':['陈锅'],'areas':['16座餐区','收银','备餐厨房','炉灶与排烟','洗涤','卫生间']},
 {'id':'H04','name':'籽杏杂货铺','center':[-26.5,-15],'size':[21,10],'door':'n','roof':'pitch','color':'sage','floors':1,'people':['周籽','陆杏'],'areas':['收银台','三组货架','蔬果与饮品','后仓','卫生间']},
 {'id':'H05','name':'花苔花店','center':[1.75,-15],'size':[21,10],'door':'n','roof':'lantern','color':'sage','floors':1,'people':['花音','林苔'],'areas':['鲜花与绿植展示','花艺工作台','包装台','保鲜柜','清洗','卫生间']},
 {'id':'H06','name':'银梳理发屋','center':[28.125,-15],'size':[17,10],'door':'n','roof':'flat','color':'bluegrey','floors':1,'people':['银梳','卷云'],'areas':['3个剪发位','2个洗发位','接待等候','消毒与毛巾柜','卫生间']}]

def roof(b):
 w,d=b['size'];c=b['id']+'_Roof';accent=b['color']
 if b['roof']=='lantern':
  # Raised glazed lantern sits over a real 8 x 3m opening.
  for yy in [-1,1]:box('Roof opening rim',0,yy*(d+3)/4,4.06,w+.35,(d-3)/2+.175,.16,'white',c)
  for xx in [-1,1]:box('Roof opening side',xx*(w+.35+8)/4,0,4.06,(w+.35-8)/2,3,.16,'white',c)
  for yy in [-1.5,1.5]:
   box('Greenhouse clerestory glass',0,yy,4.51,8,.028,.8,'glass',c)
   for xx in [-4,-2,0,2,4]:box('Lantern mullion',xx,yy,4.51,.07,.10,.86,'sage',c)
  for xx in [-4,4]:box('Lantern end glass',xx,0,4.51,.03,3,.8,'glass',c)
  for side in [-1,1]:
   ang=math.atan2(.65,1.65);o=box('Glazed lantern roof',0,side*.825,5.22,8.35,math.hypot(1.65,.65),.045,'glass',c);o.rotation_euler.x=-side*ang
   for xx in [-4,-2,0,2,4]:
    o=box('Lantern roof rib',xx,side*.825,5.26,.075,math.hypot(1.65,.65),.08,'sage',c);o.rotation_euler.x=-side*ang
  box('Lantern ridge',0,0,5.59,8.4,.10,.1,'sage',c)
 else:box('Closed ceiling slab',0,0,4.06,w+.35,d+.35,.16,'white',c)
 if b['roof']!='pitch':
  for yy in [-d/2,d/2]:box('Parapet',0,yy,4.38,w+.35,.18,.48,'cream',c);box('Coping',0,yy,4.66,w+.45,.28,.07,accent,c)
  for xx in [-w/2,w/2]:box('Side parapet',xx,0,4.38,.18,d-.18,.48,'cream',c);box('Side coping',xx,0,4.66,.28,d-.05,.07,accent,c)
 else:
  half=d/2+.45;rise=1.65;ang=math.atan2(rise,half);sl=math.hypot(half,rise);base=4.13
  for side in [-1,1]:
   o=box('Pitched metal roof',0,side*half/2,base+rise/2,w+.8,sl,.14,accent,c);o.rotation_euler.x=-side*ang
   for i in range(26):
    o=box('Standing seam',-w/2+i*w/25,side*half/2,base+rise/2+.085,.025,sl,.025,accent,c);o.rotation_euler.x=-side*ang
  box('Ridge cap',0,0,base+rise+.05,w+.9,.17,.14,accent,c)
  for side in [-1,1]:
   underside=base-.07/math.cos(ang);p=[(-d/2,4.10),(d/2,4.10),(d/2,underside+rise*(1-d/2/half)),(0,underside+rise),(-d/2,underside+rise*(1-d/2/half))]
   vs=[(side*w/2+dx,yy,zz) for dx in [-.08,.08] for yy,zz in p];fs=[tuple(range(4,-1,-1)),tuple(range(5,10))]+[(i,(i+1)%5,(i+1)%5+5,i+5) for i in range(5)]
   me=bpy.data.meshes.new('Closed shop gable');me.from_pydata(vs,[],fs);me.materials.append(h.M['cream']);o=bpy.data.objects.new('Closed shop gable',me);h.col(c).objects.link(o)

def shell(b):
 w,d=b['size'];bid=b['id'];accent=b['color']
 box('Shop foundation',0,0,.09,w,d,.18,'stone',bid+'_Floor');box('Floor finish',0,0,.185,w-.22,d-.22,.01,'lightwood',bid+'_Floor')
 for side in [-1,1]:
  ops=[(-w*.31,3.8,.65,3.05),(w*.31,3.8,.65,3.05),(0,2.6,0,2.9)] if side==-1 else [(-w*.30,2.6,2.7,3.35),(w*.30,2.6,2.7,3.35),(0,1.8,0,2.8)]
  h.wall_y('Shop facade',side*d/2,-w/2,w/2,ops,bid+('_Front' if side==-1 else '_Shell'),.22,3.8)
 for side in [-1,1]:h.wall_x('Side wall',side*w/2,-d/2+.11,d/2-.11,[(0,3.6,1.1,3.2)],bid+'_Shell',.22,3.8)
 c=bid+'_Front';label(bid+'  '+b['name'],0,-d/2-.18,3.55,7.6,c,accent,.34)
 # Two separate storefront awnings leave the main entry legible.
 for x in [-w*.29,w*.29]:
  for i in range(8):
   o=box('Striped shop awning',x-2.45+i*.7,-d/2-.85,2.95,.70,1.85,.075,accent if i%2==0 else 'canvas',c);o.rotation_euler.x=.16
   box('Awning valance',x-2.45+i*.7,-d/2-1.77,2.73,.70,.045,.22,accent if i%2==0 else 'canvas',c)
 ramp('Front entry ramp',0,-d/2-.9,2.7,1.8,.09,.19,bid+'_Approach')
 ramp('Rear receiving ramp',0,d/2+.9,1.9,1.8,.19,.09,bid+'_Approach')
 for xx in [-w/2+.12,w/2-.12]:box('Shop trim',xx,-d/2-.13,1.95,.18,.10,3.5,accent,c)
 roof(b)

def cabinet(x,y,w,c,mat='sage'):
 box('Work cabinet',x,y,.72,w,.8,1.08,mat,c);box('Work counter',x,y,1.30,w+.05,.85,.08,'white',c)
 for i in range(max(1,int(w/.8))):
  xx=x-w/2+(i+.5)*w/max(1,int(w/.8));box('Cabinet handle',xx,y-.42,.91,.20,.035,.025,'metal',c)
def sink(x,y,c):
 cabinet(x,y,1.7,c);box('Steel sink',x,y,1.349,1.05,.57,.025,'metal',c);cyl('Tap',x+.35,y+.20,1.51,.022,.34,'metal',c)
def bread(x,y,z,c,kind=0):
 leaf('Baked loaf',x,y,z,(.30,.18,.15),'bread',c)
 for i in [-1,0,1]:
  o=box('Loaf score',x+i*.14,y,z+.135,.025,.16,.012,'icing',c);o.rotation_euler.z=.4
 if kind:leaf('Bun topping',x,y,z+.11,(.18,.13,.06),'icing',c)
def cake(x,y,z,c):
 cyl('Cake plate',x,y,z,.28,.025,'white',c);cyl('Cake base',x,y,z+.14,.23,.25,'icing',c);cyl('Cake icing',x,y,z+.275,.24,.035,'berry',c)
 for i in range(5):
  a=i*math.tau/5;leaf('Berry garnish',x+.14*math.cos(a),y+.14*math.sin(a),z+.32,(.045,.045,.05),'red',c)
def product_shelf(x,y,w,c,kind='goods'):
 for z in [.44,1.13,1.82]:
  box('Display shelf',x,y,z,w,.95,.08,'lightwood',c)
  for i in range(int(w/.65)):
   xx=x-w/2+.35+i*.65
   if kind=='bread':bread(xx,y,z+.20,c,i%2)
   elif kind=='produce':
    box('Produce crate',xx,y,z+.20,.55,.75,.30,'wood',c)
    for j in range(4):leaf('Fresh produce',xx+(.14 if j%2 else -.14),y+(.18 if j//2 else -.18),z+.39,(.13,.13,.13),['tomato','flowerYellow','leafLight'][i%3],c)
   else:
    for j in [-1,1]:
     if i%2:cyl('Jar',xx,y+j*.22,z+.23,.14,.35,'ochre' if i%3 else 'sage',c)
     else:box('Packaged goods',xx,y+j*.22,z+.26,.43,.32,.45,['sage','clay','bluegrey'][i%3],c)
     box('Product label',xx,y+j*.39,z+.24,.22,.015,.15,'white',c)
 for xx in [x-w/2,x+w/2]:box('Shelf upright',xx,y,1.28,.075,.95,2.3,'wood',c)
def flowers(x,y,z,c,i=0,s=1):
 cyl('Flower bucket',x,y,z+.23*s,.25*s,.46*s,'clay' if i%2 else 'sage',c)
 for j in range(5):
  a=j*2.4+i;xx=x+.23*s*math.cos(a);yy=y+.23*s*math.sin(a);zz=z+(.85+.1*(j%3))*s
  beam('Cut flower stem',(x,y,z+.35*s),(xx,yy,zz),.015*s,'leaf',c)
  leaf('Florist leaves',xx,yy,zz-.23*s,(.18*s,.09*s,.12*s),'leaf',c)
  for k in range(5):
   aa=k*math.tau/5;leaf('Flower petals',xx+.09*s*math.cos(aa),yy+.09*s*math.sin(aa),zz,(.10*s,.085*s,.05*s),['white','flowerPink','flowerYellow','lavender'][(i+j)%4],c)
def booth_table(x,y,c,chairs=4):
 table('Dining table',x,y,1.8,1.1,c)
 chair(x,y+1.0,c);chair(x,y-1.0,c,math.pi)
 if chairs==4:chair(x-1.3,y,c,-math.pi/2);chair(x+1.3,y,c,math.pi/2)
 cyl('Table vase',x,y,1.10,.09,.19,'clay',c);leaf('Table flower',x,y,1.32,(.12,.12,.09),'flowerYellow',c)

for b in BUILDINGS[1:]:shell(b)
# H02 bakery: shopfront display and two tasting tables, working bakery at the rear.
c='H02_Interior';box('Bakery sales base',-4.8,-1.55,.77,7.6,1.05,1.18,'clay',c);box('Display case top',-4.8,-1.55,1.40,7.7,1.13,.10,'white',c)
for yy in [-2.07,-1.03]:box('Bakery display glazing',-4.8,yy,1.72,7.6,.025,.55,'glass',c)
box('Display glass lid',-4.8,-1.55,2.0,7.65,1.08,.025,'glass',c)
for i in range(10):
 xx=-8.1+i*.72
 if i<6:bread(xx,-1.6,1.59,c,i%2)
 else:cake(xx,-1.55,1.46,c)
box('Bakery till',-.8,-1.3,1.65,.6,.13,.4,'darkgreen',c)
for x in [4.0,8.0]:booth_table(x,-1.8,c,2)
h.wall_y('Bakery workroom partition',1.5,-10.39,10.39,[(0,2.2,0,2.8),(8.65,1.3,0,2.45)],c,.14,3)
label('现烤面包 / 手作甜品',-4.8,-2.13,.85,4.2,c,'darkgreen',.22)
product_shelf(-8.8,-3.8,2.5,c,'bread')
box('Twin deck oven',-8.1,3.65,1.15,2.3,1.8,1.94,'metal',c)
for z in [.74,1.47]:
 box('Oven glass door',-8.1,2.73,z,1.95,.04,.48,'darkgreen',c);box('Oven handle',-8.1,2.67,z+.14,1.45,.07,.06,'metal',c)
 for xx in [-8.6,-7.7]:bread(xx,2.70,z,c)
table('Dough preparation table',-3.8,3.3,4.4,1.45,c,1.06)
for xx in [-4.9,-4.25,-3.6]:leaf('Proofing dough',xx,3.3,1.22,(.22,.18,.12),'icing',c)
o=cyl('Rolling pin',-2.5,3.3,1.20,.055,.65,'wood',c);o.rotation_euler.y=math.pi/2
cabinet(3.6,4.25,3.7,c);box('Mixer base',3.0,4.15,1.44,.55,.55,.16,'white',c);cyl('Mixing bowl',3,4.08,1.65,.23,.32,'metal',c);box('Mixer motor',3,4.35,1.95,.45,.28,.55,'sage',c)
sink(5.2,2.6,c);toilet(8.65,3.5,c)
# H03 restaurant: 16 seats, rear kitchen with distinct food prep/wash positions.
c='H03_Interior'
for xx in [-4.9,4.9]:
 for yy in [-2.85,-.05]:booth_table(xx,yy,c)
h.wall_y('Kitchen partition',1.45,-8.39,8.39,[(0,2.2,0,2.8),(6.65,1.3,0,2.45)],c,.14,3.1)
label('出餐 / 厨房',0,1.36,2.95,2.5,c,'darkgreen',.22)
box('Restaurant checkout',-7.25,-3.9,.74,1.2,.70,1.08,'ochre',c);box('Checkout terminal',-7.25,-3.9,1.47,.44,.08,.32,'darkgreen',c)
cabinet(-4.7,4.25,5.5,c,'metal')
for xx in [-6.5,-5.3,-4.1]:
 cyl('Stove ring',xx,4.25,1.38,.22,.05,'darkgreen',c);cyl('Cooking pot',xx,4.25,1.58,.25,.36,'metal',c)
box('Kitchen extraction hood',-4.8,4.2,2.90,5.6,.98,.55,'metal',c)
box('Hood chimney',-4.8,4.3,3.63,.7,.7,1.0,'metal',c);box('Roof exhaust chimney',-4.8,4.3,4.72,.7,.7,1.36,'metal','H03_Roof');box('Exhaust cap',-4.8,4.3,5.45,1.0,1,.12,'sage','H03_Roof')
table('Food prep island',-4.8,2.30,4.4,.9,c,1.06);box('Chopping board',-4.8,2.3,1.14,1.1,.55,.03,'wood',c)
for xx in [-5.1,-4.8,-4.5]:leaf('Prepared vegetables',xx,2.3,1.23,(.11,.15,.08),'leafLight',c)
sink(3.2,4.25,c);box('Kitchen fridge',3.0,2.3,1.18,1.1,.75,2.0,'white',c);toilet(6.65,3.5,c)
# H04 grocer: three low gondolas with clear main centre aisle, checkout and rear store.
c='H04_Interior'
for x,y,kind in [(-5.8,-1.65,'produce'),(5.8,-1.65,'goods'),(-5.8,1.0,'goods')]:product_shelf(x,y,5.1,c,kind)
box('Grocer checkout',-4.6,-4.1,.76,3.4,.75,1.16,'sage',c);box('Till',-4.3,-4.1,1.49,.54,.1,.34,'darkgreen',c)
for i in range(4):
 box('Shopping basket',-8.8,-3.7,.35+i*.10,.6,.45,.25,'wood',c)
box('Drinks refrigerator',8.9,-.4,1.42,1.2,2.5,2.45,'white',c);box('Drinks fridge glass',8.27,-.4,1.53,.025,2.25,1.95,'glass',c)
for yy in [-1.15,-.4,.35]:
 for z in [.65,1.3,1.95]:cyl('Drink bottle',8.6,yy,z,.13,.44,'bluegrey',c)
h.wall_y('Store room partition',2.25,-10.39,10.39,[(0,2.2,0,2.8),(8.65,1.3,0,2.45)],c,.14,3)
for x in [-7,-3.6,3.4]:
 for z in [.44,1.25]:
  box('Backstock shelf',x,4.2,z,2.5,.95,.08,'wood',c)
  for dx in [-.75,0,.75]:box('Supply carton',x+dx,4.2,z+.3,.62,.7,.5,'ochre',c)
toilet(8.65,3.5,c)
# H05 florist: bouquets, island arrangement worktable and a genuine roof lantern.
c='H05_Interior'
for xx in [-8.9,-6.8,-4.7]:
 for yy in [-3.8,-1.7]:flowers(xx,yy,.19,c,int(abs(xx+yy)))
for xx in [-8.5,-6.1,-3.7]:
 box('Plant display riser',xx,1.4,.38,1.9,1.4,.4,'lightwood',c)
 h.Z=.58
 for dx in [-.5,.5]:h.plant(xx+dx,1.4,1.1,c)
 h.Z=0
table('Flower arranging table',4.8,-.9,5.5,1.9,c,1.05)
for i in range(4):flowers(3.1+i*1.1,-.9,1.12,c,i,.55)
box('Wrapping paper rack',8.9,-2.9,1.15,.8,.8,1.92,'wood',c)
for i in range(4):
 o=cyl('Wrapping roll',8.9,-3.15+i*.17,1.95,.08,.9,'canvas' if i%2 else 'flowerPink',c);o.rotation_euler.y=math.pi/2
h.wall_y('Florist workroom partition',2.25,-10.39,10.39,[(0,2.2,0,2.8),(8.65,1.3,0,2.45)],c,.14,3)
sink(-3.0,4.25,c);cabinet(3.4,4.25,3.6,c)
box('Flower cooler',-7.8,4.05,1.42,2.6,1.25,2.45,'sage',c);box('Cooler glass',-7.8,3.40,1.54,2.3,.025,2.0,'glass',c)
for x in [-8.5,-7.8,-7.1]:flowers(x,4.05,.35,c,2,.75)
toilet(8.65,3.5,c)
# H06 salon: three chairs and mirrors, two wash stations, waiting and utility rooms.
c='H06_Interior'
for i,xx in enumerate([-5.7,0,4.3]):
 box('Mirror oak surround',xx,1.95,2.08,1.9,.12,1.8,'wood',c);box('Salon mirror',xx,1.87,2.08,1.68,.035,1.6,'metal',c)
 box('Styling shelf',xx,1.52,1.18,2.0,.58,.10,'lightwood',c)
 cyl('Salon chair base',xx,.1,.27,.48,.18,'metal',c);cyl('Hydraulic seat stem',xx,.1,.55,.09,.50,'metal',c)
 box('Salon chair cushion',xx,.1,.84,.74,.70,.16,'sage',c);box('Salon chair back',xx,-.23,1.22,.74,.14,.72,'sage',c)
 for dx in [-.42,.42]:box('Salon armrest',xx+dx,.1,1.03,.12,.7,.12,'wood',c)
 box('Salon footrest',xx,.76,.48,.55,.25,.07,'metal',c)
 for dx in [-.55,.55]:cyl('Styling bottle',xx+dx,1.5,1.40,.065,.32,'white' if dx<0 else 'clay',c)
h.wall_y('Salon utility partition',2.5,-8.39,8.39,[(2.5,1.6,0,2.6),(6.65,1.3,0,2.45)],c,.14,3)
# Mirrors mounted against the solid partition, not floating in the aisle.
for xx in [-5.7,0,4.3]:box('Mirror partition support',xx,2.20,2.08,1.9,.42,1.8,'cream',c)
for xx in [-5.9,-2.1]:
 box('Wash recliner',xx,3.6,.70,.82,1.15,.70,'bluegrey',c);o=box('Recliner back',xx,4.0,1.12,.82,.18,.95,'bluegrey',c);o.rotation_euler.x=-.32
 cyl('Shampoo basin pedestal',xx,4.35,.7,.26,.9,'white',c);cyl('Shampoo basin',xx,4.35,1.18,.42,.16,'white',c);cyl('Basin inset',xx,4.35,1.27,.28,.018,'darkgreen',c)
box('Salon reception counter',-5.9,-3.9,.77,3.5,.75,1.18,'bluegrey',c)
box('Booking terminal',-5.8,-3.9,1.52,.5,.08,.33,'darkgreen',c)
box('Waiting sofa',4.8,-3.9,.64,4,.85,.8,'fabric',c);box('Waiting sofa back',4.8,-4.28,1.1,4,.13,.65,'sage',c)
for x in [3.9,5.4]:box('Waiting cushion',x,-3.8,.83,1.3,.6,.15,'sage',c)
toilet(6.65,3.5,c)
box('Towel cabinet',3.7,4.25,1.36,1.2,.75,2.35,'white',c)
for z in [.75,1.1,1.45,1.8]:box('Folded towels',3.7,3.84,z,.92,.16,.24,'fabric',c)
# Classic barber pole beside the front entrance, contained within shop's own canopy zone.
for i in range(12):cyl('Barber pole band',-2,-5.22,1.1+i*.11,.13,.11,['white','red','bluegrey'][i%3],'H06_Front')
for z in [1.0,2.43]:leaf('Barber pole cap',-2,-5.22,z,(.17,.17,.13),'metal','H06_Front')
# Place new shops at original plan centres. Fronts of south row face north.
for b in BUILDINGS[1:]:
 x,y=b['center'];angle=math.pi if b['door']=='n' else 0
 for name,c in list(h.C.items()):
  if name.startswith(b['id']+'_'):
   for o in c.objects:
    a,bb=o.location.x,o.location.y;o.location.x=x+math.cos(angle)*a-math.sin(angle)*bb;o.location.y=y+math.sin(angle)*a+math.cos(angle)*bb;o.rotation_euler.z+=angle
# Append the original cafe. Resolve the entire hierarchy before detaching any parent.
f=S/'H01-Cafe.blend';maps={'01 Building':'Shell','02 Roof':'Roof','03 FrontFacade':'Front','04 EastFacade':'East','05 Furniture':'Interior','06 Terrace':'Terrace','07 Planters':'Planters'}
with bpy.data.libraries.load(str(f),link=False) as (src,dst):dst.collections=list(maps)
cols=list(dst.collections)
for c in cols:bpy.context.scene.collection.children.link(c)
bpy.context.view_layer.update();records=[]
for c in cols:
 for o in c.objects:
  if o.type=='MESH':records.append((o,o.matrix_world.copy(),c,maps[c.name]))
source_tri=sum(len(o.data.loop_triangles) for o,_,_,_ in records) # recalc below
source_tri=0;source_snapshot=[]
for o,world,c,part in records:
 o.data.calc_loop_triangles();source_tri+=len(o.data.loop_triangles)
 source_snapshot.append({'name':o.name,'triangles':len(o.data.loop_triangles),'matrix':[list(row) for row in world]})
 o.parent=None;o.matrix_world=world;c.objects.unlink(o);h.col('H01_'+part).objects.link(o);o.name='H01__'+o.name
 o.location.x-=26.5;o.location.y+=11.5
# Open only the assembled copy's existing rear door about its hinge, without changing its mesh.
bpy.context.view_layer.update()
rear=next(o for o,_,_,_ in records if o.name=='H01__RearServiceDoor');pivot=Vector((-26.5+4.62,11.5+4.41,0));rear.matrix_world=Matrix.Translation(pivot)@Matrix.Rotation(math.pi/2,4,'Z')@Matrix.Translation(-pivot)@rear.matrix_world
prep=bpy.data.objects['H01__ServicePrepTable']
prep.matrix_world=Matrix.Translation(Vector((-20.27,14.7,0)))@Matrix.Rotation(math.pi/2,4,'Z')@Matrix.Translation(Vector((21,-15.3,0)))@prep.matrix_world
for name in ['Fridge','FridgeHandle']:bpy.data.objects['H01__'+name].location.x-=.12
for c in cols:
 for o in list(c.objects):bpy.data.objects.remove(o,do_unlink=True)
 bpy.data.collections.remove(c)
ramp('Cafe rear connector',-21.35,16.9,1.8,1.8,.155,.09,'H01_Approach')
source={'file':'reference/cafe/H01-Cafe.blend','blendSha256':hashlib.sha256(f.read_bytes()).hexdigest(),'glbSha256':hashlib.sha256((S/'H01-cafe.glb').read_bytes()).hexdigest(),'meshObjects':len(records),'triangles':source_tri,'scale':1,'translation':[-26.5,11.5,0],'changedCopyOnly':['Rear service door opened 90 degrees about its hinge','Added external rear receiving ramp; original architecture, terrace and textures retained','Prep table rotated and moved against east partition; fridge and handle shifted 0.12m west to clear the receiving aisle']}
assert len(records)==790 and source_tri==27670
# Shared block: east-west pedestrian street, receiving lanes and four boundary connections.
box('H site',0,0,-.18,85,55,.36,'grass','Ground')
PATHS=[[-42.5,-3.75,42.5,.75],[-13,-25,-10.5,23.5],[14,-25,17,23.5],[-40.5,20.5,40.5,23.5],[-40.5,-25,40.5,-22],[-40.5,-25,-38,23.5],[38,-25,40.5,23.5],[-1.5,20.5,1.5,27.5],[-1.5,-27.5,1.5,-22]]
for b in BUILDINGS:
 x,y=b['center'];w,d=b['size'];north=b['door']=='n';front=y+(d/2 if north else -d/2);rear_y=y+(-d/2 if north else d/2)
 b['entry']=[x,front];b['rear']=[x if b['id']!='H01' else x+5.15,rear_y];b['rotation']=math.pi if north else 0
 if b['id']=='H01':PATHS.append([x-1.5,.75,x+1.5,4.52])
 elif north:PATHS.append([x-1.5,front,x+1.5,-3.75])
 else:PATHS.append([x-1.5,.75,x+1.5,front])
 rx=b['rear'][0]
 PATHS.append([rx-1.2,-22 if north else rear_y,rx+1.2,rear_y if north else 23.5])
 # Recessed customer aprons stay out of the through street.
 if b['id']!='H01':PATHS.append([x-w/2-.15,front if north else front-3.2,x+w/2+.15,front+3.2 if north else front])
# Cafe patio access follows existing terrace edge without duplicate coplanar paving.
PATHS += [[-37.85,2.0,-15.15,4.52],[-28,0.75,-25,2.1]]
xs=sorted({r[i] for r in PATHS for i in [0,2]});ys=sorted({r[i] for r in PATHS for i in [1,3]});TILES=[]
for ya,yb in zip(ys,ys[1:]):
 runs=[]
 for xa,xb in zip(xs,xs[1:]):
  xx,yy=(xa+xb)/2,(ya+yb)/2
  if any(a<xx<c and bb<yy<d for a,bb,c,d in PATHS):
   if runs and abs(runs[-1][1]-xa)<1e-6:runs[-1]=(runs[-1][0],xb)
   else:runs.append((xa,xb))
 for xa,xb in runs:box('Continuous street paving',(xa+xb)/2,(ya+yb)/2,.045,xb-xa,yb-ya,.09,'gravel','Paths');TILES.append([xa,ya,xb,yb])
# Low planted pockets rather than rows of raised vegetable-like beds.
def tree(x,y,s=1):
 cyl('Street tree trunk',x,y,1.5*s,.16*s,3*s,'wood','Landscape')
 for dx,dy,z in [(0,0,3.6),(-.75,.1,3.05),(.7,.2,3.2),(0,-.7,3.1)]:leaf('Street tree canopy',x+dx*s,y+dy*s,z*s,(1.2*s,1.15*s,1.2*s),'leaf' if dx else 'leafLight','Landscape')
def shrub(x,y,i):
 leaf('Soft shrub',x,y,.44,(.72,.62,.48),'leafLight','Landscape')
 for j in range(3):
  a=i+j*2.4;xx=x+.6*math.cos(a);yy=y+.5*math.sin(a)
  cyl('Flower stem',xx,yy,.30,.012,.6,'leaf','Landscape')
  for k in range(5):
   aa=k*math.tau/5;leaf('Border flower',xx+.08*math.cos(aa),yy+.08*math.sin(aa),.63,(.085,.07,.045),['white','flowerPink','lavender','flowerYellow'][(i+j)%4],'Landscape')
def bench(x,y,face='s'):
 box('Street bench',x,y,.53,2.7,.65,.14,'wood','Street_Furniture');box('Bench back',x,y+(.28 if face=='s' else -.28),.90,2.7,.10,.60,'sage','Street_Furniture')
 for dx in [-.95,.95]:box('Bench foot',x+dx,y,.27,.12,.52,.48,'darkgreen','Street_Furniture')
for x,y,s in [(-35,18.8,.65),(-18,18.8,.65),(-6.5,18.8,.65),(10.5,18.8,.65),(22,18.8,.65),(35,18.8,.65),(-33,-6,.7),(-19,-6,.7),(-5.5,-6,.7),(9,-6,.7),(22,-6,.7),(35,-6,.7),(-6.2,1.9,.6),(10.5,1.9,.6),(21.5,1.9,.6),(35,1.9,.6)]:tree(x,y,s)
for i,(x,y) in enumerate([(-35,1),(-18,1),(-31,-5.4),(-21,-5.4),(-4,-5.4),(7.5,-5.4),(23.5,-5.4),(33.5,-5.4),(-9,2.1),(12,2.1),(19,2.1),(37,2.1)]):shrub(x,y,i)
for i in range(32):
 x=-38+i*2.45
 if abs(x)<3:continue
 shrub(x,25.6+.25*math.sin(i*1.8),i)
for x,y,face in [(-32,1,'s'),(-20,1,'s'),(-4,-5.7,'n'),(8,-5.7,'n'),(23.5,-5.7,'n'),(33.5,-5.7,'n')]:bench(x,y,face)
# Outdoor shop displays remain on the aprons; entrance centres remain clear.
for x in [-32.5,-21.0]:
 box('Outdoor produce stand',x,-8.4,.70,2.5,.8,1.15,'wood','H04_Display')
 for j in range(6):leaf('Outdoor produce',x-1+j*.4,-8.4,1.36,(.17,.17,.15),'tomato' if j%2 else 'flowerYellow','H04_Display')
for i,x in enumerate([-6.8,-4.8,7.5,9.5]):flowers(x,-8.3,.09,'H05_Display',i)
for x in [24,32]:
 cyl('Restaurant terrace table',x,4.4,.93,.65,.1,'wood','H03_Display');cyl('Terrace table stem',x,4.4,.52,.08,.8,'metal','H03_Display')
 for xx in [x-.95,x+.95]:box('Terrace stool',xx,4.4,.49,.48,.48,.8,'sage','H03_Display')
# Bakery menu and florist sign to create a readable shopfront rhythm.
for bid,x,y,t in [('H02',-1.5,4.1,'今日出炉'),('H03',24.5,5.1,'今日家常'),('H05',5,-8.4,'鲜花 / 花艺')]:
 for dx in [-.38,.38]:box('Menu board leg',x+dx,y,.72,.06,.08,1.25,'wood',bid+'_Display')
 label(t,x,y,1.25,1.4,bid+'_Display','darkgreen',.18)
# Low-key rear logistics: delivery shelves and sorted waste away from storefronts.
for bid,x,y in [('H02',-5.5,18.8),('H03',22,18.8),('H04',-32,-21.2),('H05',8,-21.2),('H06',33,-21.2)]:
 box('Receiving pallet',x,y,.22,2.4,.85,.22,'wood','Logistics')
 for dx in [-.65,.65]:box('Delivery crate',x+dx,y,.62,1.0,.70,.65,'ochre' if bid!='H05' else 'sage','Logistics')
for x in [-35,-33.4]:box('Sorted waste bin',x,-21.2,.66,1.1,.8,1.2,'sage' if x==-35 else 'bluegrey','Logistics');box('Bin lid',x,-21.2,1.29,1.16,.85,.08,'darkgreen','Logistics')
for x,y in [(-14.5,-5.0),(12.5,-5.0),(-14.5,1.8),(17.8,1.8)]:
 cyl('Street lantern post',x,y,1.82,.05,3.55,'darkgreen','Street_Furniture');box('Street lantern',x,y,3.6,.38,.38,.48,'canvas','Street_Furniture')
for x,y,t in [(4,25.8,'H  日常商业街'),(37,-5.7,'东往旅店'),(-37,-5.7,'西往田园')]:
 box('Wayfinding post',x,y,1,.08,.08,2,'wood','Wayfinding');label(t,x,y,1.9,3.5,'Wayfinding','darkgreen',.24)
# Export all groups, keeping studio and cameras separate.
scene=bpy.context.scene;scene.name='01 H whole street';scene.unit_settings.system='METRIC'
bpy.context.view_layer.update()
for n,c in list(h.C.items()):
 root=bpy.data.objects.new(n,None);c.objects.link(root)
 for o in list(c.objects):
  if o!=root:
   world=o.matrix_world.copy();o.parent=root;o.matrix_world=world
bpy.context.view_layer.update();meshes=[o for o in scene.objects if o.type=='MESH'];tri=0
for o in meshes:o.data.calc_loop_triangles();tri+=len(o.data.loop_triangles)
for im in bpy.data.images:
 if im.has_data and not im.packed_file:im.pack()
bpy.ops.object.select_all(action='SELECT');glb=R/'H-daily-shops.glb';bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_cameras=False,export_lights=False)
meta={'title':'H 区 · 日常商业街','date':'2026-10-15','plot':[85,55],'worldPlanRect':[450,720,340,220],'buildings':BUILDINGS,'sourceCafe':source,'groups':list(h.C),'paths':TILES,'pathRectangles':PATHS,'meshObjects':len(meshes),'triangles':tri,'sha256':hashlib.sha256(glb.read_bytes()).hexdigest(),'units':'metres','sourceAxes':'Z up, north +Y','glbAxes':'Y up, north -Z','blender':bpy.app.version_string,'status':'design-review','portals':{'north':[0,27.5],'south':[0,-27.5],'east':[42.5,-1.5],'west':[-42.5,-1.5]}}
(R/'manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2));(R/'reference/cafe-import-snapshot.json').write_text(json.dumps(source_snapshot,ensure_ascii=False,indent=2))
h.studio(scene);scene.cycles.samples=20;scene.render.resolution_x=1600;scene.render.resolution_y=1200;bpy.data.objects['Studio ground'].location.z=-.65
scene.camera=h.camera('H full street camera',(91,-112,100),(0,0,0),110);views=[(scene,'overview.png')]
settings=[('02 Plan',(0,-.001,110),(0,0,0),90,None,'plan.png')]
for i,b in enumerate(BUILDINGS):
 x,y=b['center'];north=b['door']=='n';settings.append((f'{i+3:02d} '+b['id'],(x+22,y+(26 if north else -26),28),(x,y,1),29 if b['id'] in ['H01','H03','H06'] else 31,b['id'],b['id']+'-interior.png'))
settings.append(('09 Shopfront lane',(99,43,42.6),(1,-1,1.4),86,'lane','street.png'))
for name,loc,target,scale,selected,file in settings:
 sc=scene.copy();sc.name=name;sc.use_fake_user=True;sc.camera=h.camera(name+' camera',loc,target,scale)
 for child in sc.view_layers[0].layer_collection.children:
  n=child.name
  if n=='Studio':continue
  if selected=='lane':hide=False
  elif selected:
   hide=(n.startswith('H0') and not n.startswith(selected+'_')) or (not n.startswith('H0') and n not in ['Ground','Paths'])
   if n.startswith(selected+'_') and n.split('_',1)[1] in ['Roof','Front','East']:hide=True
  else:hide=n.endswith('_Roof')
  child.exclude=hide
 views.append((sc,file))
bpy.context.window.scene=scene
for scr in bpy.data.screens:
 for ar in scr.areas:
  if ar.type=='VIEW_3D':ar.spaces.active.shading.type='MATERIAL';ar.spaces.active.overlay.show_overlays=False;ar.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(R/'H-daily-shops.blend'))
for sc,file in views:
 if os.getenv('H_RENDER') and file not in os.getenv('H_RENDER').split(','):continue
 sc.render.filepath=str(R/file);bpy.ops.render.render(write_still=True,scene=sc.name);print('RENDERED',file,flush=True)
print('COMPLETE',len(meshes),tri,flush=True)
