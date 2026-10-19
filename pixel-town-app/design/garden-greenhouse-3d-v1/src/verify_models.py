import bpy,json,math,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent.parent
m=json.loads((R/'manifest.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(R/'G-garden-greenhouse.blend'))
def bb(o):
 vs=[o.matrix_world@v.co for v in o.data.vertices]
 return [(min(v[i] for v in vs),max(v[i] for v in vs)) for i in range(3)]
def overlap(a,b,dims=3):return all(min(a[i][1],b[i][1])-max(a[i][0],b[i][0])>1e-4 for i in range(dims))
def objects(c):return [o for o in bpy.data.collections[c].objects if o.type=='MESH']
assert len(bpy.data.scenes)==5
assert bpy.data.scenes['03 Greenhouse interior'].view_layers[0].layer_collection.children['Greenhouse_Roof'].exclude
assert bpy.data.scenes['04 Tool house interior'].view_layers[0].layer_collection.children['Tool_Roof'].exclude
assert sum(o.name.startswith('Rotation plot ') for o in objects('Fields'))==4
assert sum(o.name.startswith('Fruit tree trunk') for o in objects('Orchard'))==9
assert sum(o.name.startswith('Growing bench top') for o in objects('Greenhouse_Interior'))==6
paths=[bb(o) for o in objects('Paths')]
for i,a in enumerate(paths):
 for b in paths[i+1:]:assert not overlap(a,b,2),'overlapping path faces'
# Wayfinding signs stand outside walkable paths.
for o in objects('Wayfinding'):
 b=bb(o)
 for a in paths:assert not overlap(a,b,2),('wayfinding obstructs path',o.name)
# Every path tile connects by an edge to one continuous path network.
seen={0};pending=[0]
while pending:
 i=pending.pop();a=paths[i]
 for j,b in enumerate(paths):
  if j in seen:continue
  gaps=[min(a[k][1],b[k][1])-max(a[k][0],b[k][0]) for k in range(2)]
  if min(gaps)>-1e-4 and max(gaps)>1e-4:seen.add(j);pending.append(j)
assert len(seen)==len(paths),(len(seen),len(paths),'disconnected paths')
for n,(x,y) in m['portals'].items():assert any(a[0][0]-.001<=x<=a[0][1]+.001 and a[1][0]-.001<=y<=a[1][1]+.001 for a in paths),n
# Two greenhouse aisles and the east entrance are free of benches and herb beds.
for corridor in [[(-31.8,-7.2),(8.35,9.35),(.22,2.6)],[(-31.8,-7.2),(13.7,14.7),(.22,2.6)],[(-9.5,-6.9),(10.3,12.7),(.22,2.6)]]:
 for o in objects('Greenhouse_Interior'):assert not overlap(corridor,bb(o)),o.name
# Tool-house west entry and route to the south door bypass the packing island.
for corridor in [[(13.1,19.5),(-15.8,-14.2),(.25,2.6)],[(20.9,23.9),(-19.1,-16.1),(.25,2.6)]]:
 for o in objects('Tool_Interior'):assert not overlap(corridor,bb(o)),o.name
# No field or building footprint intersects the main path surfaces.
for n in ['Rotation plot 1','Rotation plot 2','Rotation plot 3','Rotation plot 4','Greenhouse slab','Tool house slab']:
 b=bb(bpy.data.objects[n])
 for a in paths:assert not overlap(a,b,2),('path enters solid footprint',n)
scenes=list(bpy.data.scenes.keys());bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(R/'G-garden-greenhouse.glb'))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];tri=0
for o in meshes:
 o.data.calc_loop_triangles();tri+=len(o.data.loop_triangles)
 for v in o.data.vertices:assert all(math.isfinite(x) for x in v.co)
assert len(meshes)==m['meshObjects'] and tri==m['triangles']
assert hashlib.sha256((R/'G-garden-greenhouse.glb').read_bytes()).hexdigest()==m['sha256']
result={'status':'PASS','blender':bpy.app.version_string,'meshObjects':len(meshes),'triangles':tri,'scenes':scenes,'pathTiles':len(paths),'pathNetwork':'connected, no overlapping top faces','portals':'all reach site boundary','greenhouseAisles':'two 1 m clear test corridors and 2.4 m east doorway','toolHousePassages':'west and south entry approach volumes clear','glbReimport':'mesh and triangle counts match','sha256':m['sha256']}
(R/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print('ALL VALIDATION PASS',json.dumps(result,ensure_ascii=False))
