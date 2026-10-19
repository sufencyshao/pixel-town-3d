# 小镇动物3D资产 V1

本目录为独立设计资产包，保留原20个动物的ID、中文名字、物种、品种、花色与相对体型身份。没有修改正式应用、存档、原2D素材、人物或整镇V5。整镇生活与人/动物互动由上层独立运行预览接入。

- `assets/manifest.json`：20项机器可读清单，`glb`路径相对于本目录。
- `assets/<id>.glb`：米制、+Y向上、+Z向前、落地原点；每只1套蒙皮骨架。
- `assets/<id>.blend`：可编辑原生工程，材质/使用的图像打包，动作保存在Action与NLA轨道。
- `renders/`：每只站立渲染与总览；渲染为独立展示缩放，体型以manifest的米制尺寸为准。
- `source/build_animals.py`：重建脚本（Blender 5.2.2），`source/validate_animals.py`：原生重开和GLB回导验证。
- `qa/validation.json`：逐只逐动作姿态样本的有限值、关节运动、地面与水平根位移证据。
- `ATTRIBUTION.md`、`vendor/`：第三方来源和许可证；分发时必须保留Cat署名。

动物使用四足、翼/腿及物种自然姿态；没有双足人类表演、穿衣、说话或人类职业动作。犬猫/马复用成熟公开模型及实际关节动画，鸟、兔、豚鼠、陆龟使用本轮原创关节骨架和分节网格。

## 动作接口

每只实际clip由manifest.actions逐项列出。统一Idle/Walk/Eat/Rest；四足哺乳动物含Run，龟无Run；猫/狗/马及鸟兔豚鼠含Drink。鸟含Fly/Hop，兔含Hop，龟含Hide；其他Groom/Sniff/Wag/Observe按实际物种与文件声明。

Walk/Run/Hop为原地动作，动画根水平位置已烘焙清零，场景wrapper承担导航推进。Fly为局部飞行姿态与翼拍，上层控制世界位置和高度。Rest为循环休息状态，犬站立放松/垂头、兔豚鼠收腿、鸟低栖、猫收腿伏蹲、马站立休息；过渡由上层clip交叉淡化承担。高度负穿地已对真实蒙皮逐帧采样修正；Run保留足部自然离地相位。

目前为风格化低多边形游戏动物，品种辨识使用毛色、耳型、体长、腿高、羽冠、翼纹、甲纹和尾形。不是解剖/临床模型，不含脚底IK、肌肉模拟、羽毛/毛发物理和精确爪部接触。宠物互动不能凭动作名推断已完成世界坐标的主人手掌接触；该部分由整镇运行层验证。

## 重建与验证

使用本机Blender：

```sh
"/Users/summerwindy/Library/Application Support/Steam/steamapps/common/Blender/Blender.app/Contents/MacOS/Blender" --background --python source/build_animals.py
"/Users/summerwindy/Library/Application Support/Steam/steamapps/common/Blender/Blender.app/Contents/MacOS/Blender" --background --python source/finalize_assets.py
"/Users/summerwindy/Library/Application Support/Steam/steamapps/common/Blender/Blender.app/Contents/MacOS/Blender" --background --python source/validate_animals.py
```

来源固定提交/原文件SHA-256、修改范围和作者署名见 `ATTRIBUTION.md`。各角色的相对体型字段保留原清单，实际3D尺寸按物种合理范围分别制作，不能把旧2D的scale直接当作米。
