from pathlib import Path
import zipfile,hashlib,json,re,base64,struct
R=Path(__file__).resolve().parent.parent
m=json.loads((R/'manifest.json').read_text());v=json.loads((R/'validation.json').read_text())
assert v['status']=='PASS' and v['sha256']==m['sha256']
assert json.loads((R/'qa/detail-validation.json').read_text())['status']=='PASS'
asset=(R/'Town-complete.glb').read_bytes();s=(R/'完整小镇-离线预览.html').read_text()
embedded=re.search(r'window.TOWN_ASSET\s*=\s*["\x27]([^"\x27]+)',s)
assert embedded and base64.b64decode(embedded[1])==asset
def images(p):
    with p.open('rb') as f:
        f.read(12);n,t=struct.unpack('<II',f.read(8));j=json.loads(f.read(n));n,t=struct.unpack('<II',f.read(8));b=f.read(n)
    hashes=[]
    for i in j.get('images',[]):
        view=j['bufferViews'][i['bufferView']];start=view.get('byteOffset',0);hashes.append(hashlib.sha256(b[start:start+view['byteLength']]).hexdigest())
    return sorted(hashes)
a=images(R/'Town-complete.glb');assert len(a)==8 and a==images(R.parent/'whole-town-3d-v1/Town-complete.glb')
(R/'qa/texture-validation.json').write_text(json.dumps({'status':'PASS','images':8,'sameAsV1':True,'hashes':a},indent=2))
for name in ['Town-complete.blend1']:
    p=R/name
    if p.exists():p.unlink()
files=[p for p in sorted(R.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ['.log','.blend1'] and p.name!='package-validation.json']
z=R.parent/'完整小镇-街道细节-Blender模型-V2.zip'
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as out:
    for p in files:out.write(p,str(Path(R.name)/p.relative_to(R)))
with zipfile.ZipFile(z) as out:
    assert out.testzip() is None
    for p in files:assert hashlib.sha256(out.read(str(Path(R.name)/p.relative_to(R)))).digest()==hashlib.sha256(p.read_bytes()).digest()
result={'status':'PASS','files':len(files),'zipBytes':z.stat().st_size,'embeddedGLBMatches':True,'membersMatch':True,'CRC':'PASS','sha256':hashlib.sha256(z.read_bytes()).hexdigest()}
(R/'package-validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
