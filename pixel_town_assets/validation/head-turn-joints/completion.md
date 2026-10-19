# 全部人物摇头颈肩修正 v6（历史版本）

日期：2026-10-03。历史版本：`20261003-refusal-fixed-joints-v6`。

> 历史版本说明：用户继续反馈肩膀消失、颈部错位及衣料挡住头发。v6 的技术检查并未证明视觉问题已解决；本页保留历史记录，当前实现、制作侧逐人复查及签收状态见 [v7 报告](../head-turn-anatomy/completion.md)。

已按用户反馈检查并重建 **全部 40 人的 shake_head，共 1000 帧**，包含大森、迟野及此前点名的角色。保留原肩膀、衣领和颈根，逐角色校准转头与身体的接缝。仍以约 ±30° 为插画姿势目标，720 ms 内左右往返两次，回正停顿 480 ms；每帧为 256×256 透明硬边 RGBA。

[40 人修正前/后动态对照](preview-v6.html) · [逐文件修改清单](changed-files.json) · [专项检查](validation.json) · [全库报告](full-validation/asset-validation.md)

## 问题与修正

上一版用水平截线分割头身，把较高的衣领和肩膀划进了移动头部；长发与发辫又干扰了颈部配准。闻豆的原头像素分成多个连通块，只保留最大块还会丢失面部。仅检查“移动头部之外的身体没有改变”，不能检出被错误划入头部的衣服。

本次复用 v5 的 40 张整头姿势源图，未重新生成角色。保留现有 sprite sheet、角色帧命名和日常切片/播放流程，改变头身分区与配准：

- 为 40 人分别标定衣服边界、固定颈根和两个原衣服检查区域，配置集中在 `tools/head_joint_calibration.json`。
- 头部取完整像素集合；脸、头发、耳朵、帽子和眼镜随关键姿势一起转向。长发只在标定范围内剔除，原衣领与肩膀作为前景保留。
- 校正花音、沈知、安安、禾青、闻豆、许巡的源姿势颈部锚点；安安、闻豆改用实际颈部位置，避免把侧面长发尾端当成颈部。闻豆同时恢复完整原头部尺寸标定。
- 沈知、林苔、闻豆的少量被原头发遮住的衣服，只在限定范围内复用同一行原衣服像素；沈知使用原对侧衣袖像素。没有重画整个身体。
- 花音、禾青、许巡的胸前下段发辫保留原图位置与遮挡，头和上段发束转向；这三人的发辫连接需要目测确认。
- 最近邻采样、角色原色量化、无抖色，Alpha 仍为 0/255。清除原发梢残影，禁止生成头部覆盖固定肩膀、衣领或颈根。

38 人的五个回正相位仍与原正面归一化图逐像素相同。麦麦、陈锅沿用 v5 的匹配回正补画，处理旧白帽透明残影；原 `frame_01` 未修改。±30° 是插画制作目标，未从实际 3D 模型测量角度。

## 验证结果

| 检查 | 结果 |
|---|---|
| 颈肩专项 | 40 动作、1000 帧，0 错误 |
| 原衣服与颈根 | 每人固定身体遮罩内原像素，在全部 25 相位保持一致 |
| 独立衣服检查 | 40 人、80 个原衣服检查区域，全部相位通过；不依赖移动头部范围 |
| 颈部连接 | 每人 25 相位均有跨接缝的八邻域不透明路径，无检测到的断点 |
| 整头转向 | 每人 7 种独立姿势，发顶/帽顶及轮廓随姿势改变 |
| 节奏与规格 | 两次往返后回正；24×30 ms＋480 ms；256×256、RGBA、二值 Alpha；图集与单帧一致 |
| 日常动作 | 60 对象、162 动作、2936 帧，0 错误、0 提示 |
| 全库 | 65 对象、920 动作，0 错误、137 提示 |
| 原素材保护 | 4784 个受保护文件哈希一致；1520 个上一版文件备份哈希一致 |
| 脚本 | 三个修改脚本通过语法编译 |
| 浏览器预览 | 40 张卡片、80 张图片均加载为 256×256；无损坏图片、无横向溢出（1280×720） |

全库 137 个提示中，40 个为单次事件的 GIF 循环预览，11 个为宠物 GIF 合并停顿帧但总时长正确，其余 86 个来自既有素材。原 sprite sheet、基础帧、已签收背面走路、点头/交谈、宠物及 v5 原始生成姿势表均在保护范围内。

已逐角色查看七种独立姿势的颈肩接缝比较页，并复查最后修正的卷云发梢。程序检查覆盖 1000 帧；重复相位未声称逐帧人工观看。连接检查只能发现断裂，不能代替对头颈比例、遮挡和造型自然度的视觉确认。

[浏览器核验记录](browser-check.json) 与 [实机对照截图](browser-proof.jpg) 已保存；动态效果请使用上方 40 人对照页。

## 修改文件

上一版已有 **1330 个资产/元数据文件**发生内容修改：810 个单帧、120 个图集/GIF/动作总览、120 个元数据、280 个已配准头部切片。重建输出共 1000 帧，其中沿用原正面的回正帧内容保持一致。另新增 **80 个原身体/原头部遮罩 PNG**与一份标定 JSON。

| 文件组 | 修改内容 |
|---|---|
| `characters/<40角色>/animations/daily/shake_head/frame_01.png…frame_25.png` | 修正颈肩接缝及衣领遮挡；回正策略保持 |
| `characters/<40角色>/animations/daily/shake_head.png`、`.gif`、`overview.gif` | 重新合成图集、透明预览与三动作总览 |
| `characters/<40角色>/animation.json`、`animation-manifest.json`、`animations/daily/manifest.json` | v6 标定、遮罩来源与哈希、播放参数 |
| `characters/<40角色>/source/shake-head-solid/*.png` | 使用同一源图重新配准 280 个整头切片 |
| `characters/<40角色>/source/shake-head-joint-body.png`、`shake-head-joint-original-head.png` | 新增 80 个原固定身体/原移动头部的检查依据 |
| `tools/head_turn.py` | 原衣服前景、颈根固定、完整原头部提取、逐角色锚点和有限露出区域修补 |
| `tools/head_joint_calibration.json` | 新增 40 人边界、颈根、源姿势锚点、发束范围及衣服检查区域 |
| `tools/revise_head_turn.py` | v6 批量制作、v5 备份、动态对照和修改清单 |
| `tools/verify_head_turn.py` | 新增原衣服独立检查与逐相位颈部连接检查 |
| `validation/head-turn-joints/` | 标定检查区域、核验结果、关键姿势、对照预览和本报告 |
| `validation/head-turn-revision/preview.html` | 用户原预览 URL 同步 v6 |
| `validation/daily-actions/generation.json`、`preview.html`、`completion.md` | 当前摇头来源、动态预览和说明 |
| `validation/head-turn-solid/completion.md`、`preview.html` | v5 标记为历史版本；历史对照引用 v5 备份 |
| `asset-gallery.html`、`人物工作交接.md` | 素材画廊重建、追加当前版本交接 |
| `production/head-turn-joints-20261003/` | v5 文件备份、前后源码快照、标定/诊断脚本 |

精确到每个角色文件的清单见 [changed-files.json](changed-files.json)。回退文件位于 `production/head-turn-joints-20261003/before/`；源码分别在 `code-before/` 和 `code-after/`。生产记录目录根部同名的三个主脚本是修正前快照；当前重建使用 `tools/` 内代码。

## 仍需人工确认的角色

**这次 v6 的 40 人摇头动作均待用户视觉确认。**此前“全部确认”继续适用于原背面走路。本次已完成技术检查与制作侧关键姿势复查，不把它们记成用户签收。

重点先看知秋、沈知、安安、夏芽、林苔、闻豆的头颈比例和肩膀遮挡；花音、禾青、许巡的上下发辫衔接；麦麦、陈锅的白帽。所有角色名单如下。

| 角色与动态预览 | 名称 | 目测重点 | 状态 |
|---|---|---|---|
| [01_hero_male](../../characters/01_hero_male/animations/daily/shake_head.gif) | 阿澈 | 下颌、颈根、衣领和双肩；圆度与两次拒绝节奏 | 待视觉确认 |
| [02_hero_female](../../characters/02_hero_female/animations/daily/shake_head.gif) | 小满 | 短发、脸颊圆度及领口连接 | 待视觉确认 |
| [03_barista_male](../../characters/03_barista_male/animations/daily/shake_head.gif) | 林屿 | 下颌、颈根、衣领和双肩；圆度与两次拒绝节奏 | 待视觉确认 |
| [04_baker_male](../../characters/04_baker_male/animations/daily/shake_head.gif) | 麦麦 | 白帽轮廓；沿用 v5 补画的回正姿势 | 待视觉确认 |
| [05_carpenter_male](../../characters/05_carpenter_male/animations/daily/shake_head.gif) | 大森 | 方脸下颌与工作服肩膀连接 | 待视觉确认 |
| [06_postman_male](../../characters/06_postman_male/animations/daily/shake_head.gif) | 小路 | 下颌、颈根、衣领和双肩；圆度与两次拒绝节奏 | 待视觉确认 |
| [07_police_male](../../characters/07_police_male/animations/daily/shake_head.gif) | 程正 | 下颌、颈根、衣领和双肩；圆度与两次拒绝节奏 | 待视觉确认 |
| [08_doctor_male](../../characters/08_doctor_male/animations/daily/shake_head.gif) | 许衡 | 眼镜透视、白大褂领口 | 待视觉确认 |
| [09_gardener_male](../../characters/09_gardener_male/animations/daily/shake_head.gif) | 阿禾 | 下颌、颈根、衣领和双肩；圆度与两次拒绝节奏 | 待视觉确认 |
| [10_musician_male](../../characters/10_musician_male/animations/daily/shake_head.gif) | 迟野 | 耳下发梢、衣领与吉他遮挡 | 待视觉确认 |
| [11_chef_male](../../characters/11_chef_male/animations/daily/shake_head.gif) | 陈锅 | 白帽轮廓；沿用 v5 补画的回正姿势 | 待视觉确认 |
| [12_florist_female](../../characters/12_florist_female/animations/daily/shake_head.gif) | 花音 | 上段发辫随头转向，下段原辫固定在胸前的衔接 | 待视觉确认 |
| [13_pastrychef_female](../../characters/13_pastrychef_female/animations/daily/shake_head.gif) | 糖糖 | 粉色帽子、发髻与领口 | 待视觉确认 |
| [14_teacher_female](../../characters/14_teacher_female/animations/daily/shake_head.gif) | 温书 | 眼镜、衣领和手持书本遮挡 | 待视觉确认 |
| [15_nurse_female](../../characters/15_nurse_female/animations/daily/shake_head.gif) | 苏晴 | 护士帽与颈根 | 待视觉确认 |
| [16_librarian_female](../../characters/16_librarian_female/animations/daily/shake_head.gif) | 知秋 | 后发髻、眼镜与高领边界 | 待视觉确认 |
| [17_cafeowner_female](../../characters/17_cafeowner_female/animations/daily/shake_head.gif) | 沈知 | 马尾、右肩白袖和颈部长度 | 待视觉确认 |
| [18_artist_female](../../characters/18_artist_female/animations/daily/shake_head.gif) | 鹿眠 | 贝雷帽、后发髻与肩膀 | 待视觉确认 |
| [19_vet_female](../../characters/19_vet_female/animations/daily/shake_head.gif) | 安安 | 马尾移开后的肩膀，以及重新标定的颈部位置 | 待视觉确认 |
| [20_student_female](../../characters/20_student_female/animations/daily/shake_head.gif) | 夏芽 | 马尾、背包肩带与颈根 | 待视觉确认 |
| [21_firefighter_male](../../characters/21_firefighter_male/animations/daily/shake_head.gif) | 陆焰 | 深肤色下颌、制服高领及肩膀 | 待视觉确认 |
| [22_grocer_male](../../characters/22_grocer_male/animations/daily/shake_head.gif) | 周籽 | 下颌、颈根、衣领和双肩；圆度与两次拒绝节奏 | 待视觉确认 |
| [23_farmer_male](../../characters/23_farmer_male/animations/daily/shake_head.gif) | 田伯 | 围裙肩带和领口 | 待视觉确认 |
| [24_driver_male](../../characters/24_driver_male/animations/daily/shake_head.gif) | 韩途 | 制服衣领与颈根 | 待视觉确认 |
| [25_hairdresser_male](../../characters/25_hairdresser_male/animations/daily/shake_head.gif) | 银梳 | 下颌、颈根、衣领和双肩；圆度与两次拒绝节奏 | 待视觉确认 |
| [26_baker_male](../../characters/26_baker_male/animations/daily/shake_head.gif) | 陶麦 | 围裙领口与颈根 | 待视觉确认 |
| [27_librarian_male](../../characters/27_librarian_male/animations/daily/shake_head.gif) | 书衡 | 衣领与颈根 | 待视觉确认 |
| [28_mechanic_male](../../characters/28_mechanic_male/animations/daily/shake_head.gif) | 罗栓 | 工作服肩膀、下颌与领口 | 待视觉确认 |
| [29_innkeeper_male](../../characters/29_innkeeper_male/animations/daily/shake_head.gif) | 顾栈 | 衣领和双肩 | 待视觉确认 |
| [30_florist_male](../../characters/30_florist_male/animations/daily/shake_head.gif) | 林苔 | 长发移开后露出的肩膀、绿围裙和颈根 | 待视觉确认 |
| [31_firefighter_female](../../characters/31_firefighter_female/animations/daily/shake_head.gif) | 岑灯 | 深肤色下颌、制服高领及肩膀 | 待视觉确认 |
| [32_grocer_female](../../characters/32_grocer_female/animations/daily/shake_head.gif) | 陆杏 | 短发发梢与橙围裙领口 | 待视觉确认 |
| [33_farmer_female](../../characters/33_farmer_female/animations/daily/shake_head.gif) | 禾青 | 上段发辫随头转向，下段原辫固定在胸前的衔接 | 待视觉确认 |
| [34_driver_female](../../characters/34_driver_female/animations/daily/shake_head.gif) | 叶驰 | 下颌、颈根、衣领和双肩；圆度与两次拒绝节奏 | 待视觉确认 |
| [35_hairdresser_female](../../characters/35_hairdresser_female/animations/daily/shake_head.gif) | 卷云 | 金色发梢残影、眼镜与紫色领口 | 待视觉确认 |
| [36_barista_female](../../characters/36_barista_female/animations/daily/shake_head.gif) | 闻豆 | 重新标定的完整头部、两侧卷发与肩膀连接 | 待视觉确认 |
| [37_carpenter_female](../../characters/37_carpenter_female/animations/daily/shake_head.gif) | 榆棠 | 红围裙肩带和双肩 | 待视觉确认 |
| [38_postal_female](../../characters/38_postal_female/animations/daily/shake_head.gif) | 章铃 | 帽子与颈根 | 待视觉确认 |
| [39_police_female](../../characters/39_police_female/animations/daily/shake_head.gif) | 许巡 | 上段发辫随头转向，下段原辫固定在制服前的衔接 | 待视觉确认 |
| [40_doctor_female](../../characters/40_doctor_female/animations/daily/shake_head.gif) | 余笙 | 眼镜、白衣领口与颈根 | 待视觉确认 |

## 重建

在 `pixel_town_assets/` 工作目录运行：

```sh
python3 tools/revise_head_turn.py
python3 tools/verify_head_turn.py
python3 tools/verify_daily_actions.py
python3 tools/build_gallery.py
python3 tools/validate_assets.py --output validation/head-turn-joints/full-validation
```

重建读取已有原始姿势表，不调用图像生成 API。仅交付本素材库，游戏动作触发及应用内素材同步仍按日常动作交接处理。
