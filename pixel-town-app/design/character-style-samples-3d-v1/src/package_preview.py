from pathlib import Path
import json,base64
r=Path(__file__).resolve().parent.parent
assets={p.parent.name:base64.b64encode(p.read_bytes()).decode() for p in sorted((r/'assets').glob('*/*.glb'))}
s=(r/'template.html').read_text().replace('__REFERENCE__','data:image/png;base64,'+base64.b64encode((r/'reference/阿澈-2D原型.png').read_bytes()).decode()).replace('__ASSETS__',json.dumps(assets)).replace('__VIEWER__',(r/'viewer.bundle.js').read_text())
(r/'人物三种比例-离线预览.html').write_text(s);print('offline HTML bytes',len(s.encode()))
