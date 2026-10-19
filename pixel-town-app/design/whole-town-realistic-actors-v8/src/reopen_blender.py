import bpy,json,math
from pathlib import Path
R=Path(__file__).resolve().parent.parent
bpy.ops.wm.open_mainfile(filepath=str(R/'Town-with-original-actors.blend'))
actors=json.loads((R/'actors.json').read_text());positions=[]
for a in actors:
 o=bpy.data.objects.get(a['id']);assert o,a['id'];p=o.matrix_world.translation;expected=(a['position'][0],-a['position'][2],a['position'][1]);error=math.dist(p,expected);assert error<.001,(a['id'],list(p),expected);positions.append({'id':a['id'],'position':list(p),'error':error})
report={'reopened':True,'actors':len(positions),'armatures':sum(o.type=='ARMATURE' for o in bpy.data.objects),'externalImages':len([i for i in bpy.data.images if i.source=='FILE' and not i.packed_file]),'positions':positions};(R/'qa/blender-reopen.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('Reopened and checked',len(positions),'actor transforms')
