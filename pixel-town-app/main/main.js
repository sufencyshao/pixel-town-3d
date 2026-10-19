'use strict';
const {app,BrowserWindow,ipcMain,Menu,dialog,safeStorage}=require('electron');
const path=require('path');
const fs=require('fs');
const crypto=require('crypto');
const {Town}=require('./engine');
const {catalog,petCatalog}=require('./catalog');
const {Persistence}=require('./persistence');
const {Journal}=require('./journal');
const Life=require('../shared/life');
const {behaviorPrompt}=require('./character-behavior');
const {ZONES}=require('./catalog');
const ModelAssignment=require('../shared/model-assignment');
const llm=require('./llm');
app.setName('像素小镇');
const DEV=!app.isPackaged||!!process.defaultApp;
app.setPath('userData',process.env.PIXEL_TOWN_DATA_DIR||path.join(app.getPath('appData'),DEV?'pixel-town-life-dev':'pixel-town-life'));
let win,town,persistence,journal,timer,saveTimer,lastSaveError='';
if(!app.requestSingleInstanceLock()) app.quit();
else app.whenReady().then(()=>{
  persistence=new Persistence(app.getPath('userData'),safeStorage);
  let state;
  try { state=persistence.load();journal=new Journal(path.join(app.getPath('userData'),'journals')); } catch(e) { dialog.showErrorBox('小镇存档或日志无法读取','现有文件已保留。'+e.message); app.quit(); return; }
  const save=()=>{ try { persistence.save(town.state);journal.flush(); lastSaveError=''; } catch(e) { if(e.message!==lastSaveError) { lastSaveError=e.message; town.event('存档或日志写入失败：'+e.message,'error'); } } };
  town=new Town(state,llm,()=>{clearTimeout(saveTimer);saveTimer=setTimeout(save,700);},journal);
  if(process.env.PIXEL_TOWN_3D==='1'){town.state.autonomous=false;town.state.resumeAutonomy=false;}
  if(!town.state.events.length) town.event('欢迎来到白板小镇。六位居民已入住，点击人物可以观察生活。','system');
  if(persistence.recovered) town.event('已从备份恢复存档，损坏文件另行保留。','system');
  Menu.setApplicationMenu(Menu.buildFromTemplate([{label:'像素小镇',submenu:[{role:'about'},{type:'separator'},{role:'quit'}]},{label:'编辑',submenu:[{role:'undo'},{role:'redo'},{type:'separator'},{role:'cut'},{role:'copy'},{role:'paste'},{role:'selectAll'}]},{label:'视图',submenu:[{role:'reload'},{role:'toggleDevTools'},{role:'togglefullscreen'}]}]));
  function createWindow() {
    if(win&&!win.isDestroyed()){win.show();win.focus();return true;}
    win=new BrowserWindow({width:1480,height:960,minWidth:1040,minHeight:720,title:'像素小镇 · 白板实验室',backgroundColor:'#f7f8f6',titleBarStyle:'hiddenInset',webPreferences:{preload:path.join(__dirname,'preload.js'),contextIsolation:true,nodeIntegration:false,sandbox:true}});
    win.webContents.setWindowOpenHandler(()=>({action:'deny'}));
    win.webContents.on('will-navigate',(e,url)=>{if(url!==win.webContents.getURL())e.preventDefault();});
    win.loadFile(path.join(__dirname,'../renderer/index.html'));
  }
  const threeD=require('./town-3d-window').installTown3D({BrowserWindow,ipcMain,town,llm,catalog,petCatalog,dataDir:app.getPath('userData'),saveBindings:candidate=>persistence.save(candidate),openSettings:()=>{createWindow();const show=()=>win?.webContents.send('town:open-settings');if(win.webContents.isLoading())win.webContents.once('did-finish-load',show);else show();return true;}});
  if(process.env.PIXEL_TOWN_3D==='1')threeD.open();else createWindow();
  const emit=()=>{if(win&&!win.isDestroyed())win.webContents.send('town:snapshot',town.snapshot());};
  function handle(name,fn) { ipcMain.handle(name,async(event,...args)=>{if(event.sender!==win?.webContents)throw new Error('无效窗口'); try { const result=await fn(...args); emit(); return {ok:true,value:result}; } catch(e) {emit(); return {ok:false,error:e.message};} }); }
  handle('town:get',()=>({state:town.snapshot(),catalog,petCatalog,dataDir:app.getPath('userData'),encrypted:persistence.encryptionAvailable??null}));
  handle('town:open3d',()=>threeD.open());
  handle('town:config',c=>town.configure(c));
  handle('town:time',minute=>town.advanceTo(minute));
  handle('town:count',n=>town.setCount(n));
  handle('town:roster',ids=>town.setRoster(ids));
  handle('town:pets',ids=>town.setPets(ids));
  handle('town:update',(id,data)=>{town.update(id,data);return true;});
  handle('town:knowledge',value=>{const next=Life.validateWorld(value);persistence.save({...town.state,worldInfo:next});town.setKnowledge(next);lastSaveError='';return true;});
  handle('town:life',(id,value)=>{const life=town.prepareLife(id,value),candidate=structuredClone(town.state);candidate.residents.find(r=>r.id===id).life=life;persistence.save(candidate);town.setLife(id,value);lastSaveError='';return true;});
  handle('town:context',id=>{const r=town.entity(id);if(r.isPlayer)throw new Error('主角由玩家控制，不调用人物模型');return {name:r.name,system:town.prompt(r)+(r.kind==='animal'?'':'\n'+behaviorPrompt(town.animationFor(r),{partners:town.partnersFor(r),zones:ZONES,currentGoal:r.life?.focus||null})),paidCall:false};});
  handle('journal:subjects',()=>[...journal.subjects.values()]);
  handle('journal:get',(id,options)=>journal.page(id,options));
  handle('journal:export',async(id,day)=>{const text=journal.markdown(id,day),subject=journal.subjects.get(id);const result=await dialog.showSaveDialog(win,{defaultPath:`${subject.name.replace(/[\\/:]/g,'_')}-第${day}天.md`,filters:[{name:'角色每日日志',extensions:['md']}]});if(result.canceled)return false;fs.writeFileSync(result.filePath,text);return true;});
  handle('town:models:assign',payload=>{
    if(town.busy)throw new Error('已有模型操作正在进行，请结束后再批量分配');
    const plan=ModelAssignment.plan(town.state,payload);
    const candidate=structuredClone(town.state);
    const nextEntities=new Map([...candidate.residents,...candidate.pets].map(r=>[r.id,r]));
    const liveEntities=new Map([...town.state.residents,...town.state.pets].map(r=>[r.id,r]));
    for(const assignment of plan.assignments)nextEntities.get(assignment.id).model=structuredClone(assignment.model);
    const distribution=plan.counts.map(({providerId,count})=>`${town.state.providers.find(p=>p.id===providerId).name} ${count} 位`).join('、');
    const strategy=plan.strategy==='grouped'?'连续分组':'按顺序轮流';
    candidate.events.unshift({id:Date.now()+'-'+crypto.randomUUID(),time:candidate.clock,text:`已为 ${plan.assignments.length} 位居民或动物批量分配模型（${strategy}）：${distribution}`,kind:'system',ids:plan.assignments.map(a=>a.id)});
    candidate.events=candidate.events.slice(0,180);
    // Save the complete candidate before changing any live entity or event.
    persistence.save(candidate);
    for(const assignment of plan.assignments)liveEntities.get(assignment.id).model=nextEntities.get(assignment.id).model;
    town.state.events=candidate.events;
    lastSaveError='';town.touch();
    return {assigned:plan.assignments.length,counts:plan.counts,strategy:plan.strategy};
  });
  handle('town:act',(id,action,point)=>town.act(id,action,point));
  handle('town:move',(id,point)=>town.move(id,point));
  handle('town:teleport',(id,point)=>town.teleport(id,point));
  handle('town:control',id=>town.control(id));
  handle('player:control',()=>town.control('player'));
  handle('player:expression',expression=>town.setPlayerExpression(expression));
  handle('player:save',payload=>{
    const candidate=town.preparePlayer(payload);
    // Persist the candidate before exposing it; a failed write leaves the live player and control intact.
    persistence.save({...town.state,player:candidate});
    if(town.state.player)Object.assign(town.state.player,candidate);else town.state.player=candidate;
    journal.register(town.state.player,town.state.clock);town.record(town.state.player,'profile','主角姓名或外观已保存。',{source:'player'});
    lastSaveError='';town.touch();return true;
  });
  handle('town:input',point=>town.setInput(point));
  handle('town:invite',(aid,bid)=>{const a=town.resident(aid),b=town.resident(bid);if(!a.enabled||!b.enabled||aid===bid)throw new Error('请选择另一位在场居民');if(town.busy)throw new Error('已有对话正在进行');if(town.state.controlledId===aid||town.state.controlledId===bid)town.control(null);town.meet(a,b,false);});
  handle('town:step',()=>{for(let i=0;i<10;i++)town.tick(0.5/town.state.speed,true);town.touch();});
  handle('town:talk',(a,b)=>town.converse(a,b));
  handle('town:decide',id=>town.decide(id));
  handle('town:chat',(id,text)=>town.chat(id,text));
  function provider(data) {
    const existing=town.state.providers.find(p=>p.id===data.id);
    return {id:existing?.id||'p-'+crypto.randomUUID(),name:String(data.name||'自定义 API').slice(0,60),type:data.type==='anthropic'?'anthropic':'openai',baseUrl:String(data.baseUrl||'').trim().replace(/\/+$/,'').replace(/\/chat\/completions$/i,'').replace(/\/v1\/messages$/i,''),apiKey:data.apiKey===undefined?(existing?.apiKey||''):String(data.apiKey),models:Array.isArray(data.models)?data.models.map(String).filter(Boolean).slice(0,500):[]};
  }
  handle('provider:save',data=>{if(data.id==='demo')throw new Error('本地规则不可修改'); const p=provider(data);if(!/^https?:\/\//.test(p.baseUrl))throw new Error('Base URL 必须以 http:// 或 https:// 开头');const previous=structuredClone(town.state.providers); const idx=town.state.providers.findIndex(x=>x.id===p.id);if(idx>=0)town.state.providers[idx]=p;else town.state.providers.push(p);try{persistence.save(town.state);}catch(e){town.state.providers=previous;throw e;}town.touch();return p.id;});
  handle('provider:remove',id=>{if(id==='demo')throw new Error('本地规则不可删除');if([...town.state.residents,...town.state.pets].some(r=>r.model.providerId===id))throw new Error('有居民或动物正在使用此服务商，请先修改居民模型配置');town.state.providers=town.state.providers.filter(p=>p.id!==id);town.touch();});
  handle('provider:models',data=>llm.fetchModels(provider(data)));
  handle('provider:test',(data,model)=>llm.testProvider(provider(data),model));
  // 用户点选后才读取原应用数据，原路径仅 readFile，不迁移、不写回。
  const sourceFile=name=>path.join(app.getPath('appData'),'ai-friends-chat',name+'.json');
  const legacyProviders=()=>{const settings=JSON.parse(fs.readFileSync(sourceFile('settings'),'utf8'));return (settings.providers||[]).filter(p=>p.type!=='demo');};
  handle('legacy:provider-options',()=>legacyProviders().map(p=>({id:p.id,name:p.name,type:p.type,models:p.models||[],hasKey:!!p.apiKey,imported:town.state.providers.some(x=>x.id==='legacy-'+p.id)})));
  handle('legacy:providers',ids=>{const options=legacyProviders();if(ids!==undefined&&(!Array.isArray(ids)||!ids.length||new Set(ids).size!==ids.length||ids.some(id=>typeof id!=='string'||!options.some(p=>p.id===id))))throw new Error('请选择有效的原应用服务商');const previous=structuredClone(town.state.providers);let count=0;for(const p of options) {if(ids&&!ids.includes(p.id))continue;const id='legacy-'+p.id;if(town.state.providers.some(x=>x.id===id))continue;town.state.providers.push({id,name:p.name,type:p.type,baseUrl:p.baseUrl,apiKey:p.apiKey||'',models:p.models||[]});count++;}try{persistence.save(town.state);}catch(e){town.state.providers=previous;throw e;}town.touch();return count;});
  handle('legacy:friends',()=>{const friends=JSON.parse(fs.readFileSync(sourceFile('friends'),'utf8'));return friends.map(({id,name,occupation,persona,profileMd})=>({id,name,occupation,persona,profileMd}));});
  handle('town:export',async()=>{const result=await dialog.showSaveDialog(win,{defaultPath:'像素小镇存档.json',filters:[{name:'JSON 存档（不含密钥）',extensions:['json']}]});if(result.canceled)return false;const s=town.snapshot();s.providers.forEach(p=>delete p.hasKey);fs.writeFileSync(result.filePath,JSON.stringify(s,null,2));return true;});
  let tickCount=0;
  timer=setInterval(()=>{if(!threeD.active())town.tick(0.1);if(++tickCount%2===0)emit();},100);
  const checkpoint=setInterval(save,10000);
  app.on('before-quit',()=>{threeD.stop();clearInterval(timer);clearInterval(checkpoint);clearTimeout(saveTimer);save();});
  app.on('activate',()=>{if(BrowserWindow.getAllWindows().length===0){if(process.env.PIXEL_TOWN_3D==='1')threeD.open();else createWindow();}});
});
app.on('window-all-closed',()=>app.quit());
