"""Check the elbow's anatomical bend plane, not just finite animation values."""
import bpy,math,json,os
from pathlib import Path
from mathutils import Vector

root=Path(__file__).resolve().parent.parent
assets=Path(os.environ.get('WAVE_ASSET_DIR',str(root/'assets')))
checks=[];samples={}
def check(name,condition,info):
 checks.append({'name':name,'pass':bool(condition),'info':info})
 print('PASS' if condition else 'FAIL',name,info)

def inspect(label):
 rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
 for track in rig.animation_data.nla_tracks:track.mute=True
 action=bpy.data.actions['Wave'];rig.animation_data.action=action
 start,end=action.frame_range;rows=[]
 for i in range(73):
  t=start+(end-start)*i/72;bpy.context.scene.frame_set(int(t),subframe=t-int(t));bpy.context.view_layer.update()
  upper,lower,hand=[rig.pose.bones[n] for n in ['upperarm_l','lowerarm_l','hand_l']]
  d=upper.matrix.to_3x3().inverted()@(lower.tail-lower.head).normalized()
  palm=(rig.matrix_world.to_3x3()@hand.matrix.to_3x3()@Vector((1,0,0))).normalized()
  # glTF stores joints, not Blender edit-bone tails. On import Blender chooses
  # display-tail lengths; attachment checks must use the actual bind joints.
  elbow_attach=upper.bone.matrix_local.inverted()@lower.bone.head_local
  wrist_attach=lower.bone.matrix_local.inverted()@hand.bone.head_local
  rows.append({'phase':i/72,'side_bend_degrees':math.degrees(math.asin(max(-1,min(1,d.x)))),'flexion_degrees':math.degrees(math.atan2(d.z,d.y)),'palm_forward':palm.dot(Vector((0,-1,0))),'elbow_gap':(upper.matrix@elbow_attach-lower.head).length,'wrist_gap':(lower.matrix@wrist_attach-hand.head).length,'elbow':list(rig.matrix_world@lower.head),'wrist':list(rig.matrix_world@hand.head),'upper_rotation':list(upper.matrix.to_quaternion()),'forearm_rotation':list(lower.matrix.to_quaternion())})
 samples[label]=rows
 check(label+' elbow stays in flexion plane',max(abs(r['side_bend_degrees']) for r in rows)<15,{'max_side_bend_degrees':max(abs(r['side_bend_degrees']) for r in rows),'limit':15})
 check(label+' elbow flexes toward biceps',all(45<r['flexion_degrees']<115 for r in rows),{'range':[min(r['flexion_degrees'] for r in rows),max(r['flexion_degrees'] for r in rows)]})
 check(label+' palm faces forward',min(r['palm_forward'] for r in rows)>.5,{'minimum_forward_dot':min(r['palm_forward'] for r in rows)})
 check(label+' connected elbow and wrist',max(max(r['elbow_gap'],r['wrist_gap']) for r in rows)<.0001,{'max_gap':max(max(r['elbow_gap'],r['wrist_gap']) for r in rows)})
 check(label+' no frame jumps',max((Vector(a['wrist'])-Vector(b['wrist'])).length for a,b in zip(rows,rows[1:]))<.05,{'max_wrist_step':max((Vector(a['wrist'])-Vector(b['wrist'])).length for a,b in zip(rows,rows[1:]))})
 check(label+' smooth loop boundary',(Vector(rows[0]['wrist'])-Vector(rows[-1]['wrist'])).length<.002,{'wrist_loop_gap':(Vector(rows[0]['wrist'])-Vector(rows[-1]['wrist'])).length})

bpy.ops.wm.open_mainfile(filepath=str(assets/'01-Ache.blend'));inspect('native')
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(assets/'01-Ache.glb'));inspect('GLB')
error=max((Vector(a[joint])-Vector(b[joint])).length for a,b in zip(samples['native'],samples['GLB']) for joint in ['elbow','wrist'])
check('exported joints match native motion',error<.00001,{'max_world_position_error_m':error})
suffix=os.environ.get('WAVE_REPORT_SUFFIX','')
(root/('qa/wave-validation'+suffix+'.json')).write_text(json.dumps({'date':'2026-10-17','checks':checks,'samples':samples},ensure_ascii=False,indent=2))
if not all(c['pass'] for c in checks):raise AssertionError('wave elbow regression failed')
print('PASSED',len(checks),'checks across 146 sampled poses')
