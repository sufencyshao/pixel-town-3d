import bpy,json,math,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent.parent
meta=json.loads((R/'manifest.json').read_text());checks=[]
def check(value,name):
 assert value,name
 checks.append(name)
bpy.ops.wm.open_mainfile(filepath=str(R/'D-craft-workshops.blend'))
bpy.context.view_layer.update()
def objs(c):return [o for o in bpy.data.collections[c].objects if o.type=='MESH']
def bounds(o):
 from mathutils import Vector
 vs=[o.matrix_world@Vector(v) for v in o.bound_box]
 return [(min(v[i] for v in vs),max(v[i] for v in vs)) for i in range(3)]
def overlap(a,b,d=3):return all(min(a[i][1],b[i][1])-max(a[i][0],b[i][0])>1e-4 for i in range(d))
bb={o.name:bounds(o) for o in bpy.data.objects if o.type=='MESH'}
check(len(bpy.data.scenes)==7,'Seven saved review scenes')
for s,id in [('03 Woodworking','D01'),('04 Repair','D02'),('05 Art studio','D03'),('06 Rehearsal','D04')]:
 for suffix in ['Roof','Front']:check(bpy.data.scenes[s].view_layers[0].layer_collection.children[id+'_'+suffix].exclude,s+' cut '+suffix)
plan_path=R.parent/'town-3d-masterplan-v1/plan-data.json'
if not plan_path.exists():plan_path=R/'reference/masterplan-D.json'
plan=json.loads(plan_path.read_text())
# Compare against actual plan buildings regardless of other zone revisions.
source=next(v for v in plan.values() if isinstance(v,list) and any(isinstance(b,dict) and b.get('id')=='D01' for b in v))
for b in meta['buildings']:
 expected=next(v for v in source if v['id']==b['id'])
 check(b['size']==[expected['w']/4,expected['h']/4],b['id']+' footprint matches masterplan')
 check(b['center']==[(expected['x']+expected['w']/2-270)/4,(540-expected['y']-expected['h']/2)/4],b['id']+' placement matches masterplan')
 x,y=b['center'];w,d=b['size']
 check(x-w/2>=-37.5 and x+w/2<=37.5 and y-d/2>=-27.5 and y+d/2<=27.5,b['id']+' inside site')
 foundation=bb[b['id']+' foundation'];check(abs(foundation[2][1]-.18)<1e-5,b['id']+' foundation meets wall base')
 roof=objs(b['id']+'_Roof');low=min(bb[o.name][2][0] for o in roof if 'ceiling' in o.name or 'flat roof' in o.name or 'opening ring' in o.name)
 check(abs(low-4.18)<1e-4,b['id']+' wall top meets roof slab')
 for o in objs(b['id']+'_Interior'):
  a=bb[o.name]
  check(a[0][0]>=x-w/2-.01 and a[0][1]<=x+w/2+.01 and a[1][0]>=y-d/2-.01 and a[1][1]<=y+d/2+.01,b['id']+' contained: '+o.name)
paths=[bb[o.name] for o in objs('Paths')]
check(all(not overlap(a,b,2) for i,a in enumerate(paths) for b in paths[i+1:]),'No coplanar path overlaps')
seen={0};pending=[0]
while pending:
 a=paths[pending.pop()]
 for j,b in enumerate(paths):
  if j in seen:continue
  gaps=[min(a[k][1],b[k][1])-max(a[k][0],b[k][0]) for k in range(2)]
  if min(gaps)>-1e-4 and max(gaps)>1e-4:seen.add(j);pending.append(j)
check(len(seen)==len(paths),'One connected path network')
for name,(x,y) in meta['portals'].items():check(any(a[0][0]-1e-4<=x<=a[0][1]+1e-4 and a[1][0]-1e-4<=y<=a[1][1]+1e-4 for a in paths),'Portal connected: '+name)
for b in meta['buildings']:check(all(not overlap(bb[b['id']+' foundation'],a,2) for a in paths),b['id']+' paths outside foundation')
for o in objs('Wayfinding'):check(all(not overlap(bb[o.name],a,2) for a in paths),'Sign off path: '+o.name)
# Entrances and the principal work aisles, tested as walking volumes above the floor.
corridors={'D01':[[(-19.6,-17.9),(2.25,14),(.25,2.6)],[(-32.7,-5.6),(9.25,10.75),(.25,2.6)]],'D02':[[(16.3,17.7),(2.25,16.7),(.25,2.6)],[(24.1,25.9),(15.0,17.8),(.25,2.6)]],'D03':[[(-19.5,-18),(-18,-7.25),(.25,2.6)]],'D04':[[(16.2,17.8),(-13,-7.25),(.25,2.6)],[(20.8,22),(-16,-11.5),(.56,2.6)]]}
for bid,volumes in corridors.items():
 for i,vol in enumerate(volumes):
  blockers=[o.name for group in ['Interior','Shell','Front'] for o in objs(bid+'_'+group) if overlap(vol,bb[o.name])]
  check(not blockers,bid+' clear corridor '+str(i)+str(blockers))
# Central lane must be clear of solid street fixtures at pedestrian height.
main=[(-37.5,37.5),(-4.5,-.5),(.15,2.1)]
for c in ['Landscape','Street_Furniture','Wayfinding','Logistics']:
 blockers=[o.name for o in objs(c) if overlap(main,bb[o.name]) and not o.name.startswith(('Courtyard tree canopy','Mixed flower'))]
 check(not blockers,'Clear display lane: '+c+str(blockers))
for collection,base,count in [('D01_Interior','Carpenter workbench',4),('D02_Interior','Cycle repair bay pad',2),('D03_Interior','Canvas painting',6),('D04_Interior','Bass drum shell',1)]:
 check(sum(o.name.split('.')[0]==base for o in objs(collection))==count,'Equipment count: '+base)
# Actual skylight aperture must pass through the studio roof slab to the lantern.
opening=[(-24.55,-12.95),(-15.475,-12.775),(4.19,4.70)]
check(all(not overlap(opening,bb[o.name]) for o in objs('D03_Roof')),'Studio clerestory roof opening is clear')
scenes=list(bpy.data.scenes.keys());bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(R/'D-craft-workshops.glb'))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];tri=0;degen=0
for o in meshes:
 o.data.calc_loop_triangles();tri+=len(o.data.loop_triangles)
 for v in o.data.vertices:assert all(math.isfinite(x) for x in v.co),o.name
 for t in o.data.loop_triangles:
  a,b,c=[o.data.vertices[i].co for i in t.vertices]
  if (b-a).cross(c-a).length<1e-10:degen+=1
check(len(meshes)==meta['meshObjects'],'GLB mesh count matches manifest');check(tri==meta['triangles'],'GLB triangle count matches manifest');check(degen==0,'No degenerate triangles after reimport')
check(hashlib.sha256((R/'D-craft-workshops.glb').read_bytes()).hexdigest()==meta['sha256'],'GLB hash matches manifest')
result={'status':'PASS','date':'2026-10-14','blender':bpy.app.version_string,'checks':len(checks),'scenes':scenes,'meshes':len(meshes),'triangles':tri,'degenerateTriangles':degen,'pathTiles':len(paths),'sha256':meta['sha256'],'items':checks}
(R/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print('ALL VALIDATION PASS',len(checks),'checks',len(meshes),'meshes',tri,'triangles')
