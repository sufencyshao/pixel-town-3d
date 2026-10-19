'use strict';
// Native Electron UI regression. All data are in memory and no API is contacted.
const {app,BrowserWindow,ipcMain}=require('electron');
const path=require('node:path');
const assert=require('node:assert/strict');
const appRoot=process.env.TOWN_TEST_APP_ROOT||path.join(__dirname,'..');
const {Town}=require(path.join(appRoot,'main/engine'));
const {initialState,catalog,petCatalog}=require(path.join(appRoot,'main/catalog'));
const Appearance=require(path.join(appRoot,'shared/appearance'));
let win;
app.whenReady().then(async()=>{
  const town=new Town(initialState(),{chatCompletion:async()=>{throw new Error('No API allowed in UI tests');}});
  let failSave=false,saveDelay=0;
  const emit=()=>win.webContents.send('town:snapshot',town.snapshot());
  const commands={
    'town:get':()=>({state:town.snapshot(),catalog,petCatalog,dataDir:'in-memory-player-test',encrypted:true}),
    'town:config':data=>town.configure(data),'town:control':id=>town.control(id),'player:control':()=>town.control('player'),
    'town:input':point=>town.setInput(point),'town:act':(id,action,point)=>town.act(id,action,point),
    'town:move':(id,point)=>town.move(id,point),'player:expression':value=>town.setPlayerExpression(value),
    'player:save':async data=>{await new Promise(r=>setTimeout(r,saveDelay));if(failSave)throw new Error('模拟写盘失败');const p=town.preparePlayer(data);if(town.state.player)Object.assign(town.state.player,p);else town.state.player=p;town.touch();return true;}
  };
  for(const [name,fn] of Object.entries(commands))ipcMain.handle(name,async(_, ...args)=>{try{const value=await fn(...args);emit();return{ok:true,value};}catch(e){emit();return{ok:false,error:e.message};}});
  win=new BrowserWindow({show:false,width:1480,height:960,webPreferences:{preload:path.join(appRoot,'main/preload.js'),contextIsolation:true,nodeIntegration:false,sandbox:true}});
  const errors=[];win.webContents.on('console-message',(_,level,text)=>{if(level>=3)errors.push(text);});
  const evaluate=code=>win.webContents.executeJavaScript(code,true);
  const until=async code=>{const deadline=Date.now()+5000;while(Date.now()<deadline){if(await evaluate(code))return;await new Promise(r=>setTimeout(r,20));}throw new Error('Timed out: '+code);};
  const click=selector=>evaluate(`document.querySelector(${JSON.stringify(selector)}).click()`);
  const field=(key,value)=>evaluate(`(()=>{const e=document.querySelector('[data-field=${key}]');if(!e)throw new Error('Missing field: ${key}');e.value=${JSON.stringify(String(value))};e.dispatchEvent(new Event('input',{bubbles:true}));})()`);
  const press=key=>evaluate(`document.body.dispatchEvent(new KeyboardEvent('keydown',{key:${JSON.stringify(key)},bubbles:true}))`);
  const release=key=>evaluate(`document.body.dispatchEvent(new KeyboardEvent('keyup',{key:${JSON.stringify(key)},bubbles:true}))`);
  const checks=[];
  async function check(name,fn){await fn();checks.push(name);}
  try{
    await win.loadFile(path.join(appRoot,'renderer/index.html'));await until("!!state&&!!document.querySelector('#player-entry')");
    await click('#player-entry');await until("!state.running&&!document.querySelector('#player-settings').hidden");
    await check('Settings keep player, NPC and animal panels separate',async()=>{assert.equal(await evaluate("document.querySelector('#character-settings').hidden&&document.querySelector('#pet-settings').hidden"),true);assert.equal(town.state.player,null);});
    await click('#create-player');
    await check('Game presets use resident artwork and both styles retain independent draft values',async()=>{
      assert.equal(await evaluate("document.querySelector('#player-editor').dataset.styleMode"),'preset');
      assert.equal(await evaluate("document.querySelector('#creator-canvas').width"),256);
      assert.equal(await evaluate("document.querySelectorAll('button[data-style-mode]').length"),2);
      assert.equal(await evaluate("document.querySelectorAll('[data-preset]').length"),8);
      await click('[data-group=preset]');await field('presetAccessory','roundGlasses');await field('presetHairColor','#A95E6D');
      await click('[data-style-mode=custom]');await click('[data-group=hair]');await field('hairStyle','bun');
      await click('[data-style-mode=preset]');await click('[data-group=preset]');
      assert.equal(await evaluate("document.querySelector('[data-field=presetAccessory]').value"),'roundGlasses');
      await click('[data-style-mode=custom]');await click('[data-group=hair]');
      assert.equal(await evaluate("document.querySelector('[data-field=hairStyle]').value"),'bun');
      await click('#reset-player');
    });
    await click('[data-style-mode=custom]');
    await check('All 30 appearance fields have editable controls and change preview',async()=>{
      const expected={...Appearance.customDefaults};let initial=await evaluate("document.querySelector('#creator-canvas').toDataURL()");
      for(const group of ['identity','hair','face','body','clothes','accessories']){
        await click(`[data-group=${group}]`);
        for(const f of Appearance.fields.filter(f=>f.group===group)){expected[f.key]=f.type==='select'?f.options.at(-1).value:f.type==='color'?'#8D617B':f.max;await field(f.key,expected[f.key]);}
      }
      assert.ok(initial!==await evaluate("document.querySelector('#creator-canvas').toDataURL()"));
      await click('[data-group=identity]');await evaluate("const name=document.querySelector('#player-name');name.value='测试旅人';name.dispatchEvent(new Event('input'))");
      await click('#save-player');await until("state.player?.name==='测试旅人'&&state.controlledId==='player'&&!document.querySelector('#player-editor').open");
      assert.deepEqual(town.state.player.appearance,expected);assert.equal(await evaluate("document.querySelector('.sprite.player img').naturalWidth"),128);assert.equal(await evaluate("document.querySelector('#population-label').textContent"),'6');
    });
    await check('Four directions, actions and live expression work in game',async()=>{
      for(const [key,dir]of [['w','back'],['a','left'],['s','front'],['d','right']]){await press(key);await new Promise(r=>setTimeout(r,30));town.tick(.5);emit();await release(key);assert.equal(town.state.player.direction,dir);}
      await click('#player-actions');await click('[data-player-action=cheer]');await until("state.player.action==='cheer'");town.tick(.5);emit();assert.equal(town.state.player.action,'cheer');assert.equal(town.state.controlledId,'player');
      await press('d');await new Promise(r=>setTimeout(r,30));town.tick(.5);emit();await release('d');assert.equal(town.state.player.action,'walk');
      await click('#player-actions');await click('[data-player-expression=happy]');await until("state.player.appearance.expression==='happy'");
    });
    await check('Direct action releases held keys so repeated keydown resumes movement',async()=>{
      await press('d');await new Promise(r=>setTimeout(r,30));await click('[data-action=greet]');await until("state.player.action==='greet'");
      assert.equal(await evaluate("held.size"),0);const x=town.state.player.x;await press('d');await new Promise(r=>setTimeout(r,30));town.tick(.5);emit();await release('d');assert.ok(town.state.player.x>x);
    });
    await click('#player-entry');await click('#edit-player');
    await check('Saved look resets and cancellation leaves player unchanged',async()=>{const saved=structuredClone(town.state.player.appearance);await click('#random-player');await click('#reset-player');await click('[data-group=face]');assert.equal(await evaluate("document.querySelector('[data-field=expression]').value"),saved.expression);await field('expression','sad');await click('#cancel-player');assert.deepEqual(town.state.player.appearance,saved);});
    await click('#edit-player');saveDelay=300;
    await check('Pending save disables inputs and rejects Escape/cancel',async()=>{
      await click('#save-player');assert.equal(await evaluate("Array.from(document.querySelector('#player-editor').querySelectorAll('button,input,select')).every(e=>e.disabled)"),true);
      assert.equal(await evaluate("document.querySelector('#player-editor').dispatchEvent(new Event('cancel',{cancelable:true}))"),false);await click('#cancel-player');assert.equal(await evaluate("document.querySelector('#player-editor').open"),true);
      await until("!document.querySelector('#player-editor').open&&state.controlledId==='player'");
    });
    await click('#player-entry');await click('#edit-player');failSave=true;saveDelay=10;
    await check('Failed save stays editable and preserves saved look',async()=>{const saved=structuredClone(town.state.player.appearance);await field('skin','#613D31');await click('#save-player');await until("!document.querySelector('#save-player').disabled");assert.equal(await evaluate("document.querySelector('#player-editor').open"),true);assert.deepEqual(town.state.player.appearance,saved);assert.match(await evaluate("document.querySelector('#toast').textContent"),/模拟写盘失败/);});
    await click('#cancel-player');await click('[data-settings-tab=residents]');assert.equal(await evaluate("document.querySelector('#player-settings').hidden"),true);
    failSave=false;saveDelay=0;await click('#back-game');
    await check('All eight preset players load daily atlases through CSP and play the selected gesture',async()=>{
      for(const preset of Appearance.gamePresets){
        town.state.player.appearance=Appearance.normalize({styleMode:'preset',avatarPreset:preset.id});town.state.player.direction='front';town.state.player.action='idle';town.state.player.target=null;emit();
        await evaluate("select('player')");
        for(const key of ['nod','shake_head','chat']){
          await click('#player-actions');await click('[data-player-action='+key+']');
          await until(`state.player.action===${JSON.stringify(key)}&&nodes.get('player').dataset.heroClip.startsWith(${JSON.stringify(preset.id+'/'+key+'/')})&&window.PlayerUI.isAnimationReady(state.player,${JSON.stringify(key)})`);
          assert.equal(await evaluate("nodes.get('player').querySelector('img').naturalWidth"),256);
        }
      }
      town.act('player','shake_head');emit();await until("state.player.action==='shake_head'");town.tick(1.2);emit();await until("state.player.action==='idle'");
    });
    assert.deepEqual(errors,[]);console.log(JSON.stringify({ok:true,checks:checks.length,fields:Appearance.fields.length,presetDailyClips:24,apiCalls:town.state.stats.length}));app.exit(0);
  }catch(e){console.error(e.stack);console.error(errors);app.exit(1);}
});
