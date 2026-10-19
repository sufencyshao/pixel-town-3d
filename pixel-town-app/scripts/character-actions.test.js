'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const {Town}=require('../main/engine');
const {initialState,catalog}=require('../main/catalog');
const actions=require('../shared/actions');
const animation=require('../renderer/animation');
const appearance=require('../shared/appearance');
function town(){const t=new Town(initialState(),{});t.setRoster([t.active()[0].id]);return t;}

test('40 human catalogs ship all three daily clips, including the latest Wen Dou correction',()=>{
  const humans=catalog.filter(c=>c.kind==='human');assert.equal(humans.length,40);
  const source=path.resolve(__dirname,'../../pixel_town_assets');
  for(const r of humans){
    assert.equal(r.animation.frameWidth,256);assert.equal(r.animation.frameHeight,256);assert.equal(Object.keys(r.animation.animations).length,15);
    for(const key of ['nod','shake_head','chat']){
      const clip=r.animation.animations[key];assert.ok(clip,key);const relative=r.assetFolder+'/'+clip.atlas;
      const png=fs.readFileSync(path.join(__dirname,'../assets',relative));
      assert.equal(png.readUInt32BE(16),clip.frames*256);assert.equal(png.readUInt32BE(20),256);
      if(fs.existsSync(source))assert.equal(crypto.createHash('sha256').update(png).digest('hex'),crypto.createHash('sha256').update(fs.readFileSync(path.join(source,relative))).digest('hex'),relative);
    }
    const shake=r.animation.animations.shake_head;
    assert.equal(shake.frames,25);assert.equal(shake.loop,false);assert.deepEqual(shake.durations,[...Array(24).fill(30),480]);
    assert.equal(shake.headTurn.revision,'20261003-refusal-anatomy-v7');assert.equal(shake.headTurn.shakeCount,2);
  }
  assert.equal(humans.find(c=>c.asset==='36_barista_female').animation.animations.shake_head.headTurn.roleRevision,'20261003-wendou-joint-v1');
});

test('refusal keeps its 30ms phases and 480ms neutral hold; nod never restarts its cycle',()=>{
  const r={...catalog.find(c=>c.kind==='human'),action:'shake_head'};
  for(const [ms,expected]of [[0,0],[29,0],[30,1],[89,2],[90,3],[180,6],[360,12],[540,18],[719,23],[720,24],[1199,24],[1200,24],[9000,24]])assert.equal(animation.sample(r,ms).frame,expected);
  r.action='nod';assert.equal(animation.sample(r,1439).frame,15);assert.equal(animation.sample(r,1440).frame,15);assert.equal(animation.sample(r,9000).frame,15);
  r.action='chat';assert.equal(animation.sample(r,1440).frame,0);assert.equal(actions.gestureDuration('shake_head',r.animation),1200);
});

test('a gesture cancels movement, repeats from a new version, pauses, and returns to idle on time',()=>{
  const t=town(),r=t.active()[0];t.move(r.id,{x:1200,y:800});t.act(r.id,'shake_head');assert.equal(r.target,null);assert.equal(r.remaining,1.2);
  const version=r.actionVersion;t.tick(.2);t.act(r.id,'shake_head');assert.equal(r.actionVersion,version+1);assert.equal(r.remaining,1.2);
  t.configure({running:false});t.tick(4);assert.equal(r.remaining,1.2);t.configure({running:true});
  t.tick(.72);assert.equal(r.action,'shake_head');t.tick(.48);assert.equal(r.action,'idle');assert.equal(r.remaining,10);
  t.act(r.id,'nod');t.configure({speed:4});t.tick(.35);assert.equal(r.action,'nod');t.tick(.01);assert.equal(r.action,'idle');assert.equal(t.state.stats.length,0);
});

test('preset player uses the same gesture duration, keeps control, and keyboard movement interrupts',()=>{
  const t=town();t.state.player=t.preparePlayer({name:'动作测试主角',appearance:appearance.normalize({styleMode:'preset',avatarPreset:'01_hero_male'})});t.control('player');
  const r=t.state.player;t.act('player','shake_head');assert.equal(t.state.controlledId,'player');t.tick(1.2);assert.equal(r.action,'idle');
  t.act('player','nod');t.setInput({x:1,y:0});t.tick(.1);assert.equal(r.action,'walk');assert.equal(r.moving,true);
  t.setInput({x:0,y:0});t.tick(.1);assert.equal(r.action,'idle');
  r.appearance.styleMode='custom';assert.throws(()=>t.act('player','shake_head'),/尚无此动作/);
  const mini=t.state.residents.find(c=>c.kind==='codexmini');mini.enabled=true;assert.throws(()=>t.act(mini.id,'nod'),/尚无此动作/);
});

test('model-selected refusal is available in the prompt and finishes after the real clip duration',async()=>{
  const t=town(),r=t.active()[0];t.state.providers.push({id:'mock',type:'openai'});r.model.providerId='mock';
  t.llm={chatCompletion:async options=>{assert.match(options.system,/nod\|shake_head/);return{text:'{"action":"shake_head","thought":"暂时不需要"}',usage:{},latency:1};}};
  await t.decide(r.id);assert.equal(r.action,'shake_head');assert.equal(r.remaining,1.2);assert.equal(r.thinking,false);t.tick(1.2);assert.equal(r.action,'idle');
});

test('existing saves refresh animation metadata while retaining edited people and model bindings',()=>{
  const old=initialState(),r=old.residents[0];r.name='原来名字';r.persona.personality='原来性格';r.memory=['原来记忆'];r.messages=[{role:'user',content:'旧对话'}];r.model.temperature=.3;
  for(const a of ['nod','shake_head','chat'])delete r.animation.animations[a];
  const t=new Town(old,{}),loaded=t.resident(r.id);assert.ok(loaded.animation.animations.shake_head);assert.equal(loaded.name,'原来名字');assert.equal(loaded.persona.personality,'原来性格');assert.deepEqual(loaded.memory,['原来记忆']);assert.deepEqual(loaded.messages,[{role:'user',content:'旧对话'}]);assert.equal(loaded.model.temperature,.3);
});
