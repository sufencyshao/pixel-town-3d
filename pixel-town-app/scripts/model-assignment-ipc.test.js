'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const vm=require('node:vm');
const {Town}=require('../main/engine');
const {Persistence}=require('../main/persistence');
const appearance=require('../shared/appearance');

const temporary=fn=>{
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'town-model-assignment-ipc-'));
  return Promise.resolve().then(()=>fn(dir)).finally(()=>fs.rmSync(dir,{recursive:true,force:true}));
};
const plain=value=>JSON.parse(JSON.stringify(value));
const configs=[
  {providerId:'unit-a',model:'model-a',temperature:.35,maxTokens:512},
  {providerId:'unit-b',model:'model-b',temperature:1.1,maxTokens:1024}
];

function harness(dir) {
  const handlers=new Map(),snapshots=[];let town,window,fail=false,saveCount=0,onSave=()=>{},networkCalls=0;
  const safe={isEncryptionAvailable:()=>true,encryptString:s=>Buffer.from(s),decryptString:b=>b.toString()};
  const store=new Persistence(dir,safe);
  class HarnessTown extends Town {constructor(...args){super(...args);town=this;}}
  class HarnessStore {
    load(){return null;}
    save(candidate){saveCount++;onSave(candidate);if(fail)throw new Error('测试磁盘写入失败');store.save(candidate);}
  }
  class BrowserWindow {
    constructor(){window=this;this.webContents={send:(_,snapshot)=>snapshots.push(snapshot),on(){},setWindowOpenHandler(){},getURL(){return '';}};}
    isDestroyed(){return false;}loadFile(){}
  }
  const electron={app:{isPackaged:false,setName(){},setPath(){},getPath:()=>dir,requestSingleInstanceLock:()=>true,whenReady:()=>({then:fn=>fn()}),on(){},quit(){}},BrowserWindow,ipcMain:{handle:(name,fn)=>handlers.set(name,fn)},Menu:{buildFromTemplate:x=>x,setApplicationMenu(){}},dialog:{showErrorBox(){throw new Error('Unexpected startup failure');}},safeStorage:safe};
  const network=()=>{networkCalls++;throw new Error('No API request allowed');};
  const code=fs.readFileSync(path.join(__dirname,'../main/main.js'),'utf8');
  vm.runInNewContext(code,{require:id=>id==='electron'?electron:id==='./engine'?{Town:HarnessTown}:id==='./persistence'?{Persistence:HarnessStore}:id==='./llm'?{chatCompletion:network,fetchModels:network,testProvider:network}:id.startsWith('./')?require(path.join(__dirname,'../main',id)):require(id),__dirname:path.join(__dirname,'../main'),process:{env:{PIXEL_TOWN_DATA_DIR:dir},defaultApp:true},structuredClone,setTimeout:()=>1,setInterval:()=>1,clearTimeout(){},clearInterval(){}});
  town.state.providers.push(
    {id:'unit-a',name:'测试 API A',type:'openai',baseUrl:'https://unit.invalid/v1',apiKey:'test-only-secret-a',models:['model-a']},
    {id:'unit-b',name:'测试 API B',type:'anthropic',baseUrl:'https://unit.invalid/v1',apiKey:'test-only-secret-b',models:['model-b']}
  );
  town.state.player=town.preparePlayer({name:'测试旅人',appearance:{...appearance.defaults}});
  return {town,store,handlers,snapshots,get saveCount(){return saveCount;},get networkCalls(){return networkCalls;},setFailure:value=>{fail=value;},onSave:fn=>{onSave=fn;},invoke:(name,...args)=>handlers.get(name)({sender:window.webContents},...args),invalidSender:(name,...args)=>handlers.get(name)({sender:{}},...args)};
}

test('按需复制原应用 API，候选列表不泄露密钥；只复制选中项且保存失败可回退',()=>temporary(async dir=>{
  const original=path.join(dir,'ai-friends-chat');fs.mkdirSync(original);
  const file=path.join(original,'settings.json');
  const settings={providers:[{id:'demo',type:'demo',apiKey:''},{id:'legacy-a',name:'旧 API A',type:'openai',baseUrl:'https://a.invalid',models:['a-model'],apiKey:'private-legacy-key-a'},{id:'legacy-b',name:'旧 API B',type:'anthropic',baseUrl:'https://b.invalid',models:['b-model'],apiKey:'private-legacy-key-b'}]};
  fs.writeFileSync(file,JSON.stringify(settings));const source=fs.readFileSync(file,'utf8'),h=harness(dir);
  const options=await h.invoke('legacy:provider-options');assert.equal(options.ok,true);assert.equal(options.value.length,2);assert.equal(h.saveCount,0);
  assert.ok(!JSON.stringify(options).includes('private-legacy-key'));assert.ok(!JSON.stringify(options).includes('apiKey'));
  for(const ids of [[],['missing'],['legacy-a','legacy-a'],{}])assert.equal((await h.invoke('legacy:providers',ids)).ok,false);
  assert.equal(h.saveCount,0);const copied=await h.invoke('legacy:providers',['legacy-a']);assert.equal(copied.ok,true);assert.equal(copied.value,1);
  assert.ok(h.town.state.providers.some(p=>p.id==='legacy-legacy-a'));assert.ok(!h.town.state.providers.some(p=>p.id==='legacy-legacy-b'));
  assert.equal(h.store.load().providers.at(-1).apiKey,'private-legacy-key-a');assert.ok(!fs.readFileSync(h.store.file,'utf8').includes('private-legacy-key'));
  const before=structuredClone(h.town.state.providers);h.setFailure(true);assert.equal((await h.invoke('legacy:providers',['legacy-b'])).ok,false);assert.deepEqual(h.town.state.providers,before);
  assert.equal(fs.readFileSync(file,'utf8'),source);assert.equal(h.networkCalls,0);
}));

test('真实批量 IPC 一次保存两个 API 配置并保持居民、动物、主角和运行状态',()=>temporary(async dir=>{
  const h=harness(dir),t=h.town,recipients=[t.state.residents[0],t.state.residents[1],t.state.pets[0]];
  assert.ok(recipients.every(Boolean));
  recipients[0].memory=['保留记忆'];recipients[0].messages=[{role:'user',content:'原有聊天',time:1}];recipients[0].relationships[recipients[1].id]=15;
  recipients[0].target={x:800,y:700};recipients[0].moving=true;recipients[0].thinking=true;
  t.state.running=false;t.state.autonomous=true;t.state.controlledId='player';t.input={x:1,y:0};
  const before=structuredClone(t.state),revision=t.revision,providerRefs=t.state.providers.slice(),entityRefs=[...t.state.residents,...t.state.pets],player=t.state.player;
  const request={targets:recipients.map(r=>r.id).reverse(),configs,strategy:'round-robin',preserveParameters:false};
  h.onSave(candidate=>{
    assert.deepEqual(t.state,before);assert.equal(t.revision,revision);
    assert.notEqual(candidate,t.state);assert.deepEqual(candidate.providers,before.providers);
    assert.equal(candidate.events[0].kind,'system');assert.equal(candidate.events.length,before.events.length+1);
    assert.deepEqual(candidate.residents[0].model,configs[0]);assert.deepEqual(candidate.residents[1].model,configs[1]);assert.deepEqual(candidate.pets[0].model,configs[0]);
  });
  const result=await h.invoke('town:models:assign',request);
  assert.deepEqual(plain(result),{ok:true,value:{assigned:3,counts:[{providerId:'unit-a',count:2},{providerId:'unit-b',count:1}],strategy:'round-robin'}});
  assert.equal(h.saveCount,1);assert.equal(t.revision,revision+1);assert.equal(t.state.player,player);assert.deepEqual(t.state.player,before.player);
  assert.equal(t.state.providers[1],providerRefs[1]);assert.equal(t.state.providers[2],providerRefs[2]);assert.deepEqual(t.state.providers,before.providers);
  const expected=structuredClone(before);expected.residents[0].model={...configs[0]};expected.residents[1].model={...configs[1]};expected.pets[0].model={...configs[0]};expected.events=t.state.events;
  assert.deepEqual(t.state,expected);assert.deepEqual(t.input,{x:1,y:0});assert.equal(t.busy,false);
  [...t.state.residents,...t.state.pets].forEach((r,i)=>assert.equal(r,entityRefs[i]));
  assert.deepEqual(t.state.events[0].ids,recipients.map(r=>r.id));assert.match(t.state.events[0].text,/3.*批量分配/);
  const restored=h.store.load();assert.deepEqual(restored.residents[0].model,configs[0]);assert.deepEqual(restored.pets[0].model,configs[0]);assert.equal(restored.providers[1].apiKey,'test-only-secret-a');
  for(const key of ['test-only-secret-a','test-only-secret-b']) {
    assert.ok(!JSON.stringify(result).includes(key));assert.ok(!JSON.stringify(h.snapshots).includes(key));assert.ok(!JSON.stringify(recipients).includes(key));assert.ok(!fs.readFileSync(h.store.file,'utf8').includes(key));
  }
  assert.equal(h.networkCalls,0);
}));

test('单 API 分配默认保留各自参数，分组分配支持连续均分',()=>temporary(async dir=>{
  const h=harness(dir),r=h.town.state.residents.slice(0,5);
  r.forEach((entity,i)=>Object.assign(entity.model,{temperature:i*.2,maxTokens:100+i*10}));
  const result=await h.invoke('town:models:assign',{targets:r.map(x=>x.id),configs:[configs[0]],strategy:'round-robin'});
  assert.equal(result.ok,true);r.forEach((entity,i)=>assert.deepEqual(entity.model,{providerId:'unit-a',model:'model-a',temperature:i*.2,maxTokens:100+i*10}));
  const grouped=await h.invoke('town:models:assign',{targets:r.map(x=>x.id),configs,strategy:'grouped',preserveParameters:false});
  assert.equal(grouped.ok,true);assert.deepEqual(r.map(x=>x.model.providerId),['unit-a','unit-a','unit-a','unit-b','unit-b']);
  assert.deepEqual(plain(grouped.value.counts),[{providerId:'unit-a',count:3},{providerId:'unit-b',count:2}]);assert.equal(h.saveCount,2);assert.equal(h.networkCalls,0);
}));

test('非法批量配置整批拒绝，主角、缺失目标、重复目标和密钥字段均不会保存',()=>temporary(async dir=>{
  const h=harness(dir),id=h.town.state.residents[0].id,base={targets:[id],configs:[configs[0]],strategy:'round-robin',preserveParameters:false};
  const before=structuredClone(h.town.state),revision=h.town.revision;
  const requests=[null,{...base,targets:[id,'player']},{...base,targets:[id,'missing']},{...base,targets:[id,id]},{...base,configs:[configs[0],{...configs[1],providerId:'missing'}]},{...base,configs:[{...configs[0],temperature:9}]},{...base,configs:[{...configs[0],apiKey:'reject-key'}]},{...base,configs:[{...configs[0],model:''}]}];
  for(const request of requests){const result=await h.invoke('town:models:assign',request);assert.equal(result.ok,false);assert.deepEqual(h.town.state,before);assert.equal(h.town.revision,revision);assert.ok(!JSON.stringify(result).includes('reject-key'));}
  assert.equal(h.saveCount,0);assert.equal(fs.existsSync(h.store.file),false);assert.equal(h.networkCalls,0);
}));

test('候选存档写入失败不更新任何对象、参数、事件或已有磁盘档案',()=>temporary(async dir=>{
  const h=harness(dir),t=h.town;h.store.save(t.state);const diskBefore=fs.readFileSync(h.store.file,'utf8'),before=structuredClone(t.state),revision=t.revision;
  const resident=t.state.residents[0],model=resident.model,events=t.state.events,pet=t.state.pets[0];h.setFailure(true);
  const result=await h.invoke('town:models:assign',{targets:[resident.id,pet.id],configs,strategy:'round-robin',preserveParameters:false});
  assert.equal(result.ok,false);assert.match(result.error,/磁盘写入失败/);assert.equal(h.saveCount,1);assert.deepEqual(t.state,before);assert.equal(t.revision,revision);
  assert.equal(t.state.residents[0],resident);assert.equal(resident.model,model);assert.equal(t.state.pets[0],pet);assert.equal(t.state.events,events);assert.equal(fs.readFileSync(h.store.file,'utf8'),diskBefore);assert.equal(h.networkCalls,0);
}));

test('忙锁拒绝分配且保持状态；IPC 限定当前窗口，preload 放行此接口并传递错误',()=>temporary(async dir=>{
  const h=harness(dir),payload={targets:[h.town.state.residents[0].id],configs:[configs[0]],strategy:'round-robin',preserveParameters:false};
  h.town.busy=true;const before=structuredClone(h.town.state),revision=h.town.revision;
  const rejected=await h.invoke('town:models:assign',payload);assert.equal(rejected.ok,false);assert.match(rejected.error,/正在进行/);assert.deepEqual(h.town.state,before);assert.equal(h.town.revision,revision);assert.equal(h.saveCount,0);
  await assert.rejects(h.invalidSender('town:models:assign',payload),/无效窗口/);
  let api;const calls=[];
  const preload=fs.readFileSync(path.join(__dirname,'../main/preload.js'),'utf8');
  vm.runInNewContext(preload,{require:id=>{assert.equal(id,'electron');return {contextBridge:{exposeInMainWorld:(name,value)=>{assert.equal(name,'townAPI');api=value;}},ipcRenderer:{invoke:(name,...args)=>{calls.push({name,args});return h.invoke(name,...args);},on(){},removeListener(){}}};}});
  await assert.rejects(api.invoke('town:models:assign',payload),/正在进行/);h.town.busy=false;
  const success=await api.invoke('town:models:assign',payload);assert.equal(success.assigned,1);assert.equal(calls[0].name,'town:models:assign');assert.equal(calls[0].args[0],payload);
  await assert.rejects(api.invoke('town:unsupported'),/不支持/);assert.equal(calls.length,2);assert.equal(h.networkCalls,0);
}));
