'use strict';
const fs=require('fs'),path=require('path');
const {Town3DService}=require('./town-3d-service');
function installTown3D({BrowserWindow,ipcMain,town,llm,catalog,petCatalog,dataDir,saveBindings,openSettings}){
  const root=path.resolve(__dirname,'../design/town-ai-v9'),entry=path.join(root,'三维小镇-AI生活.html');let window,service;
  function getService(){if(!service)service=new Town3DService({town,llm,catalog:[...catalog,...petCatalog],capabilities:JSON.parse(fs.readFileSync(path.join(root,'capabilities.json'),'utf8')).actors,pending:JSON.parse(fs.readFileSync(path.join(root,'../whole-town-realistic-actors-v8/reference/pending-animals.json'),'utf8')),file:path.join(dataDir,'town-3d-life.json'),saveBindings});return service;}
  function open(){
    if(window&&!window.isDestroyed()){window.show();window.focus();return true;}
    if(!fs.existsSync(entry))throw new Error('请先运行 npm run build:3d 生成三维入口');getService();
    window=new BrowserWindow({width:1550,height:1020,minWidth:390,minHeight:650,title:'像素小镇 · 三维 AI 生活',backgroundColor:'#f6f3e9',webPreferences:{preload:path.join(__dirname,'town-3d-preload.js'),contextIsolation:true,nodeIntegration:false,sandbox:true}});
    window.webContents.setWindowOpenHandler(()=>({action:'deny'}));window.webContents.on('will-navigate',(e,url)=>{if(url!==window.webContents.getURL())e.preventDefault()});
    const interrupt=reason=>{try{service?.interrupt(reason)}catch(e){console.error('三维中断记录保存失败：'+e.message)}};
    window.webContents.on('did-start-navigation',()=>interrupt('三维窗口重载'));
    window.webContents.on('render-process-gone',()=>interrupt('三维渲染进程退出'));
    window.on('closed',()=>{interrupt('三维窗口关闭');window=null});window.loadFile(entry);return true;
  }
  for(const name of ['get','context','decide','cancel','receipt','bind','settings'])ipcMain.handle('town3d:'+name,async(event,...args)=>{
    if(event.sender!==window?.webContents)return {ok:false,error:'无效三维窗口'};
    try{let value;const s=getService();if(name==='get')value=s.initial();else if(name==='settings')value=openSettings();else value=await s[name](...args);return {ok:true,value};}catch(e){return {ok:false,error:e.message};}
  });
  return {open,active:()=>!!window&&!window.isDestroyed(),stop:()=>service?.cancel()};
}
module.exports={installTown3D};
