"""Reopen every saved Blender project, then independently reimport its exported GLB."""
import bpy,json,math,time
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent.parent
reports=[]
for p in sorted((R/'assets').glob('*/manifest.json')):
 c=json.loads(p.read_text());checks=[]
 def check(name,value,info=None):checks.append({'name':name,'pass':bool(value),'info':info})
 bpy.ops.wm.open_mainfile(filepath=str(p.parent/'character.blend'))
 rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
 check('65 bones on native reopen',len(rig.data.bones)==65)
 acts={a.name:a for a in bpy.data.actions};check('30 actions on native reopen',set(c['actions'])==set(acts))
 check('Packed textures available',all(i.packed_file or i.source=='GENERATED' for i in bpy.data.images if i.type=='IMAGE'))
 meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];bad=[];basis=[]
 for o in meshes:
  if o.data.shape_keys:
   basis.append(max((v.co-k.co).length for v,k in zip(o.data.vertices,o.data.shape_keys.key_blocks[0].data)))
  for v in o.data.vertices:
   if not all(math.isfinite(x) for x in v.co) or abs(sum(g.weight for g in v.groups)-1)>.001:bad.append(o.name);break
 check('Finite native mesh with normalized weights',not bad,bad)
 check('Basis geometry matches native vertex geometry',not basis or max(basis)<.00001,basis)
 rig.animation_data.action=acts['Idle'];bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
 skin=next(o for o in meshes if o.name=='Skin');ev=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());z=[(ev.matrix_world@v.co).z for v in ev.data.vertices]
 check('Native skull height within 5cm of design',abs(max(z)-c['design']['height'])<.05,{'skullZ':max(z),'design':c['design']['height']})
 # A dedicated import scene avoids accidentally validating the still-loaded original.
 bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.ops.import_scene.gltf(filepath=str(p.parent/'character.glb'))
 imported=[o for o in bpy.context.scene.objects if o.type=='ARMATURE']
 check('GLB imports as one65-bone rig',len(imported)==1 and len(imported[0].data.bones)==65)
 check('GLB retains30 actions',len(bpy.data.actions)==30,len(bpy.data.actions))
 reports.append({'id':c['id'],'name':c['name'],'checks':checks,'failed':[x for x in checks if not x['pass']]})
 print('NATIVE_REOPEN',c['id'],sum(x['pass'] for x in checks),'/',len(checks),flush=True)
out={'residents':len(reports),'passed':sum(x['pass'] for r in reports for x in r['checks']),'total':sum(len(r['checks']) for r in reports),'reports':reports}
(R/'qa/native-validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
assert len(reports)==45 and all(not r['failed'] for r in reports),out
