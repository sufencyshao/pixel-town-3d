'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const Time=require('../shared/world-time');
const Regions=require('../shared/sprite-regions');
const {Town}=require('../main/engine'),{initialState,catalog}=require('../main/catalog');

test('sunrise, noon, sunset and moon positions follow the same cyclic game clock',()=>{
  const dawn=Time.sample(360),noon=Time.sample(720),dusk=Time.sample(1080),midnight=Time.sample(1440);
  assert.equal(dawn.label,'日出');assert.equal(dawn.sun.visible,true);assert.equal(dawn.sun.x,8);
  assert.equal(noon.label,'白昼');assert.equal(noon.sun.x,50);assert.equal(noon.sun.y,52);
  assert.equal(dusk.label,'日落');assert.equal(dusk.sun.visible,false);assert.equal(dusk.moon.visible,true);assert.equal(dusk.moon.x,8);
  assert.equal(midnight.label,'夜晚');assert.equal(midnight.moon.x,50);assert.equal(midnight.moon.y,52);assert.equal(midnight.day,2);
  assert.equal(Time.format(1505),'01:05');assert.equal(Time.sample(1440).sky,Time.sample(0).sky);
  for(let m=0;m<1440;m+=5){const e=Time.sample(m);assert.equal(Number(e.sun.visible)+Number(e.moon.visible),1);assert.ok(e.spriteBrightness>=.78&&e.spriteBrightness<=1);}
});
test('dawn and dusk lighting is continuous, including midnight and day rollover',()=>{
  for(const m of [0,300,330,360,420,720,1020,1080,1140,1260,1440]){
    const a=Time.sample(m-.001),b=Time.sample(m+.001);
    assert.ok(Math.abs(a.night-b.night)<.0001);
    assert.equal(a.sky,b.sky);assert.equal(a.ground,b.ground);
  }
  for(const clock of [NaN,Infinity,'360',undefined])assert.throws(()=>Time.sample(clock));
});
test('time choices always advance to the next occurrence and reject invalid input atomically',()=>{
  assert.equal(Time.next(540,360),1800);assert.equal(Time.next(540,720),720);assert.equal(Time.next(720,720),2160);
  const town=new Town(initialState(),{});town.configure({running:false});
  const r=town.active()[0],before={x:r.x,y:r.y,model:structuredClone(r.model),running:town.state.running};
  r.bubble='旧对白';r.bubbleUntil=550;r.thought='旧心声';r.thoughtUntil=550;
  const version=r.intentVersion;town.advanceTo(1080);
  assert.equal(town.state.clock,1080);assert.equal(r.bubble,'');assert.equal(r.thought,'');assert.ok(r.intentVersion>version);
  assert.deepEqual({x:r.x,y:r.y,model:r.model,running:town.state.running},before);assert.equal(town.state.stats.length,0);
  for(const value of [-1,1440,1.2,'360',NaN,null]){const snapshot=town.snapshot();assert.throws(()=>town.advanceTo(value));assert.deepEqual(town.snapshot(),snapshot);}
});
test('pause, manual steps and speed affect the environment exactly as the game clock advances',()=>{
  const town=new Town(initialState(),{});town.state.clock=1079.5;town.configure({running:false,speed:4});
  town.tick(.5);assert.equal(town.state.clock,1079.5);assert.equal(Time.sample(town.state.clock).sun.visible,true);
  town.tick(.125,true);assert.equal(town.state.clock,1080);assert.equal(Time.sample(town.state.clock).moon.visible,true);
  town.configure({running:true,speed:2});town.tick(.25);assert.equal(town.state.clock,1080.5);
});
test('API context includes the actual saved time and current light phase',()=>{
  const town=new Town(initialState(),{});town.state.clock=22*60;
  assert.match(town.prompt(town.active()[0]),/22:00.*夜晚/);
  assert.match(town.prompt(town.state.pets[0]),/22:00.*夜晚/);
});
test('foreground masks preserve every body pixel, remove only the reviewed region and never mutate a source',()=>{
  const data=new Uint8ClampedArray(16*12*4);for(let y=2;y<10;y++)for(let x=5;x<11;x++)data.set([80,120,40,255],(y*16+x)*4);
  data.set([19,20,21,255],(4*16+1)*4);const original=data.slice();
  const source={width:16,height:12,data};const result=Regions.pixels(source,[4,0,16,12],-1);
  for(let y=2;y<10;y++)for(let x=4;x<10;x++)assert.deepEqual(Array.from(result.data.slice((y*16+x)*4,(y*16+x)*4+4)),[80,120,40,255]);
  assert.equal(result.data[(4*16)*4+3],0);assert.deepEqual(source.data,original);
  assert.equal(Regions.inset([64,0,256,256]),'inset(0% 0% 0% 25%)');assert.equal(Regions.valid([256,0,64,256]),false);
});
test('actual catalog supplies the verified librarian correction to every runtime consumer',()=>{
  const knowledge=catalog.find(c=>c.asset==='16_librarian_female');
  assert.ok(knowledge.animation.animations.walk_right.visibleBounds.every(b=>Regions.valid(b)));
  assert.equal(knowledge.animation.animations.walk_right.offsetX,-38);assert.deepEqual(knowledge.animation.frameBounds['6'],[0,0,143,256]);
});
test('advancing time cancels a pending decision and rejects its old-time expression',async()=>{
  let respond,signal;
  const town=new Town(initialState(),{chatCompletion:options=>{signal=options.signal;return new Promise(resolve=>respond=resolve);}});
  const r=town.active()[0];town.state.providers.push({id:'time-test',type:'openai',name:'test',models:['test']});r.model={providerId:'time-test',model:'test',temperature:.5,maxTokens:500};
  const task=town.decide(r.id);await new Promise(resolve=>setImmediate(resolve));
  town.advanceTo(1320);assert.equal(signal.aborted,true);
  respond({text:JSON.stringify({action:'nod',thought:'这是旧时刻的想法。',speech:''}),usage:{prompt_tokens:1,completion_tokens:1},latency:1});
  assert.deepEqual(await task,{discarded:true});assert.notEqual(r.action,'nod');assert.equal(r.thought,'');assert.equal(town.state.stats.at(-1).applied,false);
});
