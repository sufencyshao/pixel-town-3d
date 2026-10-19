from pathlib import Path
import urllib.request,json,struct,hashlib,concurrent.futures
R=Path(__file__).resolve().parent.parent;j=json.loads((R/'vendor/catalog.json').read_text());by={m['slug']:m for m in j['models']}
slugs=['female-adult-16','female-adult-17','fire-female-02','fire-female-03','security-female-01','business-female-03']
def dl(slug):
 m=by[slug];p=R/'assets'/(slug+'.glb');raw=urllib.request.urlopen('https://models.codelove.in'+m['glb'],timeout=35).read();p.write_bytes(raw);n=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+n]);return {'file':'assets/'+slug+'.glb','url':'https://models.codelove.in'+m['glb'],'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'asset':g['asset'],'animations':[a.get('name') for a in g.get('animations',[])],'skins':[len(s['joints']) for s in g.get('skins',[])]}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:result=list(ex.map(dl,slugs))
items=json.loads((R/'vendor/downloads.json').read_text());items.extend(result);(R/'vendor/downloads.json').write_text(json.dumps(items,ensure_ascii=False,indent=2))
meta=json.loads((R/'manifest.json').read_text());(R/'qa/main-manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2));base=meta[1]
for slug in slugs:
 m=by[slug];d=next(d for d in result if d['file']=='assets/'+slug+'.glb');c={**base,'id':slug,'label':m['title'],'name':m['title'],'sourceModel':slug,'sourceTitle':m['title'],'kind':'补充选型','glb':'assets/'+slug+'.glb','bones':d['skins'][0],'sha256':d['sha256']};meta.append(c)
(R/'manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
