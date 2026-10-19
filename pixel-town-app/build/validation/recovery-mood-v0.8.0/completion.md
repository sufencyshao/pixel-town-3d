# 像素小镇 v0.8.0 完成记录

已安装并启动 `/Applications/像素小镇.app` v0.8.0。正式小镇继续自主运行；沿用六位居民现有 DeepSeek 绑定、各自 Tokens/Temperature、60 秒自动任务间隔与每日 100 次逻辑调用上限。

## 行为、心情与对话

- 新增偷懒、打盹、躺下，可由 API 在日常决策中主动选择；本地人物按疲劳、工作压力、夜晚和个人性格选择。默认持续 12 / 25 / 90 游戏分钟，各有不同恢复速度，到达后才恢复。
- 精力和心情分开。工作、休息、爱好、实际听到的关心/伤害与附近公开行为影响感受，并记入个人每日日志。普通分歧不会一律当成侮辱，私人心声不传播给邻居。
- 性格和兴趣影响独处、向熟人倾诉、分享、投入爱好或运动的倾向；模型获得自己的近期原因与变化，可自行改变主意。心情自评与动作在原本同一次 API 回复中返回，没有新增评价请求。
- 人物互动条新增「心情」，显示心情/压力/精力、原因、个人倾向、最近感受及每日记录入口。存档与重启保留。
- 移除一段最多六轮的限制。双方愿意就继续，任一方不愿继续则结束；每次继续计入现有每日额度。暂停、控制、配置变化、错误和额度不足仍停止继续。
- 修正等待调度时持续扣精力和疲劳反复拖低心情的问题。自动休息预留附近空位，休息区拥挤时会实际走到空位，也处理重启中已在休息/等待的人物；手动摆放保留指定位置。

## 验证

- 145 项单元/IPC 检查全部通过，包括低落独处与熟人倾诉、正向个体差异、言语与见闻影响、保存失败保护、等待状态、休息空位、九轮交流和第七轮等待时暂停取消。
- 人物/动物渲染、主角、批量配置、API 表达、昼夜、自主目标与日志的 Electron 回归通过。
- 最终构建包用本地 HTTP/SSE + 隔离存档验证：自动打盹、精力恢复、同次心情自评、九轮对话自主结束、日志筛选、小窗口与完整重启。10 次本地 HTTP 请求，付费 API 0 次。
- 检查 40 位常规人物 + 5 位伙伴的 135 个休息姿势，逐个加载，并逐张查看九张对照图。使用现有完整人物像素，透明 256×256 输出与整数转向，脖肩保持相连。
- 安装包深层严格签名校验通过（本机临时签名）；安装与构建包的 2405 个常规文件相同，39 个运行源码/配置/文档文件与项目相同。

真实 API 观察分段记录：

| 阶段 | 逻辑调用 | 成功执行 | 失败 | 等待/未执行 |
| --- | ---: | ---: | ---: | ---: |
| 初次新版本试运行 | 8 | 7 | 1 | 0 |
| 等待消耗修正后 | 18 | 18 | 0 | 0 |
| 最终空位修正后 | 9 | 9 | 0 | 0 |

这些是正式应用自行发起的请求，没有点击「让 TA 想一想」、强制休息或发送测试对白。已观察到人物夜间主动选择躺下、精力恢复与独立心情原因，随后继续职业/爱好安排；现场心情记录包含睡眠、散步和模型自评。真实对话超过六轮的证据采用隔离服务，不把本地模拟说成真实服务商长聊。

初次试运行中有一次 JSON 格式错误，已按原机制记录并等待后续决策；没有编造回复。官方 DeepSeek 的结构化生活请求现显式使用非思考模式/JSON 输出，保持用户保存的输出上限。依据 [官方 Chat Completions 文档](https://api-docs.deepseek.com/api/create-chat-completion/)。旧版空回复没有保存完整结束原因，不能据此确证具体成因。

结果：[verification.json](verification.json)、[构建包结果](bundle/renderer-result.json)、[正式最终观察](real-api-final-observation.json)、[签名记录](installed-signature.log)。

## 修改文件

修改 20 个源码/文档文件，新增 8 个，删除 0 个。完整清单见 [changed-files.json](changed-files.json)。

| 文件组 | 用途 |
| --- | --- |
| `shared/emotions.js`（新增） | 心情、压力、个人应对倾向、活动/言语/见闻影响及本地选择 |
| `shared/recovery-poses.js`、`renderer/recovery.js`（新增） | 整帧休息姿态、透明像素输出及播放缓存 |
| `renderer/emotions.js` / `.css`（新增） | 个人心情界面与日志入口 |
| `main/engine.js`、`main/catalog.js`、`main/persistence.js` | 自动休息、心情执行/保存、空位、等待状态与不限固定轮数交流 |
| `main/character-behavior.js`、`main/life-context.js`、`shared/actions.js`、`shared/life.js`、`main/llm.js` | 动作能力、个人情绪资料与同次 API 协议、官方 DeepSeek 参数 |
| `main/journal.js`、`renderer/life.js`、`renderer/app.js`、`renderer/animation.js`、`renderer/player-customizer.js`、`renderer/index.html` | 心情日志筛选、人物/主角动作和界面接入 |
| `scripts/emotions.test.js`、休息/心情 Electron 验证脚本（新增）及现有测试 | 行为、心情、长对话、布局与重启验收 |
| `package.json`、`README.md`、`HANDOVER.md` | v0.8.0 版本、操作和交接 |

另为 v0.7.0 完成报告追加已解除系统授权等待、后续自主生活已运行的观察说明。

## 文件保留与当前视觉边界

- 2087 个运行素材、18785 个源素材文件逐个 SHA-256 未改变；纳入基线的原 AI Chat 17 个源码与 95 个数据文件未改变。
- 正式居民/动物的身份、人设、模型、外观、入住状态、世界资料和服务商配置保留；密钥继续加密保存。已有统计前缀和 98 份 JSONL 日志内容保留，新的实际经历继续追加。
- 休息姿势复用原坐姿/等候和完整侧身帧，打盹带轻微呼吸与像素 Z，卧姿为整体四分之一转向并配垫子。本轮没有逐角色新画闭眼、弯膝、躺下/起身过渡；部分 Mini 的等候帧带原有道具。这些属于后续美术精修项，当前动作和保存可以直接使用。
- 保持原图与现有颈肩连接。既有摇头美术签收状态仍以素材交接为准，本轮没有重画摇头，也没有宣称重新签收全部原动画。
- 没有新增实体睡床、全场碰撞或寻路；空位处理用于自动休息。职业产出、建筑、物品与经济仍是既有未实现范围。

备份（修改前源码、旧应用与每次替换前正式数据）：

`/Users/summerwindy/Desktop/AI Chat/pixel-town-app/backups/recovery-mood-v0.8.0-20261004-185507`

## 查看结果

- [正式心情界面](installed-mood.png)、[正式场景](installed-scene.png)
- [自动打盹/心情测试界面](bundle/mood-dialog.png)、[卧姿场景](bundle/lying-in-town.png)、[心情日志](bundle/emotion-journal.png)
- 逐角色姿态：[01](bundle/pose-review-01.png)、[02](bundle/pose-review-02.png)、[03](bundle/pose-review-03.png)、[04](bundle/pose-review-04.png)、[05](bundle/pose-review-05.png)、[06](bundle/pose-review-06.png)、[07](bundle/pose-review-07.png)、[08](bundle/pose-review-08.png)、[09](bundle/pose-review-09.png)
