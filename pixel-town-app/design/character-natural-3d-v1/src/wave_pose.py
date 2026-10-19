"""Bake a wave with a coherent shoulder roll and an elbow flexion hinge."""
import math
from mathutils import Vector,Quaternion,Matrix

def bake_wave(bpy,rig,scene):
 old=bpy.data.actions['Wave'];base=old.copy();base.name='_WaveReference'
 rig.animation_data.action=base;bpy.data.actions.remove(old)
 action=bpy.data.actions.new('Wave');action.use_fake_user=True
 start,end=base.frame_range
 for frame in range(73):
  rig.animation_data.action=base;t=start+(end-start)*frame/72
  scene.frame_set(int(t),subframe=t-int(t));bpy.context.view_layer.update()
  phase=frame/72
  upper=rig.pose.bones['upperarm_l'];rest_direction=(upper.bone.tail_local-upper.bone.head_local).normalized()
  arm_direction=Vector((.94,-.16,.30)).normalized()
  swing=rest_direction.rotation_difference(arm_direction)
  # The old clip aimed each bone independently. That retained the arm's T-pose
  # roll while bending the elbow sideways. Rotate the biceps toward the bend.
  roll=Quaternion(rest_direction,math.radians(-90))
  rotation=swing@roll@upper.bone.matrix_local.to_quaternion()
  upper.matrix=Matrix.LocRotScale(upper.head.copy(),rotation,Vector((1,1,1)))
  bpy.context.view_layer.update()
  lower=rig.pose.bones['lowerarm_l'];lower.rotation_mode='QUATERNION'
  lower.rotation_quaternion=Quaternion((1,0,0),math.radians(74+3*math.sin(phase*math.tau*2)))
  hand=rig.pose.bones['hand_l'];hand.rotation_mode='QUATERNION'
  hand.rotation_quaternion=Quaternion((1,0,0),math.radians(12)*math.sin(phase*math.tau*2))
  for finger in rig.pose.bones:
   if finger.name.endswith('_l') and finger.name.startswith(('index_','middle_','pinky_','ring_','thumb_')):
    finger.rotation_mode='QUATERNION';finger.rotation_quaternion=Quaternion()
  bpy.context.view_layer.update();rig.animation_data.action=action
  for bone in rig.pose.bones:
   bone.keyframe_insert('rotation_quaternion',frame=frame);bone.keyframe_insert('location',frame=frame)
 rig.animation_data.action=action;bpy.data.actions.remove(base)
 return action
