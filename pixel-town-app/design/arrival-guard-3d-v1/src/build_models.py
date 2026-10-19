import bpy,sys,math,json,hashlib,os
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
import model_helpers as h
R=Path(__file__).resolve().parents[1]
h.PALETTE.update({'paving':'e2dac7','asphalt':'a7ada6','red':'b95748','rubber':'37433f','windshield':'688d92','amber':'e4b968','linen':'e1d4b7'})
h.init();box,cyl,leaf,beam=h.box,h.cyl,h.leaf,h.beam
# Furniture helpers are redirected into the currently selected building collection.
h.group=lambda part: ACTIVE
ACTIVE='Inn_L01_Furniture'

def mesh(n,vs,fs,mat,c):
 m=bpy.data.meshes.new(n);m.from_pydata(vs,[],fs);m.materials.append(h.M[mat]);m.update();o=bpy.data.objects.new(n,m);h.col(c).objects.link(o);return o

def rotate_group_objects(objs,cx,cy,a):
 for o in objs:
  x,y=o.location.x-cx,o.location.y-cy;o.location.x=cx+math.cos(a)*x-math.sin(a)*y;o.location.y=cy+math.sin(a)*x+math.cos(a)*y;o.rotation_euler.z+=a

def tree(x,y,s=1):
 cyl('Tree trunk',x,y,1.5*s,.14*s,3*s,'wood','Planting')
 for dx,dy,dz in [(0,0,3.2),(.7,0,2.8),(-.6,.2,2.7),(0,-.65,2.8)]:leaf('Tree crown',x+dx*s,y+dy*s,dz*s,(1.05*s,1*s,1.1*s),'leafLight' if dx==0 else 'leaf','Planting')
def flowers(x,y,i=0):
 for j in range(4):
  a=j*2.4+i;xx=x+.25*math.cos(a);yy=y+.25*math.sin(a);z=.42+.07*(j%3);cyl('Flower stem',xx,yy,z/2,.013,z,'leaf','Planting')
  for k in range(5):
   a=k*math.tau/5;leaf('Flower petal',xx+.08*math.cos(a),yy+.08*math.sin(a),z,(.09,.08,.045),['flowerPink','flowerYellow','white','lavender'][i%4],'Planting')
def bench(x,y,w=2.6,rot=0,c='Street_Furniture'):
 before=set(h.col(c).objects);box('Bench seat',x,y,.54,w,.6,.13,'lightwood',c);box('Bench back',x,y+.27,.9,w,.09,.62,'sage',c)
 for dx in [-w*.36,w*.36]:box('Bench foot',x+dx,y,.28,.12,.46,.48,'darkgreen',c)
 rotate_group_objects(set(h.col(c).objects)-before,x,y,rot)
def plaque(t,x,y,w=3,c='Wayfinding'):
 for dx in [-w*.36,w*.36]:box('Signpost',x+dx,y,.66,.08,.08,1.32,'wood',c)
 h.sign(t,x,y,1.35,w,c)
def rect_tiles(rects):
 xs=sorted(set(v for r in rects for v in [r[0],r[2]]));ys=sorted(set(v for r in rects for v in [r[1],r[3]]));out=[]
 for ya,yb in zip(ys,ys[1:]):
  spans=[]
  for xa,xb in zip(xs,xs[1:]):
   if any(r[0]<=(xa+xb)/2<=r[2] and r[1]<=(ya+yb)/2<=r[3] for r in rects):
    if spans and abs(spans[-1][1]-xa)<1e-6:spans[-1][1]=xb
    else:spans.append([xa,xb])
  out += [(a,ya,b,yb) for a,b in spans]
 return out
# Original I rectangle: (825,720,215,220) / 4 => 53.75 x 55m.
box('I terrain',0,0,-.28,53.75,55,.56,'grass','Ground')
# Separate vehicle apron and eastern access road; matching top elevations.
VEHICLE=[(18.5,-27.5,26.875,27.5),(2.375,-21.5,18.5,-8.75)]
for i,(x0,y0,x1,y1) in enumerate(rect_tiles(VEHICLE)):box('Vehicle surface %02d'%i,(x0+x1)/2,(y0+y1)/2,.025,x1-x0,y1-y0,.05,'asphalt','Vehicle_Routes')
box('South approach context',22.6875,-31,.015,8.375,7,.06,'asphalt','Approach')
for y in [-32,-27,-22,-5,0,5,10,15,20,25]:box('Access road dashed line',23,y,.059,.10,1.65,.008,'white','Road_Markings')
# White edge line with open emergency access between y=-21.5 and -8.75.
for ya,yb in [(-27.5,-21.5),(-8.75,27.5)]:box('Road edge marking',18.65,(ya+yb)/2,.059,.10,yb-ya,.008,'white','Road_Markings')
box('East road edge marking',26.55,0,.059,.10,55,.008,'white','Road_Markings')
# Pedestrian path wraps the western building fronts; no path is laid across the garage apron.
PATH_INPUT=[(-26.3,-27.5,-23.3,27.5),(-26.3,23,17.5,26),(-26.875,9.25,-22.3,11.75),(-26.3,-3,17.5,1),
 (-23.4,-6,-20.9,-3),(-23.3,-6,-9,-4),(-9.8,-8.8,-7.2,-4),(4,-4,7,27.5),
 (7,6,18.5,8.7),(15.5,6,18.5,23),(-3,18,0,23)]
PATHS=rect_tiles(PATH_INPUT)
for i,(x0,y0,x1,y1) in enumerate(PATHS):box('Pedestrian paving %02d'%i,(x0+x1)/2,(y0+y1)/2,.065,x1-x0,y1-y0,.13,'paving','Paths')
# West inn door forecourt, north patio and south street frontage.
box('Inn west entrance landing',-22.9,10.5,.105,1.05,3,.21,'stone','Inn_Entrance')
box('Inn north patio',-10.5,20.4,.095,17,4,.19,'lightwood','Inn_Terrace')
for x in [-17.5,-3.5]:
 for y in [18.75,22.05]:box('Patio pergola post',x,y,1.68,.11,.11,3.16,'wood','Inn_Terrace')
for x in [-17.5+i*.7 for i in range(21)]:box('Patio pergola lath',x,20.4,3.27,.07,4,.10,'wood','Inn_Terrace')
bench(-12,21.2,2.4,c='Inn_Terrace');bench(-6,21.2,2.4,c='Inn_Terrace')
# Inn follows original I01 footprint: 23 x 15, center (-10.875,10.5), west entry.
IX,IY=-10.875,10.5
box('Inn ground floor',IX,IY,.09,23,15,.18,'lightwood','Inn_L01_Floor')
# Upper slab has a real stair opening: x[-22.15,-18.05], y[11.7,17.75].
HOLE=[-22.15,11.7,-18.05,17.75]
for n,x0,y0,x1,y1 in [('main',-18.05,3,.625,18),('west south',-22.375,3,-18.05,11.7),('west edge',-22.375,11.7,-22.15,18),('north edge',-22.15,17.75,-18.05,18)]:box('Inn upper slab '+n,(x0+x1)/2,(y0+y1)/2,3.47,x1-x0,y1-y0,.22,'lightwood','Inn_L02_Floor')
for level,z in [(1,0),(2,3.4)]:
 h.Z=z;p='Inn_L%02d_'%level
 h.wall_y('Inn south facade',3,-22.375,.625,[(-19.5,2,1,2.75),(-14.7,2.5,1,2.75),(-8.65,2.5,1,2.75),(-2.6,2.5,1,2.75)],p+'South',.20,3.18)
 h.wall_y('Inn north facade',18,-22.375,.625,[(-20.1,2,1,2.75),(-14.7,2.5,1,2.75),(-8.65,2.5,1,2.75),(-1.5,1.5,0,2.5)] if level==1 else [(-20.1,2,1,2.75),(-14.7,2.5,1,2.75),(-8.65,2.5,1,2.75),(-2.6,2.5,1,2.75)],p+'North',.2,3.18)
 h.wall_x('Inn west facade',-22.275,3.1,17.9,[(6.4,2,1,2.75),(10.5,2.0,0,2.6),(15.4,2,1,2.75)] if level==1 else [(6.4,2,1,2.75),(10.5,1.8,1,2.75),(15.4,2,1,2.75)],p+'West',.2,3.18)
 h.wall_x('Inn east facade',.525,3.1,17.9,[(6.2,2,1,2.75),(10.5,1.7,1,2.75),(15.2,2,1.1,2.75)],p+'East',.2,3.18)
 # Plaster string courses attach to wall faces, without covering any opening.
 for y in [2.88,18.12]:box('Inn facade band',IX,y,3.25,23.3,.07,.16,'white',p+('South' if y<10 else 'North'))
h.Z=0
# Custom low pitched sage roof, ridge east/west, closes gables.
base,half,rise=6.98,8.05,1.9
box('Inn eaves fascia',IX,IY,base-.13,23.6,15.6,.18,'white','Inn_Roof')
for side in [-1,1]:
 a=-side*math.atan2(rise,half);o=box('Inn roof slope',IX,IY+side*half/2,base+rise/2,24,math.hypot(half,rise),.16,'sage','Inn_Roof');o.rotation_euler.x=a
 for i in range(43):
  o=box('Inn standing seam',IX-11.8+i*.56,IY+side*half/2,base+rise/2+.10,.023,math.hypot(half,rise),.025,'sage','Inn_Roof');o.rotation_euler.x=a
box('Inn ridge',IX,IY,base+rise+.04,24.05,.2,.17,'darkgreen','Inn_Roof')
for x in [-22.3,.55]:mesh('Inn solid gable',[(x-.05,3,base),(x-.05,18,base),(x-.05,IY,base+rise-.10),(x+.05,3,base),(x+.05,18,base),(x+.05,IY,base+rise-.10)],[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)],'cream','Inn_Roof')
# West porch and welcoming sign, faces commercial street.
box('Inn west canopy',-23,10.5,2.98,1.65,3.5,.16,'sage','Inn_Entrance')
for y in [8.95,12.05]:box('Inn porch post',-23.65,y,1.52,.11,.11,2.95,'wood','Inn_Entrance')
before=set(h.col('Inn_Entrance').objects);h.sign('溪畔旅店',-22.42,10.5,2.70,2.6,'Inn_Entrance');rotate_group_objects(set(h.col('Inn_Entrance').objects)-before,-22.42,10.5,-math.pi/2)
# Ground floor: reception, breakfast dining, lounge and separate pantry.
ACTIVE='Inn_L01_Furniture'
box('Reception counter',-18,6.7,.76,4.1,.85,1.16,'sage',ACTIVE);box('Reception counter top',-18,6.7,1.38,4.2,.95,.10,'lightwood',ACTIVE)
box('Reception terminal',-18.7,6.75,1.63,.55,.08,.45,'dark',ACTIVE);h.sign('RECEPTION',-18,6.21,.99,2.4,ACTIVE)
box('Key rack',-20,3.18,1.8,2.4,.1,.9,'wood',ACTIVE)
for i in range(6):cyl('Room key hook',-20.85+i*.34,3.04,1.8,.035,.09,'gold',ACTIVE)
for x,y in [(-12.5,5.7),(-6.5,5.7)]:h.table(x,y)
h.sofa(-10.5,15.3,3.3);h.sofa(-15.1,15.3,2.5);h.desk(-4.4,9)
# Pantry at northeast, accessible from lobby and rear door.
h.wall_x('Pantry partition',-4,12,17.9,[(13,1.1,0,2.45)],'Inn_L01_Interior',.12,3.05)
h.wall_y('Pantry south partition',12,-4,.42,[(-1.5,1.3,0,2.45)],'Inn_L01_Interior',.12,3.05)
h.kitchen(-2.3,16.9,2.7)
for x,y in [(-21.1,8.1),(-4.8,17),(-12,10)]:h.plant(x,y,.7,ACTIVE)
# Twin-run stair, 20 risers, landing, continuous upper opening.
STEPS=[]
for i in range(10):
 z=.18+(i+1)*.17;y=12.0+i*.34
 box('Inn stair lower %02d'%i,-21.22,y,z-.065,1.5,.34,.13,'wood','Inn_Stair');STEPS.append(z)
 z=1.88+(i+1)*.17;y=15.06-i*.34
 box('Inn stair upper %02d'%i,-19.4,y,z-.065,1.5,.34,.13,'wood','Inn_Stair');STEPS.append(z)
box('Inn intermediate landing',-20.3,16.32,1.815,3.42,2.18,.13,'lightwood','Inn_Stair')
beam('Stair lower outside handrail',(-22,11.85,1.24),(-22,15.45,2.94),.045,'wood','Inn_Stair')
beam('Stair upper outside handrail',(-18.6,15.45,2.94),(-18.6,11.85,4.64),.045,'wood','Inn_Stair')
for i in range(0,10,2):
 for x,y,z in [(-22,12+i*.34,.35+i*.17),(-18.6,15.06-i*.34,2.05+i*.17)]:box('Stair baluster',x,y,z+.49,.035,.035,.98,'darkgreen','Inn_Stair')
h.rail_x(-18.05,14.72,3.58,6.04,'Inn_L02_Rails');h.rail_y(-20.1,17.75,3.58,4.1,'Inn_L02_Rails')
# Six ensuite rooms on floor 2; central 2.4m corridor connects to stair.
h.Z=3.4;ACTIVE='Inn_L02_Furniture';ROOMS=[]
for y in [9.3,11.7]:h.wall_y('Guest corridor wall',y,-18,.425,[(-15.5,1,0,2.45),(-9.4,1,0,2.45),(-3.3,1,0,2.45)],'Inn_L02_Interior',.12,3.05)
for x in [-18,-11.9,-5.8]:
 for ya,yb in [(3.1,9.24),(11.76,17.9)]:h.wall_x('Guest room divider',x,ya,yb,[],'Inn_L02_Interior',.12,3.05)
for row in [0,1]:
 for j in range(3):
  x0=-18+j*6.1;x1=x0+6.1;ya,yb=(3.1,9.24) if row==0 else (11.76,17.9);room_id=str(201+row*3+j)
  # Bathroom in east outer corner of each room, wall stops short of window.
  by=4.36 if row==0 else 16.64;bx=x1-1.39
  box('Ensuite floor '+room_id,bx,by,.20,2.45,2.35,.035,'tile','Inn_L02_Interior')
  h.wall_x('Ensuite side '+room_id,x1-2.68,by-1.21,by+1.21,[(by,.86,0,2.25)],'Inn_L02_Interior',.10,2.8)
  for yy in [by-1.21,by+1.21]:box('Ensuite end '+room_id,bx,yy,1.58,2.58,.10,2.8,'cream','Inn_L02_Interior')
  h.bath(bx,by);bedy=5.1 if row==0 else 15.45;h.bed(x0+1.52,bedy,1.6)
  h.wardrobe(x1-1.23,8.65 if row==0 else 12.35,1.45)
  h.desk(x1-1.55,6.8 if row==0 else 14.1)
  # Number signs face into corridor, never cover door clear opening.
  sy=9.38 if row==0 else 11.62;before=set(h.col(ACTIVE).objects);h.sign(room_id,x0+3.6,sy,2.45,.72,ACTIVE)
  if row==0:rotate_group_objects(set(h.col(ACTIVE).objects)-before,x0+3.6,sy,math.pi)
  ROOMS.append({'id':room_id,'floor':2,'bounds':[x0,ya,x1,yb],'door':[x0+2.5,9.3 if row==0 else 11.7],'ensuite':True})
h.Z=0
# Fire station at original I02: 25 x 12.75, east-facing engine bays.
FX,FY=-10.125,-15.125
box('Fire station floor',FX,FY,.09,25,12.75,.18,'stone','Fire_Floor')
h.wall_y('Station south wall',-21.5,-22.625,2.375,[(-19,2.3,1.4,3),(-8,3.2,2.1,3.65)],'Fire_South',.22,4.5)
h.wall_y('Station north wall',-8.75,-22.625,2.375,[(-19,2.3,1.1,2.8),(-8.5,1.5,0,2.6),(-2.5,2.3,2.1,3.65)],'Fire_North',.22,4.5)
h.wall_x('Station west wall',-22.515,-21.39,-8.86,[(-18.2,1.6,1.4,2.9),(-11.8,1.6,1.4,2.9)],'Fire_West',.22,4.5)
h.wall_x('Station east bay frame',2.265,-21.39,-8.86,[(-18.2,4.65,0,3.85),(-12.05,4.65,0,3.85)],'Fire_East',.22,4.5)
# Crew room / dispatch partition with actual openings into both bays.
h.wall_x('Garage support partition',-14,-21.38,-8.87,[(-18.2,1.15,0,2.5),(-11.6,1.15,0,2.5)],'Fire_Interior',.14,3.1)
h.wall_y('Crew dispatch partition',-15.15,-22.4,-14.08,[(-17.1,1.1,0,2.45)],'Fire_Interior',.14,3.1)
ACTIVE='Fire_Furniture';h.sofa(-19,-18.3,3);h.table(-17,-12.1)
h.desk(-20,-10);h.wardrobe(-20.8,-20.65,2)
box('Dispatch map',-18,-8.88,2.1,3,.045,1.3,'sage',ACTIVE)
for i in range(4):box('Dispatch route',-19+i*.6,-8.912,2.1,.025,.015,1.0,'linen',ACTIVE)
# 4 lockers, protective coats, helmet shelf and hose racks in clear rear service area.
for i in range(4):
 x=-12.8+i*.86;box('Gear locker',x,-9.23,1.32,.75,.6,2.28,'red',ACTIVE);box('Locker inset',x,-9.55,1.3,.60,.025,1.95,'sage',ACTIVE);box('Coat reflective band',x,-9.58,1.1,.51,.025,.075,'amber',ACTIVE);leaf('Fire helmet',x,-9.25,2.64,(.26,.25,.18),'amber',ACTIVE)
for y in [-20.8,-19.6]:
 cyl('Hose roll',-12.8,y,.47,.30,.6,'linen',ACTIVE);cyl('Hose connector',-12.8,y,.79,.10,.05,'metal',ACTIVE)
box('Garage workbench',-5.2,-20.94,.70,3.6,.7,1.1,'wood',ACTIVE)
for x in [-6.5,-5.8,-5.1]:box('Service tool',x,-21.32,1.9,.06,.05,.75,'metal',ACTIVE)
# Raised roller doors retain a visible rolled head, do not obstruct bay openings.
for y in [-18.2,-12.05]:
 o=cyl('Rolled bay door',2.07,y,4.13,.22,4.7,'metal','Fire_East');o.rotation_euler.x=math.pi/2
 for yy in [y-2.36,y+2.36]:box('Bay red jamb',2.43,yy,2,.16,.13,3.85,'red','Fire_East')
 # Parked position marked in first bay, second available for another vehicle.
 for yy in [y-1.68,y+1.68]:box('Engine bay guide',-5.7,yy,.187,13,.055,.009,'white','Fire_Markings')
box('Fire roof slab',FX,FY,4.82,25.45,13.2,.24,'white','Fire_Roof')
for x in [-22.63,2.38]:box('Fire roof parapet',x,FY,5.09,.16,13.0,.36,'cream','Fire_Roof')
for y in [-21.61,-8.64]:box('Fire roof parapet',FX,y,5.09,24.98,.16,.36,'cream','Fire_Roof')
box('Fire east red fascia',2.48,FY,4.57,.18,12.8,.34,'red','Fire_East')
before=set(h.col('Fire_East').objects);h.sign('溪畔消防 · 119',2.59,FY,4.55,5.4,'Fire_East');rotate_group_objects(set(h.col('Fire_East').objects)-before,2.59,FY,math.pi/2)
h.sign('值守 / 整备',-8.5,-8.60,2.78,2.9,'Fire_North')
# Apron keep-clear boundary, separated from bus bay 14.75m farther north.
for y in [-21.15,-9.1]:box('Apron keep clear line',10.5,y,.059,15.5,.10,.008,'amber','Road_Markings')
for i in range(5):
 o=box('Apron hatched edge',3.8+i*2.5,-20.6,.059,1.4,.08,.008,'amber','Road_Markings');o.rotation_euler.z=math.pi/4
# Fire engine: local x longitudinal, front east. Static display model.
def fire_engine(x,y):
 c='Fire_Engine';box('Engine chassis',x,y,.66,7.6,2.38,.38,'rubber',c)
 box('Engine equipment body',x-1.1,y,1.58,5.05,2.38,1.68,'red',c);box('Engine cab',x+2.6,y,1.65,2.1,2.45,1.88,'red',c)
 box('Engine windshield',x+3.665,y,2.1,.035,2.18,.76,'windshield',c)
 for s in [-1,1]:
  box('Engine cab side glass',x+2.58,y+s*1.24,2.14,1.62,.03,.73,'windshield',c)
  box('Engine reflective side',x-1.1,y+s*1.204,1.21,5.1,.035,.13,'linen',c)
  for xx in [-2.8,-1.2,.4]:
   box('Engine equipment shutter',x+xx,y+s*1.23,1.75,1.42,.04,1.18,'metal',c)
   for z in [1.3,1.5,1.7,1.9,2.1]:box('Shutter rib',x+xx,y+s*1.259,z,1.38,.025,.024,'white',c)
  for xx in [-2.65,2.45]:
   o=cyl('Engine tire',x+xx,y+s*1.21,.65,.57,.23,'rubber',c);o.rotation_euler.x=math.pi/2
   o=cyl('Engine hub',x+xx,y+s*1.35,.65,.26,.035,'metal',c);o.rotation_euler.x=math.pi/2
  box('Engine mirror arm',x+3.1,y+s*1.4,2.0,.10,.36,.06,'metal',c);box('Engine mirror',x+3.1,y+s*1.6,2.08,.12,.10,.3,'dark',c)
 for yy in [-.8,.8]:box('Engine headlamp',x+3.7,y+yy,1.05,.055,.40,.25,'white',c)
 box('Engine bumper',x+3.77,y,.78,.15,2.6,.18,'white',c);box('Engine roof lightbar',x+2.6,y,2.69,.35,1.45,.2,'red',c)
 for yy in [-.48,.48]:box('Engine ladder rail',x-1.1,y+yy,2.56,4.65,.07,.09,'metal',c)
 for i in range(10):box('Engine ladder rung',x-3.3+i*.48,y,2.58,.05,.98,.05,'metal',c)
h.Z=.10
fire_engine(-6.4,-18.2)
h.Z=0
for y in [-18.2,-12.05]:
 mesh("Garage threshold ramp",[(2.375,y-2.325,.18),(3.15,y-2.325,.055),(3.15,y+2.325,.055),(2.375,y+2.325,.18),(2.375,y-2.325,.025),(3.15,y-2.325,.025),(3.15,y+2.325,.025),(2.375,y+2.325,.025)],[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],"stone","Fire_Threshold")
# Arrival stop: platform west of road, shelter faces east, bus separate from fire apron.
box('Bus boarding kerb',18.40,14.5,.12,.18,17,.24,'stone','Bus_Platform')
for y in [9+i*.42 for i in range(29)]:box('Tactile tile',17.98,y,.144,.42,.36,.025,'amber','Bus_Platform')
box('Bus shelter pad',13.65,15.0,.105,3.4,9.5,.21,'stone','Bus_Shelter')
for x in [12.2,15.1]:
 for y in [10.6,19.4]:box('Shelter post',x,y,1.55,.08,.08,2.9,'darkgreen','Bus_Shelter')
box('Shelter glass back',12.22,15,1.5,.04,8.7,2.35,'glass','Bus_Shelter');box('Shelter canopy',13.7,15,3.05,3.6,9.7,.18,'sage','Bus_Roof')
for y in [12.4,16]:bench(13.4,y,2.6,math.pi/2,'Bus_Shelter')
box('Bus timetable post',16.8,20.7,1.6,.09,.09,3.2,'darkgreen','Bus_Stop')
box('Bus stop timetable',16.8,20.7,2.7,1.2,.14,1.25,'white','Bus_Stop');h.text('Bus title','溪畔站',16.8,20.61,3.01,.24,'darkgreen','Bus_Stop');h.text('Bus route','01  小镇环线',16.8,20.61,2.65,.12,'darkgreen','Bus_Stop')
for z in [2.40,2.29]:box('Timetable detail',16.8,20.61,z,.78,.018,.025,'sage','Bus_Stop')
# Low floor shuttle, local y longitudinal, nose north.
def bus(x,y):
 c='Shuttle_Bus';box('Bus undercarriage',x,y,.56,2.45,8.4,.35,'rubber',c);box('Bus lower body',x,y,1.05,2.5,8.55,.83,'sage',c)
 box('Bus upper body',x,y,2.12,2.52,8.55,1.32,'cream',c);box('Bus roof',x,y,2.85,2.58,8.60,.16,'sage',c)
 box('Bus front windscreen',x,y+4.29,2.12,2.29,.025,1.05,'windshield',c);box('Bus rear window',x,y-4.29,2.12,2.22,.025,.88,'windshield',c)
 for s in [-1,1]:
  for dy in [-3,-1.6,-.2,1.2,2.65]:box('Bus side glazing',x+s*1.275,y+dy,2.13,.022,1.23,1.0,'windshield',c)
  for dy in [-2.65,2.65]:
   o=cyl('Bus tire',x+s*1.24,y+dy,.6,.54,.22,'rubber',c);o.rotation_euler.y=math.pi/2
   o=cyl('Bus wheel hub',x+s*1.37,y+dy,.6,.25,.04,'metal',c);o.rotation_euler.y=math.pi/2
 # Boarding doors on west side, aligned with platform.
 for dy in [-.2,2.65]:
  box('Bus passenger door',x-1.29,y+dy,1.68,.028,1.05,1.89,'windshield',c)
  box('Bus door split',x-1.314,y+dy,1.68,.025,.035,1.88,'cream',c)
 for xx in [-.85,.85]:box('Bus headlamp',x+xx,y+4.30,1.05,.38,.035,.2,'white',c)
 box('Bus destination board',x,y+4.307,2.58,1.35,.025,.23,'darkgreen',c)
 box('Bus bumper',x,y+4.36,.7,2.50,.13,.17,'cream',c)
 box('Bus roof ventilation',x,y-1.2,3.02,1.6,2,.20,'white',c)
bus(20.3,14)
# Planting and street furniture arranged outside traffic and door clearances.
for x,y,s in [(-20.8,26.6,1.05),(-13,26.6,1.15),(-5.1,26.6,1),(10,26.6,1.1),(-20.5,-25.2,1.0),(-13,-25.3,1.1),(-5,-25.3,1.1),(10.6,2.8,1.0),(1.9,26.6,.85),(10.1,11,1.05)]:tree(x,y,s)
for i in range(17):
 x=-21+i*1.3;y=-23.6+.25*math.sin(i);leaf('South buffer shrub',x,y,.55,(.65,.6,.7),'leafLight','Planting');flowers(x,y+.6,i)
for i in range(12):
 x=-20+i*1.8;y=1.8;leaf('Inn frontage planting',x,y,.48,(.62,.42,.53),'leafLight','Planting');flowers(x,y-.4,i)
for x,y in [(8.6,18),(9.4,4),(1.8,19.4),(-2.9,-5.5)]:
 for i in range(4):flowers(x+i*.35,y,i)
bench(-16,-3.7,3);bench(-5,-3.7,3);bench(10.2,4.6,2.6,math.pi/2)
for x,y in [(-23,22),(8,22),(8,-4.4),(-23,-24)]:
 cyl('Street lamp pole',x,y,1.9,.05,3.8,'darkgreen','Street_Furniture');box('Street lamp lantern',x,y,3.85,.42,.42,.35,'white','Street_Furniture');box('Street lamp cap',x,y,4.04,.50,.50,.10,'sage','Street_Furniture')
for x in [10,10.8]:box('Recycling bin',x,9.5,.51,.55,.55,.98,'sage','Street_Furniture')
# Welcome sign is in the landscape strip, west of the southern vehicle throat.
plaque('溪畔小镇  /  欢迎到来',9,-25.0,6)
plaque('旅店 / 商业街 ←',10.5,1.3,3.8);plaque('I  到达与守护',-20.6,-7.2,3.7)
# Two low bollards flank—not obstruct—the direct commercial-street connection.
for y in [8.5,12.5]:cyl('West entrance bollard',-26.3,y,.49,.10,.98,'darkgreen','Street_Furniture')
# Bake bevels and group by function for interactive cutaway.
scene=bpy.context.scene;scene.name='01 Arrival and guard';scene.unit_settings.system='METRIC'
for o in list(bpy.data.objects):
 if o.type=='MESH' and o.modifiers:
  o.data=o.data.copy();bpy.context.view_layer.objects.active=o
  for mod in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
for name,c in list(h.C.items()):
 root=bpy.data.objects.new(name,None);c.objects.link(root)
 for o in list(c.objects):
  if o!=root:o.parent=root
bpy.context.view_layer.update();meshes=[o for o in bpy.data.objects if o.type=='MESH'];tri=0
for o in meshes:
 o.data.calc_loop_triangles();tri+=len(o.data.loop_triangles)
 for v in o.data.vertices:assert all(math.isfinite(q) for q in v.co)
 for t in o.data.loop_triangles:
  a,b,c=[o.data.vertices[k].co for k in t.vertices];assert (b-a).cross(c-a).length>1e-10,o.name
bpy.ops.object.select_all(action='SELECT');asset=R/'I-arrival-guard.glb';bpy.ops.export_scene.gltf(filepath=str(asset),export_format='GLB',use_selection=True,export_cameras=False,export_lights=False)
meta={'title':'I 到达与守护','date':'2026-10-14','corePlot':[53.75,55],'inn':{'id':'I01','center':[IX,IY],'size':[23,15],'floors':2,'rooms':ROOMS,'westEntrance':[-22.375,10.5],'stairOpening':HOLE,'risers':20,'riserHeight':.17,'corridorWidth':2.4},'fireStation':{'id':'I02','center':[FX,FY],'size':[25,12.75],'bayDoors':[[2.265,-18.2],[2.265,-12.05]],'bayClearWidth':4.65,'engines':1,'apron':[2.375,-21.5,18.5,-8.75],'personnelDoor':[-8.5,-8.75]},'bus':{'center':[20.3,14],'length':8.55,'width':2.52,'boardingSide':'west','platform':[15.5,6,18.5,23]},'pathRects':PATHS,'vehicleRects':VEHICLE,'pedestrianPortals':{'westCommercial':[-26.875,10.5],'northPark':[5.5,27.5],'southWest':[-24.8,-27.5]},'groups':list(h.C.keys()),'meshObjects':len(meshes),'triangles':tri,'degenerateTriangles':0,'sha256':hashlib.sha256(asset.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'units':'metres','sourceAxes':'Z up; north +Y','glbAxes':'Y up; north -Z','status':'design-review'}
# Northern path reaches the original plot edge.
(R/'manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
h.studio(scene);bpy.data.objects['Studio ground'].location.z=-1.25;scene.cycles.samples=20;scene.render.resolution_x=1600;scene.render.resolution_y=1200
scene.camera=h.camera('Arrival overview',(82,-98,85),(0,-2,1),93);views=[(scene,'overview.png')]
configs=[('02 Arrival plan',(0,-3,120),(0,-3,0),91,[],'plan.png'),
 ('03 Inn welcome',(-49,-19,30),(IX,10.5,3),36,[],'inn-exterior.png'),
 ('04 Inn lobby',(14,-12,34),(IX,10,1),36,['Inn_Roof']+[n for n in h.C if n.startswith('Inn_L02')]+['Inn_L01_South','Inn_L01_East'],'inn-lobby.png'),
 ('05 Inn guest rooms',(10,-12,42),(IX,10.5,4),34,['Inn_Roof','Inn_L02_South','Inn_L02_East'],'inn-rooms.png'),
 ('06 Fire station',(30,-38,27),(FX,-15,1),40,['Fire_Roof','Fire_East','Fire_South'],'fire-interior.png'),
 ('07 Bus arrival',(47,-4,29),(17,14,1.4),31,[],'bus-stop.png')]
for name,loc,target,scale,hide,file in configs:
 sc=scene.copy();sc.name=name;sc.use_fake_user=True;sc.camera=h.camera(name+' camera',loc,target,scale)
 for n in hide:sc.view_layers[0].layer_collection.children[n].exclude=True
 views.append((sc,file))
bpy.context.window.scene=scene
for scr in bpy.data.screens:
 for ar in scr.areas:
  if ar.type=='VIEW_3D':ar.spaces.active.shading.type='MATERIAL';ar.spaces.active.overlay.show_overlays=False;ar.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(R/'I-arrival-guard.blend'))
for sc,file in views:
 if os.environ.get('I_SKIP_RENDERS'):continue
 sc.render.filepath=str(R/file);bpy.ops.render.render(write_still=True,scene=sc.name);print('RENDERED',file,flush=True)
print('COMPLETE',len(meshes),tri,flush=True)
