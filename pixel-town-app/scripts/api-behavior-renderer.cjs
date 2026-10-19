'use strict';
// Isolated renderer + real HTTP/SSE API kernel; no user data or paid API calls.
const {app,BrowserWindow,ipcMain}=require('electron');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),http=require('node:http'),assert=require('node:assert/strict');
const root=process.env.TOWN_TEST_APP_ROOT||path.join(__dirname,'..');
const {Town}=require(path.join(root,'main/engine'));
const {initialState,catalog,petCatalog}=require(path.join(root,'main/catalog'));
const llm=require(path.join(root,'main/llm'));
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'town-api-ui-'));app.setPath('userData',dir);
let win,server,requests=0;
app.whenReady().then(async()=>{
  const town=new Town(initialState(),llm),wen=town.state.residents.find(r=>r.asset==='36_barista_female'),lin=town.state.residents.find(r=>r.asset==='30_florist_male');
  town.setRoster([wen.id,lin.id]);town.configure({running:false});
  server=http.createServer(async(req,res)=>{
    let data='';for await(const chunk of req)data+=chunk;const body=JSON.parse(data);requests++;
    const user=body.messages.at(-1).content;
    const expression=user.includes('拒绝')?{action:'shake_head',thought:'我有自己的安排，先不答应。',speech:'今天不行，谢谢你的邀请。'}:
      user.includes('同意')?{action:'nod',thought:'这个主意听起来不错。',speech:'好呀，我愿意。'}:
      {action:'rest',thought:'<script>window.uiAttacked=true</script>先坐一会儿。',speech:''};
    res.writeHead(200,{'content-type':'text/event-stream'});
    res.end('data: '+JSON.stringify({choices:[{delta:{content:JSON.stringify(expression)}}]})+'\n\ndata: '+JSON.stringify({usage:{prompt_tokens:7,completion_tokens:9}})+'\n\ndata: [DONE]\n\n');
  });
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  town.state.providers.push({id:'ui-api',name:'界面测试 API',type:'openai',baseUrl:'http://127.0.0.1:'+server.address().port+'/v1',models:['ui-model'],apiKey:'ui-only-test-key'});
  for(const r of [wen,lin])r.model={providerId:'ui-api',model:'ui-model',temperature:.4,maxTokens:500};
  const commands={'town:get':()=>({state:town.snapshot(),catalog,petCatalog,dataDir:'isolated-api-ui-test',encrypted:true}),
    'town:config':c=>town.configure(c),'town:chat':(id,text)=>town.chat(id,text),'town:decide':id=>town.decide(id),'town:input':v=>town.setInput(v)};
  for(const [channel,fn]of Object.entries(commands))ipcMain.handle(channel,async(_,...args)=>{try{const value=await fn(...args);win.webContents.send('town:snapshot',town.snapshot());return {ok:true,value};}catch(e){win.webContents.send('town:snapshot',town.snapshot());return {ok:false,error:e.message};}});
  const errors=[];
  win=new BrowserWindow({show:false,width:1480,height:960,webPreferences:{preload:path.join(root,'main/preload.js'),sandbox:true,contextIsolation:true,nodeIntegration:false,backgroundThrottling:false}});
  win.webContents.on('console-message',(_,level,message)=>{if(level>=3)errors.push(message);});
  const evaluate=code=>win.webContents.executeJavaScript(code,true);
  const until=async code=>{const end=Date.now()+10000;while(Date.now()<end){if(await evaluate(code))return;await new Promise(resolve=>setTimeout(resolve,40));}throw new Error('Timed out: '+code);};
  try {
    await win.loadFile(path.join(root,'renderer/index.html'));await until("!!state&&document.querySelectorAll('.sprite').length===2");
    await evaluate(`select(${JSON.stringify(wen.id)});document.querySelector('#open-chat').click();document.querySelector('#chat-input').value='请自然地拒绝这次邀请';document.querySelector('#chat-form').requestSubmit()`);
    await until("!!document.querySelector('.chat-expression')&&!state.busy");
    assert.equal(requests,1);assert.equal(wen.action,'shake_head');assert.equal(wen.remaining,1.2);
    assert.ok(await evaluate("document.querySelector('.chat-expression').textContent.includes('摇头拒绝')&&document.querySelector('.chat-expression').textContent.includes('心声')"));
    assert.ok(await evaluate("document.querySelector('.chat-message.assistant').textContent.includes('今天不行')"));
    await evaluate("document.querySelector('#close-modal').click()");await until(`nodes.get(${JSON.stringify(wen.id)}).dataset.clip==='shake_head'`);
    assert.equal(await evaluate("document.querySelector('#character-thought').textContent"),wen.thought);
    assert.equal(await evaluate(`nodes.get(${JSON.stringify(wen.id)}).querySelector('.bubble').classList.contains('thought')`),false);
    await evaluate("animationTime+=450");await until(`nodes.get(${JSON.stringify(wen.id)}).querySelector('.atlas-sprite').style.backgroundPosition!=='0px 0px'`);
    assert.notEqual(await evaluate(`nodes.get(${JSON.stringify(wen.id)}).querySelector('.atlas-sprite').style.backgroundPosition`),'0px 0px');
    town.tick(1.2,true);win.webContents.send('town:snapshot',town.snapshot());await until(`nodes.get(${JSON.stringify(wen.id)}).dataset.clip==='idle'`);
    await evaluate("document.querySelector('#open-chat').click();document.querySelector('#chat-input').value='你愿意同意我的提议吗';document.querySelector('#chat-form').requestSubmit()");
    await until("!state.busy&&state.residents.find(r=>r.asset==='36_barista_female').action==='nod'");assert.equal(requests,2);assert.equal(wen.remaining,1.44);
    await evaluate("document.querySelector('#close-modal').click();document.querySelector('#ask-ai').click()");
    await until("!state.busy&&state.residents.find(r=>r.asset==='36_barista_female').action==='rest'");assert.equal(requests,3);
    assert.equal(await evaluate("window.uiAttacked"),undefined,'Model text must never execute');
    assert.equal(await evaluate(`nodes.get(${JSON.stringify(wen.id)}).querySelector('.bubble').classList.contains('thought')`),true);
    assert.ok(await evaluate("document.querySelector('#character-thought').textContent.includes('<script>')"));
    win.setSize(1040,720);await new Promise(resolve=>setTimeout(resolve,80));
    assert.ok(await evaluate("(()=>{const n=document.querySelector('#inspector'),b=n.getBoundingClientRect();return b.left>=0&&b.right<=innerWidth&&b.bottom<=innerHeight&&n.scrollWidth<=n.clientWidth;})()"));
    await evaluate("document.querySelector('#open-settings').click();document.querySelector('[data-settings-tab=api]').click()");
    assert.ok(await evaluate("document.querySelector('#api-ownership').textContent.includes('2 位人物')"));
    assert.ok(await evaluate("document.querySelector('#stats').textContent.includes('摇头拒绝')"));
    assert.equal(errors.length,0,errors.join('\n'));assert.ok(!JSON.stringify(town.snapshot()).includes('ui-only-test-key'));
    console.log(JSON.stringify({ok:true,httpRequests:requests,paidApiCalls:0,thoughtAndSpeechSeparate:true,refusalCompletes:true,nodDuration:1.44,safeText:true,smallWindow:true,appRoot:root}));
  }catch(e){console.error(e.stack);process.exitCode=1;}
  finally{server.closeAllConnections();await new Promise(resolve=>server.close(resolve));win?.destroy();fs.rmSync(dir,{recursive:true,force:true});app.exit(process.exitCode||0);}
});
