'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const Protocol=require('../shared/town-3d-protocol');
const {buildContext,entityFor}=require('./town-3d-context');
class Town3DService {
  constructor({town,llm,catalog,capabilities,pending=[],file,saveBindings,write=fs.writeFileSync,rename=fs.renameSync}){
    Object.assign(this,{town,llm,catalog,capabilities,pending,file,saveBindings,write,rename});
    this.runtime={version:1,actors:{},history:[]};this.executions=new Map();this.request=null;this.revision=0;
    if(file&&fs.existsSync(file)){
      const data=JSON.parse(fs.readFileSync(file,'utf8'));
      if(data.version!==1||!data.actors||!Array.isArray(data.history))throw new Error('三维生活记录结构无效，原文件已保留');
      this.runtime=data;
    }
    this.runtime.identityBindings||=Object.fromEntries(capabilities.map(c=>[c.id,entityFor(town.state,c.id)?.id]).filter(([,id])=>id));
  }
  entity(id,state=this.town.state){return entityFor(state,id,this.runtime.identityBindings);}
  persist(candidate){
    if(!this.file)return;
    fs.mkdirSync(path.dirname(this.file),{recursive:true});const tmp=this.file+'.tmp';
    try{this.write(tmp,JSON.stringify(candidate,null,2),{mode:0o600});this.rename(tmp,this.file);}finally{if(fs.existsSync(tmp))fs.unlinkSync(tmp);}
  }
  cap(id){const c=this.capabilities.find(c=>c.id===id);if(!c)throw new Error('角色不在三维小镇');const r=this.entity(id),preset=r?.presets?.find(p=>p.id===(r.presetId||r.defaultPreset))||r?.presets?.[0];return {...c,name:r?.name||c.name,jobs:c.jobs.map(j=>({...j,name:(r?.occupation||j.workplace)+' · 职业练习',workplace:preset?.workplace||j.workplace,steps:preset?.occupationalBehaviors?.length?preset.occupationalBehaviors.slice(0,3).map((name,i)=>({name,seconds:8+i*2})):j.steps}))};}
  scene(input){
    if(!input||!Array.isArray(input.actors)||input.actors.length!==this.capabilities.length)throw new Error('三维场景尚未就绪');
    const ids=new Set();const actors=input.actors.map(a=>{
      this.cap(a.id);if(ids.has(a.id)||!Array.isArray(a.position)||a.position.length!==3||a.position.some(n=>!Number.isFinite(n))||a.position[0]<-135||a.position[0]>165||Math.abs(a.position[1])>30||a.position[2]<-115||a.position[2]>110)throw new Error('三维位置无效');ids.add(a.id);
      return {id:a.id,position:a.position.slice(),busy:a.busy===true,action:String(a.action||'').slice(0,80)};
    });
    const e=input.environment||{};
    return {actors,environment:{day:Number.isFinite(e.day)?Math.max(1,Math.floor(e.day)):1,hour:Number.isFinite(e.hour)?Math.min(24,Math.max(0,e.hour)):9,weather:String(e.weather||'未知').slice(0,40),season:String(e.season||'未知').slice(0,40),paused:e.paused===true}};
  }
  initial(){return {runtime:structuredClone(this.runtime),capabilities:this.capabilities.map(c=>this.cap(c.id)),providers:this.town.state.providers.filter(p=>p.type!=='demo').map(p=>({id:p.id,name:p.name,models:p.models||[],hasKey:!!p.apiKey,type:p.type})),bindings:this.capabilities.map(c=>{const r=this.entity(c.id);return {id:c.id,name:r?.name||c.name,entityId:r?.id||null,model:r?.model?structuredClone(r.model):null};}),limits:{daily:this.town.state.dailyLimit,used:this.town.state.stats.filter(s=>s.day===new Date().toLocaleDateString('en-CA')).length,interval:this.town.state.apiInterval}};}
  context(id,input){const scene=this.scene(input),context=buildContext({state:this.town.state,actorId:id,capabilities:this.capabilities.map(c=>this.cap(c.id)),runtime:this.runtime,scene,catalog:this.catalog,pending:this.pending});const r=this.entity(id);context.data.pastLifeJournal=this.town.journal?.recent(r?.id,this.town.state.clock,8)?.map(({time,type,text})=>({time,type,text}))||[];context.system+='\n本人旧小镇实际日志（历史二维场景，不代表当前三维坐标或技能）：'+JSON.stringify(context.data.pastLifeJournal);return context;}
  fingerprint(r){const provider=this.town.state.providers.find(p=>p.id===r.model.providerId);return crypto.createHash('sha256').update(JSON.stringify({model:r.model,provider,persona:r.persona,name:r.name,occupation:r.occupation,preset:r.presetId,schedule:r.schedule,profileMd:r.profileMd,life:r.life,world:this.town.state.worldInfo,controlled:this.town.state.controlledId})).digest('hex');}
  cancel(id){
    this.revision++;if(this.request&&(!id||this.request.id===id)){this.request.controller.abort(new Error('三维 AI 已停止'));this.request=null;}
    // Renderer still sends a cancellation receipt for any plan already being executed.
    return true;
  }
  interrupt(reason='窗口关闭或重载'){
    this.cancel();if(!this.executions.size)return;
    const candidate=structuredClone(this.runtime);
    for(const e of this.executions.values())candidate.history.push({requestId:e.requestId,actorId:e.actorId,time:new Date().toISOString(),status:'interrupted',results:[],reason,detail:'没有最终引擎回执；不认定动作或工作完成，位置保留上次确认值。'});
    candidate.history=candidate.history.slice(-400);this.persist(candidate);this.runtime=candidate;this.executions.clear();
  }
  async bind(id,model){
    const r=this.entity(id);if(!r)throw new Error('观景动物不绑定人物 API');
    this.cancel(id);if(this.executions.has(id))throw new Error('请先停止正在执行的三维行为');
    if(!model||typeof model.providerId!=='string'||!this.town.state.providers.some(p=>p.id===model.providerId)||typeof model.model!=='string'||!model.model.trim()||model.model.length>120||!Number.isFinite(model.temperature)||model.temperature<0||model.temperature>2||!Number.isInteger(model.maxTokens)||model.maxTokens<512||model.maxTokens>8192)throw new Error('API 绑定参数无效（输出预算512–8192）');
    const next=structuredClone(this.town.state),target=this.entity(id,next);target.model={providerId:model.providerId,model:model.model.trim(),temperature:model.temperature,maxTokens:model.maxTokens};
    this.saveBindings(next);r.model=target.model;this.town.touch();return this.initial();
  }
  async decide(id,input,instruction=''){
    if(typeof instruction!=='string'||instruction.length>2000)throw new Error('指令最多2000字');
    if(this.request||this.executions.size)throw new Error('已有三维请求或行为正在进行，请先停止或等待完成');
    if(this.town.busy)throw new Error('二维窗口已有模型操作，请等待完成');
    const actor=this.cap(id),r=this.entity(id);if(!r)throw new Error('该观景动物没有 API 身份');
    if(r.isPlayer||this.town.state.controlledId===r.id)throw new Error('该角色正在由玩家控制');
    const provider=this.town.state.providers.find(p=>p.id===r.model?.providerId);if(!provider||provider.type==='demo')throw new Error('请先配置并绑定真实 API；本地规则不会伪造 AI 决策');
    const day=new Date().toLocaleDateString('en-CA');const used=this.town.state.stats.filter(s=>s.day===day).length;
    if(used>=this.town.state.dailyLimit)throw new Error('今日 API 调用已达到小镇上限');
    const {system}=this.context(id,input),revision=this.revision,fingerprint=this.fingerprint(r),controller=new AbortController(),requestId=crypto.randomUUID();
    const request={id,controller,requestId};this.request=request;
    const stat={id:requestId,day,residentId:r.id,provider:provider.name,model:r.model.model,purpose:'3d-decision',ok:false,applied:false,startedAt:Date.now()};
    this.town.state.stats.push(stat);this.town.touch();
    try{
      const result=await this.llm.chatCompletion({provider,model:r.model.model,system,messages:[{role:'user',content:instruction||'根据当前背景、作息、需求和实际执行回执，选择接下来一小步生活行为。'}],temperature:r.model.temperature,maxTokens:r.model.maxTokens,structured:true,signal:controller.signal,onDelta:()=>{}});
      if(controller.signal.aborted||this.revision!==revision||this.fingerprint(r)!==fingerprint)throw new Error('角色或控制状态已改变，本次过期结果已丢弃');
      const plan=Protocol.parse(result.text,actor);
      for(const c of plan.commands)if(c.type==='social'){
        const context=this.context(id,input).data;if(!context.now.neighbors.some(n=>n.id===c.targetId&&n.canTalk))throw new Error('交谈对象不在附近或正忙');
      }
      stat.ok=true;stat.tokens=(result.usage?.promptTokens||0)+(result.usage?.completionTokens||0);stat.latency=result.latency;
      this.executions.set(id,{requestId,actorId:id,plan,capability:actor,startedAt:Date.now(),modelFingerprint:fingerprint});
      return {requestId,actorId:id,plan,capability:actor};
    }catch(error){
      const safe=String(error.message||error).replaceAll(provider.apiKey||'\u0000','[已隐藏]').slice(0,1000);stat.error=safe;throw new Error(safe);
    }finally{if(this.request===request)this.request=null;this.town.touch();}
  }
  receipt(input){
    if(!input||typeof input.actorId!=='string')throw new Error('回执缺少人物');
    const e=this.executions.get(input.actorId);
    if(!e){if(this.runtime.history.some(h=>h.requestId===input.requestId))return {duplicate:true};throw new Error('回执没有对应的执行计划');}
    if(e.requestId!==input.requestId||!['completed','cancelled','failed'].includes(input.status)||!Array.isArray(input.results)||input.results.length>e.plan.commands.length)throw new Error('执行回执无效');
    const results=input.results.map((r,index)=>{
      const c=e.plan.commands[index];if(r.index!==index||!['completed','failed','cancelled'].includes(r.status)||!Number.isFinite(r.elapsed)||r.elapsed<0||r.elapsed>7200)throw new Error('指令回执无效');
      if(r.status==='completed'&&['wait','preset','pose'].includes(c.type)&&r.elapsed+.05<c.seconds)throw new Error('动作尚未计时完成');
      const item={index,type:c.type,status:r.status,elapsed:r.elapsed};
      if(c.type==='work'&&r.status==='completed'){
        const job=e.capability.jobs.find(j=>j.id===c.jobId);
        if(!Array.isArray(r.stages)||r.stages.length!==job.steps.length||r.stages.some((s,i)=>s.name!==job.steps[i].name||!Number.isFinite(s.seconds)||s.seconds+.05<job.steps[i].seconds||s.seconds>7200)||r.elapsed+.05<job.steps.reduce((n,s)=>n+s.seconds,0))throw new Error('职业练习阶段未全部完成');
        item.jobId=c.jobId;item.stages=job.steps.map((s,i)=>({name:s.name,seconds:r.stages[i].seconds}));
      }
      if(r.error)item.error=String(r.error).slice(0,240);
      if(c.type==='social'&&r.status==='completed')item.targetId=c.targetId;
      return item;
    });
    if(input.status==='completed'&&(results.length!==e.plan.commands.length||results.some(r=>r.status!=='completed')))throw new Error('计划尚未全部完成');
    const scene=this.scene(input.scene),now=scene.actors.find(a=>a.id===input.actorId),candidate=structuredClone(this.runtime);
    const summary={requestId:e.requestId,actorId:e.actorId,time:new Date().toISOString(),status:input.status,thought:e.plan.thought,proposedSpeech:e.plan.speech,speech:'',results,position:now.position};
    candidate.history.push(summary);candidate.history=candidate.history.slice(-400);
    const own=candidate.actors[e.actorId]||={};own.position=now.position;own.workLog||=[];
    const person=this.entity(e.actorId);own.needs||={energy:person?.energy??80,happiness:person?.happiness??75,social:person?.social??65};
    for(const r of results){const seconds=Math.min(600,r.elapsed);own.needs.energy=Math.min(100,Math.max(0,own.needs.energy+(r.type==='wait'?.05:r.type==='work'?-.08:r.type==='move'?-.03:-.005)*seconds));if(r.status==='completed'&&r.type==='social')own.needs.social=Math.min(100,own.needs.social+5);if(r.status==='completed'&&r.type==='work')own.needs.happiness=Math.min(100,own.needs.happiness+1);}
    for(const r of results.filter(r=>r.type==='work'&&r.status==='completed'))own.workLog.push({requestId:e.requestId,jobId:r.jobId,time:summary.time,stages:r.stages,outcome:'职业练习完成；没有制造或交易实物'});
    own.workLog=own.workLog.slice(-40);
    // Public words are delivered only with actual proximity evidence from this execution.
    const delivered=new Set(results.filter(r=>r.type==='social'&&r.status==='completed').map(r=>r.targetId).filter(id=>{const target=scene.actors.find(a=>a.id===id);return target&&this.cap(id).type==='person'&&Math.hypot(target.position[0]-now.position[0],target.position[2]-now.position[2])<=4}));
    const social=e.plan.commands.some(c=>c.type==='social'),hasOutcome=results.some(r=>r.status==='completed');
    if(!social&&hasOutcome)for(const a of scene.actors)if(a.id!==e.actorId&&this.cap(a.id).type==='person'&&Math.hypot(a.position[0]-now.position[0],a.position[2]-now.position[2])<=4)delivered.add(a.id);
    if(hasOutcome&&(!social||delivered.size))summary.speech=e.plan.speech;
    summary.deliveredTo=[...delivered];
    if(e.plan.speech)for(const targetId of delivered){const target=candidate.actors[targetId]||={};target.heard||=[];target.heard.push({speakerId:e.actorId,speaker:this.entity(e.actorId)?.name||this.cap(e.actorId).name,text:e.plan.speech,time:summary.time,source:'实际执行时附近送达；不是对方回应'});target.heard=target.heard.slice(-12);}
    this.persist(candidate);this.runtime=candidate;this.executions.delete(e.actorId);
    const stat=this.town.state.stats.find(s=>s.id===e.requestId);if(stat){stat.applied=true;stat.executionStatus=input.status;}this.town.touch();
    return {saved:true,summary};
  }
}
module.exports={Town3DService};
