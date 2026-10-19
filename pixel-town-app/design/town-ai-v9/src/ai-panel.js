import {ActorExecutor} from './ai-executor.js';
import Context from '../../../main/town-3d-context.js';
const $=id=>document.getElementById(id);
export class TownAIPanel {
 static async create(population){const panel=new TownAIPanel(population);await panel.load();return panel}
 constructor(population){this.population=population;this.epoch=0;this.inFlight=false;this.autoId=null;this.nextCall=0;this.unsaved=null;this.receiptPromise=Promise.resolve();this.events=[];this.api=window.town3DAPI;
  this.executor=new ActorExecutor(population,{capabilities:window.TOWN_CAPABILITIES.actors,navigation:window.TOWN_NAVIGATION.humanNavigation,onChange:()=>this.renderState(),onFinish:r=>{this.receiptPromise=this.saveReceipt(r)}});
 }
 async load(){
  this.data=this.api?await this.api.invoke('get'):{capabilities:window.TOWN_CAPABILITIES.actors,bindings:[],providers:[],runtime:{actors:{},history:[]},limits:{daily:0,interval:60}};
  this.executor.capabilities=new Map(this.data.capabilities.map(c=>[c.id,c]));this.applyNames();
  // Restored positions are accepted only on the same public walkable grid. Animals keep their authored placement.
  for(const [id,s] of Object.entries(this.data.runtime.actors)){const a=this.population.avatars.get(id);if(a&&a.profile.type==='person'&&s.position&&this.executor.nav.nearest(s.position,.26)!==null)a.root.position.fromArray(s.position)}
  $('ai-mode').textContent=this.api?'已连接本机 API 主进程 · 自主调用默认关闭':'浏览器预览 · API 调用请用“三维AI生活.command”打开';
  $('ai-settings').disabled=!this.api;$('ai-settings').onclick=()=>this.run(()=>this.api.invoke('settings'));
  $('ai-refresh').onclick=()=>this.run(async()=>{if(this.api){this.data=await this.api.invoke('get');this.executor.capabilities=new Map(this.data.capabilities.map(c=>[c.id,c]));this.applyNames();}this.syncSelection(true)});
  $('ai-context').onclick=()=>this.run(()=>this.showContext());$('ai-context-close').onclick=()=>$('ai-context-dialog').close();
  $('ai-once').onclick=()=>this.run(()=>this.decide());$('ai-stop').onclick=()=>this.run(()=>this.stop());
  $('ai-auto').onchange=()=>this.run(async()=>{if($('ai-auto').checked){if(!this.api)throw new Error('请从桌面三维入口使用 API');this.autoId=this.population.selected;this.nextCall=0;this.log('已启用当前人物自主行动，按调用间隔和每日上限运行。')}else await this.stop()});
  $('ai-bind').onclick=()=>this.run(async()=>{await this.stop();this.data=await this.api.invoke('bind',this.population.selected,{providerId:$('ai-provider').value,model:$('ai-model').value,temperature:Number($('ai-temperature').value),maxTokens:Number($('ai-tokens').value)});this.syncSelection(true);this.log('API 绑定已保存；只保存模型引用，密钥留在主进程。')});
  $('ai-provider').onchange=()=>{$('ai-model').value=this.data.providers.find(p=>p.id===$('ai-provider').value)?.models[0]||''};
  $('ai-retry-save').onclick=()=>this.run(async()=>{if(this.unsaved)await this.saveReceipt(this.unsaved);});
  for(const id of ['actor-action','actors-pause']){const el=$(id),event=id==='actor-action'?'onchange':'onclick',original=el[event];el[event]=async e=>{try{await this.stop();original?.(e)}catch(error){this.error(error)}}}
  document.addEventListener('visibilitychange',()=>{if(document.hidden)this.run(()=>this.stop())});
  this.syncSelection(true);window.townAI=this;this.log('每次 API 调用都会携带三维能力、当前人物完整背景、公开居民档案与本人关系和执行反馈。');
 }
 async run(fn){try{return await fn()}catch(error){this.error(error)}}
 applyNames(){for(const binding of this.data.bindings){const a=this.population.avatars.get(binding.id);if(a)a.profile.name=binding.name;const label=this.population.labels.find(l=>l.id===binding.id);if(label)label.el.textContent=binding.name;}this.population.refreshOptions();this.population.sync();}
 error(error){this.autoId=null;$('ai-auto').checked=false;this.log(error.message,'error');this.renderState()}
 log(text,kind='info'){this.events.unshift({text,time:new Date().toLocaleTimeString(),kind});this.events=this.events.slice(0,35);const el=$('ai-events');el.replaceChildren();for(const e of this.events){const li=document.createElement('li');li.textContent=e.time+' '+e.text;if(e.kind==='error')li.style.color='#a84832';el.append(li)}}
 syncSelection(force=false){const id=this.population.selected;if(!force&&id===this.selected)return;if(this.autoId&&this.autoId!==id){this.autoId=null;$('ai-auto').checked=false;this.api?.invoke('cancel').catch(e=>this.error(e));this.epoch++;this.log('切换观察人物，已关闭自主调用。现有行为可继续完成或点击停止。')}
  this.selected=id;const cap=this.executor.capabilities.get(id),binding=this.data.bindings.find(b=>b.id===id);$('ai-actor').textContent=binding?.name||cap?.name||id;
  const select=$('ai-provider');select.replaceChildren();for(const p of this.data.providers){const o=document.createElement('option');o.value=p.id;o.textContent=p.name;select.append(o)}
  select.value=binding?.model?.providerId||this.data.providers[0]?.id||'';$('ai-model').value=binding?.model?.providerId!=='demo'?binding?.model?.model||'':'';$('ai-temperature').value=binding?.model?.temperature??.8;$('ai-tokens').value=Math.max(1024,binding?.model?.maxTokens||1024);
  $('ai-capability').textContent=`${cap?.clips.length||0} 项原动作 · ${Object.keys(cap?.joints||{}).length} 个可控关节 · ${cap?.jobs.length||0} 份职业练习`;
  $('ai-job-note').textContent=cap?.jobs[0]?cap.jobs[0].name+'：'+cap.jobs[0].steps.map(s=>s.name).join(' → ')+'。在已布置室外工作点练习，不产出实物。':'当前模型没有职业任务。使用原版实际动作；无步态时保持原位。';
  for(const key of ['ai-once','ai-auto','ai-bind'])$(key).disabled=!this.api||!binding?.entityId;
  this.renderState();
 }
 renderState(){if(!$('ai-state'))return;if(this.api&&this.data)$('ai-budget').textContent='今日全镇已调用 '+this.data.limits.used+' / '+this.data.limits.daily+' 次；API 上下文预览免费。';const e=this.executor.snapshot();$('ai-state').textContent=this.unsaved?'记录尚未保存，后续调用已暂停':this.inFlight?'AI 正在决定下一步…':e?`${this.executor.capabilities.get(e.actorId)?.name} · ${e.type||'准备'} ${e.stage||''} · ${e.elapsed.toFixed(1)}秒`:'等待安排 · 可以查看上下文或请求下一步';$('ai-retry-save').hidden=!this.unsaved;$('ai-once').disabled=!this.api||this.inFlight||!!e||!!this.unsaved||!this.data?.bindings.find(b=>b.id===this.population.selected)?.entityId;}
 offlineContext(){const residents=window.TOWN_PUBLIC_CATALOG.map(p=>({...p,catalogId:p.id,memory:[],relationships:{},model:{providerId:'demo'},energy:80,happiness:75,social:65}));return Context.buildContext({state:{residents,pets:[],clock:540},actorId:this.population.selected,capabilities:this.data.capabilities,runtime:this.data.runtime,scene:this.executor.scene(),catalog:residents,pending:window.PENDING_ANIMALS})}
 async showContext(){const result=this.api?await this.api.invoke('context',this.population.selected,this.executor.scene()):this.offlineContext();$('ai-context-text').textContent=result.system;$('ai-context-dialog').showModal();return result}
 async stop(){this.epoch++;this.autoId=null;$('ai-auto').checked=false;if(this.api)await this.api.invoke('cancel');this.executor.stop();await this.receiptPromise;this.renderState()}
 async decide(automatic=false){if(!this.api)throw new Error('请使用桌面三维入口接入 API');if(this.inFlight||this.executor.active||this.unsaved)return;
  const epoch=this.epoch,id=this.population.selected;this.inFlight=true;this.renderState();
  try{const response=await this.api.invoke('decide',id,this.executor.scene(),automatic?'':$('ai-instruction').value);
   if(epoch!==this.epoch){await this.api.invoke('receipt',{requestId:response.requestId,actorId:id,status:'cancelled',results:[],scene:this.executor.scene()});return;}
   this.log('AI 心声（仅观察者可见）：'+response.plan.thought);this.executor.start(response);
  }catch(error){this.error(error)}finally{this.inFlight=false;this.nextCall=performance.now()+Math.max(15,Number($('ai-interval').value)||60,this.data.limits.interval||60)*1000;this.renderState()}
 }
 async saveReceipt(receipt){this.unsaved=receipt;this.renderState();try{const result=await this.api.invoke('receipt',receipt);this.unsaved=null;const fresh=await this.api.invoke('get');this.data.runtime=fresh.runtime;this.data.limits=fresh.limits;const last=result.summary;if(last?.speech){this.log('台词：'+last.speech);this.population.say(last.actorId,last.speech);}this.log('执行结果：'+receipt.status+'；已保存 '+receipt.results.filter(r=>r.status==='completed').length+' 个完成步骤。');this.renderState();return result}catch(error){this.error(new Error('记录写入失败，已暂停后续调用：'+error.message));return null}}
 update(dt){this.syncSelection();this.executor.update(dt);this.renderState();if(this.autoId&&this.autoId===this.population.selected&&!this.population.paused&&!this.inFlight&&!this.executor.active&&!this.unsaved&&performance.now()>=this.nextCall)this.decide(true)}
}
