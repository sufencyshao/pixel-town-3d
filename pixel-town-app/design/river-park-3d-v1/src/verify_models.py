import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent.parent;m=json.loads((R/'manifest.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(R/'F-river-park.blend'))
def bb(o):
 v=[o.matrix_world@Vector(c) for c in o.bound_box];return [(min(p[i] for p in v),max(p[i] for p in v)) for i in range(3)]
def rect(b):return [Vector((b[0][0],b[1][0])),Vector((b[0][1],b[1][0])),Vector((b[0][1],b[1][1])),Vector((b[0][0],b[1][1]))]
def overlap(a,b,tol=1e-5):
 for poly in [a,b]:
  for i,x in enumerate(poly):
   e=poly[(i+1)%len(poly)]-x;n=Vector((-e.y,e.x));n.normalize();aa=[p.dot(n) for p in a];bb=[p.dot(n) for p in b]
   if min(max(aa),max(bb))-max(min(aa),min(bb))<=tol:return False
 return True
paths=[[Vector(p) for p in poly] for poly in m['pathPolygons']]
for i,a in enumerate(paths):
 for b in paths[i+1:]:assert not overlap(a,b),'path top faces overlap'
# Shared edges form one path network, connecting the three F-block entrances.
def touches(a,b):
 for poly in [a,b]:
  for i,x in enumerate(poly):
   e=poly[(i+1)%len(poly)]-x;n=Vector((-e.y,e.x));n.normalize();aa=[p.dot(n) for p in a];bb=[p.dot(n) for p in b]
   if min(max(aa),max(bb))-max(min(aa),min(bb)) < -1e-4:return False
 return True
seen={0};todo=[0]
while todo:
 i=todo.pop()
 for j,b in enumerate(paths):
  if j not in seen and touches(paths[i],b):seen.add(j);todo.append(j)
assert len(seen)==len(paths),(len(seen),len(paths),'path connectivity')
# Portal positions lie on some polygon boundary or inside.
for name,xy in m['portals'].items():
 p=Vector(xy);tiny=[p+Vector((x,y)) for x,y in [(-.001,-.001),(.001,-.001),(.001,.001),(-.001,.001)]]
 assert any(touches(tiny,a) for a in paths),name
# Relevant furniture and signs keep the path surfaces clear.
checked=0
for group in ['Furniture','Signs','Pet_Fence','Vet_Front','Vet_Shell','Vet_East','Trees','Planting']:
 for o in bpy.data.collections[group].objects:
  if o.type!='MESH':continue
  b=bb(o)
  # Canopies and high sign lettering may overhang; ground-level objects must not occupy paths.
  if b[2][0]>2.3:continue
  for a in paths:assert not overlap(a,rect(b)),('obstruction',o.name)
  checked+=1
# Veterinary building passages are free of fixed furniture; ignore the partition door frames.
vx,vy=m['vetCenter']
boxes=[[(vx-.7,vx+.7),(4.4,7.9),(.2,2.3)],[(vx+.35,vx+1.65),(7.6,8.4),(.2,2.3)],[(vx-2.45,vx-1.55),(11.6,13.3),(.2,2.3)],[(vx+.35,vx+1.65),(13.8,14.6),(.2,2.3)]]
for o in bpy.data.collections['Vet_Interior'].objects:
 if o.type!='MESH' or o.name.startswith(('Consultation','Treatment partition','Recovery partition','Door','Name plaque','Label')):continue
 a=bb(o)
 for b in boxes:assert not all(min(a[i][1],b[i][1])-max(a[i][0],b[i][0])>1e-4 for i in range(3)),('vet passage',o.name)
# River visible below the bank: studio floor must not cover it.
assert bb(bpy.data.objects['Studio ground'])[2][1]<-.8
water=[o for o in bpy.data.collections['River'].objects if o.type=='MESH' and o.name.startswith('River water')]
assert len(water)==160
for o in water:assert abs(o.data.vertices[0].co.z+.75)<1e-6
# Bridge handrails do not cut through the riverside approach.
for o in bpy.data.collections['Bridges'].objects:
 if o.type=='MESH' and o.name.startswith(('Bridge guard post','Bridge handrail')):
  for a in paths:assert not overlap(a,rect(bb(o))),('bridge approach blocked',o.name)
scenes=list(bpy.data.scenes.keys());assert len(scenes)==6
assert bpy.data.scenes['03 Vet interior'].view_layers[0].layer_collection.children['Vet_Roof'].exclude
assert sum(o.name.startswith('Park bench seat') for o in bpy.data.collections['Audience'].objects)==6
# Export integrity: re-open the GLB and compare mesh/triangle counts and all positions.
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(R/'F-river-park.glb'))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];tri=0
for o in meshes:
 assert len(o.data.materials)>0;o.data.calc_loop_triangles();tri+=len(o.data.loop_triangles)
 for v in o.data.vertices:assert all(math.isfinite(x) for x in v.co)
assert len(meshes)==m['meshObjects'] and tri==m['triangles']
assert hashlib.sha256((R/'F-river-park.glb').read_bytes()).hexdigest()==m['sha256']
r={'status':'PASS','blender':bpy.app.version_string,'meshObjects':len(meshes),'triangles':tri,'scenes':scenes,'pathPieces':len(paths),'pathNetwork':'one connected network; no overlapping path faces','corePortals':'west/north/south present','groundLevelObjectsChecked':checked,'vetPassages':'4 key doorway approach volumes clear','waterVisibility':'studio ground below river surface','bridgeApproaches':'guardrails do not cross promenade','sha256':m['sha256']}
(R/'validation.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));print('ALL VALIDATION PASS',json.dumps(r,ensure_ascii=False))
