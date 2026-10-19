"""Package complete licensed models. Geometry/materials/skins/animations remain source data."""
from pathlib import Path
import json,struct,hashlib,base64,copy
R=Path(__file__).resolve().parent.parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def read_glb(path):
 raw=path.read_bytes();assert struct.unpack_from('<I',raw)[0]==0x46546c67;n=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+n]);size,kind=struct.unpack_from('<II',raw,20+n);assert kind==0x004e4942;return g,raw[28+n:28+n+size]
def portable(path,out):
 if path.suffix=='.glb':g,binary=read_glb(path)
 else:
  g=json.loads(path.read_text());assert len(g['buffers'])==1;u=g['buffers'][0]['uri'];assert u.startswith('data:');binary=base64.b64decode(u.split(',',1)[1])
 original=copy.deepcopy(g)
 for im in g.get('images',[]):
  u=im.get('uri','')
  if u and not u.startswith('data:'):
   p=path.parent/u;im['uri']='data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode()
 for buf in g['buffers']:buf.pop('uri',None)
 # Assert all visual and motion definitions survive the resource-only repacking.
 for key in ['nodes','meshes','materials','skins','animations','accessors','bufferViews','textures','samplers']:assert g.get(key)==original.get(key),key
 text=json.dumps(g,separators=(',',':')).encode();text+=b' '*((-len(text))%4);data=binary+b'\0'*((-len(binary))%4)
 raw=struct.pack('<III',0x46546c67,2,28+len(text)+len(data))+struct.pack('<II',len(text),0x4e4f534a)+text+struct.pack('<II',len(data),0x004e4942)+data;out.write_bytes(raw)
 check,b=read_glb(out);assert b[:len(binary)]==binary
 return {'sourceFile':str(path.relative_to(R)),'sourceSha256':sha(path.read_bytes()),'portableSha256':sha(raw),'binaryDataSha256':sha(binary),'sourceBinaryDataSha256':sha(binary),'originalDefinitionKeysPreserved':True,'animations':[{'name':a['name']} for a in g.get('animations',[])],'meshCount':len(g.get('meshes',[])),'skinCount':len(g.get('skins',[]))}
items=[
 ('male-casual','便装男性','人物','Quaternius','vendor/quaternius-men/Quaternius-Casual.glb','https://quaternius.com/packs/ultimatemodularcharacters.html','开源项目保存的完整便装成品，24项原生动画。'),
 ('male-worker','工装男性','人物','Quaternius','vendor/quaternius-men/Quaternius-Worker.glb','https://quaternius.com/packs/ultimatemodularcharacters.html','开源项目保存的完整工装成品，24项原生动画。'),
 ('female-casual','便装女性','人物','Quaternius','vendor/quaternius-women/Casual.gltf','https://quaternius.com/packs/ultimatemodularwomen.html','作者下载目录中的完整便装角色，24项原生动画。'),
 ('female-worker','工装女性','人物','Quaternius','vendor/quaternius-women/Worker.gltf','https://quaternius.com/packs/ultimatemodularwomen.html','作者下载目录中的完整工装角色，24项原生动画。')]
for id,label in [('cat','猫'),('dog','狗'),('bunny','兔子'),('parrot','鹦鹉')]:items.append(('pet-'+id,label,'动物','Kenney','vendor/kenney-cube-pets/Models/GLB format/animal-'+id+'.glb','https://kenney.nl/assets/cube-pets','作者Cube Pets 2.0原版，8项原生动画；保留成品外形与配色。'))
records=[]
for id,label,kind,author,src,official,note in items:
 out=R/'assets'/(id+'.glb');audit=portable(R/src,out);records.append({'id':id,'label':label,'kind':kind,'author':author,'official':official,'license':'CC0-1.0','note':note,'glb':str(out.relative_to(R)),**audit})
(R/'manifest.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
assets={c['id']:base64.b64encode((R/c['glb']).read_bytes()).decode() for c in records}
s=(R/'template.html').read_text().replace('__META__',json.dumps(records,ensure_ascii=False)).replace('__ASSETS__',json.dumps(assets)).replace('__VIEWER__',(R/'viewer.bundle.js').read_text());(R/'原版成品-离线预览.html').write_text(s)
originals=sorted(p for p in (R/'vendor').rglob('*') if p.is_file());(R/'qa/source-hashes.json').write_text(json.dumps({str(p.relative_to(R)):sha(p.read_bytes()) for p in originals},ensure_ascii=False,indent=2))
print('Packed complete original models',len(records),'HTML bytes',len(s.encode()))
