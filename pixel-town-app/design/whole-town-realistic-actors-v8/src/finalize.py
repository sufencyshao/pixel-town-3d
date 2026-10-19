from pathlib import Path
import json,hashlib,zipfile,re,base64
R=Path(__file__).resolve().parent.parent
qa=json.loads((R/'qa/browser-validation.json').read_text());assert all(c['pass'] for c in qa['checks']);native=json.loads((R/'qa/blender-reopen.json').read_text());assert native['reopened'] and native['actors']==61 and native['armatures']==61 and native['externalImages']==0
lock=json.loads((R/'reference/source-lock.json').read_text());assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in lock.items());actors=json.loads((R/'actors.json').read_text());people=json.loads((R/'reference/original-human-identities.json').read_text());oldpets=json.loads((R/'reference/original-animal-identities.json').read_text())['animals'];pending=json.loads((R/'reference/pending-animals.json').read_text());assert {a['id'] for a in actors if a['type']=='person'}=={a['id'] for a in people};placedpets={a['id'] for a in actors if a['type']=='animal' and not a['id'].startswith('scenery-')};assert placedpets|{a['id'] for a in pending}=={a['id'] for a in oldpets};assert len(placedpets)==14
# Prove embedded bytes are the actual copied source files, including the unchanged town.
s=(R/'现成人物与动物-完整小镇.html').read_text();models=json.loads(re.search(r'window.MODEL_ASSETS=(.*?);window.MOTION_META=',s).group(1));index=json.loads((R/'reference/asset-index.json').read_text());assert len(models)==52
for key,p in index.items():assert base64.b64decode(models[key])==(R/p).read_bytes()
motions=json.loads(re.search(r'window.MOTION_ASSETS=(.*?);window.PENDING_ANIMALS=',s).group(1));assert len(motions)==20
for key,value in motions.items():assert base64.b64decode(value)==(R/'animations'/(key+'.glb')).read_bytes()
town=json.loads(re.search(r'window.TOWN_ASSET=(.*?);window.TOWN_ACTORS=',s).group(1));assert base64.b64decode(town)==(R/'Town-complete.glb').read_bytes()
lines=['# 入镇对象对应表','','| 姓名 | 身份或当前外观 | 区块 | 初始坐标 x,y,z | 现成动作 |','|---|---|---|---|---|']
for a in actors:lines.append('| '+a['name']+' | '+a['role']+' | '+a['zone']+' | '+', '.join(str(v) for v in a['position'])+' | '+('10类配套动作' if a.get('animationSet') else '作者原动画' if a.get('defaultAction') else '原姿势')+' |')
lines+=['','## 未放模型但保留的动物档案','', '、'.join(a['name']+'（'+a['breed']+'）' for a in pending),'','上述45人物、14原动物身份及2观景动物采用成品原外观。原件品种和对应关系见actors.json；不将观景麻雀/鸭改名为原鹦鹉。']
(R/'入镇对应表.md').write_text('\n'.join(lines)+'\n')
(R/'验收记录.md').write_text('''# 现成人物与动物入镇 V8 · 验收记录

2026-10-18。实际放入45人物＋16动物（14个原身份与2只观景鸟），未重复放置阿澈；6个缺成品的原动物身份保留。45人物ID集合与人物候选一致，14已放＋6待放动物ID集合等于原20档案；外形、品种变化与能力限制在对应表/页面中明示。

19项整镇浏览器检查通过，详见qa/browser-validation.json：对象数量与唯一ID、配套动作绑定/能力边界、61对象镜头取景、默认姿势静态障碍射线与地面高度、独立猫骨架、人物挥手骨骼实际变化、原GLB下载摘要、姓名/职业搜索、区块隔离/建筑剖切、冬季降雪/夜景、390px布局、file断网全模型加载、实际完整GLB导出。浏览过程无应用错误或绑定告警。静态障碍检测为三高度/八方向抽样，非连续体积碰撞与全动作穿插验收。

当前离线HTML内嵌52份人物/动物GLB、20动作与静态小镇，均和目录原件逐字节一致；源候选库与原小镇文件摘要锁定检查通过。只新增独立布置、运行脚本、场景快照和交接，不改正式应用/API/存档。

实际导出的Town-with-original-actors.glb约417MB，含61个具名角色根节点、162个蒙皮节点定义及小镇几何，不是空壳或旧静态小镇改名。Three.js导出期间有法线归一化、金属度/粗糙度贴图合并两类格式转换提示（145次，见qa/export-diagnostics.json），没有导出错误；作者原件不回写。GLB及Blender均为当前姿态的静态布置，未烘焙440组配套动作。

GLB已实际导入Blender并保存约363MB的.blend；重开后61个具名对象及61骨架均存在，坐标按Y-up/Z-up转换与actors.json误差小于1mm，268张图像均在包内，无外链图像缺失。详见qa/blender-import.json、qa/blender-reopen.json及对应日志。

整镇截图、人物/动物近景、夜雪与手机布局见qa。写实成品与原小镇低多边形建筑的画风差异保留，没有擅自重建角色或建筑。本轮完成入镇布置和可操作预览；未做自主生活/寻路、食水互动、全动画脚底接触、衣物物理、交通或正式应用接入。海琴烟/康娜的特殊外形及部分工作服仍是现成候选的已知限制。
''')
files=sorted(p for p in R.rglob('*') if p.is_file() and p.name!='delivery-sha256.json');hashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files};(R/'delivery-sha256.json').write_text(json.dumps(hashes,ensure_ascii=False,indent=2));out=R.parent/'完整小镇-现成人物与写实动物-V8.zip'
with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=5) as z:
 for p in sorted(R.rglob('*')):
  if p.is_file():z.write(p,str(Path(R.name)/p.relative_to(R)))
with zipfile.ZipFile(out) as z:
 assert z.testzip() is None
 for name,h in hashes.items():assert hashlib.sha256(z.read(R.name+'/'+name)).hexdigest()==h
report={'zip':out.name,'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'files':len(files)+1,'zipFilesMatch':True,'sourceHashesUnchanged':True,'embeddedBytesMatch':True,'people':45,'animals':16,'pendingIdentities':6,'browserChecks':len(qa['checks']),'blenderReopened':True};(R.parent/'现成人物动物入镇-V8-发布校验.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))
