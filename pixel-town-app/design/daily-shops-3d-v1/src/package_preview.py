from pathlib import Path
import base64,json
p=Path(__file__).resolve().parent.parent
s=(p/'template.html').read_text().replace('__ASSET__',json.dumps(base64.b64encode((p/'H-daily-shops.glb').read_bytes()).decode())).replace('__VIEWER__',(p/'viewer.bundle.js').read_text())
(p/'日常商业街-离线预览.html').write_text(s)
print('Built standalone preview')
