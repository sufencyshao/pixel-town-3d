import json, urllib.request, urllib.parse, hashlib, shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1]
repo='NafisRayan/Animate-Rigged-Humanoid-No-Blender'; commit='5821923af517ac5fdc82505faa92a0d575fc1b1a'
prefix='Universal Base Characters[Standard]/Universal Base Characters[Standard]/'
base=prefix+'Base Characters/Godot - UE/'
records=[]
def fetch(remote,local):
 url=f'https://raw.githubusercontent.com/{repo}/{commit}/'+urllib.parse.quote(remote,safe='/')
 p=R/local;p.parent.mkdir(parents=True,exist_ok=True)
 if not p.exists():
  req=urllib.request.Request(url,headers={'User-Agent':'PixelTown-Foundation-Asset-Audit'})
  with urllib.request.urlopen(req,timeout=60) as response:p.write_bytes(response.read())
 b=p.read_bytes();records.append({'path':str(p.relative_to(R)),'upstreamPath':remote,'url':url,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
 return p
fetch(prefix+'License_Standard.txt','reference/License_Base_Characters.txt')
for kind in ['Superhero_Male','Superhero_Female']:
 p=fetch(base+kind+'_FullBody.gltf','vendor/base/'+kind+'_FullBody.gltf')
 doc=json.loads(p.read_text())
 for b in doc.get('buffers',[]):fetch(base+urllib.parse.unquote(b['uri']),'vendor/base/'+urllib.parse.unquote(b['uri']))
 for im in doc.get('images',[]):
  u=urllib.parse.unquote(im['uri'])
  # Preserve exact source URI while resolving exporter spelling variants to same authentic PNG.
  source=u.replace('_png.png','.png')
  if source=='T_Superhero_Female_Dark.png':source='T_Superhero_Female_Dark_BaseColor.png'
  fetch(base+source,'vendor/base/'+u)
hair=prefix+'Hairstyles/Origin at 0/glTF (Godot)/'
for name in ['Hair_Beard','Hair_Buns','Hair_Buzzed','Hair_BuzzedFemale','Hair_Long','Hair_SimpleParted']:
 p=fetch(hair+name+'.gltf','vendor/hair/'+name+'.gltf')
 doc=json.loads(p.read_text())
 for b in doc.get('buffers',[]):fetch(hair+urllib.parse.unquote(b['uri']),'vendor/hair/'+urllib.parse.unquote(b['uri']))
 for im in doc.get('images',[]):
  u=urllib.parse.unquote(im['uri']);fetch(hair+u,'vendor/hair/'+u)
(R/'reference/source-manifest.json').write_text(json.dumps({'date':'2026-10-18','repo':'https://github.com/'+repo,'commit':commit,'license':'CC0-1.0','official':'https://quaternius.com/packs/universalbasecharacters.html','files':records},indent=2,ensure_ascii=False))
print(json.dumps({'files':len(records),'bytes':sum(x['bytes'] for x in records)},indent=2))
