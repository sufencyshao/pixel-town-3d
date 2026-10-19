'use strict';
// Exercise the real renderer with an isolated in-memory town. No API or user data.
const {app,BrowserWindow,ipcMain}=require('electron');
const path=require('node:path');
const fs=require('node:fs');
const assert=require('node:assert/strict');
const appRoot=process.env.TOWN_TEST_APP_ROOT||path.join(__dirname,'..');
const {Town}=require(path.join(appRoot,'main/engine'));
const {initialState,catalog,petCatalog}=require(path.join(appRoot,'main/catalog'));
const ModelAssignment=require(path.join(appRoot,'shared/model-assignment'));
const Appearance=require(path.join(appRoot,'shared/appearance'));
let win;
app.whenReady().then(async()=>{
  const town=new Town(initialState(),{chatCompletion:async()=>{throw new Error('UI checks must not call an API');}});
  town.state.providers.push({id:'test-a',name:'青禾 · Key A',type:'openai',baseUrl:'https://example.invalid/v1',apiKey:'fake-test-a',models:['town-life-small']},{id:'test-b',name:'晚风 · Key B',type:'anthropic',baseUrl:'https://example.invalid',apiKey:'fake-test-b',models:['town-life-medium']});
  town.state.residents.forEach((r,i)=>r.enabled=i<6);
  town.state.residents.slice(0,6).forEach((r,i)=>Object.assign(r.model,{temperature:.4+i*.1,maxTokens:200+i*20}));
  town.state.player=town.preparePlayer({name:'我的旅人',appearance:Appearance.defaults});
  town.state.pets[0].enabled=true;
  let failSave=false,failRefresh=false,saveDelay=0,assignCalls=0,lastPayload;
  const emit=()=>win.webContents.send('town:snapshot',town.snapshot());
  const commands={
    'town:get':()=>{if(failRefresh)throw new Error('模拟刷新失败');return{state:town.snapshot(),catalog,petCatalog,dataDir:'in-memory-batch-test',encrypted:true};},
    'town:config':data=>town.configure(data),'town:input':data=>town.setInput(data),
    'town:models:assign':async data=>{
      assignCalls++;lastPayload=structuredClone(data);
      if(town.busy)throw new Error('当前任务未完成');
      const plan=ModelAssignment.plan(town.state,data);
      await new Promise(resolve=>setTimeout(resolve,saveDelay));
      if(failSave)throw new Error('模拟磁盘写入失败');
      for(const a of plan.assignments)town.entity(a.id).model=a.model;
      town.touch();return{assigned:plan.assignments.length,counts:plan.counts,strategy:plan.strategy};
    }
  };
  for(const [name,fn]of Object.entries(commands))ipcMain.handle(name,async(_,...args)=>{try{const value=await fn(...args);emit();return{ok:true,value};}catch(e){emit();return{ok:false,error:e.message};}});
  win=new BrowserWindow({show:false,width:1480,height:960,webPreferences:{preload:path.join(appRoot,'main/preload.js'),sandbox:true,contextIsolation:true,nodeIntegration:false}});
  const errors=[];win.webContents.on('console-message',(_,level,text)=>{if(level>=3)errors.push(text);});
  const evaluate=code=>win.webContents.executeJavaScript(code,true);
  const until=async code=>{const deadline=Date.now()+10000;while(Date.now()<deadline){if(await evaluate(code))return;await new Promise(r=>setTimeout(r,30));}throw new Error('Timed out: '+code);};
  const click=selector=>evaluate(`document.querySelector(${JSON.stringify(selector)}).click()`);
  const change=(selector,value,event='input')=>evaluate(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});e.value=${JSON.stringify(String(value))};e.dispatchEvent(new Event(${JSON.stringify(event)},{bubbles:true}));})()`);
  const checkValue=(selector,checked)=>evaluate(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});e.checked=${checked};e.dispatchEvent(new Event('input',{bubbles:true}));})()`);
  const bindings=()=>structuredClone([...town.state.residents,...town.state.pets].map(r=>[r.id,r.model]));
  const checks=[];
  async function check(name,fn){await fn();checks.push(name);}
  try{
    await win.loadFile(path.join(appRoot,'renderer/index.html'));
    await until("!!state&&!!document.querySelector('#player-entry')");
    await click('#open-settings');await until("!state.running&&!document.querySelector('#api-page').hidden");
    const playerBefore=structuredClone(town.state.player);
    await check('Settings expose batch entry; cancel changes neither keys nor bindings',async()=>{
      assert.equal(await evaluate("!!document.querySelector('#batch-resident-api')&&!!document.querySelector('#batch-pet-api')&&!!document.querySelector('#batch-all-api')"),true);
      const before=bindings();await click('#batch-resident-api');
      assert.equal(await evaluate("document.querySelectorAll('[data-batch-target]').length"),town.state.residents.length);
      assert.equal(await evaluate("document.querySelectorAll('[data-batch-target=player]').length"),0);
      assert.equal(await evaluate("document.querySelectorAll('[data-batch-preview]').length"),6);
      assert.equal(await evaluate("Array.from(document.querySelectorAll('[data-batch-target]:checked')).length"),6);
      assert.equal(await evaluate("Array.from(document.querySelectorAll('[data-batch-field=temperature]')).every(e=>e.disabled)"),true);
      assert.equal(await evaluate("document.querySelector('#batch-api-editor').textContent.includes('fake-test-a')"),false);
      await click('#batch-cancel');assert.deepEqual(bindings(),before);assert.equal(assignCalls,0);
    });
    await check('One configuration applies to six NPCs and preserves each parameter',async()=>{
      const parameters=town.state.residents.slice(0,6).map(r=>[r.model.temperature,r.model.maxTokens]);
      await click('#batch-resident-api');await click('#batch-apply');await until("!document.querySelector('#batch-api-editor').open");
      assert.deepEqual(town.state.residents.slice(0,6).map(r=>[r.model.providerId,r.model.model]),Array.from({length:6},()=>['test-a','town-life-small']));
      assert.deepEqual(town.state.residents.slice(0,6).map(r=>[r.model.temperature,r.model.maxTokens]),parameters);
      assert.ok(town.state.residents.slice(6).every(r=>r.model.providerId==='demo'));
      assert.equal(assignCalls,1);assert.equal(lastPayload.preserveParameters,true);
      assert.deepEqual(town.state.player,playerBefore);
    });
    await check('Several configs preview exact alternating and grouped assignment; explicit parameters save',async()=>{
      await click('#batch-resident-api');await checkValue('[data-batch-config=test-b] [data-batch-api-check]',true);
      const preview=()=>evaluate("Array.from(document.querySelectorAll('[data-batch-preview]')).map(row=>row.cells[1].firstChild.textContent)");
      assert.deepEqual(await preview(),['青禾 · Key A','晚风 · Key B','青禾 · Key A','晚风 · Key B','青禾 · Key A','晚风 · Key B']);
      await change('#batch-strategy','grouped','change');
      assert.deepEqual(await preview(),['青禾 · Key A','青禾 · Key A','青禾 · Key A','晚风 · Key B','晚风 · Key B','晚风 · Key B']);
      await click('#batch-preserve');
      await change('[data-batch-config=test-a] [data-batch-field=temperature]',.2);
      await change('[data-batch-config=test-a] [data-batch-field=maxTokens]',640);
      await change('[data-batch-config=test-b] [data-batch-field=temperature]',1.1);
      await change('[data-batch-config=test-b] [data-batch-field=maxTokens]',980);
      await change('[data-batch-config=test-a] [data-batch-field=model]','');
      assert.equal(await evaluate("document.querySelector('#batch-apply').disabled"),true);
      await change('[data-batch-config=test-a] [data-batch-field=model]','town-life-small');
      await change('#batch-strategy','round-robin','change');
      await until("Array.from(document.querySelectorAll('#batch-target-list img')).every(i=>i.complete&&i.naturalWidth>0)");
      if(process.env.TOWN_BATCH_SCREENSHOTS){await new Promise(resolve=>setTimeout(resolve,180));const dir=process.env.TOWN_BATCH_SCREENSHOTS;fs.mkdirSync(dir,{recursive:true});fs.writeFileSync(path.join(dir,'batch-api-assignment.png'),(await win.webContents.capturePage()).toPNG());}
      await click('#batch-apply');await until("!document.querySelector('#batch-api-editor').open");
      assert.deepEqual(town.state.residents.slice(0,6).map(r=>r.model),Array.from({length:6},(_,i)=>i%2?{providerId:'test-b',model:'town-life-medium',temperature:1.1,maxTokens:980}:{providerId:'test-a',model:'town-life-small',temperature:.2,maxTokens:640}));
      assert.deepEqual(town.state.player,playerBefore);
    });
    await check('Animals, inactive targets and search are selectable; zero selection cannot submit',async()=>{
      await click('[data-settings-tab=pets]');await click('#batch-pet-api');
      assert.equal(await evaluate("document.querySelectorAll('[data-batch-target]').length"),town.state.pets.length);
      assert.equal(await evaluate("document.querySelectorAll('[data-batch-target]:checked').length"),1);
      await click('#batch-clear-targets');assert.equal(await evaluate("document.querySelector('#batch-apply').disabled"),true);
      await change('#batch-search',town.state.pets[1].name);await click('#batch-select-visible');
      assert.equal(await evaluate("document.querySelectorAll('[data-batch-preview]').length"),1);
      const id=town.state.pets[1].id;await click('#batch-apply');await until("!document.querySelector('#batch-api-editor').open");
      assert.equal(town.entity(id).model.providerId,'test-a');assert.equal(town.entity(id).enabled,false);
      assert.equal(town.state.pets[0].model.providerId,'demo');
    });
    await check('Provider shortcut preselects that API; all-target display never includes player',async()=>{
      await click('[data-settings-tab=api]');await click('[data-batch-provider=test-b]');
      assert.equal(await evaluate("Array.from(document.querySelectorAll('[data-batch-config]')).filter(r=>r.querySelector('[data-batch-api-check]').checked).map(r=>r.dataset.batchConfig).join(',')"),'test-b');
      assert.equal(await evaluate("document.querySelectorAll('[data-batch-target]').length"),town.state.residents.length+town.state.pets.length);
      assert.equal(await evaluate("document.querySelectorAll('[data-batch-target=player]').length"),0);
      await click('#batch-cancel');
    });
    await check('Small window keeps Apply reachable and both lists independently scroll',async()=>{
      win.setSize(1040,720);await click('#batch-all-api');
      const layout=await evaluate("(()=>{const d=document.querySelector('#batch-api-editor').getBoundingClientRect(),a=document.querySelector('#batch-apply').getBoundingClientRect(),p=document.querySelector('#batch-preview'),t=document.querySelector('#batch-target-list');return {width:innerWidth,height:innerHeight,dialog:{left:d.left,top:d.top,right:d.right,bottom:d.bottom},apply:{left:a.left,top:a.top,right:a.right,bottom:a.bottom},previewHeight:p.clientHeight,targetsScroll:t.scrollHeight>t.clientHeight,overflow:document.querySelector('.batch-config-panel').scrollWidth>document.querySelector('.batch-config-panel').clientWidth};})()");
      assert.ok(layout.dialog.left>=0&&layout.dialog.top>=0&&layout.dialog.right<=layout.width&&layout.dialog.bottom<=layout.height);
      assert.ok(layout.apply.bottom<=layout.height&&layout.previewHeight>=70&&layout.targetsScroll&&!layout.overflow,JSON.stringify(layout));
      if(process.env.TOWN_BATCH_SCREENSHOTS){await new Promise(resolve=>setTimeout(resolve,180));fs.writeFileSync(path.join(process.env.TOWN_BATCH_SCREENSHOTS,'batch-api-small-window.png'),(await win.webContents.capturePage()).toPNG());}
      await click('#batch-cancel');win.setSize(1480,960);
    });
    await check('Busy task disables Apply and re-enables after task; pending write blocks Escape/cancel',async()=>{
      await click('#batch-resident-api');town.busy=true;emit();await until("document.querySelector('#batch-apply').disabled");
      town.busy=false;emit();await until("!document.querySelector('#batch-apply').disabled");
      saveDelay=250;const before=assignCalls;await click('#batch-apply');
      assert.equal(await evaluate("Array.from(document.querySelector('#batch-api-editor').querySelectorAll('button,input,select')).every(e=>e.disabled)"),true);
      assert.equal(await evaluate("document.querySelector('#batch-api-editor').dispatchEvent(new Event('cancel',{cancelable:true}))"),false);
      await click('#batch-cancel');assert.equal(await evaluate("document.querySelector('#batch-api-editor').open"),true);
      await until("!document.querySelector('#batch-api-editor').open");assert.equal(assignCalls,before+1);
    });
    await check('Save failure keeps draft editable without partial changes, retry applies',async()=>{
      failSave=true;saveDelay=20;const before=bindings();await click('#batch-resident-api');
      await change('[data-batch-config=test-a] [data-batch-field=model]','my-custom-model');
      await click('#batch-apply');await until("!document.querySelector('#batch-apply').disabled");
      assert.equal(await evaluate("document.querySelector('#batch-api-editor').open"),true);
      emit();await new Promise(resolve=>setTimeout(resolve,80));
      assert.match(await evaluate("document.querySelector('#batch-message').textContent"),/模拟磁盘写入失败/);
      assert.deepEqual(bindings(),before);
      assert.equal(await evaluate("document.querySelector('[data-batch-config=test-a] [data-batch-field=model]').value"),'my-custom-model');
      failSave=false;await click('#batch-apply');await until("!document.querySelector('#batch-api-editor').open");
      assert.ok(town.state.residents.slice(0,6).every(r=>r.model.model==='my-custom-model'));
      assert.deepEqual(town.state.player,playerBefore);
    });
    await check('Committed assignment is never reported as failed when the following refresh fails',async()=>{
      await click('#batch-resident-api');failRefresh=true;const calls=assignCalls;
      await click('#batch-apply');await until("!document.querySelector('#batch-api-editor').open");
      assert.match(await evaluate("document.querySelector('#toast').textContent"),/已保存.*界面刷新失败/);
      assert.equal(assignCalls,calls+1);assert.deepEqual(town.state.player,playerBefore);failRefresh=false;
    });
    assert.deepEqual(errors,[]);console.log(JSON.stringify({ok:true,checks:checks.length,characters:catalog.length,pets:petCatalog.length,apiCalls:town.state.stats.length}));app.exit(0);
  }catch(e){console.error(e.stack);console.error(errors);app.exit(1);}
});
