> 历史版本：v5 的颈肩问题已由 [v6 全角色修正](../head-turn-joints/completion.md) 替换。本页保留当时制作与检查记录；v5 动态对照固定引用修正前备份。

# 整个头部转向修正 v5

日期：2026-10-03。历史版本：`20261003-refusal-whole-head-v5`。

40 位角色的 `shake_head` 已替换为整头关键姿势：头发、耳朵、脸、后脑和附着配饰一起转向。每组 25 张 256×256 透明硬边帧，约 ±30°，720 ms 内左右往返两次，回正停顿 480 ms。动作清单 `loop=false`，GIF 为重复预览。

[打开全部角色旧/新动态对照](preview.html) · [逐文件修改清单](changed-files.json) · [专项检查](validation.json) · [生成来源与提示词索引](../../production/head-turn-solid-20261003/generation.json)

## 制作方法

使用 imagegen 技能与内置图像工具，分别参考每个角色自己的原正面、左右方向素材，补画小角度的整头姿势。生成时逐角色处理，未把其他角色的头部当作通用替换件。40 张原始生成图、120 张方向参考与各角色完整 prompt 均保存于 `production/head-turn-solid-20261003/<角色>/`。实际生成尺寸记录于索引，未把生成器请求尺寸当作实际尺寸。

沿用现有独立切片/颈部对齐流程：4×2 姿势表切片，最近邻采样、无抖色，量化到该角色原 `frame_01` 的不透明颜色，Alpha 处理为 0/255。身体复用原正面，发辫移开后露出的极少量衣服区域取同一行原衣服像素；旧头部区域之外逐像素固定。保留原素材的像素密度，没有把人物强制变成宠物的 64px 网格。

38 人的五个回正相位与原正面归一化图逐像素相同。04 麦麦、11 陈锅旧白帽内部已透明且外轮廓与头部断开，因此这两人的摇头动作采用补画的匹配回正姿势，以清除旧帽残影和透明/实心帽闪变；原 `frame_01` 未改动。这两人的帽型须重点人工确认。

±30° 是插画姿势的制作目标，不是从真实 3D 模型测量出来的旋转角。生成式补画的细小脸型、发束和配饰差异仍须结合实际显示尺寸确认。

## 验证结果

- 整头专项：40 动作、1000 帧，0 错误；每组 7 个独立姿势，发顶/帽顶与透明轮廓确实变化，整头切片原样合成；两次往返、720 ms 动作与480 ms停顿正确。
- 日常动作检查：60 个对象、162 组动作、2936 帧，0 错误、0 循环提示；RGBA、帧尺寸、二值 Alpha、图集/单帧一致性、原色复用与源哈希通过。
- 全库检查：65 个对象、920 动作，0 错误、137 提示；40 个提示为单次事件的 GIF 重复预览，11 个为宠物 GIF 合并停顿帧，其余 86 个来自旧素材。详见 [全库报告](full-validation/asset-validation.md)。
- 4744 个受保护文件哈希一致，包括原 sprite sheet、基础帧、已签收背面走路、点头/交谈和宠物素材。1240 个上一版资产/元数据已完整备份。
- 已查看全部 40 人的关键姿势页，并重点复查白帽残影和游离像素；技术检查覆盖全部 1000 帧。没有把程序检查视为用户视觉签收。
- 五个修改脚本通过语法编译。完整素材画廊和原预览 URL 已更新。浏览器核对 40 张卡片、80 张旧/新图片；首批加载的 16 张图片均为 256×256，无损坏图片、无横向溢出，其他图片按滚动延迟加载。

## 修改文件

旧文件中有 **1050 个资产/元数据文件发生内容修改**；另新增 **320 个头部源图/对齐切片**。

| 文件组 | 修改内容 |
|---|---|
| `characters/<40角色>/animations/daily/shake_head/` | 25 帧中的转向帧；两位厨师另更新回正帧 |
| `characters/<40角色>/animations/daily/shake_head.png`、`.gif` | 图集与透明动态预览 |
| `characters/<40角色>/animations/daily/overview.gif` | 日常三动作总览 |
| `characters/<40角色>/animation.json`、`animation-manifest.json`、`animations/daily/manifest.json` | 整头姿势来源、源哈希、对齐记录和播放参数 |
| `characters/<40角色>/source/shake-head-solid-poses.png`、`source/shake-head-solid/*.png` | 40 个原始新姿势表、280 张对齐头部切片 |
| `tools/head_turn.py`、`revise_head_turn.py`、`verify_head_turn.py` | 整头切片/颈部配准、批量替换、验证 |
| `tools/build_daily_actions.py`、`verify_daily_actions.py` | 重建流程与原色复用检查 |
| `validation/head-turn-solid/`、`validation/head-turn-revision/preview.html`、`validation/daily-actions/`、`asset-gallery.html`、`人物工作交接.md` | 预览、记录、完整清单与交接更新 |

上一版内容和源码分别位于 `production/head-turn-solid-20261003/before/` 与 `code-before/`。v2/v3/v4 历史报告及 GIF 保留；旧 v4 动态对照已固定引用备份。仅更新素材库，未重新打包或同步 `pixel-town-app`。

## 仍需人工确认的角色

**40 人的新摇头动作均待本次视觉确认**。此前“全部确认”只保留先前背面走路签收，不自动签收本次动作。

| 角色 | 名称 | 重点 | 状态 |
|---|---|---|---|
| 01_hero_male | 阿澈 | 整头圆度、转向幅度与快速两次拒绝节奏 | 待视觉确认 |
| 02_hero_female | 小满 | 短发轮廓、两眼透视 | 待视觉确认 |
| 03_barista_male | 林屿 | 整头圆度、转向幅度与快速两次拒绝节奏 | 待视觉确认 |
| 04_baker_male | 麦麦 | 白帽内部与帽型；本动作回正姿势补画 | 待视觉确认 |
| 05_carpenter_male | 大森 | 整头圆度、转向幅度与快速两次拒绝节奏 | 待视觉确认 |
| 06_postman_male | 小路 | 整头圆度、转向幅度与快速两次拒绝节奏 | 待视觉确认 |
| 07_police_male | 程正 | 整头圆度、转向幅度与快速两次拒绝节奏 | 待视觉确认 |
| 08_doctor_male | 许衡 | 眼镜透视 | 待视觉确认 |
| 09_gardener_male | 阿禾 | 整头圆度、转向幅度与快速两次拒绝节奏 | 待视觉确认 |
| 10_musician_male | 迟野 | 发梢与吉他遮挡 | 待视觉确认 |
| 11_chef_male | 陈锅 | 白帽内部与帽型；本动作回正姿势补画 | 待视觉确认 |
| 12_florist_female | 花音 | 长辫与脖子连接 | 待视觉确认 |
| 13_pastrychef_female | 糖糖 | 粉色厨师帽与发髻 | 待视觉确认 |
| 14_teacher_female | 温书 | 眼镜透视 | 待视觉确认 |
| 15_nurse_female | 苏晴 | 护士帽 | 待视觉确认 |
| 16_librarian_female | 知秋 | 眼镜与后发髻 | 待视觉确认 |
| 17_cafeowner_female | 沈知 | 马尾与肩部遮挡 | 待视觉确认 |
| 18_artist_female | 鹿眠 | 贝雷帽和后发髻 | 待视觉确认 |
| 19_vet_female | 安安 | 马尾透视 | 待视觉确认 |
| 20_student_female | 夏芽 | 马尾与背包遮挡 | 待视觉确认 |
| 21_firefighter_male | 陆焰 | 整头圆度、转向幅度与快速两次拒绝节奏 | 待视觉确认 |
| 22_grocer_male | 周籽 | 整头圆度、转向幅度与快速两次拒绝节奏 | 待视觉确认 |
| 23_farmer_male | 田伯 | 整头圆度、转向幅度与快速两次拒绝节奏 | 待视觉确认 |
| 24_driver_male | 韩途 | 整头圆度、转向幅度与快速两次拒绝节奏 | 待视觉确认 |
| 25_hairdresser_male | 银梳 | 整头圆度、转向幅度与快速两次拒绝节奏 | 待视觉确认 |
| 26_baker_male | 陶麦 | 整头圆度、转向幅度与快速两次拒绝节奏 | 待视觉确认 |
| 27_librarian_male | 书衡 | 整头圆度、转向幅度与快速两次拒绝节奏 | 待视觉确认 |
| 28_mechanic_male | 罗栓 | 整头圆度、转向幅度与快速两次拒绝节奏 | 待视觉确认 |
| 29_innkeeper_male | 顾栈 | 整头圆度、转向幅度与快速两次拒绝节奏 | 待视觉确认 |
| 30_florist_male | 林苔 | 长发发梢 | 待视觉确认 |
| 31_firefighter_female | 岑灯 | 整头圆度、转向幅度与快速两次拒绝节奏 | 待视觉确认 |
| 32_grocer_female | 陆杏 | 整头圆度、转向幅度与快速两次拒绝节奏 | 待视觉确认 |
| 33_farmer_female | 禾青 | 双辫、草帽和衣领衔接 | 待视觉确认 |
| 34_driver_female | 叶驰 | 整头圆度、转向幅度与快速两次拒绝节奏 | 待视觉确认 |
| 35_hairdresser_female | 卷云 | 眼镜和卷发 | 待视觉确认 |
| 36_barista_female | 闻豆 | 高马尾、发箍和耳环 | 待视觉确认 |
| 37_carpenter_female | 榆棠 | 整头圆度、转向幅度与快速两次拒绝节奏 | 待视觉确认 |
| 38_postal_female | 章铃 | 整头圆度、转向幅度与快速两次拒绝节奏 | 待视觉确认 |
| 39_police_female | 许巡 | 后颈发束 | 待视觉确认 |
| 40_doctor_female | 余笙 | 眼镜透视 | 待视觉确认 |
