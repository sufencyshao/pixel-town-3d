from pathlib import Path
import base64,json
p=Path(__file__).resolve().parent.parent
s=(p/'template.html').read_text().replace('__ASSET__',json.dumps(base64.b64encode((p/'E-town-square.glb').read_bytes()).decode())).replace('__VIEWER__',(p/'viewer.bundle.js').read_text())
(p/'小镇客厅-离线预览.html').write_text(s)
print('Built standalone preview')
