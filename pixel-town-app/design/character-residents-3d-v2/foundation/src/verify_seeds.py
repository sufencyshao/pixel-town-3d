import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector,Quaternion
R=Path(__file__).resolve().parents[1]
M=json.loads((R/'seed-manifest.json').read_text());checks=[]
def check(label,value,extra=None):
 checks.append({'check':label,'pass':bool(value),'details':extra});assert value,(label,extra)

def lighting(scene):
 scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True
 scene.render.resolution_x=800;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
 if scene.world is None:scene.world=bpy.data.worlds.new('QA_World')
 scene.world.color=(.18,.18,.18)
 scene.view_settings.view_transform='AgX'
 for name,loc,power,size in [('Key',(-2,-3,4),250,4),('Fill',(2,-2,2),180,3),('Rim',(0,2,3),300,3)]:
  bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
 bpy.ops.object.camera_add();camera=bpy.context.object;scene.camera=camera;camera.data.type='ORTHO'
 return camera

for seed in M['seeds']:
 key=seed['sex'];bpy.ops.wm.open_mainfile(filepath=str(R/seed['blend']));scene=bpy.context.scene
 rig=bpy.data.objects[seed['rigName']];body=bpy.data.objects['Body'];eyes=bpy.data.objects['Eyes'];brows=bpy.data.objects['Eyebrows']
 check(key+' native bone names',list(rig.data.bones.keys())==M['canonicalBones'])
 check(key+' no active animation',not rig.animation_data)
 check(key+' body topology preserved',len(body.data.vertices)==seed['meshAudit']['Body']['vertices'] and len(body.data.polygons)==seed['meshAudit']['Body']['faces'])
 check(key+' UV kept',len(body.data.uv_layers)>0 and len(eyes.data.uv_layers)>0)
 for o in [body,eyes,brows]:
  check(key+' '+o.name+' all weighted',all(.99<=sum(g.weight for g in v.groups)<=1.01 for v in o.data.vertices))
  check(key+' '+o.name+' skin rig',any(m.type=='ARMATURE' and m.object==rig for m in o.modifiers))
 check(key+' seed full skin single material',[m.name for m in body.data.materials]==['Skin_Neutral'])
 check(key+' images self-contained',all(im.packed_file or im.source=='GENERATED' for im in bpy.data.images),[im.name for im in bpy.data.images])
 for side in ['l','r']:
  u=rig.data.bones['upperarm_'+side];l=rig.data.bones['lowerarm_'+side];t=rig.data.bones['thigh_'+side];c=rig.data.bones['calf_'+side]
  check(key+' '+side+' shoulder T horizontal',abs(u.head_local.z-u.tail_local.z)<.00001)
  check(key+' '+side+' elbow connected distance',(u.tail_local-l.head_local).length<.00001)
  check(key+' '+side+' knee connected distance',(t.tail_local-c.head_local).length<.00001)
  check(key+' '+side+' knee forward of ankle',c.head_local.y<c.tail_local.y)
 camera=lighting(scene)
 for label,pos,scale,target in [('front',(0,-4,1.0),2.05,(0,0,.91)),('side',(4,0,1.0),2.05,(0,0,.91)),('face',(0,-2,1.66),.46,(0,0,seed['height']-.13))]:
  camera.location=pos;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=scale
  scene.render.filepath=str(R/'qa'/f'{key}-{label}.png');bpy.ops.render.render(write_still=True)
 # Native and exported formats are reopened independently; export file availability is not treated as successful import.
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(R/seed['glb']))
 rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
 check(key+' GLB roundtrip65 bones',len(rig.data.bones)==65)
 check(key+' GLB roundtrip names',set(rig.data.bones.keys())==set(M['canonicalBones']))
 check(key+' GLB roundtrip3 meshes',sum(o.type=='MESH' and len(o.vertex_groups)>0 for o in bpy.context.scene.objects)==3)
 check(key+' frozen bytes unchanged',all(hashlib.sha256((R/seed[f]).read_bytes()).hexdigest()==seed['sha256'][f] for f in ['blend','glb']))
# Explicitly quantify rest orientation differences; identical names alone do not prove all local axes match.
A=M['seeds'][0]['restBones'];B=M['seeds'][1]['restBones'];from mathutils import Matrix
axis_diff=[]
for name in M['canonicalBones']:
 qa=Matrix(A[name]['matrixLocal']).to_quaternion();qb=Matrix(B[name]['matrixLocal']).to_quaternion();angle=math.degrees(qa.rotation_difference(qb).angle);angle=min(angle,360-angle)
 if angle>.001:axis_diff.append({'bone':name,'orientationDifferenceDegrees':angle})
report={'status':'passed','checks':checks,'count':len(checks),'restOrientationDifferencesMaleVsFemale':sorted(axis_diff,key=lambda x:x['orientationDifferenceDegrees'],reverse=True),'note':'Different body proportions mean rest locations and some bone rotations differ. Apply shared body actions as local rotations and preserve each seed rest; do not overwrite female rest matrices with male ones.'}
(R/'qa/seed-validation.json').write_text(json.dumps(report,indent=2,ensure_ascii=False));print('SEED QA PASSED',len(checks))
