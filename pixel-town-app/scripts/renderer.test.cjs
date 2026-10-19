'use strict';
// Run with Electron. Uses an isolated in-memory town and never connects to API.
const {app,BrowserWindow,ipcMain}=require('electron');
const path=require('path');
const assert=require('node:assert/strict');
const appRoot=process.env.TOWN_TEST_APP_ROOT||path.join(__dirname,'..');
const {Town}=require(path.join(appRoot,'main/engine'));
const {initialState,catalog,petCatalog}=require(path.join(appRoot,'main/catalog'));
let win;
app.whenReady().then(async()=>{
  const town=new Town(initialState(),{chatCompletion:async()=>{throw new Error('Renderer checks must not call an API');}});
  const commands={'town:get':()=>({state:town.snapshot(),catalog,petCatalog,dataDir:'in-memory-test',encrypted:true}),
    'town:config':data=>town.configure(data),'town:pets':ids=>town.setPets(ids),'town:update':(id,data)=>town.update(id,data),
    'town:act':(id,action,point)=>town.act(id,action,point),'town:count':n=>town.setCount(n),'town:roster':ids=>town.setRoster(ids),
    'town:input':p=>town.setInput(p)};
  for(const [name,fn]of Object.entries(commands))ipcMain.handle(name,async(_, ...args)=>{
    try{const value=await fn(...args);win?.webContents.send('town:snapshot',town.snapshot());return{ok:true,value};}catch(e){return{ok:false,error:e.message};}
  });
  const failures=[];
  win=new BrowserWindow({show:false,width:1480,height:960,webPreferences:{preload:path.join(appRoot,'main/preload.js'),sandbox:true,contextIsolation:true,nodeIntegration:false,backgroundThrottling:false}});
  win.webContents.on('console-message',(_,level,message)=>{if(level>=3)failures.push(message);});
  win.webContents.on('did-fail-load',(_,code,message)=>failures.push(code+': '+message));
  const evaluate=code=>win.webContents.executeJavaScript(code,true);
  const until=async(code)=>{const deadline=Date.now()+10000;while(Date.now()<deadline){if(await evaluate(code))return;await new Promise(r=>setTimeout(r,50));}throw new Error('Renderer timed out: '+code);};
  try{
    await win.loadFile(path.join(appRoot,'renderer/index.html'));
    await until("!!state && document.querySelectorAll('.sprite').length===6");
    assert.equal(await evaluate("document.querySelectorAll('.sprite').length"),6);
    await until("Array.from(document.querySelectorAll('.sprite img')).every(i=>i.hidden||i.complete&&i.naturalWidth>0)");
    await evaluate("document.querySelector('#open-settings').click()");
    await until("!state.running && !document.querySelector('#api-page').hidden");
    assert.ok(await evaluate("document.querySelectorAll('.settings-tabs button').length>=3"));
    await evaluate("document.querySelector('#population-button').click()");
    await until("Array.from(document.querySelectorAll('.gallery img')).every(i=>i.complete&&i.naturalWidth>0)");
    assert.equal(await evaluate("document.querySelectorAll('.gallery img').length"),town.state.residents.length);
    await evaluate("document.querySelector('#close-modal').click()");
    await evaluate("document.querySelector('[data-settings-tab=pets]').click()");
    assert.equal(await evaluate("document.querySelector('#pet-settings').hidden"),false);
    assert.equal(await evaluate("document.querySelectorAll('[data-pet-id]').length"),town.state.pets.length);
    if(town.state.pets.length){
      await evaluate("document.querySelector('#pet-population-button').click()");
      await until("Array.from(document.querySelectorAll('.gallery img')).every(i=>i.complete&&i.naturalWidth>0)");
      assert.equal(await evaluate("document.querySelectorAll('.gallery img').length"),town.state.pets.length);
      await evaluate("document.querySelector('[name=pet-enabled]').checked=true;document.querySelector('#save-pets').click()");
      await until("state.pets.some(p=>p.enabled)&&!document.querySelector('#modal').open");
      await evaluate("document.querySelector('[data-pet-id]').click()");
      await until("!!document.querySelector('#pet-provider')");
      assert.equal(await evaluate("!!document.querySelector('#chat-form')"),false);
      if(town.state.pets.length>1){
        await evaluate("document.querySelector('#cancel-pet').click();document.querySelectorAll('[data-pet-id]')[1].click()");
        await until("!!document.querySelector('#pet-provider')");
        assert.equal(await evaluate("current().enabled"),false,'Uninvited animal profiles remain editable in settings');
      }
      await evaluate("document.querySelector('#cancel-pet').click();document.querySelector('#back-game').click()");
      await until("state.running && document.querySelectorAll('.sprite').length===7");
      assert.equal(await evaluate("document.querySelector('#open-chat')!==null"),false);
    }else await evaluate("document.querySelector('#back-game').click()");
    const mini=town.state.residents.find(r=>r.kind==='codexmini');
    if(mini){
      town.setRoster([...town.state.residents.filter(r=>r.enabled).map(r=>r.id),mini.id]);win.webContents.send('town:snapshot',town.snapshot());
      await until("inhabitants().some(r=>r.kind==='codexmini')&&document.querySelectorAll('.sprite').length===8");
      await evaluate(`select(${JSON.stringify(mini.id)});residentModal()`);
      await until("!!document.querySelector('#edit-preset') && document.querySelector('.person-modal-summary img').complete && document.querySelector('.person-modal-summary img').naturalWidth>0");
      assert.ok(await evaluate("document.querySelectorAll('#edit-preset option').length>1"));
      await evaluate("document.querySelector('#close-modal').click()");
    }
    if(catalog.some(c=>c.animation)){
      await until("Array.from(document.querySelectorAll('.atlas-sprite')).some(s=>!s.hidden&&s.style.backgroundImage)");
      await until("Array.from(document.querySelectorAll('.sprite .atlas-sprite')).filter(s=>!s.hidden).every(s=>s.style.backgroundImage&&s.style.backgroundImage!=='none')");
      await evaluate(`Promise.all(Array.from(document.querySelectorAll('.atlas-sprite')).filter(s=>!s.hidden).map(s=>new Promise((resolve,reject)=>{const img=new Image();img.onload=()=>img.naturalWidth>0?resolve(true):reject(new Error('Empty atlas'));img.onerror=()=>reject(new Error('Missing atlas: '+img.src));img.src=s.style.backgroundImage.slice(5,-2);})))`);
      const requestedAtlases=await evaluate("new Set(performance.getEntriesByType('resource').map(r=>r.name).filter(name=>name.includes('/animations/')&&name.endsWith('.png'))).size");
      assert.ok(requestedAtlases<=town.inhabitants().length,'Only the active clip of each visible entity should load');
      const frames=await evaluate("Array.from(document.querySelectorAll('.atlas-sprite')).filter(s=>!s.hidden).map(s=>s.style.backgroundPosition)");
      await until("JSON.stringify(Array.from(document.querySelectorAll('.atlas-sprite')).filter(s=>!s.hidden).map(s=>s.style.backgroundPosition))!=="+JSON.stringify(JSON.stringify(frames)));
      const next=await evaluate("Array.from(document.querySelectorAll('.atlas-sprite')).filter(s=>!s.hidden).map(s=>s.style.backgroundPosition)");
      assert.notDeepEqual(frames,next);
      await evaluate("invoke('town:config',{running:false})");
      await new Promise(r=>setTimeout(r,80));
      const frozen=await evaluate("animationTime");await new Promise(r=>setTimeout(r,180));assert.equal(await evaluate("animationTime"),frozen);
    }
    const humanIds=town.state.residents.filter(r=>r.kind==='human').map(r=>r.id);
    town.setRoster(humanIds);town.configure({running:false});win.webContents.send('town:snapshot',town.snapshot());
    await until("document.querySelectorAll('.sprite').length===40+state.pets.filter(p=>p.enabled).length");
    const dailyLoaded=await evaluate(`(async()=>{let count=0;const people=catalog.filter(r=>r.kind==='human');for(const r of people)for(const key of ['nod','shake_head','chat']){const c=r.animation.animations[key];await new Promise((resolve,reject)=>{const image=new Image();image.onload=()=>{if(image.naturalWidth!==256*c.frames||image.naturalHeight!==256)return reject(new Error(r.name+'/'+key+' has invalid dimensions'));count++;resolve();};image.onerror=()=>reject(new Error(r.name+'/'+key+' failed to load'));image.src='../assets/'+r.assetFolder+'/'+c.atlas;});}return count;})()`);
    assert.equal(dailyLoaded,120);
    const wen=town.state.residents.find(r=>r.asset==='36_barista_female');
    await evaluate(`select(${JSON.stringify(wen.id)});document.querySelector('#resident-actions').click()`);
    assert.equal(await evaluate("document.querySelectorAll('[data-character-action]').length"),14);
    await evaluate("document.querySelector('[data-character-action=shake_head]').click()");
    await until(`nodes.get(${JSON.stringify(wen.id)}).dataset.clip==='shake_head'`);
    const first=await evaluate(`({...nodes.get(${JSON.stringify(wen.id)}).dataset})`);assert.equal(town.resident(wen.id).action,'shake_head');assert.equal(town.resident(wen.id).target,null);
    await evaluate("animationTime+=450");await new Promise(r=>setTimeout(r,40));
    const middle=await evaluate(`nodes.get(${JSON.stringify(wen.id)}).querySelector('.atlas-sprite').style.backgroundPosition`);
    await evaluate("document.querySelector('#resident-actions').click();document.querySelector('[data-character-action=shake_head]').click()");
    await until(`nodes.get(${JSON.stringify(wen.id)}).dataset.actionVersion!==${JSON.stringify(first.actionVersion)}`);
    const restarted=await evaluate(`nodes.get(${JSON.stringify(wen.id)}).querySelector('.atlas-sprite').style.backgroundPosition`);assert.notEqual(middle,restarted);assert.equal(restarted,'0px 0px');
    town.tick(1.2,true);win.webContents.send('town:snapshot',town.snapshot());await until(`nodes.get(${JSON.stringify(wen.id)}).dataset.clip==='idle'`);
    await evaluate("document.querySelector('#resident-actions').click();document.querySelector('[data-character-action=chat]').click()");await until(`nodes.get(${JSON.stringify(wen.id)}).dataset.clip==='chat'`);
    win.setSize(1040,720);await evaluate("document.querySelector('#resident-actions').click()");
    assert.equal(await evaluate("(()=>{const m=document.querySelector('#modal'),b=m.getBoundingClientRect();return b.left>=0&&b.right<=innerWidth&&b.top>=0&&b.bottom<=innerHeight&&m.scrollWidth<=m.clientWidth;})()"),true);
    assert.deepEqual(failures,[]);
    console.log(JSON.stringify({ok:true,characters:catalog.length,pets:petCatalog.length,atlas:catalog.filter(c=>c.animation).length,dailyAtlases:dailyLoaded,refusalRestart:true,refusalCompletes:true,smallWindow:true,apiCalls:town.state.stats.length}));
    app.exit(0);
  }catch(error){console.error(error.stack);console.error(failures);app.exit(1);}
});
