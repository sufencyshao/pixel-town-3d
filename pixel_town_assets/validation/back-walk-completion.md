# 背面走路帧补全记录

日期：2026-10-03。范围：`人物工作交接.md` 中的 01～20 号角色，共替换 40 张帧图。

**人工验收：全部通过。** 用户于 2026-10-03 明确回复“全部确认”，本次 20 个角色及先前列出的重点复核项均已确认。待人工确认角色：无。版本绑定记录见 `back-walk-approval.json`，保存当前帧和动画哈希。

## 结果与素材来源

`frame_10.png` 为原背面站立帧；`frame_11.png`、`frame_12.png` 现为背面走路两步，四相位循环为 **10→11→10→12**，每相位 160 ms，总时长 640 ms。

检查了 19 张 `raw_v2` 原始 2048×2048、4×4 sprite sheet：第 10 格是背面站立，第 11/12 格多数为正面欢呼，06 邮差与 17 店长等含背面抬手，但并非正常走路。02 女主角没有对应的 `raw_v2` sheet，使用现有切片与背面动画作为事实源。

后续已有 `tools/animate_existing.py` 生成的 16 帧 `animations/walk_up.png`。本次切出零基相位 2、10（人类计数第 3、11 帧），包含相反的摆臂/腿部动作和交替抬脚。统一按 `frame_10` 的角色尺度、位置逆向对齐，使用最近邻采样，避免每一步单独 trim 造成身高和落脚点跳变。头部区域直接复用各角色自己的 `frame_10`，保留白厨师帽顶的轮廓。没有使用生成式重绘或新颜色。

每张 PNG 为 256×256 RGBA，Alpha 只有 0/255。PNG 是交付事实源；GIF 是使用有限调色板的动作预览，不能用于颜色精度验收。网页/接触表上的底色仅为展示透明度，角色 PNG 背景是真透明。

原始 sheet、切片脚本、`frame_10` 及其余 13 张基础帧保持原字节；已有连续 16 帧 `walk_up`、欢呼及其他动画文件保持原字节。旧 11/12 各自备份在 `legacy_actions/`，欢呼的两份 manifest 源路径已改为 `legacy_actions/frame_11.png`，所有哈希已同步。

## 检查结果

- `python3 pixel_town_assets/tools/verify_back_walk.py`：20 角色、40 替换帧，0 错误。检查尺寸、Alpha、无新增不透明颜色、画布边缘、相位来源可重建、循环顺序/时长、备份哈希、双 manifest 一致性。
- `python3 pixel_town_assets/tools/verify_existing_animations.py`：20 角色、220 动作、3520 动画帧，0 错误。源哈希、透明 GIF、帧数/总时长与循环闭合均通过。
- 临时目录重建 01 男主：欢呼图集、背面连续图集、补全的 11/12 与交付版本字节一致，验证重新构建不会把走路当成欢呼。
- 对全部 20 角色再次执行补全：160 个输出/备份文件字节一致。三个修改/新增脚本通过 Python 语法编译。
- 逐页检查了全部 20 角色接触表。技术通过不能替代动作审美验收；本次保留原美术与原调色板，并未解决原图所有造型/透明洞问题。

## 已确认的视觉复核记录

下表保留验收前的重点提示，用户已统一确认当前版本；这些条目不再是待确认事项。原素材特征与限制按记录保留。

| 角色 | 已确认的原复核内容 |
|---|---|
| 02_hero_female | 参考图本尊；裙摆和花纹随动作变形，确认原参考气质与步幅；缺独立 raw_v2 sheet。 |
| 04_baker_male | 白帽顶轮廓已复用原帧保留，但原帽内白色区域已有透明缺口，确认是否需另行补色；原 16 帧连续动画仍有帽顶缺失。 |
| 08_doctor_male | 长白外套遮挡腿部，确认两步读作行走而非侧向摆动；新帧选较温和相位规避极端相位的腿间碎点。 |
| 10_musician_male | 斜背吉他和背带沿用既有动画变形，需确认是否应作为刚性附件保持形状。 |
| 11_chef_male | 同 04 的白厨师帽透明区域；原 16 帧连续动画仍有帽顶缺失。 |
| 12_florist_female | 长裙/花束遮挡手腿；确认裙摆和花束能接受当前相位变形。 |
| 13_pastrychef_female | 短裙摆、双丸子与小帽；确认裙摆运动和抬脚幅度。 |
| 14_teacher_female | 长发、浅色裙装，脚部动作较小，确认最终缩小显示仍有走路辨识度。 |
| 15_nurse_female | 短裙与护士帽，确认双腿交替和裙摆幅度。 |
| 16_librarian_female | 长裙与发髻，确认裙摆形变和腿部辨识度。 |
| 17_cafeowner_female | 围裙/裙摆轮廓随相位变形；确认动作与服装一致性。 |
| 20_student_female | 大背包、短裙遮挡躯干，确认背包形变和步伐幅度。 |

其余 01、03、05、06、07、09、18、19 号角色也已获得用户确认。四帧关键循环来自已有骨骼动画，存在侧向摆动成分，不能宣称为新手绘的纵深步态。

## 修改与新增文件

每个以下目录均：**修改** `frame_11.png`、`frame_12.png`、`animation.json`、`animation-manifest.json`；**新增** `legacy_actions/frame_11.png`、`legacy_actions/frame_12.png`、`animations/back_walk_keys.png`、`animations/back_walk_keys.gif`。

```
characters/01_hero_male
characters/02_hero_female
characters/03_barista_male
characters/04_baker_male
characters/05_carpenter_male
characters/06_postman_male
characters/07_police_male
characters/08_doctor_male
characters/09_gardener_male
characters/10_musician_male
characters/11_chef_male
characters/12_florist_female
characters/13_pastrychef_female
characters/14_teacher_female
characters/15_nurse_female
characters/16_librarian_female
characters/17_cafeowner_female
characters/18_artist_female
characters/19_vet_female
characters/20_student_female
```

其他修改/新增文件（均相对于 `pixel_town_assets/`）：

| 文件 | 作用 |
|---|---|
| `tools/animate_existing.py`（修改） | 提取公共源清理函数；欢呼读取旧备份；重建时重施背面帧补全。 |
| `tools/complete_back_walk.py`（新增） | 可重复执行的源图集切片与帧对齐流程。 |
| `tools/verify_back_walk.py`（新增） | 本次补全专项核验。 |
| `人物工作交接.md`、`characters/README.md`（修改） | 更新帧命名、待办状态与操作说明。 |
| `validation/back-walk-approval.json`（新增） | 用户确认原文、验收日期、20 个角色当前帧与动画哈希；内容发生变化时不沿用旧签收。 |
| `validation/back-walk-baseline.json`（新增） | 修改前的帧、动画文件、原始 sheet 与切片脚本哈希基线。 |
| `validation/back-walk-validation.json`（新增） | 验证结果和逐一列出的 40 张替换帧。 |
| `validation/back-walk-keys-page-1.png`～`4.png`（新增） | 20 角色的原尺寸四相位接触表。 |
| `validation/back-walk-preview.html`（新增） | 20 角色的关键循环、原连续动画与三帧并排预览。 |
| `validation/back-walk-completion.md`（新增） | 本报告。 |

`tools/existing-animation-validation.json` 已重新生成，记录 220 个现有动作的核验结果（0 错误）。检查过程中产生的临时比较图片已移除。

## 后续操作

在项目根目录运行：

```bash
python3 pixel_town_assets/tools/complete_back_walk.py
python3 pixel_town_assets/tools/verify_back_walk.py
python3 pixel_town_assets/tools/verify_existing_animations.py
```

备份只在首次执行建立，后续不覆盖。若要重切原始 sprite sheet，可使用原切片脚本，之后再执行上述补全流程。

本次更新的是源素材包，未同步/重新打包 `pixel-town-app`。应用部分旧的单帧欢呼回退仍直接读取 11/12；向应用发布这些基础帧前，应将这些消费者的欢呼源改为旧帧备份/现有 cheer 图集，并确保备份文件随应用发布。此次现有应用副本未受影响。
