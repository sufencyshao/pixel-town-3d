'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const http=require('node:http');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const {Town}=require('../main/engine');
const {initialState,catalog}=require('../main/catalog');
const {Persistence}=require('../main/persistence');
const {available}=require('../shared/actions');
const {parseExpression}=require('../main/character-behavior');
const {clipFor}=require('../renderer/animation');
const llm=require('../main/llm');
const response=(action='nod',thought='想认真听听',speech='好呀。',extra={})=>({text:JSON.stringify({action,thought,speech,...extra}),usage:{promptTokens:5,completionTokens:8},latency:2});
const flush=()=>new Promise(resolve=>setImmediate(resolve));
function fixture() {
  const t=new Town(initialState(),{}),[a,b]=t.active();
  t.state.providers.push({id:'unit-api',name:'测试 API',type:'openai',baseUrl:'http://127.0.0.1',apiKey:'behavior-unit-key'});
  a.model={providerId:'unit-api',model:'model-a',temperature:.4,maxTokens:500};
  t.llm={chatCompletion:async()=>response()};
  return {t,a,b};
}

test('40 人与 5 个 Mini 的模型动作均有真实素材，聊天不选择移动；Mini 不假装有摇头素材',()=>{
  assert.equal(catalog.filter(r=>r.kind==='human').length,40);
  for(const person of catalog) {
    const actions=available(person.animation);
    assert.ok(actions.length);
    for(const action of actions.filter(a=>a!=='walk')){
      const sample=clipFor({...person,action,direction:'front',target:null,moving:false,thinking:false});
      assert.ok(sample?.atlas,person.name+'/'+action);
      assert.ok(action==='idle'||sample.key!=='idle',person.name+'/'+action+' cannot silently fall back');
    }
    if(actions.includes('walk'))for(const direction of ['front','back','left','right'])assert.match(clipFor({...person,action:'walk',direction,moving:true}).key,/^walk/);
    assert.ok(!available(person.animation,'conversation').includes('walk'));
    assert.ok(!available(person.animation,'conversation').includes('work'));
    if(person.kind==='human')assert.ok(actions.includes('nod')&&actions.includes('shake_head')&&actions.includes('chat'));
    else {
      assert.ok(!actions.includes('shake_head')&&!actions.includes('nod')&&!actions.includes('chat'));
      assert.throws(()=>parseExpression(response('shake_head').text,person.animation),/素材/);
    }
  }
});

test('模型输出严格验证对象、字段、台词、坐标与邀请对象，非法输出没有部分动作',async()=>{
  const {t,a,b}=fixture(),animation=a.animation;
  for(const text of ['[]','null','plain text','{"action":"nod"}',response('constructor').text,
    response('nod','x'.repeat(121)).text,response('nod','想法',{}).text,
    response('nod','想法','台词',{rotate:30}).text,'{"action":"nod","thought":"想法","__proto__":{}}',
    response('walk').text,response('walk','想法','',{destination:{x:89,y:150}}).text,
    response('walk','想法','',{destination:{x:'200',y:200}}).text,
    response('walk','想法','',{destination:{x:200,y:200,z:0}}).text,
    response('chat','想法','一起聊聊',{partnerId:'player'}).text,
    response('nod','想法','好',{partnerId:b.id}).text]){
    assert.throws(()=>parseExpression(text,animation,{partners:[b]}),/有效/);
  }
  assert.throws(()=>parseExpression(response('walk','想法','走吧',{destination:{x:200,y:200}}).text,animation,{mode:'conversation'}),/有效/);
  assert.throws(()=>parseExpression(response('chat','想法','').text,animation,{mode:'conversation'}),/台词/);
  const data=parseExpression('```json\n'+response('walk','走向公园','',{destination:{x:1100,y:250}}).text+'\n```',animation);
  assert.deepEqual(data.destination,{x:1100,y:250});
  a.action='rest';a.target=null;t.llm.chatCompletion=async()=>({text:'{"action":"work","thought":"坏","destination":{"x":-9,"y":200}}',usage:{},latency:1});
  await assert.rejects(t.decide(a.id),/有效/);assert.equal(a.action,'idle');assert.equal(a.behaviorStatus,'waiting');
  assert.equal(t.state.stats.length,1);assert.equal(t.state.stats[0].ok,false);assert.equal(t.state.stats[0].responseOk,true);
});

test('安静想法与说出口的台词分开，选择的摇头播放完整后进入等待',async()=>{
  const {t,a}=fixture();t.configure({autonomous:true});t.state.lastApiAt=Date.now();
  t.llm.chatCompletion=async()=>response('shake_head','这件事我不想答应','');
  const expression=await t.decide(a.id);assert.equal(expression.action,'shake_head');
  assert.equal(a.thought,'这件事我不想答应');assert.equal(a.bubble,'');assert.equal(a.remaining,1.2);
  assert.ok(t.state.events.some(e=>e.kind==='thought'));assert.ok(!t.state.events.some(e=>e.kind==='dialogue'));
  assert.equal(t.state.stats[0].action,'shake_head');assert.equal(t.state.stats[0].applied,true);
  t.tick(.72);assert.equal(a.action,'shake_head');t.tick(.48);assert.equal(a.action,'idle');assert.equal(a.behaviorStatus,'waiting');
  assert.equal(t.state.stats.length,1);assert.equal(a.lastExpression.action,'shake_head');
});

test('聊天一次调用同时给出台词、心声和动作；历史只向模型发送真正说的话',async()=>{
  const {t,a}=fixture(),calls=[];
  t.llm.chatCompletion=async opts=>{calls.push(opts);return response('shake_head','需要留点时间给自己','今天不行，我想先把书整理好。');};
  const reply=await t.chat(a.id,'现在一起出去玩吗？');
  assert.equal(reply,'今天不行，我想先把书整理好。');assert.equal(a.action,'shake_head');assert.equal(a.target,null);
  assert.equal(a.thought,'需要留点时间给自己');assert.equal(a.bubble,reply);assert.equal(a.messages.at(-1).action,'shake_head');
  assert.equal(a.messages.at(-1).source,'api');assert.ok(!a.messages.at(-1).content.startsWith('{'));
  assert.match(calls[0].system,/speech/);assert.match(calls[0].system,/性格/);assert.match(calls[0].system,/shake_head/);
  await t.chat(a.id,'那晚点呢？');assert.equal(calls.length,2);
  assert.ok(calls[1].messages.some(m=>m.content===reply));assert.ok(calls[1].messages.every(m=>!m.content.includes('需要留点时间给自己')));
  assert.ok(!JSON.stringify(t.snapshot()).includes('behavior-unit-key'));
});

test('双方独立 API 表达各自动作与心声；第一人的私有想法不作为对话发送给第二人',async()=>{
  const {t,a,b}=fixture();b.model={...a.model,model:'model-b'};let finish;const calls=[];
  t.llm.chatCompletion=async opts=>{calls.push(opts);return opts.model==='model-a'?response('nod','只留在自己心里的想法','要一起散步吗？'):new Promise(resolve=>{finish=resolve;});};
  const talking=t.converse(a.id,b.id);await flush();assert.equal(a.action,'nod');assert.equal(a.thinking,false);assert.equal(b.thinking,true);
  assert.ok(calls[1].messages[0].content.includes('要一起散步吗？'));assert.ok(!calls[1].system.includes('只留在自己心里'));
  t.tick(1.44,true);assert.equal(a.action,'idle');assert.equal(a.dialoguePending,true);
  finish(response('shake_head','还想继续手上的事','今天不行，谢谢你。'));await talking;
  assert.equal(b.action,'shake_head');assert.equal(b.remaining,1.2);assert.equal(b.thought,'还想继续手上的事');
  assert.equal(t.state.stats.length,2);assert.equal(t.busy,false);assert.equal(a.dialoguePending,false);
});

test('模型主动选择邻居发出邀请，走到相遇区后复用原台词，只再调用对方一次',async()=>{
  const {t,a,b}=fixture();b.model={...a.model,model:'model-b'};t.configure({autonomous:true});let count=0;
  t.llm.chatCompletion=async opts=>{count++;return opts.model==='model-a'?response('chat','想听听邻居今天的故事','今天过得怎么样？',{partnerId:b.id}):response('nod','愿意和邻居交流','挺不错的，谢谢关心！');};
  await t.decide(a.id,{automatic:true});assert.equal(count,1);assert.equal(a.meeting.partner,b.id);assert.equal(a.bubble,'');
  for(const r of [a,b]){r.x=r.target.x;r.y=r.target.y;}
  t.tick(.1,true);await flush();assert.equal(count,1,'Wait for the configured global interval');
  t.state.lastApiAt=Date.now()-61000;t.tick(.1,true);await flush();
  assert.equal(count,2);assert.equal(b.action,'nod');assert.equal(a.bubble,'今天过得怎么样？');assert.equal(b.bubble,'挺不错的，谢谢关心！');
  assert.equal(a.memory.filter(m=>m.includes('我想到')).length,1);
});

test('自主 API 人物完成当前行为后再决策，间隔、预算与暂停期间不被本地随机行为覆盖',async()=>{
  const {t,a}=fixture();for(const r of t.active())r.remaining=10000;
  t.configure({autonomous:true});let count=0;t.localAction=r=>{if(r.id===a.id)throw new Error('Bound actor must wait for API');return 'idle';};
  t.llm.chatCompletion=async()=>{count++;return response('work','先把今天的事情做完','',{destination:{x:a.x,y:a.y}});};
  t.tick(.1);await flush();assert.equal(count,1);assert.equal(a.action,'work');
  t.state.lastApiAt=0;t.tick(.1);await flush();assert.equal(count,1,'Do not interrupt the API-selected activity');
  a.remaining=0;t.state.lastApiAt=Date.now();t.tick(.1);assert.equal(a.action,'idle');assert.equal(a.behaviorStatus,'waiting');assert.equal(count,1);
  t.configure({dailyLimit:1});t.state.lastApiAt=0;t.tick(.1);assert.equal(count,1);
  t.configure({dailyLimit:10,running:false});t.tick(10);assert.equal(count,1);
  t.configure({running:true});t.tick(.1);await flush();assert.equal(count,2);
});

for(const change of ['manual-action','control','move','appearance','model','leave','leave-and-return','autonomy-off'])test('迟到的模型回复不会覆盖新指令：'+change,async()=>{
  const {t,a,b}=fixture();t.configure({autonomous:true});let finish;
  t.llm.chatCompletion=()=>new Promise(resolve=>{finish=resolve;});
  const deciding=t.decide(a.id,{automatic:true});await flush();
  if(change==='manual-action')t.act(a.id,'greet',{x:a.x,y:a.y});
  if(change==='control')t.control(a.id);
  if(change==='move')t.move(a.id,{x:1000,y:500});
  if(change==='appearance')t.update(a.id,{asset:catalog.find(r=>r.kind==='codexmini').asset});
  if(change==='model')t.update(a.id,{model:{...a.model,model:'model-new'}});
  if(change==='leave')t.setRoster([b.id]);
  if(change==='leave-and-return'){t.setRoster([b.id]);t.setRoster([a.id,b.id]);}
  if(change==='autonomy-off')t.configure({autonomous:false});
  const expected={action:a.action,target:structuredClone(a.target),actionVersion:a.actionVersion,controlled:t.state.controlledId};
  finish(response('nod','这句话应被忽略','旧回复'));const result=await deciding;
  assert.equal(result.discarded,true);assert.equal(a.action,expected.action);assert.deepEqual(a.target,expected.target);assert.equal(a.actionVersion,expected.actionVersion);
  assert.equal(t.state.controlledId,expected.controlled);assert.equal(a.thought,'');assert.ok(!a.memory.includes('这句话应被忽略'));
  assert.equal(t.state.stats.at(-1).applied,false);assert.equal(t.busy,false);assert.equal(a.thinking,false);
});

test('手动接管立即取消网络等待，方向键可立即移动且旧回复不能夺回控制',async()=>{
  const {t,a}=fixture();let signal;
  t.llm.chatCompletion=opts=>{signal=opts.signal;return new Promise((resolve,reject)=>{signal.addEventListener('abort',()=>reject(new Error('request aborted')),{once:true});});};
  const request=t.decide(a.id);await flush();assert.equal(signal.aborted,false);
  t.control(a.id);assert.equal(signal.aborted,true);t.setInput({x:1,y:0});const x=a.x;t.tick(.1,true);assert.ok(a.x>x);
  const result=await request;assert.equal(result.discarded,true);assert.equal(t.state.controlledId,a.id);assert.equal(t.busy,false);assert.equal(a.action,'walk');
  assert.equal(t.state.stats.length,1);assert.equal(t.state.stats[0].applied,false);
});

test('真实 OpenAI 兼容 HTTP 流经 API 内核后表达摇头；单次请求、无明文密钥快照',async()=>{
  const bodies=[];
  const server=http.createServer(async(req,res)=>{
    let body='';for await(const part of req)body+=part;
    bodies.push(JSON.parse(body));assert.equal(req.url,'/v1/chat/completions');
    res.writeHead(200,{'content-type':'text/event-stream'});
    const text=response('shake_head','想坚持自己的安排','这次就不去了。').text;
    for(const content of [text.slice(0,21),text.slice(21)])res.write('data: '+JSON.stringify({choices:[{delta:{content}}]})+'\n\n');
    res.end('data: '+JSON.stringify({usage:{prompt_tokens:8,completion_tokens:13}})+'\n\ndata: [DONE]\n\n');
  });
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  try {
    const {t,a}=fixture();t.state.providers.at(-1).baseUrl='http://127.0.0.1:'+server.address().port+'/v1';t.llm=llm;
    assert.equal(await t.chat(a.id,'现在陪我去玩好吗？'),'这次就不去了。');
    assert.equal(a.action,'shake_head');assert.equal(bodies.length,1);assert.equal(bodies[0].model,'model-a');assert.equal(bodies[0].max_tokens,500);
    assert.ok(bodies[0].messages[0].content.includes('thought'));assert.equal(t.state.stats[0].tokens,21);assert.equal(t.state.stats[0].action,'shake_head');
    assert.ok(!JSON.stringify(t.snapshot()).includes('behavior-unit-key'));
  }finally{server.closeAllConnections();await new Promise(resolve=>server.close(resolve));}
});

test('心声、台词与动作历史保存恢复，明确开启的自主生活也持续保存',async()=>{
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'town-behavior-'));
  try {
    const {t,a}=fixture();t.configure({autonomous:true});await t.chat(a.id,'你好');
    const safe={isEncryptionAvailable:()=>true,encryptString:s=>Buffer.from(s),decryptString:b=>b.toString()};
    const store=new Persistence(dir,safe);store.save(t.state);const restored=new Town(store.load(),{}).resident(a.id);
    assert.equal(restored.lastExpression.action,'nod');assert.equal(restored.messages.at(-1).thought,'想认真听听');assert.equal(restored.dialoguePending,false);
    assert.equal(store.load().autonomous,true);assert.equal(store.load().resumeAutonomy,true);assert.ok(!fs.readFileSync(store.file,'utf8').includes('behavior-unit-key'));
  }finally{fs.rmSync(dir,{recursive:true,force:true});}
});
