from pathlib import Path
import json,hashlib,zipfile,re,base64

root=Path(__file__).resolve().parent.parent
def digest(data):return hashlib.sha256(data).hexdigest()
for file in (root/'assets').glob('*.blend1'):file.unlink()
native=json.loads((root/'qa/model-validation.json').read_text())
browser=json.loads((root/'qa/browser-validation.json').read_text())
wave=json.loads((root/'qa/wave-validation.json').read_text())
assert len(native['checks'])==66 and all(x['pass'] for x in native['checks'])
assert len(browser['checks'])==51 and all(x['pass'] for x in browser['checks']) and not browser['errors']
assert len(wave['checks'])==13 and all(x['pass'] for x in wave['checks'])
html=(root/'阿澈-C方向-离线预览.html').read_text()
embedded=json.loads(re.search(r'window.CHARACTER_ASSET=("[^"]+");',html).group(1))
assert base64.b64decode(embedded)==(root/'assets/01-Ache.glb').read_bytes()
files=sorted(p for p in root.rglob('*') if p.is_file() and p.name!='delivery-manifest.json' and '__pycache__' not in p.parts)
manifest={'date':'2026-10-17','revision':'1.1 wave elbow correction','status':'first character, pending visual feedback','model_checks':66,'browser_checks':51,'wave_checks':13,'files':{str(p.relative_to(root)):{'bytes':p.stat().st_size,'sha256':digest(p.read_bytes())} for p in files}}
(root/'delivery-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
files.append(root/'delivery-manifest.json')
archive=root.parent/'人物3D-C方向-阿澈首版-V1.1.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as package:
 for file in files:package.write(file,str(Path(root.name)/file.relative_to(root)))
with zipfile.ZipFile(archive) as package:
 assert package.testzip() is None
 assert len(package.namelist())==len(files)
 for file in files:assert package.read(str(Path(root.name)/file.relative_to(root)))==file.read_bytes()
report={'archive':archive.name,'bytes':archive.stat().st_size,'sha256':digest(archive.read_bytes()),'files':len(files),'crc_pass':True,'member_bytes_match':True,'embedded_glb_matches':True}
(root.parent/'人物3D-C方向-阿澈首版-V1.1.校验.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
