# API 人物表达接入 v0.5.0

已安装至 `/Applications/像素小镇.app`。API 现在在人物生活决策、镇长聊天与人物对话中同时返回动作、心声、台词；每人继续使用自己的模型、人设和记忆。

## 已完成

- 只向模型提供当前形象真实具备的动作；点头一次、摇头约 30° 快速两下，继续使用原图集。
- 心声与台词分开显示，聊天记录保留对应动作；点击人物可使用“让 TA 想一想”。
- 开启模型自主生活后，绑定人物完成当前行为再等待调度；本地随机规则不覆盖模型意图。
- 检查目的地、邀请对象、输出长度与字段；手动接管、移动、离镇、配置变化取消或忽略旧回复；保留调用间隔、每日上限和失败计数。
- 原 AI Chat 配置改为按选项复制，密钥加密存储且不返回界面。按用户授权已复制 DeepSeek 与 grok 两套配置，并给知秋、夏芽、林屿分别绑定。

## 验证结果

98 项单元与集成检查通过。居民渲染验证覆盖 40 人、120 组日常动作；主角和批量分配各 9 组 UI 检查通过。API 界面使用本地真实 HTTP/SSE 测试，验证同一次回复表达动作与台词、摇头结束、点头时长、文本转义和 1040×720 布局。源代码与构建包中的 API UI 测试均通过。

真实服务商测试使用已安装包的引擎与 API 内核、隔离人物状态，没有把测试对白写入正式存档。共 6 次真实 API 逻辑调用（包含兼容排查；逻辑次数不等于 HTTP 尝试次数），结果：

| 人物 / 配置 | 实际结果 |
| --- | --- |
| 夏芽 / DeepSeek deepseek-v4-flash | 成功；选择 rest，返回心声与休息台词 |
| 知秋 / DeepSeek deepseek-v4-flash | 成功；按人设拒绝邀请，选择 shake_head，单次 1200 ms |
| 林屿 / DeepSeek deepseek-v4-flash | 成功；同意咖啡邀请，选择 nod，单次 1440 ms；返回心声与台词 |
| 林屿 / grok grok-4.6，1024 Tokens | 未通过；回复不是可解析 JSON，应用拒绝应用动作 |
| grok-4.6，2048 Tokens 排查 | 未通过；45 秒无响应超时 |
| grok-4.3 排查 | 未通过；中转返回 HTTP 503，无可用模型通道 |

最终落盘核对：知秋、夏芽、林屿均已保存 DeepSeek / deepseek-v4-flash 绑定，可直接使用“让 TA 想一想”或“问问近况”。grok 配置保留，当前中转的三次尝试未通过。本轮没有开启持续的后台付费调用；其余人物的 API 由用户自行添加，已有的批量分配入口也可使用。

## 安装与保护

安装包和构建包 2390 个常规文件完全一致；23 个应用源码文件与项目一致，签名 deep / strict 校验通过。2086 个运行素材和 18785 个源素材文件 SHA-256 保持一致，256×256、透明背景与硬边像素未重新处理。原 AI Chat 的 33 个源码文件和 95 个数据文件均未修改。正式存档仅通过正常应用流程保存配置与人物绑定，没有重建存档。

修改前源码、旧版与正式数据备份：`backups/api-character-behavior-v0.5.0-20261004-094956/`。

修改详情：[changed-files.json](</Users/summerwindy/Desktop/AI Chat/pixel-town-app/build/validation/api-character-behavior-v0.5.0/changed-files.json>)。实际 API 结果：[首轮测试](</Users/summerwindy/Desktop/AI Chat/pixel-town-app/build/validation/api-character-behavior-v0.5.0/live-api-results.json>)、[林屿补测](</Users/summerwindy/Desktop/AI Chat/pixel-town-app/build/validation/api-character-behavior-v0.5.0/lin-deepseek-result.json>)、[最终状态](</Users/summerwindy/Desktop/AI Chat/pixel-town-app/build/validation/api-character-behavior-v0.5.0/live-summary.json>)。安装与素材核验：[installation.json](</Users/summerwindy/Desktop/AI Chat/pixel-town-app/build/validation/api-character-behavior-v0.5.0/installation.json>)、[protected-files.json](</Users/summerwindy/Desktop/AI Chat/pixel-town-app/build/validation/api-character-behavior-v0.5.0/protected-files.json>)。

## 主要修改文件

- `main/character-behavior.js`、`main/engine.js`：统一表达协议、意图控制、动作与调度。
- `main/catalog.js`、`main/persistence.js`：新心声字段与旧档兼容。
- `main/main.js`、`main/preload.js`：选择复制 API 的 IPC 与密钥边界。
- `shared/actions.js`、`renderer/animation.js`：真实动作白名单与 Mini 移动素材选择。
- `renderer/app.js`、`renderer/index.html`、`renderer/styles.css`：思考入口、心声、台词、动作记录与设置状态。
- `scripts/` 中新增行为协议 / API HTTP / 界面检查，并更新相关回归测试。
- `package.json`、`README.md`、`HANDOVER.md`：版本、命令与交接记录。
