# 虎斑猫新增姿势生成记录

日期：2026-10-03；工具：内置 `image_gen`，通过 `imagegen` 技能使用。透明背景请求为 true。

参考/编辑目标：`pets/01_cat_tabby/frame_01.png`。生成原图保存在本目录 `01_cat_tabby-stretch-sleep-source.png`，角色自包含副本为 `pets/01_cat_tabby/source/daily-tabby-poses.png`。原站姿没有覆盖。

请求 1024×1024；实际返回 **1254×1254 RGBA**。整理脚本读取实际尺寸划分 4×4 单元，不假设模型严格遵守请求尺寸；统一缩放、脚点对齐、64×64 逻辑像素最近邻放大到 256×256，使用同一组 32 色导出调色板，Alpha 二值化。生成图可能包含半透明边缘，成品帧没有半透明像素。

## 发送给工具的完整 prompt

```text
Use case: game-asset sprite-sheet expansion. Input image 1 is the EXACT identity and pixel art style reference for town pet 01_cat_tabby, a natural brown-and-black striped tabby cat facing right, four-legged, ears pointed, black tail rings, small cream muzzle. Create ONE square 1024x1024 sprite sheet containing a strict 4 by 4 equal cell grid, 16 cells of 256x256, no grid lines, no labels, no text, no ground or shadow, genuinely transparent RGBA background. All sprites entirely inside their cells with ample transparent padding. Same natural cat anatomy, coat, pixel art, proportions and right-facing orientation as input, never anthropomorphic. Render at a coarse 64px logical pixel grid per cell enlarged 4x nearest-neighbor: flat colored pixel clusters, crisp stair-step edges, no anti-aliasing, no gradients, no blur. Sprite feet baseline about y=232 inside each cell, body maximum width about 205px, consistent scale in ALL cells, never recenter or rescale during an action. Top two rows (cells 1-8) show ONE complete stretch action: cell1 neutral standing, cell2 starts lowering chest, cell3 forelegs extend forward and hindquarters stay high, cell4 clear full feline bow stretch, cell5 full stretch hold, cell6 chest starts lifting, cell7 returning to neutral, cell8 same neutral stance as cell1 for seamless single-action completion. Bottom two rows (cells9-16) show eight gentle breathing phases of a natural CLOSED-EYED curled-up sleeping cat, tail wrapped close around body, paws tucked naturally, no extra limbs, no human gesture, no floating body parts. First and last sleep phases match for looping. Preserve stripes and body identity across poses. Only expand the referenced cat into these new poses; do not invent another cat, backgrounds or accessories.
```
