import bpy,math,json,hashlib
from pathlib import Path
from mathutils import Vector,Quaternion
O=Path(__file__).resolve().parent;R=O.parents[1]
bpy.ops.wm.open_mainfile(filepath=str(O/'qa/actor-motion.blend'));scene=bpy.context.scene;rig=next(o for o in scene.objects if o.type=='ARMATURE')
def curves(action):
 for layer in action.layers:
  for strip in layer.strips:
   if hasattr(strip,'channelbags'):
    for bag in strip.channelbags:
     yield from bag.fcurves
def fingerprint(action):
 rows=[]
 for fc in curves(action):rows.append([fc.data_path,fc.array_index,[(list(p.co),list(p.handle_left),list(p.handle_right),p.interpolation) for p in fc.keyframe_points]])
 return hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()
def setframe(a,f):
 rig.animation_data.action=a;scene.frame_set(int(f),subframe=f-int(f));bpy.context.view_layer.update()
def pose():return {b.name:(b.location.copy(),b.rotation_quaternion.copy().normalized()) for b in rig.pose.bones}
def angle(a,b):
 v=math.degrees(a.rotation_difference(b).angle);return min(v,360-v)
def diff(a,b):return {'location':max((a[n][0]-b[n][0]).length for n in a),'rotationDeg':max(angle(a[n][1],b[n][1]) for n in a)}
orig=json.loads((O/'qa/original-action-fingerprints.json').read_text());checks=[]
checks.append({'check':'65 canonical bones','pass':len(rig.data.bones)==65})
checks.append({'check':'30 complete named actions','pass':len(bpy.data.actions)==30})
checks.append({'check':'22 preserved action fingerprints','pass':all(fingerprint(bpy.data.actions[n])==h for n,h in orig['fcurves'].items())})
with bpy.data.libraries.load(str(R/'character-natural-3d-v1/assets/01-Ache.blend'),link=False) as (src,dst):dst.actions=['Wave']
wave=dst.actions[0];checks.append({'check':'Wave exact C1.1 data','pass':fingerprint(wave)==fingerprint(bpy.data.actions['Wave'])});bpy.data.actions.remove(wave)
manifest=json.loads((O/'actions.json').read_text());loops={a['name'] for a in manifest['actions'] if a['playback']=='loop'}
body=[o for o in scene.objects if o.type=='MESH']
def floor_min():
 low=1e9;deps=bpy.context.evaluated_depsgraph_get()
 for ob in body:
  ev=ob.evaluated_get(deps);me=ev.to_mesh();mat=rig.matrix_world.inverted()@ev.matrix_world
  low=min(low,min((mat@v.co).z for v in me.vertices));ev.to_mesh_clear()
 return low
report={};keyposes={};normerr=0;newnormerr=0;nonfinite=[];hinges={};qsteps={};low=1e9
for a in bpy.data.actions:
 start,end=map(int,a.frame_range);prev=None;maxstep=0;root=[];mins=[];hinge=[]
 for frame in range(start,end+1):
  setframe(a,frame);p=pose()
  for b in rig.pose.bones:
   q=b.rotation_quaternion;normerr=max(normerr,abs(q.magnitude-1))
   if a.name in ['Eat','Drink','Read','Phone','Stretch','LieDown','LieRest','GetUp']:newnormerr=max(newnormerr,abs(q.magnitude-1))
   if not all(math.isfinite(x) for x in [*b.location,*q,*b.scale]):nonfinite.append([a.name,frame,b.name])
   if prev:maxstep=max(maxstep,angle(prev[b.name][1],p[b.name][1]))
  if a.name in ['Eat','Drink','Read','Phone','LieRest'] or (a.name=='Stretch' and 42<=frame<=108):
   for side in ['l','r']:
    q=rig.pose.bones['lowerarm_'+side].rotation_quaternion.normalized();ideal=Quaternion((q.w,q.x,0,0)).normalized();hinge.append(math.degrees(ideal.rotation_difference(q).angle))
  root.append(list(rig.pose.bones['root'].location));prev=p
  if a.name in ['LieDown','LieRest','GetUp']:
   floor=floor_min();mins.append(floor);low=min(low,floor)
 setframe(a,start);p0=pose();setframe(a,end);p1=pose();keyposes[a.name]=(p0,p1)
 report[a.name]={'frames':end-start+1,'maxAdjacentBoneRotationDeg':maxstep,'loopBoundary':diff(p0,p1),'rootLocalDrift':max((Vector(v)-Vector(root[0])).length for v in root),'floorMin':min(mins) if mins else None,'floorMax':max(mins) if mins else None,'hingeOffAxisDeg':max(hinge) if hinge else None}
 if hinge:hinges[a.name]=max(hinge)
 qsteps[a.name]=maxstep
checks.extend([{'check':'All sampled quaternion/location/scale finite','pass':not nonfinite},{'check':'New quaternion norm error below .001','pass':newnormerr<.001,'max':newnormerr,'preservedSourceMaximum':normerr,'runtimeRule':'normalize before retarget bake'},{'check':'New arms preserve single-axis elbow flexion (under 3 deg off-axis)','pass':max(hinges.values())<3,'byAction':hinges},{'check':'New lie floor no penetration beyond 0.2mm','pass':low>-.0002,'minimum':low}])
for a in ['Eat','Drink','Read','Phone','Stretch','LieDown','LieRest','GetUp']:
 checks.append({'check':a+' root in place','pass':report[a]['rootLocalDrift']<1e-6})
 checks.append({'check':a+' no abrupt joint jumps','pass':report[a]['maxAdjacentBoneRotationDeg']<12,'maxDegreesPerFrame':report[a]['maxAdjacentBoneRotationDeg']})
for a in ['Eat','Read','Phone','LieRest']:
 d=report[a]['loopBoundary'];checks.append({'check':a+' loop continuity','pass':d['location']<.0001 and d['rotationDeg']<.1,'difference':d})
for label,pa,pb in [('LieDown -> LieRest',keyposes['LieDown'][1],keyposes['LieRest'][0]),('LieRest -> GetUp',keyposes['LieRest'][0],keyposes['GetUp'][0]),('LieDown/GetUp identical standing pose',keyposes['LieDown'][0],keyposes['GetUp'][1])]:
 d=diff(pa,pb);checks.append({'check':label,'pass':d['location']<.0001 and d['rotationDeg']<.1,'difference':d})
# Lying must be horizontal with genuinely folded knees and a supporting hand.
setframe(bpy.data.actions['LieRest'],0);hip=rig.pose.bones['pelvis'].head;head=rig.pose.bones['Head'].head;hand=rig.pose.bones['hand_r'].head
axis=(head-hip).normalized();horizontal=abs(axis.z);knees={s:math.degrees(rig.pose.bones['calf_'+s].rotation_quaternion.angle) for s in ['l','r']}
# Hand length extends .12-.20m past its wrist under the lateral head.
support_tip=hand+rig.pose.bones['hand_r'].matrix.to_3x3()@Vector((0,.1,0));support_dist=(head-support_tip).length
checks.extend([{'check':'Lie torso horizontal','pass':horizontal<.20,'upDot':horizontal},{'check':'Lie both knees flexed','pass':all(40<v<135 for v in knees.values()),'degrees':knees},{'check':'Lower palm supports lateral head','pass':support_dist<.20,'headToPalmMetres':support_dist}])
# Re-run the C1.1 anatomical Wave tests on the actual shared library.
wave_rows=[];a=bpy.data.actions['Wave']
for f in range(73):
 setframe(a,f);u,l,h=[rig.pose.bones[n] for n in ['upperarm_l','lowerarm_l','hand_l']]
 d=u.matrix.to_3x3().inverted()@(l.tail-l.head).normalized();palm=(rig.matrix_world.to_3x3()@h.matrix.to_3x3()@Vector((1,0,0))).normalized()
 elbow_attach=u.bone.matrix_local.inverted()@l.bone.head_local;wrist_attach=l.bone.matrix_local.inverted()@h.bone.head_local
 wave_rows.append({'phase':f/72,'sideBendDeg':math.degrees(math.asin(max(-1,min(1,d.x)))),'flexionDeg':math.degrees(math.atan2(d.z,d.y)),'palmForward':palm.dot(Vector((0,-1,0))),'jointGap':max((u.matrix@elbow_attach-l.head).length,(l.matrix@wrist_attach-h.head).length),'wrist':list(rig.matrix_world@h.head)})
checks.extend([
 {'check':'Wave elbow flexion plane','pass':max(abs(r['sideBendDeg']) for r in wave_rows)<.1,'maxDegrees':max(abs(r['sideBendDeg']) for r in wave_rows)},
 {'check':'Wave elbow anatomical flexion','pass':all(45<r['flexionDeg']<115 for r in wave_rows),'range':[min(r['flexionDeg'] for r in wave_rows),max(r['flexionDeg'] for r in wave_rows)]},
 {'check':'Wave palm faces front','pass':min(r['palmForward'] for r in wave_rows)>.5,'minDot':min(r['palmForward'] for r in wave_rows)},
 {'check':'Wave connected shoulder/elbow/wrist','pass':max(r['jointGap'] for r in wave_rows)<.0001,'maxGap':max(r['jointGap'] for r in wave_rows)},
 {'check':'Wave continuous wrist motion','pass':max((Vector(x['wrist'])-Vector(y['wrist'])).length for x,y in zip(wave_rows,wave_rows[1:]))<.05},
 {'check':'Wave loop wrist boundary','pass':(Vector(wave_rows[0]['wrist'])-Vector(wave_rows[-1]['wrist'])).length<.002}
])
(O/'qa/wave-axes.json').write_text(json.dumps(wave_rows,indent=2))
# Ground/contact references before proportion retarget; no floor IK is claimed.
contacts={}
for a in bpy.data.actions:
 rows=[];start,end=a.frame_range
 for phase in [0,.5,1]:
  setframe(a,start+(end-start)*phase)
  names=['pelvis','Head','hand_l','hand_r','thigh_l','thigh_r','calf_l','calf_r','foot_l','foot_r','ball_l','ball_r']
  rows.append({'phase':phase,'meshGroundZ':floor_min(),'joints':{n:list(rig.pose.bones[n].head) for n in names}})
 contacts[a.name]=rows
(O/'contact-samples.json').write_text(json.dumps({'space':'canonical Blender armature-local metres; multiply by object scale0.896874785 for source world metres; +Z up, front-Y','meaning':'Reference joint heads and whole skinned-body minimum height at three phases. Seated/swim source offsets retained. Recipient ground/seat/water alignment must be fitted after proportion retarget.','actions':contacts},ensure_ascii=False,indent=2))
# Motion-only file must save/reopen with all names and canonical 65 bones.
bpy.ops.wm.open_mainfile(filepath=str(O/'shared-motion.blend'));rr=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
checks.extend([{'check':'Shared Blender reopen: only one rig object','pass':len(bpy.context.scene.objects)==1 and len(rr.data.bones)==65},{'check':'Shared Blender reopen: 30 retained Actions','pass':len(bpy.data.actions)==30}])
out={'schemaVersion':1,'passed':sum(c['pass'] for c in checks),'total':len(checks),'failed':[c for c in checks if not c['pass']],'checks':checks,'sampledFrameCount':sum(v['frames'] for v in report.values()),'actionMetrics':report,'nonfinite':nonfinite}
(O/'qa/validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print('MOTION_VALIDATION',out['passed'],out['total'],'FAILURES',out['failed'])
