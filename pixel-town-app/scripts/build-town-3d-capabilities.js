'use strict';
const fs=require('fs'),path=require('path');
const {catalog,petCatalog}=require('../main/catalog');
const {JOINTS}=require('../shared/town-3d-protocol');
const {fallback}=require('../shared/town-3d-jobs');
const base=path.resolve(__dirname,'../design/whole-town-realistic-actors-v8');
const out=path.resolve(__dirname,'../design/town-ai-v9');
const read=p=>JSON.parse(fs.readFileSync(path.join(base,p),'utf8'));
const actors=read('actors.json'),index=read('reference/asset-index.json');
function glb(file){const bytes=fs.readFileSync(path.join(base,file));return JSON.parse(bytes.subarray(20,20+bytes.readUInt32LE(12)).toString());}
const sources=new Map();
const capabilities=actors.map(p=>{
  if(!sources.has(p.assetKey))sources.set(p.assetKey,glb(index[p.assetKey]));
  const d=sources.get(p.assetKey),bones=new Set((d.skins||[]).flatMap(s=>s.joints.map(i=>d.nodes[i].name.replace(/\s/g,'_'))));
  const clips=p.animationSet?['Idle','Look around','Talk','Thoughtful','Wave','Cheer','Clap','Dance','Walk','Run']:(d.animations||[]).filter(a=>a.samplers.some(s=>d.accessors[s.input]?.max?.[0]>0)).map(a=>a.name);
  const profile=catalog.find(c=>c.catalogId===p.id)||petCatalog.find(c=>c.catalogId===p.id);
  const preset=profile?.presets?.find(s=>s.id===profile.defaultPreset)||profile?.presets?.[0];
  const steps=p.type==='person'&&p.id!=='kanna'?(preset?.occupationalBehaviors?.length?preset.occupationalBehaviors:fallback(p.id)):[];
  const jobs=steps.length?[{id:'daily:'+p.id,name:(preset.workplace||p.role)+' · 职业练习',workplace:preset.workplace||p.role,location:p.position,zone:p.zone,scope:'已布置的公共室外工作点；不代表进入室内或操作真实设备',steps:steps.slice(0,3).map((text,i)=>({name:text,seconds:8+i*2}))}]:[];
  return {id:p.id,name:p.name,type:p.type,zone:p.zone,position:p.position,sourceModel:p.sourceModel||p.assetKey,license:p.license,clips,joints:p.animationSet?Object.fromEntries(Object.entries(JOINTS).filter(([,v])=>bones.has(v.bone))):{},locomotion:{...(clips.includes('Walk')?{walk:'Walk'}:{}),...(clips.includes('Run')?{run:'Run'}:{})},jobs,boneCount:bones.size};
});
fs.writeFileSync(path.join(out,'capabilities.json'),JSON.stringify({version:1,actors:capabilities},null,2));
fs.writeFileSync(path.join(out,'catalog-public.json'),JSON.stringify([...catalog,...petCatalog].map(p=>({id:p.catalogId,name:p.name,occupation:p.occupation,kind:p.kind,persona:p.persona,schedule:p.schedule,defaultPreset:p.defaultPreset,presets:p.presets,profileMd:p.profileMd})),null,2));
console.log('capabilities:',capabilities.length,'people:',capabilities.filter(c=>c.type==='person').length,'jobs:',capabilities.filter(c=>c.jobs.length).length);
