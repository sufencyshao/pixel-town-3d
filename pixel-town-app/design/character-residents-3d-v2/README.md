# 小镇45位人物 · C自然比例 V2

2026-10-18，延续已选的C方向。40位原居民与5位固定伙伴逐人制作；自定义主角与20自然动物不计入45身份。

- [人物制作室](小镇人物-C方向-离线预览.html)：原2D对照，45身份筛选，30动作、进度/暂停、表情、骨骼、道具、6个近看视角及最多4人的同尺度体型比较。
- [放入小镇查看](town/小镇人物与动物-离线预览.html)：人物按职业分区试放到公共步道，保留动物V6照看、四季和天气；通过顶部的人物选择框靠近观察。走路为原地动作试演，人物尚无自主工作/入住。
- `assets/<人物ID>/character.blend`：可编辑单人物工程，纹理已打包。
- `assets/<人物ID>/character.glb`：65骨骼、30动作与Blink/Smile/Talk目标。
- `assets/<人物ID>/runtime.glb`：同一人物的轻量无动作模型，不作为全动作下载。
- `town/Town-with-residents.blend`：整镇、20动物与45人物的初始摆放和完整动作库。
- `identity/identities.json`：原图辨识点与逐人新设计身高、肩腰胯、腿长、头身参数。数值是设计输入，不是从像素图推算出的真人测量。
- `qa/` 与[验收报告](验收报告.md)：实际导出检查、Blender重开、浏览器操作与逐人六视图证据。

## 使用

保留整个文件夹后双击人物制作室HTML，可通过file协议断网切换人物；模型按需载入同目录的`assets/<ID>/preview.js`，避免把45个模型一次塞进页面。GLB与Blender下载为相对文件链接，移动或解压后仍可用。整镇HTML也可直接打开，但体积较大，首次载入需要更多时间。

可在本目录运行`python3 -m http.server 49332 --bind 127.0.0.1`后访问本地预览。制作室正常操作包括搜索、类别筛选、旋转/缩放、正背侧/面部/鞋子、30动作、暂停/拖动进度、表情、骨骼与道具开关。并排比较保持原始米制尺度，不将身高归一化；卧姿自动拉开间距。

## 来源与身份

男女基础为Quaternius Universal Base Characters Standard的Superhero Male/Female（CC0）；两者具有不同实际拓扑，不声称使用未取得的Regular/Teen网格。固定来源、提交、许可证与审核在`foundation/seed-manifest.json`和该目录来源说明中。

发型使用已冻结的Quaternius发型网格，并补连续头皮、发辫、发髻、卷发与逐人细节；鞋面/鞋底使用此前已冻结的Quaternius Modular Men Casual网格，修改颜色、鞋型、靴筒、鞋带/搭带。服装为逐人重建的独立蒙皮衣物，帽饰、眼镜、职业配件、冠饰、角和尾巴依原图补建。阿澈原2D白T与已选C黑T有差异，本版沿用已确认C黑T并在身份表如实记录。

动作延续原C V1.1的19项与动物V6的3项照看片段，补8项吃饭、喝水、阅读、手机、伸展、躺下、侧躺与起身，共30项。原地步行、作业、舞蹈、游泳等是动画示意；工具挂点与生活道具存在不等于职业产出或所有家具接触IK。完整动作来源、时间、播放方式与挂点见[motion/README](motion/README.md)。

整镇副本沿用V6模型/代码及20动物来源；原动物许可与署名已随`town/animal-library/`保留。人物和动物的自主决策边界保持分开。

## 重建与验证

`src/build_residents.py`在Blender5.2.2LTS后台生成45位；输入为本地冻结的底模、头发/鞋网格、身份和动作库。随后运行`src/finish_shoulders.py`补齐上肩覆盖并重新导出，`src/package_preview.py`组装制作室。先用esbuild将`src/studio.js`打包为`viewer.bundle.js`，依赖three0.180.0、esbuild0.25.9。

`motion/validate_batch_glb.py`独立解析实际GLB二进制；`src/validate_native.py`逐工程重开和GLB重导入；`src/verify_browser.cjs`通过Chrome检查全员动作及浏览器操作并生成六视图；`src/contact_sheets.py`生成逐人审阅表。完整检验命令和结果见验收报告。

`src/setup_town.py`冻结V6副本与人物步道落点；复制`src/resident-world.js`至`town/src/`后打包`town/src/viewer.js`，`src/package_town.py`生成整镇HTML，`src/build_town_native.py`创建含动物与人物的原生工程。首次从原项目重建需保留相邻V6、C V1.1和原角色库；已生成的离线预览/模型可独立使用。

## 边界

这是独立3D资产与交互预览；未替换正式Electron应用、API、密钥、存档或原2D人物。全员衣物与头发为骨骼蒙皮/刚性附件，没有衣物和头发物理、全身接触IK、全场连续碰撞或室内楼层寻路。夸张动作、长发/裙装与道具接触仍可继续精修；用户最终视觉签收与制作侧验证分开记录。整镇既有天气/动物生活由HTML运行，Blender只保存初始摆放与动作，不把脚本行为烘焙成长期生活。
