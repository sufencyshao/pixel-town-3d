'use strict';
const {contextBridge,ipcRenderer}=require('electron');
const allowed=new Set(['get','context','decide','cancel','receipt','bind','settings']);
contextBridge.exposeInMainWorld('town3DAPI',{invoke:async(name,...args)=>{
  if(!allowed.has(name))throw new Error('不支持的三维操作');const result=await ipcRenderer.invoke('town3d:'+name,...args);if(!result.ok)throw new Error(result.error);return result.value;
}});
