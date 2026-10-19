'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {Town}=require('../main/engine');
const {initialState,ZONES,catalog}=require('../main/catalog');
const {Journal}=require('../main/journal');
const {Persistence}=require('../main/persistence');
const {parseExpression}=require('../main/character-behavior');
const Life=require('../shared/life');
const safe={isEncryptionAvailable:()=>true,encryptString:s=>Buffer.from(s),decryptString:b=>b.toString()};
const reply=value=>({text:JSON.stringify(value),usage:{promptTokens:10,completionTokens:15},latency:1});
const expression=(action='rest',extra={})=>({action,thought:'想把今天安排好。',speech:'',...extra});
const pause=()=>new Promise(resolve=>setImmediate(resolve));
function fixture(journal=new Journal()){
  const t=new Town(initialState(),{},()=>{},journal),a=t.state.residents.find(r=>r.asset==='16_librarian_female'),b=t.state.residents.find(r=>r.asset==='03_barista_male');
  t.setRoster([a.id,b.id]);t.state.providers.push({id:'life-api',name:'测试 API',type:'openai',apiKey:'private-life-unit-key'});
  for(const r of [a,b])r.model={providerId:'life-api',model:'test-model',temperature:.6,maxTokens:500};
  t.llm={chatCompletion:async()=>reply(expression())};return {t,a,b};
}
async function temp(fn){const dir=fs.mkdtempSync(path.join(os.tmpdir(),'town-life-'));try{return await fn(dir);}finally{fs.rmSync(dir,{recursive:true,force:true});}}

test('每个人物获得独立生活方向，原身份、API、人设、记忆和关系保持',()=>{
  const state=initialState(),old=structuredClone(state.residents);state.residents[0].memory=['昨天和朋友聊过'];state.residents[0].relationships['resident-2']=12;
  const t=new Town(state,{});assert.equal(t.state.residents.length,45);assert.equal(new Set(t.state.residents.map(r=>r.life.aspiration)).size,45);
  for(let i=0;i<old.length;i++)for(const key of ['name','persona','model','enabled','occupation','asset'])assert.deepEqual(t.state.residents[i][key],old[i][key]);
  assert.equal(t.state.residents[0].memory[0],'昨天和朋友聊过');assert.equal(t.state.residents[0].relationships['resident-2'],12);
  assert.equal(t.journal.subjects.size,72);assert.ok(t.journal.subjects.has('place-work'));assert.ok(t.journal.subjects.has('sky-moon'));
});

test('真实决策请求带应用能力、当前职业作息、共同资料及日志；私密资料不串人',async()=>{
  const {t,a,b}=fixture();a.x=500;a.y=500;b.x=580;b.y=500;
  t.setKnowledge({...Life.defaults,background:'这里在筹备邻里读书交流',facts:'公告：周末分享书单'});
  t.event('我今天观察到太阳升起','life',[a.id]);b.lastExpression={thought:'another-character-private-thought'};b.memory=['another-character-private-memory'];
  let request;t.llm.chatCompletion=async x=>{request=x;return reply(expression('work',{duration:40,goal:{title:'想整理自己的阅读思路',reason:'为下次分享做好准备',status:'ongoing'}}));};
  await t.decide(a.id);
  for(const word of ['2D 像素生活','周末分享书单','我今天观察到太阳升起','occupationalReference','持续目标','实际功能'])assert.ok(request.system.includes(word),word);
  assert.ok(!request.system.includes('private-life-unit-key'));assert.ok(!request.system.includes('another-character-private-thought'));assert.ok(!request.system.includes('another-character-private-memory'));
  assert.equal(a.remaining,40);assert.equal(a.life.focus.title,'想整理自己的阅读思路');assert.deepEqual(a.target,ZONES.work);
});

test('夜间跨午夜作息准确，职业背景不会虚构成已经创建的建筑',()=>{
  const r=catalog.find(r=>r.asset==='16_librarian_female');
  assert.match(Life.routineAt(r,23*60).time,/22:30/);assert.equal(Life.routineAt(r,3*60).backgroundPlace,'住宅区');
  assert.notEqual(Life.routineAt(r,9*60).backgroundPlace,'住宅区');assert.match(Life.guide(ZONES),/没有职业产出/);
});

test('API 提出的目标跨行为与重启持续，计划、到达、进展和完成自评分开',()=>temp(async dir=>{
  const journal=new Journal(path.join(dir,'journals')),{t,a}=fixture(journal);t.configure({autonomous:true});
  const goal={title:'先恢复精力再去认识邻居',reason:'我今天有些累了',status:'ongoing'};
  t.llm.chatCompletion=async()=>reply(expression('rest',{duration:1,goal}));await t.decide(a.id);
  let entries=journal.page(a.id).entries;assert.ok(entries.some(e=>e.type==='goal'&&e.goalStatus==='ongoing'));assert.ok(!entries.some(e=>e.type==='outcome'&&e.text.includes('这一段行为结束')));
  a.x=a.target.x;a.y=a.target.y;t.state.lastApiAt=Date.now();t.tick(1);
  entries=journal.page(a.id).entries;assert.ok(entries.some(e=>e.type==='arrival'));assert.ok(entries.some(e=>e.type==='outcome'&&e.text.includes('这一段行为结束')));assert.equal(a.life.focus.status,'ongoing');
  const store=new Persistence(dir,safe);store.save(t.state);journal.flush();const restored=new Town(store.load(),{},()=>{},new Journal(path.join(dir,'journals'))),r=restored.resident(a.id);
  assert.equal(r.life.focus.title,goal.title);assert.ok(restored.prompt(r).includes('这一段行为结束'));assert.equal(restored.state.autonomous,true);
  restored.llm={chatCompletion:async()=>reply(expression('idle',{goal:{...goal,reason:'已经休息好，可以开始新的一步',status:'completed'}}))};await restored.decide(a.id);assert.equal(r.life.focus.status,'completed');
  assert.ok(restored.journal.page(a.id).entries.some(e=>e.goalStatus==='completed'&&e.text.startsWith('自评完成')));
}));

test('目标、交流意愿和时长严格受限，不能结束不存在的目标或改变单次摇头长度',()=>{
  const {a}=fixture();
  for(const extra of [{goal:{title:'新目标',reason:'想做',status:'completed'}},{goal:{title:'a',reason:'b',status:'ongoing',hidden:1}},{duration:181},{duration:'30'},{interaction:{feeling:1,continue:true}}])assert.throws(()=>parseExpression(JSON.stringify(expression('rest',extra)),a.animation),/有效/);
  assert.throws(()=>parseExpression(JSON.stringify(expression('shake_head',{duration:30})),a.animation),/时长/);
  assert.throws(()=>parseExpression(JSON.stringify(expression('nod',{speech:'好',interaction:{feeling:-4,continue:true}})),a.animation,{mode:'conversation'}),/交流意愿/);
});

test('日志按游戏日期留存超过180条，分页筛选与整天导出不丢更早经历',()=>temp(dir=>{
  const j=new Journal(dir);j.register({id:'person-1',name:'测试居民',kind:'human'},500);
  for(let n=0;n<245;n++)j.add('person-1',{time:500+n,type:n%2?'thought':'action',text:'真实记录 '+n});
  j.add('person-1',{time:1441,type:'environment',text:'第二天已到来'});j.flush();
  const restored=new Journal(dir),page=restored.page('person-1',{day:1,type:'action',limit:20});assert.equal(page.total,246);assert.equal(page.filteredTotal,123);assert.equal(page.entries.length,20);assert.equal(page.hasMore,true);
  const second=restored.page('person-1',{day:1,type:'action',limit:20,cursor:page.nextCursor});assert.ok(page.entries.every(e=>!second.entries.some(x=>x.id===e.id)));
  assert.deepEqual(restored.days('person-1'),[2,1]);assert.ok(restored.markdown('person-1',1).includes('真实记录 0'));assert.ok(restored.markdown('person-1',1).includes('真实记录 244'));
  assert.throws(()=>restored.page('../outside'),/日志对象/);assert.throws(()=>restored.page('person-1',{day:0}),/参数/);assert.throws(()=>restored.page('person-1',{limit:1000}),/参数/);
}));

test('损坏日志原文保留，可读记录继续分页；之后的写入不被残缺行吞掉',()=>temp(dir=>{
  const j=new Journal(dir);j.register({id:'subject',name:'测试',kind:'human'},500);j.add('subject',{time:501,type:'thought',text:'完整记录'});j.flush();const file=path.join(dir,'subject/1.jsonl');fs.appendFileSync(file,'{"broken"');
  const recovered=new Journal(dir);assert.equal(recovered.page('subject').total,2);assert.match(recovered.page('subject').warning,/1 条损坏/);assert.ok(fs.readFileSync(file,'utf8').endsWith('{"broken"'));
  recovered.add('subject',{time:502,type:'outcome',text:'后续实际进展'});recovered.flush();const next=new Journal(dir);assert.equal(next.page('subject').total,3);assert.ok(next.page('subject').entries.some(e=>e.text==='后续实际进展'));assert.ok(fs.readFileSync(file,'utf8').includes('{"broken"'));
}));

test('附近居民记录公开见闻，远处人物与私人心声不会泄漏；动物只记录刺激',()=>{
  const {t,a,b}=fixture();a.x=500;a.y=500;b.x=600;b.y=500;const far=t.state.residents.find(r=>r.id!==a.id&&r.id!==b.id);far.enabled=true;far.x=1400;far.y=900;
  const pet=t.state.pets[0];pet.enabled=true;pet.x=550;pet.y=500;
  t.event(a.name+'向邻居挥手','life',[a.id]);t.event(a.name+'的私人心声：private-only','thought',[a.id]);
  assert.ok(t.journal.page(b.id).entries.some(e=>e.type==='observation'&&e.text.includes('挥手')));assert.ok(!t.journal.page(b.id).entries.some(e=>e.text.includes('private-only')));assert.ok(!t.journal.page(far.id).entries.some(e=>e.text.includes('挥手')));
  assert.ok(t.journal.page(pet.id).entries.some(e=>e.type==='observation'&&e.text.includes('感官刺激')));assert.ok(!t.prompt(pet).includes('private-only'));assert.ok(!t.prompt(pet).includes('向邻居挥手'));
});

test('无需人工动作的连续模型生活轮流思考，完成后继续且受间隔与暂停约束',async()=>{
  const {t}=fixture(),[a,b]=t.active(),calls=[];a.target=b.target=null;a.remaining=b.remaining=0;t.configure({autonomous:true});
  t.llm.chatCompletion=async opts=>{calls.push(opts.system);return reply(expression('idle',{duration:1,goal:{title:'先观察一下周围',reason:'想知道邻居在做什么',status:'ongoing'}}));};
  t.state.lastApiAt=0;t.tick(.1);await pause();assert.equal(calls.length,1);assert.equal(a.behaviorSource,'api');
  t.tick(.1);await pause();assert.equal(calls.length,1);t.state.lastApiAt=Date.now()-61000;t.tick(.1);await pause();assert.equal(calls.length,2);assert.equal(b.behaviorSource,'api');
  t.state.lastApiAt=Date.now()-61000;t.tick(2);await pause();assert.equal(calls.length,3);assert.ok(calls[2].includes('先观察一下周围'));assert.ok(calls[2].includes('这一段行为结束'));
  t.configure({running:false});t.state.lastApiAt=0;t.tick(100);await pause();assert.equal(calls.length,3);
});

test('模型主动邀请后到达才交流，台词复用并记入双方日志',async()=>{
  const {t}=fixture(),[a,b]=t.active();t.configure({autonomous:true});let calls=0;
  t.llm.chatCompletion=async()=>{calls++;return reply(calls===1?expression('chat',{partnerId:b.id,speech:'想听听你对安静阅读的看法',goal:{title:'和邻居交换兴趣',reason:'想慢慢认识彼此',status:'ongoing'}}):expression('chat',{speech:'我也喜欢安静，但更喜欢边喝咖啡边聊。',interaction:{feeling:2,continue:false}}));};
  a.remaining=b.remaining=0;t.state.lastApiAt=0;t.tick(.1);await pause();assert.equal(calls,1);assert.equal(a.meeting.partner,b.id);
  t.state.lastApiAt=Date.now()-61000;t.tick(.1);assert.equal(calls,1);
  a.x=a.target.x;a.y=a.target.y;b.x=b.target.x;b.y=b.target.y;t.tick(.1);t.tick(.1);await pause();assert.equal(calls,2);assert.equal(a.meeting,null);assert.equal(b.meeting,null);
  assert.ok(t.journal.page(b.id).entries.some(e=>e.type==='speech'&&e.text.includes('想听听')));assert.ok(t.journal.page(a.id).entries.some(e=>e.type==='speech'&&e.text.includes('边喝咖啡')));
});

test('自主交流可持续、分歧与结束由模型表达；两人主观关系可以不同',async()=>{
  const {t,a,b}=fixture();const replies=[
    expression('shake_head',{speech:'我不同意，把所有活动都安排一起会让我累。',interaction:{feeling:-2,continue:true}}),
    expression('chat',{speech:'我理解，但相处多一点也能认识彼此。',interaction:{feeling:2,continue:true}}),
    expression('shake_head',{speech:'我还是需要自己的时间，今天先聊到这里。',interaction:{feeling:-1,continue:false}})
  ];let requests=0;t.llm.chatCompletion=async()=>reply(replies[requests++]);const result=await t.converse(a.id,b.id);
  assert.equal(requests,3);assert.equal(result.turns,3);assert.equal(a.relationships[b.id],-1);assert.equal(b.relationships[a.id],2);assert.match(a.bubble,/先聊到这里/);assert.equal(a.action,'shake_head');
  assert.ok(t.journal.page(a.id).entries.some(e=>e.type==='relation'&&e.text.includes('-1')));assert.ok(!t.prompt(b).includes('我对'+b.name+'的印象变化 -1'));
});

test('持续交流超过六轮，额度不足不会再请求；没有继续意愿时仍按两轮兼容',async()=>{
  const {t,a,b}=fixture();let calls=0;t.llm.chatCompletion=async()=>{calls++;return reply(expression('chat',{speech:'我还想听听你的看法。',interaction:{feeling:0,continue:true}}));};
  t.configure({dailyLimit:10});assert.equal((await t.converse(a.id,b.id)).turns,10);assert.equal(calls,10);
  t.configure({dailyLimit:12});assert.equal((await t.converse(a.id,b.id)).turns,2);assert.equal(calls,12);assert.equal(t.dailyCalls(),12);
});

test('明确开启的自主生活重启恢复；关闭、旧存档以及暂停都保留用户选择',()=>temp(dir=>{
  const {t}=fixture();const store=new Persistence(dir,safe);t.configure({autonomous:true});store.save(t.state);assert.equal(store.load().autonomous,true);
  t.configure({autonomous:false});store.save(t.state);assert.equal(store.load().autonomous,false);
  const old=initialState();old.autonomous=true;delete old.resumeAutonomy;store.save(old);assert.equal(store.load().autonomous,false);
  t.configure({autonomous:true,running:false});store.save(t.state);assert.equal(store.load().autonomous,true);assert.equal(store.load().running,false);
}));

test('改基础资料、暂停或手动动作使迟到的自动目标与台词失效，不写成已经行动',async()=>{
  for(const change of ['world','pause','manual']){
    const {t,a}=fixture();t.configure({autonomous:true});let release;t.llm.chatCompletion=()=>new Promise(resolve=>release=resolve);
    const request=t.decide(a.id,{automatic:true});await pause();
    if(change==='world')t.setKnowledge({...Life.defaults,facts:'新公告'});else if(change==='pause')t.configure({running:false});else t.act(a.id,'greet');
    release(reply(expression('work',{speech:'late-secret-speech',goal:{title:'late-secret-goal',reason:'旧决定',status:'ongoing'}})));
    assert.equal((await request).discarded,true);assert.ok(!JSON.stringify(t.journal.page(a.id)).includes('late-secret'));assert.equal(a.life.focus,null);
  }
});

test('动物模型完成自身自然活动再思考，不被本地随机动作覆盖；取消迟到行为',async()=>{
  const {t}=fixture(),p=t.state.pets[0];p.enabled=true;p.model={providerId:'life-api',model:'pet',temperature:.5,maxTokens:200};t.configure({autonomous:true});p.remaining=0;p.target=null;
  t.llm.chatCompletion=async()=>reply({action:'rest',senses:['light'],need:'rest'});await t.decide(p.id);assert.equal(p.behaviorSource,'api');t.state.lastApiAt=Date.now();p.remaining=1;t.tick(1);assert.equal(p.behaviorStatus,'waiting');assert.equal(p.behaviorSource,'api');
  let release;t.llm.chatCompletion=()=>new Promise(resolve=>release=resolve);const request=t.decide(p.id,{automatic:true});await pause();t.setPets([]);release(reply({action:'walk',senses:['motion'],need:'exploration'}));assert.equal((await request).discarded,true);assert.equal(p.enabled,false);
});

test('昼夜和区域日志按实际时刻记录，时间跳转不补写途中没有发生的活动',()=>{
  const {t,a}=fixture();t.advanceTo(1320);const entries=t.journal.page(a.id).entries;assert.ok(entries.some(e=>e.type==='environment'&&e.text.includes('夜晚')));assert.ok(!entries.some(e=>e.type==='environment'&&e.text.includes('日落')));
  assert.ok(t.journal.page('place-work').entries.some(e=>e.type==='environment'));t.advanceTo(360);assert.ok(t.journal.page(a.id,{day:2}).entries.some(e=>e.text.includes('日出')));
});

test('日志保留完整台词和镇长长消息，画面气泡的短显示不会截断原文',async()=>{
  const {t,a}=fixture(),speech='很长的角色台词。'.repeat(35),message='镇长说的完整事情。'.repeat(300);
  t.llm.chatCompletion=async()=>reply(expression('chat',{speech}));await t.chat(a.id,message);
  assert.equal(a.bubble.length,140);const entries=t.journal.page(a.id).entries;assert.ok(entries.some(e=>e.type==='speech'&&e.text.endsWith(speech)));assert.ok(entries.some(e=>e.type==='speech'&&e.text.endsWith(message)));
});

test('低精力和天色变化可让模型重新考虑长行为，仍只执行模型自己的选择',async()=>{
  const {t,a,b}=fixture();t.configure({autonomous:true});a.action='work';a.target=null;a.remaining=120;a.energy=12;a.decisionAt=Date.now()-61000;b.decisionAt=Date.now();b.remaining=999;t.state.lastApiAt=0;
  let calls=0;t.llm.chatCompletion=async()=>{calls++;return reply(expression('rest',{duration:30,goal:{title:'先恢复精力',reason:'我感到累了，暂时不继续工作',status:'ongoing'}}));};
  t.tick(.1);await pause();assert.equal(calls,1);assert.equal(a.action,'rest');assert.equal(a.remaining,30);assert.equal(a.life.focus.title,'先恢复精力');
  a.target=null;a.energy=90;a.social=65;a.action='work';a.remaining=90;a.lastExpression.time=12*60;t.state.clock=22*60;assert.equal(t.readyForDecision(a),true);
});
