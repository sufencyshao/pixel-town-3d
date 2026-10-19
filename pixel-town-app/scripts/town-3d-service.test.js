'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('fs'),path=require('path'),os=require('os');
const {Town3DService}=require('../main/town-3d-service');
const {initialState,catalog,petCatalog}=require('../main/catalog');
const capabilities=require('../design/town-ai-v9/capabilities.json').actors;
const id='03_barista_male';
const valid={version:1,thought:'先整理一下',speech:'',commands:[{type:'wait',seconds:1}]};
function setup(options={}){
 const state=initialState();state.providers.push({id:'mock',type:'openai',name:'Mock',apiKey:'SECRET_SENTINEL',baseUrl:'http://localhost',models:['mock']});const self=state.residents[2];self.model={providerId:'mock',model:'mock',temperature:.8,maxTokens:1024};self.memory=['只有林屿自己知道的记忆'];self.relationships[state.residents[3].id]=23;state.residents[3].memory=['他人私密记忆不能泄露'];
 const town={state,touch(){}};const scene={actors:capabilities.map(c=>({id:c.id,position:c.position,busy:false,action:'Idle'})),environment:{day:2,hour:10,weather:'sunny',season:'spring'}};
 const svc=new Town3DService({town,catalog:[...catalog,...petCatalog],capabilities,llm:{chatCompletion:async()=>({text:JSON.stringify(valid),usage:{promptTokens:10,completionTokens:20}})},saveBindings(){},...options});return {svc,town,scene,self};
}
test('context covers 45 people, current profile/schedule, genuine directional relations, private memories and 3D capabilities',()=>{
 const {svc,scene}=setup();const {data,system}=svc.context(id,scene);assert.equal(data.publicResidents.filter(c=>c.kind!=='animal'&&c.kind!=='scenery').length,45);assert.match(system,/手冲台/);assert.match(system,/Bip01_Head/);assert.match(system,/只有林屿自己知道/);assert.doesNotMatch(system,/他人私密记忆|SECRET_SENTINEL/);assert.equal(data.self.relationships[0].id,'04_baker_male');assert.equal(data.self.relationships[0].feeling,23);assert.equal(data.now.hour,10);assert.match(data.world.actualScene,/九区三维/);
});
test('3D identity stays attached to the resident instance after 2D appearance changes, and current preset supplies job steps',()=>{
 const {svc,scene,self}=setup();self.name='林屿新名字';self.catalogId='another-appearance';self.asset='another-appearance';self.presetId='preset_2';
 const context=svc.context(id,scene);assert.equal(context.data.self.name,'林屿新名字');assert.equal(context.data.capabilities.jobs[0].steps[0].name,'准备早餐饮品');assert.equal(svc.initial().bindings.find(b=>b.id===id).entityId,self.id);
});
test('provider changes invalidate pending responses and cancelled speech is never delivered',async()=>{
 let resolve;const {svc,scene,town}=setup({llm:{chatCompletion:()=>new Promise(r=>resolve=r)}});const pending=svc.decide(id,scene);town.state.providers.at(-1).baseUrl='http://changed';resolve({text:JSON.stringify(valid)});await assert.rejects(pending,/过期/);
 const second=setup({llm:{chatCompletion:async()=>({text:JSON.stringify({...valid,speech:'尚未说出口'})})}});const result=await second.svc.decide(id,second.scene);second.svc.receipt({...result,status:'cancelled',results:[],scene:second.scene});assert.equal(second.svc.runtime.history[0].speech,'');assert.equal(second.svc.runtime.actors['04_baker_male']?.heard,undefined);
});
test('successful decision and receipt create next-turn evidence, duplicate receipt is idempotent',async()=>{
 const {svc,scene}=setup();const result=await svc.decide(id,scene);const receipt={...result,status:'completed',results:[{index:0,status:'completed',elapsed:1}],scene};assert.equal(svc.receipt(receipt).saved,true);assert.equal(svc.receipt(receipt).duplicate,true);assert.equal(svc.context(id,scene).data.executionFeedback[0].status,'completed');assert.equal(svc.executions.size,0);
});
test('bad JSON, forbidden joints and unsuccessful API responses do not create executable plans',async()=>{
 for(const response of ['hello',JSON.stringify({...valid,commands:[{type:'pose',joints:{root:[0,0,0]},seconds:1}]})]){const {svc,scene}=setup({llm:{chatCompletion:async()=>({text:response})}});await assert.rejects(svc.decide(id,scene));assert.equal(svc.executions.size,0)}
 const {svc,scene}=setup({llm:{chatCompletion:async()=>{throw new Error('bad SECRET_SENTINEL')}}});await assert.rejects(svc.decide(id,scene),/已隐藏/);assert.doesNotMatch(JSON.stringify(svc.town.state.stats),/SECRET_SENTINEL/);
});
test('cancel and edited profile discard stale successful responses; budget prevents network calls',async()=>{
 for(const cancel of [true,false]){let resolve;const {svc,scene,self}=setup({llm:{chatCompletion:()=>new Promise(r=>resolve=r)}});const promise=svc.decide(id,scene);if(cancel)svc.cancel();else self.persona.background='已修改背景';resolve({text:JSON.stringify(valid)});await assert.rejects(promise);assert.equal(svc.executions.size,0)}
 const {svc,town,scene}=setup();town.state.dailyLimit=0;await assert.rejects(svc.decide(id,scene),/上限/);assert.equal(town.state.stats.length,0);
});
test('write failure preserves runtime, execution and API binding, then receipt can be retried',async()=>{
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'town-3d-test-'));const file=path.join(dir,'life.json');let broken=true;
 const {svc,scene,self}=setup({file,write:(...args)=>{if(broken)throw new Error('disk full');fs.writeFileSync(...args)},saveBindings:()=>{throw new Error('cannot save')}});
 try{const result=await svc.decide(id,scene);const receipt={...result,status:'completed',results:[{index:0,status:'completed',elapsed:1}],scene};assert.throws(()=>svc.receipt(receipt),/disk full/);assert.equal(svc.runtime.history.length,0);assert.equal(svc.executions.size,1);broken=false;svc.receipt(receipt);assert.equal(JSON.parse(fs.readFileSync(file)).history.length,1);const before=structuredClone(self.model);await assert.rejects(svc.bind(id,{providerId:'mock',model:'changed',temperature:1,maxTokens:1024}),/cannot save/);assert.deepEqual(self.model,before);}finally{fs.rmSync(dir,{recursive:true,force:true})}
});
test('work completion requires all timed stages; receipts cannot manufacture goods or relation changes',async()=>{
 const cap=capabilities.find(c=>c.id===id),job=cap.jobs[0];const {svc,scene,self}=setup({llm:{chatCompletion:async()=>({text:JSON.stringify({...valid,commands:[{type:'work',jobId:job.id}]})})}});const result=await svc.decide(id,scene);const receipt={...result,status:'completed',results:[{index:0,status:'completed',elapsed:30,stages:[]}],scene};assert.throws(()=>svc.receipt(receipt),/阶段/);receipt.results[0].stages=job.steps.map(s=>({name:s.name,seconds:s.seconds}));svc.receipt(receipt);assert.equal(svc.runtime.actors[id].workLog.length,1);assert.match(svc.runtime.actors[id].workLog[0].outcome,/没有制造/);assert.equal(self.relationships['resident-4'],23);
});
test('window interruption records uncertainty and restart restores only confirmed execution evidence',async()=>{
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'town-3d-restart-'));const file=path.join(dir,'life.json');try{const {svc,scene,town}=setup({file});await svc.decide(id,scene);svc.interrupt('关闭测试');assert.equal(svc.executions.size,0);assert.equal(svc.runtime.history[0].status,'interrupted');assert.equal(svc.runtime.actors[id]?.workLog,undefined);const reopened=new Town3DService({town,llm:{},catalog:[...catalog,...petCatalog],capabilities,file,saveBindings(){}});assert.equal(reopened.context(id,scene).data.executionFeedback[0].status,'interrupted');}finally{fs.rmSync(dir,{recursive:true,force:true})}
});
