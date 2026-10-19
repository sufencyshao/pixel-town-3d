# 居民 C 自然比例：冻结底模与发型模块

2026-10-18。仅本目录为本次基础资产工作区；未修改阿澈 V1.1、三比例样例、原 2D、正式应用、API、存档或项目根索引。

## 已冻结的男女底模

- `male-seed.blend` / `female-seed.blend`：原生 T 姿势，独立成年男女拓扑，均包含完整连续 Body、Eyes、Eyebrows。源默认内衣贴图已替换为一项 `Skin_Neutral`，没有以材质分区假充衣服，也没有预先裁切身体。没有默认头发、动画或源 Icosphere 显示辅助网格。
- 对应 GLB 已重新导入。`seed-manifest.json` 与两份独立 JSON 记录三轴范围、完整 65 骨名/父子/头尾/局部 rest 矩阵、所有对象世界矩阵、骨架和网格名称、身体分区坐标、来源与 SHA-256。
- 骨架 `Resident_Base_Rig`；网格 `Body` / `Eyes` / `Eyebrows`；米制、Z 向上、正面 -Y；对象世界矩阵均为单位阵，scale=1，顶点在同一骨架局部坐标。只将脚底整体平移到 Z=0；男高 1.8195869 m，女高 1.7750509 m。个体身高、头身、肩胸腰胯及四肢重塑由总构建器决定。
- 65 骨名按阿澈 V1.1 实际文件逐项比对一致。两性 rest 位置和部分骨旋转有真实差别，不能直接把男性 rest 矩阵盖到女性骨架。共享动作应保留各自 rest 适配。

`qa/seed-validation.json`：48 项通过，包括原生重开、GLB 回读、完整权重、UV、纹理打包、骨名、肩肘/髋膝连续、原拓扑及冻结字节摘要。原网格的 UV 分离顶点保留；只用于检查的位置焊接结果为男女各一个连续分量、0 开放边，表明颈部/脸/躯干并非分离拼接。`qa/` 下有男女正、侧和面部原生渲染。

## 发型构建接口

```python
from hair_builder import create_hair, create_facial_hair
objects = create_hair(rig, features, head_bounds, material_factory, bind_fn)
# 可选；上层如果已有胡须逻辑，不必重复调用。
objects += create_facial_hair(rig, features, head_bounds, material_factory, bind_fn)
```

- `head_bounds = {"min": [x,y,z], "max": [x,y,z]}`，描述未做个体形变的完整种子头部（含耳）。本目录 QA 按 Body 中 `z >= rig.data.bones['Head'].head_local.z - .035` 的顶点统计。
- 在 `create_hair` 调用时，保留该 rig 下名称含 Body 或 Skin 的实际头皮网格。闭合发帽从其真实成熟头骨表面提取并加厚，避免椭球帽在额头/头顶穿出皮肤。没有 Body 时才用参数表面备用。
- `features` 使用身份 JSON 中的 `hairStyle`、`hairColor`、`hairDetail`、`hairTipColor`、`hairtieColor`、`bowColor`、`accessories`、`distinctive`。支持 short、sidepart、bob、long、ponytail、twinbraid、singlebraid、bun、twin-buns、spiky、swept、curly，并区分高/低/小/半扎/卷侧尾、短密卷/蓬松卷、单侧/正后辫和长波浪。
- `material_factory(name, hex_or_tuple, roughness=.8)`；HEX 应按 sRGB 转为 Blender 节点的线性 RGB。tuple 使用线性值。工厂应确保原理化 BSDF 连接现有活动材质输出，不能只创建未连接节点。
- `bind_fn(obj, 'Head')` 由调用者完成父级/全部 Head 权重和 Armature modifier。本模块返回真正 Mesh 对象，未残留 Curve。调用之后由总构建器统一做头身/骨架的个体形变。
- 使用成熟 CC0 Hair_Long、Hair_Buns、Hair_SimpleParted、Hair_Buzzed / Female 和 Hair_Beard 原网格；新增真实头皮闭合壳、柔和刘海/侧帘、三股编辫、绑带、马尾、低髻、短卷/长卷体积。白紫发梢是连续网格上的材质区域。
- 不生成帽子、冠饰、角、眼镜、串珠等身份配饰；上层另做。长发和辫尾当前刚性绑定 Head，未实现发骨动态、物理或动作避肩碰撞。

`qa/hair-validation.json` 对 45 份实际身份 features 逐个构建，检查全 Mesh、全部 Head 权重及每顶头皮帽 0 边界/0 非流形。`hair-contact-1.png`～`3.png` 为发型联系表，12/13/16/17/19/20/33/36/39 有背面补充。这里使用冻结种子的相同中性肤色和脸，仅验收发型构建，不等于总任务已完成逐人的脸型、衣物、动作或视觉签收。

## 现成衣物候选

`clothing-library.json` 提取固定源 Casual / Worker 的 Body、Legs、Feet 及核对用 Head。保留成熟三角网格、逐面材质、源权重、rest 世界坐标与三轴范围。它们属于旧 Modular Men 骨架，尚未适配本版 65 骨架或某位居民；只能按解剖点拟合并重新权重，不能直接套旧源动作。Casual/Worker 来源 SHA 与 CC0 许可证在 `reference/`；原文件位于阿澈 V1 的 `reference/`，只读使用。

## 来源、许可与可重建边界

[Quaternius 官方页面](https://quaternius.com/packs/universalbasecharacters.html) 与[作者 Itch 页面](https://quaternius.itch.io/universal-base-characters)在本轮重新核对，明确为 CC0、三类男女共六种完整包基础、兼容 Universal Animation Library。**本次固定 GitHub Standard 树实际只有 Superhero 男/女，不包含 Regular 或 Teen；没有把两种伪称为六种，也未下载付费 Source。**

原模型/六种实际提供发型取自 [NafisRayan 固定提交 5821923](https://github.com/NafisRayan/Animate-Rigged-Humanoid-No-Blender/tree/5821923af517ac5fdc82505faa92a0d575fc1b1a)，只复用其中归属 Quaternius 的模型与许可。`reference/source-manifest.json` 逐文件记录原路径、固定 URL、字节与 SHA；保留 `License_Base_Characters.txt` 及 GitHub 完整树。导出器图片 URI 的 `_png` 别名从同一个固定版本对应真实 PNG 解析，源 glTF 内容不变。

成品衣物只读源取自 [fatal-funnel-public 固定提交 29a6bdf](https://github.com/euuuuuuan/fatal-funnel-public/tree/29a6bdfd01ad175c389cbd0bac80c30f926ff96b/packages/renderer/assets/models/quaternius-men)，仅 CC0 Quaternius 素材，不复用游戏代码。

重建脚本按 `src/fetch_sources.py` → `src/build_seeds.py` → `src/extract_hair.py`；QA 为 `src/verify_seeds.py` / `src/verify_hair.py`；衣物提取为 `src/extract_clothes.py`。使用 Blender 5.2.2 LTS 原生运行。已冻结底模的 SHA 仍以 manifest 为准；发型模块独立，不覆盖底模。
