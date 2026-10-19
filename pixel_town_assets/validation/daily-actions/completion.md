# 人物与宠物日常动作扩展

日期：2026-10-03。现有 40 位人物、20 只自然动物；本批新增 **162 组动作、2936 张 256×256 透明 RGBA 帧**。Codexmini 原作未扩展。

[打开本批动态预览](preview.html)；[打开完整素材画廊](../../asset-gallery.html)。

## 本批动作

| 范围 | 新增动作 | 数量 |
|---|---|---:|
| 40 位人物 | 点头 nod、摇头 shake_head、交谈手势 chat | 120 |
| 5 只猫 | 摆尾 wag、低幅扑动 pounce | 10 |
| 6 只狗 | 摆尾 wag、舒展 stretch | 12 |
| 4 只鸟 | 啄食 peck、跳步 hop | 8 |
| 2 只兔 | 短跳 hop、啃咬 chew | 4 |
| 豚鼠 | 觅食 forage、啃咬 chew | 2 |
| 陆龟 | 晒暖探头 bask、觅食 forage | 2 |
| 矮马 | 摆尾 wag、采食 graze | 2 |
| 虎斑猫额外新姿势 | 完整舒展 stretch、闭眼蜷睡 sleep | 2 |

人物点头/交谈各 16 帧、90 ms/帧；摇头拒绝现为 25 帧，前 24 帧各 30 ms、回正末帧 480 ms，两次左右往返共 720 ms，GIF 含回正停顿共 1200 ms；程序宠物动作 16 帧，80 ms/帧（陆龟为 130 ms/帧）。虎斑猫的新姿势各 8 帧，舒展为 160 ms/帧，蜷睡为 200 ms/帧。所有动作图集从左到右排列，PNG 是完整颜色/Alpha 事实源，GIF 用于独立预览。

## 制作方法与质量边界

120 组动作（人物点头/交谈与宠物程序动作）扩展项目现有的像素分区骨骼代码，重用每个人物/动物自身原始 frame_01 的不透明像素与颜色；最近邻采样。40 组摇头按用户最新反馈改为左右各约 30°、快速摇两下后回正，参考原正面和左右方向素材补画整头关键姿势，头发、耳朵、脸和配饰同步转向，原身体复用。当前 v7 独立标定原下巴与颈根，头颅和脖子分别配准，原衣服作为稳定底层，头发自然遮挡肩膀；章铃/许巡补齐发型遮住的肩顶，长辫保留原图细节。详见 [当前全角色颈肩修正记录](../head-turn-anatomy/completion.md)。36 人回正相位精确复用原正面；章铃/许巡保留原头部并叠到修补后的身体；两位厨师沿用匹配白帽回正姿势。人物点头为头部下沉/轻压缩，交谈为头/手臂交错运动，保留原嘴型，不包含口型同步。

宠物按物种分配动作，维持四足或鸟类双足形态。扑动/跳步是低幅弹跳近似；狗舒展是现站姿的前躯低伏近似，不能当作新手绘的完整伸腿姿势。啃咬没有增加食物道具；觅食/采食/啄食表现局部头部动作，场景食物交互未模拟。摆尾、嘴部细动或陆龟探头在很小的显示尺寸下可能较轻，需要按实际游戏尺寸确认。

虎斑猫的舒展/蜷睡两组使用 imagegen 技能调用内置图像工具，新增实际姿势图；舒展包含前腿伸出、后躯抬高和回到站姿，蜷睡闭眼。原图、完整 prompt、实际尺寸与整理流程见 [生成记录](../../production/action-expansion-20261003/imagegen-prompt.md)。成品使用同一组 32 色、64×64 逻辑像素、4 倍最近邻导出；没有生成式插帧。原生成图的同一动作姿势/花纹仍可能存在细微差别，需要确认。

## 验证与原资产保护

- 专项检查：60 个对象、162 新动作、2936 帧，0 错误、0 循环提示。核对图集和逐帧一致性、透明 GIF、总时长、源哈希、原色复用、64px 逻辑网格、非空帧和边界裁切。
- 全库检查（v7 颈肩修正后）：65 个对象、920 动作，0 错误、137 提示。40 组摇头是单次事件配置、GIF 为重复预览；11 组宠物 GIF 合并连续停顿帧且总时长正确；其余 86 个提示来自已有素材。最新报告在 validation/head-turn-anatomy/full-validation/；本目录的全库报告保留首批的历史结果。
- 原素材哈希保护：2464 个基础帧/原动画/原始 sheet/旧备份及背面签收记录没有改变；已签收背面循环的 140 个受保护资产哈希全部保持。
- 原 20 人的 220 个基础动作重新核验通过；背面补全 40 帧重新核验通过。
- 在临时目录重建男主原动画，三个新动作仍留在清单中，且新图集字节未变；新动作 sidecar 防止旧构建流程覆盖动作元数据。
- 新增/修改的六个 Python 脚本通过语法编译。
- 浏览器预览核对 60 张卡片、162 个动作选项，无横向溢出；虎斑猫切换蜷睡后加载 256×256 GIF。
- 已查看 40 人全部三动作的源姿势/关键相位比较页、20 只动物新动作的关键相位比较页，以及虎斑猫舒展/蜷睡全部 8 帧。未声称逐帧人工观看全部 2936 帧。

## 人工确认状态

**这批新动作尚未得到用户视觉签收；之前背面走路的“全部确认”仍只属于先前那一批。摇头旧版被用户指出像钟摆，已替换为整个头部一起转动、约 ±30°、0.72 秒内快速摇两下后回正的版本，40 人 v7 已完成制作侧七姿势复查，尚待用户最终签收，名单及各自复核重点见当前修正报告。**

重点确认：虎斑猫新姿势的条纹/体型与原站姿一致性、6 只狗舒展近似的辨识度、16/17 兔子的短跳和啃咬、18 豚鼠/19 陆龟细小动作、20 矮马的头颈和尾部运动。人物中 10 乐手的吉他、12 花店店主花束、14/16 手持书本、18 画家画板可能随分区出现形变，建议重点确认；其余人物仍需要统一检查点头/摇头/交谈幅度。

## 文件位置与修改清单

所有角色新增文件都在 `animations/daily/`：每动作 `<action>.png` 横向图集、`<action>.gif`、`<action>/frame_01.png…` 单帧；独立 `manifest.json` 保存本批源哈希；`overview.gif` 仅展示本批动作。原有 `overview.gif` 仍展示旧动作，素材画廊可单独选择所有新动作。

人物更新 animation.json 和 animation-manifest.json；宠物更新 animation.json、profile.json 物种白名单、profile.md 动作记录。基础 frame_NN 与旧动作图片没有覆盖。

| 类别 / 目录 | 本批动作 |
|---|---|
| characters/01_hero_male | nod（点头）, shake_head（摇头）, chat（交谈手势） |
| characters/02_hero_female | nod（点头）, shake_head（摇头）, chat（交谈手势） |
| characters/03_barista_male | nod（点头）, shake_head（摇头）, chat（交谈手势） |
| characters/04_baker_male | nod（点头）, shake_head（摇头）, chat（交谈手势） |
| characters/05_carpenter_male | nod（点头）, shake_head（摇头）, chat（交谈手势） |
| characters/06_postman_male | nod（点头）, shake_head（摇头）, chat（交谈手势） |
| characters/07_police_male | nod（点头）, shake_head（摇头）, chat（交谈手势） |
| characters/08_doctor_male | nod（点头）, shake_head（摇头）, chat（交谈手势） |
| characters/09_gardener_male | nod（点头）, shake_head（摇头）, chat（交谈手势） |
| characters/10_musician_male | nod（点头）, shake_head（摇头）, chat（交谈手势） |
| characters/11_chef_male | nod（点头）, shake_head（摇头）, chat（交谈手势） |
| characters/12_florist_female | nod（点头）, shake_head（摇头）, chat（交谈手势） |
| characters/13_pastrychef_female | nod（点头）, shake_head（摇头）, chat（交谈手势） |
| characters/14_teacher_female | nod（点头）, shake_head（摇头）, chat（交谈手势） |
| characters/15_nurse_female | nod（点头）, shake_head（摇头）, chat（交谈手势） |
| characters/16_librarian_female | nod（点头）, shake_head（摇头）, chat（交谈手势） |
| characters/17_cafeowner_female | nod（点头）, shake_head（摇头）, chat（交谈手势） |
| characters/18_artist_female | nod（点头）, shake_head（摇头）, chat（交谈手势） |
| characters/19_vet_female | nod（点头）, shake_head（摇头）, chat（交谈手势） |
| characters/20_student_female | nod（点头）, shake_head（摇头）, chat（交谈手势） |
| characters/21_firefighter_male | nod（点头）, shake_head（摇头）, chat（交谈手势） |
| characters/22_grocer_male | nod（点头）, shake_head（摇头）, chat（交谈手势） |
| characters/23_farmer_male | nod（点头）, shake_head（摇头）, chat（交谈手势） |
| characters/24_driver_male | nod（点头）, shake_head（摇头）, chat（交谈手势） |
| characters/25_hairdresser_male | nod（点头）, shake_head（摇头）, chat（交谈手势） |
| characters/26_baker_male | nod（点头）, shake_head（摇头）, chat（交谈手势） |
| characters/27_librarian_male | nod（点头）, shake_head（摇头）, chat（交谈手势） |
| characters/28_mechanic_male | nod（点头）, shake_head（摇头）, chat（交谈手势） |
| characters/29_innkeeper_male | nod（点头）, shake_head（摇头）, chat（交谈手势） |
| characters/30_florist_male | nod（点头）, shake_head（摇头）, chat（交谈手势） |
| characters/31_firefighter_female | nod（点头）, shake_head（摇头）, chat（交谈手势） |
| characters/32_grocer_female | nod（点头）, shake_head（摇头）, chat（交谈手势） |
| characters/33_farmer_female | nod（点头）, shake_head（摇头）, chat（交谈手势） |
| characters/34_driver_female | nod（点头）, shake_head（摇头）, chat（交谈手势） |
| characters/35_hairdresser_female | nod（点头）, shake_head（摇头）, chat（交谈手势） |
| characters/36_barista_female | nod（点头）, shake_head（摇头）, chat（交谈手势） |
| characters/37_carpenter_female | nod（点头）, shake_head（摇头）, chat（交谈手势） |
| characters/38_postal_female | nod（点头）, shake_head（摇头）, chat（交谈手势） |
| characters/39_police_female | nod（点头）, shake_head（摇头）, chat（交谈手势） |
| characters/40_doctor_female | nod（点头）, shake_head（摇头）, chat（交谈手势） |
| pets/01_cat_tabby | wag（摆尾）, pounce（扑动）, stretch（舒展）, sleep（蜷睡） |
| pets/02_cat_calico | wag（摆尾）, pounce（扑动） |
| pets/03_cat_british_blue | wag（摆尾）, pounce（扑动） |
| pets/04_cat_siamese | wag（摆尾）, pounce（扑动） |
| pets/05_cat_maine | wag（摆尾）, pounce（扑动） |
| pets/06_dog_corgi | wag（摆尾）, stretch（舒展） |
| pets/07_dog_shiba | wag（摆尾）, stretch（舒展） |
| pets/08_dog_border | wag（摆尾）, stretch（舒展） |
| pets/09_dog_golden | wag（摆尾）, stretch（舒展） |
| pets/10_dog_dachshund | wag（摆尾）, stretch（舒展） |
| pets/11_dog_poodle | wag（摆尾）, stretch（舒展） |
| pets/12_bird_budgie_green | peck（啄食）, hop（跳步） |
| pets/13_bird_budgie_blue | peck（啄食）, hop（跳步） |
| pets/14_bird_cockatiel | peck（啄食）, hop（跳步） |
| pets/15_bird_canary | peck（啄食）, hop（跳步） |
| pets/16_rabbit_lop | hop（跳步）, chew（啃咬） |
| pets/17_rabbit_dutch | hop（跳步）, chew（啃咬） |
| pets/18_guineapig_rosette | forage（低头觅食）, chew（啃咬） |
| pets/19_tortoise_hermann | bask（晒暖探头）, forage（低头觅食） |
| pets/20_pony_shetland | wag（摆尾）, graze（低头采食） |

其他新增/修改：

- tools/build_daily_actions.py、tools/verify_daily_actions.py：本批制作和专项检查。
- tools/animate_existing.py、tools/build_animal_animations.py：旧构建流程保留本批独立动作清单；动物旧构建不再错误地用待机回退生成新动作。
- tools/verify_existing_animations.py：原动作的高独立帧数门槛只检查原 11 类动作；新动作的停顿帧/总时长另行专项核验。
- tools/build_gallery.py、asset-gallery.html：新增动作中文名称与可播放选项，当前 65 对象、920 动作。
- expansion-guide.md、characters/README.md、人物工作交接.md：追加本批说明。
- production/action-expansion-20261003/：生成原图、prompt、修改前元数据快照。
- pets/01_cat_tabby/source/daily-tabby-poses.png：新姿势原图的自包含副本。
- validation/daily-actions/：基线、生成/核验 JSON、完整核验输出、12 页采样、12 页动作比较、动态预览、本报告、逐文件清单。

可机器读取的首批全路径清单见 changed-files.json；摇头最新变更完整清单见 [head-turn-anatomy/changed-files.json](../head-turn-anatomy/changed-files.json)。

## 重建与使用

```sh
python3 pixel_town_assets/tools/build_daily_actions.py
python3 pixel_town_assets/tools/verify_daily_actions.py
python3 pixel_town_assets/tools/build_gallery.py
python3 pixel_town_assets/tools/validate_assets.py --output validation/daily-actions/full-validation
```

原生成图已经保存，重建不调用图像 API。metadata-before.json 是本批开始前的可读元数据快照，用于核对或手工回退；baseline.json 记录受保护图片的原哈希。

本次交付源素材包和素材画廊，未同步/重打包 pixel-town-app。游戏主程序要使用新人物 nod/shake_head，仍须增加动作白名单和交互入口；chat 已是游戏动作，但应用副本需要同步新图集。宠物新动作已有游戏动作名称支持，发布时要同步新 profile 和图集。新动作尚未接入自主行为触发/场景互动，不能把图像交付等同于完整游戏功能。

## 闻豆颈部追加修正（2026-10-03）

用户反馈暴露出 v7 中闻豆的颈根标定和原衣料检查样本错误，已独立纠正为 `20261003-wendou-joint-v1`。现在原 V 领颈根及衣领下缘在 25 相位保持原形/原位，蓝肩带和米色衣领属于稳定身体。其余39人沿用原资产及上一轮视觉记录；不把本次单角色修正当作全人物的新人工验收结论。见 [最新专项对照](../wendou-joint/preview.html)、[追加报告与清单](../wendou-joint/completion.md)。新摇头最终用户签收仍待记录，原背面签收有效。日常专项仍0错误；全库最新检查仍0错误、137既有提示。
