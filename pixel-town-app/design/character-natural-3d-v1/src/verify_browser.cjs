const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto'),os=require('os');
const root=path.resolve(__dirname,'..'),qa=path.join(root,'qa');
const checks=[],errors=[];
const hash=data=>crypto.createHash('sha256').update(data).digest('hex');
function check(name,pass,info=null){if(!pass)throw new Error(name+' '+JSON.stringify(info));checks.push({name,pass,info});console.log('PASS',name);}
async function scrub(page,n){await page.locator('#timeline').evaluate((el,value)=>{el.value=String(value);el.dispatchEvent(new Event('input',{bubbles:true}));},n);await page.waitForTimeout(70);}
async function snap(page,name){await page.screenshot({path:path.join(qa,name+'.png')});}
async function morph(page,name){return page.evaluate(key=>avatarStudio.morphs.filter(o=>key in o.morphTargetDictionary).map(o=>o.morphTargetInfluences[o.morphTargetDictionary[key]]),name);}
async function pose(page,name,phase){await page.click('[data-action="'+name+'"]');await scrub(page,phase);return page.evaluate(()=>{avatarStudio.model.updateMatrixWorld(true);const a=[];avatarStudio.model.traverse(o=>{if(o.isBone)a.push(...o.matrixWorld.elements)});return a;});}
(async()=>{const browser=await chromium.launch({channel:'chrome',headless:true});try{
 const context=await browser.newContext({viewport:{width:1440,height:1000},acceptDownloads:true});
 const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
 await page.goto(process.env.PREVIEW_URL||'http://127.0.0.1:49329/阿澈-C方向-离线预览.html');await page.waitForFunction(()=>window.avatarStudio?.ready);
 check('C identity and 2D reference',await page.locator('h1').innerText()==='阿澈 · C 方向首版'&&await page.locator('.intro img').evaluate(i=>i.complete&&i.naturalWidth>0));
 const names=await page.evaluate(()=>Object.keys(avatarStudio.actions));check('all 19 clips exposed',names.length===19&&await page.locator('[data-action]').count()===19,names);
 await page.click('#pause');const paused=await page.evaluate(()=>avatarStudio.elapsed);await page.waitForTimeout(160);check('pause freezes clip',await page.evaluate(t=>avatarStudio.elapsed===t,paused));
 await page.click('#pause');await page.waitForTimeout(160);check('resume advances clip',await page.evaluate(t=>avatarStudio.elapsed>t,paused));
 await page.selectOption('#speed','1.5');check('speed control selected',await page.locator('#speed').inputValue()==='1.5');await page.selectOption('#speed','1');
 for(const name of names){const values=await pose(page,name,450);check(name+' selectable and finite',await page.evaluate(n=>avatarStudio.active===n&&avatarStudio.paused,name)&&values.length===65*16&&values.every(Number.isFinite));}
 for(const name of ['Walk','Wave','Nod','ShakeHead']){const a=await pose(page,name,100),b=await pose(page,name,350);check(name+' changes skeletal pose',Math.max(...a.map((v,i)=>Math.abs(v-b[i])))>.01);}
 await pose(page,'Sit',450);check('chair follows seated action',await page.evaluate(()=>avatarStudio.scene.getObjectByName('PreviewChair').visible));await snap(page,'sit');
 await pose(page,'Swim',450);check('swim demonstration offset and water',await page.evaluate(()=>avatarStudio.model.position.y===.6&&avatarStudio.scene.getObjectByName('PreviewWater').visible));await snap(page,'swim');
 await pose(page,'Idle',0);check('standing resets water and model offset',await page.evaluate(()=>avatarStudio.model.position.y===0&&!avatarStudio.scene.getObjectByName('PreviewWater').visible&&!avatarStudio.scene.getObjectByName('PreviewChair').visible));
 for(const [action,next] of [['SitDown','Sit'],['StandUp','Idle']]){await pose(page,action,990);await page.click('#pause');await page.waitForFunction(n=>avatarStudio.active===n,next);check(action+' transitions to '+next,await page.evaluate(n=>avatarStudio.active===n,next));}
 await pose(page,'Idle',0);await page.evaluate(()=>avatarStudio.seconds=1);await page.click('[data-view="full"]');await page.waitForTimeout(100);await snap(page,'full');
 for(const view of ['front','back','shoes','face']){await page.click('[data-view="'+view+'"]');check(view+' view control',await page.locator('[data-view="'+view+'"]').getAttribute('aria-pressed')==='true');if(view==='shoes'){await snap(page,'shoes');await page.locator('#stage').screenshot({path:path.join(qa,'shoes-detail.png')});}}
 await page.click('[data-expression="smile"]');await page.waitForTimeout(80);check('smile target responds',(await morph(page,'Smile')).every(v=>Math.abs(v-.85)<.001));await snap(page,'face-smile');
 await page.click('[data-expression="talk"]');await page.waitForTimeout(80);check('talk target responds',(await morph(page,'Talk')).every(v=>v>.24));
 await page.click('[data-expression="neutral"]');await page.evaluate(()=>avatarStudio.seconds=1);await page.waitForTimeout(80);check('neutral mouth closes',(await morph(page,'Talk')).every(v=>v===0));await snap(page,'face-open');
 await page.evaluate(()=>avatarStudio.seconds=.08);await page.waitForTimeout(80);check('blink closes eyelids',(await morph(page,'Blink')).every(v=>v>.99));await snap(page,'face-blink');
 await page.uncheck('#blink');await page.waitForTimeout(70);check('blink switch restores open eyes',(await morph(page,'Blink')).every(v=>v===0));await page.check('#blink');
 await page.check('#bones');check('skeleton enabled',await page.evaluate(()=>avatarStudio.helper.visible));await page.uncheck('#bones');check('skeleton disabled',await page.evaluate(()=>!avatarStudio.helper.visible));
 await page.click('[data-view="full"]');await pose(page,'Wave',450);await page.evaluate(()=>avatarStudio.seconds=1);await snap(page,'wave');
 const downloadEvent=page.waitForEvent('download');await page.click('#download');const download=await downloadEvent;const temp=fs.mkdtempSync(path.join(os.tmpdir(),'ache-glb-'));const target=path.join(temp,'model.glb');await download.saveAs(target);
 check('download bytes match GLB',hash(fs.readFileSync(target))===hash(fs.readFileSync(path.join(root,'assets/01-Ache.glb'))));fs.rmSync(temp,{recursive:true});
 await page.setViewportSize({width:390,height:844});await pose(page,'Idle',0);await page.evaluate(()=>{avatarStudio.seconds=1;window.scrollTo(0,0)});await page.waitForTimeout(120);check('390px page has no horizontal overflow',await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));check('mobile stage stays visible',await page.locator('#stage').evaluate(el=>el.clientHeight>=440&&el.clientWidth===390&&el.getBoundingClientRect().top>=0&&el.getBoundingClientRect().bottom<=innerHeight));await snap(page,'mobile');
 await page.locator('[data-action="Wave"]').click();check('mobile action control works',await page.evaluate(()=>avatarStudio.active==='Wave'));
 const offline=await browser.newContext({viewport:{width:1440,height:1000},offline:true});const local=await offline.newPage(),requests=[];local.on('request',r=>{if(/^https?:/.test(r.url()))requests.push(r.url())});local.on('pageerror',e=>errors.push(e.message));
 await local.goto('file://'+path.join(root,'阿澈-C方向-离线预览.html'));await local.waitForFunction(()=>window.avatarStudio?.ready);check('file opens fully offline',await local.evaluate(()=>Object.keys(avatarStudio.actions).length===19));check('offline preview makes no HTTP requests',requests.length===0,requests);await offline.close();
 check('no browser or shader errors',errors.length===0,errors);
 fs.writeFileSync(path.join(qa,'browser-validation.json'),JSON.stringify({date:'2026-10-17',checks,errors,viewports:[[1440,1000],[390,844]],note:'Chrome headless; visual screenshots also inspected. No claim of real mobile device QA.'},null,2));console.log('PASSED',checks.length);
 }finally{await browser.close()}})().catch(e=>{console.error(e);process.exitCode=1});
