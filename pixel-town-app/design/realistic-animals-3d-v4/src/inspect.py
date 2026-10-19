import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parent.parent
result={}
for source in [R/'vendor/oga/benny.blend',R/'vendor/oga/jack-russell.blend',R/'vendor/oga/shrike/bird_yellow_billed_shrike/bird_shrike1.blend']:
 bpy.ops.wm.open_mainfile(filepath=str(source))
 result[source.name]={'objects':[{'name':o.name,'type':o.type,'bones':len(o.data.bones) if o.type=='ARMATURE' else None,'materials':[s.material.name if s.material else None for s in o.material_slots],'uv':[u.name for u in o.data.uv_layers] if o.type=='MESH' else None} for o in bpy.data.objects], 'materials':{m.name:{'nodes':[(n.type,n.image.name if n.type=='TEX_IMAGE' and n.image else None) for n in m.node_tree.nodes] if m.node_tree else [],'links':[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in m.node_tree.links] if m.node_tree else []} for m in bpy.data.materials},'images':[{'name':i.name,'path':i.filepath,'packed':bool(i.packed_file),'size':list(i.size)} for i in bpy.data.images], 'actions':[{'name':a.name,'frames':list(a.frame_range)} for a in bpy.data.actions]}
(R/'qa/source-inspection.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
