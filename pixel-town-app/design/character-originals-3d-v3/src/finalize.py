from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib,base64,re,zipfile
R=Path(__file__).resolve().parent.parent;meta=json.loads((R/'manifest.json').read_text());qa=json.loads((R/'qa/browser-validation.json').read_text());assert all(c['pass'] for c in qa['checks']) and not qa['errors'] and not qa['warnings'];assert not any(m['skippedSourceTracks'] for m in qa['motion'])
identity=json.loads((R/'reference/original-identities.json').read_text());original=json.loads((R.parent/'character-residents-3d-v2/assets/manifest.json').read_text())['characters'];assert identity==[{k:c[k] for k in ['id','name','kind','role','sex']} for c in original];assert [(c['id'],c['name'],c['role'],c['sex']) for c in meta]==[(c['id'],c['name'],c['role'],c['sex']) for c in identity]
html=(R/'现成人物-离线预览.html').read_text();embedded=json.loads(re.search(r'window.ORIGINAL_ASSETS=(.*?);</script>',html).group(1));motions=json.loads(re.search(r'window.ANIMATION_ASSETS=(.*?);window.ORIGINAL_META=',html).group(1));assert len(embedded)==45 and len(motions)==20
for c in meta:assert base64.b64decode(embedded[c['id']])==(R/c['glb']).read_bytes()
for id,b in motions.items():assert base64.b64decode(b)==(R/'animations'/(id+'.glb')).read_bytes()
font=ImageFont.truetype('/System/Library/Fonts/STHeiti Light.ttc',18)
for batch in range(3):
 sheet=Image.new('RGB',(1500,1170),'#fafaf4');draw=ImageDraw.Draw(sheet)
 for k,m in enumerate(meta[batch*15:(batch+1)*15]):
  im=Image.open(R/'qa'/(m['id']+'-full.png'));im.thumbnail((300,350));x=(k%5)*300+(300-im.width)//2;y=(k//5)*390;sheet.paste(im,(x,y));draw.text(((k%5)*300+12,y+350),m['name']+' · '+m['role'],font=font,fill='#344438')
 sheet.save(R/'qa'/('人物总览-'+str(batch+1)+'.jpg'),quality=90)
(R/'验收记录.md').write_text('''# 现成人物 V3 核对记录

2026-10-18。45套不同作者成品文件，40居民＋5伙伴的候选身份对应；44成人各10类配套原动作，儿童候选不套成人动作。保持源文件字节，没有重做脸、衣服、骨架或动作。

97项浏览器检查通过：45人实际几何/贴图与动作套件、44成人合计440次模型/动作组合的轨道绑定、蒙皮顶点变化和有限值；人物/动作下载摘要一致；姓名/职业检索、390px、file断网加载男女套件与儿童模型、无绑定警告/页面报错。详见 `qa/browser-validation.json`。当前45模型未跳过任何动作轨道。未将共用动作说成独立制作的440条动作。

45模型与20动作的HTML内嵌数据均和下载原件逐字节一致，MIT与来源固定仓库65路径已匹配。45个id/名字/职业/sex与冻结身份及旧roster逐项一致。许可、来源和摘要见README、vendor、licenses和manifest。

全身图已逐人截取，三张总览、代表人物的正背侧/面部截图可回看；已排除防暴警装等不合适的候选。最终更换的杂货店员、咖啡师与女警候选保持原版服装；女警目前是安保服，不能算对应警服完成。女消防员为出勤呼吸器装备。旧筛选截图仅为过程证据，不是当前预览。

当前45人均为未获用户美术确认的外观提案；海琴烟/康娜的普通人形是否合适仍待定。部分职业缺工作服；无全部生活动作、道具握持、脚底IK、衣物物理或整镇接入。本轮不修改正式应用、API、存档或旧人物成品。
''')
files=sorted(p for p in R.rglob('*') if p.is_file() and p.name!='delivery-sha256.json');hashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files};(R/'delivery-sha256.json').write_text(json.dumps(hashes,ensure_ascii=False,indent=2));out=R.parent/'现成人物成品-45位候选-V3.zip'
with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(R.rglob('*')):
  if p.is_file():z.write(p,str(Path(R.name)/p.relative_to(R)))
with zipfile.ZipFile(out) as z:
 assert z.testzip() is None
 for name,h in hashes.items():assert hashlib.sha256(z.read(R.name+'/'+name)).hexdigest()==h
report={'file':out.name,'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'files':len(files)+1,'zipFilesMatch':True,'models':45,'sourceClips':20,'animatedCharacters':44,'modelMotionCombinations':440,'browserChecks':len(qa['checks']),'identitiesMatch':True,'embeddedBytesMatch':True};(R.parent/'现成人物成品-V3-发布校验.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))
