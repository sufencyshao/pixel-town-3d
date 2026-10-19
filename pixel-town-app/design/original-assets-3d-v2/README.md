# 原版成品 V2 · 自然比例动物

2026-10-18。用户反馈上一版动物太Q，撤下Cube Pets动物，改为作者原版四足犬与马。人物4套样例继续保留，尚无用户美术签收。本轮只做小样选型，没有批量重建、按2D改外形或替换正式应用。

[打开离线预览](原版成品-离线预览.html)。默认展示哈士奇；可切换模型、旋转、查看正背侧、播放全部原生动作、暂停/拖动进度及下载GLB。保留完整目录后可直接双击HTML离线打开。也可运行 `python3 -m http.server 49334 --bind 127.0.0.1`。

## 本版模型

|模型|来源|原生动画|许可|
|---|---|---:|---|
|便装男性、工装男性|Quaternius完整角色，固定版本开源项目文件|各24项|CC0|
|便装女性、工装女性|Quaternius官方Drive完整角色|各24项|CC0|
|哈士奇、柴犬|Quaternius Ultimate Animated Animal Pack原版|各12项|CC0|
|马|同上|13项|CC0|

动物仍是低多边形风格，比例比Cube Pets接近真实四足动物，并非写实毛发模型。未缩头、拉腿、换色或重绑骨架。猫候选在实际查看后因面部显示效果不佳排除；本版不声称猫、兔、鸟等全部物种已经选好。

动物作者与许可：[Quaternius官方资源页](https://quaternius.com/packs/ultimateanimatedanimals.html)。使用本地已冻结且摘要核对一致的完整原文件，来自[agentkaerf/FreeModels](https://github.com/agentkaerf/FreeModels)，固定提交 `db3df04d1e4714298a09510b26fb6de6645138a2`。源URL、字节数、SHA-256见 `vendor/animals/sources.json`，原许可随包保留。

人物来源：[男性包](https://quaternius.com/packs/ultimatemodularcharacters.html)、[女性包](https://quaternius.com/packs/ultimatemodularwomen.html)。男角色由开源项目 `euuuuuuan/fatal-funnel-public` 固定提交 `29a6bdfd01ad175c389cbd0bac80c30f926ff96b` 保存；女性来自作者官方Drive目录。原件、许可和下载来源分别在 `vendor/quaternius-men/`、`vendor/quaternius-women/`。人物便携GLB与V1字节一致。

## 原件与预览

`vendor/`只保留完整原件及许可；`assets/`为离线便携GLB。`src/prepare.py`只做资源内嵌和容器封装，逐项断言节点、网格、材质、骨架、动画、访问器定义不变，核对原缓冲字节不变。各摘要见 `manifest.json`、`qa/source-hashes.json`。页面统一光照，自动取景并将脚底放到地面，不改变比例；不同资源独立取景，并非同尺度比较。

本轮检查见 `qa/browser-validation.json`：逐个实际运行所有原生动画，核对动作变化及有效数值、播放进度、骨架开关、下载摘要、390px布局和断网file打开。正背侧截图位于 `qa/`。技术通过只说明预览可用，外观仍需用户判断。

原动画数量不等于生活动作覆盖：犬马有原生走路、奔跑、进食和待机等，也包含攻击/死亡动作；人物未自带完整坐卧生活动作。本版保留并展示原动作，不用重命名冒充缺失动作。后续接入继续保留名字、人设、记忆、关系和API绑定。

## 重新生成

复用现有 `../river-park-3d-v1/node_modules/` 的Three.js与esbuild构建 `src/viewer.js`，然后运行 `python3 src/prepare.py`。浏览器验证使用 `src/verify.cjs`（Playwright与Chrome）。该目录没有安装新依赖或生成新模型。
