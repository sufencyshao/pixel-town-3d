'use strict';
const {contextBridge,ipcRenderer}=require('electron');
const allowed=new Set(['town:get','town:config','town:count','town:roster','town:pets','town:update','town:act','town:move','town:teleport','town:control','town:input','town:invite','town:step','town:talk','town:decide','town:chat','town:export','provider:save','provider:remove','provider:models','provider:test','legacy:providers','legacy:friends']);
allowed.add('player:save');allowed.add('player:control');
allowed.add('player:expression');
allowed.add('town:models:assign');
allowed.add('legacy:provider-options');
allowed.add('town:time');
allowed.add('town:open3d');
for(const name of ['town:knowledge','town:life','town:context','journal:subjects','journal:get','journal:export'])allowed.add(name);
contextBridge.exposeInMainWorld('townAPI',{
  onOpenSettings:fn=>{const listener=()=>fn();ipcRenderer.on('town:open-settings',listener);return ()=>ipcRenderer.removeListener('town:open-settings',listener);},
  invoke:async(name,...args)=>{if(!allowed.has(name))throw new Error('不支持此操作');const result=await ipcRenderer.invoke(name,...args);if(!result.ok)throw new Error(result.error);return result.value;},
  subscribe:fn=>{const listener=(_,s)=>fn(s);ipcRenderer.on('town:snapshot',listener);return ()=>ipcRenderer.removeListener('town:snapshot',listener);}
});
