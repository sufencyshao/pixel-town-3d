import sys,math,json,hashlib,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import model_helpers as h
import bpy
from mathutils import Vector
R=Path(__file__).resolve().parent.parent
h.PALETTE.update({'sand':'ded3b7','path':'ddd6c3','meadow':'acc18c','river':'85b8bf','ripple':'bdd9d5','flowerWhite':'f2eddc'})
h.init();box,cyl,leaf,beam=h.box,h.cyl,h.leaf,h.beam

def mesh(n,verts,faces,mat,c):
 m=bpy.data.meshes.new(n);m.from_pydata(verts,[],faces);m.materials.append(h.M[mat]);m.update();o=bpy.data.objects.new(n,m);h.col(c).objects.link(o);return o

def strip(n,points,width,z,mat,c,depth=.10):
 vs=[]
 for i,(x,y) in enumerate(points):
  if i==0:d=Vector(points[1])-Vector(points[0])
  elif i==len(points)-1:d=Vector(points[-1])-Vector(points[-2])
  else:d=Vector(points[i+1])-Vector(points[i-1])
  d.normalize();nx,ny=-d.y*width/2,d.x*width/2
  vs.extend([(x+nx,y+ny,z),(x-nx,y-ny,z),(x+nx,y+ny,z-depth),(x-nx,y-ny,z-depth)])
 fs=[]
 for i in range(len(points)-1):
  a=4*i;b=a+4;fs.extend([(a,a+1,b+1,b),(a+2,b+2,b+3,a+3),(a,b,b+2,a+2),(a+1,a+3,b+3,b+1)])
 fs.extend([(0,2,3,1),(len(vs)-4,len(vs)-3,len(vs)-1,len(vs)-2)])
 return mesh(n,vs,fs,mat,c)

def tree(x,y,s=1,c='Trees'):
 cyl('Park tree trunk',x,y,1.45*s,.16*s,2.9*s,'wood',c)
 for dx,dy,dz in [(0,0,3.1),(.8,0,2.6),(-.7,.2,2.7),(0,-.7,2.5)]:leaf('Park tree crown',x+dx*s,y+dy*s,dz*s,(1.15*s,1.1*s,1.05*s),'leaf' if dx else 'leafLight',c)

def shrub(x,y,s=.7,c='Planting'):
 leaf('Park shrub',x,y,.48*s,(1*s,.82*s,.65*s),'leafLight',c)

def flowers(cx,cy,i=0,c='Planting'):
 for j in range(5):
  a=j*2.4+i;r=.2+.1*(j%3);x,y=cx+r*math.cos(a),cy+r*math.sin(a);z=.45+.07*(i%3)
  cyl('Flower stem',x,y,z/2,.014,z,'leaf',c)
  for k in range(5):
   a=k*math.tau/5;leaf('Flower petal',x+.10*math.cos(a),y+.1*math.sin(a),z,(.10,.09,.045),['flowerWhite','flowerPink','flowerYellow','lavender'][i%4],c)

def bench(x,y,w=2.8,c='Furniture',rot=0):
 before=set(h.col(c).objects)
 box('Park bench seat',x,y,.57,w,.64,.12,'lightwood',c)
 box('Park bench back',x,y+.30,.96,w,.08,.7,'sage',c)
 for dx in [-w*.35,w*.35]:box('Park bench leg',x+dx,y,.30,.10,.50,.49,'darkgreen',c)
 for o in set(h.col(c).objects)-before:
  dx,dy=o.location.x-x,o.location.y-y;o.location.x=x+math.cos(rot)*dx-math.sin(rot)*dy;o.location.y=y+math.sin(rot)*dx+math.cos(rot)*dy;o.rotation_euler.z=rot

def fence_y(x1,x2,y,c='Pet_Fence',height=1.2):
 for i in range(math.ceil((x2-x1)/1.8)+1):
  x=x1+(x2-x1)*i/math.ceil((x2-x1)/1.8);box('Fence post',x,y,height/2,.10,.10,height,'wood',c)
 for z in [.4,.85]:box('Fence rail',(x1+x2)/2,y,z,x2-x1,.06,.075,'lightwood',c)
def fence_x(x,y1,y2,c='Pet_Fence',height=1.2):
 for i in range(math.ceil((y2-y1)/1.8)+1):
  y=y1+(y2-y1)*i/math.ceil((y2-y1)/1.8);box('Fence post',x,y,height/2,.10,.10,height,'wood',c)
 for z in [.4,.85]:box('Fence rail',x,(y1+y2)/2,z,.06,y2-y1,.075,'lightwood',c)
def plaque(t,x,y,w=3,c='Signs'):
 for dx in [-w*.34,w*.34]:box('Sign post',x+dx,y,.62,.075,.075,1.24,'wood',c)
 h.sign(t,x,y,1.24,w,c)

# F core matches original plot. River and bridge pieces are neighboring context.
# Gently curving river kept east of the core; final town assembly can adjust banks.
def shore(y):return 32.5+6.5*(y/40)**2
YS=[-40+i*.5 for i in range(161)]
for i in range(160):
 ya,yb=YS[i:i+2];xa,xb=shore(ya),shore(yb);west=-26.875 if -27.5<(ya+yb)/2<27.5 else 21.5
 mesh('West park ground', [(west,ya,0),(xa,ya,0),(xb,yb,0),(west,yb,0)],[(0,1,2,3)],'grass','Ground')
 mesh('River water',[(xa+.8,ya,-.75),(xa+20,ya,-.75),(xb+20,yb,-.75),(xb+.8,yb,-.75)],[(0,1,2,3)],'river','River')
 mesh('West sloped bank',[(xa,ya,0),(xa+.8,ya,-.8),(xb+.8,yb,-.8),(xb,yb,0)],[(0,1,2,3)],'sand','Banks')
 mesh('East sloped bank',[(xa+20,ya,-.8),(xa+21.4,ya,.08),(xb+21.4,yb,.08),(xb+20,yb,-.8)],[(0,1,2,3)],'sand','Banks')
 mesh('Natural far bank',[(xa+21.4,ya,.08),(72,ya,.08),(72,yb,.08),(xb+21.4,yb,.08)],[(0,1,2,3)],'meadow','Far_Bank')
# Vertical cut edges make the diorama read as a solid terrain tile.
box('West terrain edge',-26.87,0,-.50,.02,55,1,'earth','Ground')
for yy in [-27.5,27.5]:box('Core terrain edge',-2.6875,yy,-.5,48.375,.02,1,'earth','Ground')
for yy in [-33.75,33.75]:box('Bridge approach terrain edge',21.5,yy,-.5,.02,12.5,1,'earth','Ground')
box('Far terrain edge',72,0,-.45,.02,80,1.06,'earth','Far_Bank')
for y in [-40,40]:
 x=shore(y);mesh('Terrain cut edge',[(21.5,y,0),(x,y,0),(x+.8,y,-.75),(x+20,y,-.75),(x+21.4,y,.08),(72,y,.08),(72,y,-1),(21.5,y,-1)],[(0,1,2,3,4,5,6,7)],'earth','Ground')
# F01 vet cottage at its original 23 x 13 m footprint.
vx,vy=-10.875,11;W,D=23,13
box('Vet floor',vx,vy,.09,W,D,.18,'tile','Vet_Floor')
h.OX=vx
h.wall_y('Vet south wall',vy-6.5,-11.5,11.5,[(0,1.9,0,2.55),(-7,3,1,2.7),(6,3.4,1.1,2.7)],'Vet_Front',.18,3.12)
h.wall_y('Vet north wall',vy+6.5,-11.5,11.5,[(-8.5,2,1.5,2.7),(-2,2.4,1.5,2.7),(6,3,1.6,2.7)],'Vet_Shell',.18,3.12)
h.wall_x('Vet west wall',-11.41,vy-6.41,vy+6.41,[(vy-1,2.5,1.1,2.7)],'Vet_Shell',.18,3.12)
h.wall_x('Vet east wall',11.41,vy-6.41,vy+6.41,[(vy-2,2.3,1.2,2.7),(vy+3,2.4,1.5,2.7)],'Vet_East',.18,3.12)
h.wall_x('Consultation partition',1,vy-6.4,vy+6.4,[(vy-3,1.05,0,2.4),(vy+3.2,1.05,0,2.4)],'Vet_Interior',.12,2.9)
h.wall_y('Treatment partition',vy+1.2,1.06,11.3,[(3,1.1,0,2.4)],'Vet_Interior',.12,2.9)
h.wall_y('Recovery partition',vy+1.5,-11.3,.94,[(-2,1.1,0,2.4)],'Vet_Interior',.12,2.9)
h.OX=0
box('Vet roof cap',vx,vy,3.42,23.55,13.55,.24,'sage','Vet_Roof')
for x in [vx-11.52,vx+11.52]:box('Vet roof parapet',x,vy,3.72,.14,13.34,.36,'cream','Vet_Roof')
for y in [vy-6.52,vy+6.52]:box('Vet roof parapet',vx,y,3.72,22.9,.14,.36,'cream','Vet_Roof')
box('Vet entrance canopy',vx,vy-7,2.95,4,1.2,.13,'wood','Vet_Front')
h.sign('F01  溪畔动物诊所',vx,vy-6.63,2.77,3.7,'Vet_Front')
# Paw emblem, rather than human medical branding.
o=leaf('Vet paw pad',vx+3,vy-6.63,2.70,(.22,.035,.18),'sage','Vet_Front')
for dx,dz in [(-.24,.22),(-.09,.33),(.10,.33),(.25,.21)]:leaf('Vet paw toe',vx+3+dx,vy-6.65,2.7+dz,(.07,.03,.095),'sage','Vet_Front')
# Reception / waiting on the west, examination and treatment on the east.
box('Reception desk',vx-4,vy-.4,.78,4,1,1.2,'sage','Vet_Interior');box('Reception desktop',vx-4,vy-.4,1.42,4.1,1.1,.09,'lightwood','Vet_Interior')
box('Reception monitor',vx-3.5,vy-.27,1.72,.55,.05,.4,'dark','Vet_Interior')
bench(vx-8,vy-3.8,3,'Vet_Interior');bench(vx-8,vy-.9,3,'Vet_Interior')
for x,y in [(vx+6,vy-1.5),(vx+6,vy+3.8)]:
 box('Veterinary examination pedestal',x,y,.71,.55,.8,1.04,'sage','Vet_Interior');box('Veterinary examination tabletop',x,y,1.29,2.2,1.0,.12,'metal','Vet_Interior');box('Exam table padded mat',x,y,1.38,2.0,.90,.06,'fabric','Vet_Interior')
 # Articulated lamp as a static prop.
 cyl('Exam lamp stand',x+1.8,y+.6,1.2,.04,2.1,'metal','Vet_Interior');beam('Exam lamp arm',(x+1.8,y+.6,2.25),(x+.8,y+.6,2.7),.05,'metal','Vet_Interior');cyl('Exam lamp shade',x+.8,y+.6,2.65,.22,.12,'white','Vet_Interior')
box('Treatment cabinet',vx+9.7,vy+3.5,.74,.75,4,1.12,'sage','Vet_Interior')
box('Treatment worktop',vx+9.7,vy+3.5,1.34,.82,4.1,.08,'white','Vet_Interior')
box('Utility sink counter',vx-4,vy+5.7,.75,4,.7,1.14,'wood','Vet_Interior');box('Utility sink',vx-4,vy+5.7,1.36,.85,.6,.07,'metal','Vet_Interior')
cyl('Utility tap',vx-4,vy+5.95,1.55,.025,.4,'metal','Vet_Interior')
# Open recovery cubbies: each has a mattress, framed entry and rear panel.
for j in range(3):
 x=vx-9.6+j*2.0;y=vy+4.3
 box('Recovery cubby floor',x,y,.31,1.6,2,.20,'wood','Vet_Interior');box('Recovery bedding',x,y,.48,1.4,1.7,.14,'fabric','Vet_Interior')
 for xx in [x-.77,x+.77]:box('Recovery cubby side',xx,y,.91,.06,2,1.2,'white','Vet_Interior')
 box('Recovery cubby rear',x,y+.97,.91,1.5,.06,1.2,'white','Vet_Interior');box('Recovery cubby top',x,y,1.54,1.6,2,.06,'lightwood','Vet_Interior')
for t,x,y in [('候诊',vx-7,vy+1.42),('检查',vx+6,vy+1.12),('护理',vx+5,vy+6.35)]:h.sign(t,x,y,2.5,1,'Vet_Interior')
tree(-21,-20,1.0,'Pet_Trees');tree(-6.8,-8,1.05,'Pet_Trees');tree(1,-9,1.1)
# Pet lawn: open double-gate vestibule separates dogs from general park movement.
box('Pet activity lawn',-14,-13,.022,19,19,.044,'meadow','Pet_Lawn')
fence_y(-23.5,-15.1,-3.5);fence_y(-12.9,-4.5,-3.5);fence_y(-23.5,-4.5,-22.5);fence_x(-23.5,-22.5,-3.5);fence_x(-4.5,-22.5,-3.5)
fence_x(-15.2,-6.3,-3.5);fence_x(-12.8,-6.3,-3.5)
fence_y(-15.2,-15.1,-6.3);fence_y(-12.9,-12.8,-6.3)
# Two gate leaves shown open along vestibule walls, clear 2.2 m passage.
for x in [-15.15,-12.85]:box('Pet gate open leaf',x,-4.55,.6,.06,2,1.1,'sage','Pet_Fence')
# Tunnel arched shell, open at both ends, oriented east-west.
vs=[];N=16
for x in [-20.5,-18]:
 for r in [1.05,.86]:
  for i in range(N+1):
   a=i*math.pi/N;vs.append((x,-12+r*math.cos(a),.06+r*math.sin(a)))
fs=[];K=N+1
for i in range(N):
 fs.extend([(i,i+1,2*K+i+1,2*K+i),(K+i,3*K+i,3*K+i+1,K+i+1),(i,K+i,K+i+1,i+1),(2*K+i,2*K+i+1,3*K+i+1,3*K+i)])
fs.extend([(0,2*K,3*K,K),(N,K+N,3*K+N,2*K+N)])
mesh('Open agility tunnel',vs,fs,'sage','Pet_Equipment')
for y in [-11,-14.5,-18]:
 for x in [-10.7,-8.3]:box('Low hurdle support',x,y,.42,.08,.08,.84,'wood','Pet_Equipment')
 box('Low agility hurdle',-9.5,y,.48,2.4,.08,.08,'roof','Pet_Equipment')
for i in range(5):cyl('Dog stepping stump',-18+i*1.05,-18,.20+.04*(i%2),.31,.4+.08*(i%2),'wood','Pet_Equipment')
bench(-20,-7.5,3,'Pet_Equipment');cyl('Pet drinking bowl',-6.8,-6.2,.16,.42,.19,'metal','Pet_Equipment');cyl('Pet bowl water',-6.8,-6.2,.26,.34,.015,'water','Pet_Equipment')
plaque('宠物草地 · 双门缓冲',-19,-2.5,3.4)
# Small outdoor music pavilion, facing north toward the audience.
box('Bandstand deck',9,-19,.33,10,6,.66,'lightwood','Stage')
# Entry stair and side ramp lead to the stage; neither blocks the audience route.
for i in range(3):box('Stage entry tread',9,-15.3-i*.28,.11*(i+1),2.4,.28,.22*(i+1),'wood','Stage')
# 5.6 m long shallow ramp from the north side to stage level.
mesh('Stage side ramp',[(14,-13.4,.10),(15.4,-13.4,.10),(15.4,-19,.66),(14,-19,.66),(14,-13.4,0),(15.4,-13.4,0),(15.4,-19,0),(14,-19,0)],[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],'wood','Stage')
for x in [4.5,13.5]:
 for y in [-21.5,-16.5]:box('Bandstand post',x,y,2.07,.14,.14,2.82,'wood','Stage')
# Gentle barrel roof with timber ribs and sage cladding.
vs=[]
for y in [-22.2,-15.8]:
 for i in range(17):
  x=3.7+i*10.6/16;z=3.55+.95*math.sin(math.pi*i/16);vs.append((x,y,z))
mesh('Bandstand curved canopy',vs,[(i,i+1,17+i+1,17+i) for i in range(16)],'sage','Stage_Roof')
for i in range(9):
 x=3.7+i*10.6/8;z=3.55+.95*math.sin(math.pi*i/8);box('Canopy timber rib',x,-19,z-.07,.07,6.5,.10,'wood','Stage_Roof')
box('Stage acoustic backdrop',9,-21.8,1.8,9,.09,2.1,'lightwood','Stage')
for j in range(13):box('Backdrop slat',4.65+j*.725,-21.87,1.8,.08,.05,2.1,'wood','Stage')
for x in [5.3,12.7]:box('Outdoor speaker',x,-20.8,1.35,.6,.5,1.1,'darkgreen','Stage')
cyl('Microphone stand',9,-18.2,1.42,.025,1.5,'metal','Stage');cyl('Microphone stand base',9,-18.2,.7,.24,.07,'dark','Stage')
for y in [-6.3,-9.2,-12.1]:
 for x in [6,11.3]:bench(x,y,3.5,'Audience')
plaque('林间小舞台',18.8,-21.5,2.5)
# Quiet wildlife garden northeast, separated from pet lawn by the clinic and routes.
for x,y,s in [(6,20,1.1),(16,22,1.3),(18,9,1),(5,8,1.0),(9,26,.85)]:tree(x,y,s,'Habitat')
for i,(x,y) in enumerate([(5,13),(6,16),(10,23),(13,24),(17,18),(18,13),(13,7),(8,8)]):shrub(x,y,1.1,'Habitat');flowers(x+1,y-.7,i,'Habitat')
# A shallow wildlife water patch is separated from the river and public dog lawn.
cyl('Habitat pond rim',12,15,.06,2.2,.12,'sand','Habitat',32)
cyl('Habitat shallow water',12,15,.135,1.92,.03,'water','Habitat',32)
for i in range(9):
 a=i*2.4;leaf('Habitat pond stone',12+2.1*math.cos(a),15+2.1*math.sin(a),.23,(.35,.26,.24),'stone','Habitat')
beam('Habitat basking log',(10.2,14.5,.28),(12.1,13.9,.35),.28,'wood','Habitat')
for x,y in [(7.5,18),(17,19)]:
 box('Birdhouse post',x,y,1.25,.08,.08,2.5,'wood','Habitat');box('Birdhouse body',x,y,2.65,.5,.4,.55,'lightwood','Habitat');box('Birdhouse roof',x,y,2.97,.66,.55,.08,'roof','Habitat');o=cyl('Birdhouse entry',x,y-.207,2.69,.095,.012,'dark','Habitat');o.rotation_euler.x=math.pi/2
for y in [10,12.5,15,17.5,20,22]:shrub(20,y,.8,'Habitat')
plaque('安静栖息角 · 请勿追逐',13,5,3.8)
# Riverside observation deck sits above the sloped bank, connected at x=shore-3.5.
px=shore(2)-3.5;ex=shore(2)+6.5
box('Riverside overlook deck',(px+ex)/2,2,.11,ex-px,8,.22,'lightwood','Overlook')
for i in range(17):box('Deck board seam',(px+ex)/2,-1.9+i*.49,.226,ex-px,.014,.012,'wood','Overlook')
for x in [px+1,ex-1]:
 for y in [-1,5]:cyl('Overlook pier',x,y,-.48,.18,1.2,'wood','Overlook')
for y in [-2,6]:
 for i in range(7):box('Overlook railing post',px+i*(ex-px)/6,y,.80,.065,.065,1.14,'darkgreen','Overlook')
 box('Overlook railing cap',(px+ex)/2,y,1.39,ex-px,.08,.07,'wood','Overlook')
for i in range(6):box('Overlook river post',ex,-2+i*1.6,.80,.065,.065,1.14,'darkgreen','Overlook')
box('Overlook river rail',ex,2,1.39,.08,8,.07,'wood','Overlook')
bench(ex-2,2,2.8,'Overlook',math.pi/2)
# Bridges are neighboring-context connectors at the original north/south bridge latitudes.
for label,y in [('North',35),('South',-36.25)]:
 x0,x1=24.375,70.625
 box(label+' bridge deck',(x0+x1)/2,y,.14,x1-x0,4.75,.28,'lightwood','Bridges')
 for i in range(62):box('Bridge board joint',x0+i*(x1-x0)/61,y,.286,.02,4.75,.012,'wood','Bridges')
 for yy in [y-2.38,y+2.38]:
  g0,g1=shore(y)-.9,shore(y)+21.4
  for j in range(15):box('Bridge guard post',g0+j*(g1-g0)/14,yy,.91,.07,.07,1.25,'darkgreen','Bridges')
  box('Bridge handrail',(g0+g1)/2,yy,1.56,g1-g0,.08,.08,'wood','Bridges')
 for x in [shore(y)+2,shore(y)+18]:
  for yy in [y-1.7,y+1.7]:cyl('Bridge pier',x,yy,-.35,.25,1.2,'wood','Bridges')
# Walkway union represented as adjacent non-overlapping trapezoids.
# Curved river promenade + central park spine + west, clinic and pet approaches.
rects=[(-26.875,23,-1.5,1.5), (21.5,24.5,-27.5,27.5), (vx-.85,vx+.85,1.5,4.5),(-15,-13,-3.5,-1.5), (17,23,-10.5,-7.5),(14,23,-14.4,-12.6),(23,shore(2)-3.5,-1.5,3.5)]
# Connect park spine to promenade at both ends without crossing protected habitats.
rects += [(21.5,shore(26)+.2,25,27.5),(21.5,shore(-26)+.2,-27.5,-25)]
cuts=sorted(set(YS+[v for r in rects for v in r[2:]]+[-2,6]))
pathpolys=[]
for ya,yb in zip(cuts,cuts[1:]):
 ym=(ya+yb)/2;active=[]
 # Leave the elevated viewing platform footprint free of overlapping path top faces.
 if not -2<=ym<=6:active.append((lambda y:shore(y)-4.2,lambda y:shore(y)-1.8))
 else:active.append((lambda y:shore(y)-4.2,lambda y:px))
 for x0,x1,y0,y1 in rects:
  if y0<=ym<=y1:active.append((lambda y,x=x0:x,lambda y,x=x1:x))
 active.sort(key=lambda r:r[0](ym));groups=[]
 for l,r in active:
  if groups and l(ym)<=max(b(ym) for a,b in groups[-1])+1e-5:groups[-1].append((l,r))
  else:groups.append([(l,r)])
 for group in groups:
  la,ra=min(a(ya) for a,b in group),max(b(ya) for a,b in group);lb,rb=min(a(yb) for a,b in group),max(b(yb) for a,b in group)
  if min(ra-la,rb-lb)<1e-5:continue
  pts=[(la,ya,.10),(ra,ya,.10),(rb,yb,.10),(lb,yb,.10)]
  mesh('Connected park walk',pts,[(0,1,2,3)],'path','Paths');pathpolys.append([[p[0],p[1]] for p in pts])
# Far bank natural trail, separate from dog/play space.
strip('Far bank nature walk',[(66+.8*math.sin(y/12),y) for y in YS],1.8,.13,'sand','Far_Bank')
# River edge bollards beside the main promenade, left openings at bridges/platform.
for y in range(-30,32,3):
 if -3<y<7:continue
 x=shore(y)-1.15;cyl('Riverside safety post',x,y,.64,.07,1.25,'wood','River_Rail')
for ya,yb in [(-31,-2),(6,32)]:
 strip('Riverside top rail',[(shore(y)-1.15,y) for y in [ya+i*(yb-ya)/32 for i in range(33)]],.07,1.24,'wood','River_Rail',.07)
# Trees and layered informal planting keep the park full while preserving routes.
for x,y,s in [(-24,23,1.3),(-17,24,1.15),(-6,24,1.25),(-24,-26,1.2),(-16,-25.5,1),(-6,-25,1.2),(2,-25,1.0),(18,-25,1.1),(-24,-.1,.7)]:
 if y==-.1:continue
 tree(x,y,s)
for x,y,s in [(60,-25,1.3),(69,-18,1.2),(60,-10,1.2),(70,0,1.35),(60,12,1.3),(69,22,1.3),(62,29,1.1)]:tree(x,y,s,'Far_Bank')
for i in range(32):
 y=-29+i*1.85
 if -4<y<8:continue
 x=shore(y)+.35;leaf('Riverbank boulder',x,y,-.15,(.5,.65,.45),'stone','Banks')
 for j in range(4):
  xx=x+.5+.18*j;yy=y+.13*math.sin(j);o=leaf('River reed',xx,yy,.17,(.055,.07,.65),'sage','Banks');o.rotation_euler.y=.15*(j-1)
for i in range(25):
 x=-23+i*.78;y=21+.6*math.sin(i*2.4);shrub(x,y,.45+.10*(i%3));flowers(x,y-.65,i)
for i in range(19):
 x=-22+i*1.7;y=-25.1+.4*math.sin(i*2.4);flowers(x,y,i)
for x,y in [(18,-3.5),(20,3.5),(1.5,-4.8),(1.5,2.7),(-25,5),(-25,15)]:shrub(x,y,.85)
# Drinking fountain, recycling station and low park lights beside—not in—the walk.
box('Drinking fountain pedestal',18,2.9,.62,.48,.45,1.1,'stone','Furniture');box('Fountain basin',18,2.9,1.19,.64,.55,.09,'metal','Furniture')
for x in [16.5,17.3]:box('Park recycling bin',x,3.2,.48,.56,.56,.92,'sage','Furniture')
for x,y in [(-24,2.5),(19,-2.6),(25.5,15),(25.5,-18)]:
 cyl('Park lamp pole',x,y,1.6,.04,3.2,'darkgreen','Furniture');box('Park lamp head',x,y,3.2,.4,.4,.14,'white','Furniture')
bench(25,12,3,'Furniture',math.pi/2);bench(25,-8,3,'Furniture',math.pi/2)
plaque('F  河岸公园',-23,2.3,3.6);plaque('河畔慢行 · 北桥 / 南桥',27,-23,3.6)
# Small current streaks keep the water readable, without animated simulation.
for i in range(23):
 y=-30+i*2.6;x=shore(y)+6+(i%3)*3.4;box('River glint',x,y,-.727,.09,1.4,.01,'ripple','River')

# Group/export and geometric checks.
scene=bpy.context.scene;scene.name='01 Riverside park';scene.unit_settings.system='METRIC'
for name,c in list(h.C.items()):
 parent=bpy.data.objects.new(name,None);c.objects.link(parent)
 for o in list(c.objects):
  if o!=parent:o.parent=parent
bpy.context.view_layer.update();meshes=[o for o in bpy.data.objects if o.type=='MESH'];tri=0
for o in meshes:
 o.data.calc_loop_triangles();tri+=len(o.data.loop_triangles)
 for v in o.data.vertices:assert all(math.isfinite(x) for x in v.co)
 for t in o.data.loop_triangles:
  a,b,c=[o.data.vertices[k].co for k in t.vertices];assert (b-a).cross(c-a).length>1e-10,o.name
bpy.ops.object.select_all(action='SELECT');asset=R/'F-river-park.glb';bpy.ops.export_scene.gltf(filepath=str(asset),export_format='GLB',use_selection=True,export_cameras=False,export_lights=False)
meta={'title':'F 区 · 河岸公园','corePlot':[53.75,55],'displayBounds':[-26.875,72,-40,40],'vetBuilding':[23,13],'vetCenter':[vx,vy],'riverWidth':20,'petLawn':[19,19],'audienceBenches':6,'suggestedAudienceSeats':18,'meshObjects':len(meshes),'triangles':tri,'degenerateTriangles':0,'sha256':hashlib.sha256(asset.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'status':'design-review','units':'metres','sourceAxes':'Z up, north +Y','glbAxes':'Y up, north -Z','groups':list(h.C.keys()),'portals':{'west':[-26.875,0],'north':[23,27.5],'south':[23,-27.5]},'pathPolygons':pathpolys,'riverContext':'Adjacent context; shoreline proposed for this asset, final masterplan assembly pending'}
(R/'manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
h.studio(scene);bpy.data.objects['Studio ground'].location.z=-1.50;scene.cycles.samples=20;scene.render.resolution_x=1600;scene.render.resolution_y=1200
scene.camera=h.camera('Park overview',(110,-125,112),(22.5,0,0),138)
views=[(scene,'overview.png')]
for name,loc,target,scale,hide,file in [
 ('02 Park plan',(19,-.001,130),(19,0,0),110,['Vet_Roof'],'plan.png'),
 ('03 Vet interior',(16,-16,34),(vx,vy,1),34,['Vet_Roof','Vet_Front','Vet_East'],'vet-interior.png'),
 ('04 Pet meadow',(7,-34,30),(-14,-13,0),29,[],'pet-meadow.png'),
 ('05 Music pavilion',(34,12,28),(9,-15,1),35,[],'music-pavilion.png'),
 ('06 Riverside walk',(84,-35,38),(36,3,0),55,[],'riverside.png')]:
 sc=scene.copy();sc.name=name;sc.use_fake_user=True;sc.camera=h.camera(name+' camera',loc,target,scale)
 for n in hide:sc.view_layers[0].layer_collection.children[n].exclude=True
 views.append((sc,file))
bpy.context.window.scene=scene
for scr in bpy.data.screens:
 for ar in scr.areas:
  if ar.type=='VIEW_3D':ar.spaces.active.shading.type='MATERIAL';ar.spaces.active.overlay.show_overlays=False;ar.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(R/'F-river-park.blend'))
for sc,file in views:
 if os.environ.get('F_SKIP_RENDERS'):continue
 sc.render.filepath=str(R/file);bpy.ops.render.render(write_still=True,scene=sc.name);print('RENDERED',file,flush=True)
print('COMPLETE',len(meshes),tri,flush=True)
