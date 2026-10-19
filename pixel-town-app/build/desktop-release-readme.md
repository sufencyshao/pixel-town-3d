# 溪畔日常3D · 0.9.0

完整三维小镇、45位人物、16个已入镇动物、原版动画、四季昼夜天气、API与人物设置、骨架姿态、室外步道移动、40居民职业练习、实际回执和日志均随包提供。无需单独安装Node.js、Python、Blender或运行本机开发脚本。

## Mac

解压后打开“溪畔日常3D.app”，也可复制到“应用程序”。这是独立名称和Bundle ID，不覆盖原“像素小镇.app”。本次为Apple Silicon（arm64）版本，使用本地临时签名，未做Apple开发者公证。若系统阻止未知来源应用，可在系统设置的“隐私与安全性”中对本应用选择允许打开。

## Windows

将Windows压缩包**完整解压**，双击文件夹中的 `PixelTown3D.exe`。不要只拷贝exe，旁边的DLL、resources、locales均是运行所需。使用Windows 10/11 64位；这份包采用官方Electron x64运行环境，在Mac交叉组装，尚未在Windows实机验收。

## API、存档与原数据

本包不含个人API密钥、聊天或私人存档。自主调用默认关闭，选择人物后可查看完整AI资料再启用。新增服务商/编辑人设可点“API与人物设置”；回到三维窗口后“刷新配置”。

独立数据目录为：Mac `~/Library/Application Support/pixel-town-life-3d-v9/`；Windows `%APPDATA%\pixel-town-life-3d-v9\`。同一系统首次打开且三维存档为空时，只读复制原 `pixel-town-life` 的档案和日志。已有三维数据会继续使用，不重置。原二维应用及其数据不覆盖。

Mac钥匙串和Windows DPAPI不能直接互换已加密API密钥。换电脑/跨系统时，请在新系统重新填写API Key；不要直接覆盖本机加密存档。可用原设置的“不含密钥”导出保存资料；当前没有自动导入跨系统档案的UI。

## 当前能力边界

工作是室外工作点的分阶段职业练习，完成后有真实记录；不是物品生产、交易或真实诊疗。尚无室内/上楼、工具抓取/IK、设备控制、车辆驾驶、完整物理或衣物模拟。无对应步态的动物不滑行冒充走路，其余6个未有合适模型的动物保留档案。

## 在Windows继续开发

另外提供“完整源码工程”压缩包，保留当前主程序、2D设置及运行素材、V8原模型与动画、V9全部源码、可编辑整镇Blender工程、构建/测试脚本和锁定依赖。安装Node.js 22或更新LTS后，在工程目录运行：

```
npm ci
npm run start:3d
npm run build:3d
npm test
npm run package:3d -- --platform win32 --out releases\local-win
```

源码构建已改为跨平台Node脚本，不要求Python或bash。可编辑模型在 `design/whole-town-realistic-actors-v8/Town-with-original-actors.blend`。旧设计探索与历史备份不放入源码包；当前版本所需模型、贴图、骨架和动作均保留。模型来源与署名见同目录 `licenses/`。
