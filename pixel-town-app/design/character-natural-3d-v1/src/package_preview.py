from pathlib import Path
import json,base64
r=Path(__file__).resolve().parent.parent
s=(r/'template.html').read_text().replace('__REFERENCE__','data:image/png;base64,'+base64.b64encode((r/'reference/阿澈-2D原型.png').read_bytes()).decode()).replace('__ASSET__',json.dumps(base64.b64encode((r/'assets/01-Ache.glb').read_bytes()).decode())).replace('__VIEWER__',(r/'viewer.bundle.js').read_text())
(r/'阿澈-C方向-离线预览.html').write_text(s);print('offline HTML bytes',len(s.encode()))
