from pathlib import Path
import base64,json
p=Path(__file__).resolve().parent.parent
s=(p/'template.html').read_text().replace('__META__',json.dumps(json.loads((p/'manifest.json').read_text()),ensure_ascii=False)).replace('__ASSET__',json.dumps(base64.b64encode((p/'AC-residential-districts.glb').read_bytes()).decode())).replace('__VIEWER__',(p/'viewer.bundle.js').read_text())
(p/'住宅区-离线预览.html').write_text(s)
print('Built standalone district preview')
