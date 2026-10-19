from pathlib import Path
import json,base64
r=Path(__file__).resolve().parent.parent
m=json.loads((r/'assets/manifest.json').read_text())
refs={c['id']:'data:image/png;base64,'+base64.b64encode((r/'identity/reference'/(c['id']+'.png')).read_bytes()).decode() for c in m['characters']}
for c in m['characters']:
 p=r/c['glb'];(p.parent/'preview.js').write_text('window.RESIDENT_ASSETS['+json.dumps(c['id'])+']='+json.dumps(base64.b64encode(p.read_bytes()).decode())+';')
s=(r/'template.html').read_text()
for key,value in {'__META__':json.dumps(m,ensure_ascii=False),'__ASSETS__':'{}','__REFS__':json.dumps(refs),'__MOTION__':(r/'motion/actions.json').read_text(),'__VIEWER__':(r/'viewer.bundle.js').read_text()}.items():s=s.replace(key,value)
(r/'小镇人物-C方向-离线预览.html').write_text(s)
print('Preview residents',len(m['characters']),'HTML bytes',len(s.encode()))
