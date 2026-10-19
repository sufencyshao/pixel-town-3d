from pathlib import Path
import json,base64,shutil
R=Path(__file__).resolve().parent.parent;T=R/'town';enc=lambda p:json.dumps(base64.b64encode(p.read_bytes()).decode())
shutil.copy2(R/'src/resident-world.js',T/'src/resident-world.js')
meta=json.loads((T/'animal-library/assets/manifest.json').read_text());assets={c['id']:base64.b64encode((T/'animal-library'/c['glb']).read_bytes()).decode() for c in meta['animals']}
s=(T/'template.html').read_text()
for k,v in {'__META__':(T/'manifest.json').read_text(),'__ENV__':(T/'environment-data.json').read_text(),'__ASSET__':enc(T/'Town-complete.glb'),'__ANIMAL_META__':json.dumps(meta,ensure_ascii=False),'__ANIMAL_NAV__':(T/'reference/navigation.json').read_text(),'__ANIMAL_ASSETS__':json.dumps(assets),'__CARETAKER__':enc(R/'assets/01_hero_male/character.glb'),'__RESIDENT_META__':(R/'assets/manifest.json').read_text(),'__PLACEMENTS__':(T/'resident-placements.json').read_text(),'__VIEWER__':(T/'viewer.bundle.js').read_text()}.items():s=s.replace(k,v)
(T/'小镇人物与动物-离线预览.html').write_text(s)
print('Packaged town bytes',len(s.encode()))
