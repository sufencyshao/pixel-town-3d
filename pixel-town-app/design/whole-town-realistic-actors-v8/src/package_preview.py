from pathlib import Path
import json,base64
R=Path(__file__).resolve().parent.parent
enc=lambda p:base64.b64encode(p.read_bytes()).decode()
index=json.loads((R/'reference/asset-index.json').read_text());motions=json.loads((R/'reference/animation-models.json').read_text());s=(R/'template.html').read_text()
for key,value in {'__META__':(R/'manifest.json').read_text(),'__ENV__':(R/'environment-data.json').read_text(),'__ASSET__':json.dumps(enc(R/'Town-complete.glb')),'__ACTORS__':(R/'actors.json').read_text(),'__MODELS__':json.dumps({k:enc(R/p) for k,p in index.items()}),'__MOTION_META__':json.dumps(motions,ensure_ascii=False),'__MOTIONS__':json.dumps({m['id']:enc(R/'animations'/(m['id']+'.glb')) for m in motions}),'__PENDING__':(R/'reference/pending-animals.json').read_text(),'__VIEWER__':(R/'viewer.bundle.js').read_text()}.items():s=s.replace(key,value)
(R/'现成人物与动物-完整小镇.html').write_text(s);print('HTML bytes',len(s.encode()))
