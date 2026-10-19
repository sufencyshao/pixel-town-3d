from pathlib import Path
import json,base64
R=Path(__file__).resolve().parent.parent
meta=json.loads((R/'manifest.json').read_text())
assets={m['id']:base64.b64encode((R/m['glb']).read_bytes()).decode() for m in meta}
s=(R/'template.html').read_text().replace('__META__',json.dumps(meta,ensure_ascii=False)).replace('__ASSETS__',json.dumps(assets)).replace('__VIEWER__',(R/'viewer.bundle.js').read_text())
(R/'写实动物-原版预览.html').write_text(s)
print('Packaged',len(meta),'original models into offline HTML')
