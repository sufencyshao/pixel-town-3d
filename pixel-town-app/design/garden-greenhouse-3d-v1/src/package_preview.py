from pathlib import Path
import base64,json
p=Path(__file__).resolve().parent.parent
s=(p/'template.html').read_text().replace('__ASSET__',json.dumps(base64.b64encode((p/'G-garden-greenhouse.glb').read_bytes()).decode())).replace('__VIEWER__',(p/'viewer.bundle.js').read_text())
(p/'田园与温室-离线预览.html').write_text(s)
print('Built standalone preview')
