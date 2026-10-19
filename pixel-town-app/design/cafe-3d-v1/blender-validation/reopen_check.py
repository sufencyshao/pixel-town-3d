import bpy,json
from pathlib import Path
p=Path('/Users/summerwindy/Desktop/AI Chat/pixel-town-app/design/cafe-3d-v1/blender-validation')
r={'file':bpy.data.filepath,'version':bpy.app.version_string,'scenes':{},'packed_images':[]}
for s in bpy.data.scenes:
 r['scenes'][s.name]={'camera':s.camera.name,'excluded_collections':[x.name for x in s.view_layers[0].layer_collection.children if x.exclude]}
for i in bpy.data.images:
 if i.type=='IMAGE':r['packed_images'].append({'name':i.name,'packed':bool(i.packed_file),'size':list(i.size),'has_data':i.has_data})
print(json.dumps(r),flush=True)
assert '01 Exterior' in r['scenes'] and '02 Interior Cutaway' in r['scenes']
assert set(r['scenes']['02 Interior Cutaway']['excluded_collections'])=={'02 Roof','03 FrontFacade','04 EastFacade'}
assert not r['scenes']['01 Exterior']['excluded_collections']
assert len(r['packed_images'])==8 and all(i['packed'] and i['has_data'] for i in r['packed_images'])
r['result']='PASS';(p/'reopen-check.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));print(json.dumps(r))
