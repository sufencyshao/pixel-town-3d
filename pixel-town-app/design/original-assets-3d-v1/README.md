# 原版成品模型 · 8个代表预览

2026-10-18。响应用户要求，直接复用现成完整模型，不按原2D形象改脸、衣服、发型或身材。本轮只做少量实际成品预览，供判断原版效果；未将它们批量分配给45位居民，也未替换正式应用。

[打开离线预览](原版成品-离线预览.html)：可旋转/缩放，查看正背侧，播放原生动作，暂停和拖动进度，下载便携GLB。保留整个文件夹后可直接双击HTML离线打开，无需安装依赖。也可在本目录运行`python3 -m http.server 49333 --bind 127.0.0.1`。

## 实际取得的成品

|模型|来源|原生动画|许可|
|---|---|---:|---|
|便装男性、工装男性|Quaternius；开源项目保存的完整GLB|各24项|CC0|
|便装女性、工装女性|Quaternius作者官方Drive下载目录|各24项|CC0|
|猫、狗、兔、鹦鹉|Kenney Cube Pets 2.0官方完整包|各8项|CC0|

人物：[男性包](https://quaternius.com/packs/ultimatemodularcharacters.html)、[女性包](https://quaternius.com/packs/ultimatemodularwomen.html)。男性原件来自[euuuuuuan/fatal-funnel-public](https://github.com/euuuuuuan/fatal-funnel-public)，固定提交`29a6bdfd01ad175c389cbd0bac80c30f926ff96b`；源URL和摘要在`vendor/quaternius-men/source.json`。完整模型此前已冻结到本项目，此轮校验原摘要后直接取用，未采用此前自造衣物或底模。

女性使用官网链接的[官方Drive目录](https://drive.google.com/drive/folders/1720N9IGyQHXYvtvZJzazhxtTTlz-y2Vf)中`Individual Characters/glTF/Casual.gltf`和`Worker.gltf`。原件、原许可与下载URL/SHA-256在`vendor/quaternius-women/`；原许可文件标题沿用Males，但其CC0文本及女性官网CC0标注一致，原文件未改写。

动物：[Kenney Cube Pets](https://kenney.nl/assets/cube-pets)。官网链接的ZIP文件名仍带1.0，包内`License.txt`与内容标明2.0；本次按实际包内版本记录。完整ZIP、全部原件及许可在`vendor/kenney_cube-pets_1.0.zip`与`vendor/kenney-cube-pets/`，来源记录在`vendor/kenney-source.json`。本页展示4只代表，不声称全包动物都适合现有小镇物种。

## 保留了什么

原始文件只读留在`vendor/`；`assets/`为便携GLB。打包时仅把外部图片转成内嵌资源、把已有glTF缓冲装进GLB容器，便于离线使用；没有重画贴图、修改颜色/材质参数、改变顶点/拓扑、重绑骨骼或制作替代动画。`src/prepare.py`逐项断言网格、材质、节点、骨架、动画和访问器定义保持一致，并核对原缓冲字节不变。摘要与源定义记录见`manifest.json`及`qa/source-hashes.json`。

预览中自动取景并将脚底摆到地面，不改变模型比例；不同资源的原始单位可能不同，因此此页并非同尺度体型比较。画面采用统一预览光照，未声称与作者宣传图逐像素相同。

人物使用原生蒙皮骨骼；Cube Pets使用原生部件动画，没有为了统一规范强行添加骨架。人体24项动画包含战斗动作，不等于24项生活动作；此页只列站立、走跑、挥手/互动等相关项。原人物没有现成坐卧、吃饭等完整生活动作，后续应找匹配的成熟动作资源，不用重命名冒充已有动作。

## 实际检查

8模型已实际载入Chrome；逐个运行所有原生动画，检查实际节点变换有限且动作变化存在。暂停/进度、人物骨骼显示、下载文件摘要、正背侧查看、390px布局与file断网打开合计25项检查通过，控制台错误0。8组正/背/侧截图在`qa/`，结果见[浏览器检查](qa/browser-validation.json)。未做本轮无必要的Blender重导出、批量人物重建或正式存档/API测试。

## 后续

先以原版实际外观决定采用哪些资源，再做必要的角色身份映射、原始单位适配、成熟动画映射和小镇接入。人物名字、人设、记忆、关系、API绑定保留；不为贴合原2D外形再次重做成品。VRoid等其他候选仍在独立来源清单中，未混充为本轮已取得模型。
