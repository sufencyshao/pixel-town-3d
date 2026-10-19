'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),{execFileSync}=require('child_process');
const ROOT=path.resolve(__dirname,'..'),VERSION=require('../package.json').version,PRODUCT='溪畔日常3D';
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
function copy(from,to,dereference=true){fs.mkdirSync(path.dirname(to),{recursive:true});fs.cpSync(from,to,{recursive:true,dereference,verbatimSymlinks:!dereference,filter:p=>!['.DS_Store','__pycache__'].includes(path.basename(p))});}
function files(dir,prefix=''){return fs.readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?files(path.join(dir,e.name),prefix+e.name+'/'):[prefix+e.name]);}
function runtimeApp(destination){
 fs.mkdirSync(destination,{recursive:true});
 for(const folder of ['main','renderer','shared','assets'])copy(path.join(ROOT,folder),path.join(destination,folder));
 const v9='design/town-ai-v9';
 for(const file of ['三维小镇-AI生活.html','capabilities.json','README.md','验收记录.md'])copy(path.join(ROOT,v9,file),path.join(destination,v9,file));
 const v8='design/whole-town-realistic-actors-v8';
 for(const file of ['reference/pending-animals.json','整镇分区总图.svg','README.md','licenses'])copy(path.join(ROOT,v8,file),path.join(destination,v8,file));
 copy(path.join(ROOT,v8,'整镇分区总图.svg'),path.join(destination,v9,'整镇分区总图.svg'));
 const undici=path.dirname(require.resolve('undici/package.json'));copy(undici,path.join(destination,'node_modules/undici'));
 const pkg={name:'pixel-town-3d',productName:PRODUCT,version:VERSION,description:'完整三维小镇与独立 AI 生活',main:'main/desktop-3d.js',dependencies:{undici:'6.21.1'}};
 fs.writeFileSync(path.join(destination,'package.json'),JSON.stringify(pkg,null,2));
 copy(path.join(ROOT,'build/desktop-release-readme.md'),path.join(destination,'使用说明.md'));
 const inventory=files(destination).sort().map(file=>({file,bytes:fs.statSync(path.join(destination,file)).size,sha256:hash(path.join(destination,file))}));
 fs.writeFileSync(path.join(destination,'release-manifest.json'),JSON.stringify({version:VERSION,entry:pkg.main,privateDataIncluded:false,files:inventory},null,2));
 return inventory;
}
function plist(file,key,value){execFileSync('/usr/libexec/PlistBuddy',['-c',`Set :${key} ${value}`,file]);}
function build({platform=process.platform,runtime,out}={}){
 const parent=path.resolve(out||path.join(ROOT,'releases',VERSION));fs.mkdirSync(parent,{recursive:true});
 let target,resources;
 if(platform==='darwin'){
  runtime=runtime||path.join(path.dirname(require.resolve('electron/package.json')),'dist/Electron.app');
  target=path.join(parent,PRODUCT+'.app');if(fs.existsSync(target))throw new Error('输出已存在，请指定新的 --out 目录，避免覆盖：'+target);
  copy(runtime,target,false);resources=path.join(target,'Contents/Resources');
  fs.renameSync(path.join(target,'Contents/MacOS/Electron'),path.join(target,'Contents/MacOS',PRODUCT));
  const info=path.join(target,'Contents/Info.plist');
  for(const [key,value] of Object.entries({CFBundleName:PRODUCT,CFBundleDisplayName:PRODUCT,CFBundleIdentifier:'com.summerwindy.pixel-town-3d',CFBundleExecutable:PRODUCT,CFBundleShortVersionString:VERSION,CFBundleVersion:VERSION}))plist(info,key,value);
  const icon=path.join(ROOT,'build/town.icns');if(fs.existsSync(icon)){copy(icon,path.join(resources,'town.icns'));plist(info,'CFBundleIconFile','town.icns');}
 }else if(platform==='win32'){
  runtime=runtime||path.join(path.dirname(require.resolve('electron/package.json')),'dist');
  target=path.join(parent,PRODUCT+'-Windows-x64');if(fs.existsSync(target))throw new Error('输出已存在：'+target);copy(runtime,target);resources=path.join(target,'resources');
  const exe=path.join(target,'electron.exe');if(!fs.existsSync(exe))throw new Error('Windows Electron 运行环境缺少 electron.exe');fs.renameSync(exe,path.join(target,'PixelTown3D.exe'));
  copy(path.join(ROOT,'build/desktop-release-readme.md'),path.join(target,'使用说明.md'));
 }else throw new Error('当前发布目标支持 darwin 或 win32');
 const defaultApp=path.join(resources,'default_app.asar');if(fs.existsSync(defaultApp))fs.unlinkSync(defaultApp);
 const inventory=runtimeApp(path.join(resources,'app'));
 if(platform==='darwin')execFileSync('codesign',['--force','--deep','--sign','-',target],{stdio:'inherit'});
 copy(path.join(ROOT,'build/desktop-release-readme.md'),path.join(parent,platform==='darwin'?'Mac使用说明.md':'Windows使用说明.md'));
 console.log(JSON.stringify({target,platform,version:VERSION,applicationFiles:inventory.length}));return {target,platform,version:VERSION};
}
if(require.main===module){const args=process.argv.slice(2),arg=key=>{const i=args.indexOf('--'+key);return i<0?undefined:args[i+1]};try{build({platform:arg('platform'),runtime:arg('runtime'),out:arg('out')})}catch(e){console.error(e.message);process.exitCode=1}}
module.exports={build,runtimeApp};
