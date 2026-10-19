'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const E=require('../shared/emotions'),P=require('../shared/recovery-poses'),A=require('../shared/actions');
const {Town}=require('../main/engine'),{initialState,catalog}=require('../main/catalog'),{parseExpression,behaviorPrompt}=require('../main/character-behavior'),{Persistence}=require('../main/persistence');
const base=()=>new Town(initialState(),{}),person=(p,likes='阅读')=>({id:'fixture-'+p,asset:p,kind:'human',persona:{personality:p,likes},happiness:35,energy:70,social:50,relationships:{},action:'idle'});
test('三种恢复行为由疲劳、工作压力与夜间需要自动选择',()=>{
  const r=person('慵懒、敏感');r.emotion=E.normalize(r,540);r.energy=10;assert.equal(E.localPlan(r,540).action,'lie_down');r.energy=30;assert.equal(E.localPlan(r,540).action,'doze');assert.equal(E.localPlan(r,1320).action,'lie_down');r.energy=65;r.happiness=55;r.emotion.stress=80;assert.equal(E.localPlan(r,600).action,'slack');
});
test('同样低落时，独处与向亲近者倾诉是不同的选择，不强迫陌生人',()=>{
  const alone=person('安静、独立'),social=person('体贴、善于倾听'),friend={id:'friend',name:'熟人',action:'idle'},stranger={id:'stranger',name:'陌生人',action:'idle'};for(const r of [alone,social])r.relationships.friend=30;
  assert.notEqual(E.localPlan(alone,600,[friend,stranger],()=>0).action,'chat');assert.equal(E.localPlan(social,600,[friend,stranger],()=>0).partnerId,'friend');social.relationships.friend=0;assert.notEqual(E.localPlan(social,600,[friend,stranger],()=>0).action,'chat');
});
test('同样心情好时可以分享、投入爱好或活动身体，倾向按个人不同',()=>{
  const share=person('健谈、开朗','分享故事'),focus=person('安静、独立','阅读、下棋'),exercise=person('开朗','跑步、运动');for(const r of [share,focus,exercise])r.happiness=90;const neighbors=[{id:'one'},{id:'two'}];
  assert.equal(E.localPlan(share,600,neighbors,()=>0).action,'chat');assert.equal(E.localPlan(focus,1200,neighbors,()=>0).action,'play');assert.equal(E.localPlan(exercise,600,neighbors,()=>0).action,'walk');assert.equal(E.traits(focus).positive,'focus');
});
test('工作压力与实际恢复持续影响心情，日志批量记录且暂停冻结',()=>{
  const t=base(),r=t.active()[0];t.setRoster([r.id]);t.act(r.id,'work',{x:r.x,y:r.y});r.remaining=120;r.happiness=60;r.energy=80;const start=r.emotion.stress;for(let i=0;i<50;i++)t.tick(1);assert.ok(r.emotion.stress>start);assert.ok(t.journal.page(r.id).entries.some(e=>e.type==='emotion'&&/工作/.test(e.text)));
  t.act(r.id,'doze',{x:r.x,y:r.y});const before={energy:r.energy,stress:r.emotion.stress};t.tick(8);assert.ok(r.energy>before.energy);assert.ok(r.emotion.stress<before.stress);t.configure({running:false});const frozen=JSON.stringify([r.happiness,r.energy,r.emotion]);t.tick(20);assert.equal(JSON.stringify([r.happiness,r.energy,r.emotion]),frozen);
});
test('恢复需先到达目的地，睡眠人物不会被自动邀请打断，手动动作可唤醒',()=>{
  const t=base(),r=t.active()[0],other=t.active()[1];r.energy=10;t.act(r.id,'lie_down',{x:r.x+200,y:r.y});t.tick(1);assert.equal(r.energy,10);assert.ok(r.target);assert.ok(!t.partnersFor(other).some(x=>x.id===r.id));t.teleport(r.id,{x:r.x,y:r.y});t.act(r.id,'doze',{x:r.x,y:r.y});t.act(r.id,'walk',{x:r.x+10,y:r.y});assert.equal(r.action,'walk');assert.ok(r.target);
});
test('等待 API 调度不持续扣精力或拖垮心情，工作仍有实际消耗',()=>{
  const t=base(),r=t.active()[0];t.setRoster([r.id]);t.state.providers.push({id:'paid',type:'openai'});r.model.providerId='paid';t.configure({autonomous:true,apiInterval:3600});t.state.lastApiAt=Date.now();
  r.action='idle';r.remaining=0;r.behaviorStatus='waiting';r.energy=15;r.happiness=10;r.emotion=E.normalize(r,t.state.clock);const pressure=r.emotion.stress;
  for(let minute=0;minute<60;minute++)t.tick(1);
  assert.equal(r.energy,15);assert.ok(r.happiness>10);assert.ok(r.emotion.stress<pressure);assert.equal(t.state.stats.length,0);assert.equal(r.action,'idle');
  t.act(r.id,'work',{x:r.x,y:r.y});t.tick(5);assert.equal(r.energy,11);
});
test('自动休息预留不同空位，重启继续走到空位，手动摆放保持原位',()=>{
  const t=base(),people=t.active(),center={x:1240,y:710};
  t.state.providers.push({id:'paid',type:'openai'});t.configure({autonomous:true,apiInterval:3600});t.state.lastApiAt=Date.now();for(const r of people)r.model.providerId='paid';
  for(const [i,r] of people.entries())t.act(r.id,i%2?'doze':'lie_down',center,'api');
  for(let i=0;i<people.length;i++)for(let j=i+1;j<people.length;j++)assert.ok(Math.hypot(people[i].target.x-people[j].target.x,people[i].target.y-people[j].target.y)>=120);
  for(const r of people){r.x=center.x;r.y=center.y;r.target=null;r.action='lie_down';r.behaviorSource='api';}
  const resumed=new Town(structuredClone(t.state),{});assert.ok(resumed.active().every(r=>r.target&&Math.hypot(r.target.x-center.x,r.target.y-center.y)>=120));
  for(const r of people){r.action='idle';r.behaviorStatus='waiting';}
  const waiting=new Town(structuredClone(t.state),{});assert.ok(waiting.active().every(r=>r.action==='walk'&&r.target));for(let i=0;i<35;i++)waiting.tick(1);assert.ok(waiting.active().every(r=>r.action==='idle'&&!r.target));
  for(const r of resumed.active())r.behaviorSource='manual';const manual=new Town(structuredClone(resumed.state),{});const first=manual.active()[0];manual.act(first.id,'doze',center);assert.deepEqual(first.target,center);
});
test('实际听到的关心或冒犯影响个人心情，普通分歧不被一律当成侮辱',()=>{
  const r=person('冷静、理性'),speaker={id:'friend',name:'好友'};E.words(r,speaker,'谢谢你，辛苦了',600);assert.ok(r.happiness>35);const before=r.happiness;E.words(r,speaker,'我不同意，但愿意继续听听你的观点。',601);assert.equal(r.happiness,before);E.words(r,speaker,'你真没用，别烦我',602);assert.ok(r.happiness<before);assert.equal(r.emotion.recent.at(-1).relatedId,'friend');
});
test('近处见闻按个性影响感受，远处和私人心声不改变别人的心情',()=>{
  const t=base(),[a,b,c]=t.active();b.persona.personality='安静、独立';b.x=a.x+40;b.y=a.y;c.x=1510;c.y=910;a.x=200;a.y=200;b.x=240;b.y=200;const far=c.happiness;t.act(a.id,'cheer',{x:a.x,y:a.y});assert.ok(b.emotion.recent.some(x=>/热闹/.test(x.reason)));assert.equal(c.happiness,far);const before=b.happiness;t.event(a.name+'的心声：我讨厌你','thought',[a.id]);assert.equal(b.happiness,before);
});
test('API 心情自评与新恢复动作采用同一次结构化回复，未知或越界值拒绝',()=>{
  const animation=catalog[0].animation,valid={action:'doze',thought:'有些困了，想缓一缓',speech:'',duration:25,emotion:{change:2,stress:-2,reason:'先休息，不强撑'}};
  assert.equal(parseExpression(JSON.stringify(valid),animation).emotion.change,2);for(const mutation of [{emotion:{change:100,stress:0,reason:'好'}},{emotion:{change:0,stress:1.5,reason:'好'}},{emotion:{change:0,stress:0,reason:''}},{action:'doze',destination:{x:1600,y:200}}])assert.throws(()=>parseExpression(JSON.stringify({...valid,...mutation}),animation));
  assert.ok(!A.available(animation,'conversation').includes('lie_down'));assert.ok(A.available(animation).includes('slack'));assert.match(behaviorPrompt(animation),/情绪倾向/);assert.ok(!behaviorPrompt(animation,{mode:'conversation'}).includes('最多六轮'));
});
test('模型得到自己的心情、原因与熟人倾向，私有感受不流给邻居',()=>{
  const t=base(),[a,b]=t.active();a.emotion.reason='私人感受测试字符串';a.persona.personality='体贴';a.relationships[b.id]=30;assert.ok(t.prompt(a).includes('私人感受测试字符串'));assert.ok(!t.prompt(b).includes('私人感受测试字符串'));assert.match(t.prompt(a),/emotions/);
});
test('心情与压力在正式存档结构中恢复，非法数据不会覆盖存档',()=>{
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'town-emotion-')),safe={isEncryptionAvailable:()=>true,encryptString:x=>Buffer.from(x),decryptString:x=>x.toString()};try{const t=base(),r=t.active()[0],store=new Persistence(dir,safe);t.recordEmotion(r,E.apply(r,{change:-3,stress:4,reason:'工作有一点累'},600));store.save(t.state);const loaded=new Town(store.load(),{}).resident(r.id);assert.equal(loaded.emotion.reason,'工作有一点累');assert.equal(loaded.happiness,r.happiness);const before=fs.readFileSync(store.file);r.emotion.stress=1000;assert.throws(()=>store.save(t.state));assert.deepEqual(fs.readFileSync(store.file),before);}finally{fs.rmSync(dir,{recursive:true,force:true});}
});
test('侧躺拒绝站姿旋转回退，坐姿与打盹继续使用透明画布',()=>{
  const image={width:64,height:96,data:new Uint8ClampedArray(64*96*4)};for(let y=10;y<80;y++)for(let x=20;x<40;x++)image.data.set([x,y,100,255],(y*64+x)*4);const original=Buffer.from(image.data);assert.throws(()=>P.pixels(image,'lie_down'),/专门绘制/);const out=P.pixels(image,'doze');assert.equal(out.width,256);assert.equal(out.height,256);assert.deepEqual(Buffer.from(image.data),original);assert.equal(out.data[3],0);
});
test('双方继续时超过六轮，任一方主动结束即停止',async()=>{
  const t=base(),[a,b]=t.active();t.state.providers.push({id:'model',type:'openai',apiKey:'',name:'测试'});for(const r of [a,b])r.model.providerId='model';let calls=0;t.llm.chatCompletion=async()=>({text:JSON.stringify({action:'chat',thought:'继续聊聊',speech:'愿意听听你接着说。',interaction:{feeling:0,continue:++calls<9}}),usage:{},latency:1});assert.equal((await t.converse(a.id,b.id)).turns,9);assert.equal(calls,9);assert.equal(t.busy,false);
});
test('超过六轮后暂停仍取消网络等待，不产生迟到发言',async()=>{
  const t=base(),[a,b]=t.active();t.state.providers.push({id:'model',type:'openai',apiKey:'',name:'测试'});for(const r of [a,b])r.model.providerId='model';t.configure({autonomous:true});let calls=0,ready;const seventh=new Promise(resolve=>ready=resolve);t.llm.chatCompletion=async({signal})=>{if(++calls===7){ready();await new Promise((_,reject)=>signal.addEventListener('abort',()=>reject(new Error('cancelled')),{once:true}));}return {text:JSON.stringify({action:'chat',thought:'还想聊',speech:'我愿意继续听。',interaction:{feeling:0,continue:true}}),usage:{},latency:1};};const task=t.converse(a.id,b.id,true);await seventh;t.configure({running:false});await task;assert.equal(calls,7);assert.equal(t.busy,false);assert.equal(t.state.stats.at(-1).applied,false);assert.equal(t.journal.page(a.id).entries.filter(x=>x.type==='speech'&&x.source==='heard').length,3);
});
