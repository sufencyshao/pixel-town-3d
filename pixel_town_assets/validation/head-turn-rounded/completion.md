# 人物摇头圆度修正

2026-10-03；版本 `20261003-refusal-rounded-v4`。

用户反馈上一版摇头时头部显得扁。40 人已改为保持原头部宽度、高度和透明外轮廓的弧面纹理转向，保留左右约 30°、0.72 秒快速摇两下后回正的节奏。

[40 人旧/新动态对照](preview.html)；[男主 GIF](hero-refusal.gif)；[女主 GIF](heroine-refusal.gif)；[8 人原正面/旧版/新左右极限](volume-comparison.png)；[逐文件修改清单](changed-files.json)。对照页左侧为上一版变窄效果，右侧为当前版本。

## 原因与修正

上一版投影把整颗头的横坐标乘以 cos(yaw)，30° 时理论宽度压缩到约 86.6%；头部侧面又缺乏真实厚度来源，所以产生薄片观感。

当前保留原正面的头部不透明轮廓，五官与前侧纹理按弧面变换移动，脸颊/后脑不会一起缩窄。每行变换为 v=u+a(1-u²)，a=0.6 tan(yaw)，两端点始终固定；±30° 内映射单调，不折叠。只采样该行原不透明像素，避免发束/眼镜转向时拉入空白 Alpha。颈部以下逐像素固定；没有整头平移、倾斜或上下摇摆。

这仍是原二维像素的弧面转向近似，保留原脸型、发色与像素颜色；没有恢复真实 3D 头部，也没有逐角度新绘。轮廓检查通过不能代替动作自然感的人工确认。

## 节奏与规格

- 每人 25 张 256×256 透明 RGBA 帧；40 人共 1000 张摇头帧。
- 正面 → 左约 30° → 正面 → 右约 30° → 正面，连续执行两次，最后回正。
- 前 24 帧各 30 ms，运动共 720 ms；第 25 帧回正停顿 480 ms。GIF 每轮 1200 ms，停顿后重复预览。
- `loop=false` 为单次拒绝事件，`previewLoop=true` 为 GIF 重复预览。播放器应读取 `durations` 数组；动作结束保持正面末帧。
- PNG 最近邻硬边采样，Alpha 仅 0/255；不增加颜色或模糊叠脸。每个转头相位的 Alpha 轮廓与标准化原正面完全一致，头部宽高比例均保持 100%。

## 核验

- 摇头专项：40 组、1000 帧，0 错误。新增逐帧原轮廓/头宽保护检查，原正面相位、固定身体、30° 上限、两次往返和 GIF 各帧时长检查均通过。
- 日常动作专项：60 个对象、162 组、2936 帧，0 错误、0 接缝提示。核对图集与独立单帧、256×256、二值透明度、源颜色/哈希、非空帧和边界。
- 全库：65 对象、920 动作，0 错误、137 提示。其中 40 项为单次事件的 GIF 重复预览，11 项为宠物 GIF 合并停顿帧，其余 86 项来自已有素材。
- 4744 个受保护文件 SHA-256 保持；上一版 1240 个角色资产/元数据已备份并核对。此前签收背面循环的 140 个资产也通过保护检查。
- 已查看 40 人全部 8 页关键姿势，复核回正、两次左右极限、帽子/眼镜/长发与道具周边。浏览器对照页显示 40 张卡片、80 张旧/新图片，已加载图片均为 256×256，无横向溢出。
- 修改的 4 个制作/核验脚本通过语法编译。

机器记录：[摇头专项](validation.json)、[日常专项](../daily-actions/validation.json)、[全库报告](full-validation/asset-validation.md)。

## 修改文件

各 `characters/<角色>/`：`animations/daily/shake_head.png`、`shake_head.gif`、`shake_head/frame_01.png…frame_25.png`、`daily/overview.gif`，以及 `animation.json`、`animation-manifest.json`、`daily/manifest.json`。实际改变 1040 个角色资产/元数据文件；200 个正面相位单帧与上一版相同。本次没有新增动作单帧编号。

修改 `tools/head_turn.py`、`tools/revise_head_turn.py`、`tools/verify_head_turn.py`、`tools/build_daily_actions.py`；更新画廊、日常生成/核验/预览/动作比较/报告、人物工作交接和历史指向说明。完整路径与当前哈希见 changed-files.json。

原角色基础 frame_NN、sprite sheet、点头、交谈、宠物动作和已签收背面素材保持。v3 资产/元数据备份位于 `production/head-turn-rounded-20261003/before/`，改动前源码位于同目录 `code-before/`；废弃样片仅放在 `experiments/`，不作为成品。

```sh
python3 pixel_town_assets/tools/revise_head_turn.py
python3 pixel_town_assets/tools/verify_head_turn.py
python3 pixel_town_assets/tools/verify_daily_actions.py
python3 pixel_town_assets/tools/build_gallery.py
python3 pixel_town_assets/tools/validate_assets.py --output validation/head-turn-rounded/full-validation
```

全量 daily 构建使用同一套轮廓保护方法。交付的是素材与预览；pixel-town-app 未同步或重新打包。

## 仍需人工确认

40 人当前摇头仍待视觉签收，重点看圆度、远近侧五官/耳朵、眼镜和发束在转头时的自然程度。02/19 短发、04/11/13 帽子、08/14/16/35/40 眼镜、10 吉他及 12/33/36/39 发束可重点检查。此前背面走路的用户签收继续有效。

| 角色目录 | 姓名 | 当前摇头确认 |
|---|---|---|
| characters/01_hero_male | 阿澈 | 圆度修正待视觉确认 |
| characters/02_hero_female | 小满 | 圆度修正待视觉确认 |
| characters/03_barista_male | 林屿 | 圆度修正待视觉确认 |
| characters/04_baker_male | 麦麦 | 圆度修正待视觉确认 |
| characters/05_carpenter_male | 大森 | 圆度修正待视觉确认 |
| characters/06_postman_male | 小路 | 圆度修正待视觉确认 |
| characters/07_police_male | 程正 | 圆度修正待视觉确认 |
| characters/08_doctor_male | 许衡 | 圆度修正待视觉确认 |
| characters/09_gardener_male | 阿禾 | 圆度修正待视觉确认 |
| characters/10_musician_male | 迟野 | 圆度修正待视觉确认 |
| characters/11_chef_male | 陈锅 | 圆度修正待视觉确认 |
| characters/12_florist_female | 花音 | 圆度修正待视觉确认 |
| characters/13_pastrychef_female | 糖糖 | 圆度修正待视觉确认 |
| characters/14_teacher_female | 温书 | 圆度修正待视觉确认 |
| characters/15_nurse_female | 苏晴 | 圆度修正待视觉确认 |
| characters/16_librarian_female | 知秋 | 圆度修正待视觉确认 |
| characters/17_cafeowner_female | 沈知 | 圆度修正待视觉确认 |
| characters/18_artist_female | 鹿眠 | 圆度修正待视觉确认 |
| characters/19_vet_female | 安安 | 圆度修正待视觉确认 |
| characters/20_student_female | 夏芽 | 圆度修正待视觉确认 |
| characters/21_firefighter_male | 陆焰 | 圆度修正待视觉确认 |
| characters/22_grocer_male | 周籽 | 圆度修正待视觉确认 |
| characters/23_farmer_male | 田伯 | 圆度修正待视觉确认 |
| characters/24_driver_male | 韩途 | 圆度修正待视觉确认 |
| characters/25_hairdresser_male | 银梳 | 圆度修正待视觉确认 |
| characters/26_baker_male | 陶麦 | 圆度修正待视觉确认 |
| characters/27_librarian_male | 书衡 | 圆度修正待视觉确认 |
| characters/28_mechanic_male | 罗栓 | 圆度修正待视觉确认 |
| characters/29_innkeeper_male | 顾栈 | 圆度修正待视觉确认 |
| characters/30_florist_male | 林苔 | 圆度修正待视觉确认 |
| characters/31_firefighter_female | 岑灯 | 圆度修正待视觉确认 |
| characters/32_grocer_female | 陆杏 | 圆度修正待视觉确认 |
| characters/33_farmer_female | 禾青 | 圆度修正待视觉确认 |
| characters/34_driver_female | 叶驰 | 圆度修正待视觉确认 |
| characters/35_hairdresser_female | 卷云 | 圆度修正待视觉确认 |
| characters/36_barista_female | 闻豆 | 圆度修正待视觉确认 |
| characters/37_carpenter_female | 榆棠 | 圆度修正待视觉确认 |
| characters/38_postal_female | 章铃 | 圆度修正待视觉确认 |
| characters/39_police_female | 许巡 | 圆度修正待视觉确认 |
| characters/40_doctor_female | 余笙 | 圆度修正待视觉确认 |
