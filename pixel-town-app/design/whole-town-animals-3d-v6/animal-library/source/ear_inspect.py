import bpy
for f in ['ShibaInu','Husky']:
 bpy.ops.wm.open_mainfile(filepath='/Users/summerwindy/Desktop/AI Chat/pixel-town-app/design/animal-assets-3d-v1/source/'+f+'.blend');o=next(o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers));g={v.index:v.name for v in o.vertex_groups};ear={i for i,n in g.items() if n.startswith('Ear')};rm=[v for v in o.data.vertices if sum(w.weight for w in v.groups if w.group in ear)>.35]
 print(f,'eargroups',[(i,g[i]) for i in ear], 'rm',len(rm),'bounds',[[min(v.co[i] for v in rm),max(v.co[i] for v in rm)] for i in range(3)])
 print('head bounds',[[min(v.co[i] for v in o.data.vertices if any(g[w.group]=='Head' and w.weight>.5 for w in v.groups)),max(v.co[i] for v in o.data.vertices if any(g[w.group]=='Head' and w.weight>.5 for w in v.groups))] for i in range(3)])
