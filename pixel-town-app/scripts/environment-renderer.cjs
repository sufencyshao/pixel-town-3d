'use strict';
// Actual Electron renderer, isolated town, all network / paid API calls disabled.
const {app,BrowserWindow,ipcMain}=require('electron');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),assert=require('node:assert/strict');
const root=process.env.TOWN_TEST_APP_ROOT||path.join(__dirname,'..'),report=path.join(__dirname,'../build/validation/day-night-v0.6.0');
const {Town}=require(path.join(root,'main/engine')),{initialState,catalog,petCatalog}=require(path.join(root,'main/catalog'));
const data=fs.mkdtempSync(path.join(os.tmpdir(),'town-time-ui-'));app.setPath('userData',data);
let win;
app.whenReady().then(async()=>{
  const town=new Town(initialState(),{chatCompletion:()=>{throw new Error('This check must never call API');}});
  const librarian=town.state.residents.find(r=>r.asset==='16_librarian_female');
  town.setRoster(town.state.residents.filter(r=>['16_librarian_female','01_hero_male','05_carpenter_male','03_barista_male','02_hero_female','09_gardener_male'].includes(r.asset)).map(r=>r.id));
  town.configure({running:false});town.state.clock=720;
  town.active().forEach((r,i)=>{r.x=420+i%3*400;r.y=380+Math.floor(i/3)*300;r.action='idle';r.remaining=1000;});
  librarian.x=1220;librarian.y=680;town.act(librarian.id,'walk',{x:1450,y:680});librarian.direction='right';
  const commands={'town:get':()=>({state:town.snapshot(),catalog,petCatalog,dataDir:'isolated-time-check',encrypted:true}),'town:config':c=>town.configure(c),'town:time':m=>town.advanceTo(m),'town:input':v=>town.setInput(v)};
  for(const [name,fn]of Object.entries(commands))ipcMain.handle(name,async(_,...args)=>{try{const value=await fn(...args);win.webContents.send('town:snapshot',town.snapshot());return{ok:true,value};}catch(e){return{ok:false,error:e.message};}});
  const errors=[];win=new BrowserWindow({show:false,width:1480,height:960,webPreferences:{preload:path.join(root,'main/preload.js'),sandbox:true,contextIsolation:true,nodeIntegration:false,backgroundThrottling:false}});
  win.webContents.on('console-message',(_,level,message)=>{if(level>=3)errors.push(message);});
  const evaluate=code=>win.webContents.executeJavaScript(code,true);
  const until=async code=>{const stop=Date.now()+10000;while(Date.now()<stop){if(await evaluate(code))return;await new Promise(resolve=>setTimeout(resolve,40));}throw new Error('Timed out: '+code);};
  const emit=()=>win.webContents.send('town:snapshot',town.snapshot());
  try{
    await win.loadFile(path.join(root,'renderer/index.html'));
    await until(`!!state&&nodes.get('${librarian.id}')?.dataset.clip==='walk_right'`);
    assert.ok(await evaluate(`nodes.get('${librarian.id}').querySelector('.atlas-sprite').style.clipPath.startsWith('inset(')`));
    assert.ok(parseFloat(await evaluate(`nodes.get('${librarian.id}').querySelector('.atlas-sprite').style.translate`))<0,'contaminated normalization is recentered');
    for(let n=0;n<16;n++){
      await evaluate(`animationTime=Number(nodes.get('${librarian.id}').dataset.clipAt)+${n*80+1};new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))`);
      assert.ok(await evaluate(`nodes.get('${librarian.id}').querySelector('.atlas-sprite').style.clipPath.startsWith('inset(')`),'every phase is clipped');
    }
    const hero=await evaluate(`(async()=>{
      const r=state.residents.find(r=>r.id==='${librarian.id}');await PresetAvatar.ensureLoaded(r.asset,r.animation);await PresetAvatar.ensureAnimation(r.asset,'walk_right');
      const source=await new Promise((resolve,reject)=>{const im=new Image();im.onload=()=>{const c=document.createElement('canvas');c.width=im.naturalWidth;c.height=im.naturalHeight;const ctx=c.getContext('2d',{willReadFrequently:true});ctx.drawImage(im,0,0);resolve(ctx.getImageData(0,0,256,256).data);};im.onerror=reject;im.src='../assets/'+r.assetFolder+'/animations/walk_right.png';});
      const rendered=PresetAvatar.renderAnimationPixels({avatarPreset:r.asset},'walk_right',0),bound=r.animation.animations.walk_right.visibleBounds[0],dx=r.animation.animations.walk_right.offsetX;
      let retained=0,removed=0,errors=0;
      for(let y=0;y<256;y++)for(let x=0;x<256;x++){
        const a=(y*256+x)*4;if(!source[a+3])continue;
        if(x<bound[0]||x>=bound[2]||y<bound[1]||y>=bound[3]){removed++;continue;}
        retained++;const b=(y*256+x+dx)*4;for(let q=0;q<4;q++)if(source[a+q]!==rendered.data[b+q])errors++;
      }
      const alpha=new Set();for(let i=3;i<rendered.data.length;i+=4)alpha.add(rendered.data[i]);
      return {retained,removed,errors,alpha:[...alpha].sort()};
    })()`);
    assert.ok(hero.removed>300);assert.ok(hero.retained>10000);assert.equal(hero.errors,0);assert.deepEqual(hero.alpha,[0,255]);
    await evaluate(`select('${librarian.id}');frameOverride=7;animationTime+=1;new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))`);
    await until(`!nodes.get('${librarian.id}').querySelector('img').hidden&&nodes.get('${librarian.id}').querySelector('img').complete`);
    assert.ok(await evaluate(`nodes.get('${librarian.id}').querySelector('img').style.clipPath.startsWith('inset(')`));
    await evaluate('frameOverride=null');
    fs.mkdirSync(report,{recursive:true});
    const phases=[];
    for(const [minute,label,file]of [[370,'日出','sunrise'],[720,'白昼','noon'],[1070,'日落','sunset'],[1320,'夜晚','moonlight']]){
      town.state.clock=minute;emit();await until(`document.querySelector('#time-phase').textContent==='${label}'`);
      await evaluate('new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))');
      fs.writeFileSync(path.join(report,file+'.png'),(await win.webContents.capturePage()).toPNG());
      if(file==='noon'){
        const rect=await evaluate(`(()=>{const b=nodes.get('${librarian.id}').getBoundingClientRect();return{x:Math.floor(b.left-30),y:Math.floor(b.top-10),width:Math.ceil(b.width+60),height:Math.ceil(b.height+35)};})()`);
        fs.writeFileSync(path.join(report,'librarian-fixed.png'),(await win.webContents.capturePage(rect)).toPNG());
      }
      phases.push({minute,label,sun:await evaluate("!document.querySelector('#sun').hidden"),moon:await evaluate("!document.querySelector('#moon').hidden")});
    }
    assert.equal(phases[0].sun,true);assert.equal(phases[3].moon,true);
    const moonAt=await evaluate("document.querySelector('#moon').style.left");town.tick(.5);emit();await new Promise(r=>setTimeout(r,150));assert.equal(await evaluate("document.querySelector('#moon').style.left"),moonAt);
    town.configure({running:true,speed:4});town.tick(.25);town.configure({running:false});emit();await until("state.clock===1321");assert.notEqual(await evaluate("document.querySelector('#moon').style.left"),moonAt);
    win.setSize(1040,720);await new Promise(r=>setTimeout(r,80));
    await evaluate("document.querySelector('#time-button').click()");
    assert.ok(await evaluate("(()=>{const m=document.querySelector('#modal'),b=m.getBoundingClientRect();return m.open&&b.left>=0&&b.top>=0&&b.right<=innerWidth&&b.bottom<=innerHeight&&m.scrollWidth<=m.clientWidth;})()"));
    await evaluate(`document.querySelector('[data-time="360"]').click()`);await until("state.clock===1800");
    assert.equal(town.state.stats.length,0);assert.equal(town.state.running,false);assert.equal(await evaluate("document.querySelector('#day').textContent"),'第 2 天');
    fs.writeFileSync(path.join(report,'small-window.png'),(await win.webContents.capturePage()).toPNG());
    assert.deepEqual(errors,[]);
    const result={ok:true,phases,librarianWalkPhases:16,baseFrameClipped:true,presetBodyPixels:hero.retained,presetRemovedFragmentPixels:hero.removed,presetAlpha:hero.alpha,pause:true,speed:true,timeChoiceRollover:true,smallWindow:true,apiCalls:0,appRoot:root};
    fs.writeFileSync(path.join(report,'renderer-result.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
  }catch(e){console.error(e.stack);console.error(errors);process.exitCode=1;}
  finally{win?.destroy();fs.rmSync(data,{recursive:true,force:true});app.exit(process.exitCode||0);}
});
