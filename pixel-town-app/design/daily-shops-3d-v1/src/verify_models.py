import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from collections import deque
R=Path(__file__).resolve().parent.parent;m=json.loads((R/'manifest.json').read_text());checks=[]
def check(v,n):
 assert v,n
 checks.append(n)
bpy.ops.wm.open_mainfile(filepath=str(R/'H-daily-shops.blend'));bpy.context.window.scene=bpy.data.scenes['01 H whole street'];bpy.context.view_layer.update()
def objs(c):return [o for o in bpy.data.collections[c].objects if o.type=='MESH']
def bounds(o):
 vs=[o.matrix_world@Vector(v) for v in o.bound_box]
 return [(min(v[i] for v in vs),max(v[i] for v in vs)) for i in range(3)]
allmeshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and 'Studio' not in [c.name for c in o.users_collection]]
bb={o.name:bounds(o) for o in allmeshes}
check(len(bpy.data.scenes)==9,'Nine Blender review scenes')
check(m['plot']==[85,55],'Masterplan H plot retained: 85 x 55 m')
check(len(m['buildings'])==6,'Six commercial buildings')
check(all(a[0][0]>=-42.501 and a[0][1]<=42.501 and a[1][0]>=-27.501 and a[1][1]<=27.501 for a in bb.values()),'All model geometry remains inside H plot')
rects=[]
for b in m['buildings']:
 x,y=b['center'];w,d=b['size'];rects.append((b['id'],x-w/2,y-d/2,x+w/2,y+d/2))
for i,(id,a,b,c,d) in enumerate(rects):
 for jd,e,f,g,h in rects[i+1:]:check(min(c,g)<=max(a,e) or min(d,h)<=max(b,f),'Buildings disjoint: '+id+' / '+jd)
check(len([o for o in objs('H06_Interior') if o.name.startswith('Salon chair cushion')])==3,'Three styling chairs')
check(len([o for o in objs('H06_Interior') if o.name.startswith('Wash recliner')])==2,'Two shampoo chairs')
for b in m['buildings'][1:]:
 walls=objs(b['id']+'_Shell');ceilings=[o for o in objs(b['id']+'_Roof') if o.name.startswith(('Closed ceiling slab','Roof opening rim'))]
 check(abs(max(bb[o.name][2][1] for o in walls)-min(bb[o.name][2][0] for o in ceilings))<1e-5,b['id']+' wall meets ceiling without vertical gap')
v=m['sourceCafe']
for p,key in [(r,'blendSha256') for r in [R/'reference/cafe/H01-Cafe.blend',R.parent/'cafe-3d-v1/blender-validation/H01-Cafe.blend']]+[(r,'glbSha256') for r in [R/'reference/cafe/H01-cafe.glb',R.parent/'cafe-3d-v1/H01-cafe.glb']]:
 check(hashlib.sha256(p.read_bytes()).hexdigest()==v[key],'Cafe source unchanged: '+str(p.relative_to(R.parent)))
records=json.loads((R/'reference/cafe-import-snapshot.json').read_text());cafetri=0
for rec in records:
 o=bpy.data.objects['H01__'+rec['name']];o.data.calc_loop_triangles();cafetri+=len(o.data.loop_triangles)
 assert len(o.data.loop_triangles)==rec['triangles']
 expected=Matrix.Translation(Vector(v['translation']))@Matrix(rec['matrix'])
 if rec['name']=='RearServiceDoor':
  pivot=Vector((-26.5+4.62,11.5+4.41,0));expected=Matrix.Translation(pivot)@Matrix.Rotation(math.pi/2,4,'Z')@Matrix.Translation(-pivot)@expected
 if rec['name']=='ServicePrepTable':expected=Matrix.Translation(Vector((-20.27,14.7,0)))@Matrix.Rotation(math.pi/2,4,'Z')@Matrix.Translation(Vector((21,-15.3,0)))@expected
 if rec['name'] in ['Fridge','FridgeHandle']:expected=Matrix.Translation(Vector((-.12,0,0)))@expected
 assert max(abs(o.matrix_world[i][j]-expected[i][j]) for i in range(4) for j in range(4))<1e-4,rec['name']
check(len(records)==790 and cafetri==27670,'All 790 cafe meshes retain geometry and expected placement; rear door and receiving furniture explicitly adjusted')
check(len([i for i in bpy.data.images if i.packed_file])>=8,'Cafe packed textures retained')
# Geometry-backed 0.25 m grid with a 0.35 m body radius. Only ground-floor walking surfaces.
walkobjects=[]
for o in allmeshes:
 cs=[c.name for c in o.users_collection]
 if any(c=='Paths' or c.endswith('_Floor') or c.endswith('_Approach') for c in cs):walkobjects.append(o)
 elif any(c.startswith('H01_') for c in cs) and any(t in o.name for t in ['__Foundation','__TerraceSlab','__OakFloor']) and bb[o.name][2][1]<.3:walkobjects.append(o)
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
walk={(i,j) for i in range(-168,169) for j in range(-108,109) if clear(i*.25,j*.25)}
start=(0,-106);check(start in walk,'South portal body clearance');q=deque([start]);seen={start}
while q:
 i,j=q.popleft()
 for n in [(i-1,j),(i+1,j),(i,j-1),(i,j+1)]:
  if n in walk and n not in seen:seen.add(n);q.append(n)
goals={'west':(-42,-1.5),'east':(42,-1.5),'north':(0,27),'cafeEntry':(-26.5,7.75),'cafeRearInside':(-21.25,15.25),'cafeRearThreshold':(-21.25,16)}
for b in m['buildings'][1:]:
 x,y=b['center'];sign=1 if b['door']=='s' else -1
 for name,xx,yy in [('entry',0,-4),('rearInside',0,4),('backroom',2.5 if b['id']=='H06' else 0,3.0),('WC',b['size'][0]/2-1.85,3.1)]:goals[b['id']+name]=(x+sign*xx,y+sign*yy)
for name,(x,y) in goals.items():check((round(x*4),round(y*4)) in seen,'Continuous body route reaches '+name)
# All paving tiles are disjoint in XY, so no coplanar duplicate walkway faces.
for i,r in enumerate(m['paths']):
 for t in m['paths'][i+1:]:assert min(r[2],t[2])-max(r[0],t[0])<1e-6 or min(r[3],t[3])-max(r[1],t[1])<1e-6
check(True,'Public paving union has no overlapping tiles')
scenes=list(bpy.data.scenes.keys());bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(R/'H-daily-shops.glb'))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];tri=degen=0
for o in meshes:
 o.data.calc_loop_triangles();tri+=len(o.data.loop_triangles)
 for v in o.data.vertices:assert all(math.isfinite(x) for x in v.co)
 for t in o.data.loop_triangles:
  a,b,c=[o.data.vertices[i].co for i in t.vertices]
  if (b-a).cross(c-a).length<1e-10:degen+=1
check(len(meshes)==m['meshObjects'],'GLB mesh count equals source');check(tri==m['triangles'],'GLB triangle count equals source');check(degen==0,'GLB zero degenerate triangles');check(hashlib.sha256((R/'H-daily-shops.glb').read_bytes()).hexdigest()==m['sha256'],'GLB current hash')
result={'status':'PASS','date':'2026-10-15','blender':bpy.app.version_string,'checks':len(checks),'scenes':scenes,'meshObjects':len(meshes),'triangles':tri,'degenerateTriangles':degen,'sampledWalkCells':len(walk),'reachableCells':len(seen),'bodyRadius':.35,'rayBoundaryToleranceMetres':.00002,'gridSpacing':.25,'reachableGoals':goals,'sha256':m['sha256'],'items':checks,'scope':'Static sampled ground-floor entry routes; not runtime collision, stair traversal or regulatory accessibility certification'}
(R/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print('ALL VALIDATION PASS',len(checks),'assertions;',len(seen),'reachable grid cells;',len(meshes),'meshes;',tri,'triangles')
