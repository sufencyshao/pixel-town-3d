import json,struct
from pathlib import Path
R=Path(__file__).resolve().parent.parent
for path in (R/'assets').glob('*/*.glb'):
 raw=path.read_bytes();n,t=struct.unpack_from('<II',raw,12);g=json.loads(raw[20:20+n]);tail=raw[20+n:]
 for node in g.get('nodes',[]):
  name=node.get('name','')
  if any(k in name for k in ['hat','Hat','Cap','cap','Crown','crown','beret']):node.setdefault('extras',{})['removableForRest']=True
 j=json.dumps(g,separators=(',',':')).encode();j+=b' '*((-len(j))%4);out=struct.pack('<III',0x46546c67,2,20+len(j)+len(tail))+struct.pack('<II',len(j),0x4e4f534a)+j+tail;path.write_bytes(out)
print('Synchronized GLB rest accessory flags')
