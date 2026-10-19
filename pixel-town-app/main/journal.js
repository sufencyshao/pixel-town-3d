'use strict';
const fs=require('fs');
const path=require('path');
const crypto=require('crypto');
const Time=require('../shared/world-time');
const TYPES=Object.freeze({profile:'档案',action:'行为',arrival:'到达',outcome:'进展',observation:'见闻',thought:'心声',speech:'交流',goal:'目标',relation:'关系',emotion:'心情',environment:'环境',system:'小镇',error:'异常',need:'感官需求'});
class Journal {
  constructor(dir=null){
    this.dir=dir;this.subjects=new Map();this.cache=new Map();this.pending=new Map();this.registryDirty=false;this.bootstrapped=false;this.warnings=new Map();this.revision=0;
    if(dir){fs.mkdirSync(dir,{recursive:true,mode:0o700});const p=path.join(dir,'subjects.json');if(fs.existsSync(p)){const data=JSON.parse(fs.readFileSync(p,'utf8'));if(!data||data.version!==1||!Array.isArray(data.subjects))throw new Error('角色日志索引格式无效');for(const s of data.subjects){this.checkId(s.id);this.subjects.set(s.id,s);}this.bootstrapped=true;}}
  }
  checkId(id){if(typeof id!=='string'||!/^[-a-zA-Z0-9_]{1,100}$/.test(id))throw new Error('日志对象不存在');return id;}
  register(subject,time){
    this.checkId(subject.id);const old=this.subjects.get(subject.id),next={id:subject.id,name:String(subject.name||subject.id).slice(0,60),kind:subject.kind||'human'};
    if(JSON.stringify(old)!==JSON.stringify(next)){this.subjects.set(subject.id,next);this.registryDirty=true;}
    if(!old)this.add(subject.id,{time,type:'profile',text:subject.enabled===false?'档案已登记，当前未在小镇活动。':'日志已建立，开始记录实际发生的生活。'});
  }
  file(id,day){return path.join(this.dir,this.checkId(id),String(day)+'.jsonl');}
  read(id,day){
    const key=id+'/'+day;if(this.cache.has(key))return this.cache.get(key);
    const list=[],seen=new Set();let damaged=0;if(this.dir){const p=this.file(id,day);if(fs.existsSync(p)){for(const line of fs.readFileSync(p,'utf8').split('\n').filter(Boolean)){let e;try{e=JSON.parse(line);}catch{damaged++;continue;}if(!e||typeof e.id!=='string'||e.subjectId!==id||!Number.isFinite(e.time)||e.time<0||e.day!==day||Math.floor(e.time/1440)+1!==day||!Object.hasOwn(TYPES,e.type)||typeof e.text!=='string'){damaged++;continue;}if(!seen.has(e.id)){seen.add(e.id);list.push(e);}}}}
    if(damaged)this.warnings.set(key,`${damaged} 条损坏记录无法读取，原日志文件已保留，其余记录仍可查看。`);
    this.cache.set(key,list);return list;
  }
  add(id,{time,type,text,source='system',relatedIds=[],...extra}){
    if(!this.subjects.has(id))throw new Error('日志对象不存在');
    if(!Number.isFinite(time)||time<0||!Object.hasOwn(TYPES,type)||typeof text!=='string')throw new Error('日志记录格式无效');
    const day=Math.floor(time/1440)+1,key=id+'/'+day;
    const e={id:crypto.randomUUID(),subjectId:id,day,time,type,text:text.slice(0,6000),source,relatedIds:relatedIds.filter(x=>typeof x==='string').slice(0,12),...extra};
    this.read(id,day).push(e);if(!this.pending.has(key))this.pending.set(key,[]);this.pending.get(key).push(e);this.revision++;return e;
  }
  days(id){
    this.checkId(id);if(!this.subjects.has(id))throw new Error('日志对象不存在');
    const days=new Set();for(const key of this.cache.keys())if(key.startsWith(id+'/'))days.add(Number(key.split('/')[1]));
    if(this.dir){const p=path.join(this.dir,id);if(fs.existsSync(p))for(const file of fs.readdirSync(p))if(/^[1-9]\d*\.jsonl$/.test(file))days.add(Number(file.slice(0,-6)));}
    return [...days].sort((a,b)=>b-a);
  }
  page(id,{day,cursor=null,limit=120,type='all'}={}){
    const days=this.days(id);if(day===undefined)day=days[0]||1;
    if(!Number.isSafeInteger(day)||day<1||!Number.isInteger(limit)||limit<1||limit>200||(cursor!==null&&typeof cursor!=='string')||(type!=='all'&&!Object.hasOwn(TYPES,type)))throw new Error('日志查询参数无效');
    const full=this.read(id,day).slice().sort((a,b)=>a.time-b.time),entries=type==='all'?full:full.filter(e=>e.type===type),end=cursor===null?entries.length:entries.findIndex(e=>e.id===cursor);
    if(end<0)throw new Error('日志分页位置已失效');
    const start=Math.max(0,end-limit),result=entries.slice(start,end).reverse();
    const counts={};for(const e of full)counts[e.type]=(counts[e.type]||0)+1;
    return {subject:this.subjects.get(id),day,days,total:full.length,filteredTotal:entries.length,counts,entries:result,hasMore:start>0,nextCursor:result.at(-1)?.id||null,warning:this.warnings.get(id+'/'+day)||''};
  }
  recent(id,clock,limit=12){
    const today=Math.floor(clock/1440)+1,result=[];for(const day of this.days(id).filter(d=>d<=today).slice(0,3)){for(const e of this.read(id,day).slice().sort((a,b)=>b.time-a.time)){if(e.time<=clock&&e.type!=='profile'&&e.type!=='error')result.push(e);if(result.length>=limit)return result.reverse();}}return result.reverse();
  }
  bootstrap(state,zones){
    for(const s of [...state.residents,...state.pets,...(state.player?[state.player]:[]),{id:'town',name:'小镇',kind:'world'},{id:'sky-sun',name:'太阳',kind:'celestial'},{id:'sky-moon',name:'月亮',kind:'celestial'},...Object.keys(zones).map(id=>({id:'place-'+id,name:{work:'工作区域',rest:'休息区域',play:'游玩区域',chat:'相遇区域'}[id],kind:'place'}))])this.register(s,state.clock);
    if(!this.bootstrapped){
      for(const e of state.events.slice().reverse()){const type={dialogue:'speech',thought:'thought',relation:'relation',animal:'action',life:'action',error:'error',system:'system'}[e.kind]||'system';this.add('town',{time:e.time,type,text:e.text,source:'history',relatedIds:e.ids||[]});for(const id of e.ids||[])if(this.subjects.has(id))this.add(id,{time:e.time,type,text:e.text,source:'history',relatedIds:e.ids||[]});}
      this.bootstrapped=true;
    }
  }
  flush(){
    if(!this.dir){this.pending.clear();return;}
    for(const [key,entries] of this.pending){if(!entries.length)continue;const [id,day]=key.split('/'),file=this.file(id,Number(day));fs.mkdirSync(path.dirname(file),{recursive:true,mode:0o700});fs.appendFileSync(file,(fs.existsSync(file)?'\n':'')+entries.map(e=>JSON.stringify(e)).join('\n')+'\n',{mode:0o600});this.pending.delete(key);}
    if(this.registryDirty){const file=path.join(this.dir,'subjects.json'),tmp=file+'.tmp';fs.writeFileSync(tmp,JSON.stringify({version:1,subjects:[...this.subjects.values()]},null,2),{mode:0o600});fs.renameSync(tmp,file);this.registryDirty=false;}
    // Keep recent day caches only; full histories remain on disk and are paged on demand.
    if(this.cache.size>220)for(const key of [...this.cache.keys()].sort((a,b)=>Number(a.split('/')[1])-Number(b.split('/')[1])).slice(0,this.cache.size-180))if(!this.pending.has(key))this.cache.delete(key);
  }
  markdown(id,day){
    const p=this.page(id,{day,limit:200}),entries=this.read(id,p.day).slice().sort((a,b)=>a.time-b.time);const lines=[`# ${p.subject.name} · 第 ${p.day} 天`, '',`共 ${entries.length} 条记录。时间为小镇游戏时间；行为、计划、心声与见闻分别标记。`,p.warning,''];
    for(const e of entries){lines.push(`- **${Time.format(e.time)} · ${TYPES[e.type]}**（${e.source}） ${e.text.replaceAll('\n','  ').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}`);}
    return lines.join('\n')+'\n';
  }
}
module.exports={Journal,TYPES};
