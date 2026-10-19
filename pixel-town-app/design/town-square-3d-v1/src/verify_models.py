import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from collections import deque
R=Path(__file__).resolve().parent.parent;m=json.loads((R/'manifest.json').read_text());checks=[]
def check(v,n):
 assert v,n
 checks.append(n)
bpy.ops.wm.open_mainfile(filepath=str(R/'E-town-square.blend'));bpy.context.view_layer.update()
def objs(c):return [o for o in bpy.data.collections[c].objects if o.type=='MESH']
def bounds(o):
 vs=[o.matrix_world@Vector(v) for v in o.bound_box]
 return [(min(v[i] for v in vs),max(v[i] for v in vs)) for i in range(3)]
bb={o.name:bounds(o) for o in bpy.data.objects if o.type=='MESH'}
check(len(bpy.data.scenes)==7,'Seven review scenes')
for c in ['Market_Fixtures','Market_Canopies','Event_Decor']:check(bpy.data.scenes['02 Daily square'].view_layers[0].layer_collection.children[c].exclude,'Daily mode hides '+c)
check(bpy.data.scenes['03 Plan'].view_layers[0].layer_collection.children['Landmark_Canopy'].exclude,'Plan reveals tree seating')
ref=R.parent/'town-3d-masterplan-v1/plan-data.json'
if not ref.exists():ref=R/'reference/masterplan-E.json'
p=json.loads(ref.read_text());zone=next(z for vals in p.values() if isinstance(vals,list) for z in vals if isinstance(z,dict) and z.get('id')=='E')
check(m['plot']==[zone['rect'][2]/4,zone['rect'][3]/4],'Footprint matches masterplan E')
check(m['plazaDiameter']==36 and m['plazaCenter']==[0,-2.5],'Original plaza diameter and centre')
check(len([o for o in objs('Market_Fixtures') if o.name.split('.')[0]=='Market rolling counter'])==6,'Six independent mobile stalls')
check(len([o for o in objs('Ring_Seats') if o.name.split('.')[0]=='Tree ring backrest'])==4,'Four curved seating segments')
for c in m['groups']:
 for o in objs(c):
  a=bb[o.name];check(a[0][0]>=-42.501 and a[0][1]<=42.501 and a[1][0]>=-27.501 and a[1][1]<=27.501,'Within plot: '+o.name)
water=bpy.data.objects['Shallow water surface'];bottom=bpy.data.objects['Water basin bottom']
check(abs(water.location.z-bb[bottom.name][2][1]-.25)<1e-5,'Shallow basin has 0.25 m water depth')
check(bb[bottom.name][2][0]>=0,'Basin floor covers ground surface')
for o in objs('Ring_Seats'):
 if o.name.startswith('Ring seat leg'):check(abs(bb[o.name][2][0]-.09)<1e-5,'Ring seat leg grounded: '+o.name)
# Use the actual exported-source paving mesh for footprint queries.
paving=bpy.data.objects['Continuous square paving'];bvh=BVHTree.FromObject(paving,bpy.context.evaluated_depsgraph_get())
def paved(x,y):return bvh.ray_cast(Vector((x,y,2)),Vector((0,0,-1)),3)[0] is not None
check(not paved(0,-2.5),'No paving in tree well');check(not paved(28,7),'No paving underneath basin')
for x,y in [(-42,-2.5),(42,-2.5),(0,27),(0,-27)]:check(paved(x,y),'Boundary portal reaches paving '+str((x,y)))
# 0.5 m sample grid, 0.35 m body radius; geometry-only accessibility, not game navigation.
blockers=[]
for c in ['Pergola_Frame','Pergola_Furniture','Seating','Community','Amenities','Wayfinding']:
 for o in objs(c):
  a=bb[o.name]
  if a[2][0]<2.1 and a[2][1]>.15:blockers.append(a)
for s in m['marketStalls']:
 x,y=s['center'];blockers.append([(x-2.3,x+2.3),(y-1.3,y+1.3),(0,3)])
def clear(x,y):
 if math.hypot(x,y+2.5)<5.5 or math.hypot(x-28,y-7)<5.2:return False
 for a in blockers:
  xx=max(a[0][0],min(x,a[0][1]));yy=max(a[1][0],min(y,a[1][1]))
  if math.hypot(x-xx,y-yy)<.35:return False
 for dx,dy in [(0,0),(.35,0),(-.35,0),(0,.35),(0,-.35),(.247,.247),(-.247,.247),(.247,-.247),(-.247,-.247)]:
  if not paved(x+dx,y+dy):return False
 return True
walk={(i,j) for i in range(-84,85) for j in range(-54,55) if clear(i*.5,j*.5)}
start=(-84,-5);check(start in walk,'West entry body clearance')
seen={start};q=deque([start])
while q:
 i,j=q.popleft()
 for n in [(i-1,j),(i+1,j),(i,j-1),(i,j+1)]:
  if n in walk and n not in seen:seen.add(n);q.append(n)
goals={'east':(42,-2.5),'north':(0,27),'south':(0,-27),'noticeboard':(-12,21),'drinking':(11,20.5),'market':(-28,-2.5),'water':(28,1),'pergola':(28,-12),'treeNorth':(0,5),'treeSouth':(0,-10),'treeEast':(7.5,-2.5),'treeWest':(-7.5,-2.5)}
for n,(x,y) in goals.items():check((round(x*2),round(y*2)) in seen,'Body route reaches '+n)
# Paving top triangles all face upward and carry no duplicated planar triangle.
paving.data.calc_loop_triangles();keys=[]
for t in paving.data.loop_triangles:
 a,b,c=[paving.data.vertices[i].co for i in t.vertices];check((b-a).cross(c-a).z>1e-9,'Paving positive area '+str(t.index));keys.append(tuple(sorted(tuple(round(v,6) for v in p) for p in [a,b,c])))
check(len(keys)==len(set(keys)),'No duplicate pavement triangles')
scenes=list(bpy.data.scenes.keys());bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(R/'E-town-square.glb'))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];tri=degen=0
for o in meshes:
 o.data.calc_loop_triangles();tri+=len(o.data.loop_triangles)
 for v in o.data.vertices:assert all(math.isfinite(x) for x in v.co)
 for t in o.data.loop_triangles:
  a,b,c=[o.data.vertices[i].co for i in t.vertices]
  if (b-a).cross(c-a).length<1e-10:degen+=1
check(len(meshes)==m['meshObjects'],'GLB mesh count');check(tri==m['triangles'],'GLB triangle count');check(degen==0,'GLB zero degenerate triangles');check(hashlib.sha256((R/'E-town-square.glb').read_bytes()).hexdigest()==m['sha256'],'GLB current hash')
result={'status':'PASS','date':'2026-10-14','blender':bpy.app.version_string,'checks':len(checks),'scenes':scenes,'meshObjects':len(meshes),'triangles':tri,'degenerateTriangles':degen,'sampledWalkCells':len(walk),'reachableCells':len(seen),'bodyRadius':.35,'gridSpacing':.5,'reachableGoals':goals,'sha256':m['sha256'],'items':checks}
(R/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print('ALL VALIDATION PASS',len(checks),'assertions;',len(seen),'reachable grid cells;',len(meshes),'meshes;',tri,'triangles')
