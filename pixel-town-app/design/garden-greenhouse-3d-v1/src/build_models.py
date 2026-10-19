import sys,math,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import model_helpers as h
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parent.parent
h.ROOT=ROOT
h.PALETTE.update({'tomato':'c96149','flowerPink':'d398aa','flowerYellow':'e3c363','lavender':'a095bd','gravel':'d4c8aa','soil':'897158','apple':'bf6750','pear':'c1bc68'})
h.init()
box,cyl,leaf,beam=h.box,h.cyl,h.leaf,h.beam

def plant(x,y,s=.8,c='Greenhouse_Interior'):
 h.plant(x,y,s,c)

def flower(x,y,mat='flowerPink',scale=1,c='Borders'):
 z=.55*scale
 cyl('Flower stem',x,y,z/2,.016*scale,z,'leaf',c)
 for k in range(5):
  a=k*math.tau/5;leaf('Flower petal',x+.105*scale*math.cos(a),y+.105*scale*math.sin(a),z,(.11*scale,.1*scale,.055*scale),mat,c)
 leaf('Flower centre',x,y,z+.02,(.045*scale,.045*scale,.04*scale),'flowerYellow',c)

def crop(x,y,kind,c,z=.23):
 if kind==0:
  for a in [0,1.6,3.2,4.8]:leaf('Cabbage leaf',x+.21*math.cos(a),y+.21*math.sin(a),z+.22,(.34,.27,.18),'leafLight',c)
  leaf('Cabbage heart',x,y,z+.36,(.22,.23,.23),'sage',c)
 elif kind==1:
  cyl('Tomato support',x,y,z+.8,.026,1.6,'wood',c)
  for dz in [.4,.8,1.15]:
   leaf('Tomato foliage',x,y,z+dz,(.34,.28,.25),'leaf',c)
   for dx in [-.24,.24]:leaf('Ripe tomato',x+dx,y-.18,z+dz,(.09,.09,.09),'tomato',c)
 elif kind==2:
  for a in [0,1.2,2.4,3.6,4.8]:
   o=leaf('Root crop foliage',x+.08*math.cos(a),y+.08*math.sin(a),z+.4,(.1,.16,.42),'leafLight',c);o.rotation_euler.y=.3*math.cos(a)
 else:
  for a in [0,1.5,3,4.5]:leaf('Herb foliage',x+.14*math.cos(a),y+.14*math.sin(a),z+.4,(.22,.19,.4),'leaf',c)

def bench(x,y,c='Rest'):
 box('Bench seat',x,y,.58,2.3,.65,.12,'wood',c)
 box('Bench back',x,y+.3,.96,2.3,.09,.72,'sage',c)
 for dx in [-.8,.8]:box('Bench support',x+dx,y,.30,.12,.52,.50,'darkgreen',c)

def plaque(t,x,y,w=2.6,c='Wayfinding'):
 for dx in [-w*.35,w*.35]:box('Sign post',x+dx,y,.60,.07,.07,1.2,'wood',c)
 h.sign(t,x,y,1.24,w,c)

# The 75 x 55 m block matches the original plan's 300 x 220 drawing units.
box('G site',0,0,-.18,75,55,.36,'grass','Ground')
# An open cross forms north, east and south access; paths reach the site edge.
box('North south garden walk',-3,0,.045,3.0,55,.09,'gravel','Paths')
box('East market connector',17.25,0,.045,40.5,3,.09,'gravel','Paths')
box('West field connector',-20.25,0,.045,31.5,3,.09,'gravel','Paths')
box('Southern service lane',0,-25,.05,75,4,.10,'stone','Paths')
box('Orchard loop east',34.4,13,.04,1.8,23,.08,'gravel','Paths')
box('Orchard loop north',15.375,24,.04,39.75,1.8,.08,'gravel','Paths')
# Split fence panels leave all four entrances open.
for y in [-27,27]:
 for a,b in [(-36.8,-5),(0,36.8)]:
  if y<0:continue
  for x in [a+i*2.5 for i in range(int((b-a)/2.5)+1)]:box('Boundary post',x,y,.65,.11,.11,1.3,'wood','Borders')
  for z in [.45,.95]:box('Boundary rail',(a+b)/2,y,z,b-a,.065,.075,'lightwood','Borders')
for x in [-36.8,36.8]:
 for a,b in [(-22,-2),(2,26)]:
  for y in [a+i*2.5 for i in range(int((b-a)/2.5)+1)]:box('Boundary post',x,y,.65,.11,.11,1.3,'wood','Borders')
  for z in [.45,.95]:box('Boundary rail',x,(a+b)/2,z,.065,b-a,.075,'lightwood','Borders')
# Greenhouse at the masterplan G01 footprint, 25.5 x 13 m.
gx,gy=-19.75,11.5;W,D=25.5,13;top=3.5;rise=2.8
box('Greenhouse slab',gx,gy,.10,W,D,.20,'stone','Greenhouse_Floor')
box('Greenhouse east access',-5,gy,.075,4,3,.15,'stone','Paths')
for i in range(9):
 x=gx-W/2+i*W/8
 for y in [gy-D/2,gy+D/2]:box('Greenhouse steel column',x,y,1.86,.10,.10,3.32,'sage','Greenhouse_Shell')
 for y in [gy-D/2,gy+D/2]:beam('Greenhouse roof rafter',(x,y,top),(x,gy,top+rise),.10,'sage','Greenhouse_Roof')
for y in [gy-D/2,gy+D/2]:
 box('Greenhouse plinth',gx,y,.43,W,.18,.46,'cream','Greenhouse_Shell')
 for i in range(8):box('Greenhouse side glass',gx-W/2+(i+.5)*W/8,y,2.05,W/8-.12,.025,2.76,'glass','Greenhouse_Shell')
 for z in [.70,2,top]:box('Greenhouse side rail',gx,y,z,W,.08,.07,'sage','Greenhouse_Shell')
# East doorway remains open at 2.4 m clear width; west facade is glazed.
for x in [gx-W/2,gx+W/2]:
 for side in [-1,1]:
  yc=gy+side*3.875;box('Greenhouse end glass',x,yc,1.92,.025,5.25,3.35,'glass','Greenhouse_Shell')
  for yy in [gy+side*1.25,gy+side*6.5]:box('Greenhouse entrance jamb',x,yy,1.86,.10,.10,3.32,'sage','Greenhouse_Shell')
 box('Greenhouse door lintel',x,gy,3.02,.10,2.5,.10,'sage','Greenhouse_Shell')
 box('Greenhouse transom',x,gy,3.28,.025,2.4,.42,'glass','Greenhouse_Shell')
 # Glazed triangular gable with real frame edges.
 me=bpy.data.meshes.new('Glass gable');me.from_pydata([(x,gy-D/2,top),(x,gy+D/2,top),(x,gy,top+rise)],[],[(0,1,2)]);me.materials.append(h.M['glass']);o=bpy.data.objects.new('Glass gable',me);h.col('Greenhouse_Roof').objects.link(o)
 if x<gx:box('Greenhouse west glazing',x,gy,1.60,.025,2.4,2.8,'glass','Greenhouse_Shell')
for side in [-1,1]:
 ang=-side*math.atan2(rise,D/2);sl=math.hypot(D/2,rise)
 for i in range(8):
  o=box('Glazed roof panel',gx-W/2+(i+.5)*W/8,gy+side*D/4,top+rise/2,W/8-.11,sl-.04,.025,'glass','Greenhouse_Roof');o.rotation_euler.x=ang
 for frac in [.33,.66]:box('Roof longitudinal purlin',gx,gy+side*D/2*frac,top+rise*(1-frac),W,.075,.075,'sage','Greenhouse_Roof')
box('Greenhouse ridge',gx,gy,top+rise,W+.12,.14,.14,'sage','Greenhouse_Roof')
# Six perimeter growing benches and two low central nursery beds; aisles remain open.
for side in [-1,1]:
 for xi in [-28,-20,-12]:
  y=gy+side*4.5
  box('Growing bench top',xi,y,.92,6,1.5,.10,'lightwood','Greenhouse_Interior')
  for dx in [-2.5,2.5]:
   for dy in [-.55,.55]:box('Growing bench leg',xi+dx,y+dy,.51,.09,.09,.82,'sage','Greenhouse_Interior')
  for j in range(6):
   for dy in [-.38,.38]:
    xx=xi-2.5+j
    cyl('Seedling pot',xx,y+dy,1.06,.18,.18,'roof','Greenhouse_Interior')
    leaf('Seedling leaves',xx,y+dy,1.35,(.25,.22,.32),'leafLight','Greenhouse_Interior')
for x in [-26,-17]:
 box('Indoor herb bed',x,gy,.33,6,1.6,.36,'wood','Greenhouse_Interior')
 box('Indoor herb soil',x,gy,.52,5.8,1.4,.05,'soil','Greenhouse_Interior')
 for i in range(7):crop(x-2.5+i*.8,gy,3,'Greenhouse_Interior',.54)
plaque('G01  四季温室',gx,4.5,3.3)
# Four outdoor rotation plots, with 3 m separating paths.
for i,(x,y) in enumerate([(-27,-7.5),(-13,-7.5),(-27,-18),(-13,-18)]):
 c='Fields';box('Rotation plot %d'%(i+1),x,y,.15,11,7.5,.24,'soil',c)
 for yy in [y-3.85,y+3.85]:box('Low timber field edge',x,yy,.21,11.3,.12,.32,'wood',c)
 for xx in [x-5.6,x+5.6]:box('Low timber field edge',xx,y,.21,.12,7.6,.32,'wood',c)
 for row in range(5):
  yy=y-2.7+row*1.35;box('Drip irrigation line',x,yy,.29,10.5,.025,.025,'darkgreen',c)
  for j in range(9):crop(x-4.6+j*1.15,yy,i,c,.28)
 plaque(['01  叶菜轮作','02  茄果轮作','03  根茎轮作','04  香草轮作'][i],x,y-3.58,2.6)
box('Field cross path',-20,-12.75,.04,29,2.5,.08,'gravel','Paths')
box('Field centre path',-20,-13.4,.04,2.5,20,.08,'gravel','Paths')
# Orchard: nine fruit trees, with visible harvest and varied scale.
for row,y in enumerate([7,14.4,21]):
 for j,x in enumerate([9,19.7,29]):
  s=1.35+.13*((j+row)%3)
  cyl('Fruit tree trunk',x,y,1.35*s,.18,2.7*s,'wood','Orchard')
  for dx,dy,dz in [(0,0,3.1),(-.7,.3,2.8),(.8,.2,2.7),(0,-.7,2.65)]:leaf('Fruit tree crown',x+dx*s,y+dy*s,dz*s,(1.35*s,1.25*s,1.3*s),'leaf' if j%2 else 'leafLight','Orchard')
  for k in range(10):
   a=k*2.4;leaf('Orchard fruit',x+1.9*s*math.cos(a),y+1.8*s*math.sin(a),(2.8+.35*math.sin(k))*s,(.14,.14,.17),'apple' if (j+row)%2 else 'pear','Orchard')
  cyl('Mulch ring',x,y,.025,1.55,.05,'soil','Orchard',24)
plaque('果园  ·  随季采收',19,3,3.2)
# Tool/packing house: masterplan G02 footprint, east plot, west-facing entrance.
sx,sy=22.375,-15;SW,SD=18.25,12
box('Tool house slab',sx,sy,.12,SW,SD,.24,'stone','Tool_Floor')
# Rear and side walls; front is towards south, with wide entrance plus west service door.
h.OX=sx;h.Z=0
h.wall_y('Tool north wall',sy+6,-SW/2,SW/2,[(0,3,1.1,2.8)],'Tool_Shell',.18,3.6)
h.wall_y('Tool south wall',sy-4,-SW/2,SW/2,[(0,2.6,0,3.0),(-5.5,2.6,1.1,2.8),(5.5,2.6,1.1,2.8)],'Tool_Front',.18,3.6)
h.wall_x('Tool west wall',-SW/2,sy-3.9,sy+5.9,[(sy,2.2,0,3.0)],'Tool_Shell',.18,3.6)
h.wall_x('Tool east wall',SW/2,sy-3.9,sy+5.9,[(sy,2.6,1.1,2.8)],'Tool_Shell',.18,3.6)
h.OX=0
# Shallow pitched roof, with open south work porch beneath the overhang.
for side in [-1,1]:
 o=box('Tool pitched roof',sx,sy+side*3.25,4.35,SW+.8,math.hypot(6.5,1.35),.14,'darkgreen','Tool_Roof');o.rotation_euler.x=-side*math.atan2(1.35,6.5)
box('Tool ridge',sx,sy,5.06,SW+1,.17,.16,'darkgreen','Tool_Roof')
# Continuous upper infill meets the sloping roof at both long facades.
for yy in [sy-4,sy+6]:
 roofz=5.025-abs(yy-sy)*1.35/6.5
 box('Tool eaves infill',sx,yy,(3.78+roofz)/2,SW,.18,max(.01,roofz-3.78),'cream','Tool_Roof')
# Close the high gables above the wall to avoid open seams.
for x in [sx-SW/2,sx+SW/2]:
 me=bpy.data.meshes.new('Tool gable');me.from_pydata([(x,sy-4,3.78),(x,sy+6,3.78),(x,sy+6,3.78+1.35*(.5/6.5)),(x,sy,5.025),(x,sy-4,3.78+1.35*(2.5/6.5))],[],[(0,1,2,3,4)]);me.materials.append(h.M['cream']);o=bpy.data.objects.new('Tool gable infill',me);h.col('Tool_Roof').objects.link(o)
for x in [sx-SW/2+.25,sx+SW/2-.25]:box('Porch column',x,sy-5.65,1.94,.16,.16,3.40,'wood','Tool_Front')
# Potting bench and packing table, stocked shelves, hand tools.
for x in [sx-5.5,sx+5.5]:
 box('Work table',x,sy+3.5,1.07,4.5,1.2,.12,'lightwood','Tool_Interior')
 for dx in [-1.9,1.9]:box('Worktable base',x+dx,sy+3.5,.60,.12,1,.82,'sage','Tool_Interior')
 for j in range(4):cyl('Stored terracotta pot',x-1.4+j*.85,sy+3.5,1.30,.25,.34,'roof','Tool_Interior')
for z in [.4,1.3,2.2]:
 box('Storage shelf',sx+7.4,sy,.18+z,1.1,5.3,.08,'wood','Tool_Interior')
 for j in range(4):box('Harvest crate',sx+7.4,sy-1.8+j*1.2,z+.43,.75,.85,.45,'lightwood','Tool_Interior')
for y in [sy-2.5,sy+2.5]:box('Shelf upright',sx+7.4,y,1.6,.08,.1,2.9,'sage','Tool_Interior')
for j in range(6):
 x=sx-7+j*.7;cyl('Tool handle',x,sy+5.7,1.5,.035,2.2,'wood','Tool_Interior');box('Spade blade',x,sy+5.7,.40,.32,.07,.40,'metal','Tool_Interior')
box('Packing island',sx,sy,.85,4,1.8,1.22,'sage','Tool_Interior');box('Packing top',sx,sy,1.50,4.1,1.9,.08,'lightwood','Tool_Interior')
plaque('G02  园艺工具屋',sx-5,sy-6.35,3.6)
box('Tool west service approach',5.875,sy,.06,14.75,2.4,.12,'stone','Paths')
box('Tool south service approach',sx,-23,.06,3,4,.12,'stone','Paths')
# Wash/rainwater point outside; compost bins west of shed near the service lane.
for x in [sx+7.8]:
 cyl('Rainwater tank',x,sy+7.9,1.2,1.05,2.4,'sage','Utilities',24)
 cyl('Tank lid',x,sy+7.9,2.43,1.10,.09,'darkgreen','Utilities',24)
box('Wash sink stand',sx+3.9,sy+7.7,.66,2.4,.8,1.2,'wood','Utilities');box('Wash sink basin',sx+3.9,sy+7.7,1.30,2.5,.85,.12,'metal','Utilities')
cyl('Water tap',sx+3.9,sy+8,1.56,.035,.46,'metal','Utilities')
for i in range(3):
 x=3+i*2.9;y=-20
 box('Compost soil',x,y,.5,2.2,2.2,.9,'soil','Utilities')
 for xx in [x-1.2,x+1.2]:
  for z in [.3,.7,1.1]:box('Compost slat',xx,y,z,.08,2.5,.25,'wood','Utilities')
 for z in [.3,.7,1.1]:box('Compost rear slat',x,y+1.2,z,2.4,.08,.25,'wood','Utilities')
plaque('堆肥与循环',6,-22,2.8)
# A shaded work/rest terrace between field, greenhouse and orchard.
box('Garden rest deck',4.8,-6.5,.10,7,6,.20,'lightwood','Rest')
for x in [1.7,7.9]:
 for y in [-9.1,-3.9]:box('Pergola upright',x,y,1.63,.13,.13,3.05,'wood','Rest')
for i in range(12):box('Pergola lath',1.4+i*.62,-6.5,3.2,.10,6,.12,'wood','Rest')
bench(4.8,-8.2);cyl('Garden meeting table',4.8,-5.7,.98,.9,.12,'wood','Rest');cyl('Garden table support',4.8,-5.7,.56,.15,.8,'wood','Rest')
box('Rest access',-.1,-6.5,.07,2.8,2,.14,'gravel','Paths')
# Soft mixed flower edges on unused margins, avoiding a crop-like grid.
for j in range(60):
 x=-33.4+(j%20)*1.30+.45*math.sin(j*2.4);y=22.8+1.3*math.sin(j*1.73)
 flower(x,y,['white','flowerPink','lavender','flowerYellow'][j%4],.8+.25*(j%3))
for x,y in [(-34,21),(-8,23),(33,-5),(34,-10),(34,-20)]:
 leaf('Soft boundary shrub',x,y,.6,(1.1,.9,.7),'leafLight','Borders')
for i in range(30):
 a=i*2.4;x=33.6+.8*math.cos(a);y=-4-i*.53
 flower(x,y,['white','flowerYellow','lavender'][i%3],1,'Borders')
plaque('G  田园与温室',-7,25,3.7)

# Partition all path rectangles into non-overlapping strips: no coplanar junction faces.
pathcol=h.C['Paths'];rects=[]
for o in list(pathcol.objects):
 rects.append((o.location.x-o.dimensions.x/2,o.location.x+o.dimensions.x/2,o.location.y-o.dimensions.y/2,o.location.y+o.dimensions.y/2,o.data.materials[0].name))
 bpy.data.objects.remove(o,do_unlink=True)
xs=sorted(set(round(r[i],5) for r in rects for i in [0,1]));ys=sorted(set(round(r[i],5) for r in rects for i in [2,3]))
for ya,yb in zip(ys,ys[1:]):
 runs=[]
 for xa,xb in zip(xs,xs[1:]):
  xc,yc=(xa+xb)/2,(ya+yb)/2;hits=[r for r in rects if r[0]-1e-5<xc<r[1]+1e-5 and r[2]-1e-5<yc<r[3]+1e-5]
  if hits:
   mat=hits[-1][4]
   if runs and runs[-1][2]==mat and abs(runs[-1][1]-xa)<1e-5:runs[-1]=(runs[-1][0],xb,mat)
   else:runs.append((xa,xb,mat))
 for xa,xb,mat in runs:box('Joined garden path',(xa+xb)/2,(ya+yb)/2,.05,xb-xa,yb-ya,.10,mat,'Paths')
# Independent grouped assets for Blender editing and GLB visibility controls.
scene=bpy.context.scene;scene.name='01 Whole block';scene.unit_settings.system='METRIC'
for name,c in list(h.C.items()):
 parent=bpy.data.objects.new(name,None);c.objects.link(parent)
 for o in list(c.objects):
  if o!=parent:o.parent=parent
bpy.context.view_layer.update()
meshes=[o for o in bpy.data.objects if o.type=='MESH'];tri=0;degen=0
for o in meshes:
 o.data.calc_loop_triangles();tri+=len(o.data.loop_triangles)
 for v in o.data.vertices:assert all(math.isfinite(x) for x in v.co)
 for t in o.data.loop_triangles:
  a,b,c=[o.data.vertices[k].co for k in t.vertices]
  if (b-a).cross(c-a).length<1e-10:degen+=1
assert not degen
bpy.ops.object.select_all(action='SELECT');asset=ROOT/'G-garden-greenhouse.glb'
bpy.ops.export_scene.gltf(filepath=str(asset),export_format='GLB',use_selection=True,export_cameras=False,export_lights=False)
meta={'title':'G 区 · 田园与温室','plot':[75,55],'greenhouse':[25.5,13],'toolHousePlot':[18.25,12],'rotationPlots':4,'fruitTrees':9,'greenhouseBenches':6,'meshObjects':len(meshes),'triangles':tri,'degenerateTriangles':degen,'sha256':hashlib.sha256(asset.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'status':'design-review','units':'metres','sourceAxes':'Z up, north +Y','glbAxes':'Y up, north -Z','groups':list(h.C.keys()),'portals':{'north':[-3,27.5],'east':[37.5,0],'south':[-3,-27.5],'serviceWest':[-37.5,-25],'serviceEast':[37.5,-25]}}
(ROOT/'manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
h.studio(scene);scene.cycles.samples=16;scene.render.resolution_x=1600;scene.render.resolution_y=1200
# Enlarge lighting and fit complete site in an orthographic view.
scene.camera=h.camera('Whole block camera',(83,-100,95),(0,0,0),100)
views=[(scene,'overview.png')]
for name,loc,target,scale,hide,file in [
 ('02 Master plan',(0,-.001,110),(0,0,0),85,[],'plan.png'),
 ('03 Greenhouse interior',(8,-17,28),(gx,gy,1),35,['Greenhouse_Roof'],'greenhouse-interior.png'),
 ('04 Tool house interior',(44,-40,26),(sx,sy,1),29,['Tool_Roof','Tool_Front'],'tool-interior.png'),
 ('05 Fields and orchard',(65,-70,60),(0,-2,0),85,[],'fields-orchard.png')]:
 sc=scene.copy();sc.name=name;sc.use_fake_user=True;sc.camera=h.camera(name+' camera',loc,target,scale)
 for n in hide:sc.view_layers[0].layer_collection.children[n].exclude=True
 views.append((sc,file))
bpy.context.window.scene=scene
for scr in bpy.data.screens:
 for ar in scr.areas:
  if ar.type=='VIEW_3D':ar.spaces.active.shading.type='MATERIAL';ar.spaces.active.overlay.show_overlays=False;ar.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'G-garden-greenhouse.blend'))
for sc,file in views:
 sc.render.filepath=str(ROOT/file);bpy.ops.render.render(write_still=True,scene=sc.name);print('RENDERED',file,flush=True)
print('COMPLETE',json.dumps(meta,ensure_ascii=False),flush=True)
