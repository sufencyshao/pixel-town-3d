'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const app=path.resolve(__dirname,'..'),workspace=path.dirname(app),version=require('../package.json').version;
const dest=path.resolve(process.argv[2]||path.join(app,'releases',version,'source','PixelTown3D-source'));
if(fs.existsSync(dest))throw new Error('源码输出已经存在，保留原文件，请使用新目录：'+dest);
const cp=(from,to)=>{fs.mkdirSync(path.dirname(to),{recursive:true});fs.cpSync(from,to,{recursive:true,dereference:true,filter:p=>!['node_modules','.DS_Store','__pycache__'].includes(path.basename(p))})};
for(const folder of ['main','renderer','shared','scripts','assets'])cp(path.join(app,folder),path.join(dest,'pixel-town-app',folder));
for(const file of ['package.json','package-lock.json','README.md','HANDOVER.md'])cp(path.join(app,file),path.join(dest,'pixel-town-app',file));
for(const file of ['town.icns','desktop-release-readme.md'])if(fs.existsSync(path.join(app,'build',file)))cp(path.join(app,'build',file),path.join(dest,'pixel-town-app/build',file));
for(const file of ['验收报告.md','node-tests.log','source-build.log','source-tests.log','packaged-launch.json','bundle-inventory.json','windows-runtime.json','packaged-app.png']){
 const relative=path.join('build','validation','release-3d-v'+version,file);if(fs.existsSync(path.join(app,relative)))cp(path.join(app,relative),path.join(dest,'pixel-town-app',relative));
}
for(const folder of ['town-ai-v9','whole-town-realistic-actors-v8'])cp(path.join(app,'design',folder),path.join(dest,'pixel-town-app/design',folder));
// Original current sprite exports are independent test fixtures, not copies manufactured from runtime assets.
for(const folder of ['characters','pets','codexmini'])cp(path.join(workspace,'pixel_town_assets',folder),path.join(dest,'pixel_town_assets',folder));
for(const file of ['roster.json','人物工作交接.md','expansion-guide.md'])if(fs.existsSync(path.join(workspace,'pixel_town_assets',file)))cp(path.join(workspace,'pixel_town_assets',file),path.join(dest,'pixel_town_assets',file));
for(const file of ['AGENTS.md','PROJECT_CONTEXT.md'])if(fs.existsSync(path.join(workspace,file)))cp(path.join(workspace,file),path.join(dest,file));
fs.writeFileSync(path.join(dest,'启动三维小镇-Windows.bat'),'@echo off\r\ncd /d "%~dp0pixel-town-app"\r\ncall npm run start:3d\r\npause\r\n');
const mac=path.join(dest,'启动三维小镇-Mac.command');fs.writeFileSync(mac,'#!/bin/bash\nset -e\ncd "$(dirname "$0")/pixel-town-app"\nunset ELECTRON_RUN_AS_NODE\nnpm run start:3d\n');fs.chmodSync(mac,0o755);
fs.writeFileSync(path.join(dest,'README-继续开发.md'),`# 溪畔日常3D ${version} 完整当前源码\n\n在Windows或Mac安装Node.js 22或更新LTS后，进入 **pixel-town-app** 子目录：\n\n\`\`\`\nnpm ci\nnpm run start:3d\nnpm run build:3d\nnpm test\nnpm run package:3d -- --platform win32 --out releases/local-win\n\`\`\`\n\nWindows打包使用本机npm安装的Electron；Mac打包请将platform改为darwin。成品应用不要求用户安装Node.js。三维构建已是Node脚本，无须Python/bash。首次依赖安装需要网络。\n\n当前运行/修改需要的三维原件、52成品模型、20配套动作、V8全部数据、V9源码、2D设置与素材及测试用原始导出均在本包；可编辑整镇工程：pixel-town-app/design/whole-town-realistic-actors-v8/Town-with-original-actors.blend。旧设计探索和历史备份未收入。\n\n不含个人API密钥、账户、私人存档或聊天。换系统请重新配置API Key，Mac钥匙串加密文件不能直接在Windows解密。详细功能边界和运行说明见pixel-town-app/build/desktop-release-readme.md。\n\n本地真实API测试默认关闭；npm test使用模拟调用，不消耗真实服务商额度。现有测试中的macOS设置/签名检查仅适用于Mac，Windows平台实机测试仍需要继续完成。\n`);
const entries=[];function walk(dir){for(const e of fs.readdirSync(dir,{withFileTypes:true})){const p=path.join(dir,e.name);if(e.isDirectory())walk(p);else entries.push({file:path.relative(dest,p).split(path.sep).join('/'),bytes:fs.statSync(p).size,sha256:crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex')})}}walk(dest);
fs.writeFileSync(path.join(dest,'SOURCE-MANIFEST.json'),JSON.stringify({version,privateDataIncluded:false,files:entries},null,2));console.log(JSON.stringify({source:dest,files:entries.length,bytes:entries.reduce((n,e)=>n+e.bytes,0)}));
