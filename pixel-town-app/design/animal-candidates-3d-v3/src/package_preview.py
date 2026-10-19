from pathlib import Path
import struct,json,base64,hashlib
R=Path(__file__).resolve().parent.parent
items=[
 ('rabbit','Kelgar兔子','CDmir / TinyWorlds','rabbit.glb','https://opengameart.org/content/rabbit-0','CC0-1.0','为Kelgar制作的完整兔子，原骨架和原动作。仅转换旧Blender格式、用原贴图连接PBR材质，没有重新制作外形或动画。'),
 ('bird','自然体型小鸟','Fabio Gonzalez','bird.glb','https://opengameart.org/content/bird','CC0-1.0','完整原版小鸟，原贴图、19骨及一条原生组合动画。仅做旧格式/材质转换，未新增动作。'),
 ('madtroll-cat','madtrollstudio猫','madtrollstudio','madtroll-cat.glb','https://poly.pizza/m/YvVobPlTlQ','CC-BY-3.0','开源游戏find-the-cat中保存的完整猫成品，原文件字节不变。静态、无骨架和原生动作，当前仅作外形候选，不能直接冒充能行走的动物。'),
]
items=[item for item in items if item[0]=='rabbit']
meta=[];assets={}
for id,label,author,file,url,license,note in items:
 raw=(R/'assets'/file).read_bytes();n=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+n]);meta.append({'id':id,'label':label,'author':author,'kind':'动物候选','glb':'assets/'+file,'official':url,'license':license,'note':note,'animations':[{'name':a.get('name','Animation')} for a in g.get('animations',[])],'skinCount':len(g.get('skins',[])),'sha256':hashlib.sha256(raw).hexdigest(),'front':'-Z' if id=='bird' else '+Z','defaultAction':'Guarding' if id=='rabbit' else None});assets[id]=base64.b64encode(raw).decode()
(R/'manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
s=(R/'template.html').read_text().replace('__META__',json.dumps(meta,ensure_ascii=False)).replace('__ASSETS__',json.dumps(assets)).replace('__VIEWER__',(R/'viewer.bundle.js').read_text())
(R/'写实动物-原版预览.html').write_text(s)
(R/'其他成品动物-离线预览.html').write_text(s)
print([(m['label'],len(m['animations']),m['skinCount']) for m in meta])
