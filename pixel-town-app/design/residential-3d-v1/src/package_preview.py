from pathlib import Path
import json,base64
p=Path(__file__).resolve().parent.parent
keys=['courtyard','hero','apartment-3','apartment-4','apartment-5']
m={k:json.loads((p/k/'manifest.json').read_text()) for k in keys}
a={k:base64.b64encode((p/k/(k+'.glb')).read_bytes()).decode() for k in keys}
s=(p/'template.html').read_text().replace('__META__',json.dumps(m,ensure_ascii=False)).replace('__ASSETS__',json.dumps(a)).replace('__VIEWER__',(p/'viewer.bundle.js').read_text())
(p/'住宅模型-离线预览.html').write_text(s);print('Built standalone preview')
