"""Embed unchanged complete source GLBs alongside the existing town simulation."""
from pathlib import Path
import json, base64, hashlib, copy

R = Path(__file__).resolve().parent.parent
config = json.loads((R/'reference/asset-bindings.json').read_text())
identities = json.loads((R/'reference/original-animal-identities.json').read_text())['animals']
source_meta = json.loads((R.parent/'original-assets-3d-v2/manifest.json').read_text()) if (R.parent/'original-assets-3d-v2/manifest.json').exists() else json.loads((R/'reference/source-models.json').read_text())
(R/'reference/source-models.json').write_text(json.dumps(source_meta, ensure_ascii=False, indent=2))
models = {m['id']: m for m in source_meta}
dimensions = json.loads((R/'reference/model-dimensions.json').read_text())
animals, pending = [], []
assets = {}
for original in identities:
    p = copy.deepcopy(original)
    model_id = config['bindings'].get(p['id'])
    if not model_id:
        pending.append({'id':p['id'], 'name':p['name'], 'breed':p['breed'], 'species':p['species'], 'status':'待匹配原版成品'})
        continue
    m = models[model_id]
    raw = (R/'assets/models'/f'{model_id}.glb').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == m['portableSha256']
    assets[model_id] = base64.b64encode(raw).decode()
    p.update({'sourceModel':model_id, 'sourceLabel':m['label'], 'source':'Quaternius CC0 原版完整模型', 'sourceSha256':m['portableSha256'], 'actions':[a['name'] for a in m['animations']], 'glb':f'assets/models/{model_id}.glb', 'fitHeight':config.get('fitHeights',{}).get(p['id'],p['height'])})
    d = dimensions[model_id]
    scale = p['fitHeight']/(d['max'][1]-d['min'][1])
    center = [(a+b)/2 for a,b in zip(d['min'],d['max'])]
    p['displayScale'] = scale
    p['displayOffset'] = [-center[0]*scale,-d['min'][1]*scale,-center[2]*scale]
    p['height'] = p['fitHeight']
    p['length'] = (d['max'][2]-d['min'][2])*scale
    p['width'] = (d['max'][0]-d['min'][0])*scale
    p['radius'] = max(p['length'],p['width'])*.4
    p['headLocal'] = [x*scale+off for x,off in zip(d['head'],p['displayOffset'])]
    p['bodyLocal'] = [0,p['height']*.45,0]
    p['originalBreed'] = p['breed']
    if p['species']=='狗':
        p['breed'] = m['label']
        p['coat'] = '原版赤褐白' if model_id=='animal-shiba' else '原版灰白'
    p['appearance'] = p['breed']+' · Quaternius原版'
    if p['species']=='马':
        p['appearance'] = '作者Horse原版 · 原身份档案保留'
    animals.append(p)
human_dimensions = dimensions[config['caretaker']]
human_scale = 1.76/(human_dimensions['max'][1]-human_dimensions['min'][1])
meta = {'animals':animals, 'pending':pending, 'totalIdentities':len(identities), 'caretaker':{'sourceModel':config['caretaker'], 'displayScale':human_scale, 'displayOffset':[0,-human_dimensions['min'][1]*human_scale,0]}}
(R/'reference/runtime-animal-manifest.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2))
nav = json.loads((R/'reference/navigation-original.json').read_text())
selected = {p['id'] for p in animals}
nav['habitats'] = [h for h in nav['habitats'] if selected.intersection(h['petIds'])]
for h in nav['habitats']:
    h['petIds'] = [id for id in h['petIds'] if id in selected]
    if h.get('restSlots') and isinstance(h['restSlots'][0],dict):
        h['restSlots'] = [s for s in h['restSlots'] if s.get('petId') in selected]
(R/'reference/navigation.json').write_text(json.dumps(nav, ensure_ascii=False, separators=(',',':')))
human = (R/'assets/models'/f"{config['caretaker']}.glb").read_bytes()
assert hashlib.sha256(human).hexdigest() == models[config['caretaker']]['portableSha256']
s = (R/'template.html').read_text()
for key, value in {
    '__ENV__':(R/'environment-data.json').read_text(), '__META__':(R/'manifest.json').read_text(),
    '__ASSET__':json.dumps(base64.b64encode((R/'Town-complete.glb').read_bytes()).decode()),
    '__ANIMAL_META__':json.dumps(meta, ensure_ascii=False), '__ANIMAL_NAV__':json.dumps(nav, ensure_ascii=False),
    '__ANIMAL_ASSETS__':json.dumps(assets), '__CARETAKER__':json.dumps(base64.b64encode(human).decode()),
    '__VIEWER__':(R/'viewer.bundle.js').read_text(),
}.items():
    s = s.replace(key, value)
(R/'原版模型整镇-离线预览.html').write_text(s)
print('Embedded', len(animals), 'original animals using', len(assets), 'shared complete models;', len(pending), 'identities pending;', len(s.encode()), 'HTML bytes')
