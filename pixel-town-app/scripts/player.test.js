'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const vm=require('node:vm');
const {Town}=require('../main/engine');
const {Persistence}=require('../main/persistence');
const {initialState}=require('../main/catalog');
const appearance=require('../shared/appearance');
const payload=(name='旅人',extra={})=>({name,appearance:{...appearance.defaults,...extra}});
const create=t=>{t.state.player=t.preparePlayer(payload());return t.state.player;};
const temporary=fn=>{const dir=fs.mkdtempSync(path.join(os.tmpdir(),'pixel-town-player-test-'));return Promise.resolve().then(()=>fn(dir)).finally(()=>fs.rmSync(dir,{recursive:true,force:true}));};
const safe={isEncryptionAvailable:()=>true,encryptString:s=>Buffer.from(s),decryptString:b=>b.toString()};

test('两种主角形象可切换并重启，独立组件和原捏脸参数均保留',()=>temporary(async dir=>{
  const t=new Town(initialState(),{}),player=create(t);
  player.memory=['保留的生活记录'];player.relationships[t.state.residents[0].id]=12;player.x=933;
  Object.assign(player,t.preparePlayer(payload('旅人',{hairStyle:'twintails',hairColor:'#AA5566',height:4,presetHairColor:'#7C503E',presetAccessory:'roundGlasses'})));
  Object.assign(player,t.preparePlayer({name:player.name,appearance:{...player.appearance,styleMode:'custom'}}));
  assert.equal(player.appearance.presetAccessory,'roundGlasses');assert.equal(player.appearance.hairStyle,'twintails');
  Object.assign(player,t.preparePlayer({name:player.name,appearance:{...player.appearance,styleMode:'preset',avatarPreset:'20_student_female'}}));
  const store=new Persistence(dir,safe);store.save(t.state);const restored=new Town(store.load(),{}).state.player;
  assert.equal(restored.appearance.styleMode,'preset');assert.equal(restored.appearance.avatarPreset,'20_student_female');
  assert.equal(restored.appearance.hairStyle,'twintails');assert.equal(restored.appearance.hairColor,'#AA5566');assert.equal(restored.appearance.height,4);
  assert.equal(restored.appearance.presetHairColor,'#7C503E');assert.equal(restored.appearance.presetAccessory,'roundGlasses');
  assert.equal(restored.x,933);assert.deepEqual(restored.memory,['保留的生活记录']);assert.equal(restored.relationships[t.state.residents[0].id],12);
}));

test('主角独立于 NPC；旧存档和初始状态没有自动创建主角',()=>{
  const t=new Town(initialState(),{}),npcBefore=structuredClone(t.state.residents);
  assert.equal(t.state.player,null);assert.throws(()=>t.resident('player'),/不存在/);
  const candidate=t.preparePlayer(payload());assert.equal(t.state.player,null);
  t.state.player=candidate;assert.equal(candidate.id,'player');assert.equal(candidate.isPlayer,true);assert.equal(candidate.kind,'human');
  assert.equal(t.resident('player'),candidate);assert.equal(t.entity('player'),candidate);assert.ok(t.inhabitants().includes(candidate));
  assert.deepEqual(t.state.residents,npcBefore);assert.equal(t.active().filter(r=>!r.isPlayer).length,6);assert.equal(t.active().length,7);
  assert.deepEqual(candidate.model,{providerId:'demo',model:'demo',temperature:.8,maxTokens:300});
});

test('NPC 人数和阵容保持 1–60 范围，增减不会改变或解除主角',()=>{
  const t=new Town(initialState(),{}),player=create(t);player.memory=['我的记忆'];t.control('player');
  t.setCount(60);assert.equal(t.state.residents.filter(r=>r.enabled).length,60);assert.equal(t.active().length,61);
  t.setCount(1);assert.equal(t.active().length,2);assert.equal(t.state.controlledId,'player');
  const npc=t.state.residents.find(r=>r.enabled);t.setRoster([npc.id]);assert.equal(t.state.player,player);assert.equal(t.state.controlledId,'player');
  assert.throws(()=>t.setRoster(['player']));assert.deepEqual(player.memory,['我的记忆']);
});

test('主角静止且无自主 AI；键盘、点击地面移动与手动动作可用',async()=>{
  let calls=0;const t=new Town(initialState(),{chatCompletion:async()=>{calls++;throw new Error('不应请求');}}),r=create(t);
  for(const npc of t.state.residents)npc.remaining=10000;
  const position={x:r.x,y:r.y};r.remaining=-100;t.tick(5);assert.deepEqual({x:r.x,y:r.y},position);assert.equal(r.action,'idle');assert.equal(r.target,null);
  t.control('player');t.setInput({x:1,y:1});t.tick(1);assert.ok(Math.abs(Math.hypot(r.x-position.x,r.y-position.y)-75)<.001);
  t.setInput({x:0,y:0});t.tick(.1);assert.equal(r.action,'idle');assert.equal(r.moving,false);
  t.move('player',{x:r.x+50,y:r.y});const x=r.x;t.tick(1);assert.equal(r.x,x+30);assert.equal(r.moving,true);
  t.act('player','jump');assert.equal(r.action,'jump');t.tick(5);assert.equal(r.action,'idle');
  await assert.rejects(t.decide('player'),/亲自控制/);assert.equal(calls,0);
});

test('NPC 自动交谈不会选择玩家；手动邀请完成双向关系和记忆',async()=>{
  const t=new Town(initialState(),{}),player=create(t);t.setCount(1);const npc=t.state.residents.find(r=>r.enabled);
  t.localAction=()=> 'chat';npc.remaining=0;t.tick(.1);assert.equal(npc.meeting,undefined);assert.equal(player.memory.length,0);
  assert.throws(()=>t.meet(npc,player),/玩家邀请/);await assert.rejects(t.converse(npc.id,'player',true),/玩家邀请/);
  t.control('player');t.meet(player,npc,false);const target=structuredClone(player.target);t.setInput({x:1,y:0});assert.deepEqual(player.target,target);
  t.tick(.1);assert.equal(player.action,'chat');assert.ok(player.meeting);assert.equal(player.memory.length,0);
  player.x=player.target.x;player.y=player.target.y;npc.x=npc.target.x;npc.y=npc.target.y;
  t.tick(.1);t.tick(.1);await new Promise(resolve=>setImmediate(resolve));
  assert.equal(player.relationships[npc.id],2);assert.equal(npc.relationships.player,2);assert.ok(player.memory.some(m=>m.includes(npc.name)));assert.equal(t.busy,false);
});

test('主角手动动作持续播放且保持控制；按键可中断动作重新走动',()=>{
  const t=new Town(initialState(),{}),player=create(t);t.control('player');
  for(const npc of t.state.residents)npc.remaining=10000;
  for(const action of ['greet','cheer','jump','rest','surprise','idle','play']) {
    t.setInput({x:1,y:1});t.tick(.1);t.act('player',action);
    assert.equal(t.state.controlledId,'player');assert.deepEqual(t.input,{x:0,y:0});assert.equal(player.target,null);assert.equal(player.moving,false);
    const start={x:player.x,y:player.y},duration=player.remaining;t.tick(.2);
    assert.equal(player.action,action);assert.equal(player.remaining,duration-.2);assert.deepEqual({x:player.x,y:player.y},start);
    t.setInput({x:1,y:0});t.tick(.1);assert.equal(player.action,'walk');assert.equal(player.moving,true);assert.equal(t.state.controlledId,'player');
    t.setInput({x:0,y:0});t.tick(.1);assert.equal(player.action,'idle');
    t.act('player',action);t.tick(player.remaining+.1);assert.equal(player.action,'idle');assert.equal(t.state.controlledId,'player');assert.equal(player.target,null);
  }
  const npc=t.state.residents.find(r=>r.enabled);t.control(npc.id);t.act(npc.id,'jump');assert.equal(t.state.controlledId,null);
});

test('主角表情严格接受 schema 枚举，非法输入无状态变化；可持久化恢复',()=>temporary(dir=>{
  const t=new Town(initialState(),{});assert.throws(()=>t.setPlayerExpression('happy'),/不存在/);const player=create(t);t.control('player');
  const expressions=appearance.fields.find(field=>field.key==='expression').options.map(option=>option.value);
  for(const expression of expressions){const revision=t.revision;assert.equal(t.setPlayerExpression(expression),true);assert.equal(player.appearance.expression,expression);assert.equal(t.revision,revision+1);assert.equal(t.state.controlledId,'player');}
  const before=structuredClone(t.state),revision=t.revision;
  for(const invalid of [null,undefined,42,'smile','constructor',{},['happy']])assert.throws(()=>t.setPlayerExpression(invalid));
  assert.deepEqual(t.state,before);assert.equal(t.revision,revision);
  const p=new Persistence(dir,safe);t.setPlayerExpression('shy');p.save(t.state);assert.equal(p.load().player.appearance.expression,'shy');
}));

test('改外观保留主角位置、聊天、记忆、关系与途中邀请，不改 NPC',()=>{
  const t=new Town(initialState(),{}),player=create(t),npc=t.state.residents.find(r=>r.enabled);t.meet(player,npc,false);
  player.x=915;player.y=715;player.memory=['保持'];player.messages=[{role:'user',content:'你好',time:0}];player.relationships[npc.id]=12;
  const before=structuredClone(t.state.residents),candidate=t.preparePlayer(payload('新旅人',{hairColor:'#abcdef',gender:'female'}));
  assert.equal(candidate.x,915);assert.equal(candidate.y,715);assert.deepEqual(candidate.meeting,player.meeting);assert.deepEqual(candidate.memory,player.memory);assert.deepEqual(candidate.messages,player.messages);assert.deepEqual(candidate.relationships,player.relationships);
  assert.equal(candidate.gender,'女');assert.equal(candidate.appearance.hairColor,'#ABCDEF');assert.deepEqual(t.state.residents,before);
  assert.throws(()=>t.update('player',{model:{providerId:'demo'}}),/编辑器/);
});

test('非法主角输入不会修改原玩家、控制、阵容和事件',()=>{
  const t=new Town(initialState(),{});create(t);t.control('player');const before=structuredClone(t.state);
  for(const value of [null,{},payload(''),payload('a'.repeat(31)),payload('旅人',{skin:'red'}),payload('旅人',{height:99}),payload('旅人',{eyes:'constructor'}),payload('旅人',{unknown:true}),{name:'旅人',appearance:[]}])assert.throws(()=>t.preparePlayer(value));
  assert.deepEqual(t.state,before);
});

test('旧档兼容；重启恢复玩家外观、位置、关系及聊天并清理运行标志',()=>temporary(dir=>{
  const p=new Persistence(dir,safe),old=initialState();delete old.player;p.save(old);assert.equal(p.load().player,null);
  const t=new Town(p.load(),{}),player=create(t),npc=t.state.residents.find(r=>r.enabled);player.appearance=appearance.normalize({gender:'male',hairStyle:'curly',skin:'#987654'});player.gender='男';
  player.x=1000;player.y=800;player.relationships[npc.id]=21;player.memory=['持续记忆'];player.messages=[{role:'assistant',content:'持续聊天',time:10}];
  t.meet(player,npc,false);player.thinking=true;player.moving=true;t.state.controlledId='player';t.state.autonomous=true;p.save(t.state);
  const loaded=p.load();assert.deepEqual(loaded.player.appearance,player.appearance);assert.equal(loaded.player.x,1000);assert.equal(loaded.player.y,800);
  assert.deepEqual(loaded.player.memory,['持续记忆']);assert.deepEqual(loaded.player.messages,player.messages);assert.equal(loaded.player.relationships[npc.id],21);
  assert.equal(loaded.player.thinking,false);assert.equal(loaded.player.moving,false);assert.equal(loaded.player.action,'idle');assert.equal(loaded.player.target,null);assert.equal(loaded.player.meeting,null);assert.equal(loaded.controlledId,null);assert.equal(loaded.autonomous,false);
  assert.equal(loaded.residents.find(r=>r.id===npc.id).meeting,null);
}));

test('持久化拒绝非法外观和玩家结构，不覆盖已有存档',()=>temporary(dir=>{
  const p=new Persistence(dir,safe),t=new Town(initialState(),{});create(t);p.save(t.state);const original=fs.readFileSync(p.file,'utf8');
  const changes=[s=>s.player.appearance.hairStyle='unknown',s=>s.player.appearance.skin='#fff',s=>s.player.id='resident-1',s=>s.player.isPlayer=false,s=>s.player.model.providerId='missing',s=>s.player.relationships.a=Infinity,s=>s.player.messages=[{role:'user',content:{}}],s=>s.residents.push(structuredClone(s.player))];
  for(const change of changes){const state=structuredClone(t.state);change(state);assert.throws(()=>p.save(state),/结构/);assert.equal(fs.readFileSync(p.file,'utf8'),original);}
}));

function mainHarness(dir) {
  const handlers=new Map();let town,window,fail=false;const store=new Persistence(dir,safe);
  class HarnessTown extends Town{constructor(...args){super(...args);town=this;}}
  class HarnessStore {load(){return null;}save(state){if(fail)throw new Error('磁盘写入失败');store.save(state);}}
  class BrowserWindow{constructor(){window=this;this.webContents={send(){},on(){},setWindowOpenHandler(){},getURL(){return '';}};}isDestroyed(){return false;}loadFile(){}}
  const electron={app:{isPackaged:false,setName(){},setPath(){},getPath:()=>dir,requestSingleInstanceLock:()=>true,whenReady:()=>({then:fn=>fn()}),on(){},quit(){}},BrowserWindow,ipcMain:{handle:(name,fn)=>handlers.set(name,fn)},Menu:{buildFromTemplate:x=>x,setApplicationMenu(){}},dialog:{showErrorBox(){},showSaveDialog:async()=>({canceled:true})},safeStorage:safe};
  const script=fs.readFileSync(path.join(__dirname,'../main/main.js'),'utf8');
  vm.runInNewContext(script,{require:id=>id==='electron'?electron:id==='./engine'?{Town:HarnessTown}:id==='./persistence'?{Persistence:HarnessStore}:id==='./llm'?{}:id.startsWith('./')?require(path.join(__dirname,'../main',id)):require(id),__dirname:path.join(__dirname,'../main'),process:{env:{PIXEL_TOWN_DATA_DIR:dir},defaultApp:true},setTimeout:()=>1,setInterval:()=>1,clearTimeout(){},clearInterval(){} });
  return {get town(){return town;},store,setFailure:value=>fail=value,invoke:(name,...args)=>handlers.get(name)({sender:window.webContents},...args)};
}

test('真实 IPC 玩家保存先落盘，失败不创建主角且不改变旧主角与控制',()=>temporary(async dir=>{
  const h=mainHarness(dir);h.setFailure(true);let result=await h.invoke('player:save',payload());assert.equal(result.ok,false);assert.equal(h.town.state.player,null);assert.equal(fs.existsSync(h.store.file),false);
  h.setFailure(false);result=await h.invoke('player:save',payload());assert.equal(result.ok,true);assert.equal(result.value,true);assert.equal(h.store.load().player.name,'旅人');
  await h.invoke('player:control');const player=h.town.state.player,before=structuredClone(h.town.state);h.setFailure(true);
  result=await h.invoke('player:save',payload('改名'));assert.equal(result.ok,false);assert.equal(h.town.state.player,player);assert.deepEqual(h.town.state,before);assert.equal(h.store.load().player.name,'旅人');
  result=await h.invoke('player:save',payload('改名',{skin:'bad'}));assert.equal(result.ok,false);assert.deepEqual(h.town.state,before);
  h.setFailure(false);result=await h.invoke('player:save',payload('改名'));assert.equal(result.ok,true);assert.equal(h.town.state.player,player);assert.equal(h.town.state.controlledId,'player');assert.equal(h.store.load().player.name,'改名');
}));

test('忙锁期间保存保持对象身份；对话继续写入当前玩家的记忆与关系',()=>temporary(async dir=>{
  const h=mainHarness(dir);await h.invoke('player:save',payload());const t=h.town,player=t.state.player,npc=t.state.residents.find(r=>r.enabled);
  t.state.providers.push({id:'fake',type:'openai',name:'测试',apiKey:'unit-secret'});npc.model.providerId='fake';let finish;
  t.llm={chatCompletion:()=>new Promise(resolve=>{finish=resolve;})};const talking=t.converse('player',npc.id);assert.equal(t.busy,true);assert.equal(player.dialoguePending,true);
  const result=await h.invoke('player:save',payload('仍然是我',{hat:'cap'}));assert.equal(result.ok,true);assert.equal(t.state.player,player);assert.equal(player.dialoguePending,true);
  t.control('player');t.setInput({x:1,y:0});const x=player.x;t.tick(.1);assert.equal(player.x,x);assert.equal(player.action,'chat');
  finish({text:JSON.stringify({action:'nod',thought:'一起逛逛应该不错',speech:'好呀，我们一起逛逛。'}),usage:{},latency:1});await talking;
  assert.equal(player.relationships[npc.id],2);assert.ok(player.memory.some(m=>m.includes('一起逛逛')));assert.equal(player.thinking,false);assert.equal(t.busy,false);assert.ok(!JSON.stringify(t.snapshot()).includes('unit-secret'));
}));

test('主角表情 IPC 可调用且错误返回保留原外观',()=>temporary(async dir=>{
  const h=mainHarness(dir);await h.invoke('player:save',payload());await h.invoke('player:control');
  const result=await h.invoke('player:expression','surprised');assert.equal(result.ok,true);assert.equal(result.value,true);assert.equal(h.town.state.player.appearance.expression,'surprised');assert.equal(h.town.state.controlledId,'player');
  const before=structuredClone(h.town.state),invalid=await h.invoke('player:expression','illegal');assert.equal(invalid.ok,false);assert.deepEqual(h.town.state,before);
  h.store.save(h.town.state);assert.equal(h.store.load().player.appearance.expression,'surprised');
}));
