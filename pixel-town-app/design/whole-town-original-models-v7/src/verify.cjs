const {chromium}=require('playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const R=path.resolve(__dirname,'..'),checks=[],errors=[];
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
function check(name,pass,details){checks.push({name,pass:!!pass,details});console.log(pass?'PASS':'FAIL',name);if(!pass)throw new Error(name+' '+JSON.stringify(details));}
(async()=>{const browser=await chromium.launch({channel:'chrome',headless:true});try{
 const page=await browser.newPage({viewport:{width:1440,height:1000},acceptDownloads:true});
 page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
 await page.goto('http://127.0.0.1:49335/原版模型整镇-离线预览.html',{waitUntil:'load',timeout:120000});
 await page.waitForFunction(()=>window.animalTown?.ready,null,{timeout:120000});
 const meta=JSON.parse(fs.readFileSync(path.join(R,'reference/runtime-animal-manifest.json')));
 await page.evaluate(()=>{animalTown.manual=true;townViewer.setTime(12);animalTown.environment.state.setWeather('sunny');});
 check('Matched originals load; all unmatched identities remain listed',await page.evaluate(()=>animalTown.avatars.size===ANIMAL_META.animals.length&&ANIMAL_META.animals.length+ANIMAL_META.pending.length===20&&document.querySelector('#pending-animals').textContent.includes('麦粒')));
 check('No custom / rejected animal model is embedded',await page.evaluate(()=>Object.keys(ANIMAL_ASSETS).length===ANIMAL_META.animals.length&&ANIMAL_META.animals.every(p=>p.sourceModel.startsWith('animal-'))));
 for(const p of meta.animals){
  await page.selectOption('#animal-select',p.id);
  const dims=await page.evaluate(id=>{const w=animalTown,a=w.sim.get(id),avatar=w.avatars.get(id);w.sim.cancel();a.state='idle';a.path=[];a.velocity=0;w.draw(0);avatar.mixer.update(1);avatar.mixer.update(0);avatar.root.updateMatrixWorld(true);let min=Infinity,max=-Infinity;const V=w.camera.position.constructor;avatar.model.traverse(o=>{if(o.isMesh){o.computeBoundingBox?.();const b=o.boundingBox||o.geometry.boundingBox;for(const x of [b.min.x,b.max.x])for(const y of [b.min.y,b.max.y])for(const z of [b.min.z,b.max.z]){const v=new V(x,y,z).applyMatrix4(o.matrixWorld);min=Math.min(min,v.y);max=Math.max(max,v.y);}}});return {feet:min-a.position[1],height:max-min,target:a.height,scale:avatar.model.parent.scale.toArray(),clip:avatar.actions[avatar.clip].getClip().name};},p.id);
  check(p.id+' uniform fit and feet at actual town ground',Math.abs(dims.feet)<.025&&Math.abs(dims.height-dims.target)<.025&&dims.scale.every(s=>Math.abs(s-dims.scale[0])<1e-9),dims);
  const motion=await page.evaluate(id=>{const v=animalTown.avatars.get(id),actions=[...new Set(Object.values(v.actions))];let changed=0,finite=true;for(const a of actions){v.mixer.stopAllAction();a.reset().play();a.time=a.getClip().duration*.2;v.mixer.update(0);v.root.updateMatrixWorld(true);const before=[];v.model.traverse(o=>before.push(...o.matrixWorld.elements));a.time=a.getClip().duration*.65;v.mixer.update(0);v.root.updateMatrixWorld(true);const after=[];v.model.traverse(o=>after.push(...o.matrixWorld.elements));finite=finite&&after.every(Number.isFinite);if(after.some((v,i)=>Math.abs(v-before[i])>1e-5))changed++;}v.clip=null;animalTown.draw(0);return {count:actions.length,changed,finite};},p.id);
  check(p.id+' all original clips run in town',motion.count===p.actions.length&&motion.changed===motion.count&&motion.finite,motion);
  await page.evaluate(id=>{const w=animalTown,a=w.sim.get(id);w.sim.cancel();a.state='idle';a.path=[];a.velocity=0;w.avatars.get(id).clip=null;w.select(id,true);w.draw(0);},p.id);
  await page.waitForTimeout(180);await page.screenshot({path:path.join(R,'qa',p.id+'-town.png')});
 }
 const nativeHuman=await page.evaluate(()=>{const h=animalTown.human;return [...new Set(Object.values(h.actions))].map(a=>a.getClip().name);});
 check('Caretaker is complete native character with 24 original clips',nativeHuman.length===24&&nativeHuman.every(n=>n.startsWith('CharacterArmature|')),nativeHuman);
 const humanMotion=await page.evaluate(()=>{const v=animalTown.human,actions=[...new Set(Object.values(v.actions))];let changed=0,finite=true;for(const a of actions){v.mixer.stopAllAction();a.reset().play();a.time=a.getClip().duration*.2;v.mixer.update(0);v.root.updateMatrixWorld(true);const before=[];v.model.traverse(o=>before.push(...o.matrixWorld.elements));a.time=a.getClip().duration*.65;v.mixer.update(0);v.root.updateMatrixWorld(true);const after=[];v.model.traverse(o=>after.push(...o.matrixWorld.elements));finite=finite&&after.every(Number.isFinite);if(after.some((v,i)=>Math.abs(v-before[i])>1e-5))changed++;}v.clip=null;animalTown.draw(0);return {count:actions.length,changed,finite};});
 check('All 24 native human animations remain functional',humanMotion.count===24&&humanMotion.changed===24&&humanMotion.finite,humanMotion);
 check('Missing petting motion is explicitly unavailable',await page.locator('[data-animal-interaction="pet"]').isDisabled());
 const dog='07_dog_shiba';
 for(const command of ['feed','call','fetch','walk']){
  const result=await page.evaluate(({id,kind})=>{const w=animalTown;w.select(id,true);w.localVisit();const start=w.sim.events.length,r=w.command(id,kind);let active=false,native=null;for(let i=0;i<2600;i++){w.advance(.05);if(w.sim.human.task?.phase==='active'){active=true;native=w.human.actions[w.human.clip].getClip().name;}if(!w.sim.human.task)break;}return {ok:r.ok,active,native,events:w.sim.events.slice(start).map(e=>e.kind),phase:w.sim.human.phase};},{id:dog,kind:command});
  check(command+' completes with native character and original animal',result.ok&&result.active&&result.events.includes(command+'-complete'),result);
  if(command==='feed'){await page.evaluate(id=>{animalTown.localVisit();animalTown.command(id,'feed');for(let i=0;i<2000;i++){animalTown.advance(.05);if(animalTown.sim.human.phase==='feeding'){animalTown.advance(.5);break;}}},dog);await page.waitForTimeout(180);await page.screenshot({path:path.join(R,'qa/feed-native.png')});const visible=await page.evaluate(()=>{const root=animalTown.human.root,V=townViewer.camera.position.constructor,points=[];root.updateMatrixWorld(true);root.traverse(o=>{if(o.isMesh){o.computeBoundingBox?.();const b=o.boundingBox||o.geometry.boundingBox;for(const x of [b.min.x,b.max.x])for(const y of [b.min.y,b.max.y])for(const z of [b.min.z,b.max.z])points.push(new V(x,y,z).applyMatrix4(o.matrixWorld).project(townViewer.camera));}});return points.every(p=>Math.abs(p.x)<.98&&Math.abs(p.y)<.98&&p.z>-1&&p.z<1);});check('Interaction camera contains full native human',visible);await page.evaluate(()=>animalTown.sim.cancel());}
 }
 const social=await page.evaluate(id=>{const w=animalTown;w.sim.cancel();const start=w.sim.events.length,r=w.command(id,'social');for(let i=0;i<1000;i++){w.advance(.05);if(w.sim.events.slice(start).some(e=>e.kind==='social-complete'))break;}return {ok:r.ok,events:w.sim.events.slice(start).map(e=>e.kind)};},dog);
 check('Native dogs approach and complete companion interaction',social.ok&&social.events.includes('social-greeting')&&social.events.includes('social-complete'),social);
 const navigation=await page.evaluate(()=>{animalTown.sim.cancel();animalTown.advance(45);return animalTown.sim.animals.map(a=>({id:a.id,finite:a.position.every(Number.isFinite),legal:a.grid.legal(a.position[0],a.position[2])}));});
 check('All source animals remain on valid town routes',navigation.every(a=>a.finite&&a.legal),navigation);
 await page.evaluate(()=>{animalTown.sim.cancel();animalTown.environment.state.setWeather('rain');animalTown.advance(110);});
 const shelter=await page.evaluate(()=>animalTown.sim.animals.map(a=>({id:a.id,state:a.state,distance:Math.hypot(a.position[0]-a.restSlot[0],a.position[2]-a.restSlot[2]),position:a.position,restSlot:a.restSlot,path:a.path.length,blocked:a.blocked,radius:a.radius})));check('Rain shelter remains functional with source proportions',shelter.every(a=>a.state==='rest'&&a.distance<.2),shelter);
 await page.evaluate(()=>{townViewer.setTime(22);animalTown.advance(30);});
 check('Night rest remains functional',await page.evaluate(()=>animalTown.sim.animals.every(a=>a.state==='rest')));
 await page.evaluate(id=>{townViewer.setTime(12);animalTown.environment.state.setWeather('sunny');animalTown.select(id,true);},dog);
 const downloadPromise=page.waitForEvent('download');await page.click('#animal-download');const download=await downloadPromise,tmp=path.join(R,'qa/download.glb');await download.saveAs(tmp);
 check('Downloaded source GLB has unchanged bytes',hash(fs.readFileSync(tmp))===hash(fs.readFileSync(path.join(R,meta.animals.find(a=>a.id===dog).glb))));fs.unlinkSync(tmp);
 await page.setViewportSize({width:390,height:844});await page.evaluate(()=>window.scrollTo(0,0));await page.waitForTimeout(200);
 check('390px layout has no horizontal overflow',await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.screenshot({path:path.join(R,'qa/mobile.png')});
 await page.setViewportSize({width:1440,height:1000});await page.evaluate(()=>{animalTown.sim.cancel();townViewer.district('all');townViewer.view('exterior');window.scrollTo(0,0);});await page.waitForTimeout(180);await page.screenshot({path:path.join(R,'qa/whole-town.png')});
 await page.close();const local=await browser.newPage({viewport:{width:1200,height:850}}),requests=[];local.on('pageerror',e=>errors.push(e.message));await local.route(/^https?:/,r=>{requests.push(r.request().url());r.abort();});
 await local.goto('file://'+path.join(R,'原版模型整镇-离线预览.html'),{timeout:120000});await local.waitForFunction(()=>window.animalTown?.ready,null,{timeout:120000});
 check('Offline file opens original models in full town',requests.length===0&&await local.evaluate(()=>animalTown.avatars.size===ANIMAL_META.animals.length),requests);
 check('No browser application errors',errors.length===0,errors);
 }finally{await browser.close();fs.writeFileSync(path.join(R,'qa/browser-validation.json'),JSON.stringify({checks,errors,status:checks.every(c=>c.pass)&&!errors.length?'PASS':'FAIL'},null,2));}
})().catch(e=>{console.error(e);process.exitCode=1;});
