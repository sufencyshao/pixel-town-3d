# 溪畔日常 · 现成人物与动物入镇 V8

2026-10-18。打开 `现成人物与动物-完整小镇.html`。已放入45位人物、14只原动物身份与2只观景鸟类，保留九区建筑、室内、四季、昼夜、天气和街景查看。人物、动物采用上一轮取得的作者完整成品，未按旧2D重做。

## 使用

右侧可搜索姓名/职业/物种，选择后近看全身或面部；也可点击附近名字或场景里的模型。支持播放该成品实际具备的动作、暂停动作、区块隔离和建筑剖切。走路/跑步按钮明确是原地试演，本版没有接入自主寻路或动物喂食、追球等生活流程。

“下载所选原模型”提供未修改的作者GLB。“下载当前入镇GLB”导出包含小镇、45人物和16动物的当前静态姿态；下方“静态小镇GLB”仍是未加角色的原小镇。两者边界明确。

`Town-with-original-actors.glb` 是本轮实际导出的入镇布置，不是把旧静态小镇重命名。`Town-with-original-actors.blend` 为该入镇快照的可编辑Blender版本；人物/动物有骨架，当前快照不含动画动作。运行预览中的动作来自另外保存的作者原件，不能声称已全部烘焙进整镇工程。首次打开约195MB的单文件HTML需等待载入；真实手机性能未验收。

## 实际放入的对象

- 45人物均沿用上一轮现成候选。公共服务角色放在B区，木工/维修/演奏/绘画放在D区，访客与活动协理放在E区，志愿照看者、园丁与兽医助理在F区，农夫在G区，商业角色在H区，到达/旅店/消防角色在I区。以 `actors.json` 的逐人位置和装束备注为准，非角色自主工作实现。
- 5猫、6犬、2兔与1马共14个原动物身份进入既有花园、庭院、公园和果园活动区。名字和ID保留。5猫共用kenchoo原版橘白猫，6犬复用原版比格/德牧，2兔复用Kelgar兔子，马用原版棕马；没有假称取得了5种猫和6种犬的独立外形成品。显示品种随原版更新，历史品种存在 `originalBreed` 中。
- 麻雀与绿头鸭是2只观景候选，未覆盖原鹦鹉、玄凤或金丝雀的身份。
- 青豆、蓝芽、小冠、柠羽、花栗、苔背共6只仍待合适的写实原件。档案保存在 `reference/original-animal-identities.json`，缺口在 `reference/pending-animals.json` 和页面中公开。

44成人有同库10类配套原动作，儿童候选为原姿势。猫和兔有原动画；犬、马、麻雀和鸭的原件没附动画，保持原姿势。没有通过平移静态模型冒充行走或飞行，也没有重做身体动画。

## 原件、许可和数据

人物以及犬/马/两种鸟：[Microsoft Rocketbox](https://github.com/microsoft/Microsoft-Rocketbox)，MIT；便携GLB由[CodeLove](https://models.codelove.in/)转换。猫：[kenchoo / Bicolor Cat](https://sketchfab.com/3d-models/bicolor-cat-e623a618ca344a8393d7ba4d63ec23cf)，CC BY 4.0，原副本来源[vr-cats](https://github.com/code4fukui/vr-cats)。兔：[CDmir / TinyWorlds为Kelgar制作的Rabbit](https://opengameart.org/content/rabbit-0)，CC0，沿用V3旧格式/原图着色器转换。署名与许可在 `licenses/`。

人物、动物、动作原GLB均和上一版逐字节一致；仅在场景外层容器做位置、方向及动物的等比米制适配。源码和记录在 `src/`、`actors.json` 和 `reference/`，原件摘要锁定在 `reference/source-lock.json`。原 `Town-complete.glb`、人物候选库与动物候选库不覆盖。

本轮修改独立设计目录与项目交接，不修改正式Electron应用、API、存档、人物记忆、关系或配置。海琴烟/康娜仍是普通人形外观候选，尚无原精灵/龙类外形；部分职业只有日常装或安保装，未制作专用制服，备注随模型保留。

## 核对范围与限制

见 `验收记录.md` 与 `qa/`。核对加载数量、实际骨架/动作绑定、原件下载摘要、61个对象镜头取景、默认姿势的静态障碍射线与地面高度、区块隔离/剖切、四季天气/夜景、390px布局、file断网、入镇GLB与Blender回读。静态障碍射线是抽样，不能等同连续碰撞、所有动画逐帧穿插或完整物理验收；没有脚底IK、衣物物理、道具握持、室内生活或自主工作。

重建：使用项目既有Three.js/esbuild打包 `src/viewer.js`，执行 `python3 src/package_preview.py`。`src/verify.cjs`检查浏览器功能，`src/save_blender.py`从实际导出GLB保存Blender工程。运行预览和原件均随包，断网可打开。
