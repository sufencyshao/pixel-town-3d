import bpy,json,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent.parent
bpy.ops.wm.open_mainfile(filepath=str(R/'Town-complete.blend'))
bpy.context.window.scene=bpy.data.scenes['01 Whole town'];bpy.context.view_layer.update()
scene=bpy.context.scene;deps=bpy.context.evaluated_depsgraph_get()
# Sample true roof/tree/ground elevations in Blender XY, converted to GLB XZ.
x0,z0=-135,-115;step=.75;nx,nz=401,301;heights=[]
for j in range(nz):
 for i in range(nx):
  hit,loc,*_=scene.ray_cast(deps,Vector((x0+i*step,-(z0+j*step),45)),Vector((0,0,-1)),distance=48)
  heights.append(round(max(-1,loc.z) if hit else -1,3))
# Extract actual lamp diffuser component centres from the merged editable mesh.
o=bpy.data.objects['T__Lamp_Glow'];me=o.data;adj=[set() for _ in me.vertices]
for p in me.polygons:
 ids=list(p.vertices)
 for a,b in zip(ids,ids[1:]+ids[:1]):adj[a].add(b);adj[b].add(a)
seen=set();lamps=[]
for i in range(len(adj)):
 if i in seen:continue
 stack=[i];seen.add(i);group=[]
 while stack:
  j=stack.pop();group.append(o.matrix_world@me.vertices[j].co)
  for n in adj[j]:
   if n not in seen:seen.add(n);stack.append(n)
 p=sum(group,Vector())/len(group);lamps.append([round(p.x,3),round(p.z,3),round(-p.y,3)])
assert len(lamps)==53,len(lamps)
data={'grid':{'x0':x0,'z0':z0,'step':step,'nx':nx,'nz':nz,'heights':heights},'lamps':lamps,'scope':'0.75m sampled top surfaces for rain occlusion; original roof heights retained in cutaway views'}
(R/'environment-data.json').write_text(json.dumps(data,separators=(',',':')))
print('ENVIRONMENT DATA',len(heights),len(lamps),flush=True)
