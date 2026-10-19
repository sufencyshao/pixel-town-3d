from pathlib import Path
import json,base64
r=Path(__file__).resolve().parent.parent
s=(r/'template.html').read_text().replace('__META__',(r/'manifest.json').read_text()).replace('__ASSET__',json.dumps(base64.b64encode((r/'Town-complete.glb').read_bytes()).decode())).replace('__VIEWER__',(r/'viewer.bundle.js').read_text())
(r/'完整小镇-离线预览.html').write_text(s);print('Standalone town HTML ready',len(s))
