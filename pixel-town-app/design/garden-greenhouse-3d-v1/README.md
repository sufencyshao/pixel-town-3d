# G 区 · 田园与温室 V1

2026-10-13。继续「设计小镇3D整体平面图」聊天中未完成的 G 区制作。温暖自然的低多边形风格，独立静态场景资产，待用户视觉审阅。

## 查看与编辑

- `田园与温室-离线预览.html`：内嵌模型和 Three.js，可直接打开，六种视角、旋转缩放、屋顶开关、GLB下载与保存画面。Blender下载和SVG链接需保留同目录文件。
- `G-garden-greenhouse.blend`：原生工程，含整体、总平面、温室内部、工具屋内部和田园五个场景。
- `G-garden-greenhouse.glb`：包含命名集合的可交换模型；无外部贴图、字体依赖。
- `overview.png`、`plan.png`、`greenhouse-interior.png`、`tool-interior.png`、`fields-orchard.png`：Blender 实际渲染。
- `布局示意.svg`：带中文功能标注的矢量平面示意。
- `manifest.json`、`validation.json`、`验收报告.md`：模型参数与当前检查证据。

## 落位与尺度

与 `town-3d-masterplan-v1/plan-data.json` 的 G 区一致，300 × 220 图纸单位按4单位/米换算为75 × 55 m。地块中心为Blender原点，北为+Y，Z向上。总图坐标转换：`x=(planX-270)/4`，`y=(830-planY)/4`。GLB导出后Y向上、北为-Z。

G01温室沿用总图中心(-19.75,11.5)，25.5 × 13 m。G02工具屋地块沿用中心(22.375,-15)，18.25 × 12 m；其中南侧2 m为带屋檐工作廊，封闭主体深约10 m。整体高度约6.3 m温室、5.1 m工具屋。

西南四块11 × 7.5 m轮作田分别示意叶菜、茄果、根茎、香草。田间横纵步道约2.5 m；北侧温室有六组育苗台、两块低香草床，东侧2.4 m门洞连主步道。东侧九株果树，外围有散步路线。中部廊架提供小桌、长椅；工具屋含工具挂放、两组工作台、分拣台、储物架，屋后配置洗手池和雨水桶，西南设三格堆肥。

北接D区，东接H区，南侧4 m后勤路通工具屋。步道交叉部分分割为互不重叠的37个铺装块，避免共面黑块；标牌放在通行范围外。田伯、禾青、阿禾是原方案的工作角色，花音、林苔可来温室取材；尚未绑定人物行为。

## 组织与重建

集合按 Ground / Paths / Fields / Orchard / Greenhouse_* / Tool_* / Utilities / Rest / Borders / Wayfinding 组织。室内视角通过隐藏屋顶及工具屋南立面实现。

```sh
blender --background --python src/build_models.py
blender --background --python src/verify_models.py
npm ci
npm run preview:build
python3 src/make_plan.py
```

构建使用Blender 5.2.2 LTS、Three.js 0.180.0和esbuild 0.25.9。`src/model_helpers.py`为本轮冻结的既有住宅建模基础函数，G区可独立重建。中文网格标牌构建时使用macOS `STHeiti Medium.ttc`，其他平台重建请更换字体路径。重建会覆盖生成资产，人工编辑工程应先另存。

本轮没有接入正式应用、存档、角色动作、碰撞、寻路、作物生长、采收或季节系统；窗、作物、设备为静态示意，尺寸不是工程施工依据。旧总图及其他建筑资产保留。
