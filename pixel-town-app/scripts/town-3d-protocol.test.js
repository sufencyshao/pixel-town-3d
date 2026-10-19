'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const Protocol=require('../shared/town-3d-protocol');
const caps=require('../design/town-ai-v9/capabilities.json').actors;
const human=caps.find(c=>c.id==='03_barista_male');
const plan=commands=>({version:1,thought:'准备好好工作',speech:'',commands});
test('3D protocol uses actual clips, semantic joint limits and individual jobs',()=>{
  assert.equal(Protocol.parse(plan([{type:'pose',joints:{head:[10,20,0]},seconds:2}]),human).commands[0].type,'pose');
  assert.equal(Protocol.parse(plan([{type:'work',jobId:human.jobs[0].id}]),human).commands[0].jobId,human.jobs[0].id);
  for(const commands of [[{type:'preset',clip:'invented',seconds:2}],[{type:'preset',clip:'Walk',seconds:2}],[{type:'pose',joints:{head:[0,99,0]},seconds:2}],[{type:'pose',joints:{pelvis:[0,0,0]},seconds:2}],[{type:'pose',joints:{head:[NaN,0,0]},seconds:2}],[{type:'work',jobId:'daily:someone-else'}],[{type:'move',destination:{x:0,z:Infinity},gait:'walk'}],[{type:'eval',code:'anything'}]])assert.throws(()=>Protocol.parse(plan(commands),human));
});
test('animals/child cannot borrow adult speech, locomotion or joints',()=>{
  const dog=caps.find(c=>c.id==='07_dog_shiba'),child=caps.find(c=>c.id==='kanna');
  assert.throws(()=>Protocol.parse(plan([{type:'move',destination:{x:1,z:1},gait:'walk'}]),dog));
  assert.throws(()=>Protocol.parse({...plan([{type:'wait',seconds:1}]),speech:'我是人类'},dog));
  assert.throws(()=>Protocol.parse(plan([{type:'preset',clip:'Dance',seconds:2}]),child));
  assert.equal(caps.filter(c=>c.jobs.length).length,40);assert.equal(caps.length,61);
});
test('public navigation respects step heights, walls, occupied destination and unreachable regions',async()=>{
  const fs=require('fs');const source=fs.readFileSync(require('path').join(__dirname,'../design/town-ai-v9/src/navigation.js'),'utf8');
  const {PublicNavigation}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
  const g=new PublicNavigation({cols:4,rows:3,origin:[0,0],spacing:.5,cells:[0,1,2,3,4,7,8,9,10,11],heights:{},maxStep:.13});
  const route=g.path([0,0,0],[1.5,0,1]);assert.equal(route.length,6);assert.throws(()=>g.path([0,0,0],[.5,0,.5]));assert.throws(()=>g.path([0,0,0],[1.5,0,1],new Set([11])));
  g.heights[1]=1;g.valid.delete(4);assert.throws(()=>g.path([0,0,0],[1.5,0,1]));
});
