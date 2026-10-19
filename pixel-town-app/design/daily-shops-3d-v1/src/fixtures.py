import math,bpy
import model_helpers as h
box,cyl,leaf,beam=h.box,h.cyl,h.leaf,h.beam
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

