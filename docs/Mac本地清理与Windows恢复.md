# Mac 本地清理与 Windows 恢复

状态：云端覆盖核对与补传完成，正在执行本机清理；执行结果随后更新。

仓库已按用户明确授权改为公开，未登录也可查看和下载；此前404来自私有仓库权限。

用户要求本机只保留可用 App，后续在 Windows 从 GitHub 下载继续制作。

- 当前独立 Mac 应用安装在 `/Applications/溪畔日常3D.app`，0.9.0；签名检查与独立安装位置启动检查通过，61 个角色载入。现有二维 `/Applications/像素小镇.app` 保留。
- 原 AI Chat 应用和源码不在清理范围。小镇和原 AI Chat 的私人存档、API 配置保留在 macOS Application Support，不上传 GitHub。
- 小镇源码、原始素材、Blender/GLB/离线预览、历史工程、本地 Git 工作副本、下载运行库/重复包、临时预览转入单独的废纸篓目录，不清空用户已有废纸篓。
- 清理前额外核对内容摘要，补传259份此前成品包之外的中间设计、旧源码快照与制作脚本。原始含私有校验清单的旧 ZIP 不重复上传，云端保留已剔除这些清单的发布副本；私人验证快照和运行缓存不作为制作资产上传。
- 云端现为7类35个产品档案，另有7份 SHA256SUMS.txt，42附件的大小和 SHA-256 已统一核对。

## Windows

直接从 [0.9.0 发布](https://github.com/sufencyshao/pixel-town-3d/releases/tag/v0.9.0)下载 Windows 完整便携 ZIP 或完整源码工程 ZIP。前者完整解压后运行 PixelTown3D.exe；后者按包内说明进入 pixel-town-app 继续开发。Windows 包仍未实机验收。

Git 克隆则按仓库 README 使用 tools/restore-assets.py 恢复大资源；历代工程和制作过程从[分类下载](成品下载.md)获取。API 密钥需要重新配置，Mac 私人存档未在仓库中。
