import bpy,json,math,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
results={}
for key,code in [('clinic','B03'),('library','B02')]:
 p=ROOT/key;meta=json.loads((p/'manifest.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(p/(code+'-'+key+'.blend')))
 expected={'01 Exterior','02 Interior','03 Plan'}
 if key=='library':expected|={'04 Upper Interior','05 Upper Plan'}
 assert set(bpy.data.scenes.keys())==expected
 if key=='library':
  assert len([o for o in bpy.data.objects if o.name.startswith('Stair tread')])==22
  def bounds(o):
   vs=[o.matrix_world@v.co for v in o.data.vertices]
   return [(min(v[i] for v in vs),max(v[i] for v in vs)) for i in range(3)]
  stairs=[o for o in bpy.data.objects if o.name.startswith('Stair tread')]
  slabs=[o for o in bpy.data.objects if o.name.startswith('Upper slab')]
  for st in stairs:
   a=bounds(st)
   for slab in slabs:
    b=bounds(slab)
    assert not all(min(a[i][1],b[i][1])-max(a[i][0],b[i][0])>1e-5 for i in range(3)), 'Stair intersects slab'
  assert abs(max(bounds(o)[2][1] for o in stairs)-3.9925)<1e-4

  for n in ['02 Interior','03 Plan']:
   assert bpy.data.scenes[n].view_layers[0].layer_collection.children['UpperFloor'].exclude
  assert not bpy.data.scenes['04 Upper Interior'].view_layers[0].layer_collection.children['UpperFloor'].exclude
 else:
  assert bpy.data.objects.get('Medical red cross') is not None
 for name in ['02 Interior','03 Plan']:
  assert all(bpy.data.scenes[name].view_layers[0].layer_collection.children[c].exclude for c in ['Roof','FrontFacade','EastFacade'])
 scenes=list(bpy.data.scenes.keys());bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(p/meta['asset']));meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];tri=0;coords=[]
 for o in meshes:
  o.data.calc_loop_triangles();tri+=len(o.data.loop_triangles);assert len(o.data.materials)>0
  for v in o.data.vertices:
   assert all(math.isfinite(x) for x in v.co)
   coords.append(o.matrix_world@v.co)
 bounds=[max(v[i] for v in coords)-min(v[i] for v in coords) for i in range(3)]
 assert len(meshes)==meta['meshObjects'];assert tri==meta['triangles'];assert meta['degenerateTriangles']==0
 results[key]={'status':'PASS','blender':bpy.app.version_string,'blendScenes':scenes,'glbMeshes':len(meshes),'triangles':tri,'boundsBlenderXYZ':bounds,'materialCount':len(bpy.data.materials),'missingMaterials':0,'sha256':hashlib.sha256((p/meta['asset']).read_bytes()).hexdigest()}
(ROOT/'validation.json').write_text(json.dumps(results,ensure_ascii=False,indent=2));print('VALIDATION',json.dumps(results),flush=True)
