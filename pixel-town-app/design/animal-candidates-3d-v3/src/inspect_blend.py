import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parent.parent
report={}
for name in ['rabbit','bird']:
 bpy.ops.wm.open_mainfile(filepath=str(R/'vendor/oga'/f'{name}.blend'))
 report[name]={'objects':[{'name':o.name,'type':o.type,'vertices':len(o.data.vertices) if o.type=='MESH' else None,'bones':len(o.data.bones) if o.type=='ARMATURE' else None,'modifiers':[(m.name,m.type) for m in o.modifiers]} for o in bpy.data.objects], 'actions':[{'name':a.name,'range':list(a.frame_range)} for a in bpy.data.actions], 'materials':[{'name':m.name,'nodes':[(n.name,n.type) for n in m.node_tree.nodes] if m.node_tree else None,'color':list(m.diffuse_color)} for m in bpy.data.materials], 'images':[{'name':i.name,'packed':bool(i.packed_file),'path':i.filepath,'size':list(i.size)} for i in bpy.data.images]}
(R/'qa/source-blend-inspection.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False))
