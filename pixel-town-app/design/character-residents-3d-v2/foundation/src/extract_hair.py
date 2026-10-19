import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];library={}
for p in (R/'vendor/hair').glob('*.gltf'):
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(p))
 o=next(o for o in bpy.context.scene.objects if o.type=='MESH')
 pts=[o.matrix_world@v.co for v in o.data.vertices]
 library[p.stem]={'source':'vendor/hair/'+p.name,'vertices':[list(v) for v in pts],'faces':[list(f.vertices) for f in o.data.polygons],'bounds':[[min(v[i] for v in pts),max(v[i] for v in pts)] for i in range(3)]}
(R/'hair-library.json').write_text(json.dumps(library,separators=(',',':')))
print(json.dumps({k:{'vertices':len(v['vertices']),'bounds':v['bounds']} for k,v in library.items()},indent=2))
