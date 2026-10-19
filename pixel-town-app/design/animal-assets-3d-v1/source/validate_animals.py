import bpy,json,math
from pathlib import Path
from mathutils import Vector
B=Path(__file__).resolve().parents[1];M=json.loads((B/'assets/manifest.json').read_text());out=[]
def bounds(sc):
 dg=bpy.context.evaluated_depsgraph_get();pts=[o.evaluated_get(dg).matrix_world@v.co for o in sc.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers) for v in o.evaluated_get(dg).data.vertices]
 return [[min(v[i] for v in pts) for i in range(3)],[max(v[i] for v in pts) for i in range(3)]]
for a in M['animals']:
 rec={'id':a['id'],'native':{},'gltf':{}};bpy.ops.wm.open_mainfile(filepath=str(B/'assets'/(a['id']+'.blend')));ar=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');sc=bpy.context.scene
 rec['native']['reopened']=True;rec['native']['boneCount']=len(ar.data.bones);rec['native']['imagesPacked']=all(i.packed_file is not None for i in bpy.data.images if i.source=='FILE' and i.size[0]>8)
 for t in ar.animation_data.nla_tracks:t.mute=True
 rec['native']['clips']={}
 for ac in bpy.data.actions:
  ar.animation_data.action=ac
  if len(ac.slots):ar.animation_data.action_slot=ac.slots[0]
  zz=[];rootxy=[];changed=set();b0={};finite=True
  root=ar.pose.bones.get('MotionRoot') or ar.pose.bones.get('Body') or ar.pose.bones.get('root') or ar.pose.bones.get('body')
  for j in range(9):
   sc.frame_set(round(ac.frame_range[0]+(ac.frame_range[1]-ac.frame_range[0])*j/8));b=bounds(sc);zz.append(b)
   rootxy.append(list((ar.matrix_world@root.head)[:2]))
   for p in ar.pose.bones:
    vals=[x for row in p.matrix for x in row];finite &= all(math.isfinite(x) for x in vals)
    if j==0:b0[p.name]=vals
    elif any(abs(vals[i]-b0[p.name][i])>1e-5 for i in range(16)):changed.add(p.name)
  rec['native']['clips'][ac.name]={'minZ':min(b[0][2] for b in zz),'maxZ':max(b[1][2] for b in zz),'finite':finite,'movingBones':len(changed),'rootHorizontalRange':max(math.dist(v,rootxy[0]) for v in rootxy),'maxSpan':max(max(b[1][i]-b[0][i] for i in range(3)) for b in zz)}
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(B/a['glb']));ar=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');rec['gltf']['reimported']=True;rec['gltf']['boneCount']=len(ar.data.bones);rec['gltf']['actions']=[ac.name for ac in bpy.data.actions];rec['gltf']['clipNamesMatch']=set(rec['gltf']['actions'])==set(a['actions']);rec['gltf']['skinnedMeshes']=sum(1 for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers));out.append(rec)
 (B/'qa'/'validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print('VALIDATED',a['id'],flush=True)
print('ALL',len(out))
