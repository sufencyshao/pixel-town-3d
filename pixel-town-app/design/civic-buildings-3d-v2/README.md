# 诊所与图书馆 V2 · 平顶修订

按本轮反馈修改：图书馆改为两层平顶，诊所改为单层平顶并增加医疗红十字。V1目录与压缩包保留，V2是本轮最新交付。

## 使用

直接打开`诊所与图书馆-离线预览.html`。可旋转、缩放、查看外观与室内、俯视、切换图书馆楼层、下载GLB及保存画面。模型嵌入HTML，不需要联网；下载Blender工程需要保留两栋子目录。

Blender直接打开`clinic/B03-clinic.blend`或`library/B02-library.blend`。也可通过glTF导入菜单导入同名GLB。单位为米，中文标牌已转网格，现成工程及GLB无需外部字体和贴图。

## 设计变化

| 建筑 | 本轮变化 | 保留和新增空间 |
| --- | --- | --- |
| 诊所 | 单层平屋顶、绿色压顶、入口上方白底红十字立体标志 | 主体16 × 11 m；接待、6座候诊、两间诊室、两张观察床、储物、洗手点、卫生间 |
| 图书馆 | 两层平屋顶、陶土色水平装饰带、西侧楼梯、真实楼板开口与护栏 | 主体19 × 12 m；一层借还书、儿童角、新书展示、4组书架和12座阅览；二层4组书架和18座阅览 |

图书馆层高3.8 m；楼梯22级、踏步深0.29 m、宽2.3 m。二层北侧平台接入书架区与阅读区。一层原西窗阅读位及两组书架调整给楼梯，二层新增安静阅览。总计8组双面书架、30个常规阅读座位，另有儿童坐垫与门廊长椅。图书馆人物关联仍为知秋、书衡；诊所仍为许衡、余笙、苏晴。

## Blender场景

- `01 Exterior`：完整外观。
- `02 Interior`：诊所室内 / 图书馆一层剖切。
- `03 Plan`：诊所俯视 / 图书馆一层俯视。
- 图书馆另有`04 Upper Interior`、`05 Upper Plan`：二层剖切和俯视。

集合`Roof`可独立隐藏；二层分为`UpperFloor`、`UpperStructure`、`UpperFront`、`UpperEast`、`UpperInterior`，支持分层编辑。`Studio`是摄影灯光与背景，仅保存在Blender工程内。Blender为Z轴向上、正面-Y，导出GLB为Y轴向上、正面+Z。

每栋PNG为Blender实际渲染，`manifest.json`记录模型统计与建议交互点。具体本轮验证见`验收报告.md`、`validation.json`。

## 重建

使用Blender 5.2.2 LTS；在本目录执行：

```sh
blender --background --python src/build_models.py
blender --background --python src/verify_models.py
npm install
npm run preview:build
```

重建会覆盖本目录生成资产，请先另存手工编辑过的工程。源脚本制作中文网格时使用macOS的`/System/Library/Fonts/STHeiti Medium.ttc`；其他系统重建需替换该字体路径。Three.js 0.180.0、esbuild 0.25.9，许可在`vendor/`。

当前为静态游戏场景设计，尚未接入角色、碰撞、寻路和楼梯行走动画；本轮空间尺寸为模型设计参数。技术验证与用户视觉签收分别记录。
