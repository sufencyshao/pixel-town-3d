from pathlib import Path
import json, base64
R=Path(__file__).resolve().parent.parent
B=R.parent/'whole-town-realistic-actors-v8'
def js(value): return json.dumps(value,ensure_ascii=False).replace('</','<\\/')
def enc(p): return base64.b64encode(p.read_bytes()).decode()
index=json.loads((B/'reference/asset-index.json').read_text())
motions=json.loads((B/'reference/animation-models.json').read_text())
s=(B/'template.html').read_text().replace('现成人物与动物 V8','三维 AI 生活 V9')
s=s.replace('<meta charset="utf-8">','<meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src \'self\'; script-src \'self\' \'unsafe-inline\' \'wasm-unsafe-eval\'; style-src \'self\' \'unsafe-inline\'; img-src \'self\' data: blob:; connect-src blob:; object-src \'none\'; base-uri \'none\'">')
s=s.replace('<aside>','<aside>'+(R/'panel.html').read_text(),1)
s=s.replace('</style>',(R/'panel.css').read_text()+'</style>',1)
s=s.replace('本版尚未接自主寻路','AI 已接公共步道导航')
s=s.replace('<script>window.TOWN_META=', '<script>window.TOWN_CAPABILITIES='+ (R/'capabilities.json').read_text()+';window.TOWN_NAVIGATION='+(B/'reference/navigation.json').read_text()+';window.TOWN_PUBLIC_CATALOG='+js(json.loads((R/'catalog-public.json').read_text()))+';</script><script>window.TOWN_META=')
values={'__META__':(B/'manifest.json').read_text(),'__ENV__':(B/'environment-data.json').read_text(),'__ASSET__':js(enc(B/'Town-complete.glb')),'__ACTORS__':(B/'actors.json').read_text(),'__MODELS__':js({k:enc(B/p) for k,p in index.items()}),'__MOTION_META__':js(motions),'__MOTIONS__':js({m['id']:enc(B/'animations'/(m['id']+'.glb')) for m in motions}),'__PENDING__':(B/'reference/pending-animals.json').read_text(),'__VIEWER__':(R/'viewer.bundle.js').read_text()}
for key,value in values.items():s=s.replace(key,value)
target=R/'三维小镇-AI生活.html'
temporary=target.with_suffix('.html.tmp');temporary.write_text(s);temporary.replace(target)
print('V9 HTML bytes',len(s.encode()))
