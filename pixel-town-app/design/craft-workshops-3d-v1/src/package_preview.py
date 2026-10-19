from pathlib import Path
import base64,json
p=Path(__file__).resolve().parent.parent
s=(p/'template.html').read_text().replace('__ASSET__',json.dumps(base64.b64encode((p/'D-craft-workshops.glb').read_bytes()).decode())).replace('__VIEWER__',(p/'viewer.bundle.js').read_text())
(p/'手作工作区-离线预览.html').write_text(s)
print('Built standalone preview')
