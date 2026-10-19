const {chromium}=require('playwright'),fs=require('fs'),path=require('path'),crypto=require('crypto');
const R=path.resolve(__dirname,'..'),checks=[],errors=[];
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
function check(name,pass,details){checks.push({name,pass:!!pass,details});if(!pass)throw new Error(name+' '+JSON.stringify(details));}
(async()=>{const b=await chromium.launch({channel:'chrome',headless:true});try{
 const p=await b.newPage({viewport:{width:1440,height:1000},acceptDownloads:true});p.on('pageerror',e=>errors.push(e.message));p.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
 await p.goto('http://127.0.0.1:49336/写实动物-原版预览.html');await p.waitForFunction(()=>window.originalViewer?.ready);
 check('Only realistic rabbit remains in active gallery',await p.evaluate(()=>ORIGINAL_META.length===1&&originalViewer.selected==='rabbit'));
 const motion=await p.evaluate(()=>{const s=originalViewer;let positive=0,poses=0,changed=0,finite=true;s.paused=true;for(const clip of s.current.userData.clips){s.mixer.stopAllAction();const a=s.mixer.clipAction(clip);a.reset().play();a.time=clip.duration*.2;s.mixer.update(0);s.current.updateMatrixWorld(true);const before=[];s.current.traverse(o=>before.push(...o.matrixWorld.elements));a.time=clip.duration*.65;s.mixer.update(0);s.current.updateMatrixWorld(true);const after=[];s.current.traverse(o=>after.push(...o.matrixWorld.elements));finite=finite&&after.every(Number.isFinite);if(clip.duration>0){positive++;if(before.some((v,i)=>Math.abs(v-after[i])>1e-5))changed++;}else poses++;}s.setAction('Guarding');s.mixer.update(.1);s.view('full');return {positive,poses,changed,finite};});
 check('Original seven timed clips and two static poses load',motion.positive===7&&motion.poses===2&&motion.finite&&motion.changed>=5,motion);
 for(const view of ['full','back','side']){await p.click('[data-view="'+view+'"]');await p.waitForTimeout(120);await p.screenshot({path:path.join(R,'qa','realistic-rabbit-'+view+'.png')});}
 await p.click('[data-view="full"]');await p.selectOption('#action','Running');await p.locator('#timeline').evaluate(e=>{e.value='550';e.dispatchEvent(new Event('input',{bubbles:true}));});
 check('Native running clip scrubs correctly',await p.evaluate(()=>Math.abs(originalViewer.active.time/originalViewer.active.getClip().duration-.55)<.001));
 await p.selectOption('#action','Guarding');await p.check('#bones');check('Native rig can be inspected',await p.evaluate(()=>originalViewer.scene.children.some(o=>o.isSkeletonHelper&&o.visible)));await p.uncheck('#bones');
 const event=p.waitForEvent('download');await p.click('#download');const download=await event,tmp=path.join(R,'qa/download.glb');await download.saveAs(tmp);check('Download matches converted file',hash(fs.readFileSync(tmp))===hash(fs.readFileSync(path.join(R,'assets/rabbit.glb'))));fs.unlinkSync(tmp);
 await p.setViewportSize({width:390,height:844});await p.waitForTimeout(160);check('390px layout',await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 await p.close();const local=await b.newPage(),requests=[];await local.route(/^https?:/,r=>{requests.push(r.request().url());r.abort();});local.on('pageerror',e=>errors.push(e.message));await local.goto('file://'+path.join(R,'写实动物-原版预览.html'));await local.waitForFunction(()=>window.originalViewer?.ready);check('Offline file preview needs no network',requests.length===0&&await local.evaluate(()=>originalViewer.selected==='rabbit'),requests);
 check('No application errors',errors.length===0,errors);
 }finally{await b.close();fs.writeFileSync(path.join(R,'qa/browser-validation.json'),JSON.stringify({checks,errors,status:checks.every(c=>c.pass)&&!errors.length?'PASS':'FAIL'},null,2));}
})().catch(e=>{console.error(e);process.exitCode=1;});
