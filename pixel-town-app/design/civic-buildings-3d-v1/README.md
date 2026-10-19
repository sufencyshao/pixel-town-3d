# 诊所与图书馆 · 3D 模型 V1

2026-10-12。延续温暖自然的小镇方向，提供可编辑的 Blender 工程、通用 GLB 与离线交互预览。当前为设计审阅版，等待用户外观及布局反馈。

## 查看与编辑

- 双击 `诊所与图书馆-离线预览.html`，在浏览器中切换建筑、外观、室内和俯视。拖动旋转，滚轮缩放；可隐藏屋顶、下载 GLB 和保存当前画面。预览本身无需联网。
- 在 Blender 中直接打开 `clinic/B03-clinic.blend` 或 `library/B02-library.blend`。顶部场景下拉菜单包含 `01 Exterior`（外观）、`02 Interior`（室内剖切）、`03 Plan`（俯视）。
- 需要合并到其他场景时，导入对应 `.glb`；中文标牌已转为网格，模型不依赖外部字体或贴图。
- HTML 中的 Blender 下载链接使用相对路径，解压后请保留 `clinic/` 与 `library/` 文件夹。

## 空间设计

| 建筑 | 主体尺寸 | 主要空间 | 预留职业关联 |
| --- | --- | --- | --- |
| B03 溪畔诊所 | 16 × 11 m | 接待、6座候诊、2间诊室、2床观察区、储物、洗手点、卫生间、门廊 | 许衡、余笙、苏晴 |
| B02 溪畔图书馆 | 19 × 12 m | 借还书台、6组双面书架、12座共享阅览、3座靠窗阅读、儿童角、新书展示、门廊长椅 | 知秋、书衡 |

诊所采用米白墙、鼠尾草绿屋顶及隐私窗；图书馆采用陶土屋顶、木地板及明亮阅读空间。两栋均为单层，屋顶与临镜头外墙可独立隐藏。图书馆15座不计工作人员座椅、儿童坐垫及门廊长椅。

总图预留地块分别为19.5 × 15.5 m和23.75 × 15.5 m。模型总体包围盒（含屋檐、门廊）分别约17.40 × 14.10 × 5.60 m、20.40 × 15.11 × 6.70 m；正式落位还需审阅街道、绿化与地块边界。

## 文件和结构

每栋目录内：`.blend`为原生工程；`.glb`为导出资产；`exterior.png`、`interior.png`、`plan.png`为真实Blender渲染；`web-preview.png`为浏览器实际画面；`manifest.json`记录单位、人物关联、建议交互点及模型统计。

Blender集合：`Structure`主体、`Roof`屋顶、`FrontFacade`正立面、`EastFacade`东侧立面、`Interior`室内、`Landscape`景观、`Studio`摄影灯光。GLB不导出Studio。单位为米，Blender Z轴向上、正面朝-Y；GLB Y轴向上、正面朝+Z。

## 重建

`src/build_models.py`用Blender Python创建几何、材质、场景、GLB和渲染。使用Blender 5.2.2 LTS验证。重建会覆盖本目录生成文件；先另存手工修改后的工程。

```sh
blender --background --python src/build_models.py
blender --background --python src/verify_models.py
npm install
npm run preview:build
```

生成脚本使用macOS的`/System/Library/Fonts/STHeiti Medium.ttc`制作中文标牌；其他系统重建时需替换为可用的中文字体路径。现成模型不需要此字体。浏览器源文件为`src/viewer.js`、`template.html`，Three.js许可在`vendor/THREE-LICENSE.txt`。

## 当前边界

这是独立静态场景资产，尚未接入小镇运行程序，交互点为建议值，尚无人物动画、寻路、碰撞或门动画，也未做引擎性能优化。空间为游戏概念设计，不作为建筑施工或医疗设施规范审查成果。制作检查通过不代表用户视觉签收；详见`验收报告.md`。
