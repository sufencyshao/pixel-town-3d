'use strict';
const fs=require('fs'),path=require('path'),os=require('os'),test=require('node:test'),assert=require('node:assert/strict');
const {platformAppData,prepare3DData}=require('../shared/desktop-data');
test('platform storage resolves macOS, Windows APPDATA/fallback and Linux without hardcoded user paths',()=>{
 assert.equal(platformAppData({platform:'darwin',home:'/home/test',env:{}}),path.join('/home/test','Library/Application Support'));
 assert.equal(platformAppData({platform:'win32',home:'/home/test',env:{APPDATA:'/roaming'}}),'/roaming');
 assert.equal(platformAppData({platform:'win32',home:'/home/test',env:{}}),path.join('/home/test','AppData/Roaming'));
 assert.equal(platformAppData({platform:'linux',home:'/home/test',env:{XDG_CONFIG_HOME:'/config'}}),'/config');
});
test('3D storage copies encrypted save/journals once, preserving originals and an existing 3D save',()=>{
 const support=fs.mkdtempSync(path.join(os.tmpdir(),'town-3d-seed-'));try{
  const source=path.join(support,'pixel-town-life');fs.mkdirSync(path.join(source,'journals'),{recursive:true});const original=JSON.stringify({sealedKey:'encrypted-only-sentinel',residents:[]});fs.writeFileSync(path.join(source,'town.json'),original);fs.writeFileSync(path.join(source,'journals/one.jsonl'),'private journal');
  const env={};const dir=prepare3DData({support,env}),target=path.join(dir,'town.json');assert.equal(env.PIXEL_TOWN_DATA_DIR,dir);assert.equal(fs.readFileSync(target,'utf8'),original);assert.equal(fs.readFileSync(path.join(source,'town.json'),'utf8'),original);assert.equal(fs.statSync(target).mode&0o777,0o600);assert.equal(fs.readFileSync(path.join(dir,'journals/one.jsonl'),'utf8'),'private journal');
  fs.writeFileSync(target,'v9-user-edited');prepare3DData({support,env:{}});assert.equal(fs.readFileSync(target,'utf8'),'v9-user-edited');assert.equal(fs.readFileSync(path.join(source,'town.json'),'utf8'),original);
  const custom=path.join(support,'explicit-test-dir');assert.equal(prepare3DData({support,env:{PIXEL_TOWN_DATA_DIR:custom}}),custom);assert.equal(fs.existsSync(custom),false);
 }finally{fs.rmSync(support,{recursive:true,force:true})}
});
