#!/usr/bin/env python3
"""Write the v6 asset handoff from the completed validation records."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / 'validation/head-turn-joints'
result = json.loads((AUDIT / 'validation.json').read_text())
daily = json.loads((ROOT / 'validation/daily-actions/validation.json').read_text())
full = json.loads((AUDIT / 'full-validation/asset-validation.json').read_text())['summary']
assert result['roles'] == 40 and not result['errors'] and not daily['errors'] and full['errors'] == 0

focus = {
    2: '短发、脸颊圆度及领口连接',
    4: '白帽轮廓；沿用 v5 补画的回正姿势',
    5: '方脸下颌与工作服肩膀连接',
    8: '眼镜透视、白大褂领口',
    10: '耳下发梢、衣领与吉他遮挡',
    11: '白帽轮廓；沿用 v5 补画的回正姿势',
    12: '上段发辫随头转向，下段原辫固定在胸前的衔接',
    13: '粉色帽子、发髻与领口',
    14: '眼镜、衣领和手持书本遮挡',
    15: '护士帽与颈根',
    16: '后发髻、眼镜与高领边界',
    17: '马尾、右肩白袖和颈部长度',
    18: '贝雷帽、后发髻与肩膀',
    19: '马尾移开后的肩膀，以及重新标定的颈部位置',
    20: '马尾、背包肩带与颈根',
    21: '深肤色下颌、制服高领及肩膀',
    23: '围裙肩带和领口',
    24: '制服衣领与颈根',
    26: '围裙领口与颈根',
    27: '衣领与颈根',
    28: '工作服肩膀、下颌与领口',
    29: '衣领和双肩',
    30: '长发移开后露出的肩膀、绿围裙和颈根',
    31: '深肤色下颌、制服高领及肩膀',
    32: '短发发梢与橙围裙领口',
    33: '上段发辫随头转向，下段原辫固定在胸前的衔接',
    35: '金色发梢残影、眼镜与紫色领口',
    36: '重新标定的完整头部、两侧卷发与肩膀连接',
    37: '红围裙肩带和双肩',
    38: '帽子与颈根',
    39: '上段发辫随头转向，下段原辫固定在制服前的衔接',
    40: '眼镜、白衣领口与颈根',
}
rows = []
for check in result['checks']:
    folder = ROOT / 'characters' / check['role']
    name = json.loads((folder / 'profile.json').read_text())['name']
    role = int(folder.name[:2])
    review = focus.get(role, '下颌、颈根、衣领和双肩；圆度与两次拒绝节奏')
    rows.append(f"| [{folder.name}](../../characters/{folder.name}/animations/daily/shake_head.gif) | {name} | {review} | 待视觉确认 |")

report = '''# 全部人物摇头颈肩修正 v6

日期：2026-10-03。当前版本：`20261003-refusal-fixed-joints-v6`。

已按用户反馈检查并重建 **全部 40 人的 shake_head，共 1000 帧**，包含大森、迟野及此前点名的角色。保留原肩膀、衣领和颈根，逐角色校准转头与身体的接缝。仍以约 ±30° 为插画姿势目标，720 ms 内左右往返两次，回正停顿 480 ms；每帧为 256×256 透明硬边 RGBA。

[40 人修正前/后动态对照](preview.html) · [逐文件修改清单](changed-files.json) · [专项检查](validation.json) · [全库报告](full-validation/asset-validation.md)

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
'''+ '\n'.join(rows)+'''

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
'''
(AUDIT / 'completion.md').write_text(report)

handoff = ROOT / '人物工作交接.md'
text = handoff.read_text().replace('## 十三、整个头部一起转向（2026-10-03，当前版本）', '## 十三、整个头部一起转向（2026-10-03，已被第十四节替换）')
marker = '\n## 十四、全部人物颈肩接缝修正（2026-10-03，当前版本）'
section = '''
## 十四、全部人物颈肩接缝修正（2026-10-03，当前版本）

用户指出几乎所有角色在摇头时出现肩膀消失、衣领错位或脖子扭曲。已检查并重建全部 40 人的 shake_head（含大森、迟野），版本 `20261003-refusal-fixed-joints-v6`。复用第十三节保存的 40 张整头姿势表；逐角色标定原衣服边界、颈根和源姿势颈部锚点，原肩膀/衣领作为固定前景保留。闻豆恢复完整原头像素与正确配准；原回正策略、约 ±30°、720 ms 两次快速往返及 480 ms 预览停顿保持。

每组 25 张 256×256 透明硬边帧。新增原身体/原头部遮罩，独立检查原衣服像素，并逐相位核对中央颈部连接。花音、禾青、许巡的胸前下段发辫保留原位置，上段与头一起转动，衔接需视觉复核；麦麦、陈锅继续沿用 v5 匹配回正补画。

颈肩专项 40 动作/1000 帧与日常 162 动作/2936 帧均 0 错误；全库 65 对象/920 动作，0 错误、137 提示。4784 个受保护文件、1520 个 v5 备份哈希一致。1330 个已有资产/元数据修改，新增 80 个检查遮罩及一份标定 JSON。完整 [报告与40人复核名单](validation/head-turn-joints/completion.md)、[当前动态对照](validation/head-turn-joints/preview.html)、[逐文件清单](validation/head-turn-joints/changed-files.json)。原打开的 head-turn-revision 预览同步 v6；v5 动态页固定引用备份。

本次 40 人摇头仍待用户视觉签收，重点为知秋、沈知、安安、夏芽、林苔、闻豆的头颈连接，以及三位长辫角色和两位白帽角色。原背面走路签收继续有效。当前源码位于 tools/，前后快照及回退资产位于 production/head-turn-joints-20261003/。重建不调用图像 API；未同步或重新打包 pixel-town-app。
'''
text = text.split(marker)[0].rstrip() + '\n' + section
handoff.write_text(text)

history = ROOT / 'validation/head-turn-solid/completion.md'
old = history.read_text()
note = '> 历史版本：v5 的颈肩问题已由 [v6 全角色修正](../head-turn-joints/completion.md) 替换。本页保留当时制作与检查记录；v5 动态对照固定引用修正前备份。\n\n'
if not old.startswith('> 历史版本：'):
    old = note + old
old = old.replace('日期：2026-10-03。当前版本：', '日期：2026-10-03。历史版本：', 1)
history.write_text(old)

daily_doc = ROOT / 'validation/daily-actions/completion.md'
text = daily_doc.read_text()
text = text.replace('原身体复用；详见 [当前整头转向修正记录](../head-turn-solid/completion.md)。',
    '原身体复用。当前 v6 逐角色校准头身分界和颈部锚点，原肩膀、衣领、颈根固定为前景；花音、禾青、许巡胸前下段发辫保留原遮挡。详见 [当前全角色颈肩修正记录](../head-turn-joints/completion.md)。')
text = text.replace('全库检查（30° 摇头修正后）', '全库检查（v6 颈肩修正后）')
text = text.replace('最新报告在 validation/head-turn-solid/full-validation/', '最新报告在 validation/head-turn-joints/full-validation/')
text = text.replace('摇头最新变更完整清单见 [head-turn-rounded/changed-files.json](../head-turn-rounded/changed-files.json)。',
    '摇头最新变更完整清单见 [head-turn-joints/changed-files.json](../head-turn-joints/changed-files.json)。')
text = text.replace('40 人修正版仍待视觉确认。', '40 人 v6 颈肩修正版仍待视觉确认，名单及各自复核重点见当前修正报告。')
daily_doc.write_text(text)
print('Wrote v6 completion report, all 40 review rows, handoff and daily/history links.')
