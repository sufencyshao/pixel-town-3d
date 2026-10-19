from pathlib import Path
import json,base64,shutil,hashlib
r=Path(__file__).resolve().parent.parent;library=r/'animal-library';source=r.parent/'animal-assets-3d-v1';source=source if source.exists() else library
assert len(json.loads((source/'assets/manifest.json').read_text())['animals'])==20, 'Require all 20 final animals'
# Do not copy temporary Blender backups or executable dependencies.
if source.resolve()!=library.resolve():shutil.copytree(source,library,dirs_exist_ok=True,ignore=shutil.ignore_patterns('*.blend1','__pycache__','node_modules'))
meta=json.loads((library/'assets/manifest.json').read_text());assets={a['id']:base64.b64encode((library/a['glb']).read_bytes()).decode() for a in meta['animals']}
s=(r/'template.html').read_text().replace('__ENV__',(r/'environment-data.json').read_text()).replace('__META__',(r/'manifest.json').read_text()).replace('__ASSET__',json.dumps(base64.b64encode((r/'Town-complete.glb').read_bytes()).decode())).replace('__ANIMAL_META__',json.dumps(meta,ensure_ascii=False)).replace('__ANIMAL_NAV__',(r/'reference/navigation.json').read_text()).replace('__ANIMAL_ASSETS__',json.dumps(assets)).replace('__CARETAKER__',json.dumps(base64.b64encode((r/'assets/people/Ache-caretaker.glb').read_bytes()).decode())).replace('__VIEWER__',(r/'viewer.bundle.js').read_text())
(r/'小镇动物生活-离线预览.html').write_text(s);print('Town animal preview bytes',len(s.encode()),'animals',len(assets))
