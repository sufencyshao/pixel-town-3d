# E 区 · 小镇客厅 V1

2026-10-14。延续小镇暖色石铺地、木作、鼠尾草绿和低多边形植物风格。中央大树、分段环座与四向步道构成日常相遇的中心，西侧市集和东侧水景、廊架提供两种不同的活动空间。当前为独立场景设计，待用户视觉反馈。

## 查看与编辑

- `小镇客厅-离线预览.html`：模型及 Three.js 内嵌，可直接双击离线查看。七种视角：周末全景、日常广场、总平面、大树环座、周末市集、水景廊架、公告便民区。
- `E-town-square.blend`：原生 Blender 工程，七个场景保留各自相机和集合显隐。直接打开即可编辑。
- `E-town-square.glb`：用于 Blender、游戏编辑器或其他支持 glTF 的软件；网格及材质均在文件内，无外部贴图依赖。
- `布局示意.svg` / `布局示意.png`：中文标注平面图。
- `overview.png`、`daily.png`、`plan.png`、`tree-seating.png`、`market.png`、`water-pergola.png`、`community.png`：Blender 实际渲染。

预览支持单独切换市集、中央树冠和摊位/廊架顶棚，旋转缩放、自动旋转、GLB下载和截图。GLB 下载始终提供完整资产；日常/市集按钮只控制展示布置，不删除模型。HTML 的 Blender 和平面图链接需保留同目录文件。

## 功能布局

| 位置 | 内容与尺度 |
| --- | --- |
| 中央 | 直径36 m大树广场，约14 m高的低多边形树冠；半径3.8 m树池，四段环座，环座外缘半径5.1 m |
| 西侧 | 六个可移动摊位：鲜蔬、面包、花束、陶作、旧书、木作；两列布置，主通道从中间通过 |
| 东北侧 | 半径约4.34 m水面，水深约0.25 m的浅水景，石质出水台和两张面向水池的长椅 |
| 东南侧 | 14 × 8 m阅读廊架，木格栅、少量攀援植物、两张长椅与两张圆桌 |
| 北侧 | 公告栏、换书柜、高低饮水点、宠物水碗、分类收集箱和休息座椅 |
| 场地边缘 | 错落乔木、混合花灌木、照明与四向指示牌 |

总地块85 × 55 m，与原E区340 × 220图纸单位一致；原大树广场中心(620,550)和半径72图纸单位保留，即局部(0,-2.5)和18 m。地块中心为Blender原点，北为+Y、Z向上；原图换算 `x=(图纸X-620)/4`、`y=(540-图纸Y)/4`。GLB 为Y向上、北为-Z。

四向入口宽4.5 m，分别朝公共服务区、日常商业街、手作区和河岸公园。西口与D区东口在原总图中的Y坐标一致，区块之间的道路缝隙仍由整镇装配衔接。

石铺地使用扫描线合并圆形和矩形轮廓，树池、水池位置留真实空洞，避免多块平面在交叉处重叠。水盆底面高于原草坪，覆住池内草地；水面、池体和静态水线独立分组。廊架地台比主铺装高约0.15 m，后续人物移动接入时统一处理台阶或坡道。

## 模型组织

- `Landmark_Trunk`、`Landmark_Canopy`、`Tree_Base`、`Ring_Seats`：主树与环座。
- `Market_Fixtures`、`Market_Canopies`、`Event_Decor`：市集和旗帜。
- `Water_Basin`、`Water_Surface`：浅水景。
- `Pergola_Base`、`Pergola_Frame`、`Pergola_Roof`、`Pergola_Furniture`：廊架。
- `Community`、`Amenities`、`Seating`、`Wayfinding`、`Landscape`、`Paving`、`Paving_Detail`、`Ground`：其他场景资产。

## 重建

```sh
blender --background --python src/build_models.py
blender --background --python src/verify_models.py
npm ci
npm run preview:build
python3 src/make_plan.py
```

Blender 5.2.2 LTS；Three.js 0.180.0；esbuild 0.25.9。依赖锁文件、许可和冻结的建模基础函数随包提供。源脚本不依赖其他区块的模型；验证优先对照项目总图，独立解压时读取`reference/masterplan-E.json`。构建文字使用macOS的`STHeiti Medium.ttc`，其他平台重建时需更换字体路径，成品中文字已转为网格。重建会覆盖生成文件；人工修改请先另存。

## 边界

日常/市集切换仅是设计布置预览。阿澈、小满、夏芽的活动协助角色沿用原规划，未绑定行为。当前未接入人物坐下聊天、交易、换书、饮水、节庆调度、流水动画、碰撞、寻路或正式存档。抽样通行检查不等于游戏导航、无障碍设计或工程审查。
