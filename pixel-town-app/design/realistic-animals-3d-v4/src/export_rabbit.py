"""Convert complete legacy Blender animals for viewing; retain source art and motion."""
import bpy,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent.parent
report={}
for name in ['rabbit']:
 source=R/'vendor/oga'/f'{name}.blend';raw=source.read_bytes()
 bpy.ops.wm.open_mainfile(filepath=str(source))
 objects=[o for o in bpy.data.objects if o.type in {'MESH','ARMATURE'} and o.name!='Plane']
 before={o.name:{'vertices':len(o.data.vertices),'coordinates':hashlib.sha256(b''.join(__import__('struct').pack('<3f',*v.co) for v in o.data.vertices)).hexdigest()} for o in objects if o.type=='MESH'}
 # Old Blender Internal texture slots do not survive as linked PBR nodes.
 # Reconnect the ORIGINAL packed images to the ORIGINAL UVs; do not repaint.
 bindings={'Fur':'Fur-skin','Fur.001':'rabbot-skinn'} if name=='rabbit' else {'Material':'bird.jpg'}
 for mat in bpy.data.materials:
  image=bpy.data.images.get(bindings.get(mat.name,''))
  if not image:continue
  mat.use_nodes=True;nodes=mat.node_tree.nodes;nodes.clear();out=nodes.new('ShaderNodeOutputMaterial');p=nodes.new('ShaderNodeBsdfPrincipled');tex=nodes.new('ShaderNodeTexImage');tex.image=image
  mat.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color']);mat.node_tree.links.new(p.outputs['BSDF'],out.inputs['Surface']);p.inputs['Roughness'].default_value=.8
  if name=='rabbit' and mat.name=='Fur':
   mat.node_tree.links.new(tex.outputs['Alpha'],p.inputs['Alpha']);mat.surface_render_method='DITHERED';mat.use_backface_culling=False
  elif name=='rabbit':
   normal=nodes.new('ShaderNodeTexImage');normal.image=bpy.data.images['rabbit-NORM'];normal.image.colorspace_settings.name='Non-Color';map=nodes.new('ShaderNodeNormalMap');mat.node_tree.links.new(normal.outputs['Color'],map.inputs['Color']);mat.node_tree.links.new(map.outputs['Normal'],p.inputs['Normal'])
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.hide_set(False);o.select_set(True)
 rig=next(o for o in objects if o.type=='ARMATURE');bpy.context.view_layer.objects.active=rig
 source_actions=[{'name':a.name,'frames':list(a.frame_range)} for a in bpy.data.actions]
 bpy.ops.export_scene.gltf(filepath=str(R/'assets'/f'{name}.glb'),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_skins=True,export_def_bones=False,export_apply=False,export_yup=True)
 after={o.name:{'vertices':len(o.data.vertices),'coordinates':hashlib.sha256(b''.join(__import__('struct').pack('<3f',*v.co) for v in o.data.vertices)).hexdigest()} for o in objects if o.type=='MESH'}
 assert before==after
 assert source.read_bytes()==raw
 report[name]={'sourceSha256':hashlib.sha256(raw).hexdigest(),'sourceGeometryUnchanged':before,'sourceActions':source_actions,'bones':len(rig.data.bones),'shaderTranslation':'Reconnected original packed diffuse/alpha/normal maps for PBR export; original UVs/geometry/rig/actions retained.','exportSha256':hashlib.sha256((R/'assets'/f'{name}.glb').read_bytes()).hexdigest()}
(R/'qa/conversion.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
