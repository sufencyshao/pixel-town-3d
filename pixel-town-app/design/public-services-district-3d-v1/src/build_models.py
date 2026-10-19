import bpy,sys,math,json,hashlib,os
from pathlib import Path
from mathutils import Vector, Matrix
sys.path.insert(0,str(Path(__file__).parent));import model_helpers as h
R=Path(__file__).resolve().parent.parent;S=R.parent/'civic-buildings-3d-v2'
if (R/'reference/civic-buildings-3d-v2').exists():S=R/'reference/civic-buildings-3d-v2'
h.PALETTE.update({'clay':'b78068','bluegrey':'809ca9','ochre':'ccad6f','gravel':'d6ccba','court':'b7baa0','line':'eee8d5','red':'ce4549'})
h.init();box,cyl,leaf,beam=h.box,h.cyl,h.leaf,h.beam
BUILDINGS=[
 {'id':'B01','name':'溪畔小学','center':[-26.125,15.25],'size':[23,12],'floors':1,'door':'s','roof':'pitch','color':'ochre','areas':['两间12座教室','教师工作位','卫生间','18 × 8 m小操场'],'people':['温书']},
 {'id':'B02','name':'溪畔图书馆','center':[1.875,13.5],'size':[19,12],'floors':2,'door':'s','source':'library','areas':['借还书','儿童阅读','30座阅览','22级楼梯'],'people':['知秋','书衡']},
 {'id':'B03','name':'溪畔诊所','center':[28.25,13.5],'size':[16,11],'floors':1,'door':'s','source':'clinic','areas':['接待候诊','两间诊室','护理观察','卫生间','东侧辅助门'],'people':['许衡','余笙','苏晴']},
 {'id':'B04','name':'邻里社区中心','center':[-26.125,-17],'size':[23,13],'floors':1,'door':'n','roof':'flat','color':'clay','areas':['共享活动厅','协商长桌','儿童角','咨询室','茶水与卫生间'],'people':['阿澈','小满','夏芽']},
 {'id':'B05','name':'小镇邮局','center':[.5,-17],'size':[19,13],'floors':1,'door':'n','roof':'flat','color':'sage','areas':['寄取件窗口','自助包装','信件分拣','包裹架','后侧收发','卫生间'],'people':['小路','章铃']},
 {'id':'B06','name':'社区警务站','center':[27.625,-17],'size':[19,13],'floors':1,'door':'n','roof':'flat','color':'bluegrey','areas':['接待等候','值班工作位','社区调解室','装备柜','卫生间'],'people':['程正','许巡']}]
SOURCES={};CHANGES=[]

def label(t,x,y,z,w,c,color='darkgreen',size=.32):
 box('Plaque '+t,x,y,z,w,.09,.5,color,c);h.text('Label '+t,t,x,y-.051,z,size,'white',c)
def table(n,x,y,w,d,c,z=.94):
 box(n,x,y,z,w,d,.12,'lightwood',c)
 for dx in [-w/2+.16,w/2-.16]:
  for dy in [-d/2+.16,d/2-.16]:box(n+' leg',x+dx,y+dy,(z-.06+.19)/2,.08,.08,z-.06-.19,'wood',c)
def chair(x,y,c,rot=0,small=False):
 before=set(h.col(c).objects);s=.82 if small else 1
 box('Seat',x,y,.18+.40*s,.54*s,.52*s,.10,'sage',c)
 for dx in [-.2,.2]:
  for dy in [-.2,.2]:box('Chair leg',x+dx*s,y+dy*s,.18+.2*s,.05,.05,.4*s,'wood',c)
 box('Chair back',x,y+.23*s,.18+.72*s,.52*s,.07,.55*s,'wood',c)
 for o in set(h.col(c).objects)-before:
  a,b=o.location.x-x,o.location.y-y;o.location.x=x+math.cos(rot)*a-math.sin(rot)*b;o.location.y=y+math.sin(rot)*a+math.cos(rot)*b;o.rotation_euler.z+=rot

def desk(x,y,c,w=2):
 table('Staff desk',x,y,w,.85,c)
 box('Monitor',x+.3,y+.1,1.24,.62,.065,.38,'darkgreen',c);box('Screen',x+.3,y+.061,1.24,.55,.012,.30,'bluegrey',c);box('Keyboard',x+.3,y-.23,1.02,.5,.17,.025,'white',c)
 chair(x,y+.95,c);chair(x,y-.95,c,math.pi)
def shelves(x,y,w,c,parcels=False):
 for z in [.45,1.15,1.85]:
  box('Storage shelf',x,y,z,w,.9,.08,'wood',c)
  for i in range(int(w/.7)):
   xx=x-w/2+.4+i*.7
   if parcels:
    box('Parcel',xx,y,z+.26,.54,.58,.44,'ochre' if i%2 else 'lightwood',c);box('Parcel label',xx,y-.296,z+.27,.23,.012,.13,'white',c)
   else:
    for j in range(4):box('Stored book',xx-.2+j*.12,y,z+.22,.085,.4,.35,['sage','clay','ochre','bluegrey'][j],c)
 for xx in [x-w/2,x+w/2]:box('Shelf upright',xx,y,1.25,.07,.9,2.25,'darkgreen',c)
def toilet(x,y,c):
 # 3.0 x 2.8 m enclosure, true south door, no shower in public WCs.
 h.wall_y('WC partition',y-1.4,x-1.5,x+1.5,[(x,1.1,0,2.35)],c,.13,2.8)
 for xx in [x-1.5,x+1.5]:h.wall_x('WC side',xx,y-1.4,y+1.4,[],c,.13,2.8)
 cyl('WC bowl',x-.7,y+.4,.47,.28,.48,'white',c);box('WC tank',x-.7,y+.93,.87,.58,.26,.68,'white',c)
 box('Wash basin cabinet',x+.75,y+.85,.66,.7,.55,.95,'sage',c);box('Basin',x+.75,y+.85,1.17,.74,.6,.10,'white',c);box('Mirror',x+.75,y+1.18,1.8,.68,.04,.82,'metal',c)
 label('卫生间',x,y-1.49,2.65,1.3,c,size=.19)
def ramp(n,x,y,w,d,z0,z1,c,axis='y'):
 vs=[(-w/2,-d/2,z0),(w/2,-d/2,z0),(-w/2,d/2,z1),(w/2,d/2,z1),(-w/2,-d/2,.005),(w/2,-d/2,.005),(-w/2,d/2,.005),(w/2,d/2,.005)]
 vs=[(x+(b if axis=='x' else a),y+(a if axis=='x' else b),z) for a,b,z in vs]
 fs=[(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)]
 me=bpy.data.meshes.new(n);me.from_pydata(vs,[],fs);me.materials.append(h.M['stone']);me.update();o=bpy.data.objects.new(n,me);h.col(c).objects.link(o);return o

def new_shell(b):
 bid=b['id'];w,d=b['size'];accent=b['color']
 box(bid+' foundation',0,0,.09,w,d,.18,'stone',bid+'_Floor');box('Floor finish',0,0,.185,w-.22,d-.22,.01,'lightwood',bid+'_Floor')
 for side in [-1,1]:
  ops=[(-w*.32,3.2,1.0,3.2),(w*.32,3.2,1.0,3.2)]
  if side==1 and bid=='B01':ops=[(-w*.32,3.2,3.0,3.55),(w*.32,3.2,3.0,3.55)]
  if side==-1 or bid=='B05':ops.append((0,2.6 if side==-1 else 2.8,0,3))
  elif bid!='B01':ops.append((0,2.8,1.2,3.2))
  h.wall_y('Facade',side*d/2,-w/2,w/2,ops,bid+('_Front' if side==-1 else '_Shell'),.22,3.8)
 for side in [-1,1]:h.wall_x('Side wall',side*w/2,-d/2+.11,d/2-.11,[(0,3.8,1.1,3.2)],bid+'_Shell',.22,3.8)
 c=bid+'_Front';label(bid+'  '+b['name'],0,-d/2-.17,3.57,7.4,c,accent,.34)
 box('Sheltered entrance',0,-d/2-.80,3.15,5.3,1.7,.15,accent,c)
 ramp('Entry ramp',0,-d/2-.9,2.7,1.8,.09,.19,bid+'_Approach')
 for xx in [-w/2+.2,w/2-.2]:box('Facade accent pier',xx,-d/2-.13,1.97,.20,.10,3.58,accent,c)
 c=bid+'_Roof';box('Closed ceiling slab',0,0,4.06,w+.35,d+.35,.16,'white',c) # wall ends3.98, slabbottom3.98
 if b['roof']=='flat':
  box('Roof finish',0,0,4.16,w+.1,d+.1,.04,'stone',c)
  for yy in [-d/2,d/2]:box('Parapet',0,yy,4.43,w+.35,.18,.54,'cream',c);box('Coping',0,yy,4.73,w+.45,.28,.06,accent,c)
  for xx in [-w/2,w/2]:box('Side parapet',xx,0,4.43,.18,d-.18,.54,'cream',c);box('Side coping',xx,0,4.73,.28,d-.05,.06,accent,c)
  box('Vent housing',w*.30,d*.28,4.48,1.6,1,.60,accent,c)
  for i in range(5):box('Vent grille',w*.30-.6+i*.3,d*.28-.51,4.49,.12,.025,.35,'darkgreen',c)
 else:
  half=d/2+.45;rise=1.55;ang=math.atan2(rise,half);sl=math.hypot(half,rise);base=4.13
  for side in [-1,1]:
   o=box('School pitched roof',0,side*half/2,base+rise/2,w+.8,sl,.14,'sage',c);o.rotation_euler.x=-side*ang
   for i in range(28):
    o=box('Standing seam',-w/2+i*w/27,side*half/2,base+rise/2+.085,.025,sl,.027,'darkgreen',c);o.rotation_euler.x=-side*ang
  box('Ridge',0,0,base+rise+.05,w+.9,.15,.13,'sage',c)
  for side in [-1,1]:
   underside=base-.07/math.cos(ang);p=[(-d/2,4.10),(d/2,4.10),(d/2,underside+rise*(1-d/2/half)),(0,underside+rise),(-d/2,underside+rise*(1-d/2/half))]
   vs=[(side*w/2+dx,yy,zz) for dx in [-.08,.08] for yy,zz in p];fs=[tuple(range(4,-1,-1)),tuple(range(5,10))]+[(i,(i+1)%5,(i+1)%5+5,i+5) for i in range(5)]
   me=bpy.data.meshes.new('School gable');me.from_pydata(vs,[],fs);me.materials.append(h.M['cream']);o=bpy.data.objects.new('Closed school gable',me);h.col(c).objects.link(o)

for b in BUILDINGS:
 if b.get('source'):continue
 new_shell(b)
# B01 two class rooms, entry corridor and central teacher/WC core.
c='B01_Interior'
for side in [-1,1]:
 h.wall_x('Classroom dividing wall',side*2,-3.15,5.9,[],c,.14,2.9)
 start,end=(-11.39,-2) if side<0 else (2,11.39);cx=side*6.7
 h.wall_y('Classroom entry wall',-3.15,start,end,[(cx,1.4,0,2.5)],c,.14,2.9)
 label('一班' if side<0 else '二班',cx,-3.24,2.8,1.3,c,size=.24)
 box('Classroom chalkboard',cx,5.77,2.0,5.2,.07,1.65,'darkgreen',c)
 for j in range(4):
  for i in range(3):
   x=side*6.7+(i-1)*2.05;y=-.8+j*1.3
   table('Student desk',x,y,1.25,.65,c,.80);chair(x,y-.60,c,math.pi,True)
   box('Exercise book',x,y,.875,.34,.26,.025,'white',c)
 table('Teaching table',cx,4.45,2.5,.7,c);chair(cx,5.2,c)
 shelves(side*9.7,-4.65,2.4,c)
toilet(0,4.5,c);table('Teacher reception desk',0,.0,1.9,.72,c);chair(0,.9,c)
# B04 multipurpose hall with separate consultation room.
c='B04_Interior'
table('Community meeting table',-5.3,-.6,5.2,2.3,c)
for x in [-7.1,-5.3,-3.5]:chair(x,.95,c);chair(x,-2.15,c,math.pi)
for x,rot in [(-8.7,-math.pi/2),(-1.9,math.pi/2)]:chair(x,-.6,c,rot)
box('Community noticeboard',-6.2,6.30,2.1,5,.08,1.4,'sage',c)
for i in range(7):box('Community notes',-8.15+i*.65,6.25,2.1,.42,.012,.6,['white','ochre','clay'][i%3],c)
box('Tea counter',-6,5.3,.73,5.0,.85,1.1,'sage',c);box('Tea countertop',-6,5.3,1.33,5.1,.9,.10,'white',c)
cyl('Tea kettle',-6.5,5.3,1.56,.18,.34,'metal',c);box('Tea sink',-4.4,5.3,1.39,.65,.5,.015,'metal',c)
toilet(.1,5.0,c)
h.wall_x('Consultation privacy wall',3,-1.2,6.39,[],c,.14,2.9);h.wall_y('Consultation entry',-1.2,3,11.39,[(6,1.35,0,2.5)],c,.14,2.9)
label('邻里咨询',6,-1.29,2.8,2.0,c,size=.23);desk(7,2.8,c,2.4)
for x in [5,8.5]:box('Consultation sofa',x,5.3,.62,2.4,.90,.85,'sage',c);box('Sofa back',x,5.68,1.13,2.4,.16,.65,'fabric',c)
box('Children rug',7,-3.8,.205,5.5,2.9,.03,'fabric',c);table('Children craft table',6,-3.5,2.3,1.1,c,.67)
for x,y in [(4.3,-3.5),(7.7,-3.5),(6,-4.65)]:cyl('Low stool',x,y,.43,.32,.48,'ochre',c)
for i in range(6):box('Craft blocks',5.3+.27*i,-3.5,.80,.19,.2,.17,['clay','sage','ochre'][i%3],c)
# B05 public service in front, sorting and goods entrance at rear.
c='B05_Interior'
for x in [-4.6,4.6]:
 box('Postal service counter',x,-1.7,.79,5.9,1.0,1.2,'sage',c);box('Countertop',x,-1.7,1.43,6,1.08,.10,'white',c)
 box('Postal terminal',x,-1.5,1.68,.62,.06,.38,'darkgreen',c);chair(x,-.35,c)
label('寄 件',-4.6,-2.26,.93,1.2,c,size=.20);label('取 件',4.6,-2.26,.93,1.2,c,size=.20)
h.wall_y('Sorting room partition',1.15,-9.39,9.39,[(0,2.6,0,2.8)],c,.14,3.0)
for x in [-4.6,4.6]:
 cx=-3.5 if x<0 else x;ww=3.4 if x<0 else 4.8
 table('Sorting worktable',cx,3.1,ww,1.4,c);shelves(cx,5.6,3.4 if x<0 else 6,c,True)
 for i in range(5):box('Sorted envelopes',cx-1.25+.58*i,3.1,1.05,.43,.32,.12,'white',c)
toilet(-7.7,5,c)
# Post wall slots and packing bench inside street-facing customer area.
for i in range(5):
 for j in range(3):
  box('Letter pigeonhole',-8.1+i*.65,-6.35,.65+j*.55,.60,.18,.50,'wood',c);box('Mailbox slot',-8.1+i*.65,-6.24,.7+j*.55,.4,.025,.055,'darkgreen',c)
table('Self service wrapping',6.7,-4.7,3,.8,c);box('Packing roll',6.4,-4.7,1.10,.6,.36,.20,'ochre',c)
ramp('Postal rear ramp',0,7.4,2.9,1.8,.19,.09,'B05_Approach')
# B06 modest neighbourhood police station, no detention area.
c='B06_Interior'
box('Help desk',-4,-2.65,.83,5.2,1.0,1.30,'bluegrey',c);box('Help countertop',-4,-2.65,1.52,5.3,1.1,.08,'lightwood',c);chair(-4,-1.4,c)
label('便民接待',-4,-3.21,.98,2,c,size=.23)
for x in [3.5,5.1,6.7]:chair(x,-4.7,c,math.pi)
for x in [-6.5,-2.7]:desk(x,2.6,c,2.5)
box('Community map board',-5.5,6.30,2.1,5.2,.08,1.7,'sage',c)
for i in range(5):box('Map street',-7.5+i,6.245,2.1,.035,.02,1.4,'white',c)
for z in [1.6,2.1,2.6]:box('Map lane',-5.5,6.245,z,4.7,.02,.03,'white',c)
h.wall_x('Mediation room wall',1.4,-1,6.39,[],c,.14,2.9);h.wall_y('Mediation front',-1,1.4,9.39,[(4,1.4,0,2.5)],c,.14,2.9)
label('社区调解',4,-1.09,2.8,2,c,size=.23);table('Mediation table',5,1.9,3,1.25,c)
for x in [4.2,5.8]:chair(x,3.25,c);chair(x,.55,c,math.pi)
toilet(7.7,5,c)
for x in [2.4,3.5]:box('Equipment cabinet',x,5.7,1.35,.95,.8,2.34,'bluegrey',c);box('Cabinet handle',x+.25,5.27,1.35,.035,.04,.35,'metal',c)
# Transform the new south row by 180 degrees; everything remains in its own named layer.
for b in BUILDINGS:
 if b.get('source'):continue
 x,y=b['center'];angle=math.pi if b['door']=='n' else 0
 for name,c in list(h.C.items()):
  if name.startswith(b['id']+'_'):
   for o in c.objects:
    a,bb=o.location.x,o.location.y;o.location.x=x+math.cos(angle)*a-math.sin(angle)*bb;o.location.y=y+math.sin(angle)*a+math.cos(angle)*bb;o.rotation_euler.z+=angle
 # Entry ramps mesh coordinates were authored globally and need rotation through object matrix.
# Append library/clinic objects with their original meshes, dimensions, floor groups and materials.
for b in BUILDINGS:
 if not b.get('source'):continue
 key=b['source'];f=S/key/(b['id']+'-'+key+'.blend')
 with bpy.data.libraries.load(str(f),link=False) as (src,dst):
  names=[n for n in src.collections if n!='Studio'];dst.collections=list(names)
 count=0;tri=0;parts={}
 for name,c in zip(names,dst.collections):
  target=h.col(b['id']+'_'+name);parts[name]=[]
  for o in list(c.objects):
   if o.type!='MESH':continue
   transform=o.matrix_basis.copy();o.parent=None;o.matrix_world=transform;c.objects.unlink(o);target.objects.link(o)
   o.name=b['id']+'__'+o.name;o.data.calc_loop_triangles();tri+=len(o.data.loop_triangles);count+=1;parts[name].append(o)
  for o in list(c.objects):bpy.data.objects.remove(o,do_unlink=True)
  bpy.data.collections.remove(c)
 SOURCES[key]={'file':str(f.relative_to(R.parent)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'glbSha256':hashlib.sha256(f.with_suffix('.glb').read_bytes()).hexdigest(),'sourceMeshes':count,'sourceTriangles':tri,'scale':1,'translation':b['center'],'changedCopyOnly':[]}
 # Replace the original below-grade entrance ramp in the assembled copy to meet public paving.
 for o in list(parts['Landscape']):
  if '__Entrance ramp' in o.name:bpy.data.objects.remove(o,do_unlink=True)
 d=b['size'][1];ramp('B entrance ground connection',0,-d/2-2.3,2.3,.6,.09,.14,b['id']+'_Approach')
 SOURCES[key]['changedCopyOnly'].append('Entrance ramp now joins paving at z=0.09 and original porch at z=0.14')
 if key=='clinic':
  # The original clinic has no side door. Open only its assembled east facade at y=-1.10.
  east=h.C['B03_EastFacade'];base=next(o for o in east.objects if '__Side base' in o.name);glass=next(o for o in east.objects if '__Side glass' in o.name)
  base_mat=base.data.materials[0];glass_mat=glass.data.materials[0];bpy.data.objects.remove(base,do_unlink=True);bpy.data.objects.remove(glass,do_unlink=True)
  for lo,hi in [(-5.5,-1.8),(-.4,5.5)]:
   o=box('Clinic split side base',7.9,(lo+hi)/2,.63,.2,hi-lo,.9,'sage','B03_EastFacade');o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(base_mat)
   o=box('Clinic split side glazing',7.9,(lo+hi)/2,2.10,.028,hi-lo,2,'glass','B03_EastFacade');o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(glass_mat)
  o=box('Clinic door transom',7.9,-1.1,2.96,.028,1.4,.28,'glass','B03_EastFacade')
  for yy in [-1.77,-.43]:box('Clinic side door jamb',7.9,yy,1.48,.24,.06,2.6,'wood','B03_EastFacade')
  box('Clinic side door lintel',7.9,-1.1,2.8,.24,1.4,.08,'wood','B03_EastFacade')
  ramp('Clinic side ramp',8.95,-1.1,1.5,2.1,.19,.09,'B03_Approach','x')
  box('Clinic side canopy',8.65,-1.1,3.0,1.65,2.0,.12,'sage','B03_EastFacade')
  SOURCES[key]['changedCopyOnly'].append('East facade base/glass split to add a 1.34m clear auxiliary door; original source untouched')
 for name,c in list(h.C.items()):
  if name.startswith(b['id']+'_'):
   for o in c.objects:o.location.x+=b['center'][0];o.location.y+=b['center'][1]
# Site and connected paved routes. The southern entry bypasses the post office along a rear promenade.
box('B district ground',0,0,-.18,85,62.5,.36,'grass','Ground')
PATHS=[[-42.5,-7,42.5,-3],[-13,-28.5,-10.5,29],[14,-28.5,17,29],[-40.5,25,40.5,28],[-40.5,-29,40.5,-26],[38.5,-27.5,41,26.5],[-41,-27.5,-38.5,26.5],[-1.5,-31.25,1.5,-26],[-13,27,-10.5,31.25],[14,27,17,31.25]]
for b in BUILDINGS:
 x,y=b['center'];w,d=b['size'];front=y-d/2 if b['door']=='s' else y+d/2
 b['entry']=[x,front];b['rotation']=math.pi if b['door']=='n' else 0
 if b['id']=='B01':PATHS += [[-16.8,-3,-14.2,8.0],[-27.6,7.2,-14.2,9.3]]
 elif b['door']=='s':PATHS.append([x-1.5,-3,x+1.5,front-1.9])
 else:PATHS.append([x-1.5,front-0.1,x+1.5,-7])
PATHS += [[36.1,11.3,40,13.3],[-1.05,-26.1,2.05,-23.4],[18.5,-2,37.8,5],[18.5,-3,21,1],[35.0,-3,37.8,1],[-8.5,-2,11.5,3.0],[-1,-3,2,-1],[-38,7,-27.3,9.3]]
# Court = 18 x 8, with short end fence that does not cross school access.
box('School small playground',-26.125,2.5,.07,18,8,.14,'court','Schoolyard')
for y in [-.9,5.9]:box('Court boundary line',-26.125,y,.146,16.2,.06,.012,'line','Schoolyard')
for x in [-34.225,-18.025]:box('Court end line',x,2.5,.146,.06,6.8,.012,'line','Schoolyard')
box('Court halfway line',-26.125,2.5,.146,.06,6.8,.012,'line','Schoolyard')
# Small hoop is play-scale, kept at the west edge away from school doorway.
box('Hoop pole',-35.4,2.5,1.42,.12,.12,2.84,'darkgreen','Schoolyard');box('Hoop board',-35.25,2.5,2.65,.12,1.25,.8,'white','Schoolyard')
bpy.ops.mesh.primitive_torus_add(major_segments=24,minor_segments=6,major_radius=.24,minor_radius=.025,location=(-34.9,2.5,2.42))
o=bpy.context.object;o.name='Playground hoop rim';o.data.materials.append(h.M['red'])
for cc in list(o.users_collection):cc.objects.unlink(o)
h.col('Schoolyard').objects.link(o)
for j in range(8):
 a=j*math.tau/8;beam('Hoop net',(-34.9+.24*math.cos(a),2.5+.24*math.sin(a),2.42),(-34.9+.16*math.cos(a),2.5+.16*math.sin(a),2.09),.012,'white','Schoolyard')
for yy in [-.9,.0,.9,1.8,2.7,3.6,4.5,5.4]:box('Playground low fence',-35.6,yy,.54,.05,.05,.95,'wood','Schoolyard')
box('Playground fence cap',-35.6,2.25,1.03,.07,7.4,.07,'wood','Schoolyard')
# Paved union, subtract imported porch footprints to avoid a paving slab under the ramp lip.
xs=sorted({r[i] for r in PATHS for i in [0,2]});ys=sorted({r[i] for r in PATHS for i in [1,3]});TILES=[]
for ya,yb in zip(ys,ys[1:]):
 runs=[]
 for xa,xb in zip(xs,xs[1:]):
  xx,yy=(xa+xb)/2,(ya+yb)/2
  if any(a<xx<c and bb<yy<d for a,bb,c,d in PATHS):
   if runs and abs(runs[-1][1]-xa)<1e-6:runs[-1]=(runs[-1][0],xb)
   else:runs.append((xa,xb))
 for xa,xb in runs:
  box('Unified public path',(xa+xb)/2,(ya+yb)/2,.045,xb-xa,yb-ya,.09,'gravel','Paths');TILES.append([xa,ya,xb,yb])
def bench(x,y,face='s'):
 c='Amenities';box('Garden bench',x,y,.52,2.7,.65,.14,'wood',c);box('Bench back',x,y+(.28 if face=='s' else -.28),.91,2.7,.09,.65,'sage',c)
 for dx in [-.98,.98]:box('Bench support',x+dx,y,.26,.13,.53,.48,'darkgreen',c)
def tree(x,y,s=1):
 cyl('Garden trunk',x,y,1.5*s,.17*s,3*s,'wood','Landscape')
 for dx,dy,z in [(0,0,3.5),(-.8,.1,3.0),(.7,.2,3.2),(0,-.8,3.05)]:leaf('Garden canopy',x+dx*s,y+dy*s,z*s,(1.3*s,1.2*s,1.2*s),'leaf' if dx else 'leafLight','Landscape')
def flowers(x,y,i):
 leaf('Free form shrub',x,y,.43,(.8,.65,.48),'leafLight','Landscape')
 for j in range(5):
  a=j*2.4+i;xx=x+.67*math.cos(a);yy=y+.57*math.sin(a);zz=.55+.09*(j%3)
  cyl('Flower stem',xx,yy,zz/2,.012,zz,'leaf','Landscape')
  for k in range(5):
   aa=k*math.tau/5;leaf('Flower petal',xx+.09*math.cos(aa),yy+.09*math.sin(aa),zz,(.09,.075,.045),['white','flowerPink','flowerYellow','lavender'][(i+j)%4],'Landscape')
for x,y,face in [(-5,1,'s'),(7.7,1,'s'),(25.5,3.9,'s'),(32,3.9,'s'),(-31,-8.8,'n'),(5.6,-8.8,'n'),(31.6,-8.8,'n')]:bench(x,y,face)
for x,y,s in [(-34.9,23.3,.70),(-22,23.2,.72),(-5,23.0,.85),(10,23,.85),(24,23.0,.85),(35,23,.70),(-7.3,4.0,.75),(10.3,4.0,.8),(23,5.8,.7),(33.5,5.8,.72),(-35,-25.1,.55),(-21,-25.1,.55),(24,-25.1,.55),(35,-25.1,.55)]:tree(x,y,s)
for i,(x,y) in enumerate([(-8.8,2),(-8.5,5),(10.8,6),(12,1),(20,4.5),(37.8,4.5),(-34,-8.7),(-22,-8.7),(2.8,-8.7),(8,-8.7),(22,-8.7),(35,-8.7)]):flowers(x,y,i)
for i in range(36):
 x=-39+i*2.2
 if -14<x<-9 or 12<x<19:continue
 flowers(x,29.6+.15*math.sin(i),i)
# Reading pergola in the library forecourt: open sides, two seats, clear middle access.
for x in [-8.2,-3.2]:
 for y in [-1.5,2.6]:box('Reading pergola post',x,y,1.48,.12,.12,2.8,'wood','Courtyard_Pergola')
for i in range(9):box('Pergola lath',-8.35+i*.66,.55,2.94,.08,4.6,.10,'wood','Courtyard_Pergola_Roof')
# Clinic quiet waiting forecourt and district notices; fixtures placed off through paths.
for x,y in [(-9,-8.6),(12,-8.6),(-9.2,21.5),(18.5,21.5)]:
 cyl('Path light',x,y,1.8,.05,3.5,'darkgreen','Amenities');box('Lantern',x,y,3.57,.4,.4,.45,'white','Amenities');box('Lantern cap',x,y,3.83,.5,.5,.06,'darkgreen','Amenities')
for x,y,t in [(4,-29.8,'B  公共服务区'),(37.8,-8.6,'东往河畔住宅'),(-37,-8.6,'西往庭院住宅')]:
 box('Sign post',x,y,1,.08,.08,2,'wood','Wayfinding');label(t,x,y,1.95,3.9,'Wayfinding',size=.25)
# Post service yard: parcel cart and loading bay, south of post office, off promenade centre.
box('Postal loading pad',6.8,-24.7,.065,5.3,1.7,.13,'stone','Logistics')
box('Parcel cart deck',6.8,-24.7,.45,1.8,.85,.12,'sage','Logistics')
for x in [6.15,7.45]:
 for y in [-25,-24.4]:
  o=cyl('Cart wheel',x,y,.28,.16,.08,'dark','Logistics');o.rotation_euler.x=math.pi/2
for x in [6.4,7.1]:box('Delivered parcels',x,-24.7,.77,.55,.65,.5,'ochre','Logistics')
for y in [-25,-24.4]:beam('Cart handle upright',(7.7,y,.45),(7.7,y,1.2),.045,'metal','Logistics')
beam('Cart handle',(7.7,-25,1.2),(7.7,-24.4,1.2),.045,'metal','Logistics')
# Street mailbox faces north, near postal entrance but out of entry corridor.
box('Street postbox',-3.3,-8.8,.98,.62,.54,1.75,'sage','Amenities');box('Mail slot',-3.3,-8.51,1.42,.41,.025,.055,'darkgreen','Amenities')
# Root groups are flat and consistently named for both Blender and GLB.
scene=bpy.context.scene;scene.name='01 B district';scene.unit_settings.system='METRIC'
for name,c in list(h.C.items()):
 root=bpy.data.objects.new(name,None);c.objects.link(root)
 for o in list(c.objects):
  if o!=root:o.parent=root
bpy.context.view_layer.update()
meshes=[o for o in scene.objects if o.type=='MESH'];tri=0
for o in meshes:o.data.calc_loop_triangles();tri+=len(o.data.loop_triangles)
bpy.ops.object.select_all(action='SELECT');glb=R/'B-public-services.glb';bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_cameras=False,export_lights=False)
meta={'title':'B 区 · 公共服务庭院','date':'2026-10-14','plot':[85,62.5],'worldPlanRect':[450,120,340,250],'buildings':BUILDINGS,'sources':SOURCES,'paths':TILES,'pathRectangles':PATHS,'units':'metres','sourceAxes':'Z up, north +Y','glbAxes':'Y up, north -Z','meshObjects':len(meshes),'triangles':tri,'groups':list(h.C),'sha256':hashlib.sha256(glb.read_bytes()).hexdigest(),'status':'design-review','blender':bpy.app.version_string,'portals':{'south':[0,-31.25],'east':[42.5,-5],'west':[-42.5,-5],'northWest':[-11.75,31.25],'northEast':[15.5,31.25]}}
(R/'manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
h.studio(scene);scene.cycles.samples=20;scene.render.resolution_x=1600;scene.render.resolution_y=1200
bpy.data.objects['Studio ground'].location.z=-.65
scene.camera=h.camera('B overview',(90,-120,110),(0,1,0),115)
views=[(scene,'overview.png')]
settings=[('02 Plan',(0,-.001,115),(0,0,0),94,None,1,'plan.png')]
for i,b in enumerate(BUILDINGS):
 x,y=b['center'];north=b['door']=='n';settings.append((f'{i+3:02d} '+b['id'],(x+22,y+(27 if north else -27),29),(x,y,1),29 if b['id'] in ['B02','B03','B05','B06'] else 33,b['id'],1,b['id']+'-interior.png'))
settings.append(('09 Library upper',(24,-14,31),(1.875,13.5,4.3),29,'B02',2,'B02-upper.png'))
for name,loc,target,scale,selected,floor,file in settings:
 sc=scene.copy();sc.name=name;sc.use_fake_user=True;sc.camera=h.camera(name+' camera',loc,target,scale)
 for child in sc.view_layers[0].layer_collection.children:
  n=child.name
  if n=='Studio':continue
  if selected:
   hide=n.startswith('B0') and not n.startswith(selected+'_')
   if n.startswith(selected+'_'):
    part=n[len(selected)+1:];hide=part in ['Roof','Front','FrontFacade','EastFacade']
    if selected=='B02':hide=hide or (floor==1 and part.startswith('Upper')) or (floor==2 and part in ['UpperFront','UpperEast'])
   if not n.startswith('B0'):hide=n not in ['Ground','Paths']
  else:hide=n.endswith('_Roof') or n.startswith('B02_Upper')
  child.exclude=hide
 views.append((sc,file))
bpy.context.window.scene=scene
for scr in bpy.data.screens:
 for ar in scr.areas:
  if ar.type=='VIEW_3D':ar.spaces.active.shading.type='MATERIAL';ar.spaces.active.overlay.show_overlays=False;ar.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(R/'B-public-services.blend'))
for sc,file in views:
 if os.getenv('B_RENDER') and file not in os.getenv('B_RENDER').split(','):continue
 sc.render.filepath=str(R/file);bpy.ops.render.render(write_still=True,scene=sc.name);print('RENDERED',file,flush=True)
print('COMPLETE',len(meshes),tri,flush=True)
