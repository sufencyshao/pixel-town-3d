import bpy,json
from pathlib import Path
R=Path('/Users/summerwindy/Desktop/AI Chat/pixel-town-app/design/character-residents-3d-v2');bpy.ops.wm.open_mainfile(filepath=str(R/'assets/02_hero_female/character.blend'))
r=[]
for name in ['Top_dress','Dress_Skirt','Dress_Hem']:
 o=bpy.data.objects[name];r.append({'object':name,'uvLayers':[{'name':uv.name,'activeRender':uv.active_render,'bounds':[[min(v.uv[k] for v in uv.data) for k in range(2)],[max(v.uv[k] for v in uv.data) for k in range(2)]]} for uv in o.data.uv_layers],'materialImageCoordinateInputs':[{'material':m.name,'node':n.name,'vectorLinked':n.inputs['Vector'].is_linked} for m in o.data.materials for n in m.node_tree.nodes if n.type=='TEX_IMAGE']})
(R/'qa-identity/02_hero_female/uv-inspection.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
