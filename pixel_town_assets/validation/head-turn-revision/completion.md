# 人物摇头修正记录

> 本文保留 v2 完整侧脸版本的历史记录。用户随后要求约 30°、快速摇两下，当前 v4 圆度修正成品与核验见 [最新报告](../head-turn-rounded/completion.md)。本目录 preview.html 已指向当前版本的对照；本目录 GIF、关键姿势页和 JSON 验证记录保留历史结果。

2026-10-03；版本 20261003-shake-yaw-v2。

用户指出旧版人物摇头像钟摆。旧代码让始终朝正面的头部左右平移、倾斜，缺少侧脸朝向变化。本次只重做素材库 40 人的 shake_head，共 640 张帧；点头、交谈、宠物动作及已签收背面素材保持。

[旧版与修正版动态对照](preview.html)；[男主单独对照](hero-before-after.gif)。左侧为旧版，右侧为修正版。8 页 keyposes-N.png 展示全部 40 人的 5 个关键相位。

## 动作与来源

- 循环为正面→左转过渡→原左侧脸→回正→右转过渡→原右侧脸→回正。16 帧、90 ms/帧、总时长 1440 ms；每人有 7 个不同关键姿势，侧脸停顿帧按原时长合并到 GIF。
- 身体保持正面；头部不再整块平移或倾斜。过渡采用横向透视近似，鼻子/眼睛位置改变；极限姿势使用实际原侧脸。没有模糊混合或透明叠脸。
- 正面沿用原 frame_01；左右侧脸沿用 frame_04/07。女主 02 的 frame_04 仍偏正面，所以左侧脸使用 frame_07 的头部镜像；16 图书管理员 frame_07 的邻格残片在提取时排除。原图均未覆盖。
- 按人物设置头颈分界、侧脸缩放和颈部对齐。帽子/眼镜/长发跟随头部。长发遮挡后露出的少量衣服区域复用同一行的原正面衣服像素，颜色不增加；中央躯干和下半身保持原始像素。
- PNG 为 256×256 RGBA 单帧与横向图集，Alpha 仅 0/255；最近邻硬边采样。GIF 仅作透明预览。

## 验证

- 专项：40 组、640 帧，0 错误。正面相位与标准化原正面逐像素一致，所有相位中央躯干与下半身固定；左右极限包含原侧脸头部像素，禁止退回全正面摆动。
- 4744 个受保护文件哈希保持；880 个旧版资产/元数据已备份且哈希一致。与旧版相比，800 个摇头资产/动作元数据文件实际改变，另外 80 个正面单帧字节本来就相同。
- 日常动作专项：60 对象、162 组、2576 帧，0 错误、0 循环提示；三张原方向帧的颜色并集作为摇头原色检查范围。
- 全库：65 对象、920 动作，0 错误、137 提示。40 组摇头和 11 组宠物的提示为 GIF 合并重复停顿帧，总时长正确；其余 86 个提示来自已有素材。
- 浏览器对照显示 40 张人物卡片，两侧 GIF 实际均为 256×256；窄窗口下左右并排、无横向溢出。
- 本次新增/修改的 5 个 Python 脚本通过语法编译。已检查全部角色的方向源姿势及关键姿势比较，重点复核了长发/帽子/眼镜/道具。

## 文件与重建

- 各人物 animations/daily/shake_head.png、shake_head.gif、shake_head/frame_01…16.png：修正素材；daily/overview.gif 同步更新。
- 各人物 animation.json、animation-manifest.json、animations/daily/manifest.json：方向源哈希、关键姿势序列、对齐参数、修正版待签收标记。
- 新增 tools/head_turn.py、tools/revise_head_turn.py、tools/verify_head_turn.py；更新 tools/build_daily_actions.py 和 tools/verify_daily_actions.py。
- 更新素材画廊、日常生成清单/预览/8 页动作比较、日常制作报告及人物工作交接文档。
- production/head-turn-revision-20261003/before/ 保存旧版；validation/head-turn-revision/before.json 保存原哈希。
- 本目录 changed-files.json 为完整修改/新增路径清单；validation.json 和 full-validation/ 为验证报告。

```sh
python3 pixel_town_assets/tools/revise_head_turn.py
python3 pixel_town_assets/tools/verify_head_turn.py
python3 pixel_town_assets/tools/verify_daily_actions.py
python3 pixel_town_assets/tools/build_gallery.py
```

旧 daily 全量构建已使用同一套新摇头方法，重建不会恢复旧的钟摆变形。

## 人工确认与使用边界

40 组修正版仍待本次视觉签收。重点确认 02 女主镜像侧脸的发型、10 乐手道具附近、12 花店店主辫子、15/19/20 长发、33 辫子、35 眼镜及 36/39 发束衔接。原侧脸本身的脸型/表情/发型差异会反映在转头中；中间姿势为横向透视近似，尚未逐角度新绘。

此前背面走路的用户签收继续有效。此次修正素材包与画廊，尚未同步或重打包游戏应用。
