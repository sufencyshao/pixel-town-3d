"""Resident C-natural motion library. Rebuild only this motion directory.
Existing 22 reviewed clips remain byte-for-byte equivalent at their F-curves.
Additional daily actions are original joint animation, not renamed status clips.
"""
import bpy,math,json,hashlib
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
R=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
SOURCE=R/'whole-town-animals-3d-v6/assets/people/Ache-caretaker.blend'
C1=R/'character-natural-3d-v1/assets/01-Ache.blend'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene=bpy.context.scene;scene.render.fps=30
rig=next(o for o in scene.objects if o.type=='ARMATURE');rig.name='ResidentMotionRig'
for tr in rig.animation_data.nla_tracks:tr.mute=True
BASE={a.name:a for a in bpy.data.actions}
BODY=[o for o in scene.objects if o.type=='MESH']

def curves(action):
 for layer in action.layers:
  for strip in layer.strips:
   if hasattr(strip,'channelbags'):
    for bag in strip.channelbags:
     for fc in bag.fcurves:yield fc

def fingerprint(action):
 rows=[]
 for fc in curves(action):
  rows.append([fc.data_path,fc.array_index,[(list(p.co),list(p.handle_left),list(p.handle_right),p.interpolation) for p in fc.keyframe_points]])
 return hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()
ORIGINAL_HASH={a:fingerprint(v) for a,v in BASE.items()}

def reset():
 rig.animation_data.action=None
 for b in rig.pose.bones:
  b.rotation_mode='QUATERNION';b.location=(0,0,0);b.rotation_quaternion=Quaternion();b.scale=(1,1,1)
 bpy.context.view_layer.update()

def snapshot(action,frame=0):
 rig.animation_data.action=BASE[action]
 scene.frame_set(int(frame),subframe=frame-int(frame));bpy.context.view_layer.update()
 return {b.name:(b.location.copy(),b.rotation_quaternion.copy().normalized(),b.scale.copy()) for b in rig.pose.bones}

def put(pose):
 rig.animation_data.action=None
 for b in rig.pose.bones:
  b.rotation_mode='QUATERNION';b.location,b.rotation_quaternion,b.scale=pose[b.name]
 bpy.context.view_layer.update()

def grab():return {b.name:(b.location.copy(),b.rotation_quaternion.copy().normalized(),b.scale.copy()) for b in rig.pose.bones}
def lerp_pose(a,b,t):
 t=max(0,min(1,t));return {n:(a[n][0].lerp(b[n][0],t),a[n][1].slerp(b[n][1],t).normalized(),a[n][2].lerp(b[n][2],t)) for n in a}
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
def qaxis(axis,degrees):return Quaternion(axis,math.radians(degrees))
def joint(name,axis,degrees):
 b=rig.pose.bones[name];b.rotation_quaternion=b.rotation_quaternion@qaxis(axis,degrees)
def orientation(y,z):
 y=Vector(y).normalized();z=Vector(z);z=(z-y*z.dot(y)).normalized();x=y.cross(z).normalized();z=x.cross(y).normalized()
 return Matrix(((x.x,y.x,z.x),(x.y,y.y,z.y),(x.z,y.z,z.z))).to_quaternion().normalized()
def set_world_rotation(name,quat):
 b=rig.pose.bones[name];b.matrix=Matrix.LocRotScale(b.head.copy(),quat,Vector((1,1,1)));bpy.context.view_layer.update()
def move_pelvis(point,quat=None):
 b=rig.pose.bones['pelvis'];b.matrix=Matrix.LocRotScale(Vector(point),quat or b.matrix.to_quaternion(),Vector((1,1,1)));bpy.context.view_layer.update()
def solve_limb(upper,lower,end,target,pole):
 """Two links, one anatomical flexion plane. Child X is the hinge axis.
 Shoulder twist is solved together with elbow plane, never independent aim-only.
 """
 u=rig.pose.bones[upper];l=rig.pose.bones[lower];e=rig.pose.bones[end]
 s=u.head.copy();target=Vector(target);delta=target-s;distance=delta.length
 l1=(l.head-s).length;l2=(e.head-l.head).length
 distance=max(abs(l1-l2)+.006,min(l1+l2-.001,distance));d=delta.normalized();target=s+d*distance
 pole=Vector(pole);p=(pole-d*pole.dot(d)).normalized()
 a=(l1*l1-l2*l2+distance*distance)/(2*distance);height=math.sqrt(max(0,l1*l1-a*a));elbow=s+d*a+p*height
 uy=(elbow-s).normalized();ly=(target-elbow).normalized();x=uy.cross(ly).normalized()
 uq=Matrix(((x.x,uy.x,x.cross(uy).x),(x.y,uy.y,x.cross(uy).y),(x.z,uy.z,x.cross(uy).z))).to_quaternion()
 u.matrix=Matrix.LocRotScale(s,uq,Vector((1,1,1)));bpy.context.view_layer.update()
 z=x.cross(ly);lq=Matrix(((x.x,ly.x,z.x),(x.y,ly.y,z.y),(x.z,ly.z,z.z))).to_quaternion()
 l.matrix=Matrix.LocRotScale(l.head.copy(),lq,Vector((1,1,1)));bpy.context.view_layer.update()
def arm(side,target,pole,hand_y=None,palm_z=None):
 solve_limb('upperarm_'+side,'lowerarm_'+side,'hand_'+side,target,pole)
 if hand_y is not None:
  # This UAL hand uses +Y along fingers and +X as palm normal.
  # +Z is the across-palm axis, unlike the torso axes.
  z=Vector(palm_z).cross(Vector(hand_y)).normalized()
  set_world_rotation('hand_'+side,orientation(hand_y,z))
def leg(side,target,pole,foot_quat=None):
 solve_limb('thigh_'+side,'calf_'+side,'foot_'+side,target,pole)
 if foot_quat:set_world_rotation('foot_'+side,foot_quat)
def grip(side,amount=.32,thumb=.12):
 for b in rig.pose.bones:
  if not b.name.endswith('_'+side):continue
  if b.name.startswith(('index_','middle_','ring_','pinky_')) and '_leaf_' not in b.name:
   b.rotation_quaternion=qaxis((1,0,0),amount*math.degrees(1))
  elif b.name.startswith('thumb_') and '_leaf_' not in b.name:b.rotation_quaternion=qaxis((0,0,1),thumb*math.degrees(1))
def mesh_min_z():
 deps=bpy.context.evaluated_depsgraph_get();low=1e10
 for o in BODY:
  ev=o.evaluated_get(deps);me=ev.to_mesh()
  for v in me.vertices:low=min(low,(rig.matrix_world.inverted()@ev.matrix_world@v.co).z)
  ev.to_mesh_clear()
 return low

def fit_floor(level=0):
 low=mesh_min_z();b=rig.pose.bones['pelvis'];b.matrix.translation.z+=level-low;bpy.context.view_layer.update()
IDLE=snapshot('Idle',0);CROUCH=snapshot('Crouch',25)
# Mild original breathing retained under the hand actions.
def idle_at(phase):return snapshot('Idle',(phase % 1.0)*60)

STRETCH_HIGH=None
def daily(name,p):
 global STRETCH_HIGH
 put(idle_at(p));wave=math.sin(p*math.tau)
 for side in ['l','r']:
  b=rig.pose.bones['lowerarm_'+side];q=b.rotation_quaternion;b.rotation_quaternion=Quaternion((q.w,q.x,0,0)).normalized()
 bpy.context.view_layer.update()
 if name=='Eat':
  # Bowl steady in left hand. Right spoon travels to the mouth, holds, returns.
  lift=smooth(min(p/.30,(.85-p)/.26)) if p<.85 else 0
  if .30<p<.59:lift=1
  lift=max(0,min(1,lift));arm('l',(.17,-.30,1.15),(.45,-.2,-1),(-1,0,0),(0,0,1));grip('l',.15)
  pos=Vector((-.04,-.34,1.20)).lerp(Vector((-.025,-.285,1.548)),lift)
  arm('r',pos,(-.75,-.3,-1),(0,.93,.36),(0,-.36,.93));grip('r',.27,.21)
  joint('Head',(1,0,0),8*(1-lift)+2*lift);joint('neck_01',(0,1,0),wave*.8)
 elif name=='Drink':
  sip=smooth(min(p/.30,(.91-p)/.28)) if p<.91 else 0
  if .30<p<.63:sip=1
  sip=max(0,min(1,sip));theta=math.radians(28*sip)
  pos=Vector((-.16,-.29,1.23)).lerp(Vector((-.035,-.236,1.493)),sip)
  arm('r',pos,(-.8,-.2,-1),(0,math.sin(theta),math.cos(theta)),(0,-math.cos(theta),math.sin(theta)));grip('r',.45,.20)
  joint('Head',(1,0,0),-3*sip)
 elif name=='Read':
  arm('l',(.16,-.34,1.23),(.8,-.1,-1),(-1,.02,.02),(0,.50,.866));grip('l',.15)
  arm('r',(-.15,-.36,1.22),(-.8,-.1,-1),(1,0,.05),(0,.50,.866));grip('r',.15)
  joint('Head',(1,0,0),22);joint('Head',(0,1,0),2.2*wave)
  joint('neck_01',(0,1,0),.7*wave)
 elif name=='Phone':
  arm('l',(.11,-.35,1.32),(.7,-.2,-1),(0,.14,1),(0,-1,.14));grip('l',.26)
  # Repeated small screen taps; this is a hand/arm clip, not a renamed Talk.
  tap=.5+.5*math.sin(p*math.tau*3)
  arm('r',(-.035,-.36-.016*tap,1.415+.018*tap),(-.8,-.15,-1),(1,.1,.1),(0,-1,.1));grip('r',.46)
  for b in ['index_01_r','index_02_r','index_03_r']:rig.pose.bones[b].rotation_quaternion=Quaternion()
  joint('Head',(1,0,0),19);joint('neck_01',(0,1,0),wave*.6)
 elif name=='Stretch':
  high=smooth(min(p/.27,(1-p)/.27))
  if STRETCH_HIGH is None:
   put(IDLE)
   for side,sgn in [('l',1),('r',-1)]:
    arm(side,(sgn*.09,.015,1.912),(sgn,0,.2),(sgn*.12,0,1),(0,-1,0));grip(side,.06)
   STRETCH_HIGH=grab()
  put(lerp_pose(IDLE,STRETCH_HIGH,high));joint('spine_02',(0,0,1),1.6*math.sin(p*math.tau)*high);joint('Head',(1,0,0),-4*high)
 bpy.context.view_layer.update();return grab()

# Side lying has three independently authored body poses; the final is curled,
# with the lower forearm underneath the head and the upper hand at the abdomen.
reset();REST_PELVIS_Q=rig.pose.bones['pelvis'].bone.matrix_local.to_quaternion();SIDE_Q=qaxis((0,1,0),-90)
FOOT_REST={s:rig.pose.bones['foot_'+s].bone.matrix_local.to_quaternion() for s in ['l','r']}
def make_floor_seated():
 reset();move_pelvis((0,.03,.34));joint('spine_01',(1,0,0),8);bpy.context.view_layer.update()
 leg('r',(-.14,-.16,.09),(0,-1,0),FOOT_REST['r']);leg('l',(.38,-.15,.10),(0,-1,0),FOOT_REST['l'])
 arm('r',(-.40,.02,.12),(-.7,0,-.3),(0,-1,0),(0,0,-1));arm('l',(.18,-.24,.72),(.5,-.3,-1),(0,-.4,-1),(0,-1,.4));grip('l',.08);grip('r',.03)
 fit_floor(0);return grab()
def make_side():
 reset();move_pelvis((0,.025,.285),SIDE_Q@REST_PELVIS_Q)
 joint('spine_01',(1,0,0),5);joint('spine_02',(1,0,0),4);joint('Head',(1,0,0),-2);bpy.context.view_layer.update()
 leg('r',(.73,-.09,.155),(0,-1,0),SIDE_Q@FOOT_REST['r']);leg('l',(.64,-.18,.375),(0,-1,0),SIDE_Q@FOOT_REST['l'])
 arm('r',(-.665,-.02,.205),(0,-1,.05),(-1,0,0),(0,0,1));arm('l',(-.245,-.225,.365),(.1,-1,.15),(1,-.15,-.08),(0,-.6,.8));grip('r',.03);grip('l',.09)
 fit_floor(0);return grab()
SEATED=make_floor_seated();SIDE=make_side()
# Crouch is only a transition waypoint; no source action is changed.
# Keep root translation/rotation zero in all newly authored actions.
for pose in [SEATED,SIDE]:pose['root']=(Vector((0,0,0)),Quaternion(),Vector((1,1,1)))
def lying(phase):
 put(SIDE);breath=math.sin(phase*math.tau)
 joint('spine_02',(1,0,0),.40*breath);joint('Head',(1,0,0),.18*breath);joint('hand_l',(1,0,0),.45*breath)
 bpy.context.view_layer.update();fit_floor(0);return grab()
def transition(p):
 knots=[(0,IDLE),(.25,CROUCH),(.53,SEATED),(.88,SIDE),(1,SIDE)]
 for (a,pa),(b,pb) in zip(knots,knots[1:]):
  if a<=p<=b:
   put(lerp_pose(pa,pb,smooth((p-a)/(b-a))));fit_floor(0);return grab()
 return SIDE

CUSTOM={'Eat':120,'Drink':114,'Read':120,'Phone':120,'Stretch':150,'LieDown':150,'LieRest':120,'GetUp':150}
for name,frames in CUSTOM.items():
 action=bpy.data.actions.new(name);action.use_fake_user=True;previous_quats={}
 for frame in range(frames+1):
  p=frame/frames
  if name=='LieRest':pose=lying(p)
  elif name=='LieDown':pose=transition(p)
  elif name=='GetUp':pose=transition(1-p)
  else:pose=daily(name,p)
  pose['root']=(Vector((0,0,0)),Quaternion(),Vector((1,1,1)))
  put(pose);rig.animation_data.action=action
  for b in rig.pose.bones:
   b.rotation_quaternion.normalize()
   if b.name in previous_quats and b.rotation_quaternion.dot(previous_quats[b.name])<0:b.rotation_quaternion.negate()
   previous_quats[b.name]=b.rotation_quaternion.copy();b.keyframe_insert('rotation_quaternion',frame=frame);b.keyframe_insert('location',frame=frame)
  rig.animation_data.action=None
 for fc in curves(action):
  for key in fc.keyframe_points:key.interpolation='LINEAR'
 print('AUTHORED',name,frames)

# Store a clean armature/action asset and a separate fully skinned QA scene.
rig.animation_data.action=BASE['Idle'];scene.frame_set(0);bpy.context.view_layer.update()
for a in bpy.data.actions:a.use_fake_user=True
(OUT/'qa/original-action-fingerprints.json').write_text(json.dumps({'source':str(SOURCE),'sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'fcurves':ORIGINAL_HASH},indent=2))
rest={'schemaVersion':1,'rig':'ResidentMotionRig','fps':30,'units':'metres','space':'Blender armature local X right, -Y forward, Z up','objectMatrix':[list(row) for row in rig.matrix_world],'objectScale':list(rig.scale),'retarget':'Normalize sampled quaternions before retarget baking. Source untouched curves have at most 0.00157 raw interpolation norm error. Copy basis quaternions by canonical names; bone rest matrices/orientations are canonical. Pelvis location values are pose local, not global Z; proportion-scale translations consistently. Object transform must be retained or baked once. Do not apply extra scale twice.','bones':[{ 'name':b.name,'parent':b.parent.name if b.parent else None,'head':list(b.head_local),'tail':list(b.tail_local),'matrixLocal':[list(row) for row in b.matrix_local],'length':b.length} for b in rig.data.bones]}
(OUT/'bone-rest.json').write_text(json.dumps(rest,ensure_ascii=False,indent=2))
LABELS={'Idle':'站立呼吸','Walk':'走路','Wave':'挥手（V1.1肘轴）','Talk':'交流','Run':'慢跑','Crouch':'蹲下休息','CrouchWalk':'蹲行','SitDown':'坐下','Sit':'坐着','StandUp':'站起','PickUp':'拾取桌面物品','Work':'跪姿作业','Dance':'舞蹈','Swim':'向前游泳','JumpStart':'起跳','JumpLoop':'空中姿态','JumpLand':'落地','Nod':'点头','ShakeHead':'摇头','Pet':'跪姿轻抚','Feed':'跪姿喂食','ThrowBall':'投球','Eat':'吃饭','Drink':'喝水','Read':'阅读','Phone':'看手机','Stretch':'伸展','LieDown':'侧躺入睡','LieRest':'侧躺呼吸','GetUp':'侧躺起身'}
SOURCES={'Talk':'Idle_Talking_Loop','Run':'Jog_Fwd_Loop','Crouch':'Crouch_Idle_Loop','CrouchWalk':'Crouch_Fwd_Loop','SitDown':'Sitting_Enter','Sit':'Sitting_Idle_Loop','StandUp':'Sitting_Exit','PickUp':'PickUp_Table','Work':'Fixing_Kneeling','Dance':'Dance_Loop','Swim':'Swim_Fwd_Loop','JumpStart':'Jump_Start','JumpLoop':'Jump_Loop','JumpLand':'Jump_Land','Idle':'Idle_Loop','Walk':'Walk_Loop','Nod':'Idle_Loop + original head nod','ShakeHead':'Idle_Loop + original head shake'}
LOOPS={'Idle','Walk','Wave','Talk','Run','Crouch','CrouchWalk','Sit','Work','Dance','Swim','JumpLoop','Pet','Feed','Eat','Read','Phone','LieRest'}
SINGLE={'SitDown','StandUp','PickUp','JumpStart','JumpLand','Nod','ShakeHead','ThrowBall','Drink','Stretch','LieDown','GetUp'}
SOCKETS={
 'Eat':[{'prop':'bowl','bone':'hand_l','position':[.035,.105,0],'rotationQuaternionWXYZ':list(qaxis((0,1,0),90)),'size':[.22,.22,.08],'axes':'XY rim, +Z opening'}, {'prop':'spoon','bone':'hand_r','position':[0,.075,0],'rotationQuaternionWXYZ':list(qaxis((0,1,0),90)),'size':[.025,.16,.012],'axes':'+Y handle-to-tip'}],
 'Drink':[{'prop':'cup','bone':'hand_r','position':[0,.105,-.005],'rotationQuaternionWXYZ':list(qaxis((1,0,0),-90)),'size':[.075,.075,.105],'axes':'prop +Z opening; cup becomes upright at lowered hand'}],
 'Read':[{'prop':'open-book','bone':'hand_l','position':[.018,.145,0],'rotationQuaternionWXYZ':list(qaxis((0,1,0),90)),'size':[.21,.255,.028],'axes':'XY pages, +Z page face, spine along local X'}],
 'Phone':[{'prop':'phone','bone':'hand_l','position':[-.032,.15,0],'rotationQuaternionWXYZ':list(qaxis((0,1,0),90)),'size':[.075,.145,.012],'axes':'XY screen plane, -Z screen faces head'}]
}
entries=[]
for a in bpy.data.actions:
 name=a.name;start,end=a.frame_range
 source='Original authored daily motion, 2026-10-18' if name in CUSTOM else ('C1.1 exact corrected shoulder roll + elbow X hinge' if name=='Wave' else ('V6 original caretaker animation' if name in ['Pet','Feed','ThrowBall'] else 'Quaternius UAL1 / '+SOURCES.get(name,name)))
 entries.append({'name':name,'label':LABELS[name],'frameStart':int(start),'frameEnd':int(end),'fps':30,'duration':round((end-start)/30,6),'playback':'loop' if name in LOOPS else 'one-shot','source':source,'sourceFile':str(SOURCE.relative_to(R)) if name not in CUSTOM else 'motion/build_motion.py','preservedFcurveSHA256':ORIGINAL_HASH.get(name),'propSockets':SOCKETS.get(name,[]),'support':('side floor, lower forearm under head, both knees flexed' if name in ['LieDown','LieRest','GetUp'] else 'seat (runtime seat height)' if name in ['Sit','SitDown','StandUp'] else 'water plane' if name=='Swim' else 'ground'),'recommendedBlendSeconds':.25 if name not in ['LieDown','GetUp'] else .12})
manifest={'schemaVersion':1,'asset':'shared-motion.blend','rig':'ResidentMotionRig','boneCount':65,'fps':30,'coordinateSystem':'Blender +Z up, forward -Y; glTF export +Y up / +Z forward is exporter conversion, do not reinterpret bone-local offsets.','handBoneAxes':'UAL1 hand +Y along fingers, +X palm normal, +Z across palm. Prop socket quaternions align conventional prop +Z to palm +X where required.',
 'socketUnits':'bone-local canonical metres, inherit recipient hand scale. rotationQuaternionWXYZ uses Blender ordering.','groundFit':'Custom floor transitions were fitted against skinned reference actor each sampled frame. Recipient body/clothes/foot ground fitting remains required. Existing22 clips preserved including source vertical offsets.','lyingChain':{'enter':'LieDown','rest':'LieRest','exit':'GetUp','startEndPose':'LieDown end and GetUp start exactly match LieRest phase0; GetUp end matches grounded Idle phase0.','headSupport':'Lower right hand palm under right side of head; optional low pillow supports head and forearm; do not remove arm fold.','referencePillow':{'center':[-.75,.02,.13],'size':[.31,.22,.14],'space':'armature local; optional artistic comfort, head already arm-supported'}},'actions':entries}
(OUT/'actions.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
bpy.ops.file.pack_all();scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'qa/actor-motion.blend'),compress=True)
# Remove meshes/cameras only after preserving the QA source.
for o in list(scene.objects):
 if o!=rig:bpy.data.objects.remove(o,do_unlink=True)
rig.animation_data.action=bpy.data.actions['Idle'];scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'shared-motion.blend'),compress=True)
print('MOTION_LIBRARY_READY',len(bpy.data.actions),'actions',len(rig.data.bones),'bones')
