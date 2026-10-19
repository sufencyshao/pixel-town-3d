'use strict';
const {app,BrowserWindow,ipcMain}=require('electron');
const fs=require('fs'),path=require('path'),os=require('os'),http=require('http'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),qa=path.join(root,'design/town-ai-v9/qa');
const {Town}=require('../main/engine'),{initialState,catalog,petCatalog}=require('../main/catalog'),{Town3DService}=require('../main/town-3d-service'),llm=require('../main/llm');
const capabilities=require('../design/town-ai-v9/capabilities.json').actors;
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'town-3d-ui-'));app.setPath('userData',dir);
let window,server,requests=0,goal;const checks=[],errors=[],bodies=[];const id='03_barista_male';
function check(name,value){assert.ok(value,name);checks.push({name,pass:true});console.log('PASS',name)}
app.whenReady().then(async()=>{
 try{
  server=http.createServer(async(req,res)=>{let raw='';for await(const c of req)raw+=c;const body=JSON.parse(raw);bodies.push(body);requests++;const instruction=body.messages.at(-1).content;
   let commands=[{type:'wait',seconds:1}],speech='';
   if(instruction.includes('组合'))commands=[{type:'preset',clip:'Wave',seconds:1},{type:'pose',joints:{head:[0,15,0]},seconds:2},{type:'work',jobId:'daily:'+id}];
   if(instruction.includes('移动'))commands=[{type:'move',destination:{x:goal[0],z:goal[2]},gait:'walk'}];
   if(instruction.includes('社交')){commands=[{type:'social',targetId:'04_baker_male'}];speech='麦麦，今天的面包练习顺利吗？'}
   if(instruction.includes('坏关节'))commands=[{type:'pose',joints:{root:[0,0,0]},seconds:1}];
   if(instruction.includes('取消'))await new Promise(r=>setTimeout(r,300));
   if(res.destroyed)return;
   res.writeHead(200,{'content-type':'text/event-stream'});const text=JSON.stringify({version:1,thought:'根据真实人设安排一小步。',speech,commands});
   // Split at an arbitrary UTF-8 byte boundary to exercise the production SSE decoder.
   const bytes=Buffer.from('data: '+JSON.stringify({choices:[{delta:{content:text}}]})+'\r\n\r\ndata: '+JSON.stringify({usage:{prompt_tokens:31,completion_tokens:13}})+'\n\ndata: [DONE]\n\n');res.write(bytes.subarray(0,71));res.end(bytes.subarray(71));
  });await new Promise(r=>server.listen(0,'127.0.0.1',r));
  const town=new Town(initialState(),llm);town.state.providers.push({id:'mock-3d',type:'openai',name:'本地模拟 API',baseUrl:`http://127.0.0.1:${server.address().port}/v1`,apiKey:'MOCK_PRIVATE_KEY_NEVER_IN_RENDERER',models:['local-model']});
  town.state.residents[2].model={providerId:'mock-3d',model:'local-model',temperature:.5,maxTokens:1024};
  const service=new Town3DService({town,llm,catalog:[...catalog,...petCatalog],capabilities,file:path.join(dir,'town-3d-life.json'),saveBindings(){}});
  for(const name of ['get','context','decide','cancel','receipt','bind','settings'])ipcMain.handle('town3d:'+name,async(event,...args)=>{if(event.sender!==window.webContents)return {ok:false,error:'wrong sender'};try{return {ok:true,value:name==='get'?service.initial():name==='settings'?true:await service[name](...args)}}catch(e){return {ok:false,error:e.message}}});
  window=new BrowserWindow({show:true,width:1480,height:960,webPreferences:{preload:path.join(root,'main/town-3d-preload.js'),sandbox:true,contextIsolation:true,nodeIntegration:false,backgroundThrottling:false}});
  window.webContents.on('console-message',(_,level,message)=>{if(level>=3)errors.push(message)});
  const evaluate=code=>window.webContents.executeJavaScript(code,true);
  const until=async(code,ms=15000)=>{const end=Date.now()+ms;while(Date.now()<end){if(await evaluate(code))return;await new Promise(r=>setTimeout(r,60))}throw new Error('Timed out: '+code)};
  await window.loadFile(path.join(root,'design/town-ai-v9/三维小镇-AI生活.html'));await until('!!window.townAI&&window.townPopulation?.ready',120000);
  check('actual WebGL town loads 45 people and 16 animals',await evaluate('townPopulation.avatars.size===61'));
  await evaluate(`townPopulation.focus(${JSON.stringify(id)});townPopulation.paused=true;townAI.syncSelection(true)`);
  const initial=await evaluate('townAI.executor.scene()');
  check('default autonomy is off and load has no API requests',requests===0&&!await evaluate('document.getElementById("ai-auto").checked'));
  const context=await evaluate(`town3DAPI.invoke('context',${JSON.stringify(id)},townAI.executor.scene())`);
  check('live IPC context includes original background and all public identities',context.data.publicResidents.length===61&&context.system.includes('手冲台')&&context.data.capabilities.joints.head.bone==='Bip01_Head');
  check('provider keys never cross preload or context',!JSON.stringify(await evaluate("town3DAPI.invoke('get')")).includes('MOCK_PRIVATE_KEY')&&!context.system.includes('MOCK_PRIVATE_KEY'));
  await evaluate("document.getElementById('ai-context').click()");await until("document.getElementById('ai-context-dialog').open");check('context preview is free',requests===0);await evaluate("document.getElementById('ai-context-close').click()");
  const decide=async text=>{await evaluate(`document.getElementById('ai-instruction').value=${JSON.stringify(text)};document.getElementById('ai-once').click()`);await until('!!townAI.executor.active||(!townAI.inFlight&&townAI.events[0]?.kind==="error")');};
  const advance=async seconds=>evaluate(`(()=>{townPopulation.paused=false;for(let i=0;i<${Math.ceil(seconds*10)};i++)townPopulation.update(.1);townPopulation.paused=true;return townAI.executor.snapshot()})()`);
  await decide('执行组合');check('real HTTP/SSE uses the selected provider and full 3D guide',requests===1&&bodies[0].model==='local-model'&&bodies[0].messages[0].content.includes('Bip01_Head'));
  check('first native preset starts',await evaluate("townPopulation.update(.1);townPopulation.avatars.get('03_barista_male').active==='Wave'"));
  await advance(1.5);check('pose changes actual head quaternion within limit',await evaluate(`(()=>{const a=townPopulation.avatars.get('${id}'),p=a.aiPose;if(!p)return false;const j=p.joints[0];return j.bone.quaternion.angleTo(j.base)>.1&&j.bone.quaternion.angleTo(j.base)<.28})()`));
  await advance(35);await until('!townAI.unsaved&&!townAI.executor.active');
  check('work stages finish and persist as practice rather than goods',service.runtime.actors[id]?.workLog.length===1&&service.runtime.actors[id].workLog[0].stages.length===3);
  check('pose is removed and original Idle returns',await evaluate(`!townPopulation.avatars.get('${id}').aiPose&&townPopulation.avatars.get('${id}').active==='Idle'`));
  goal=await evaluate(`(()=>{const e=townAI.executor,a=townPopulation.avatars.get('${id}'),from=a.root.position.toArray();for(const dx of [-1,1,0])for(const dz of [-1,1,0]){if(!dx&&!dz)continue;try{const path=e.nav.path(from,[from[0]+dx,0,from[2]+dz],e.blocked('${id}'));if(path.length>1)return path.at(-1)}catch{}}throw new Error('no test goal')})()`);
  await decide('请移动');await advance(8);await until('!townAI.unsaved&&!townAI.executor.active');const pos=await evaluate(`townPopulation.avatars.get('${id}').root.position.toArray()`);check('move follows actual public navigation and reaches destination',Math.hypot(pos[0]-goal[0],pos[2]-goal[2])<.02);
  await decide('发起社交');await advance(4);await until('!townAI.unsaved&&!townAI.executor.active');check('speech is delivered to the other person without inventing a reply',service.runtime.actors['04_baker_male']?.heard?.at(-1).text.includes('面包练习')&&!service.runtime.actors['04_baker_male']?.workLog?.length);
  const count=service.runtime.history.length;await decide('坏关节');check('invalid bones are rejected before scene execution',!await evaluate('!!townAI.executor.active')&&service.runtime.history.length===count);
  await evaluate("document.getElementById('ai-instruction').value='取消这次延迟请求';document.getElementById('ai-once').click()");await until('townAI.inFlight');await evaluate("document.getElementById('ai-stop').click()");await until('!townAI.inFlight');check('stop cancels an in-flight API response',!await evaluate('!!townAI.executor.active')&&service.executions.size===0);
  const beforeAuto=requests;await evaluate("townPopulation.paused=false;document.getElementById('ai-auto').checked=true;document.getElementById('ai-auto').dispatchEvent(new Event('change'))");await until('!!townAI.executor.active');await advance(2);await until('!townAI.unsaved');await evaluate("document.getElementById('ai-stop').click()");check('autonomy needs explicit opt-in and stops on request',requests===beforeAuto+1&&!await evaluate('townAI.autoId'));
  window.setSize(390,844);await new Promise(r=>setTimeout(r,400));check('390px layout has no horizontal overflow',await evaluate('document.documentElement.scrollWidth<=innerWidth+1'));
  await evaluate(`townPopulation.focus('${id}');document.querySelectorAll('.ai-card details')[1].open=true`);window.setSize(1480,960);await new Promise(r=>setTimeout(r,500));
  fs.writeFileSync(path.join(qa,'ai-workflow.png'),(await window.webContents.capturePage()).toPNG());
  check('no renderer or shader errors',errors.length===0);
  const afterContext=service.context(id,await evaluate('townAI.executor.scene()'));check('subsequent AI context contains engine execution feedback',afterContext.data.executionFeedback.length>=3&&afterContext.data.workLog.length===1);
  fs.writeFileSync(path.join(qa,'browser-validation.json'),JSON.stringify({date:new Date().toISOString(),checks,requests,errors,contextChars:context.system.length,isolatedData:true,paidCalls:0,protocol:'production llm.js + HTTP/SSE + sandbox preload + actual WebGL',initialActors:initial.actors.length},null,2));
  console.log('3D UI checks:',checks.length,'paid calls: 0');
 }catch(e){console.error(e.stack);fs.writeFileSync(path.join(qa,'browser-failure.json'),JSON.stringify({error:e.stack,checks,errors,requests},null,2));process.exitCode=1}
 finally{window?.destroy();server?.close();fs.rmSync(dir,{recursive:true,force:true});app.exit(process.exitCode||0)}
});
