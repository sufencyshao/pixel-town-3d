# 写实动物成品预览 V4 · 2026-10-18

直接打开 `写实动物-原版预览.html`，不依赖网络。所有模型可旋转、查看正背侧、显示骨架、下载GLB；有原生动作的猫与兔可播放、暂停和拖动进度。

## 实际取得并纳入预览

| 模型 | 来源与作者 | 许可 | 本次原件实际内容 |
|---|---|---|---|
| 橘白双色猫 Bicolor Cat | kenchoo / code4fukui vr-cats | CC BY 4.0 | 40关节，1条约8.708秒原动画，原贴图 |
| 比格犬 | Microsoft Rocketbox，经CodeLove转换 | MIT | GLB 34关节，毛皮贴图，无动画 |
| 德国牧羊犬 | 同上 | MIT | GLB 35关节，毛皮贴图，无动画 |
| 麻雀 | 同上 | MIT | GLB 39关节，羽毛贴图，无动画 |
| 棕马 | 同上 | MIT | GLB 39关节，毛皮贴图，无动画 |
| 绿头鸭 | 同上 | MIT | GLB 17关节，羽毛贴图，无动画 |
| Kelgar兔子（保留V3） | CDmir / TinyWorlds | CC0 | 37源骨，7段原动画及2个静态姿势 |

这些是外观候选，未获用户美术确认，未分配20只动物身份，也未接入整镇或正式应用。不能据此说全部20只已替换。原狗品种可换，但鸟种未获同样授权，麻雀和绿头鸭只是候选；不能把原鹦鹉直接改种。猫仍只有一套成品；没有用重复改色冒充五套不同成品。

猫的源作品名为Bicolor Cat，实际呈橘白花色，预览依实际外观命名。猫GLB保留原字节，单条Animation没有自行拆分或增加动作。Rocketbox模型保持绑定姿势（例如马尾伸直），没有自造走路/摆尾动画。

## 来源、原件与转换边界

- 猫作者：[kenchoo / Bicolor Cat](https://sketchfab.com/3d-models/bicolor-cat-e623a618ca344a8393d7ba4d63ec23cf)。从[vr-cats](https://github.com/code4fukui/vr-cats/tree/0b5f3b586cdcda2d33cca54b34ce80f52f46376c)取得公开CC BY副本；原GLB asset.extras嵌有作者、许可及作品URL，与仓库署名一致。原件 `vendor/bicolor-cat.glb`，未改网格、贴图、骨架和动画。
- Rocketbox：[Microsoft原仓库](https://github.com/microsoft/Microsoft-Rocketbox/tree/0943055db6ec570bcef9f2c8b41c9e5467c808f9/Assets/Animals)，MIT。原FBX、TGA贴图和作者PNG预览均在 `vendor/rocketbox/`，固定commit和逐文件摘要在 `sources.json`。5个GLB取自[CodeLove](https://models.codelove.in/models/category/animals/)，各自内嵌Microsoft MIT完整许可；压缩GLB字节未改。原FBX也经Blender回读确认未附动画，记录 `qa/rocketbox-source-inspection.json`。GLB转换去除的辅助关节使关节数与FBX骨数略有区别，不能声称与原FBX逐关节一致。
- 兔子：[OpenGameArt Rabbit](https://opengameart.org/content/rabbit-0)，源blend和转换说明随包；保留V3结果。仅旧格式转换和原图连接PBR材质，未重建外形。
- 所有原件摘要和实际GLB动作见 `manifest.json`；许可/署名在 `licenses/`。Three.js及MeshoptDecoder为本地打包。HTML中的落地平移、相机、灯光用于预览，不写入原GLB。

## 尚未解决与排除

- **陆龟**：[Christian的动画陆龟](https://sketchfab.com/3d-models/tortoise-riggedanimated-f911589e275e4c60963d52b31bc0b061)，源为NHM Vienna扫描，CC BY-NC。作者页可检索但本机取文件受站点403限制，未取得下载原件，不能称已接入。
- **豚鼠**：[Innerscene Domestic guinea pig](https://www.innerscene.com/tools/library/3d-parts/domestic-guinea-pig-794a1725)自述原创CC0，下载API返回403。未取得文件，外观/贴图/骨架与动作均未验证，不能因页面写“textured”就认为合格。
- [QubiCone免费豚鼠](https://www.cgtrader.com/free-3d-models/animal/mammal/guinea-pig-f9a8e819-b43e-4dba-80f7-5abdc40ac208)有纹理与高低模，AI辅助修整，下载/许可与动作尚未核实。未纳入包。
- [免费Budgerigar成品](https://www.cgtrader.com/free-3d-models/animal/other/budgerigar-ba8bed9d-e798-45f7-b1d0-17cd6ac33bd3)描述有两档模型和动画；尚未取得文件、核实许可和外观，不能称已完成虎皮鹦鹉。
- Benny罗威纳、Jack Russell和黄嘴伯劳原工程在 `vendor/oga/`，只作排查记录，**未纳入当前预览**。Benny旧材质、多个UV以及缺失外链头部图需再核对；Jack Russell实际无UV毛皮贴图/无动作，不适合当前写实要求；伯劳有原羽毛图与65骨但未附动作，旧自定义着色器尚未转换。未消耗额度自行重建这些模型。
- Cube Pets、Quaternius犬马、V6自建动物不再是当前采用路线。

## 构建与验证

`src/build_preview.py`从当前manifest和assets生成单文件离线预览；`viewer.bundle.js`由 `src/viewer.js` 使用既有Three.js依赖打包。`src/verify.cjs`检查实际模型切换、内嵌字节、材质贴图、视角、猫骨骼动画、下载摘要、390px及file断网打开；结果与截图在 `qa/`。源码/运行素材/安装包/存档分开看待，本轮未修改正式应用、API或存档。
