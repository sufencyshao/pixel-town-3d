'use strict';
const {app,BrowserWindow,ipcMain}=require('electron');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),http=require('node:http'),assert=require('node:assert/strict');
const root=process.env.TOWN_TEST_APP_ROOT||path.join(__dirname,'..');
const {Town}=require(path.join(root,'main/engine')),{initialState,catalog,petCatalog}=require(path.join(root,'main/catalog'));
const {Journal}=require(path.join(root,'main/journal')),{Persistence}=require(path.join(root,'main/persistence')),Life=require(path.join(root,'shared/life'));
const llm=require(path.join(root,'main/llm'));
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'town-life-renderer-'));app.setPath('userData',dir);
const output=process.env.TOWN_LIFE_VALIDATION_DIR||path.join(__dirname,'../build/validation/model-life-v0.7.0');fs.mkdirSync(output,{recursive:true});
let win,server,requests=0;
app.whenReady().then(async()=>{
  const journal=new Journal(path.join(dir,'journals')),town=new Town(initialState(),llm,()=>{if(win&&!win.isDestroyed())win.webContents.send('town:snapshot',town.snapshot());},journal),lin=town.state.residents.find(r=>r.asset==='03_barista_male'),zhi=town.state.residents.find(r=>r.asset==='16_librarian_female');
  town.setRoster([lin.id,zhi.id]);const [a,b]=town.active();assert.equal(a.id,lin.id);b.decisionAt=Date.now();b.remaining=999;
  const goal={title:'活动一下，再了解邻居的兴趣',reason:'想把自己的日常过得丰富一点',status:'ongoing'},payloads=[];
  server=http.createServer(async(req,res)=>{
    let data='';for await(const chunk of req)data+=chunk;const body=JSON.parse(data);payloads.push(body);requests++;
    const response=requests===1?{action:'walk',thought:'想换换心情。<script>window.lifeAttacked=true</script>',speech:'',destination:{x:1230,y:290},goal}:
      requests===2?{action:'chat',thought:'好奇邻居会喜欢安静还是热闹',speech:'你觉得小镇多办一些活动会不会更好？',partnerId:b.id,goal}:
      requests===3?{action:'shake_head',thought:'我需要安静，也想说明自己的看法',speech:'我不完全同意，活动太多让我难以安静阅读。',interaction:{feeling:-1,continue:true},goal:{title:'表达自己的阅读习惯',reason:'希望邻居理解彼此节奏不同',status:'ongoing'}}:
      {action:'nod',thought:'理解各自的节奏，就先回去做自己的事情。',speech:'说得有道理，我们保留各自的安排，晚点再聊。',interaction:{feeling:2,continue:false},goal:{...goal,reason:'走过一段路，也听到了邻居真实的想法',status:'completed'}};
    res.writeHead(200,{'content-type':'text/event-stream'});res.end('data: '+JSON.stringify({choices:[{delta:{content:JSON.stringify(response)}}]})+'\n\ndata: '+JSON.stringify({usage:{prompt_tokens:17,completion_tokens:19}})+'\n\ndata: [DONE]\n\n');
  });
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  town.state.providers.push({id:'life-ui',name:'隔离测试 API',type:'openai',baseUrl:'http://127.0.0.1:'+server.address().port+'/v1',models:['life-ui-model'],apiKey:'life-renderer-secret'});
  for(const r of [a,b])r.model={providerId:'life-ui',model:'life-ui-model',temperature:.5,maxTokens:600};
  town.configure({running:true,autonomous:true});a.remaining=0;a.target=null;town.state.lastApiAt=0;
  const safe={isEncryptionAvailable:()=>true,encryptString:s=>Buffer.from(s),decryptString:v=>v.toString()},store=new Persistence(dir,safe);
  const commands={
    'town:get':()=>({state:town.snapshot(),catalog,petCatalog,dataDir:'isolated-life-ui',encrypted:true}),
    'town:config':x=>town.configure(x),'town:input':p=>town.setInput(p),
    'town:knowledge':x=>{const value=Life.validateWorld(x);store.save({...town.state,worldInfo:value});town.setKnowledge(value);},
    'town:life':(id,x)=>{const candidate=structuredClone(town.state);candidate.residents.find(r=>r.id===id).life=town.prepareLife(id,x);store.save(candidate);town.setLife(id,x);},
    'town:context':id=>({name:town.entity(id).name,system:town.prompt(town.entity(id)),paidCall:false}),
    'journal:get':(id,x)=>journal.page(id,x),'journal:subjects':()=>[...journal.subjects.values()],
    'journal:export':(id,day)=>{fs.writeFileSync(path.join(output,'ui-export-diary.md'),journal.markdown(id,day));return true;}
  };
  const notify=()=>win.webContents.send('town:snapshot',town.snapshot());
  for(const [name,fn]of Object.entries(commands))ipcMain.handle(name,async(_,...args)=>{try{const value=await fn(...args);notify();return {ok:true,value};}catch(e){notify();return {ok:false,error:e.message};}});
  const errors=[];win=new BrowserWindow({show:false,width:1480,height:960,webPreferences:{preload:path.join(root,'main/preload.js'),sandbox:true,contextIsolation:true,nodeIntegration:false,backgroundThrottling:false}});
  win.webContents.on('console-message',(_,level,message)=>{if(level>=3)errors.push(message);});
  const evaluate=code=>win.webContents.executeJavaScript(code,true),until=async(code)=>{const end=Date.now()+15000;while(Date.now()<end){if(await evaluate(code))return;await new Promise(resolve=>setTimeout(resolve,35));}throw new Error('Timed out: '+code);};
  const image=async name=>{await evaluate('new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))');await new Promise(resolve=>setTimeout(resolve,100));const shot=await win.webContents.capturePage();fs.writeFileSync(path.join(output,name),shot.toPNG());};
  const ticks=n=>{for(let i=0;i<n;i++)town.tick(.25);notify();};
  try{
    await win.loadFile(path.join(root,'renderer/index.html'));await until("!!state&&document.querySelectorAll('.sprite').length===2");
    // No user-facing decide, act, move, talk or chat command is used to initiate this life sequence.
    town.tick(.1);await until('state.busy===false&&state.stats.length===1');notify();
    assert.equal(requests,1);assert.equal(a.action,'walk');assert.equal(a.life.focus.title,goal.title);assert.ok(payloads[0].messages[0].content.includes('2D 像素生活'));assert.ok(payloads[0].messages[0].content.includes('occupationalReference'));
    ticks(200);town.state.lastApiAt=0;town.tick(.1);await until('!state.busy&&state.stats.length===2');
    assert.equal(requests,2);assert.equal(a.meeting?.partner,b.id);
    town.state.lastApiAt=0;ticks(220);await until('!state.busy&&state.stats.length===4');notify();
    assert.equal(requests,4);assert.equal(town.busy,false);assert.equal(a.life.focus.status,'completed');assert.equal(b.relationships[a.id],-1);assert.equal(a.relationships[b.id],2);
    assert.ok(payloads[1].messages[0].content.includes('已到达'));assert.ok(payloads[2].messages[0].content.includes('多办一些活动'));assert.ok(payloads[3].messages.at(-1).content.includes('第 3 轮'));
    town.configure({running:false});notify();
    await evaluate(`select(${JSON.stringify(a.id)});document.querySelector('#actor-diary').click()`);await until("document.querySelector('#diary-summary').textContent.includes('条记录')");
    assert.ok(await evaluate("document.querySelector('#diary-entries').textContent.includes('已到达')"));assert.ok(await evaluate("document.querySelector('#diary-entries').textContent.includes('好感')"));assert.equal(await evaluate('window.lifeAttacked'),undefined);
    await image('daily-journal.png');
    await evaluate("document.querySelector('#diary-type').value='thought';document.querySelector('#diary-type').dispatchEvent(new Event('change',{bubbles:true}))");await until("document.querySelectorAll('.diary-entry').length>0&&[...document.querySelectorAll('.diary-entry')].every(n=>n.classList.contains('thought'))");
    await evaluate("document.querySelector('#diary-export').click()");await until("document.querySelector('#toast').textContent.includes('完整日志')");assert.ok(fs.readFileSync(path.join(output,'ui-export-diary.md'),'utf8').includes('已到达'));
    await evaluate("document.querySelector('#daily-diary [data-life-close]').click();document.querySelector('#life-direction').click()");await until("document.querySelector('#life-aspiration')!==null");
    assert.ok(await evaluate("document.querySelector('.life-focus').textContent.includes('最近完成')"));
    await evaluate("document.querySelector('#life-aspiration').value='认真经营自己的日常，也保留安静和运动的时间';document.querySelector('#save-life-person').click()");await until("!document.querySelector('#life-editor').open");assert.equal(a.life.aspiration,'认真经营自己的日常，也保留安静和运动的时间');assert.equal(store.load().autonomous,true);
    await evaluate("document.querySelector('#open-settings').click();document.querySelector('[data-settings-tab=life]').click()");await until("!document.querySelector('#life-settings').hidden&&document.querySelectorAll('.life-person').length===45");
    await evaluate("document.querySelector('#world-facts').value='公告：可以自主交流、工作、散步运动，也允许观点不同';document.querySelector('#world-facts').dispatchEvent(new Event('input',{bubbles:true}));document.querySelector('#world-info-form').requestSubmit()");await until("document.querySelector('#world-info-status').textContent.includes('已保存')");assert.ok(town.state.worldInfo.facts.includes('允许观点不同'));assert.ok(store.load().worldInfo.facts.includes('允许观点不同'));
    await image('foundation-settings.png');
    await evaluate(`document.querySelector('[data-life-person="${a.id}"]').click();document.querySelector('[data-life-context]').click()`);await until("document.querySelector('.life-context-text')!==null");assert.ok(await evaluate("document.querySelector('.life-context-text').value.includes('允许观点不同')"));assert.equal(requests,4);await image('character-context.png');
    await evaluate("document.querySelector('#life-context [data-life-close]').click();document.querySelector('#life-editor [data-life-close]').click()");win.setSize(1040,720);await new Promise(resolve=>setTimeout(resolve,100));
    await evaluate(`window.TownLifeUI.openDiary(${JSON.stringify(b.id)})`);await until("document.querySelector('#diary-summary').textContent.includes('条记录')");
    assert.ok(await evaluate("(()=>{const d=document.querySelector('#daily-diary'),r=d.getBoundingClientRect();return r.left>=0&&r.right<=innerWidth&&r.top>=0&&r.bottom<=innerHeight&&d.scrollWidth<=d.clientWidth;})()"));await image('journal-small-window.png');
    journal.flush();store.save(town.state);const reopened=new Town(store.load(),{},()=>{},new Journal(path.join(dir,'journals')));assert.equal(reopened.state.autonomous,true);assert.equal(reopened.resident(a.id).life.aspiration,a.life.aspiration);assert.ok(reopened.prompt(reopened.resident(b.id)).includes('阅读'));
    assert.equal(errors.length,0,errors.join('\n'));assert.ok(!JSON.stringify(town.snapshot()).includes('life-renderer-secret'));
    const result={ok:true,appRoot:root,httpRequests:requests,paidApiCalls:0,noManualBehaviorTrigger:true,autonomousTravelAndInvite:true,threeTurnExchange:true,individualFeelings:true,goalPersists:true,dailyArchiveAndExport:true,knowledgeEditable:true,contextPreviewFree:true,safeText:true,smallWindow:true,resumesAfterRestart:true};fs.writeFileSync(path.join(output,'renderer-result.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
  }catch(e){console.error(e.stack);process.exitCode=1;}
  finally{server.closeAllConnections();await new Promise(resolve=>server.close(resolve));win?.destroy();fs.rmSync(dir,{recursive:true,force:true});app.exit(process.exitCode||0);}
});
