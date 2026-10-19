# 写实动物成品筛选 · 2026-10-18

最新要求：**不要卡通风格**。优先真实解剖比例、自然四足结构和毛皮/羽毛/甲壳贴图，直接复用作者成品。此前Quaternius、Cube Pets、Gobkit柯基及明显多边形猫不再作为当前采用方案；允许换犬种不代表接受反复套用两种模型。

[当前实际写实预览](写实动物-原版预览.html)：CDmir / TinyWorlds为Kelgar游戏制作的原版兔子，CC0。原件已取得并保留在 `vendor/oga/rabbit.blend`，37骨骼。浏览器GLB有7段动态剪辑和2个静态姿势：观察、奔跑、跳跃、坐姿、死亡等；没有把这些称为完整生活动作。

来源：[Rabbit，作者发布页](https://opengameart.org/content/rabbit-0)。原文件、下载URL和摘要见 `vendor/oga/downloads.json`。仅把旧Blender工程转换为GLB，将原打包的毛皮/法线/透明贴图接到PBR材质，保留原UV、网格坐标、骨架和原动作；不重塑、重绑或自造动作。转换器会对原约束动画采样以便glTF播放；导出器使用每顶点最多4骨权重，这不是原生Blender渲染的逐像素复刻。源文件及源网格坐标摘要未变，见 `qa/conversion.json`。

## 另外找到的写实方向（未冒充已下载验证）

|成品|作者与来源|当前核对程度|
|---|---|---|
|Rabbit Demo|[WildMesh 3D](https://sketchfab.com/3d-models/rabbit-demo-free-download-54507527ccec44ca9620d4b82da73265)|作者标注写实、骨架、动画与CC Attribution；免费Demo与完整30动作版本需要区分，未取得Demo文件，不声称免费包有30动作。|
|Animated Cat|[AnimalMesh 3D](https://sketchfab.com/3d-models/animated-cat-3d-animal-model-c86d90e98e8e467e92c908206e1ee667)|作者标注写实、PBR、骨架和动画；页面许可标签与“仅个人使用”说明不完全一致，原文件和具体使用条款尚待取得核对，不列为已获完整许可的交付。|
|tortoise, rigged+animated|[Christian / Enzi1984](https://sketchfab.com/3d-models/tortoise-riggedanimated-f911589e275e4c60963d52b31bc0b061)|维也纳自然史博物馆巨龟扫描的带骨架动画衍生版，CC BY-NC；约10万三角面。作者自述步行动画和权重仍可改善。尚未下载，不声称满足小镇全部动作和性能。|

以上是具体作者的成品资源，不以“网上找不到”作为继续自建动物的理由。未下载/未满足当前风格的条目不批量接入。

## 本次排除与历史试件

`vendor/gobkit/Corgi.glb`实际查看后大头、短腿明显，排除。`vendor/madtroll-cat/`是另一位作者的完整静态猫，CC BY 3.0，有署名原件；但没有骨架/动画，且外观仍是明显多边形风格，排除当前方案。Fabio Gonzalez的CC0小鸟虽有19骨和原动画，实际风格与细节不满足新的写实要求，退出当前预览。这些文件仅保留来源与筛选证据。

获取静态猫来源时建立的临时只读浅克隆已清理；固定提交、猫原件和署名文件仍在 `vendor/madtroll-cat/`，未执行该项目代码。

## 文件与范围

`assets/rabbit.glb`为可下载预览转换件；原生 `.blend` 保持完整。`src/export_originals.py`与`src/package_preview.py`用于格式转换和打包，Three.js/esbuild复用现有依赖。实际预览和动作检查在 `qa/`，不进行本轮无必要的整镇重新建模或批量接入。正式应用、API、存档和原2D未纳入修改。

本版当前8项实际浏览器检查通过：仅展示写实兔、7段原动画/2姿势载入与有效变换、原生奔跑进度、骨架、下载摘要、390px布局、断网file打开和零应用错误。详见 `qa/browser-validation.json`，正背侧截图在 `qa/realistic-rabbit-*.png`。
