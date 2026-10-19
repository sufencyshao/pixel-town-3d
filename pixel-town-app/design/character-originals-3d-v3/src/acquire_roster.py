from pathlib import Path
import json,urllib.request,concurrent.futures,hashlib,struct
R=Path(__file__).resolve().parent.parent
source=R.parent/'character-residents-3d-v2/assets/manifest.json';roster=json.loads(source.read_text())['characters'];cat=json.loads((R/'vendor/catalog.json').read_text());by={m['slug']:m for m in cat['models']}
slugs=['male-adult-01','female-adult-01','male-adult-02','male-adult-03','construction-male-02','delivery-male-01','police-male-01','medical-male-01','gardener-male-01','male-adult-04','male-adult-05','female-adult-02','chef-female-01','business-female-01','medical-female-02','business-female-02','female-adult-03','female-adult-04','medical-female-03','female-adult-05','fire-male-01','male-adult-06','wood-male-01','male-adult-07','male-adult-08','male-adult-09','business-male-01','construction-male-03','business-male-02','male-adult-10','fire-female-01','female-adult-17','female-adult-07','female-adult-08','female-adult-09','business-female-03','construction-female-01','female-adult-11','security-female-01','medical-female-01','female-adult-12','female-child-01','female-adult-13','female-adult-14','female-adult-15']
assert len(slugs)==len(roster)==len(set(slugs))==45
initial=json.loads((R/'vendor/downloads.json').read_text())
def dl(slug):
 m=by[slug];p=R/'assets'/(slug+'.glb')
 if not p.exists():p.write_bytes(urllib.request.urlopen('https://models.codelove.in'+m['glb'],timeout=40).read())
 raw=p.read_bytes();n=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+n]);assert 'Microsoft' in g['asset'].get('copyright','');assert g['asset']['extras']['license']=='MIT';return {'file':str(p.relative_to(R)),'url':'https://models.codelove.in'+m['glb'],'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'asset':g['asset'],'animations':[a.get('name') for a in g.get('animations',[])],'skins':[len(s['joints']) for s in g.get('skins',[])]}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:downloads=list(ex.map(dl,slugs))
initial={x['file']:x for x in initial};initial.update({x['file']:x for x in downloads});(R/'vendor/downloads.json').write_text(json.dumps(list(initial.values()),ensure_ascii=False,indent=2))
identities=[{k:c[k] for k in ['id','name','kind','role','sex']} for c in roster];(R/'reference/original-identities.json').write_text(json.dumps(identities,ensure_ascii=False,indent=2))
meta=[]
for c,slug,d in zip(roster,slugs,downloads):
 m=by[slug];child='child' in slug;formal=m.get('role','') not in ['','Business'];note=('儿童原版人形候选，仅展示原姿势，不将成人动作套在儿童骨架。' if child else '采用作者完整成品，保留原面部、发型、服装、体型和骨架；载入同库10项配套原动作。')
 if c['id'] in ['04_baker_male','11_chef_male','26_baker_male','34_driver_female','38_postal_female']:note+=' 当前采用日常便装，不代表已有该职业专用工作服。'
 if c['sex']=='unspecified':note+=' 伙伴仅作外观候选，原身份字段保持未指定；不根据模型性别改档案。'
 if c['id'] in ['hai-qin-yan','kanna']:note+=' 该成品为普通人形，没有原精灵/龙类外观特征，尚未确定用于此伙伴。'
 meta.append(dict(id=c['id'],label=c['name'],name=c['name'],role=c['role'],sex=c['sex'],author='Microsoft / Rocketbox',kind=c['role'],official='https://github.com/microsoft/Microsoft-Rocketbox',license='MIT',note=note,glb='assets/'+slug+'.glb',sourceModel=slug,sourceTitle=m['title'],skinCount=len(d['skins']),bones=d['skins'][0],sha256=d['sha256'],front='+Z',defaultAction='Idle',animationSet=None if child else m['animationSet'],status='appearance-candidate',outfit='作者原版工作装' if formal else '作者原版日常装'))
(R/'manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2));print('Downloaded',len(meta),'distinct characters',sum(x['bytes'] for x in downloads),'bytes')
