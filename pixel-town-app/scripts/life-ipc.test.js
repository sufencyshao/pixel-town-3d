'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),vm=require('node:vm');
const {Town}=require('../main/engine');
const {Persistence}=require('../main/persistence');
const Life=require('../shared/life');
const {activeProfile}=require('../main/life-context');
const plain=x=>JSON.parse(JSON.stringify(x));
async function temporary(fn){const dir=fs.mkdtempSync(path.join(os.tmpdir(),'town-life-ipc-'));try{return await fn(dir);}finally{fs.rmSync(dir,{recursive:true,force:true});}}
function harness(dir){
  const handlers=new Map();let town,window,fail=false,calls=0,saveCount=0;
  const safe={isEncryptionAvailable:()=>true,encryptString:s=>Buffer.from(s),decryptString:b=>b.toString()},store=new Persistence(dir,safe);
  class AppTown extends Town{constructor(...args){super(...args);town=this;}}
  class Store{load(){return null;}save(state){saveCount++;if(fail)throw new Error('测试写盘失败');store.save(state);}}
  class Window{constructor(){window=this;this.webContents={send(){},on(){},setWindowOpenHandler(){},getURL(){return '';}};}isDestroyed(){return false;}loadFile(){}}
  const electron={app:{isPackaged:false,setName(){},setPath(){},getPath:()=>dir,requestSingleInstanceLock:()=>true,whenReady:()=>({then:fn=>fn()}),on(){},quit(){}},BrowserWindow:Window,ipcMain:{handle:(k,v)=>handlers.set(k,v)},Menu:{setApplicationMenu(){},buildFromTemplate:v=>v},safeStorage:safe,dialog:{showErrorBox(){throw new Error('Startup failed');},showSaveDialog:async()=>({canceled:false,filePath:path.join(dir,'exported-diary.md')})}};
  const network=()=>{calls++;throw new Error('No network expected');};
  vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../main/main.js'),'utf8'),{require:id=>id==='electron'?electron:id==='./engine'?{Town:AppTown}:id==='./persistence'?{Persistence:Store}:id==='./llm'?{chatCompletion:network,fetchModels:network,testProvider:network}:id.startsWith('./')?require(path.join(__dirname,'../main',id)):require(id),__dirname:path.join(__dirname,'../main'),process:{env:{PIXEL_TOWN_DATA_DIR:dir},defaultApp:true},structuredClone,setTimeout:()=>1,setInterval:()=>1,clearTimeout(){},clearInterval(){}});
  return {town,store,get calls(){return calls;},get saveCount(){return saveCount;},fail:v=>fail=v,invoke:(name,...args)=>handlers.get(name)({sender:window.webContents},...args)};
}

test('真实基础资料 IPC 先落盘再生效，失败或非法输入保留原资料',()=>temporary(async dir=>{
  const h=harness(dir),before=structuredClone(h.town.state),value={...Life.defaults,name:'溪岸小镇',facts:'公告：今天聊一聊各自喜欢的活动'};
  h.fail(true);assert.equal((await h.invoke('town:knowledge',value)).ok,false);assert.deepEqual(h.town.state,before);
  h.fail(false);const saved=await h.invoke('town:knowledge',value);assert.equal(saved.ok,true);assert.deepEqual(h.store.load().worldInfo,value);assert.deepEqual(plain(h.town.state.worldInfo),value);assert.equal(h.calls,0);
  const now=structuredClone(h.town.state);assert.equal((await h.invoke('town:knowledge',{...value,apiKey:'never-store'})).ok,false);assert.deepEqual(h.town.state,now);
}));

test('生活方向 IPC 保存失败不修改人物，成功保存保留身份和独立模型',()=>temporary(async dir=>{
  const h=harness(dir),r=h.town.active()[0],before=structuredClone(r),payload={aspiration:'慢慢结识喜欢植物的邻居',routine:'傍晚散步，精力不足时独处休息',resetGoal:false};
  h.fail(true);assert.equal((await h.invoke('town:life',r.id,payload)).ok,false);assert.deepEqual(r,before);
  h.fail(false);assert.equal((await h.invoke('town:life',r.id,payload)).ok,true);assert.equal(r.life.aspiration,payload.aspiration);assert.equal(r.life.custom,true);
  for(const key of ['name','persona','model','memory','relationships','enabled','asset'])assert.deepEqual(r[key],before[key]);assert.equal(h.store.load().residents.find(x=>x.id===r.id).life.aspiration,payload.aspiration);assert.equal(h.calls,0);
}));

test('日志 IPC 读取、按日导出及基础资料预览不触发 API 或泄露 Key',()=>temporary(async dir=>{
  const h=harness(dir),r=h.town.active()[0];h.town.state.providers.push({id:'secret',type:'openai',name:'测试 API',apiKey:'private-ipc-key'});r.model.providerId='secret';
  h.town.event(r.name+'观察到附近有人散步','life',[r.id]);
  const subjects=await h.invoke('journal:subjects');assert.equal(subjects.value.length,72);assert.ok(subjects.value.some(s=>s.id==='sky-sun'));
  const p=await h.invoke('journal:get',r.id,{day:1});assert.equal(p.ok,true);assert.ok(p.value.entries.some(e=>e.text.includes('附近有人散步')));
  const context=await h.invoke('town:context',r.id);assert.equal(context.ok,true);assert.equal(context.value.paidCall,false);assert.ok(context.value.system.includes('2D 像素'));assert.ok(!JSON.stringify(context).includes('private-ipc-key'));
  assert.equal((await h.invoke('journal:export',r.id,1)).value,true);assert.ok(fs.readFileSync(path.join(dir,'exported-diary.md'),'utf8').includes('附近有人散步'));assert.equal(h.calls,0);
}));

test('当前提示只带选中预设资料，保留源 Markdown 并尊重自定义档案',()=>{
  const town=new Town(null,{}),r=town.state.residents[0],raw=r.profileMd;
  assert.ok(raw.includes('## preset_2'));const selected=activeProfile(r);assert.ok(selected.includes('## preset_1'));assert.ok(!selected.includes('## preset_2'));assert.equal(r.profileMd,raw);
  town.update(r.id,{presetId:r.presets[1].id});const changed=activeProfile(r);assert.ok(changed.includes('## '+r.presets[1].id));assert.ok(!changed.includes('## preset_1'));assert.equal(r.profileMd,raw);
  r.profileMd='# 自己写的档案\n这条个人背景仍然有效';assert.equal(activeProfile(r),r.profileMd);
});
