from pathlib import Path
import base64,json
r=Path(__file__).resolve().parents[1]
s=(r/'template.html').read_text().replace('__META__',(r/'manifest.json').read_text()).replace('__ASSET__',json.dumps(base64.b64encode((r/'I-arrival-guard.glb').read_bytes()).decode())).replace('__VIEWER__',(r/'viewer.bundle.js').read_text())
(r/'到达与守护-离线预览.html').write_text(s)
print('Built standalone preview')
