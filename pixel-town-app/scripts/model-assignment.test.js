'use strict';
const test=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');const vm=require('node:vm');
const {initialState}=require('../main/catalog');const {Town}=require('../main/engine');const ModelAssignment=require('../shared/model-assignment');
const fixture=()=>{const s=new Town(initialState(),{}).state;s.providers.push({id:'a',name:'API A',type:'openai',apiKey:'fake-secret-a',models:['model-a']},{id:'b',name:'API B',type:'anthropic',apiKey:'fake-secret-b',models:['model-b']});return s;};
const config=(id,model)=>({providerId:id,model,temperature:.4,maxTokens:1024});
test('one API binds many characters without copying keys or changing anyone else',()=>{
 const s=fixture(),before=structuredClone(s),ids=s.residents.slice(0,6).map(r=>r.id);
 const result=ModelAssignment.plan(s,{targets:ids,configs:[config('a','model-a')]});
 assert.equal(result.assignments.length,6);assert.deepEqual(result.counts,[{providerId:'a',count:6}]);
 for(const a of result.assignments){assert.equal(a.model.providerId,'a');assert.equal(a.model.model,'model-a');assert.equal(a.model.temperature,s.residents.find(r=>r.id===a.id).model.temperature);}
 assert.deepEqual(s,before);assert.ok(!JSON.stringify(result).includes('fake-secret'));assert.ok(!JSON.stringify(result).includes('apiKey'));
});
test('several API configurations divide targets consistently by list order, including animals and inactive residents',()=>{
 const s=fixture(),people=[...s.residents.slice(0,5),s.pets[0]],targets=people.map(r=>r.id).reverse(),configs=[config('a','model-a'),config('b','model-b')];
 const round=ModelAssignment.plan(s,{targets,configs,strategy:'round-robin',preserveParameters:false});
 assert.deepEqual(round.assignments.map(a=>a.model.providerId),['a','b','a','b','a','b']);assert.deepEqual(round.assignments.map(a=>a.id),people.map(r=>r.id));
 assert.ok(round.assignments.every(a=>a.model.temperature===.4&&a.model.maxTokens===1024));
 const group=ModelAssignment.plan(s,{targets,configs,strategy:'grouped'});assert.deepEqual(group.assignments.map(a=>a.model.providerId),['a','a','a','b','b','b']);
 const few=ModelAssignment.plan(s,{targets:[s.residents[0].id],configs,strategy:'grouped'});assert.deepEqual(few.counts,[{providerId:'a',count:1},{providerId:'b',count:0}]);
});
test('all validation completes without mutation and player cannot be included',()=>{
 const s=fixture(),before=structuredClone(s),id=s.residents[0].id,base={targets:[id],configs:[config('a','model-a')],preserveParameters:false};
 const invalid=[null,[],{...base,targets:[]},{...base,targets:[id,id]},{...base,targets:['missing']},{...base,targets:['player']},{...base,configs:[]},{...base,configs:[config('missing','x')]},{...base,configs:[config('a',' ')]},{...base,configs:[config('a','x'),config('a','y')]},{...base,configs:[{...config('a','x'),apiKey:'secret'}]},{...base,preserveParameters:'true'},{...base,strategy:'random'},{...base,configs:[{...config('a','x'),temperature:NaN}]},{...base,configs:[{...config('a','x'),maxTokens:64.5}]},{...base,configs:[{...config('a','x'),temperature:3}]},{...base,configs:[{...config('a','x'),maxTokens:100000}]}];
 for(const value of invalid){assert.throws(()=>ModelAssignment.plan(s,value));assert.deepEqual(s,before);}
});
test('local rules and browser preview use exactly the same planner',()=>{
 const s=fixture(),payload={targets:[s.residents[0].id],configs:[config('demo','')],preserveParameters:true};
 assert.equal(ModelAssignment.plan(s,payload).assignments[0].model.model,'demo');
 const context=vm.createContext({stateJSON:JSON.stringify(s),payloadJSON:JSON.stringify(payload)});vm.runInContext(fs.readFileSync(require.resolve('../shared/model-assignment'),'utf8'),context);
 const fromBrowser=JSON.parse(vm.runInContext('JSON.stringify(ModelAssignment.plan(JSON.parse(stateJSON),JSON.parse(payloadJSON)))',context));
 assert.deepEqual(fromBrowser,ModelAssignment.plan(s,payload));
});
