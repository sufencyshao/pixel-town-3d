import bpy
from pathlib import Path
r=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(r/'AC-residential-districts.blend'))
s=bpy.data.scenes['04 C plan'];s.camera.data.ortho_scale=90
bpy.ops.wm.save_as_mainfile(filepath=str(r/'AC-residential-districts.blend'))
s.render.filepath=str(r/'C-plan.png');bpy.ops.render.render(write_still=True,scene=s.name)
