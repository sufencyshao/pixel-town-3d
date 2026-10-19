import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parent.parent
result=[]
for f in (R/'vendor/rocketbox').rglob('*.fbx'):
 bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.ops.import_scene.fbx(filepath=str(f))
 result.append({'file':str(f.relative_to(R)),'actions':[{'name':a.name,'frames':list(a.frame_range)} for a in bpy.data.actions],'armatures':{o.name:len(o.data.bones) for o in bpy.data.objects if o.type=='ARMATURE'},'meshes':len([o for o in bpy.data.objects if o.type=='MESH'])})
(R/'qa/rocketbox-source-inspection.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
