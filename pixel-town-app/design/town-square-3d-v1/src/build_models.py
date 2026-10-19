import sys,math,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import bpy
from mathutils import Vector
import model_helpers as h
R=Path(__file__).resolve().parent.parent;h.ROOT=R
h.PALETTE.update({'paving':'dfd3b9','edge':'c5b89c','soil':'87755c','bark':'8c7554','clay':'bf866c','ochre':'d5b260','mutedblue':'7b9ea4','leafDark':'5a7859','cloth':'eee3cb'})
h.init();box,cyl,leaf,beam=h.box,h.cyl,h.leaf,h.beam
PC=(0,-2.5);CY=-2.5

def ring(n,x,y,ri,ro,z,height,mat,c,start=0,end=360,steps=96):
 steps=max(2,round(steps*(end-start)/360));vs=[]
 for zz in [z-height/2,z+height/2]:
  for r in [ri,ro]:
   for i in range(steps+1):
    a=math.radians(start+(end-start)*i/steps);vs.append((x+r*math.cos(a),y+r*math.sin(a),zz))
 k=steps+1;fs=[]
 for i in range(steps):fs.extend([(i,i+1,k+i+1,k+i),(2*k+i,3*k+i,3*k+i+1,2*k+i+1),(i,2*k+i,2*k+i+1,i+1),(k+i,k+i+1,3*k+i+1,3*k+i)])
 fs.extend([(0,k,3*k,2*k),(steps,2*k+steps,3*k+steps,k+steps)])
 # Full rings use duplicate seam vertices but have no zero-area triangles.
 me=bpy.data.meshes.new(n);me.from_pydata(vs,[],fs);me.materials.append(h.M[mat]);me.update();o=bpy.data.objects.new(n,me);h.col(c).objects.link(o);return o

def tree(x,y,s=1,c='Landscape'):
 cyl('Small tree trunk',x,y,1.45*s,.18*s,2.9*s,'bark',c)
 for dx,dy,z in [(0,0,3.5),(-.8,.2,3.1),(.7,.2,3.0),(0,-.7,3.15)]:leaf('Small tree canopy',x+dx*s,y+dy*s,z*s,(1.4*s,1.3*s,1.5*s),'leafLight' if dx==0 else 'leaf',c)

def flowers(x,y,s=1):
 c='Landscape';leaf('Soft shrub',x,y,.45*s,(.85*s,.65*s,.5*s),'leafLight',c)
 for j in range(5):
  xx=x+.78*s*math.cos(j*2.4);yy=y+.6*s*math.sin(j*2.4);z=(.62+.1*(j%2))*s
  cyl('Flower stem',xx,yy,z/2,.015,z,'leaf',c)
  for k in range(5):
   a=k*math.tau/5;leaf('Flower petal',xx+.11*s*math.cos(a),yy+.11*s*math.sin(a),z,(.115*s,.085*s,.05*s),['white','flowerPink','lavender','flowerYellow'][j%4],c)
  leaf('Flower pollen',xx,yy,z+.02,(.04,.04,.03),'ochre',c)

def bench(x,y,angle=0,c='Seating'):
 before=set(h.col(c).objects)
 for yy in [-.24,0,.24]:box('Garden bench slat',x,y+yy,.58,2.8,.20,.10,'lightwood',c)
 for zz in [.90,1.12]:box('Garden bench back',x,y+.32,zz,2.8,.09,.18,'wood',c)
 for dx in [-1,1]:box('Bench metal support',x+dx,y,.32,.10,.60,.45,'darkgreen',c)
 for o in set(h.col(c).objects)-before:
  dx=o.location.x-x;dy=o.location.y-y;o.location.x=x+math.cos(angle)*dx-math.sin(angle)*dy;o.location.y=y+math.sin(angle)*dx+math.cos(angle)*dy;o.rotation_euler.z+=angle
  if c=='Pergola_Furniture':o.location.z+=.15

def circlepoly(x,y,r,n=128):return [(x+r*math.cos(i*math.tau/n),y+r*math.sin(i*math.tau/n)) for i in range(n)]
def rectpoly(x0,x1,y0,y1):return [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
# Original E zone 340 x 220 at 4 units/m. Original plaza centre (620,550).
box('E site',0,0,-.18,85,55,.36,'grass','Ground')
positive=[circlepoly(0,CY,18),rectpoly(-42.5,42.5,CY-2.25,CY+2.25),rectpoly(-2.25,2.25,-27.5,27.5),rectpoly(-40,-19,-18,15),circlepoly(28,7,7.0),rectpoly(26.5,29.5,-.25,3),rectpoly(21.5,36.5,-18,-10),rectpoly(27,30,-10,-4.75),rectpoly(-19,-5,18,25),rectpoly(-13,-10,9,18),rectpoly(-5,0,20,23),rectpoly(5,16,19,25),rectpoly(0,5,20,23)]
holes=[circlepoly(0,CY,3.8),circlepoly(28,7,4.65)]
# A scanline polygon union gives a continuous paved mesh, with actual tree/water holes.
polys=[(p,False) for p in positive]+[(p,True) for p in holes]
edges=[];ys=set()
for poly,hole in polys:
 for a,b in zip(poly,poly[1:]+poly[:1]):
  ys.update([a[1],b[1]])
  if abs(a[1]-b[1])>1e-8:edges.append((a,b,hole))
def at(e,y):a,b,_=e;return a[0]+(b[0]-a[0])*(y-a[1])/(b[1]-a[1])
# Include crossing heights so interval ordering cannot change inside a strip.
for i,a in enumerate(edges):
 for b in edges[i+1:]:
  lo=max(min(a[0][1],a[1][1]),min(b[0][1],b[1][1]));hi=min(max(a[0][1],a[1][1]),max(b[0][1],b[1][1]))
  if hi-lo<1e-6:continue
  d0=at(a,lo)-at(b,lo);d1=at(a,hi)-at(b,hi)
  if d0*d1<0:ys.add(lo+(hi-lo)*d0/(d0-d1))
ys=sorted(set(round(y,8) for y in ys));verts=[];faces=[];vmap={};quadrecords=[]
def vertex(x,y):
 key=(round(x,7),round(y,7))
 if key not in vmap:vmap[key]=len(verts);verts.append((*key,.09))
 return vmap[key]
for ya,yb in zip(ys,ys[1:]):
 if yb-ya<1e-6:continue
 ym=(ya+yb)/2;events=[]
 for poly,hole in polys:
  crosses=[]
  for a,b in zip(poly,poly[1:]+poly[:1]):
   if min(a[1],b[1])<ym<max(a[1],b[1]):
    e=(a,b,hole);crosses.append((at(e,ym),e))
  crosses.sort(key=lambda q:q[0])
  for j,(xx,e) in enumerate(crosses):events.append((xx,e,hole,1 if j%2==0 else -1))
 events.sort(key=lambda q:q[0]);pc=hc=0;start=None
 for xx,e,hole,delta in events:
  before=pc>0 and hc==0
  if hole:hc+=delta
  else:pc+=delta
  after=pc>0 and hc==0
  if after and not before:start=e
  elif before and not after:
   if at(e,ym)-at(start,ym)<1e-6:continue
   points=[(at(start,ya),ya),(at(e,ya),ya),(at(e,yb),yb),(at(start,yb),yb)]
   ids=[vertex(x,y) for x,y in points]
   for tri in [(ids[0],ids[1],ids[2]),(ids[0],ids[2],ids[3])]:
    a,b,c=[Vector(verts[k]) for k in tri]
    if (b-a).cross(c-a).length>1e-9:faces.append(tri)
   quadrecords.append(points)
me=bpy.data.meshes.new('Joined paved surface');me.from_pydata(verts,[],faces);me.materials.append(h.M['paving']);me.update();o=bpy.data.objects.new('Continuous square paving',me);h.col('Paving').objects.link(o)
# Narrow edge and radial inlays are slightly raised, never duplicate pavement faces.
ring('Outer plaza edging',0,CY,17.82,18,.11,.04,'edge','Paving_Detail')
for r in [8.3,12.9]:ring('Plaza paving circle',0,CY,r,r+.055,.097,.009,'edge','Paving_Detail')
# Central mature tree with clear trunk, branching structure and multi-lobed crown.
cyl('Tree soil well',0,CY,.02,3.8,.04,'soil','Tree_Base',96)
ring('Tree well stone edging',0,CY,3.8,4.02,.22,.44,'stone','Tree_Base')
cyl('Mature tree trunk',0,CY,3.0,.73,6.0,'bark','Landmark_Trunk',14)
for a in [0,1.1,2.2,3.3,4.4,5.5]:
 beam('Root flare',(.2*math.cos(a),CY+.2*math.sin(a),1.0),(2.0*math.cos(a),CY+2.0*math.sin(a),.16),.36,'bark','Landmark_Trunk')
 beam('Major tree branch',(0,CY,4.5),(3.4*math.cos(a),CY+3.4*math.sin(a),8.5+.5*math.sin(a)),.40,'bark','Landmark_Trunk')
for i,(dx,dy,z,sx,sy,sz) in enumerate([(0,0,10.8,4.4,4.2,3.4),(-4,0,9.8,3.9,3.6,3.0),(4,.4,10.1,4.0,3.5,3.1),(-1,-4,9.6,4,3.5,3),(0,4,10.1,4.5,3.6,3.1),(-3,3,10.5,3.5,3.6,3.3),(3,-3,10.3,3.5,3.4,3)]):
 leaf('Mature tree crown',dx,CY+dy,z,(sx,sy,sz),['leaf','leafLight','leafDark'][i%3],'Landmark_Canopy')
# Four curved bench segments leave cardinal gaps for tree-care access.
for q in range(4):
 a,b=12+q*90,78+q*90
 for ri,ro in [(4.35,4.58),(4.61,4.84),(4.87,5.1)]:ring('Tree ring seat slat',0,CY,ri,ro,.59,.12,'lightwood','Ring_Seats',a,b)
 ring('Tree ring backrest',0,CY,4.25,4.35,.95,.65,'wood','Ring_Seats',a,b)
 for theta in [a+6,(a+b)/2,b-6]:
  t=math.radians(theta);x,y=4.7*math.cos(t),CY+4.7*math.sin(t)
  o=box('Ring seat leg',x,y,.31,.12,.66,.44,'darkgreen','Ring_Seats');o.rotation_euler.z=t-math.pi/2
# East shallow reflective basin, recessed bottom and a little stone water source.
cyl('Water basin bottom',28,7,.025,4.65,.05,'tile','Water_Basin',96)
ring('Water basin wall',28,7,4.35,4.65,.17,.60,'stone','Water_Basin')
ring('Basin coping',28,7,4.30,4.85,.50,.12,'white','Water_Basin')
cyl('Shallow water surface',28,7,.30,4.34,.015,'water','Water_Surface',96)
cyl('Fountain stone base',28,7,.20,.85,.4,'stone','Water_Basin',32)
cyl('Fountain stone column',28,7,.83,.36,.9,'stone','Water_Basin',24)
cyl('Water source cap',28,7,1.32,.52,.12,'white','Water_Basin',24)
# Stylized static falling water arcs, deliberately separate from the basin for later animation.
for k in range(6):
 a=k*math.tau/6
 for i in range(6):
  t0=i/6;t1=(i+1)/6
  def point(t):return (28+(0.35+1.5*t)*math.cos(a),7+(0.35+1.5*t)*math.sin(a),1.33-.97*t*t)
  beam('Static water arc',point(t0),point(t1),.035,'water','Water_Surface')
for y in [4,10]:bench(33.0,y,-math.pi/2)
# Southeast pergola: green metal/wood frame and a quiet reading corner.
box('Pergola deck',29,-14,.12,14,8,.24,'lightwood','Pergola_Base')
for x in [22.5,29,35.5]:
 for y in [-17.5,-10.5]:box('Pergola post',x,y,1.75,.16,.16,3.25,'wood','Pergola_Frame')
for y in [-17.5,-10.5]:box('Pergola longitudinal beam',29,y,3.42,14.4,.20,.22,'wood','Pergola_Frame')
for i in range(22):box('Pergola shade slat',22.2+i*.65,-14,3.63,.13,8.4,.16,'sage','Pergola_Roof')
for x in [25,32.8]:bench(x,-16.3,0,'Pergola_Furniture')
for x in [25,32.8]:
 cyl('Reading table',x,-13.9,.86,.72,.10,'lightwood','Pergola_Furniture',24);cyl('Reading table stem',x,-13.9,.54,.10,.54,'darkgreen','Pergola_Furniture')
 cyl('Table foot',x,-13.9,.29,.35,.08,'darkgreen','Pergola_Furniture',24)
for i in range(10):
 x=22.8+i*1.3;leaf('Pergola vine',x,-17.55,3.73,(.7,.5,.22),'leaf','Pergola_Roof')
# West six mobile stalls. Open the event collection for a weekend market; hide for daily use.
STALLS=[]
for row,y in enumerate([-12.0,10.0]):
 for j,x in enumerate([-35,-28,-21]):
  idx=row*3+j;c='Market_Fixtures';roof='Market_Canopies';face=1 if row==0 else -1
  STALLS.append({'id':idx+1,'center':[x,y],'size':[4.8,3.0]})
  box('Market rolling counter',x,y,.76,4.2,1.20,1.18,'wood',c)
  box('Stall countertop',x,y,1.40,4.4,1.35,.12,'lightwood',c)
  for xx in [x-1.9,x+1.9]:
   for yy in [y-.43,y+.43]:
    o=cyl('Stall wheel',xx,yy,.20,.11,.08,'dark',c);o.rotation_euler.x=math.pi/2
  for xx in [x-2.2,x+2.2]:
   for yy in [y-1.2,y+1.2]:box('Stall canopy pole',xx,yy,1.64,.075,.075,2.98,'wood',c)
  for side in [-1,1]:
   sl=math.hypot(1.5,.5)
   for stripe in range(8):
    o=box('Striped market canopy',x-2.1+stripe*.60,y+side*.75,3.25,.60,sl,.045,'cloth' if stripe%2 else ['sage','clay','mutedblue'][j],roof);o.rotation_euler.x=-side*math.atan2(.5,1.5)
  # Products: fruit, bread, flowers, pottery, books, handmade homeware.
  for k in range(5):
   xx=x-1.5+k*.75
   if idx in [0,1]:
    box('Produce display tray',xx,y,1.50,.61,.72,.10,'lightwood',c)
    for m in range(3):leaf('Market produce',xx+(m-1)*.16,y,1.66,(.12,.13,.13 if idx==0 else .09),'tomato' if idx==0 else 'ochre',c)
   elif idx==2:
    cyl('Market flower pot',xx,y,1.63,.15,.32,'clay',c);leaf('Market bouquet',xx,y,1.98,(.25,.24,.32),'flowerPink' if k%2 else 'flowerYellow',c)
   elif idx==3:
    cyl('Pottery body',xx,y,1.73,.21,.50,'clay' if k%2 else 'sage',c);ring('Pottery rim',xx,y,.12,.21,2.0,.04,'clay',c,steps=24)
   elif idx==4:
    for z in [1.52,1.62,1.72]:box('Market book',xx,y,z,.5,.7,.09,['sage','clay','mutedblue'][int(z*10)%3],c)
   else:box('Handmade box',xx,y,1.70,.5,.5,.5,'wood',c)
  signy=y+face*.72
  box('Stall name board',x,signy,1.08,2.9,.06,.30,'darkgreen',c)
  o=h.text('Market label',['田园鲜蔬','小镇面包','四季花束','陶作小物','旧书交换','木作好物'][idx],x,signy+face*.04,1.08,.18,'white',c)
  if face==1:o.location.y=signy+.04;o.rotation_euler.z+=math.pi
# Bunting over the market, clear of the central crossing and all stalls.
for y in [-16.4,14.2]:
 for x in [-39,-18.8]:box('Event bunting pole',x,y,2.45,.09,.09,4.90,'wood','Event_Decor')
 beam('Bunting cable',(-39,y,4.75),(-18.8,y,4.75),.018,'darkgreen','Event_Decor')
 for i in range(20):
  x=-38.6+i*.98;me=bpy.data.meshes.new('Flag');me.from_pydata([(x,y,4.74),(x+.55,y,4.74),(x+.27,y,4.20)],[],[(0,2,1)]);me.materials.append(h.M[['sage','clay','ochre','mutedblue'][i%4]]);o=bpy.data.objects.new('Weekend bunting',me);h.col('Event_Decor').objects.link(o)
# Community bulletin board and a low book-swap cabinet on the northwest pocket.
c='Community'
for x in [-16.8,-8.2]:box('Noticeboard post',x,23.6,1.65,.14,.14,3.1,'wood',c)
box('Community noticeboard',-12.5,23.6,2.05,9,.18,2.1,'wood',c)
box('Notice cork face',-12.5,23.48,2.05,8.65,.04,1.75,'cream',c)
for i in range(6):
 x=-15.9+i*1.35;box('Community notice sheet',x,23.44,2.02,1.03,.025,1.35,['white','cloth','fabric'][i%3],c)
 for k in range(3):box('Printed notice line',x,23.419,2.25-k*.16,.65,.006,.025,'sage',c)
box('Notice weather hood',-12.5,23.5,3.25,9.4,.85,.13,'sage',c)
h.text('Community heading','小 镇 公 告',-12.5,23.37,2.92,.30,'darkgreen',c)
box('Book exchange cabinet',-7,19.5,.97,2.5,.8,1.75,'wood',c)
for z in [.45,1.05,1.65]:box('Book cabinet shelf',-7,19.45,z,2.35,.75,.08,'lightwood',c)
for j in range(10):box('Exchange book',-8+j*.21,19.3,.76,.15,.4,.46,['clay','sage','mutedblue'][j%3],c)
box('Book box roof',-7,19.5,1.91,2.8,1.0,.14,'sage',c)
bench(-16,19.5,math.pi,'Seating')
# Drinking water and low pet bowl, bin station, map marker and lamps.
c='Amenities'
for x,z in [(8.0,1.05),(9.2,.78)]:
 cyl('Drinking fountain column',x,22,z/2,.20,z,'stone',c)
 cyl('Drinking bowl',x,22,z,.36,.10,'metal',c,24)
 cyl('Drinking tap',x,22.12,z+.13,.035,.18,'metal',c)
ring('Pet water bowl',10.6,22,.25,.37,.18,.17,'stone',c,steps=32);cyl('Pet bowl water',10.6,22,.19,.25,.015,'water',c,32)
for x in [13.4,14.8]:
 box('Recycling bin',x,23.2,.65,1,.85,1.3,'sage',c);box('Bin top',x,23.2,1.34,1.08,.93,.10,'darkgreen',c)
for x,y in [(-18,17),(18,17),(-18,-22),(18,-22),(-40,-5.7),(40,-5.7)]:
 cyl('Square lamp post',x,y,2.0,.055,4.0,'darkgreen',c)
 box('Square lantern',x,y,3.98,.42,.42,.56,'cloth',c);box('Lantern cap',x,y,4.31,.54,.54,.1,'darkgreen',c)
# Soft planted margins: small trees and mixed flowers clustered rather than crop rows.
for x,y,s in [(-36,23,1.0),(-26,22,1.05),(22,23,.95),(35,22,1.1),(-34,-23,1.05),(-23,-24,.85),(9,-24,.85),(39,-22,.8),(-8,-24.6,.65)]:tree(x,y,s)
for i,(x,y) in enumerate([(-38,19),(-33,24),(-28,19),(-24,24),(-20,21),(20,22),(25,25),(32,21),(38,23),(-38,-22),(-30,-25),(-26,-22),(-20,-24),(-13,-24),(6,-25),(14,-24),(20,-23),(37,-22),(39,-16)]):
 for j in range(3):flowers(x+1.4*math.cos(j*2.1+i),y+1.0*math.sin(j*2.1+i),.65+.1*(j%2))
# Four directional plaques sit to the side of each exit, not across the paving.
for x,y,t in [(-38,1.4,'西往手作小巷'),(38,1.4,'东往河岸公园'),(4.1,25.5,'北往公共服务'),(4.1,-25.5,'南往日常商业街')]:
 box('Direction post',x,y,.92,.09,.09,1.84,'wood','Wayfinding');h.sign(t,x,y,1.75,3.2,'Wayfinding')
# Independent named groups exported identically into Blender and GLB.
scene=bpy.context.scene;scene.name='01 Weekend square';scene.unit_settings.system='METRIC'
for n,c in list(h.C.items()):
 parent=bpy.data.objects.new(n,None);c.objects.link(parent)
 for o in list(c.objects):
  if o!=parent:o.parent=parent
bpy.context.view_layer.update();meshes=[o for o in bpy.data.objects if o.type=='MESH'];tri=0;degen=0
for o in meshes:
 o.data.calc_loop_triangles();tri+=len(o.data.loop_triangles)
 for t in o.data.loop_triangles:
  a,b,c=[o.data.vertices[i].co for i in t.vertices]
  if (b-a).cross(c-a).length<1e-10:degen+=1
assert degen==0,('Degenerate triangles',degen)
bpy.ops.object.select_all(action='SELECT');asset=R/'E-town-square.glb'
bpy.ops.export_scene.gltf(filepath=str(asset),export_format='GLB',use_selection=True,export_cameras=False,export_lights=False)
meta={'title':'E 区 · 小镇客厅','plot':[85,55],'plazaCenter':PC,'plazaDiameter':36,'treeWellRadius':3.8,'ringSeatOuterRadius':5.1,'marketStalls':STALLS,'waterCenter':[28,7],'waterRadius':4.34,'waterDepth':.25,'portals':{'west':[-42.5,-2.5],'east':[42.5,-2.5],'north':[0,27.5],'south':[0,-27.5]},'mainPathWidth':4.5,'groups':list(h.C),'meshObjects':len(meshes),'triangles':tri,'degenerateTriangles':degen,'units':'metres','sourceAxes':'Z up, north +Y','glbAxes':'Y up, north -Z','sha256':hashlib.sha256(asset.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'status':'design-review'}
(R/'manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2));(R/'paving-layout.json').write_text(json.dumps({'positive':positive,'holes':holes,'quads':quadrecords}))
h.studio(scene);scene.cycles.samples=24;scene.render.resolution_x=1600;scene.render.resolution_y=1200
scene.camera=h.camera('Square overview',(100,-108,104),(0,-1,0),114)
views=[(scene,'overview.png')]
settings=[('02 Daily square',(100,-108,104),(0,-1,0),114,['Market_Fixtures','Market_Canopies','Event_Decor'],'daily.png'),('03 Plan',(0,-.001,125),(0,0,0),97,['Landmark_Canopy','Market_Canopies','Pergola_Roof'],'plan.png'),('04 Under the tree',(25,-29,21),(0,CY,1),26,['Landmark_Canopy'],'tree-seating.png'),('05 Weekend market',(-10,-29,25),(-29,-1,1),37,[],'market.png'),('06 Water and pergola',(59,-35,32),(28,-3,1),44,[],'water-pergola.png'),('07 Community corner',(8,-1,25),(-8,22,1),34,[],'community.png')]
for n,loc,target,scale,hide,f in settings:
 sc=scene.copy();sc.name=n;sc.use_fake_user=True;sc.camera=h.camera(n+' camera',loc,target,scale)
 for c in hide:sc.view_layers[0].layer_collection.children[c].exclude=True
 views.append((sc,f))
bpy.context.window.scene=scene
for scr in bpy.data.screens:
 for ar in scr.areas:
  if ar.type=='VIEW_3D':ar.spaces.active.shading.type='MATERIAL';ar.spaces.active.overlay.show_overlays=False;ar.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(R/'E-town-square.blend'))
for sc,f in views:
 sc.render.filepath=str(R/f);bpy.ops.render.render(write_still=True,scene=sc.name);print('RENDERED',f,flush=True)
print('COMPLETE',json.dumps(meta,ensure_ascii=False),flush=True)
