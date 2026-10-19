import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from collections import deque
R=Path(__file__).resolve().parent.parent;m=json.loads((R/'manifest.json').read_text());checks=[]
def ck(v,n):
 assert v,n
 checks.append(n)
bpy.ops.wm.open_mainfile(filepath=str(R/'Town-complete.blend'));bpy.context.window.scene=bpy.data.scenes['01 Whole town'];bpy.context.view_layer.update()
ck(len(bpy.data.scenes)==4,'Four overall review scenes saved')
ck(set(m['zones'])==set('ABCDEFGHI'),'All nine districts assembled')
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and not any(c.name=='Studio' for c in o.users_collection)]
ck(len(meshes)==m['meshObjects'],'Saved Blender mesh count')
ck(not any('reserved' in o.name or 'Context' in o.name for o in meshes),'No old B placeholder or duplicated AC context')
for key,s in m['sources'].items():
 d=R.parent/s['folder'];ck(hashlib.sha256((d/s['blend']).read_bytes()).hexdigest()==s['blendSha256'],key+' original Blender unchanged');ck(hashlib.sha256((d/Path(s['blend']).with_suffix('.glb')).read_bytes()).hexdigest()==s['glbSha256'],key+' original GLB unchanged')
for z in 'BDEGHI':ck(m['sourceStats'][z]['triangles']==m['sources'][z]['metaTriangles'],z+' entire district triangle count retained')
for z in 'ABCDEFGHI':
 objects=[o for o in meshes if o.name.startswith(z+'__')];ck(bool(objects),z+' collection has geometry');tri=0
 for o in objects:o.data.calc_loop_triangles();tri+=len(o.data.loop_triangles)
 removed=sum(v for k,v in m['degenerateCleanup'].items() if k.startswith(z+'__'));ck(tri+removed==m['sourceStats'][z]['triangles'],z+' retained triangles reconcile with recorded zero-area cleanup')
 for o in objects:
  for v in o.data.vertices:assert all(math.isfinite(f) for f in v.co)
ck(m['residentialCapacity']=={'residentHomes':46,'heroHome':1,'hotelRooms':6},'Residential and hotel capacities retained')
# Public surfaces use actual upward triangles. Private entrances and room navigation remain source-zone scope.
walkvs=[];walkfs=[];solidvs=[];solidfs=[];bounds=[[],[],[]]
for o in meshes:
 name=o.name;me=o.data;me.calc_loop_triangles();vs=[o.matrix_world@v.co for v in me.vertices]
 for i in range(3):bounds[i].extend([min(v[i] for v in vs),max(v[i] for v in vs)])
 iswalk=any(x in name for x in ['__Paths','__Paving','__Bridges','__Riverside_Paths','__Transitions','__Far_Bank'])
 if iswalk:
  for t in me.loop_triangles:
   ps=[vs[i] for i in t.vertices];normal=(ps[1]-ps[0]).cross(ps[2]-ps[0])
   if normal.z>1e-9 and min(p.z for p in ps)>=.03 and max(p.z for p in ps)<.31:
    # Far bank collection also contains ground and trees: only the raised .13m path qualifies.
    if name=='F__Far_Bank' and not all(abs(p.z-.13)<1e-4 for p in ps):continue
    off=len(walkvs);walkvs.extend(ps);walkfs.append((off,off+1,off+2))
 # Only actual triangles around pedestrian body height need obstacle checks.
 for t in me.loop_triangles:
  ps=[vs[i] for i in t.vertices]
  if max(p.z for p in ps)<.24 or min(p.z for p in ps)>2.2:continue
  off=len(solidvs);solidvs.extend(ps);solidfs.append((off,off+1,off+2))
ck(min(bounds[0])>=-135.5 and max(bounds[0])<=165.5 and min(bounds[1])>=-110.5 and max(bounds[1])<=115.5,'Town geometry within site and small boundary tree overhang allowance')
walkBVH=BVHTree.FromPolygons(walkvs,walkfs,all_triangles=True);solidBVH=BVHTree.FromPolygons(solidvs,solidfs,all_triangles=True)
def paved(x,y):
 return any(walkBVH.ray_cast(Vector((x+dx,y+dy,.5)),Vector((0,0,-1)),.48)[0] is not None for dx,dy in [(0,0),(.00004,0),(-.00004,0),(0,.00004),(0,-.00004)])
def clear(x,y):
 if not paved(x,y):return False
 if not all(paved(x+dx,y+dy) for dx,dy in [(.35,0),(-.35,0),(0,.35),(0,-.35),(.247,.247),(-.247,.247),(.247,-.247),(-.247,-.247)]):return False
 hits=[walkBVH.ray_cast(Vector((x+dx,y+dy,.5)),Vector((0,0,-1)),.48)[0] for dx,dy in [(0,0),(.00004,0),(-.00004,0),(0,.00004),(0,-.00004)]]
 ground=max(v.z for v in hits if v is not None)
 return all(solidBVH.find_nearest(Vector((x,y,ground+z)),.35)[0] is None for z in [.5,1.15,1.75])
# Grid remains .5m globally; additionally check each exact portal point and both sides of its ramp.
walk={(i,j) for i in range(-266,327) for j in range(-216,225) if clear(i*.5,j*.5)}
start=(0,-212);ck(start in walk,'South town arrival point clear');q=deque([start]);seen={start}
while q:
 i,j=q.popleft()
 for n in [(i-1,j),(i+1,j),(i,j-1),(i,j+1)]:
  if n in walk and n not in seen:seen.add(n);q.append(n)
reached=[]
for p in m['portals']:
 x,y,z=p['point'];near=[(i,j) for i in range(round(x*2)-1,round(x*2)+2) for j in range(round(y*2)-1,round(y*2)+2) if math.hypot(i*.5-x,j*.5-y)<=.55]
 ck(clear(x,y),'Portal body clearance '+p['zone']+'/'+p['name']);ck(any(n in seen for n in near),'Connected public network reaches '+p['zone']+'/'+p['name']);reached.append(p['zone']+'/'+p['name'])
for label,x,y in [('northBridge',130,35),('southBridge',130,-36.25),('northPromenade',123,75),('farTrailCentre',144,0)]:
 near=[n for n in seen if math.hypot(n[0]*.5-x,n[1]*.5-y)<2.5];ck(bool(near),'Public route reaches '+label)
print('PUBLIC WALK PASS',len(reached),len(seen),flush=True)
# Export round-trip and UV/texture preservation, independently of source collections.
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(R/'Town-complete.glb'))
loaded=[o for o in bpy.context.scene.objects if o.type=='MESH'];tri=0;bad=0
for o in loaded:
 o.data.calc_loop_triangles();tri+=len(o.data.loop_triangles)
 for t in o.data.loop_triangles:
  a,b,c=[o.data.vertices[i].co for i in t.vertices]
  if (b-a).cross(c-a).length<1e-10:bad+=1
ck(len(loaded)==m['meshObjects'],'GLB round-trip retains part mesh count');ck(tri==m['triangles'],'GLB round-trip retains triangle count');ck(bad==0,'No degenerate triangles');ck(len([i for i in bpy.data.images if i.packed_file])>=8,'Cafe texture images imported and packed');ck(hashlib.sha256((R/'Town-complete.glb').read_bytes()).hexdigest()==m['sha256'],'Final GLB hash matches manifest')
r={'status':'PASS','date':'2026-10-15','checks':len(checks),'items':checks,'meshObjects':len(loaded),'triangles':tri,'degenerateTriangles':bad,'gridSpacing':.5,'bodyRadius':.35,'reachablePortals':reached,'sampledCells':len(walk),'reachableCells':len(seen),'sha256':m['sha256'],'scope':'Static public-route sampling and export validation; not runtime navigation, regulatory certification, or exhaustive collision testing'}
(R/'validation.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));print('ALL TOWN VALIDATION PASS',len(checks),flush=True)
