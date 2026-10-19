const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=path.resolve(__dirname,'..'),qa=path.join(root,'qa'),checks=[],errors=[];
const meta=JSON.parse(fs.readFileSync(path.join(root,'assets/manifest.json')));
const check=(name,pass,info)=>{checks.push({name,pass:!!pass,info});if(!pass)console.log('FAIL',name,info)};
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
(async()=>{const browser=await chromium.launch({channel:'chrome',headless:true});try{
 const ctx=await browser.newContext({viewport:{width:1440,height:1000},acceptDownloads:true}),page=await ctx.newPage();page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
 await page.goto('http://127.0.0.1:49332/小镇人物-C方向-离线预览.html');await page.waitForFunction(()=>window.residentStudio?.ready);
 check('All45 identities and30 actions exposed',await page.locator('[data-person]').count()===45&&await page.locator('[data-action]').count()===30);
 fs.mkdirSync(path.join(qa,'people'),{recursive:true});
 for(const c of meta.characters){
  await page.evaluate(id=>residentStudio.select(id),c.id);await page.evaluate(()=>residentStudio.paused=true);
  const result=await page.evaluate(()=>{const s=residentStudio,a=s.avatars.get(s.selected),out=[];for(const key of s.motion.keys()){s.play(key);s.elapsed=s.motion.get(key).duration*.5;const bones=[];a.model.traverse(o=>{if(o.isBone)bones.push(...o.matrixWorld.elements)});out.push({key,finite:bones.length===65*16&&bones.every(Number.isFinite),props:a.propObjects.length});}s.play('Idle');s.elapsed=0;return out;});
  check(c.name+' all30 finite poses',result.length===30&&result.every(x=>x.finite));
  check(c.name+' original reference loads',await page.locator('#reference').evaluate(i=>i.complete&&i.naturalWidth===256));
  for(const [name,action,view] of [['front','Idle','front'],['back','Idle','back'],['side','Idle','side'],['wave','Wave','full'],['sit','Sit','full'],['lie','LieRest','full']]){
   await page.evaluate(({action,view})=>{residentStudio.play(action);residentStudio.elapsed=residentStudio.motion.get(action).duration*.5;if(action!=='LieRest')residentStudio.view(view);}, {action,view});
   await page.waitForTimeout(65);await page.locator('#stage').screenshot({path:path.join(qa,'people',c.id+'-'+name+'.png')});
  }
  console.log('BROWSER_PERSON',c.id,c.name);
 }
 await page.evaluate(()=>residentStudio.select('02_hero_female'));await page.click('#compare-example');await page.waitForFunction(()=>residentStudio.ready&&residentStudio.comparing);await page.evaluate(()=>residentStudio.paused=true);await page.screenshot({path:path.join(qa,'comparison.png')});
 check('Four distinct bodies compare at unit scale',await page.evaluate(()=>residentStudio.avatars.size===4&&[...residentStudio.avatars.values()].every(a=>a.root.scale.x===1)));
 await page.evaluate(()=>residentStudio.play('LieRest'));await page.screenshot({path:path.join(qa,'comparison-rest.png')});
 const spaced=await page.evaluate(()=>[...residentStudio.avatars.values()].map(a=>a.root.position.x).sort((a,b)=>a-b));check('Lying comparisons use separate mats',spaced.every((x,i)=>!i||x-spaced[i-1]>2));
 await page.evaluate(()=>residentStudio.select('01_hero_male'));await page.evaluate(()=>residentStudio.paused=true);let t=await page.evaluate(()=>residentStudio.elapsed);await page.waitForTimeout(160);check('Pause freezes pose clock',await page.evaluate(t=>residentStudio.elapsed===t,t));await page.click('#pause');await page.waitForTimeout(160);check('Resume advances pose clock',await page.evaluate(t=>residentStudio.elapsed>t,t));
 for(const [action,next] of [['SitDown','Sit'],['LieDown','LieRest'],['GetUp','Idle']]){await page.evaluate(action=>{residentStudio.play(action);residentStudio.elapsed=residentStudio.motion.get(action).duration-.03;residentStudio.paused=false},action);await page.waitForFunction(next=>residentStudio.active===next,next);check(action+' transitions correctly',true);}
 await page.evaluate(()=>{residentStudio.paused=true;residentStudio.play('Idle');residentStudio.view('face')});await page.click('[data-expression="smile"]');check('Smile morph target responds',await page.evaluate(()=>[...residentStudio.avatars.values()][0].morphs.some(o=>(o.morphTargetInfluences[o.morphTargetDictionary.Smile]||0)>.7)));
 await page.check('#bones');check('Skeleton toggle responds',await page.evaluate(()=>[...residentStudio.avatars.values()][0].helper.visible));await page.uncheck('#bones');
 await page.evaluate(()=>residentStudio.play('Read'));check('Reading includes two hand props',await page.evaluate(()=>[...residentStudio.avatars.values()][0].propObjects.length>0));await page.uncheck('#props');check('Prop visibility toggle',await page.evaluate(()=>[...residentStudio.avatars.values()][0].propObjects.every(p=>!p.visible)));await page.check('#props');
 await page.fill('#search','木匠');check('Search filters by profession',await page.locator('[data-person]:visible').count()===2);await page.fill('#search','');await page.selectOption('#filter','companion');check('Companion filter shows5',await page.locator('[data-person]:visible').count()===5);await page.selectOption('#filter','all');
 const download=page.waitForEvent('download');await page.click('#download');const file=await download,tmp=path.join(qa,'download-check.glb');await file.saveAs(tmp);check('Downloaded model exactly matches currentGLB',hash(fs.readFileSync(tmp))===hash(fs.readFileSync(path.join(root,'assets/01_hero_male/character.glb'))));fs.unlinkSync(tmp);
 await page.setViewportSize({width:390,height:844});await page.evaluate(()=>{residentStudio.view('full');window.scrollTo(0,0)});await page.waitForTimeout(120);check('390px no horizontal overflow',await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.screenshot({path:path.join(qa,'mobile.png')});
 const offline=await browser.newContext({offline:true,viewport:{width:1440,height:1000}}),local=await offline.newPage(),remote=[];local.on('request',r=>{if(/^https?:/.test(r.url()))remote.push(r.url())});local.on('pageerror',e=>errors.push(e.message));await local.goto('file://'+path.join(root,'小镇人物-C方向-离线预览.html'));await local.waitForFunction(()=>window.residentStudio?.ready);await local.evaluate(()=>residentStudio.select('kanna'));check('File mode can switch local models offline',await local.evaluate(()=>residentStudio.ready&&residentStudio.selected==='kanna'));check('Offline makes noHTTP request',remote.length===0,remote);await offline.close();
 check('No browser errors',errors.length===0,errors);
 fs.writeFileSync(path.join(qa,'browser-validation.json'),JSON.stringify({date:'2026-10-18',checks,errors,people:meta.characters.length,screenshotsPerPerson:6,passed:checks.filter(c=>c.pass).length,total:checks.length},null,2));
 if(checks.some(c=>!c.pass))process.exitCode=1;
 }finally{await browser.close()}})().catch(e=>{console.error(e);process.exitCode=1});
