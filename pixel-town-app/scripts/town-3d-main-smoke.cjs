'use strict';
const {app,BrowserWindow}=require('electron'),fs=require('fs'),path=require('path'),os=require('os'),assert=require('node:assert/strict');
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'town-3d-main-'));process.env.PIXEL_TOWN_DATA_DIR=dir;process.env.PIXEL_TOWN_3D='1';
require('../main/main');
app.whenReady().then(async()=>{
 const checks=[];const check=(name,value)=>{assert.ok(value,name);checks.push({name,pass:true});console.log('PASS',name)};
 const until=async(fn,ms=120000)=>{const end=Date.now()+ms;while(Date.now()<end){try{const result=await fn();if(result)return result}catch{}await new Promise(r=>setTimeout(r,80))}throw new Error('Smoke timeout')};
 try{
  const three=await until(()=>BrowserWindow.getAllWindows().find(w=>w.webContents.getURL().includes('AI%E7%94%9F%E6%B4%BB')||decodeURI(w.webContents.getURL()).includes('三维小镇-AI生活')));const evaluate=code=>three.webContents.executeJavaScript(code,true);
  await until(()=>evaluate('!!window.townAI'));check('real main launches the 3D entry with sandboxed API bridge',await evaluate('!!window.town3DAPI&&typeof require==="undefined"'));
  check('3D starts without autonomous API calls',await evaluate('!townAI.autoId&&!townAI.inFlight'));
  await evaluate("document.getElementById('ai-settings').click()");const settings=await until(()=>BrowserWindow.getAllWindows().find(w=>w!==three));await until(()=>settings.webContents.executeJavaScript("!!document.getElementById('api-page')&&!document.getElementById('api-page').hidden&&!document.getElementById('model-settings').hidden"));
  check('settings opens directly on existing API tab after initial load',true);
  const providerId=await settings.webContents.executeJavaScript("townAPI.invoke('provider:save',{name:'本地验证服务商',type:'openai',baseUrl:'http://127.0.0.1:1/v1',apiKey:'',models:['smoke-model']})",true);
  await evaluate(`town3DAPI.invoke('bind','03_barista_male',{providerId:${JSON.stringify(providerId)},model:'smoke-model',temperature:.7,maxTokens:1024})`);
  const saved=JSON.parse(fs.readFileSync(path.join(dir,'town.json'),'utf8'));check('API binding persists to isolated app data and matches original resident instance',saved.residents.find(r=>r.catalogId==='03_barista_male').model.model==='smoke-model');
  check('3D API bridge rejects unrelated channels',await evaluate("town3DAPI.invoke('provider:save',{}).then(()=>false,()=>true)"));
  const contexts=await evaluate("town3DAPI.invoke('context','03_barista_male',townAI.executor.scene())");check('real main IPC builds complete live project context',contexts.data.publicResidents.length===61&&contexts.data.capabilities.clips.includes('Wave'));
  check('old 2D autonomy is off in the dedicated 3D mode',saved.autonomous===false&&saved.resumeAutonomy===false);
  fs.writeFileSync(path.join(__dirname,'../design/town-ai-v9/qa/main-integration.json'),JSON.stringify({checks,isolatedData:true,paidCalls:0},null,2));
 }catch(error){console.error(error.stack);process.exitCode=1}finally{for(const w of BrowserWindow.getAllWindows())w.destroy();fs.rmSync(dir,{recursive:true,force:true});app.exit(process.exitCode||0)}
});
