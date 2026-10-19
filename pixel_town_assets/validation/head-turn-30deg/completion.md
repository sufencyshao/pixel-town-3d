# 30° 快速拒绝摇头修正

> 本文保留 v3 的 30° 版本历史记录。用户随后反馈转向时头部变扁，当前修正保持头部原宽度与圆度；见 [最新圆度修正报告](../head-turn-rounded/completion.md)。本目录 GIF/关键姿势/核验 JSON 保留历史结果，preview.html 的 v3 图片已固定到备份。重建脚本当前生成 v4。

2026-10-03；版本 `20261003-refusal-30deg-v3`。

按用户要求，40 位人物的摇头幅度缩小为左右各约 30°，0.72 秒内快速左右往返两次，最后回正。每人 25 张 256×256 透明 RGBA 帧，共 1000 张摇头帧。

[全部 40 人动态对照](preview.html)；[男主示例](hero-refusal.gif)；[女主示例](heroine-refusal.gif)；[完整逐文件清单](changed-files.json)。动态对照左侧为此前幅度偏大的完整侧脸版，右侧为当前版本。

## 节奏与使用

- 一次完整往返：正面 → 左约 30° → 正面 → 右约 30° → 正面；连续执行两次，再停在正面。
- 单帧编号 01…25，对应相位 0…24。相位 3/15 是左侧极限，9/21 是右侧极限；0/6/12/18/24 与标准化原正面逐像素一致。
- 前 24 帧各 30 ms，实际运动 720 ms；第 25 帧回正停顿 480 ms。GIF 每轮共 1200 ms，停顿后重复便于检查。
- `loop=false` 表示摇头拒绝是单次事件；`previewLoop=true` 表示 GIF 重复预览。播放器应读取 `durations` 逐帧时长，动作完成后保持末帧。`frameMs=30` 是基础运动间隔，不能替代最后一帧的 480 ms。
- 仅包含本批动作的 daily/overview.gif 同步按各动作时长生成：点头 1440 ms、拒绝摇头 1200 ms、交谈 1440 ms，共 4080 ms。

## 像素与来源

复用每位角色自身原 frame_01.png 的正面像素，将头部投影到浅曲面上，采用 ±30° 的横向转头参数；远近侧五官间距与轮廓宽度随转向改变。所有采样使用最近邻，透明 Alpha 仅 0/255，未增加颜色、模糊叠脸、整头平移、倾斜或上下摇摆。头颈分界以下逐像素保持原正面，包括衣服、手、工具和发束末端。

±30° 是二维像素浅曲面投影的角度参数，属于小角度转头近似；没有为每个角度另画新的侧脸。原基础 16 帧、sprite sheet 及此前左右侧脸素材均保留。

## 验证结果

- 摇头专项：40 组、1000 帧，0 错误。核对 ±30° 上限、恰好两次左右极值、两次动作一致、五个正面相位一致、身体固定、7 个不同角度姿势、GIF 各帧时长和日常总览节奏。
- 日常动作专项：60 对象、162 组、2936 帧，0 错误、0 循环接缝提示。逐帧检查 256×256 RGBA、二值 Alpha、图集与单帧一致、源颜色/哈希、非空与边界裁切。
- 全库：65 对象、920 动作，0 错误、137 提示。其中 40 项是单次事件的 GIF 重复预览，11 项是宠物 GIF 合并重复停顿帧，其余 86 项来自已有素材；不是本次摇头格式错误。
- 4744 个受保护文件、880 个上一版备份文件通过 SHA-256 核验；此前签收背面循环的 140 个资产也通过哈希保护检查。点头、交谈、宠物动作和原始素材保持。
- 已查看全部 40 人的 8 页关键姿势，涵盖回正、两次左右极限，复核帽子、眼镜、长发和工具附近的连接。浏览器对照页显示 40 张卡片、80 张旧/新图片，已加载图片均为 256×256，窄窗口无横向溢出。未将关键姿势抽查等同于用户视觉签收。
- 5 个修改的 Python 脚本通过语法编译。

机器记录：[摇头专项](validation.json)、[日常专项](../daily-actions/validation.json)、[全库检查](full-validation/asset-validation.md)。

## 修改文件与回退

每位角色目录 `characters/<角色>/`：

- `animations/daily/shake_head.png`、`shake_head.gif` 与 `shake_head/frame_01.png…frame_25.png`：当前 25 帧拒绝摇头。原 frame_01 图像相同，其余已更新或新增。
- `animations/daily/overview.gif`：保留新的快速节奏。
- `animation.json`、`animation-manifest.json`、`animations/daily/manifest.json`：更新帧数、时长数组、转向参数与单次事件配置。

与上一版相比，840 个角色资产/元数据文件内容改变，新增 360 个单帧文件；40 个回正首帧内容本来相同。角色基础目录的 frame_01.png…frame_16.png 没有覆盖。

修改脚本：`tools/head_turn.py`、`tools/revise_head_turn.py`、`tools/verify_head_turn.py`、`tools/build_daily_actions.py`、`tools/verify_daily_actions.py`。更新素材画廊、日常生成/验证/预览/8 页动作比较/报告、工作交接和历史版本指向说明。完整路径及当前哈希均在 changed-files.json。

上一版 880 个资产/元数据保存在 `production/head-turn-30deg-20261003/before/`，其 SHA-256 在 before.json。改动前 5 个脚本及哈希在 `production/head-turn-30deg-20261003/code-before/`。更早的钟摆版备份与 v2 历史核验保留。

```sh
python3 pixel_town_assets/tools/revise_head_turn.py
python3 pixel_town_assets/tools/verify_head_turn.py
python3 pixel_town_assets/tools/verify_daily_actions.py
python3 pixel_town_assets/tools/build_gallery.py
python3 pixel_town_assets/tools/validate_assets.py --output validation/head-turn-30deg/full-validation
```

全量 daily 构建也使用同一套小角度拒绝摇头，重建不会恢复此前大幅侧脸版本。本次交付素材包与画廊，未同步或重新打包 pixel-town-app；游戏接入仍需支持事件动作和 durations 数组。

## 仍需人工确认的角色

40 位角色的当前 30° 拒绝摇头尚未获得用户视觉签收。此前“全部确认”继续属于已完成的背面走路批次。

重点确认小角度脸部辨识度与快速两次节奏；02 短发、04/11/13 帽子、08/14/16/35/40 眼镜、10 吉他、12/33/36/39 发束与颈部衔接可重点复核。

| 角色目录 | 姓名 | 本次人工确认 |
|---|---|---|
| characters/01_hero_male | 阿澈 | 30° 快速摇两下待视觉确认 |
| characters/02_hero_female | 小满 | 30° 快速摇两下待视觉确认 |
| characters/03_barista_male | 林屿 | 30° 快速摇两下待视觉确认 |
| characters/04_baker_male | 麦麦 | 30° 快速摇两下待视觉确认 |
| characters/05_carpenter_male | 大森 | 30° 快速摇两下待视觉确认 |
| characters/06_postman_male | 小路 | 30° 快速摇两下待视觉确认 |
| characters/07_police_male | 程正 | 30° 快速摇两下待视觉确认 |
| characters/08_doctor_male | 许衡 | 30° 快速摇两下待视觉确认 |
| characters/09_gardener_male | 阿禾 | 30° 快速摇两下待视觉确认 |
| characters/10_musician_male | 迟野 | 30° 快速摇两下待视觉确认 |
| characters/11_chef_male | 陈锅 | 30° 快速摇两下待视觉确认 |
| characters/12_florist_female | 花音 | 30° 快速摇两下待视觉确认 |
| characters/13_pastrychef_female | 糖糖 | 30° 快速摇两下待视觉确认 |
| characters/14_teacher_female | 温书 | 30° 快速摇两下待视觉确认 |
| characters/15_nurse_female | 苏晴 | 30° 快速摇两下待视觉确认 |
| characters/16_librarian_female | 知秋 | 30° 快速摇两下待视觉确认 |
| characters/17_cafeowner_female | 沈知 | 30° 快速摇两下待视觉确认 |
| characters/18_artist_female | 鹿眠 | 30° 快速摇两下待视觉确认 |
| characters/19_vet_female | 安安 | 30° 快速摇两下待视觉确认 |
| characters/20_student_female | 夏芽 | 30° 快速摇两下待视觉确认 |
| characters/21_firefighter_male | 陆焰 | 30° 快速摇两下待视觉确认 |
| characters/22_grocer_male | 周籽 | 30° 快速摇两下待视觉确认 |
| characters/23_farmer_male | 田伯 | 30° 快速摇两下待视觉确认 |
| characters/24_driver_male | 韩途 | 30° 快速摇两下待视觉确认 |
| characters/25_hairdresser_male | 银梳 | 30° 快速摇两下待视觉确认 |
| characters/26_baker_male | 陶麦 | 30° 快速摇两下待视觉确认 |
| characters/27_librarian_male | 书衡 | 30° 快速摇两下待视觉确认 |
| characters/28_mechanic_male | 罗栓 | 30° 快速摇两下待视觉确认 |
| characters/29_innkeeper_male | 顾栈 | 30° 快速摇两下待视觉确认 |
| characters/30_florist_male | 林苔 | 30° 快速摇两下待视觉确认 |
| characters/31_firefighter_female | 岑灯 | 30° 快速摇两下待视觉确认 |
| characters/32_grocer_female | 陆杏 | 30° 快速摇两下待视觉确认 |
| characters/33_farmer_female | 禾青 | 30° 快速摇两下待视觉确认 |
| characters/34_driver_female | 叶驰 | 30° 快速摇两下待视觉确认 |
| characters/35_hairdresser_female | 卷云 | 30° 快速摇两下待视觉确认 |
| characters/36_barista_female | 闻豆 | 30° 快速摇两下待视觉确认 |
| characters/37_carpenter_female | 榆棠 | 30° 快速摇两下待视觉确认 |
| characters/38_postal_female | 章铃 | 30° 快速摇两下待视觉确认 |
| characters/39_police_female | 许巡 | 30° 快速摇两下待视觉确认 |
| characters/40_doctor_female | 余笙 | 30° 快速摇两下待视觉确认 |
