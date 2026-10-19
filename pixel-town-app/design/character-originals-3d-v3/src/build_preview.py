from pathlib import Path
import json,base64
R=Path(__file__).resolve().parent.parent
meta=json.loads((R/'manifest.json').read_text());am=json.loads((R/'animation-manifest.json').read_text())
assets={m['id']:base64.b64encode((R/m['glb']).read_bytes()).decode() for m in meta}
a={m['id']:base64.b64encode((R/'animations'/(m['id']+'.glb')).read_bytes()).decode() for m in am}
s=(R/'template.html').read_text().replace('__META__',json.dumps(meta,ensure_ascii=False)).replace('__ASSETS__',json.dumps(assets)).replace('__ANIM_META__',json.dumps(am,ensure_ascii=False)).replace('__ANIM_ASSETS__',json.dumps(a)).replace('__VIEWER__',(R/'viewer.bundle.js').read_text())
(R/'现成人物-离线预览.html').write_text(s)
print('Packaged',len(meta),'characters,',len(am),'source clips')
