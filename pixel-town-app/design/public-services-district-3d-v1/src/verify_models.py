import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from collections import deque
R=Path(__file__).resolve().parent.parent;m=json.loads((R/'manifest.json').read_text());checks=[]
def check(v,n):
 assert v,n
 checks.append(n)
bpy.ops.wm.open_mainfile(filepath=str(R/'B-public-services.blend'));bpy.context.window.scene=bpy.data.scenes['01 B district'];bpy.context.view_layer.update()
def objs(c):return [o for o in bpy.data.collections[c].objects if o.type=='MESH']
def bounds(o):
 vs=[o.matrix_world@Vector(v) for v in o.bound_box]
 return [(min(v[i] for v in vs),max(v[i] for v in vs)) for i in range(3)]
allmeshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and 'Studio' not in [c.name for c in o.users_collection]]
bb={o.name:bounds(o) for o in allmeshes}
check(len(bpy.data.scenes)==9,'Nine Blender review scenes including both library floors')
check(m['plot']==[85,62.5],'Masterplan B plot retained: 85 x 62.5 m')
check(len(m['buildings'])==6,'Six public service buildings')
check(all(a[0][0]>=-42.501 and a[0][1]<=42.501 and a[1][0]>=-31.251 and a[1][1]<=31.251 for a in bb.values()),'All model geometry remains inside B plot')
rects=[]
for b in m['buildings']:
 x,y=b['center'];w,d=b['size'];rects.append((b['id'],x-w/2,y-d/2,x+w/2,y+d/2))
for i,(id,a,b,c,d) in enumerate(rects):
 for jd,e,f,g,h in rects[i+1:]:check(min(c,g)<=max(a,e) or min(d,h)<=max(b,f),'Buildings disjoint: '+id+' / '+jd)
check(len([o for o in objs('B01_Interior') if o.name.startswith('Student desk') and not 'leg' in o.name])==24,'24 school desks in two classrooms')
check(any('Medical red cross' in o.name for o in objs('B03_Roof')),'Original clinic medical red cross preserved')
check(len([o for o in objs('B02_Interior') if 'Stair tread' in o.name or 'Stair step' in o.name])==22,'Library 22 stair treads retained')
for b in m['buildings']:
 if b.get('source'):continue
 walls=objs(b['id']+'_Shell');ceiling=next(o for o in objs(b['id']+'_Roof') if o.name.startswith('Closed ceiling slab'))
 check(abs(max(bb[o.name][2][1] for o in walls)-bb[ceiling.name][2][0])<1e-5,b['id']+' wall meets ceiling without vertical gap')
for key,v in m['sources'].items():
 for f in sorted(set([R.parent/v['file'],R/'reference/civic-buildings-3d-v2'/key/Path(v['file']).name,R.parent/'civic-buildings-3d-v2'/key/Path(v['file']).name])):
  if not f.exists():continue
  check(hashlib.sha256(f.read_bytes()).hexdigest()==v['sha256'],'Source unchanged: '+str(f.relative_to(R.parent)))
  if f.with_suffix('.glb').exists():check(hashlib.sha256(f.with_suffix('.glb').read_bytes()).hexdigest()==v['glbSha256'],'Source GLB unchanged: '+key)
 check(v['scale']==1,'Original '+key+' imported at scale 1')
# Geometry-backed 0.25 m grid with a 0.35 m body radius. Only ground-floor walking surfaces.
walkobjects=[]
for o in allmeshes:
 cs=[c.name for c in o.users_collection]
 if any(c=='Paths' or c.endswith('_Floor') or c.endswith('_Approach') for c in cs):walkobjects.append(o)
 elif any(c.startswith(('B02_','B03_')) for c in cs) and any(t in o.name for t in ['__Foundation','__Porch','__Floor tile','__Oak plank']) and bb[o.name][2][1]<.3:walkobjects.append(o)
verts=[];faces=[]
for o in walkobjects:
 o.data.calc_loop_triangles()
 for t in o.data.loop_triangles:
  ps=[o.matrix_world@o.data.vertices[i].co for i in t.vertices];n=(ps[1]-ps[0]).cross(ps[2]-ps[0])
  if n.z>1e-8:
   off=len(verts);verts.extend(ps);faces.append((off,off+1,off+2))
bvh=BVHTree.FromPolygons(verts,faces,all_triangles=True)
def paved(x,y):
 # Blender float32 transforms can separate adjacent tile edges by a few micrometres.
 # At most 0.02 mm ray jitter handles boundary precision without bridging designed gaps.
 return any(bvh.ray_cast(Vector((x+dx,y+dy,1)),Vector((0,0,-1)),1)[0] is not None for dx,dy in [(0,0),(.00002,0),(-.00002,0),(0,.00002),(0,-.00002)])
blockers=[]
for o in allmeshes:
 if o in walkobjects:continue
 a=bb[o.name]
 if a[2][0]<2.0 and a[2][1]>.24 and not any(c.name in ['Ground','Schoolyard'] for c in o.users_collection):blockers.append(a)
def clear(x,y):
 if not paved(x,y):return False
 for a in blockers:
  xx=max(a[0][0],min(x,a[0][1]));yy=max(a[1][0],min(y,a[1][1]))
  if (x-xx)**2+(y-yy)**2<.35**2:return False
 return all(paved(x+dx,y+dy) for dx,dy in [(.35,0),(-.35,0),(0,.35),(0,-.35),(.247,.247),(-.247,.247),(.247,-.247),(-.247,-.247)])
walk={(i,j) for i in range(-168,169) for j in range(-124,125) if clear(i*.25,j*.25)}
start=(0,-122);check(start in walk,'South portal body clearance');q=deque([start]);seen={start}
while q:
 i,j=q.popleft()
 for n in [(i-1,j),(i+1,j),(i,j-1),(i,j+1)]:
  if n in walk and n not in seen:seen.add(n);q.append(n)
goals={'west':(-42,-5),'east':(42,-5),'northWest':(-11.5,30.5),'northEast':(15.5,30.5),'schoolInside':(-26,10),'libraryInside':(2,8.5),'clinicInside':(28,9),'communityInside':(-26,-11.5),'postInside':(.5,-11.5),'policeInside':(27.5,-11.5),'clinicSideInside':(35.5,12),'clinicSideThreshold':(36.5,12.5),'postalRearInside':(.5,-22.5),'libraryForecourt':(2,0),'clinicForecourt':(28,0),'schoolClass1':(-32,13),'schoolClass2':(-18.5,13),'schoolWC':(-26,19),'communityConsult':(-31,-18),'communityWC':(-26,-21),'postWC':(8,-21),'policeMediation':(20.5,-18),'policeWC':(20,-21)}
for name,(x,y) in goals.items():check((round(x*4),round(y*4)) in seen,'Continuous body route reaches '+name)
# All paving tiles are disjoint in XY, so no coplanar duplicate walkway faces.
for i,r in enumerate(m['paths']):
 for t in m['paths'][i+1:]:assert min(r[2],t[2])-max(r[0],t[0])<1e-6 or min(r[3],t[3])-max(r[1],t[1])<1e-6
check(True,'Public paving union has no overlapping tiles')
scenes=list(bpy.data.scenes.keys());bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(R/'B-public-services.glb'))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];tri=degen=0
for o in meshes:
 o.data.calc_loop_triangles();tri+=len(o.data.loop_triangles)
 for v in o.data.vertices:assert all(math.isfinite(x) for x in v.co)
 for t in o.data.loop_triangles:
  a,b,c=[o.data.vertices[i].co for i in t.vertices]
  if (b-a).cross(c-a).length<1e-10:degen+=1
check(len(meshes)==m['meshObjects'],'GLB mesh count equals source');check(tri==m['triangles'],'GLB triangle count equals source');check(degen==0,'GLB zero degenerate triangles');check(hashlib.sha256((R/'B-public-services.glb').read_bytes()).hexdigest()==m['sha256'],'GLB current hash')
result={'status':'PASS','date':'2026-10-14','blender':bpy.app.version_string,'checks':len(checks),'scenes':scenes,'meshObjects':len(meshes),'triangles':tri,'degenerateTriangles':degen,'sampledWalkCells':len(walk),'reachableCells':len(seen),'bodyRadius':.35,'rayBoundaryToleranceMetres':.00002,'gridSpacing':.25,'reachableGoals':goals,'sha256':m['sha256'],'items':checks,'scope':'Static sampled ground-floor entry routes; not runtime collision, stair traversal or regulatory accessibility certification'}
(R/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print('ALL VALIDATION PASS',len(checks),'assertions;',len(seen),'reachable grid cells;',len(meshes),'meshes;',tri,'triangles')
