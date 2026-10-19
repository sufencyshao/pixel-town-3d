from pathlib import Path
import json,hashlib,base64,zipfile,re,time,os
R=Path(__file__).resolve().parent.parent;sha=lambda b:hashlib.sha256(b).hexdigest()
meta=json.loads((R/'assets/manifest.json').read_text())['characters'];assert len(meta)==45 and len({c['id'] for c in meta})==45
glb=json.loads((R/'motion/qa/resident-batch-glb.json').read_text());assert glb['countPass'] and not glb['errors'] and not glb['failedIdentities'] and glb['passed']==glb['total']
for name in ['browser-validation','town-browser-validation','native-validation']:
 d=json.loads((R/'qa'/(name+'.json')).read_text());assert d['passed']==d['total'],name
assert json.loads((R/'qa/town-native-validation.json').read_text())['passed']
protected={}
for file,folder in [('ache-v1-source-hashes.json','character-natural-3d-v1'),('town-v6-source-hashes.json','whole-town-animals-3d-v6')]:
 records=json.loads((R/'reference'/file).read_text());bad=[p for p,h in records.items() if not (R.parent/folder/p).exists() or sha((R.parent/folder/p).read_bytes())!=h];protected[folder]={'files':len(records),'mismatches':bad};assert not bad,bad
refs=json.loads((R/'identity/protected-source-hashes.json').read_text());records=[refs['roster']]+refs['references'];bad=[p['path'] for p in records if sha(Path(p['path']).read_bytes())!=p['sha256']];protected['original2D']={'files':len(records),'mismatches':bad};assert not bad,bad
(R/'qa/protected-sources.json').write_text(json.dumps(protected,ensure_ascii=False,indent=2))
for c in meta:
 raw=(R/c['glb']).read_bytes();script=(R/'assets'/c['id']/'preview.js').read_text();embedded=base64.b64decode(json.loads(script.split('=',1)[1].rstrip(';')));assert embedded==raw,c['id']
 assert len(c['actions'])==30 and c['bones']==65,c['id']
town=(R/'town/小镇人物与动物-离线预览.html').read_text();embedded=base64.b64decode(json.loads(town.split('window.CARETAKER_ASSET=',1)[1].split(';',1)[0]));assert embedded==(R/'assets/01_hero_male/character.glb').read_bytes()
assert len(list((R/'qa/people').glob('*.png')))==270
final={'date':'2026-10-18','residentCount':45,'actionsPerResident':30,'nativeBonesPerResident':65,'glbChecks':[glb['passed'],glb['total']],'previewModelBytesMatch':45,'caretakerBytesMatch':True,'screenshots':270,'protectedSources':protected,'status':'Initial asset delivery; visual refinement and final user approval remain separate.'}
(R/'qa/final-validation.json').write_text(json.dumps(final,ensure_ascii=False,indent=2))
for name in ['README.md','验收报告.md']:
 for href in re.findall(r'\]\(([^)]+)\)',(R/name).read_text()):
  if '://' not in href and not href.startswith('#'):assert (R/href.split('#')[0]).exists(),href
exclude={'__pycache__','node_modules','debug-20261018'}
files=sorted(p for p in R.rglob('*') if p.is_file() and not exclude.intersection(p.parts) and p.name not in ['.DS_Store','delivery-manifest.json'] and not p.name.endswith('.blend1'))
manifest={str(p.relative_to(R)):{'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in files};(R/'delivery-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));files.append(R/'delivery-manifest.json')
out=R.parent/'人物3D-C方向-45位居民-V2.zip';tmp=out.with_suffix('.zip.tmp')
with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED,compresslevel=5,allowZip64=True) as z:
 for p in files:z.write(p,arcname=R.name+'/'+str(p.relative_to(R)))
with zipfile.ZipFile(tmp) as z:
 bad=z.testzip();assert bad is None,bad
 assert z.read(R.name+'/assets/01_hero_male/character.glb')==(R/'assets/01_hero_male/character.glb').read_bytes()
os.replace(tmp,out);report={'zip':out.name,'files':len(files),'bytes':out.stat().st_size,'sha256':sha(out.read_bytes()),'crcPassed':True,'manifestFiles':len(manifest),'previewResidentBytesMatch':45}
(R.parent/'人物3D-C方向-45位居民-V2-交付校验.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False),flush=True)
