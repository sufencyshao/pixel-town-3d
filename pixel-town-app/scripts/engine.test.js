'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const os=require('node:os');
const {Town}=require('../main/engine');
const {Persistence}=require('../main/persistence');
const {catalog,initialState}=require('../main/catalog');
const town=()=>new Town(initialState(),{});
test('人物目录保留原始20套16帧，默认六人独立档案',()=>{assert.ok(catalog.length>=20);for(const c of catalog.slice(0,20))for(let i=1;i<=16;i++)assert.ok(fs.existsSync(path.join(__dirname,'../assets/characters',c.asset,`frame_${String(i).padStart(2,'0')}.png`)));const t=town();assert.equal(t.active().length,6);t.active()[0].persona.personality='测试';assert.notEqual(t.active()[1].persona.personality,'测试');});
test('人数增长复用形象，缩减与恢复保留人物记忆',()=>{const t=town();const first=t.active()[0];first.memory=['保留'];t.setCount(35);assert.equal(t.active().length,35);assert.equal(new Set(t.active().map(r=>r.id)).size,35);t.setCount(1);t.setCount(35);assert.deepEqual(t.resident(first.id).memory,['保留']);});
test('移动、暂停、推进与精力恢复',()=>{const t=town();const r=t.active()[0];t.move(r.id,{x:900,y:600});const x=r.x;t.configure({running:false});t.tick(1);assert.equal(r.x,x);t.tick(1,true);assert.notEqual(r.x,x);t.teleport(r.id,{x:900,y:600});r.energy=10;t.act(r.id,'rest');r.target=null;t.tick(5,true);assert.ok(r.energy>10);});
test('本地对话双向记忆、关系与独立私聊',async()=>{const t=town();const[a,b,c]=t.active();await t.converse(a.id,b.id);assert.equal(a.relationships[b.id],2);assert.equal(b.relationships[a.id],2);assert.ok(a.memory.some(m=>m.includes(b.name)));assert.ok(b.memory.some(m=>m.includes(a.name)));await t.chat(a.id,'早上好');assert.equal(a.messages.length,2);assert.equal(c.messages.length,0);assert.equal(c.memory.length,0);});
test('两个居民使用各自 API 与模型参数，错误释放锁',async()=>{const t=town();const[a,b]=t.active();const calls=[];t.state.providers.push({id:'a',type:'openai',apiKey:'secret-a'},{id:'b',type:'anthropic',apiKey:'secret-b'});a.model={providerId:'a',model:'model-a',temperature:0.3,maxTokens:220};b.model={providerId:'b',model:'model-b',temperature:1.1,maxTokens:550};t.llm={chatCompletion:async opts=>{calls.push(opts);return{text:JSON.stringify({action:opts.model==='model-a'?'chat':'nod',thought:'想和邻居聊一聊',speech:opts.model==='model-a'?'你好，一起休息吗？':'好呀。'}),usage:{promptTokens:5,completionTokens:3},latency:10};}};await t.converse(a.id,b.id);assert.deepEqual(calls.map(c=>[c.provider.id,c.model,c.temperature,c.maxTokens]),[['a','model-a',0.3,220],['b','model-b',1.1,550]]);assert.ok(calls[1].messages[0].content.includes('一起休息'));assert.ok(!JSON.stringify(t.snapshot()).includes('secret-a'));t.llm.chatCompletion=async()=>{throw new Error('secret-a 故障');};await assert.rejects(t.chat(a.id,'测试'),/已隐藏/);assert.equal(t.busy,false);assert.equal(a.thinking,false);assert.equal(t.state.stats.at(-1).ok,false);});
test('结构化模型决策映射行为，畸形输出回退并记录错误',async()=>{const t=town();const r=t.active()[0];t.state.providers.push({id:'a',type:'openai'});r.model.providerId='a';t.llm={chatCompletion:async()=>({text:'```json\n{"action":"rest","thought":"想歇一会儿"}\n```',usage:{},latency:1})};await t.decide(r.id);assert.equal(r.action,'rest');assert.ok(r.memory[0].includes('想歇一会儿'));t.llm.chatCompletion=async()=>({text:'不返回 JSON',usage:{},latency:1});await assert.rejects(t.decide(r.id));assert.ok(t.state.events.some(e=>e.kind==='error'));assert.equal(t.busy,false);});
test('调用预算包含失败请求，达到上限停止自动模型循环',async()=>{const t=town();const r=t.active()[0];t.state.providers.push({id:'a',type:'openai'});r.model.providerId='a';t.configure({dailyLimit:1,autonomous:true});let count=0;t.llm={chatCompletion:async()=>{count++;throw new Error('失败');}};await assert.rejects(t.chat(r.id,'一次'));await assert.rejects(t.chat(r.id,'两次'),/上限/);for(let i=0;i<20;i++)t.tick(.5);assert.equal(count,1);});
test('密钥加密、独立存档、重启禁用模型自治、损坏备份恢复',()=>{const dir=fs.mkdtempSync(path.join(os.tmpdir(),'pixel-town-unit-'));try{const safe={isEncryptionAvailable:()=>true,encryptString:s=>Buffer.from(s.split('').reverse().join('')),decryptString:b=>b.toString().split('').reverse().join('')};const p=new Persistence(dir,safe),s=initialState();s.autonomous=true;s.providers.push({id:'key',type:'openai',apiKey:'unique-secret-key'});p.save(s);const disk=fs.readFileSync(p.file,'utf8');assert.ok(!disk.includes('unique-secret-key'));assert.equal(p.load().providers.at(-1).apiKey,'unique-secret-key');assert.equal(p.load().autonomous,false);p.save(s);fs.writeFileSync(p.file,'broken');assert.equal(p.load().residents.length,catalog.length);assert.equal(p.recovered,true);}finally{fs.rmSync(dir,{recursive:true,force:true});}});

const llm = require('../main/llm');
const fakeSafe = () => ({isEncryptionAvailable:()=>true,encryptString:s=>Buffer.from(s.split('').reverse().join('')),decryptString:b=>b.toString().split('').reverse().join('')});
function temporaryStore(fn) { const dir=fs.mkdtempSync(path.join(os.tmpdir(),'pixel-town-security-'));try {return fn(dir);}finally {fs.rmSync(dir,{recursive:true,force:true});} }
test('钥匙串不可用时拒绝含密钥保存，保留已有存档，无明文临时文件',()=>temporaryStore(dir=>{
  const safe=fakeSafe(),p=new Persistence(dir,safe),state=initialState();p.save(state);const before=fs.readFileSync(p.file,'utf8');
  state.providers.push({id:'private',type:'openai',apiKey:'unit-only-private-key'});safe.isEncryptionAvailable=()=>false;
  assert.throws(()=>p.save(state),/未保存/);assert.equal(fs.readFileSync(p.file,'utf8'),before);assert.equal(fs.existsSync(p.file+'.tmp'),false);
  assert.equal(fs.existsSync(p.file+'.bak'),false);assert.equal(state.providers.at(-1).apiKey,'unit-only-private-key');
  const fresh=new Persistence(path.join(dir,'fresh'),safe);assert.throws(()=>fresh.save(state),/未保存/);assert.equal(fs.existsSync(fresh.file),false);
}));
test('恢复后第一次保存不会覆盖健康备份，损坏主档单独保留',()=>temporaryStore(dir=>{
  const p=new Persistence(dir,fakeSafe()),state=initialState();p.save(state);p.save(state);const backup=fs.readFileSync(p.file+'.bak','utf8');
  fs.writeFileSync(p.file,'bad-json');const recovered=p.load();recovered.clock+=10;p.save(recovered);
  assert.equal(fs.readFileSync(p.file+'.bak','utf8'),backup);assert.equal(p.load().clock,state.clock+10);
  assert.ok(fs.readdirSync(dir).some(name=>name.includes('.damaged-')));assert.equal(fs.statSync(p.file).mode&0o777,0o600);
}));
test('钥匙串不可用不触发旧备份降级，结构损坏会触发恢复',()=>temporaryStore(dir=>{
  const safe=fakeSafe(),p=new Persistence(dir,safe),state=initialState();p.save(state);
  state.providers.push({id:'private',type:'openai',apiKey:'unit-only-encrypted-key'});p.save(state);safe.isEncryptionAvailable=()=>false;
  assert.throws(()=>p.load(),/钥匙串/);assert.equal(p.recovered,false);assert.equal(fs.readdirSync(dir).filter(name=>name.includes('.damaged-')).length,0);
  safe.isEncryptionAvailable=()=>true;const broken=JSON.parse(fs.readFileSync(p.file,'utf8'));delete broken.events;fs.writeFileSync(p.file,JSON.stringify(broken));
  assert.ok(p.load().events);assert.equal(p.recovered,true);
}));
test('重启清理人物控制与运行中标记，记忆和关系保持',()=>temporaryStore(dir=>{
  const p=new Persistence(dir,fakeSafe()),state=initialState(),r=state.residents[0];r.thinking=true;r.moving=true;r.memory=['记住邻居'];r.relationships['resident-2']=8;state.controlledId=r.id;state.autonomous=true;
  p.save(state);const loaded=p.load();assert.equal(loaded.controlledId,null);assert.equal(loaded.residents[0].thinking,false);assert.equal(loaded.residents[0].moving,false);assert.deepEqual(loaded.residents[0].memory,['记住邻居']);assert.equal(loaded.residents[0].relationships['resident-2'],8);assert.equal(loaded.autonomous,false);
}));
async function mockFetch(fn,run) {const undici=require('undici'),original=global.fetch,proxyFetch=undici.fetch;global.fetch=fn;undici.fetch=fn;try {await run();} finally {global.fetch=original;undici.fetch=proxyFetch;}}
const completionOpts=provider=>({provider,model:'unit-model',system:'人物背景',messages:[{role:'user',content:'你好'}],maxTokens:120,temperature:.4});
test('OpenAI SSE 分块中文及无换行末行保持完整，独立参数与用量传递',async()=>{
  let captured,delta='';const encoded=new TextEncoder().encode('data: {"choices":[{"delta":{"content":"你好"}}]}\r\n\r\ndata: {"usage":{"prompt_tokens":4,"completion_tokens":2}}');
  await mockFetch(async(url,opts)=>{captured={url,opts};return new Response(new ReadableStream({start(ctrl){ctrl.enqueue(encoded.slice(0,encoded.indexOf(0xe4)+1));ctrl.enqueue(encoded.slice(encoded.indexOf(0xe4)+1));ctrl.close();}}));},async()=>{
    const result=await llm.chatCompletion({...completionOpts({type:'openai',baseUrl:'https://unit.invalid/v1/chat/completions/',apiKey:'test-header-key'}),onDelta:part=>delta+=part});
    assert.equal(captured.url,'https://unit.invalid/v1/chat/completions');assert.equal(captured.opts.headers.Authorization,'Bearer test-header-key');assert.equal(JSON.parse(captured.opts.body).max_tokens,120);assert.equal(result.text,'你好');assert.equal(delta,'你好');assert.deepEqual(result.usage,{promptTokens:4,completionTokens:2});
  });
});
test('DeepSeek 结构化生活调用关闭默认推理，其他服务商和普通请求保持原参数',async()=>{
  const requests=[];
  await mockFetch(async(url,opts)=>{requests.push({url,body:JSON.parse(opts.body)});return new Response('data: {"choices":[{"delta":{"content":"{\\"action\\":\\"doze\\"}"},"finish_reason":"stop"}]}');},async()=>{
    const provider={type:'openai',baseUrl:'https://api.deepseek.com',apiKey:'unit-only-key'};
    await llm.chatCompletion({...completionOpts(provider),model:'deepseek-v4-flash',structured:true});
    await llm.chatCompletion({...completionOpts(provider),model:'deepseek-v4-flash'});
    await llm.chatCompletion({...completionOpts({...provider,baseUrl:'https://unit.invalid/v1'}),model:'deepseek-v4-flash',structured:true});
  });
  assert.deepEqual(requests[0].body.thinking,{type:'disabled'});assert.deepEqual(requests[0].body.response_format,{type:'json_object'});
  assert.ok(requests.every(r=>r.body.max_tokens===120));
  for(const request of requests.slice(1)){assert.equal(request.body.thinking,undefined);assert.equal(request.body.response_format,undefined);}
});
test('只有推理的空回复提供结束原因，不把推理内容当作人物台词',async()=>{
  let deltas='';
  await mockFetch(async()=>new Response('data: {"choices":[{"delta":{"reasoning_content":"unit-only-internal-reasoning"},"finish_reason":"length"}]}'),async()=>{
    await assert.rejects(llm.chatCompletion({...completionOpts({type:'openai',baseUrl:'https://unit.invalid'}),onDelta:s=>deltas+=s}),e=>e.message.includes('token 上限')&&!e.message.includes('unit-only-internal-reasoning'));
  });assert.equal(deltas,'');
});
test('Anthropic 根地址、v1 与完整接口地址正确路由，末行用量完整',async()=>{
  const requests=[];await mockFetch(async(url,opts)=>{requests.push({url,opts});return new Response('data: {"type":"message_start","message":{"usage":{"input_tokens":7}}}\n\ndata: {"type":"content_block_delta","delta":{"text":"好呀"}}\n\ndata: {"type":"message_delta","usage":{"output_tokens":3}}');},async()=>{
    for(const baseUrl of ['https://unit.invalid','https://unit.invalid/v1','https://unit.invalid/v1/messages/']) {const result=await llm.chatCompletion(completionOpts({type:'anthropic',baseUrl,apiKey:'anthropic-test-key'}));assert.equal(result.text,'好呀');assert.deepEqual(result.usage,{promptTokens:7,completionTokens:3});}
    for(const request of requests) {assert.equal(request.url,'https://unit.invalid/v1/messages');assert.equal(request.opts.headers['x-api-key'],'anthropic-test-key');assert.equal(JSON.parse(request.opts.body).model,'unit-model');}
  });
});
test('模型列表正确使用 Anthropic v1 地址，服务商错误隐藏密钥',async()=>{
  let endpoint;await mockFetch(async url=>{endpoint=url;return new Response(JSON.stringify({data:[{id:'model-c'}]}));},async()=>{assert.deepEqual(await llm.fetchModels({type:'anthropic',baseUrl:'https://unit.invalid/v1',apiKey:'list-test-key'}),{ok:true,models:['model-c']});assert.equal(endpoint,'https://unit.invalid/v1/models');});
  await mockFetch(async()=>new Response(JSON.stringify({error:{message:'server echoed unit-error-key'}}),{status:401}),async()=>{
    const provider={type:'openai',baseUrl:'https://unit.invalid/v1',apiKey:'unit-error-key'};await assert.rejects(llm.chatCompletion(completionOpts(provider)),e=>e.message.includes('[已隐藏]')&&!e.message.includes('unit-error-key'));
    const models=await llm.fetchModels(provider);assert.equal(models.ok,false);assert.ok(!models.error.includes('unit-error-key'));
  });
});
test('取消已发起的重试等待及本地演示，无额外 HTTP 请求',async()=>{
  const ctrl=new AbortController();let calls=0;await mockFetch(async()=>{calls++;setTimeout(()=>ctrl.abort(),5);return new Response('{"error":"busy"}',{status:429});},async()=>{await assert.rejects(llm.chatCompletion({...completionOpts({type:'openai',baseUrl:'https://unit.invalid/v1'}),signal:ctrl.signal}),e=>e.name==='AbortError');});assert.equal(calls,1);
  const cancelled=new AbortController();cancelled.abort();await assert.rejects(llm.chatCompletion({...completionOpts({type:'demo'}),signal:cancelled.signal}),e=>e.name==='AbortError');
});
test('参数不兼容最多两次回退，仍保持对应模型',async()=>{
  const bodies=[];await mockFetch(async(url,opts)=>{const body=JSON.parse(opts.body);bodies.push(body);if(bodies.length===1)return new Response('{"error":{"message":"unsupported stream_options"}}',{status:400});if(bodies.length===2)return new Response('{"error":{"message":"use max_completion_tokens instead of max_tokens"}}',{status:422});return new Response('data: {"choices":[{"delta":{"content":"成功"}}]}');},async()=>{assert.equal((await llm.chatCompletion(completionOpts({type:'openai',baseUrl:'https://unit.invalid/v1'}))).text,'成功');});
  assert.equal(bodies.length,3);assert.equal(bodies[1].stream_options,undefined);assert.equal(bodies[2].max_completion_tokens,120);assert.equal(bodies[2].max_tokens,undefined);assert.ok(bodies.every(b=>b.model==='unit-model'));
});
test('人物控制归一化斜向速度、边界停止，退出阵容自动解除控制',()=>{
  const t=town(),[a,b]=t.active();t.control(a.id);assert.equal(t.state.controlledId,a.id);const start={x:a.x,y:a.y};t.setInput({x:1,y:1});t.tick(1);assert.ok(Math.abs(Math.hypot(a.x-start.x,a.y-start.y)-75)<.001);assert.equal(a.moving,true);
  t.teleport(a.id,{x:1510,y:910});t.tick(1);assert.equal(a.x,1510);assert.equal(a.y,910);t.setInput({x:0,y:0});t.tick(.1);assert.equal(a.moving,false);assert.equal(a.action,'idle');t.setRoster([b.id]);assert.equal(t.state.controlledId,null);assert.deepEqual(t.input,{x:0,y:0});
});
test('阵容重复和不存在人物拒绝且不改已有阵容',()=>{
  const t=town(),ids=t.active().map(r=>r.id);assert.throws(()=>t.setRoster([]));assert.throws(()=>t.setRoster([ids[0],ids[0]]));assert.throws(()=>t.setRoster(['unknown']));assert.deepEqual(t.active().map(r=>r.id),ids);
});
test('再次邀请解除旧伙伴相遇，人物真正走到相遇位置后交谈',async()=>{
  const t=town(),[a,b,c]=t.active();t.meet(a,b,false);t.meet(a,c,false);assert.equal(b.meeting,null);assert.equal(b.target,null);assert.equal(a.meeting.partner,c.id);assert.equal(c.meeting.partner,a.id);
  t.tick(.1);assert.equal(a.memory.length,0);assert.equal(c.memory.length,0);assert.equal(a.moving,true);
  a.x=a.target.x;a.y=a.target.y;c.x=c.target.x;c.y=c.target.y;for(const r of t.active())r.remaining=1000;t.tick(.1);t.tick(.1);await new Promise(resolve=>setImmediate(resolve));assert.equal(a.relationships[c.id],2);assert.equal(b.relationships[a.id],undefined);assert.equal(t.busy,false);
});
test('双模型对话预留双方次数，预算不足不发出第一句或消耗调用',async()=>{
  const t=town(),[a,b]=t.active();t.state.providers.push({id:'paid',type:'openai'});a.model.providerId=b.model.providerId='paid';t.configure({dailyLimit:1});let calls=0;t.llm={chatCompletion:async()=>{calls++;return{text:'回复',usage:{},latency:1};}};
  await assert.rejects(t.converse(a.id,b.id),/不足/);assert.equal(calls,0);assert.equal(t.dailyCalls(),0);assert.equal(a.memory.length,0);assert.equal(b.memory.length,0);assert.equal(t.busy,false);
});
test('达到付费预算也保留本地居民对话',async()=>{
  const t=town(),[a,b]=t.active();t.configure({dailyLimit:1});t.state.stats.push({day:new Date().toLocaleDateString('en-CA')},{day:new Date().toLocaleDateString('en-CA')});await t.converse(a.id,b.id);assert.equal(a.relationships[b.id],2);
});
test('自动决策按墙钟间隔限流，模型自治关闭时保持零调用',async()=>{
  const t=town(),r=t.active()[0];t.state.providers.push({id:'paid',type:'openai'});r.model.providerId='paid';for(const resident of t.active())resident.remaining=1000;let count=0;t.llm={chatCompletion:async()=>{count++;return{text:'{"action":"idle","thought":"发呆"}',usage:{},latency:1};}};
  t.tick(.1);assert.equal(count,0);t.configure({autonomous:true,apiInterval:60});t.state.lastApiAt=Date.now();t.tick(.1);assert.equal(count,0);t.state.lastApiAt=Date.now()-61000;t.tick(.1);await new Promise(resolve=>setImmediate(resolve));assert.equal(count,1);t.tick(.1);assert.equal(count,1);t.configure({autonomous:false});t.state.lastApiAt=0;t.tick(.1);assert.equal(count,1);
});
test('模型或用户动作必须属于明确动作表，拒绝原型属性名',async()=>{
  const t=town(),r=t.active()[0];assert.throws(()=>t.act(r.id,'constructor'),/不支持/);t.state.providers.push({id:'paid',type:'openai'});r.model.providerId='paid';t.llm={chatCompletion:async()=>({text:'{"action":"toString","thought":"无效"}',usage:{},latency:1})};await assert.rejects(t.decide(r.id),/有效/);assert.equal(t.busy,false);assert.notEqual(r.action,'toString');
});

const {ANIMAL_ACTIONS,parseAnimalDecision,allowedAnimalActions}=require('../main/animals');
const animation=require('../renderer/animation');
function animalFixture(t) {
  const p={...structuredClone(t.state.residents[0]),id:'pet-unit-cat',catalogId:'unit-cat',kind:'animal',name:'测试猫',enabled:true,
    animal:{species:'猫',breed:'田园猫',coat:'虎斑',bodySize:'小',scale:.45,senses:'气味、运动、声音',behavior:'嗅闻、伏低',allowedActions:['idle','walk','rest','sniff','flee','eat','drink']},
    persona:{personality:'警觉，保持退路',background:'熟悉角落',likes:'气味与藏身处',speakingStyle:'自然叫声'},
    needs:{hunger:20,thirst:20,safety:85,stimulation:50},memory:[],messages:[],relationships:{},x:200,y:200};
  t.state.pets.push(p);return p;
}
test('动物动作按物种白名单执行，拒绝人类职业动作、对话和思想独白',()=>{
  const t=town(),p=animalFixture(t);assert.deepEqual(allowedAnimalActions(p),p.animal.allowedActions);
  assert.throws(()=>t.act(p.id,'work'),/物种/);assert.throws(()=>t.act(p.id,'greet'),/物种/);
  assert.throws(()=>t.say(p,'你好'),/人话/);assert.throws(()=>t.meet(t.active()[0],p),/交谈/);
  assert.throws(()=>parseAnimalDecision('{"action":"rest","thought":"下班了","senses":[],"need":"rest"}',p));
  assert.throws(()=>parseAnimalDecision('{"action":"rest","senses":["读懂文字"],"need":"rest"}',p));
  assert.throws(()=>parseAnimalDecision('{"action":"constructor","senses":[],"need":"rest"}',p));
  assert.ok(Object.hasOwn(ANIMAL_ACTIONS,'flee'));
});
test('动物API按独立模型返回感官与需求，无人类气泡、对话记忆和关系',async()=>{
  const t=town(),p=animalFixture(t);t.state.providers.push({id:'animal-model',type:'openai',apiKey:'animal-unit-key'});p.model.providerId='animal-model';p.model.model='animal-unit';let request;
  t.llm={chatCompletion:async opts=>{request=opts;return{text:'{"action":"sniff","senses":["smell","motion"],"need":"exploration"}',usage:{promptTokens:2,completionTokens:2},latency:1};}};
  await t.decide(p.id);assert.equal(p.action,'sniff');assert.deepEqual(p.observation,{senses:['smell','motion'],need:'exploration'});
  assert.match(request.system,/不得说人话/);assert.match(request.system,/田园猫/);assert.equal(p.bubble,'');assert.deepEqual(p.messages,[]);assert.deepEqual(p.relationships,{});
  assert.equal(t.state.stats.at(-1).purpose,'animal-decision');assert.equal(p.memory[0],'{"action":"sniff","senses":["smell","motion"],"need":"exploration"}');
  t.llm.chatCompletion=async()=>({text:'{"action":"work","senses":[],"need":"food"}',usage:{},latency:1});await assert.rejects(t.decide(p.id));assert.ok(allowedAnimalActions(p).includes(p.action));assert.equal(p.thinking,false);assert.equal(t.busy,false);
});
test('动物本地需求、运动和避让依据物种，不触发API',()=>{
  const t=town(),p=animalFixture(t);p.needs.hunger=90;assert.equal(t.localPetAction(p),'eat');p.needs.hunger=20;
  const r=t.active()[0];r.x=p.x+10;r.y=p.y;assert.equal(t.localPetAction(p),'flee');t.actPet(p.id,'flee');assert.ok(p.target.x<p.x);
  const x=p.x;t.tick(1);assert.ok(p.x<x);t.actPet(p.id,'rest');p.energy=10;t.tick(2);assert.ok(p.energy>10);assert.equal(t.state.stats.length,0);
  assert.throws(()=>t.setPets([p.id,p.id]));t.setPets([]);assert.equal(p.enabled,false);
});
test('atlas选择前后左右动作且循环边界连续，单次动作停留末帧',()=>{
  const p={kind:'human',action:'walk',direction:'back',moving:true,animation:{animations:{idle:{atlas:'idle.png',frames:16,frameMs:80,loop:true},walk_up:{atlas:'up.png',frames:16,frameMs:80,loop:true},jump:{atlas:'jump.png',frames:16,frameMs:80,loop:false}}}};
  assert.equal(animation.sample(p,0).atlas,'up.png');assert.equal(animation.sample(p,1279).frame,15);assert.equal(animation.sample(p,1280).frame,0);
  p.moving=false;p.action='jump';assert.equal(animation.sample(p,1280).frame,15);p.action='unknown';assert.equal(animation.sample(p,80).atlas,'idle.png');
});
test('旧档迁移保留居民编辑与记忆，动物需求与密钥加密保存可重启',()=>temporaryStore(dir=>{
  const old=initialState();delete old.pets;old.residents[0].name='我改过的名字';old.residents[0].persona.personality='我改过的性格';old.residents[0].memory=['原记忆'];
  const t=new Town(old,{});assert.equal(t.resident('resident-1').name,'我改过的名字');assert.equal(t.resident('resident-1').persona.personality,'我改过的性格');assert.deepEqual(t.resident('resident-1').memory,['原记忆']);
  const p=animalFixture(t);p.needs.hunger=42;p.thinking=true;p.moving=true;const store=new Persistence(dir,fakeSafe());store.save(t.state);const loaded=store.load();const pet=loaded.pets.find(v=>v.id===p.id);assert.equal(pet.needs.hunger,42);assert.equal(pet.thinking,false);assert.equal(pet.moving,false);assert.equal(loaded.autonomous,false);
}));
test('人形Codex Mini保留人格并使用人物交谈，真实动物限制仍独立',async()=>{
  const t=town(),a=t.active()[0],mini={...structuredClone(a),id:'resident-unit-mini',kind:'codexmini',name:'测试精灵',relationships:{},messages:[],memory:[]};t.state.residents.push(mini);
  await t.converse(a.id,mini.id);assert.equal(mini.relationships[a.id],2);assert.ok(mini.bubble);assert.ok(mini.memory.length);assert.match(t.prompt(mini),/职业/);
  const p=animalFixture(t);assert.throws(()=>t.say(p,'动物人类语言'),/人话/);
});
test('原Codex Mini逐帧可变时长准确播放并循环',()=>{
  const p={kind:'codexmini',action:'idle',animation:{animations:{idle:{atlas:'mini.png',frames:3,durations:[50,100,200],loop:true}}}};
  for(const [ms,expected]of [[0,0],[49,0],[50,1],[149,1],[150,2],[349,2],[350,0],[400,1]])assert.equal(animation.sample(p,ms).frame,expected);
  p.animation.animations.idle.loop=false;assert.equal(animation.sample(p,1000).frame,2);
});
test('原人物坐姿与游玩使用真实现有动作，mini缺睡眠时只等待',()=>{
  const clip=key=>({atlas:key+'.png',frames:8,frameMs:80,loop:true});
  const p={kind:'human',action:'rest',animation:{animations:{idle:clip('idle'),sit:clip('sit'),cheer:clip('cheer'),jump:clip('jump')}}};
  assert.equal(animation.clipFor(p).key,'sit');p.action='play';assert.equal(animation.clipFor(p).key,'cheer');
  p.kind='codexmini';p.animation.animations={idle:clip('idle'),wait:clip('wait'),wave:clip('wave')};p.action='rest';assert.equal(animation.clipFor(p).key,'wait');p.action='greet';assert.equal(animation.clipFor(p).key,'wave');
});
test('人设预设切换职业背景与作息，保留回忆并允许后续自定义字段',()=>{
  const t=town(),r=t.active()[0];r.memory=['老邻居的回忆'];r.presets=[{id:'farm',label:'农场学徒',role:'农场学徒',personality:'耐心',background:'熟悉农场',interests:['浇水','散步'],speech:'简短',schedule:[{start:'09:00',behavior:'照看幼苗'}]}];
  t.update(r.id,{presetId:'farm'});assert.equal(r.occupation,'农场学徒');assert.equal(r.persona.likes,'浇水、散步');assert.equal(r.schedule[0].behavior,'照看幼苗');assert.deepEqual(r.memory,['老邻居的回忆']);
  t.update(r.id,{presetId:'farm',occupation:'育苗员',persona:{personality:'更安静'}});assert.equal(r.occupation,'育苗员');assert.equal(r.persona.personality,'更安静');assert.match(t.prompt(r),/不混合成当前身份/);
});
