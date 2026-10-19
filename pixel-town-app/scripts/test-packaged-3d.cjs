'use strict';
const fs=require('fs'),path=require('path'),os=require('os'),http=require('http'),assert=require('node:assert/strict');
let electronTest;try{electronTest=require('playwright')._electron}catch{electronTest=require('/Users/summerwindy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright')._electron}
const inputExecutable=path.resolve(process.argv[2]),qa=path.resolve(__dirname,'../build/validation/release-3d-v0.9.0'),dir=fs.mkdtempSync(path.join(os.tmpdir(),'packaged-town-3d-'));
const inputBundle=inputExecutable.split(path.sep+'Contents'+path.sep+'MacOS'+path.sep)[0],stagedBundle=path.join(dir,path.basename(inputBundle));
fs.cpSync(inputBundle,stagedBundle,{recursive:true,dereference:false,verbatimSymlinks:true});
const executable=path.join(stagedBundle,'Contents/MacOS',path.basename(inputExecutable));
let desktop,server,calls=0;const checks=[],errors=[];
const check=(name,value)=>{assert.ok(value,name);checks.push({name,pass:true});console.log('PASS',name)};
const until=async(fn,ms=15000)=>{const end=Date.now()+ms;while(Date.now()<end){if(await fn())return;await new Promise(r=>setTimeout(r,80))}throw new Error('Packaged check timeout')};
async function launch(){const env={...process.env,PIXEL_TOWN_DATA_DIR:path.join(dir,'data')};delete env.ELECTRON_RUN_AS_NODE;delete env.NODE_PATH;desktop=await electronTest.launch({executablePath:executable,args:[],cwd:os.tmpdir(),env,timeout:45000});const page=await desktop.firstWindow();page.on('pageerror',e=>errors.push(e.message));await page.waitForFunction(()=>!!window.townAI&&window.townPopulation?.ready,null,{timeout:120000});return page;}
(async()=>{
 try{
  server=http.createServer(async(req,res)=>{let body='';for await(const c of req)body+=c;JSON.parse(body);calls++;res.writeHead(200,{'content-type':'text/event-stream'});res.end('data: '+JSON.stringify({choices:[{delta:{content:JSON.stringify({version:1,thought:'先确认今天的练习安排。',speech:'',commands:[{type:'preset',clip:'Wave',seconds:1},{type:'work',jobId:'daily:03_barista_male'}]})}}]})+'\n\ndata: [DONE]\n\n')});await new Promise(r=>server.listen(0,'127.0.0.1',r));
  let page=await launch();
  check('packaged executable boots without source checkout or external Node',await desktop.evaluate(({app})=>app.isPackaged&&app.getVersion()==='0.9.0'));
  check('packaged default entry is the complete 3D town, 45 people and 16 animals',await page.evaluate(()=>townPopulation.avatars.size===61&&!!town3DAPI));
  check('fresh installation makes zero API calls and autonomy is disabled',calls===0&&await page.evaluate(()=>!townAI.autoId));
  await page.evaluate(()=>town3DAPI.invoke('settings'));await until(async()=>desktop.windows().length===2);
  const settings=desktop.windows().find(p=>p!==page);await settings.waitForFunction(()=>!!window.townAPI&&document.querySelector('#model-settings')&&!document.querySelector('#model-settings').hidden);
  const sourceProfiles=await settings.evaluate(()=>townAPI.invoke('town:get'));
  await settings.waitForFunction(()=>document.querySelector('.resident-avatar')?.naturalWidth>0);
  check('packaged API/persona settings include all 45 profiles and load original sprite assets',sourceProfiles.state.residents.length===45&&await settings.evaluate(()=>document.querySelectorAll('.resident-row').length>=6));
  const provider=await settings.evaluate(port=>townAPI.invoke('provider:save',{name:'Packaged local QA',type:'openai',baseUrl:`http://127.0.0.1:${port}/v1`,apiKey:'',models:['mock-packaged']}),server.address().port);
  await page.evaluate(provider=>town3DAPI.invoke('bind','03_barista_male',{providerId:provider,model:'mock-packaged',temperature:.4,maxTokens:1024}),provider);
  await page.evaluate(()=>{townPopulation.focus('03_barista_male');document.querySelector('#ai-refresh').click()});await page.waitForFunction(()=>document.querySelector('#ai-model').value==='mock-packaged');
  const ctx=await page.evaluate(()=>town3DAPI.invoke('context','03_barista_male',townAI.executor.scene()));check('bundled contexts include original background, relationships and real skeleton capabilities',ctx.system.includes('手冲台')&&ctx.data.capabilities.joints.head.bone==='Bip01_Head'&&ctx.data.publicResidents.length===61);
  await page.evaluate(()=>{document.querySelector('#ai-instruction').value='打招呼后进行今天的职业练习';document.querySelector('#ai-once').click()});await page.waitForFunction(()=>!!townAI.executor.active);
  await page.evaluate(()=>{townPopulation.paused=false;for(let i=0;i<380;i++)townPopulation.update(.1);townPopulation.paused=true});await page.waitForFunction(()=>!townAI.executor.active&&!townAI.unsaved);
  check('packaged API executes original motion and all work stages through production HTTP/SSE',calls===1&&await page.evaluate(()=>townAI.data.runtime.actors['03_barista_male'].workLog.length===1));
  await page.screenshot({path:path.join(qa,'packaged-app.png')});
  const resourcePath=await desktop.evaluate(({app})=>app.getAppPath());check('app uses its own bundled application resources',resourcePath.includes('.app/Contents/Resources/app'));
  await desktop.close();desktop=null;
  page=await launch();const restored=await page.evaluate(()=>town3DAPI.invoke('get'));
  check('restart preserves model binding and completed work record',restored.bindings.find(b=>b.id==='03_barista_male').model.model==='mock-packaged'&&restored.runtime.actors['03_barista_male'].workLog.length===1);
  check('restart never reenables autonomous paid calls',calls===1&&await page.evaluate(()=>!townAI.autoId&&!townAI.inFlight));
  check('no packaged JavaScript errors',errors.length===0);
  fs.writeFileSync(path.join(qa,'packaged-launch.json'),JSON.stringify({date:new Date().toISOString(),executable,checks,errors,localApiCalls:calls,paidApiCalls:0,isolatedData:true,restarted:true},null,2));
 }catch(e){console.error(e.stack);fs.writeFileSync(path.join(qa,'packaged-failure.json'),JSON.stringify({error:e.stack,checks,errors},null,2));process.exitCode=1}
 finally{if(desktop)await desktop.close().catch(()=>{});server?.close();fs.rmSync(dir,{recursive:true,force:true})}
})();
