# 像素小镇 v0.6.0 完成记录

已安装到 `/Applications/像素小镇.app` 并重新启动。本次完成昼夜时间系统、截图中的知秋侧走残片与偏移修复，以及全库同类问题检查。

## 时间系统与使用

游戏时间固定 06:00 日出、12:00 太阳最高、18:00 日落；夜间显示月亮与星光。日出和日落经过地平线，天空、地面和人物光照随时间平滑变化。

沿用存档的游戏时钟，暂停、倍速和推进五分钟与天体运动同步。点击顶部时钟，可前进到下一次日出、正午、日落或夜晚；不会倒退时间。人物和动物 API 上下文已带入准确时刻和当前光照时段，跳转时间时取消旧时刻的等待回复。

构建包实际 Electron 渲染截图：[日出](</Users/summerwindy/Desktop/AI Chat/pixel-town-app/build/validation/day-night-v0.6.0/sunrise.png>)、[正午](</Users/summerwindy/Desktop/AI Chat/pixel-town-app/build/validation/day-night-v0.6.0/noon.png>)、[日落](</Users/summerwindy/Desktop/AI Chat/pixel-town-app/build/validation/day-night-v0.6.0/sunset.png>)、[月夜](</Users/summerwindy/Desktop/AI Chat/pixel-town-app/build/validation/day-night-v0.6.0/moonlight.png>)。

## 截图问题与同类检查

知秋原 `frame_07.png` 带有邻格人物的头发和鞋底残片；旧切片归一化把它们带入全部 16 帧 `walk_right`，同时使主体偏离脚下定位圈。原 `frame_06.png` 也包含邻格人物。现在各帧使用经过审阅的显示区域，向右走统一水平配准 38 像素；场景、原帧预览和预设主角均采用同一修正。

检查范围为 45 套人物形象和 20 只动物，共 **15477 帧**，其中基础帧 848、动画帧 14629。共修正 **9 位人物、206 帧** 的显示区域与位置：

| 人物 | 素材标识 |
| --- | --- |
| 阿澈 | `01_hero_male` |
| 小满 | `02_hero_female` |
| 林屿 | `03_barista_male` |
| 大森 | `05_carpenter_male` |
| 阿禾 | `09_gardener_male` |
| 温书 | `14_teacher_female` |
| 苏晴 | `15_nurse_female` |
| 知秋 | `16_librarian_female` |
| 安安 | `19_vet_female` |

另以独立的 8 邻域连通检查覆盖全部帧，剩余 23 条候选已逐张查看，属于阿澈白鞋、麦麦和陈锅白帽的正常轮廓，保留原像素。本轮没有未解释的边缘残片候选。此前交接中待确认的闻豆摇头颈部修订仍需视觉确认；本轮检查结论针对串片与位置偏移。

修复采用区域元数据和整数像素配准，**没有改写原 PNG**。帧保持 256×256、透明背景和硬边；主进程核对源文件 SHA-256 后才应用区域，避免后续替换素材时误用旧遮罩。

知秋修复后，以下为构建包实际渲染裁图：

![知秋侧走修复后](</Users/summerwindy/Desktop/AI Chat/pixel-town-app/build/validation/day-night-v0.6.0/librarian-fixed.png>)

## 验证和数据保护

- **106 项单元 / 集成测试通过**。命令：`npm test`。
- `npm run test:time` 在源码及构建包通过：日出、正午、日落、月亮，知秋 16 个走路相位、原帧预览、预设主角，暂停、4 倍速、跨天选择及 1040×720 窗口。
- 预设主角保留 11334 个主体像素的原 RGBA，移除 374 个邻格残片像素，Alpha 仅为 0 / 255。
- `test:renderer`、`test:player`、`test:batch`、`test:api` 回归通过。API 回归使用本地 HTTP / SSE 服务，本轮付费 API 调用 **0**。
- 正式安装与构建包 **2395 个常规文件一致**，27 个运行源码文件与项目一致，`codesign --verify --deep --strict` 通过。
- 新版启动并保存修正元数据；正式存档 **65 个角色档案保留**，原模型绑定、服务商配置、人设、记忆、关系、外观与入住状态均保持。API 累计统计仍为 3，时钟仍为 884.6000000000784，原暂停状态保留，模型自治关闭。
- 原运行素材 2086 个、源素材 18762 个、原 AI Chat 源码 33 个和数据 95 个均通过哈希保护核验。

安装与数据记录：[安装核验](</Users/summerwindy/Desktop/AI Chat/pixel-town-app/build/validation/day-night-v0.6.0/installation.json>)、[正式数据核验](</Users/summerwindy/Desktop/AI Chat/pixel-town-app/build/validation/day-night-v0.6.0/formal-after-install.json>)、[昼夜渲染核验](</Users/summerwindy/Desktop/AI Chat/pixel-town-app/build/validation/day-night-v0.6.0/renderer-result.json>)、[全库扫描](</Users/summerwindy/Desktop/AI Chat/pixel-town-app/build/validation/day-night-v0.6.0/sprite-audit.json>)、[连通检查与人工审阅](</Users/summerwindy/Desktop/AI Chat/pixel-town-app/build/validation/day-night-v0.6.0/component-audit.json>)。

## 修改文件

共 22 个源代码、测试、元数据和文档文件；SHA-256 清单见 [changed-files.json](</Users/summerwindy/Desktop/AI Chat/pixel-town-app/build/validation/day-night-v0.6.0/changed-files.json>)。验证输出和截图另存于本报告所在目录。

| 文件 | 变更 |
| --- | --- |
| [main/preload.js](</Users/summerwindy/Desktop/AI Chat/pixel-town-app/main/preload.js>) | 修改 |
| [main/main.js](</Users/summerwindy/Desktop/AI Chat/pixel-town-app/main/main.js>) | 修改 |
| [main/engine.js](</Users/summerwindy/Desktop/AI Chat/pixel-town-app/main/engine.js>) | 修改 |
| [main/animals.js](</Users/summerwindy/Desktop/AI Chat/pixel-town-app/main/animals.js>) | 修改 |
| [main/assets.js](</Users/summerwindy/Desktop/AI Chat/pixel-town-app/main/assets.js>) | 修改 |
| [renderer/index.html](</Users/summerwindy/Desktop/AI Chat/pixel-town-app/renderer/index.html>) | 修改 |
| [renderer/environment.css](</Users/summerwindy/Desktop/AI Chat/pixel-town-app/renderer/environment.css>) | 新增 |
| [renderer/app.js](</Users/summerwindy/Desktop/AI Chat/pixel-town-app/renderer/app.js>) | 修改 |
| [renderer/environment.js](</Users/summerwindy/Desktop/AI Chat/pixel-town-app/renderer/environment.js>) | 新增 |
| [shared/world-time.js](</Users/summerwindy/Desktop/AI Chat/pixel-town-app/shared/world-time.js>) | 新增 |
| [shared/preset-avatar.js](</Users/summerwindy/Desktop/AI Chat/pixel-town-app/shared/preset-avatar.js>) | 修改 |
| [shared/sprite-regions.js](</Users/summerwindy/Desktop/AI Chat/pixel-town-app/shared/sprite-regions.js>) | 新增 |
| [scripts/renderer.test.cjs](</Users/summerwindy/Desktop/AI Chat/pixel-town-app/scripts/renderer.test.cjs>) | 修改 |
| [scripts/world-time.test.js](</Users/summerwindy/Desktop/AI Chat/pixel-town-app/scripts/world-time.test.js>) | 新增 |
| [scripts/audit-sprite-regions.py](</Users/summerwindy/Desktop/AI Chat/pixel-town-app/scripts/audit-sprite-regions.py>) | 新增 |
| [scripts/inspect-sprite-components.py](</Users/summerwindy/Desktop/AI Chat/pixel-town-app/scripts/inspect-sprite-components.py>) | 新增 |
| [scripts/environment-renderer.cjs](</Users/summerwindy/Desktop/AI Chat/pixel-town-app/scripts/environment-renderer.cjs>) | 新增 |
| [scripts/test-environment-renderer.js](</Users/summerwindy/Desktop/AI Chat/pixel-town-app/scripts/test-environment-renderer.js>) | 新增 |
| [package.json](</Users/summerwindy/Desktop/AI Chat/pixel-town-app/package.json>) | 修改 |
| [README.md](</Users/summerwindy/Desktop/AI Chat/pixel-town-app/README.md>) | 修改 |
| [HANDOVER.md](</Users/summerwindy/Desktop/AI Chat/pixel-town-app/HANDOVER.md>) | 修改 |
| [assets/sprite-regions.json](</Users/summerwindy/Desktop/AI Chat/pixel-town-app/assets/sprite-regions.json>) | 新增 |

## 备份与后续素材更新

旧 v0.5.0 应用、修改前源码和正式数据已备份到：

`/Users/summerwindy/Desktop/AI Chat/pixel-town-app/backups/day-night-v0.6.0-20261004-143649`

旧应用保存在其中的 `installed-replaced-v0.5.0.app`。以后替换源素材后，重新运行 `scripts/audit-sprite-regions.py` 和 `scripts/inspect-sprite-components.py`，查看候选图后更新区域元数据；不能直接删除最大连通块以外的全部像素，因为白鞋与白帽也可能独立成块。
