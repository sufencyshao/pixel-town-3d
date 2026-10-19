from pathlib import Path
import base64,json
p=Path(__file__).resolve().parent.parent
assets={k:base64.b64encode((p/k/(v+'-'+k+'.glb')).read_bytes()).decode() for k,v in [('clinic','B03'),('library','B02')]}
s=(p/'template.html').read_text().replace('__ASSETS__',json.dumps(assets)).replace('__VIEWER__',(p/'viewer.bundle.js').read_text())
(p/'诊所与图书馆-离线预览.html').write_text(s)
print('Standalone preview built')
