from pathlib import Path
import json,struct,math,hashlib
B=Path(__file__).resolve().parents[1];M=json.loads((B/'assets/manifest.json').read_text());out=[];hashes={}
for a in M['animals']:
 p=B/a['glb'];b=p.read_bytes();assert b[:4]==b'glTF';jlen=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+jlen]);data=b[20+jlen+8:];checked=0;checks=[]
 def vals(ix):
  ac=g['accessors'][ix];v=g['bufferViews'][ac['bufferView']];width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[ac['type']];code,size={5120:('b',1),5121:('B',1),5122:('h',2),5123:('H',2),5125:('I',4),5126:('f',4)}[ac['componentType']];stride=v.get('byteStride',width*size);start=v.get('byteOffset',0)+ac.get('byteOffset',0)
  return [struct.unpack_from('<'+code*width,data,start+i*stride) for i in range(ac['count'])]
 for i,ac in enumerate(g['accessors']):
  if ac['componentType']==5126:
   vv=vals(i);assert all(math.isfinite(x) for row in vv for x in row);checked+=sum(len(row) for row in vv)
 for me in g['meshes']:
  for pr in me['primitives']:
   at=pr['attributes'];assert 'JOINTS_0' in at and 'WEIGHTS_0' in at
   w=vals(at['WEIGHTS_0']);assert all(abs(sum(row)-1)<.015 for row in w);checks.append(len(w))
 for an in g['animations']:
  for ch in an['channels']:
   if ch['target']['path']=='rotation':
    for q in vals(an['samplers'][ch['sampler']]['output']):assert abs(sum(v*v for v in q)-1)<.004
 assert set(an['name'] for an in g['animations'])==set(a['actions'])
 hashes[a['glb']]=hashlib.sha256(b).hexdigest();bp=B/'assets'/(a['id']+'.blend');hashes['assets/'+bp.name]=hashlib.sha256(bp.read_bytes()).hexdigest()
 out.append({'id':a['id'],'glbValid':True,'skinCount':len(g['skins']),'clips':len(g['animations']),'finiteFloatValues':checked,'skinWeightVertices':sum(checks),'unitQuaternions':True})
hashes['assets/manifest.json']=hashlib.sha256((B/'assets/manifest.json').read_bytes()).hexdigest();(B/'qa/glb-structure.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));(B/'qa/asset-sha256.json').write_text(json.dumps(hashes,indent=2));print(json.dumps({'models':len(out),'clips':sum(x['clips'] for x in out),'floats':sum(x['finiteFloatValues'] for x in out),'skinnedVertices':sum(x['skinWeightVertices'] for x in out)},indent=2))
