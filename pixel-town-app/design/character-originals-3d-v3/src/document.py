from pathlib import Path
import json,hashlib,struct
R=Path(__file__).resolve().parent.parent;meta=json.loads((R/'manifest.json').read_text());am=json.loads((R/'animation-manifest.json').read_text());old=R.parent/'realistic-animals-3d-v4'
source=json.loads((old/'vendor/rocketbox-tree.json').read_text());sha=source['sha'];paths=[x['path'] for x in source['tree'] if x['type']=='blob'];sources=[]
for m in meta:
 matches=[p for p in paths if p.startswith('Assets/Avatars/') and '/Export/' in p and p.lower().endswith('/'+m['sourceModel'].replace('-','_')+'.fbx')];assert matches
 sources.append({'id':m['id'],'sourceModel':m['sourceModel'],'originalPaths':matches,'urls':['https://github.com/microsoft/Microsoft-Rocketbox/blob/'+sha+'/'+p for p in matches]})
for a in am:
 matches=[p for p in paths if p.startswith('Assets/Animations/') and p.endswith('/'+a['id']+'.max.fbx')];assert matches;sources.append({'motion':a['id'],'originalPaths':matches,'urls':['https://github.com/microsoft/Microsoft-Rocketbox/blob/'+sha+'/'+p for p in matches]})
(R/'vendor/original-source-index.json').write_text(json.dumps({'repository':'microsoft/Microsoft-Rocketbox','commit':sha,'files':sources},ensure_ascii=False,indent=2))
rows=['# 45位人物的现成外观候选','','仅为3D外观提案，不修改正式身份/API/记忆；未获用户美术确认。','', '| 姓名 | 原身份/职业 | 作者原版成品 | 装束 | 配套原动作 |','|---|---|---|---|---|']
for c in meta:rows.append('| '+c['name']+' | '+c['role']+' | '+c['sourceTitle']+' | '+c['outfit']+' | '+('10项' if c['animationSet'] else '原姿势，未附儿童动画')+' |')
rows+=['','海琴烟和康娜只安排普通人形候选，不含原精灵/龙类外观，是否用于这两位仍待确定；没有按旧2D重新制作。伙伴的未指定性别字段保持原值。','部分职业目前用原版日常装；女警暂用原版安保服，尚非对应警服；女消防员为呼吸器出勤装备，未选择日常便装。见各人物预览说明。']
(R/'人物对应表.md').write_text('\n'.join(rows)+'\n')
report=[]
for m in meta:
 raw=(R/m['glb']).read_bytes();n=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+n]);h=hashlib.sha256(raw).hexdigest();assert h==m['sha256'];assert g['asset']['extras']['license']=='MIT';report.append({'id':m['id'],'sourceModel':m['sourceModel'],'sha256':h,'joints':sum(len(s['joints']) for s in g['skins']),'images':len(g.get('images',[])),'morphTargets':sum(len(p.get('targets',[])) for me in g['meshes'] for p in me['primitives'])})
(R/'qa/asset-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
items=json.loads((R/'vendor/downloads.json').read_text())
for item in items:
 if not (R/item['file']).exists():item['file']='vendor/unselected/'+Path(item['file']).name
 assert hashlib.sha256((R/item['file']).read_bytes()).hexdigest()==item['sha256']
(R/'vendor/downloads.json').write_text(json.dumps(items,ensure_ascii=False,indent=2))
(R/'licenses/meshoptimizer-MIT.txt').write_text((R/'licenses/Three-MIT.txt').read_text().replace('Copyright © 2010-2025 three.js authors','Copyright (c) 2016-2024 Arseny Kapoulkine'))
(R/'README.md').write_text('''# 小镇人物 · 现成模型 V3

2026-10-18。打开 `现成人物-离线预览.html`，可直接离线使用。按姓名/职业搜索，切换全身、面部近看、正背侧，查看骨架、播放/暂停/拖动配套动作，分别下载人物原件和当前动作原件。

## 这次实际完成

- 取得45套不同的Microsoft Rocketbox成品GLB，保留完整原版面部、发型、服装、材质、体型与骨架，不按旧2D重做，不拆成裸模自造衣服。
- 建立40居民＋5伙伴的姓名/职业外观候选对照，详见 `人物对应表.md` 和 `manifest.json`。这是预览提案，**没有写入正式身份、记忆、关系或API绑定**。
- 44位成人候选支持同库10类原动作：自然站立、观察、交谈、思考、挥手、欢呼、鼓掌、跳舞、走路、跑步。动作按原作者男女骨架套件分别加载，合计20个原始动作文件；不把同一动作重复用于44人说成440段独立创作。
- 康娜的儿童候选仅显示原姿势，没有套成人动作。海琴烟与康娜的普通人形缺少原精灵/龙类特征，仍待确定是否合适；没有将它们写成最终外观。

## 来源与原件

作品为[Microsoft Rocketbox](https://github.com/microsoft/Microsoft-Rocketbox)，MIT，版权Microsoft 2020。固定原始仓库commit `0943055db6ec570bcef9f2c8b41c9e5467c808f9`；45人物FBX及20动作FBX的对应URL列在 `vendor/original-source-index.json`（65项均匹配官方仓库目录）。原FBX/MAX未批量下载，不能说包内含原生MAX工程。

便携GLB取自[CodeLove](https://models.codelove.in/)的Rocketbox转换；模型与动作内嵌Microsoft版权和MIT全文，保存下载URL、实际字节数、SHA-256及glTF资产信息在 `vendor/downloads.json`。`assets/`45个人物和`animations/`20个动作保持下载原字节。未采用网站其他来源不明的游戏角色。

预览使用Three.js与MeshoptDecoder解码压缩GLB，仅更改容器显示、动作名称的中文展示、相机和落地位置；不回写模型文件。配套动作独立保存，下载“人物原件”不自动带10项动作，完整包内另有动作目录。`licenses/`保留MIT许可与署名。6个未采用原件在 `vendor/unselected/`，只作筛选记录，不进入人物预览。

## 已知边界

这些是**作者原版外观候选**，不是已获用户认可的最终全员美术，也没有接入整镇或替换正式Electron应用。人物外观可换，身份/记忆/API与外观保持分离。

部分原件共用作者的基础面部或身体，45个不同成品文件不等于45种完全不同的基础人体。部分角色只有日常装：例如面包师、男厨师、咖啡师和邮差；女警用原版安保服候选，尚无合适的日常女警原版警服；女消防员为全套呼吸器出勤装备。没有为了凑职业自己重做制服或把便装算作职业服装完成。

未实现读书、用餐、侧躺、喂食、职业操作、道具握持、衣物物理、脚底IK或自主生活。动作会产生自然衣物形变，未逐帧验收全部接触/穿插；本轮完成模型库和配套动作可用性核验。未提供眼神/口型同步或脸部表情控制。

筛选中发现未采用的原女警防暴模型缺少口唇骨，无法完整绑定同库面部轨道。预览加载器会在内存中只绑定模型实际拥有的轨道并记录缺失；最终选型已换为合适的原版安保人物。源GLB/动作文件始终未修改。当前模型的绑定检查结果见验收记录。

## 验证与重建

`src/build_preview.py`用manifest和原GLB构建单文件HTML。`src/viewer.js`用项目既有Three.js依赖打包至 `viewer.bundle.js`；`src/acquire_roster.py`是原下载记录配方，当前最终外观/装束备注以manifest为准。`qa/`记录浏览器结果、全身/面部和视角截图，以及筛选过程证据。

正式应用、存档和API不在本次修改范围。上一版被否定的自建人物保留，未覆盖。
''')
print('source, identity, asset and license records updated')
