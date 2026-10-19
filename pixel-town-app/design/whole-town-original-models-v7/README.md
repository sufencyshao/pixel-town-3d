# 原版完整模型 · 整镇接入 V7

> 当前停止采用：用户随后明确“不要卡通风格”。本目录只保留为风格要求更新前的试接入证据；不要继续扩展这批动物，也不要把它当成已获当前美术认可的版本。最新工作转为写实成品选型，见 `../animal-candidates-3d-v3/README.md`。

2026-10-18。用户认可自然比例的原版犬马样例，并明确允许更换犬种，直接采用合适的原版模型。本版把6只狗和1匹马接入原小镇生活预览；阿澈照看者也改用完整原版便装角色。没有重新制作外形、贴图、骨架或动画。

[打开整镇预览](原版模型整镇-离线预览.html)。默认近看赤丸；可在右侧切换动物、呼唤、喂食、抛球、散步及回栖息点。原四季、昼夜、天气和建筑查看功能继续保留。HTML已内嵌完整小镇、原版人物、3种原版动物及全部原生动画，断网可用。约132MB，首次载入需等待；不代表真实手机性能已验收。

## 身份与模型

|名字|原档案品种|当前成品外观|原生动作|
|---|---|---|---:|
|栗饼|柯基|Quaternius ShibaInu 柴犬|12|
|赤丸|柴犬|Quaternius ShibaInu 柴犬|12|
|墨点|边境牧羊犬|Quaternius Husky 哈士奇|12|
|麦穗|金毛|Quaternius Husky 哈士奇|12|
|可栗|腊肠犬|Quaternius ShibaInu 柴犬|12|
|卷卷|玩具贵宾|Quaternius Husky 哈士奇|12|
|小栗|设得兰矮种马|Quaternius Horse 马匹|13|

名字和ID仍对应原动物，原20只身份档案完整保存在 `reference/original-animal-identities.json`。当前犬种和毛色随作者原版更新，历史品种保存在 `originalBreed` 字段；没有把哈士奇显示成金毛。Horse仅作为小栗的马匹外观，不声称作者专门制作了设得兰品种。阿澈使用Quaternius原版男性便装完整角色，24项原生动画；人物名字、人设、记忆、关系及API配置没有迁移或重置，正式应用未纳入本轮。

其余13只猫、鸟、兔、豚鼠和陆龟尚未匹配满意的成熟成品。它们的名字和档案保留在页面“待匹配”列表，本版不显示用户已否定的旧自建外形。45位居民尚未批量换成完整原版人物。

## 保持原版的方式

动物来自 [Quaternius Ultimate Animated Animals](https://quaternius.com/packs/ultimateanimatedanimals.html)，CC0；原始glTF/许可与固定GitHub提交下载记录在 `vendor/animals/`。人物来自 [Ultimate Modular Men](https://quaternius.com/packs/ultimatemodularcharacters.html)，CC0；开源项目冻结原件和许可在 `vendor/quaternius-men/`。这些原件在上一轮已取得，本轮直接核对摘要复用。

`assets/models/`中的4份GLB与已确认的V2样例字节一致，包含完整原网格、材质、骨骼和原动画。浏览器仅在模型外加一个等比缩放/坐标平移容器，适配小镇米制尺寸与地面；不缩头、拉腿、换色、改顶点或重绑骨架。头部锚点与尺寸由实际原模型测量，见 `reference/model-dimensions.json`。同一成品在离线HTML里只内嵌一份，每只动物有独立骨骼播放实例。

原静态 `Town-complete.glb` 与V6字节一致，建筑、原植被和布局没有重做。本轮提供运行预览与原版GLB，没有重导出一个声称已更新的Blender整镇工程；旧V6和人物V2工程保留作历史。

## 行为与原动作的对应

原生 `Walk`、`Gallop`、`Eating` 对应走路、奔跑和进食；`Idle`、`Idle_2`、低头待机对应安静观察、站立休息和低头观察/饮水示意。没有加入自建身体动画。原版不含梳理毛发动作，因此本版不再随机进入梳理状态。

照看者的站立/走路/挥手使用原生 `Idle_Neutral` / `Walk` / `Wave`；喂食、抛球的手势使用原生 `Interact` 作动作示意，食物和球仍按实际流程运动。它不是精确的撒食或投掷专用动作。原人物尚缺轻抚动作，该按钮明确停用；没有用挥手或旧自造动作冒充轻抚。原生24动画含战斗内容，不等于24项生活动作。

保留了自主走动、食水、需要变化、犬类同伴接近/玩耍、追球衔回、陪伴散步及雨夜回棚。修正了棚柱避让：相邻网格中心虽能落脚，连接线也可能擦过棚柱；现在对这些连接边一并禁行，防止花店前庭的狗回棚卡住。互动镜头按实际人物和动物边界取景，避免截掉人物头顶。

## 验证与继续

验收证据见 [验收报告](验收报告.md)、`qa/browser-validation.json`、`qa/shelter-regression.json`及实际整镇截图。验证范围是桌面Chrome、390px布局和file离线；没有声明正式应用、API、存档或真实移动设备性能已验收。后续从 `reference/asset-bindings.json` 继续匹配其余物种，先核对成品质量、许可及原动作，再加入绑定；不要恢复旧自建路线。

重建：用已有Three.js 0.180.0 / esbuild 0.25.9构建 `src/viewer.js`，执行 `python3 src/package_preview.py`。运行本目录HTTP服务后执行 `src/verify.cjs`（Playwright/Chrome），运行 `node src/shelter-regression.mjs`可复查棚柱寻路回归。生成器可使用本目录保留的来源元数据，无需旧聊天或相邻目录。
