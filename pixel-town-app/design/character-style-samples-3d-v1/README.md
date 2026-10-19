# 阿澈 · 三种 3D 人物比例样例 V1

本轮按「先把每一种类型制作一个简单的例子看看我再决定」制作，供选择人物比例与视觉方向。双击 `人物三种比例-离线预览.html` 即可离线查看，无需安装依赖。

| 样例 | 方向 | 已做内容 |
|---|---|---|
| A · 大头 Q 版 | 大头、短躯干和短腿，偏向原2D的亲切感 | 自建圆脸、大眼睛、笑容、黑色短发，保留黑上衣与蓝裤 |
| B · 修长卡通 | 保留大眼睛，躯干和四肢更长 | 与A使用共同的简化脸部设计，突出头身比例差别 |
| C · 偏写实比例 | 更接近成年人头身比例 | 使用风格化成年底模，换成黑短发、黑上衣与蓝裤；未制作照片级皮肤 |

三者均参考原居民阿澈 `01_hero_male`，保留同一套标志配色和1.65 m的静态展示高度，便于比较。A/B为按比例方向重建的简单3D脸，C为成人底模；都还不是阿澈的最终身份复刻。衣物当前采用人体拓扑上的简化材质分区，没有完成独立换装衣片、布料、拉链或精细缝线。

## 可以查看什么

- 三个人物同步切换「站立 / 走路 / 挥手」，暂停、0.5/1/1.5倍速及拖动进度。
- 正面、侧前方、侧面、背面四个统一视角；每张卡片也可独立拖动旋转、滚轮缩放。
- 「查看骨骼」显示骨骼结构。每个样例使用65骨骼人形绑定，包括肩肘腕、髋膝踝和手指链；骨骼总数包含根骨及末端骨，并非65个独立人体关节。
- 每例可下载内嵌GLB，或打开同目录的Blender工程。GLB中包含三项真实骨骼动画，不依赖网页重新生成动作。
- 站立和走路从Quaternius UAL1适配；挥手为本轮烘焙的上臂抬起、肘部弯曲、张手与手腕摆动动作。

## 交付文件

- `人物三种比例-离线预览.html`：三例对比，模型、参考图与预览程序全部内嵌。
- `assets/A-chibi/`、`B-cartoon/`、`C-natural/`：各含 `Ache.blend` 和 `Ache.glb`。
- `reference/阿澈-2D原型.png`、`2d-source.json`：原2D参考的只读副本与摘要。
- `reference/source-manifest.json`：GitHub来源、固定提交、下载文件与SHA-256。
- `vendor/quaternius/`：CC0原始模型/头发/UAL1与原许可证，供重建使用。
- `src/build_samples.py`：原骨骼/网格比例改造、脸部生成、材质与动画烘焙。
- `src/viewer.js`、`template.html`、`src/package_preview.py`：预览与打包。
- `src/verify_models.py`、`qa/`：模型回读、浏览器验收与截图。
- `样例范围与来源.md`：GitHub初筛、选择基础与本轮边界。

## 验收

2026-10-17，本机Blender 5.2.2 LTS和Chrome headless / Playwright验证。Browser plugin not available，使用本机已有Playwright，没有安装新浏览器。

| 检查 | 结果 |
|---|---|
| Blender保存重开与GLB重导入 | 57项通过，`qa/model-validation.json`；每例65骨骼、Idle/Walk/Wave三动作，多帧姿态有限，GLB资产网格具有皮肤绑定 |
| 可移植工程 | Blender工程已打包所用纹理；GLB纹理内嵌，重开/重导入通过 |
| 页面与交互 | 31项通过，`qa/browser-validation.json`；标题、2D参考、三画布、动作、关节运动、暂停、进度、视角、独立旋转、骨骼开关与倍速 |
| 实际关节运动 | 三例走路时脚骨有可测位移；挥手时手腕高于肩，肘部弯曲，手部横向离开头部。对应数值在浏览器验收JSON |
| 下载 | 三份实际下载GLB与对应文件SHA-256一致 |
| 显示 | 1440×1000桌面、390×844手机尺寸；无横向溢出，手机动作控制可用 |
| 控制台与着色器 | 最终运行无应用警告/错误，着色器可运行 |
| 离线 | file页面断网打开并切换挥手成功，无HTTP请求 |
| 原始参考 | 原阿澈2D PNG摘要未改变；只在新样例目录制作，未替换现有游戏和人物存档 |

视觉证据：`qa/comparison.png`、`walking.png`、`waving.png`、`front.png`、`angle.png`、`side.png`、`back.png`、`bones.png`、`mobile-top.png`、`mobile-C.png`。浏览器脚本在 `/tmp/character-samples-qa/`。

模型验证脚本会按GLB实际资产节点检查绑定；Blender导入材质时产生的临时Icosphere不是GLB资产节点，不计作人物模型。导出提示原顶点颜色未被新材质使用，本版使用明确的材质配色，不依赖该颜色通道。

## 重建

现成HTML无需运行以下命令。修改源模型时，在本目录使用Blender 5.2.2 LTS：

```sh
blender --background --python src/build_samples.py
blender --background --python src/verify_models.py
npm install
npm run preview:build
```

Three.js 0.180.0，esbuild 0.25.9。第三方许可见 `THIRD_PARTY_LICENSES.txt` 与 `vendor/quaternius/License_*.txt`。

本轮仅用于比例选择，等待用户反馈；未完成40居民、5伙伴、自然动物或捏脸系统的3D转换，未制作完整生活/工作/侧躺/表情动作。尚无脚底IK、全身碰撞、衣物物理、自动口型、眨眼或地形适配；小幅穿插与动作自然度需在选定方向后继续逐项精修。原2D人物、正式应用、API、存档及整镇V5保持原样；真实手机性能、Safari及长期运行未验收。
