"""Record unchanged mesh data and unrelated animation keys for a focused fix."""
import hashlib,json
def digest(value):
 return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def fingerprints(bpy):
 meshes={}
 for obj in bpy.context.scene.objects:
  if obj.type!='MESH':continue
  mesh=obj.data
  meshes[obj.name]=digest({'vertices':[list(v.co) for v in mesh.vertices],'polygons':[(list(p.vertices),p.material_index) for p in mesh.polygons],'weights':[[(g.group,g.weight) for g in v.groups] for v in mesh.vertices],'groups':[g.name for g in obj.vertex_groups],'morphs':{k.name:[list(p.co) for p in k.data] for k in mesh.shape_keys.key_blocks} if mesh.shape_keys else {},'materials':[m.name if m else None for m in mesh.materials]})
 actions={}
 for action in bpy.data.actions:
  if action.name=='Wave':continue
  curves=[]
  for layer in action.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for curve in bag.fcurves:curves.append([curve.data_path,curve.array_index,[(list(p.co),p.interpolation) for p in curve.keyframe_points]])
  actions[action.name]=digest(sorted(curves))
 return {'meshes':meshes,'other_actions':actions}
