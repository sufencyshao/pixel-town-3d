import bpy,json,math,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
results={}
for key,code in [('clinic','B03'),('library','B02')]:
 p=ROOT/key;meta=json.loads((p/'manifest.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(p/(code+'-'+key+'.blend')))
 assert set(bpy.data.scenes.keys())=={'01 Exterior','02 Interior','03 Plan'}
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
