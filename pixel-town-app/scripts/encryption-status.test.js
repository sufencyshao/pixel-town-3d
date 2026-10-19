'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');const path=require('node:path');const os=require('node:os');const vm=require('node:vm');
const {Persistence}=require('../main/persistence');const {initialState}=require('../main/catalog');

test('本地启动、主角存档与 town:get 不提前查询系统钥匙串',async()=>{
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'town-encryption-status-'));let queries=0;
  const safe={isEncryptionAvailable(){queries++;throw new Error('No eager keychain query allowed');}};
  try{
    const p=new Persistence(dir,safe);assert.equal(p.encryptionAvailable,null);p.save(initialState());assert.ok(p.load());assert.equal(queries,0);
    const handlers=new Map();let window;
    class BrowserWindow{constructor(){window=this;this.webContents={send(){},on(){},setWindowOpenHandler(){},getURL(){return ''}};}loadFile(){}isDestroyed(){return false;}}
    const electron={app:{isPackaged:true,setName(){},setPath(){},getPath:()=>dir,requestSingleInstanceLock:()=>true,whenReady:()=>({then:fn=>fn()}),on(){},quit(){}},BrowserWindow,ipcMain:{handle:(n,f)=>handlers.set(n,f)},Menu:{buildFromTemplate:x=>x,setApplicationMenu(){}},dialog:{showErrorBox(){throw new Error('Unexpected startup failure')}},safeStorage:safe};
    const code=fs.readFileSync(path.join(__dirname,'../main/main.js'),'utf8');
    vm.runInNewContext(code,{__dirname:path.join(__dirname,'../main'),process:{env:{PIXEL_TOWN_DATA_DIR:dir}},require:id=>id==='electron'?electron:id==='./llm'?{}:id.startsWith('./')?require(path.join(__dirname,'../main',id)):require(id),setTimeout:()=>1,setInterval:()=>1,clearTimeout(){},clearInterval(){}});
    const result=await handlers.get('town:get')({sender:window.webContents});assert.equal(result.ok,true);assert.equal(result.value.encrypted,null);assert.equal(queries,0);
  }finally{fs.rmSync(dir,{recursive:true,force:true});}
});

test('实际写入或解密密钥才查询钥匙串，不可用时仍拒绝明文写入',()=>{
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'town-encryption-keys-'));let queries=0,available=true;
  const safe={isEncryptionAvailable(){queries++;return available},encryptString:s=>Buffer.from(s),decryptString:b=>b.toString()};
  try{const p=new Persistence(dir,safe),s=initialState();s.providers.push({id:'unit',type:'openai',apiKey:'test-only-key'});p.save(s);assert.equal(queries,1);assert.equal(p.encryptionAvailable,true);assert.ok(!fs.readFileSync(p.file,'utf8').includes('test-only-key'));p.load();assert.equal(queries,2);const previous=fs.readFileSync(p.file,'utf8');available=false;assert.throws(()=>p.save(s),/钥匙串/);assert.equal(p.encryptionAvailable,false);assert.equal(fs.readFileSync(p.file,'utf8'),previous);}finally{fs.rmSync(dir,{recursive:true,force:true});}
});
