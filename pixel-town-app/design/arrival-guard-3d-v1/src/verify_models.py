import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];m=json.loads((R/'manifest.json').read_text());checks=[]
def check(name,ok):
 checks.append({'check':name,'passed':bool(ok)})
 if not ok:raise AssertionError(name)
def overlap(a,b):return min(a[2],b[2])-max(a[0],b[0]),min(a[3],b[3])-max(a[1],b[1])
def intersects(a,b):return min(overlap(a,b))>1e-5
def contains(p,pt):return p[0]-1e-5<=pt[0]<=p[2]+1e-5 and p[1]-1e-5<=pt[1]<=p[3]+1e-5
p=m['pathRects'];check('Pedestrian paving has no duplicate overlapping tiles',all(not intersects(a,b) for i,a in enumerate(p) for b in p[i+1:]))
seen={0};todo=[0]
while todo:
 i=todo.pop()
 for j,b in enumerate(p):
  dx,dy=overlap(p[i],b)
  if j not in seen and dx>=-1e-6 and dy>=-1e-6 and max(dx,dy)>1e-5:seen.add(j);todo.append(j)
check('Pedestrian paving is one connected network',len(seen)==len(p))
for name,pt in m['pedestrianPortals'].items():check('Connected portal '+name,any(contains(a,pt) for a in p))
for name,pt in [('inn west door',m['inn']['westEntrance']),('fire staff door',m['fireStation']['personnelDoor']),('inn rear terrace',[-1.5,18])]:check('Connected '+name,any(contains(a,pt) for a in p))
check('No pedestrian paving crosses the fire vehicle apron',all(not intersects(a,m['fireStation']['apron']) for a in p))
check('Bus bay separated north of fire apron',m['bus']['center'][1]-m['bus']['length']/2>m['fireStation']['apron'][3])
check('Six ensuite rooms',len(m['inn']['rooms'])==6 and all(r['ensuite'] for r in m['inn']['rooms']))
check('Rooms are disjoint',all(not intersects(a['bounds'],b['bounds']) for i,a in enumerate(m['inn']['rooms']) for b in m['inn']['rooms'][i+1:]))
check('GLB SHA256 matches',hashlib.sha256((R/'I-arrival-guard.glb').read_bytes()).hexdigest()==m['sha256'])
bpy.ops.wm.open_mainfile(filepath=str(R/'I-arrival-guard.blend'));bpy.context.view_layer.update()
check('Seven saved camera scenes',len(bpy.data.scenes)==7)
objs=[o for o in bpy.data.objects if o.type=='MESH' and not any(c.name=='Studio' for c in o.users_collection)]
def bounds(o):
 pts=[o.matrix_world@Vector(v) for v in o.bound_box];return [min(v.x for v in pts),min(v.y for v in pts),max(v.x for v in pts),max(v.y for v in pts),min(v.z for v in pts),max(v.z for v in pts)]
# Critical travel corridors: trunk/post/sign support centrelines cannot block paved paths.
obstacles=[o for o in objs if o.name.startswith(('Tree trunk','Signpost','Street lamp pole','Recycling bin'))]
for o in obstacles:check(o.name+' outside pedestrian paths',all(not intersects(bounds(o)[:4],a) for a in p))
# A centre strip through both open bay doors to the eastern road remains clear of fixed obstacles.
for j,y in enumerate([-18.2,-12.05]):
 corridor=[-2.4,y-1.65,26.5,y+1.65]
 blockers=[o.name for o in objs if any(c.name in ['Planting','Street_Furniture','Wayfinding','Bus_Stop','Bus_Shelter','Fire_Interior','Fire_Furniture','Fire_East'] for c in o.users_collection) and bounds(o)[4]<3.3 and bounds(o)[5]>.3 and intersects(bounds(o)[:4],corridor)]
 check('Fire exit corridor '+str(j+1)+' clear',not blockers)
check('Guest corridor free of furniture',not any(intersects(bounds(o)[:4],[-17.94,9.36,.425,11.64]) and bounds(o)[4]<5.58 and bounds(o)[5]>3.6 for o in objs if any(c.name=='Inn_L02_Furniture' for c in o.users_collection)))
for room in m['inn']['rooms']:
 x,y=room['door'];clear=[x-.4,y-.32,x+.4,y+.32];check('Room '+room['id']+' door clear of furniture',not any(intersects(bounds(o)[:4],clear) and bounds(o)[4]<5.58 and bounds(o)[5]>3.6 for o in objs if any(c.name=='Inn_L02_Furniture' for c in o.users_collection)))
# Confirm actual floor opening and stair terminal elevation.
slabs=[o for o in objs if o.name.startswith('Inn upper slab')]
check('Upper slab leaves stair opening unobstructed',all(not intersects(bounds(o)[:4],m['inn']['stairOpening']) for o in slabs))
check('20 stair treads',sum(o.name.startswith(('Inn stair lower','Inn stair upper')) for o in objs)==20)
check('Stair arrives at upper floor',abs(max(bounds(o)[5] for o in objs if o.name.startswith('Inn stair upper'))-3.58)<1e-5)
check('Six bed frames',sum(o.name.startswith('Bed frame') for o in objs)==6)
check('Six bathroom fixtures',sum(o.name.startswith('Toilet base') for o in objs)==6)
check('Fire engine wheels contact floor',all(abs(bounds(o)[4]-.18)<1e-5 for o in objs if o.name.startswith('Engine tire')))
check('Two garage thresholds connect floor to apron',sum(o.name.startswith('Garage threshold ramp') for o in objs)==2)
check('One fire engine and one bus',sum(o.name=='Engine chassis' for o in objs)==1 and sum(o.name=='Bus undercarriage' for o in objs)==1)
tri=0
for o in objs:o.data.calc_loop_triangles();tri+=len(o.data.loop_triangles)
check('Blend triangle count',tri==m['triangles']);check('Blend object count',len(objs)==m['meshObjects'])
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(R/'I-arrival-guard.glb'));tri=0;imported=[o for o in bpy.data.objects if o.type=='MESH']
for o in imported:o.data.calc_loop_triangles();tri+=len(o.data.loop_triangles)
check('GLB reimport triangle count',tri==m['triangles']);check('All cutaway groups survived GLB export',all(bpy.data.objects.get(n) is not None for n in m['groups']))
(R/'validation.json').write_text(json.dumps({'passed':True,'checks':checks,'glbTriangles':tri,'glbMeshObjects':len(imported),'note':'Static layout and clearance checks; no runtime driving, navigation or engineering certification.'},ensure_ascii=False,indent=2));print('PASSED',len(checks),tri)
