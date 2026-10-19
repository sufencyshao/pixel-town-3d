'use strict';
const { initialState, createResident, migrateState, catalog, petCatalog, ACTIONS, ZONES } = require('./catalog');
const { normalizePersona } = require('./assets');
const { ANIMAL_ACTIONS, allowedAnimalActions, parseAnimalDecision, animalPrompt } = require('./animals');
const appearance = require('../shared/appearance');
const { gestures, supports, gestureDuration } = require('../shared/actions');
const { behaviorPrompt, parseExpression } = require('./character-behavior');
const worldTime = require('../shared/world-time');
const Life = require('../shared/life');
const Emotions = require('../shared/emotions');
const {characterContext} = require('./life-context');
const {Journal} = require('./journal');
const clamp=(v,min,max)=>Math.min(max,Math.max(min,Number(v)||0));
const pick=a=>a[Math.floor(Math.random()*a.length)];
class Town {
  constructor(state, llm, changed=()=>{}, journal=new Journal()) {
    this.state=migrateState(state||initialState());this.state.player ||= null;this.llm=llm;this.changed=changed;this.busy=false;this.revision=0;this.autonomyVersion=0;this.knowledgeVersion=0;this.input={x:0,y:0};this.state.controlledId=null;this.journal=journal;this.executions=new Map();this.journeys=new Map();this.journal.bootstrap(this.state,ZONES);this.environment=worldTime.sample(this.state.clock);
    for(const r of this.active())if(!r.isPlayer&&['api','local'].includes(r.behaviorSource)&&(['rest','doze','lie_down'].includes(r.action)||r.action==='idle'&&r.behaviorStatus==='waiting'&&Math.hypot(r.x-ZONES.rest.x,r.y-ZONES.rest.y)<180)){
      const point=this.recoveryPoint(r,r.target||{x:r.x,y:r.y});if(Math.hypot(point.x-r.x,point.y-r.y)>5){
        r.target=point;if(r.action==='idle'){r.action='walk';r.remaining=0;r.behaviorStatus='acting';this.record(r,'action','休息区域有些拥挤，正在走向附近的空位。',{source:'engine'});}
      }
    }
    for(const r of this.inhabitants())if(r.action!=='idle')this.executions.set(r.id,{action:r.action,version:r.actionVersion||0,hadTarget:!!r.target,arrived:!r.target,done:false});
  }
  active() { return [...this.state.residents.filter(r=>r.enabled), ...(this.state.player ? [this.state.player] : [])]; }
  activePets() { return this.state.pets.filter(r=>r.enabled); }
  inhabitants() { return [...this.active(), ...this.activePets()]; }
  entity(id) { return (id==='player'&&this.state.player)||this.state.residents.find(r=>r.id===id)||this.pet(id); }
  pet(id) { const r=this.state.pets.find(r=>r.id===id); if(!r) throw new Error('动物不存在'); return r; }
  setPets(ids) { if(!Array.isArray(ids)||ids.length>60||new Set(ids).size!==ids.length||ids.some(id=>!this.state.pets.some(p=>p.id===id))) throw new Error('动物选择无效');const selected=new Set(ids);this.state.pets.forEach(p=>{const enabled=selected.has(p.id);if(p.enabled!==enabled){p.intentVersion=(p.intentVersion||0)+1;this.cancelRequest(p.id);this.record(p,'system',enabled?'加入小镇活动。':'离开小镇活动区域。',{source:'player'});}p.enabled=enabled;});this.touch(); }
  resident(id) { const r=(id==='player'&&this.state.player)||this.state.residents.find(r=>r.id===id); if(!r) throw new Error('人物不存在'); return r; }
  animationFor(r) { return r.isPlayer ? (r.appearance.styleMode==='preset' ? catalog.find(c=>c.asset===r.appearance.avatarPreset)?.animation : null) : r.animation; }
  preparePlayer(payload) {
    if(!payload||typeof payload!=='object'||Array.isArray(payload)||typeof payload.name!=='string'||!payload.name.trim()||payload.name.trim().length>30) throw new Error('请输入 1–30 字的主角姓名');
    if(!payload.appearance||typeof payload.appearance!=='object'||Array.isArray(payload.appearance)) throw new Error('主角外观参数无效');
    const look=appearance.normalize(payload.appearance);
    const player=this.state.player ? structuredClone(this.state.player) : {...createResident(0,true),id:'player',isPlayer:true,kind:'human',occupation:'小镇主角',profileMd:'',persona:{personality:'由玩家亲自控制，好奇、友善',background:'来到小镇开始自己的生活。',likes:'探索小镇、认识邻居',speakingStyle:'自然、简短'},x:800,y:620,action:'idle',remaining:10,target:null,moving:false,direction:'front'};
    player.name=payload.name.trim();player.appearance=look;player.gender=({male:'男',female:'女',nonbinary:'中性'})[look.gender];player.enabled=true;
    player.model={providerId:'demo',model:'demo',temperature:.8,maxTokens:300};
    return player;
  }
  setPlayerExpression(expression) {
    const player=this.resident('player');
    const look=appearance.normalize({...player.appearance,expression});
    player.appearance=look;this.touch();return true;
  }
  touch() { this.revision++; this.changed(); }
  snapshot() { const s=structuredClone(this.state); s.providers=s.providers.map(({apiKey,...p})=>({...p,hasKey:!!apiKey})); s.busy=this.busy; s.revision=this.revision;s.journalRevision=this.journal.revision; return s; }
  record(r,type,text,extra={}) {this.journal.register(r,this.state.clock);return this.journal.add(r.id,{time:this.state.clock,type,text,source:r.behaviorSource||'system',...extra});}
  event(text,kind='life',ids=[]) {
    this.state.events.unshift({id:Date.now()+'-'+Math.random(),time:this.state.clock,text,kind,ids}); this.state.events=this.state.events.slice(0,180);
    const type={life:'action',animal:'action',dialogue:'speech',thought:'thought',relation:'relation',error:'error',system:'system'}[kind]||'system';
    this.journal.add('town',{time:this.state.clock,type,text,relatedIds:ids});
    const actors=ids.map(id=>[...this.state.residents,...this.state.pets,...(this.state.player?[this.state.player]:[])].find(r=>r.id===id)).filter(Boolean);
    for(const r of actors)this.record(r,type,text,{relatedIds:ids,source:kind==='thought'?'api':r.behaviorSource||'system'});
    if(['life','animal','dialogue'].includes(kind)&&actors.length){
      for(const observer of this.inhabitants().filter(r=>!ids.includes(r.id))){
        const distance=Math.min(...actors.map(a=>Math.hypot(a.x-observer.x,a.y-observer.y)));
        if(distance>260)continue;
        this.record(observer,'observation',observer.kind==='animal'?`感官刺激：距离约 ${Math.round(distance)} 的${actors[0].kind==='animal'?'动物':'人'}${kind==='dialogue'?'发出声音':'正在活动'}。`:`附近见闻：${text}`,{relatedIds:ids,source:'witness'});
        if(kind!=='dialogue')for(const actor of actors)this.recordEmotion(observer,Emotions.witness(observer,actor,actor.action,this.state.clock));
      }
      for(const [key,zone] of Object.entries(ZONES))if(actors.some(a=>Math.hypot(a.x-zone.x,a.y-zone.y)<180))this.journal.add('place-'+key,{time:this.state.clock,type:'observation',text,relatedIds:ids,source:'witness'});
    }
  }
  recordEmotion(r,change) {
    if(!change)return;this.record(r,'emotion',`心情${change.change>0?'+':''}${change.change.toFixed(1)}，当前${Emotions.label(change.value)} ${Math.round(change.value)}，压力 ${Math.round(change.stress)}。${change.reason}`,{source:change.source,relatedIds:change.relatedId?[change.relatedId]:[]});
  }
  hear(r,speaker,text) {this.record(r,'speech',`${speaker.name}对我说：${String(text).slice(0,4000)}`,{source:'heard',relatedIds:[speaker.id]});this.recordEmotion(r,Emotions.words(r,speaker,text,this.state.clock));}
  trackAction(r) {
    const old=this.executions.get(r.id);
    if(old&&!old.done)this.record(r,'outcome',`${ACTIONS[old.action]||ANIMAL_ACTIONS[old.action]||old.action}被新的行为打断。`,{action:old.action,source:'engine'});
    this.executions.set(r.id,{action:r.action,version:r.actionVersion||0,hadTarget:!!r.target,arrived:!r.target,done:false,moodAtStart:r.happiness,stressAtStart:r.emotion?.stress||0});
  }
  observeAction(r) {
    const e=this.executions.get(r.id);if(!e||e.done||e.action!==r.action)return;
    const label=(r.kind==='animal'?ANIMAL_ACTIONS:ACTIONS)[e.action]||e.action;
    if(e.hadTarget&&!e.arrived&&!r.target){
      e.arrived=true;const text=`${label}：已到达 x=${Math.round(r.x)}, y=${Math.round(r.y)}。`;
      this.record(r,'arrival',text,{source:'engine',position:{x:Math.round(r.x),y:Math.round(r.y)}});
      this.journal.add('town',{time:this.state.clock,type:'arrival',text:r.name+' '+text,relatedIds:[r.id]});
      for(const [key,z] of Object.entries(ZONES))if(Math.hypot(r.x-z.x,r.y-z.y)<180)this.journal.add('place-'+key,{time:this.state.clock,type:'arrival',text:r.name+'来到这个区域。',relatedIds:[r.id]});
    }
    if(!r.target&&r.remaining<=1e-9){e.done=true;this.record(r,'outcome',`${label}这一段行为结束；精力 ${Math.round(r.energy)}${r.kind==='animal'?'':`，社交满足 ${Math.round(r.social)}`}。`,{action:e.action,source:'engine'});if(r.kind!=='animal'&&Number.isFinite(e.moodAtStart)&&(Math.abs(r.happiness-e.moodAtStart)>=.5||Math.abs((r.emotion?.stress||0)-e.stressAtStart)>=1)){const change=Emotions.apply(r,{reason:`这一段${label}期间，心情从 ${Math.round(e.moodAtStart)} 变为 ${Math.round(r.happiness)}，压力从 ${Math.round(e.stressAtStart)} 变为 ${Math.round(r.emotion?.stress||0)}。`,source:'life'},this.state.clock);change.change=Math.round((r.happiness-e.moodAtStart)*10)/10;r.emotion.recent.at(-1).change=change.change;this.recordEmotion(r,change);}}
  }
  recordEnvironment() {
    const now=worldTime.sample(this.state.clock);if(now.day===this.environment.day&&now.phase===this.environment.phase&&now.sun.visible===this.environment.sun.visible&&now.moon.visible===this.environment.moon.visible)return;
    const text=`第 ${now.day} 天 ${now.time}，天色进入${now.label}。`;
    for(const id of ['town',...Object.keys(ZONES).map(k=>'place-'+k)])this.journal.add(id,{time:this.state.clock,type:'environment',text});
    for(const r of this.inhabitants())this.record(r,'environment',text,{source:'environment'});
    for(const [id,label,body] of [['sky-sun','太阳',now.sun],['sky-moon','月亮',now.moon]])this.journal.add(id,{time:this.state.clock,type:'environment',text:`第 ${now.day} 天 ${now.time}，${label}${body.visible?'出现在天空中':'位于地平线下'}。`,source:'environment'});
    this.environment=now;
  }
  recordJourney(r,moving) {
    const start=this.journeys.get(r.id);
    if(moving&&!start){this.journeys.set(r.id,{x:r.x,y:r.y});this.record(r,'action','玩家开始操控移动。',{source:'player'});}
    if(!moving&&start){this.journeys.delete(r.id);this.record(r,'arrival',`玩家操控移动结束，停在 x=${Math.round(r.x)}, y=${Math.round(r.y)}。`,{source:'player',position:{x:Math.round(r.x),y:Math.round(r.y)}});}
  }
  setKnowledge(value) {this.state.worldInfo=Life.validateWorld(value);this.knowledgeVersion++;this.pendingRequest?.abort();this.event('小镇基础资料已更新，之后的模型调用将使用新资料。','system');this.touch();}
  setLife(id,value) {
    const r=this.resident(id),change=Life.validateProfile(value);r.life=this.prepareLife(id,value);r.intentVersion=(r.intentVersion||0)+1;this.cancelRequest(id);
    this.record(r,'goal','镇长更新了生活方向与日常参考。'+(change.resetGoal?'当前目标已清空，下次可自行拟定。':''),{source:'player'});this.touch();
  }
  prepareLife(id,value) {const r=this.resident(id);if(r.isPlayer)throw new Error('主角由玩家决定生活方向');const change=Life.validateProfile(value),life=Life.profile(r.life,r);if(change.resetGoal&&life.focus){life.history.push({...life.focus,status:'abandoned',updatedAt:this.state.clock});life.history=life.history.slice(-12);life.focus=null;}return {...life,aspiration:change.aspiration,routine:change.routine,custom:true};}
  applyGoal(r,goal) {
    if(!goal)return;const life=Life.profile(r.life,r),old=life.focus;
    if(old&&(old.title!==goal.title||(old.status!=='ongoing'&&goal.status==='ongoing')))life.history.push({...old,status:old.status==='ongoing'?'abandoned':old.status,updatedAt:this.state.clock});
    life.history=life.history.slice(-12);life.focus={...goal,startedAt:old?.title===goal.title&&old.status==='ongoing'?old.startedAt:this.state.clock,updatedAt:this.state.clock};r.life=life;
    if(!old||old.title!==goal.title||old.status!==goal.status||old.reason!==goal.reason)this.record(r,'goal',`${{ongoing:'计划继续',completed:'自评完成',abandoned:'决定放下'}[goal.status]}：${goal.title}；${goal.reason}`,{source:'api',goalStatus:goal.status});
  }
  remember(r,text) { r.memory.push(text); r.memory=r.memory.slice(-16); }
  relation(a,b,delta) { a.relationships[b.id]=clamp((a.relationships[b.id]||0)+delta,-100,100); b.relationships[a.id]=clamp((b.relationships[a.id]||0)+delta,-100,100); }
  say(r,text) { if(r.kind==='animal')throw new Error('动物不会说人话');const spoken=String(text).slice(0,600); r.bubble=spoken.slice(0,140); r.bubbleUntil=this.state.clock+8; this.event(`${r.name}：${spoken}`,'dialogue',[r.id]); }
  apiBound(r) { return !r.isPlayer && !!this.state.providers.find(p=>p.id===r.model.providerId&&p.type!=='demo'); }
  apiOwned(r) { return this.state.autonomous && this.apiBound(r); }
  partnersFor(r) { return this.active().filter(x=>!x.isPlayer&&x.id!==r.id&&!x.thinking&&!x.meeting&&x.id!==this.state.controlledId&&!(['doze','lie_down'].includes(x.action)&&x.remaining>0)&&(!this.apiOwned(x)||x.behaviorSource!=='api'||(!x.target&&x.remaining<=0))); }
  intent(r,automatic=false) { return { version:r.intentVersion||0, asset:r.asset, model:JSON.stringify(r.model), automatic, autonomyVersion:this.autonomyVersion,knowledgeVersion:this.knowledgeVersion }; }
  currentIntent(r,intent) { return r.enabled&&this.entity(r.id)===r&&(r.intentVersion||0)===intent.version&&r.asset===intent.asset&&JSON.stringify(r.model)===intent.model&&this.knowledgeVersion===intent.knowledgeVersion&&(!intent.automatic||(this.state.running&&this.state.autonomous&&this.autonomyVersion===intent.autonomyVersion)); }
  cancelRequest(id) { if(this.pendingRequest&&this.lockedIds?.includes(id))this.pendingRequest.abort(); }
  setCount(count) {
    const n=clamp(Math.round(count),1,60);
    while(this.state.residents.length<n) this.state.residents.push(createResident(this.state.residents.length));
    const ordered=[...this.state.residents.filter(r=>r.enabled),...this.state.residents.filter(r=>!r.enabled)];
    ordered.forEach((r,i)=>{const enabled=i<n;if(r.enabled!==enabled){r.intentVersion=(r.intentVersion||0)+1;this.cancelRequest(r.id);this.record(r,'system',enabled?'来到小镇，开始参加日常生活。':'离开小镇，档案与经历保留。',{source:'player'});}r.enabled=enabled;if(!r.enabled)r.thinking=false;});
    if(this.state.controlledId&&!this.resident(this.state.controlledId).enabled)this.control(null);
    this.event(`小镇现在有 ${n} 位居民`,'system'); this.touch();
  }
  setRoster(ids) { if(!Array.isArray(ids)||!ids.length||ids.length>60) throw new Error('请选择 1–60 位居民'); const set=new Set(ids);if(set.size!==ids.length||ids.some(id=>!this.state.residents.some(r=>r.id===id)))throw new Error('居民选择无效');this.state.residents.forEach(r=>{const enabled=set.has(r.id);if(r.enabled!==enabled){r.intentVersion=(r.intentVersion||0)+1;this.cancelRequest(r.id);this.record(r,'system',enabled?'来到小镇，开始参加日常生活。':'离开小镇，档案与经历保留。',{source:'player'});}r.enabled=enabled;});if(this.state.controlledId&&!this.resident(this.state.controlledId).enabled)this.control(null);this.touch(); }
  configure(config) {
    if(typeof config.autonomous==='boolean'&&config.autonomous!==this.state.autonomous)this.autonomyVersion++;
    if(config.autonomous===false&&this.taskAutomatic)this.pendingRequest?.abort();
    if(config.running===false&&this.taskAutomatic)this.pendingRequest?.abort();
    if(typeof config.autonomous==='boolean')this.state.resumeAutonomy=config.autonomous;
    for(const key of ['running','autonomous','grid','zones']) if(typeof config[key]==='boolean') this.state[key]=config[key];
    if(config.speed!==undefined) this.state.speed=[1,2,4].includes(Number(config.speed))?Number(config.speed):1;
    if(config.apiInterval!==undefined) this.state.apiInterval=clamp(config.apiInterval,15,3600);
    if(config.dailyLimit!==undefined) this.state.dailyLimit=clamp(Math.round(config.dailyLimit),1,10000);
    this.touch();
  }
  advanceTo(minute) {
    const clock=worldTime.next(this.state.clock,minute);
    this.pendingRequest?.abort();
    this.state.clock=clock;
    this.recordEnvironment();
    for(const r of this.inhabitants()) {
      r.intentVersion=(r.intentVersion||0)+1;r.thinking=false;r.dialoguePending=false;
      if(r.bubbleUntil<clock)r.bubble='';
      if((r.thoughtUntil||0)<clock)r.thought='';
    }
    const moment=worldTime.sample(clock);
    this.event(`时间来到第 ${moment.day} 天 ${moment.time} · ${moment.label}`,'system');
    this.touch();return clock;
  }
  update(id,data) {
    if(id==='player') throw new Error('请在主角外观编辑器中保存主角');
    const original=this.entity(id),r=structuredClone(original);
    const animal=r.kind==='animal';
    if(data.name!==undefined) { if(!String(data.name).trim()) throw new Error('姓名不能为空'); r.name=String(data.name).trim().slice(0,30); }
    if(data.occupation!==undefined&&!animal) r.occupation=String(data.occupation).slice(0,60);
    if(data.asset!==undefined) { const source=(animal?petCatalog:catalog).find(c=>c.asset===data.asset); if(!source) throw new Error('形象不存在'); for(const key of ['kind','asset','assetFolder','animation','sprite','catalogId','presets','animal']) if(source[key]!==undefined)r[key]=structuredClone(source[key]); }
    if(data.presetId!==undefined) { const preset=r.presets?.find(p=>p.id===data.presetId); if(!preset)throw new Error('预设不存在');r.persona=normalizePersona(preset);r.presetId=preset.id;if(!animal&&data.occupation===undefined&&preset.role)r.occupation=String(preset.role).slice(0,60);for(const key of ['schedule','workplace','occupationalBehaviors','preferredPlaces'])if(preset[key]!==undefined)r[key]=structuredClone(preset[key]); }
    if(data.persona&&!animal) for(const k of ['personality','background','likes','speakingStyle']) if(data.persona[k]!==undefined) r.persona[k]=String(data.persona[k]).slice(0,4000);
    if(data.profileMd!==undefined&&!animal) r.profileMd=String(data.profileMd).slice(0,6000);
    if(data.model) { const m=data.model; if(!this.state.providers.some(p=>p.id===m.providerId)) throw new Error('服务商不存在'); r.model={providerId:m.providerId,model:String(m.model||'').trim().slice(0,120),temperature:clamp(m.temperature,0,2),maxTokens:clamp(Math.round(m.maxTokens),64,8192)}; if(m.providerId!=='demo'&&!r.model.model) throw new Error('请填写模型名称'); }
    if(!animal&&!r.life?.custom){const life=Life.profile(r.life,r);r.life={...Life.defaultProfile(r),focus:life.focus,history:life.history};}
    if(!animal)r.emotion=Emotions.normalize(r,this.state.clock);
    r.intentVersion=(original.intentVersion||0)+1;this.cancelRequest(id);Object.assign(original,r);this.journal.register(original,this.state.clock);this.record(original,'profile','人物档案或模型配置已更新。',{source:'player'});this.touch(); return original;
  }
  recoveryPoint(r,point) {
    const others=this.active().filter(x=>x.id!==r.id),candidates=[];
    // Reserve nearby resting spots, including destinations still being reached.
    // This does not move manually placed residents or introduce path collisions.
    for(let radius=0;radius<=4;radius++)for(let dx=-radius;dx<=radius;dx++)for(let dy=-radius;dy<=radius;dy++)if(Math.max(Math.abs(dx),Math.abs(dy))===radius){
      const x=clamp(point.x+dx*140,90,1510),y=clamp(point.y+dy*140,120,910),candidate={x,y};
      const free=others.every(other=>Math.hypot(other.x-x,other.y-y)>=120&&(!other.target||Math.hypot(other.target.x-x,other.target.y-y)>=120));
      candidates.push({point:candidate,free,distance:Math.hypot(x-point.x,y-point.y)});
    }
    return candidates.filter(x=>x.free).sort((a,b)=>a.distance-b.distance)[0]?.point||point;
  }
  act(id,action,point,source='manual') {
    const r=this.entity(id); if(r.kind==='animal') return this.actPet(id,action,point,source); if(!r.enabled) throw new Error('该人物未入住'); if(!Object.hasOwn(ACTIONS,action)) throw new Error('不支持的动作');
    const animation=this.animationFor(r); if(!supports(action,animation)) throw new Error('该形象尚无此动作素材');
    const gestureMs=gestureDuration(action,animation);
    if(r.meeting) { const other=this.active().find(x=>x.id===r.meeting.partner); if(other?.meeting?.partner===r.id) {other.meeting=null;other.target=null;other.remaining=8;} r.meeting=null; }
    if(this.state.controlledId===id&&action!=='walk'){if(r.isPlayer)this.input={x:0,y:0};else this.control(null);}
    r.action=action; r.actionVersion=(r.actionVersion||0)+1;
    if(source!=='api'){r.intentVersion=(r.intentVersion||0)+1;if(source==='manual'){this.cancelRequest(id);r.thinking=false;r.dialoguePending=false;}r.thought='';r.thoughtUntil=0;r.bubble='';r.bubbleUntil=0;}
    r.behaviorSource=source;r.behaviorStatus='acting';
    r.remaining=gestureMs===null?(['greet','cheer','jump','surprise'].includes(action)?4:action==='lie_down'?90:action==='doze'?25:action==='slack'?12:12+Math.random()*12):gestureMs/1000;
    r.moving=false;
    const area=['doze','lie_down'].includes(action)?'rest':action;
    r.target=gestureMs!==null?null:point?{x:clamp(point.x,90,1510),y:clamp(point.y,120,910)}:(!r.isPlayer&&['work','rest','play','chat'].includes(area)?{x:ZONES[area].x+Math.random()*180-90,y:ZONES[area].y+Math.random()*120-60}:action==='walk'?{x:100+Math.random()*1400,y:150+Math.random()*720}:null);
    if(!r.isPlayer&&source!=='manual'&&['rest','doze','lie_down'].includes(action)&&r.target)r.target=this.recoveryPoint(r,r.target);
    this.trackAction(r);this.event(`${r.name}开始${ACTIONS[action]}`, 'life',[r.id]); this.touch();
  }
  move(id,point) { this.act(id,'walk',point); }
  teleport(id,point) { const r=this.entity(id); r.x=clamp(point.x,90,1510); r.y=clamp(point.y,120,910); r.target=null; r.action='idle'; r.remaining=12;r.intentVersion=(r.intentVersion||0)+1;this.cancelRequest(id);r.thinking=false;r.dialoguePending=false;r.behaviorSource='manual';r.thought='';r.thoughtUntil=0;this.trackAction(r);this.record(r,'arrival',`镇长将角色摆放到 x=${Math.round(r.x)}, y=${Math.round(r.y)}。`,{source:'player'}); this.touch(); }
  meet(a,b,automatic=true,opening=null) {
    if(a.kind==='animal'||b.kind==='animal')throw new Error('动物不会参加人类交谈');
    if(automatic&&(a.isPlayer||b.isPlayer))throw new Error('主角对话需要玩家邀请');
    for(const r of [a,b])if(r.meeting){const previous=this.active().find(x=>x.id===r.meeting.partner);if(previous?.meeting?.partner===r.id){previous.meeting=null;previous.target=null;previous.remaining=8;}r.meeting=null;}
    const center={x:650+Math.random()*300,y:400+Math.random()*240};
    a.action=b.action='chat';a.remaining=b.remaining=20;
    for(const r of [a,b]){r.actionVersion=(r.actionVersion||0)+1;r.intentVersion=(r.intentVersion||0)+1;}
    a.target={x:center.x-160,y:center.y};b.target={x:center.x+160,y:center.y};
    a.meeting={partner:b.id,initiator:true,automatic,...(opening?{opening}:{})};b.meeting={partner:a.id,initiator:false,automatic};
    this.trackAction(a);this.trackAction(b);
    this.event(`${a.name}邀请${b.name}聊聊天，两人走向相遇区`,'life',[a.id,b.id]);this.touch();
  }
  control(id) {
    const next=id?this.resident(id):null;if(next&&!next.enabled)throw new Error('该人物未入住');
    if(this.state.controlledId){const old=this.resident(this.state.controlledId);this.recordJourney(old,false);old.moving=false;if(!old.isPlayer)old.intentVersion=(old.intentVersion||0)+1;if(!old.thinking&&!old.dialoguePending&&!old.meeting){old.action='idle';old.remaining=10;}}
    if(next&&!next.isPlayer){next.intentVersion=(next.intentVersion||0)+1;this.cancelRequest(next.id);next.thinking=false;next.dialoguePending=false;}
    if(next&&!next.thinking&&!next.dialoguePending&&!next.meeting){next.target=null;next.action='idle';next.remaining=10;}
    this.state.controlledId=id||null;this.input={x:0,y:0};this.touch();
  }
  setInput(point) {this.input={x:clamp(point.x,-1,1),y:clamp(point.y,-1,1)};if(this.state.controlledId){const r=this.resident(this.state.controlledId);if(!r.thinking&&!r.dialoguePending&&!r.meeting&&(this.input.x||this.input.y))r.target=null;}}
  localAction(r) {
    const plan=Emotions.localPlan(r,this.state.clock,this.partnersFor(r));r.localPartnerId=plan?.partnerId||null;
    if(plan&&supports(plan.action,this.animationFor(r)))return plan.action;
    if(r.energy<32) return 'rest';
    if(r.social<35 && this.active().length>1) return 'chat';
    const hour=(this.state.clock/60)%24;
    const playful=/爱玩|慵懒|偷懒|分心/.test(r.persona.personality);
    return pick(hour>=9&&hour<17?(playful?['work','play','walk','rest','chat']:['work','work','walk','chat']):['rest','play','walk','chat']);
  }
  readyForDecision(r) {
    if(r.target)return false;
    if(!r.decisionAt||r.remaining<=0)return true;
    if(r.kind==='animal')return (r.energy<25&&!['rest','sleep','perch'].includes(r.action))||(r.needs?.hunger>85&&!['eat','graze','peck','forage'].includes(r.action))||(r.needs?.thirst>85&&r.action!=='drink');
    const previous=r.lastExpression?.time;
    return (r.energy<25&&!Emotions.recovering.includes(r.action))||(r.social<20&&r.action!=='chat'&&!Emotions.recovering.includes(r.action))||((r.emotion?.stress||0)>70&&!Emotions.recovering.includes(r.action))||(Number.isFinite(r.lastExpression?.moodValue)&&Math.abs(r.happiness-r.lastExpression.moodValue)>=15)||(Number.isFinite(previous)&&worldTime.sample(previous).phase!==worldTime.sample(this.state.clock).phase);
  }
  tick(dt=0.5,force=false) {
    if(!this.state.running&&!force) return;
    const d=dt*this.state.speed; this.state.clock+=d;this.recordEnvironment();
    for(const r of this.active()) {
      if(r.bubbleUntil<this.state.clock) r.bubble='';
      if((r.thoughtUntil||0)<this.state.clock)r.thought='';
      r.moving=false;
      if(r.id===this.state.controlledId&&!r.thinking&&!r.dialoguePending&&!r.meeting&&(this.input.x||this.input.y)){const{x,y}=this.input,len=Math.hypot(x,y);r.x=clamp(r.x+x/len*75*d,90,1510);r.y=clamp(r.y+y/len*75*d,120,910);r.direction=Math.abs(x)>Math.abs(y)?(x<0?'left':'right'):(y<0?'back':'front');r.moving=true;r.action='walk';this.recordJourney(r,true);continue;}
      this.recordJourney(r,false);
      const moving=r.target && Math.hypot(r.x-r.target.x,r.y-r.target.y)>5;
      if(moving) { const dx=r.target.x-r.x,dy=r.target.y-r.y,len=Math.hypot(dx,dy),step=Math.min(len,30*d); r.x+=dx/len*step; r.y+=dy/len*step; r.moving=true;r.direction=Math.abs(dx)>Math.abs(dy)?(dx<0?'left':'right'):(dy<0?'back':'front'); }
      else { r.target=null; r.remaining-=d; const recoveryRate={rest:1.5,slack:.55,doze:2.2,lie_down:1.7,idle:0};r.energy=clamp(r.energy+(recoveryRate[r.action]??(r.action==='work'?-.8:-.25))*d,0,100); r.social=clamp(r.social+(r.action==='chat'?1.5:-0.25)*d,0,100); }
      if(!r.thinking){const alone=!this.active().some(x=>x.id!==r.id&&Math.hypot(x.x-r.x,x.y-r.y)<180);this.recordEmotion(r,Emotions.advance(r,d,this.state.clock,{alone,moving}));}
      this.observeAction(r);
      r.mood=Emotions.mood(r.happiness);
      if(gestures.includes(r.action)&&r.remaining<=1e-9&&!r.thinking){r.action='idle';r.remaining=this.apiOwned(r)?0:10;}
      if(r.meeting) {
        const partner=this.active().find(x=>x.id===r.meeting.partner&&x.enabled);
        if(!partner||partner.meeting?.partner!==r.id){r.meeting=null;r.remaining=8;}
        else {if(r.meeting.initiator&&!r.target&&!partner.target&&!this.busy){const {automatic,opening}=r.meeting;const needed=this.state.autonomous?[r,partner].filter(x=>this.apiBound(x)&&!(x===r&&opening)).length:0;const ready=!automatic||!needed||(Date.now()-this.state.lastApiAt>=this.state.apiInterval*1000&&this.dailyCalls()+needed<=this.state.dailyLimit);if(opening&&!this.state.autonomous){r.meeting=partner.meeting=null;this.act(r.id,'idle',null,'local');this.act(partner.id,'idle',null,'local');}else if(ready){r.meeting=partner.meeting=null;this.converse(r.id,partner.id,automatic,opening).catch(()=>{});}}continue;}
      }
      if(r.id===this.state.controlledId){if(!moving&&!r.thinking&&!r.dialoguePending&&(!r.isPlayer||r.action==='walk'||r.remaining<=0))r.action='idle';continue;}
      if(r.isPlayer){if(!moving&&!r.thinking&&!r.dialoguePending&&(r.action==='walk'||r.remaining<=0))r.action='idle';continue;}
      if(r.dialoguePending)continue;
      if(r.remaining<=0&&!r.thinking) {
        if(this.apiOwned(r)){if(r.behaviorStatus!=='waiting'){
          const recovering=['rest','doze','lie_down'].includes(r.action);r.action='idle';r.actionVersion=(r.actionVersion||0)+1;r.behaviorStatus='waiting';
          if(recovering){const point=this.recoveryPoint(r,{x:r.x,y:r.y});if(Math.hypot(point.x-r.x,point.y-r.y)>5){r.target=point;r.action='walk';r.behaviorStatus='acting';this.trackAction(r);this.record(r,'action','休息区域有些拥挤，正在走向附近的空位。',{source:'engine'});}}
        }r.remaining=0;continue;}
        const action=this.localAction(r);
        if(action==='chat') { const others=this.partnersFor(r).filter(x=>!this.apiOwned(x)); const partner=others.find(x=>x.id===r.localPartnerId)||pick(others); if(partner&&!this.busy) this.meet(r,partner); else this.act(r.id,'walk',null,'local'); }
        else this.act(r.id,action,null,'local');
      }
    }
    this.tickPets(d);
    if(this.state.autonomous && !this.busy && this.dailyCalls()<this.state.dailyLimit && Date.now()-this.state.lastApiAt>=this.state.apiInterval*1000) {
      const candidates=this.inhabitants().filter(r=>this.apiBound(r)&&!r.thinking&&!r.dialoguePending&&!r.meeting&&r.id!==this.state.controlledId&&this.readyForDecision(r)).sort((a,b)=>(a.decisionAt||0)-(b.decisionAt||0));
      if(candidates[0]) this.decide(candidates[0].id,{automatic:true}).catch(()=>{});
    }
  }
  actPet(id,action,point,source='manual') {
    const p=this.pet(id);if(!p.enabled)throw new Error('该动物尚未入住');
    if(!allowedAnimalActions(p).includes(action))throw new Error('该物种不支持此行为');
    p.action=action;p.remaining=8+Math.random()*12;p.bubble='';
    if(source!=='api'){p.intentVersion=(p.intentVersion||0)+1;if(source==='manual')this.cancelRequest(id);}p.behaviorSource=source;p.behaviorStatus='acting';p.actionVersion=(p.actionVersion||0)+1;
    const moving=['walk','run','hop','fly','swim','explore','forage','flee'].includes(action);
    const threat=action==='flee'?this.active().sort((a,b)=>Math.hypot(a.x-p.x,a.y-p.y)-Math.hypot(b.x-p.x,b.y-p.y))[0]:null;
    const retreat=threat?{x:p.x+(p.x-threat.x||1)*3,y:p.y+(p.y-threat.y||1)*3}:null;
    point=point||retreat;
    p.target=moving?{x:clamp(point?.x??(140+Math.random()*1300),90,1510),y:clamp(point?.y??(180+Math.random()*640),120,910)}:null;
    this.trackAction(p);this.event(`${p.name}：${ANIMAL_ACTIONS[action]}`,'animal',[id]);this.touch();
  }
  localPetAction(p) {
    const available=allowedAnimalActions(p),rest=available.find(a=>['sleep','rest','idle','perch'].includes(a))||available[0];
    if(p.energy<35)return rest;
    if(p.needs?.thirst>65&&available.includes('drink'))return 'drink';
    if(p.needs?.hunger>65)return available.find(a=>['eat','peck','graze','forage'].includes(a))||rest;
    const close=this.active().some(r=>Math.hypot(r.x-p.x,r.y-p.y)<80);
    if(close&&/警觉|退让|胆小/.test(p.persona.personality)&&available.includes('flee'))return 'flee';
    const night=(this.state.clock/60)%24<6||(this.state.clock/60)%24>=21;
    if(night&&!p.animal?.nocturnal)return rest;
    const spontaneous=available.filter(a=>a!=='flee'&&!(p.needs?.hunger<35&&['eat','peck','graze'].includes(a))&&!(p.needs?.thirst<35&&a==='drink'));
    return pick(spontaneous)||rest||'idle';
  }
  tickPets(d) {
    for(const p of this.activePets()) {
      p.bubble='';p.moving=false;p.needs ||= {hunger:25,thirst:20,safety:85,stimulation:50};
      if(p.target&&Math.hypot(p.x-p.target.x,p.y-p.target.y)>5){
        const dx=p.target.x-p.x,dy=p.target.y-p.y,len=Math.hypot(dx,dy),speed=clamp(p.animal?.movementSpeed||(24*(p.animal?.speedFactor||1)),8,65),step=Math.min(len,speed*d);
        p.x+=dx/len*step;p.y+=dy/len*step;p.direction=Math.abs(dx)>Math.abs(dy)?(dx<0?'left':'right'):(dy<0?'back':'front');p.moving=true;
      }else{p.target=null;p.remaining-=d;}
      p.energy=clamp(p.energy+(['sleep','rest','perch'].includes(p.action)?1.2:-.2)*d,0,100);
      p.needs.hunger=clamp(p.needs.hunger+(['eat','graze','peck','forage'].includes(p.action)?-2:.12)*d,0,100);
      p.needs.thirst=clamp(p.needs.thirst+(p.action==='drink'?-3:.15)*d,0,100);
      p.needs.stimulation=clamp(p.needs.stimulation+(['play','explore','sniff','forage'].includes(p.action)?.5:-.1)*d,0,100);
      p.mood=p.energy<25?'tired':'calm';this.observeAction(p);
      if(p.remaining<=0&&!p.thinking){if(this.apiOwned(p)){p.behaviorStatus='waiting';p.remaining=0;}else this.actPet(p.id,this.localPetAction(p),null,'local');}
    }
  }
  async decidePet(id,{automatic=false}={}) {
    const p=this.pet(id);if(!p.enabled)throw new Error('该动物尚未入住');
    const intent=this.intent(p,automatic);return this.locked([p],async()=>{
      p.decisionAt=Date.now();
      try {
        const text=await this.request(p,'animal-decision',[{role:'user',content:'根据当前感官与生理需求选择自然行为。'}]);
        if(!this.currentIntent(p,intent)){this.state.stats.at(-1).applied=false;return {discarded:true};}
        const decision=parseAnimalDecision(text,p);
        this.actPet(id,decision.action,null,'api');p.observation={senses:decision.senses,need:decision.need};
        this.record(p,'need',`感官：${decision.senses.join('、')||'无'}；需求：${decision.need}；选择 ${ANIMAL_ACTIONS[decision.action]}。`,{source:'api'});this.state.stats.at(-1).applied=true;
        this.remember(p,JSON.stringify(decision));
        return decision;
      }catch(e){if(!this.currentIntent(p,intent)){if(this.state.stats.at(-1))this.state.stats.at(-1).applied=false;return {discarded:true};}if(this.state.stats.at(-1)){this.state.stats.at(-1).ok=false;this.state.stats.at(-1).error=e.message;}this.event(`${p.name}动物决策失败：${e.message}；采用本地自然行为`,'error',[id]);if(p.enabled)this.actPet(id,this.localPetAction(p),null,'local');throw e;}
    },{automatic});
  }
  prompt(r) {
    this.journal.register(r,this.state.clock);
    if(r.kind==='animal')return animalPrompt(r,this.state)+'\n该个体最近实际活动与感官记录：'+JSON.stringify(this.journal.recent(r.id,this.state.clock,8).filter(e=>['action','arrival','outcome','observation','environment','need'].includes(e.type)).map(({time,type,text})=>({time:worldTime.format(time),type,text})))+'。这些记录只作为生物刺激与行为反馈，不转为人类思想或职业。';
    return characterContext(r,this.state,ZONES,this.journal);
  }
  async modelExpression(r,purpose,messages,mode='decision') {
    const animation=this.animationFor(r),partners=mode==='decision'?this.partnersFor(r).map(({id,name})=>({id,name})):[];
    const currentGoal=r.life?.focus||null;
    const compact=r.model.maxTokens<=400?'\n本次输出预算有限，请用一句短心声、一句简短台词和简短情绪原因。已有目标未改变时可省略 goal，优先完整输出 JSON。':'';
    const text=await this.request(r,purpose,messages,behaviorPrompt(animation,{mode,partners,zones:ZONES,currentGoal})+compact);
    const stat=this.state.stats.at(-1);
    try {
      const expression=parseExpression(text,animation,{mode,partners,currentGoal});
      stat.action=expression.action;return expression;
    }catch(e){stat.ok=false;stat.error=e.message;stat.responseOk=true;this.touch();throw e;}
  }
  applyExpression(r,expression,{mode='conversation',automatic=false,recordThought=true}={}) {
    if(mode==='decision'&&expression.action==='chat') {
      const partner=this.partnersFor(r).find(x=>x.id===expression.partnerId);
      if(!partner)throw new Error('邀请对象已离开或正在忙碌');
      this.meet(r,partner,automatic,expression);
    }else {
      const point=mode==='decision'?(expression.destination||ZONES[['doze','lie_down'].includes(expression.action)?'rest':expression.action]||{x:r.x,y:r.y}):{x:r.x,y:r.y};
      this.act(r.id,expression.action,point,'api');
      if(mode==='decision'&&['work','rest','play','idle','slack','doze','lie_down'].includes(expression.action))r.remaining=expression.duration??(expression.action==='lie_down'?90:expression.action==='doze'?25:expression.action==='slack'?12:30);
    }
    r.behaviorSource='api';r.behaviorStatus='acting';
    this.applyGoal(r,expression.goal);
    if(expression.emotion)this.recordEmotion(r,Emotions.apply(r,{...expression.emotion,source:'api'},this.state.clock));
    if(expression.interaction)this.record(r,'relation',`这轮交流的自评感受：好感变化 ${expression.interaction.feeling>0?'+':''}${expression.interaction.feeling}；${expression.interaction.continue?'还想继续聊':'想结束这段交流'}。`,{source:'api'});
    r.lastExpression={action:expression.action,thought:expression.thought,speech:expression.speech,...(expression.interaction?{interaction:expression.interaction}:{}),...(expression.emotion?{emotion:expression.emotion}:{}),moodValue:r.happiness,time:this.state.clock};
    if(recordThought){r.thought=expression.thought;r.thoughtUntil=this.state.clock+16;this.event(`${r.name}的心声：${expression.thought}`,'thought',[r.id]);this.remember(r,`我想到：${expression.thought}`);}
    r.bubble='';r.bubbleUntil=0;
    if(expression.speech&&!(mode==='decision'&&expression.action==='chat'))this.say(r,expression.speech);
    this.touch();
  }
  localSpeech(r,speech) { this.act(r.id,'chat',{x:r.x,y:r.y},'local');this.say(r,speech); }
  waitAfterError(r,intent) {
    if(!this.currentIntent(r,intent))return;
    this.act(r.id,'idle',{x:r.x,y:r.y},'api');r.remaining=0;r.behaviorStatus='waiting';r.thought='';r.thoughtUntil=0;r.bubble='';r.bubbleUntil=0;
  }
  dailyCalls() { const today=new Date().toLocaleDateString('en-CA'); return this.state.stats.filter(s=>s.day===today).length; }
  async request(r,purpose,messages,extra='') {
    const provider=this.state.providers.find(p=>p.id===r.model.providerId); if(!provider) throw new Error(`${r.name}的 API 服务商已失效`);
    if(provider.type==='demo') throw new Error('规则模式不调用 API');
    if(this.dailyCalls()>=this.state.dailyLimit) throw new Error('已达到今日 API 调用上限，请在设置中调整');
    this.state.lastApiAt=Date.now();
    // 开始即计入次数（失败也会消耗服务商额度），不在失败后频繁重复。
    const stat={id:Date.now()+'-'+Math.random(),day:new Date().toLocaleDateString('en-CA'),residentId:r.id,provider:provider.name,model:r.model.model,purpose,ok:false,startedAt:Date.now()};
    this.state.stats.push(stat); this.state.stats=this.state.stats.slice(-10000); this.touch();
    const controller=new AbortController();this.pendingRequest=controller;
    try { const result=await this.llm.chatCompletion({provider,model:r.model.model,temperature:r.model.temperature,maxTokens:r.model.maxTokens,structured:true,system:this.prompt(r)+'\n'+extra,messages,signal:controller.signal,onDelta:()=>{}}); Object.assign(stat,{ok:true,tokens:(result.usage.promptTokens||0)+(result.usage.completionTokens||0),latency:result.latency}); return result.text; }
    catch(e) { stat.error=String(e.message).replaceAll(provider.apiKey||'\0','[已隐藏]'); throw new Error(stat.error); }
    finally { if(this.pendingRequest===controller)this.pendingRequest=null;this.touch(); }
  }
  async locked(residents,fn,{automatic=false}={}) {
    if(this.busy) throw new Error('已有模型或对话任务进行中，请稍后再试');
    this.busy=true;this.lockedIds=residents.map(r=>r.id);this.taskAutomatic=automatic;residents.forEach(r=>r.thinking=true);this.touch();
    try { return await fn(); } finally { residents.forEach(r=>{r.thinking=false;r.dialoguePending=false;});this.lockedIds=[];this.taskAutomatic=false;this.busy=false;this.touch(); }
  }
  async decide(id,{automatic=false}={}) {
    const r=this.entity(id); if(r.kind==='animal')return this.decidePet(id,{automatic}); if(!r.enabled) throw new Error('该人物未入住');
    if(r.isPlayer)throw new Error('主角由玩家亲自控制');
    if(!this.apiBound(r))throw new Error('请先为人物绑定 API 与模型');
    if(this.busy)throw new Error('已有模型或对话任务进行中，请稍后再试');
    if(!automatic&&this.state.controlledId===id)this.control(null);
    const intent=this.intent(r,automatic);r.target=null;r.moving=false;
    return this.locked([r],async()=>{
      r.decisionAt=Date.now();
      try {
        const expression=await this.modelExpression(r,'decision',[{role:'user',content:'继续过自己的生活：参考持续目标、职业日常、当前需求和真实日志，选择现在最想做、也能做到的一小步。没有持续目标时可拟定一个；说明此刻心声，有需要再说出一句话或邀请一位有空的邻居。只执行这一步，不把计划描述成已完成。'}]);
        if(!this.currentIntent(r,intent)){this.state.stats.at(-1).applied=false;return {discarded:true};}
        this.applyExpression(r,expression,{mode:'decision',automatic});this.state.stats.at(-1).applied=true;
        this.remember(r,`我决定${ACTIONS[expression.action]}：${expression.thought}`);return expression;
      } catch(e) { if(!this.currentIntent(r,intent)){this.state.stats.at(-1).applied=false;return {discarded:true};}this.event(`${r.name}模型决策失败：${e.message}；等待下一次模型决策`,'error',[id]);this.waitAfterError(r,intent);throw e; }
    },{automatic});
  }
  localLine(a,b,reply) {
    const topic=a.persona.likes.split(/[、，,]/)[0];
    if(reply) return /慢热|安静|腼腆/.test(a.persona.personality)?`嗯，${b.name}，我愿意试试。我们慢慢来吧。`:`${b.name}，好呀！等我忙完，咱们一起。`;
    if(a.energy<45) return `${b.name}，我有点累了，一起坐一会儿吗？`;
    if(/爱玩|慵懒|偷懒|分心/.test(a.persona.personality)) return `${b.name}，先歇五分钟吧？我想聊聊${topic}。`;
    return `${b.name}，今天怎么样？等下要不要一起${topic.includes('散步')?'散步':`聊聊${topic}`}？`;
  }
  async converse(aid,bid,automatic=false,opening=null) {
    const a=this.resident(aid),b=this.resident(bid); if(a.id===b.id||!a.enabled||!b.enabled) throw new Error('请选择两位不同的在场居民');
    if(automatic&&(a.isPlayer||b.isPlayer))throw new Error('主角对话需要玩家邀请');
    return this.locked([a,b],async()=>{
      a.target=b.target=null; a.action=b.action='chat';
      for(const r of [a,b]){r.actionVersion=(r.actionVersion||0)+1;r.dialoguePending=true;}
      a.meeting=b.meeting=null;
      const useModel=!automatic||this.state.autonomous;
      const realA=!opening&&useModel&&a.model.providerId!=='demo',realB=useModel&&b.model.providerId!=='demo';
      const intents=[this.intent(a,automatic&&useModel),this.intent(b,automatic&&useModel)];
      const live=()=>[a,b].every((r,i)=>this.currentIntent(r,intents[i]));
      if(automatic&&!useModel) this.event(`${a.name}与${b.name}按本地规则交谈（模型自治关闭）`,'system',[aid,bid]);
      let speaker=a;
      try {
        const needed=Number(realA)+Number(realB);
        if(needed&&this.dailyCalls()+needed>this.state.dailyLimit)throw new Error('今日剩余 API 次数不足以完成双方对话，请调整上限');
        const firstExpression=opening?parseExpression(JSON.stringify({action:'chat',thought:opening.thought,speech:opening.speech}),this.animationFor(a),{mode:'conversation'}):realA?await this.modelExpression(a,'conversation',[{role:'user',content:`主动对${b.name}（${b.occupation}，${b.persona.personality}）发起生活对话，同时表达心声并选择合适的动作。`}],'conversation'):null;
        if(!live()){if(realA)this.state.stats.at(-1).applied=false;return;}
        const first=firstExpression?.speech||this.localLine(a,b,false);
        if(firstExpression)this.applyExpression(a,firstExpression,{recordThought:!opening});else this.localSpeech(a,first);
        if(realA)this.state.stats.at(-1).applied=true;
        intents[0]=this.intent(a,automatic&&useModel);a.thinking=false;
        this.remember(a,`我对${b.name}说：${first.slice(0,240)}`); this.remember(b,`${a.name}对我说：${first.slice(0,240)}`);this.hear(b,a,first);this.touch();
        speaker=b;
        const secondExpression=realB?await this.modelExpression(b,'conversation',[{role:'user',content:`${a.name}（${a.occupation}）对你说：${first}\n请自然回应，不要替对方说话；返回你的心声、台词与相符的动作。`}],'conversation'):null;
        if(!live()){if(realB)this.state.stats.at(-1).applied=false;return;}
        const second=secondExpression?.speech||this.localLine(b,a,true);
        if(secondExpression)this.applyExpression(b,secondExpression);else this.localSpeech(b,second);
        if(realB)this.state.stats.at(-1).applied=true;
        this.remember(a,`${b.name}回应：${second.slice(0,240)}`); this.remember(b,`我回应${a.name}：${second.slice(0,240)}`);this.hear(a,b,second);
        const expressions=new Map([[aid,firstExpression],[bid,secondExpression]]),willing=new Map([[aid,opening?true:firstExpression?.interaction?.continue===true],[bid,secondExpression?.interaction?.continue===true]]);
        let lastLine=second,turns=2;
        for(let turn=3;willing.get(aid)&&willing.get(bid);turn++){
          const next=turn%2===1?a:b,other=next===a?b:a;
          if(!live()||!useModel||!this.apiBound(next))break;
          if(this.dailyCalls()>=this.state.dailyLimit){this.event('本次交流已用完今日可用的模型调用次数，先保留已有对话。','system',[aid,bid]);break;}
          speaker=next;next.thinking=true;
          const expression=await this.modelExpression(next,'conversation',[{role:'user',content:`你正在与${other.name}（${other.occupation}）自主交谈。对方刚说：${lastLine}\n这是第 ${turn} 轮发言，没有固定轮数上限。参考你自己的精力、心情、目标和兴趣自然回应，可以继续话题、争论或结束；用 interaction 表达你自己的感受与是否还想继续，不替对方作决定。`}],'conversation');
          if(!live()){this.state.stats.at(-1).applied=false;return;}
          this.applyExpression(next,expression);this.state.stats.at(-1).applied=true;next.thinking=false;intents[next===a?0:1]=this.intent(next,automatic&&useModel);
          this.remember(next,`我对${other.name}说：${expression.speech.slice(0,240)}`);this.remember(other,`${next.name}对我说：${expression.speech.slice(0,240)}`);
          this.hear(other,next,expression.speech);
          expressions.set(next.id,expression);willing.set(next.id,expression.interaction?.continue===true);lastLine=expression.speech;turns=turn;
        }
        const fallback=/讨厌|别烦|不喜欢|生气|拒绝/.test(first+second)?-2:2;
        const subjective=[a,b].some(r=>expressions.get(r.id)?.interaction);
        for(const [r,other] of [[a,b],[b,a]]){const expression=expressions.get(r.id),delta=expression?.interaction?.feeling??(subjective?0:fallback);r.relationships[other.id]=clamp((r.relationships[other.id]||0)+delta,-100,100);r.social=clamp(r.social+12,0,100);if(!expression?.emotion&&delta)this.recordEmotion(r,Emotions.apply(r,{change:delta,reason:`与${other.name}交流后，保留了${delta>0?'愉快':'不太舒服'}的感受。`,source:expression?.interaction?'api':'local',relatedId:other.id},this.state.clock));if(subjective)this.record(r,'relation',`我对${other.name}的印象变化 ${delta>0?'+':''}${delta}，当前好感 ${r.relationships[other.id]}。`,{source:expression?.interaction?'api':'local',relatedIds:[other.id]});}
        if(subjective)this.event(`${a.name}与${b.name}结束这段交流，各自保留了自己的感受。`,'relation');else this.event(`${a.name}与${b.name}的好感${fallback>0?'增加':'减少'} ${Math.abs(fallback)}`, 'relation',[aid,bid]);
        return {first,second,turns};
      } catch(e) { if(!live()){if(this.state.stats.at(-1))this.state.stats.at(-1).applied=false;return;}this.event(`对话中断：${e.message}`,'error',[aid,bid]);if(this.apiBound(speaker))this.waitAfterError(speaker,intents[speaker===a?0:1]);throw e; }
    },{automatic});
  }
  async chat(id,text) {
    const r=this.resident(id); const content=String(text||'').trim().slice(0,4000); if(!content) throw new Error('请输入消息');
    if(!r.enabled)throw new Error('该人物未入住');if(r.isPlayer)throw new Error('主角由玩家亲自控制');
    if(this.busy)throw new Error('已有模型或对话任务进行中，请稍后再试');
    if(this.state.controlledId===id)this.control(null);
    const intent=this.intent(r);r.target=null;r.moving=false;
    return this.locked([r],async()=>{
      r.messages.push({role:'user',content,time:this.state.clock});this.record(r,'speech',`镇长对我说：${content}`,{source:'player'});this.recordEmotion(r,Emotions.words(r,{id:'player',name:'镇长'},content,this.state.clock)); this.touch();
      try {
        const expression=r.model.providerId==='demo'?null:await this.modelExpression(r,'user-chat',r.messages.filter(m=>m.role!=='error').slice(-24).map(({role,content})=>({role,content})),'conversation');
        if(!this.currentIntent(r,intent)){if(expression)this.state.stats.at(-1).applied=false;throw new Error('人物状态已改变，本次回复已取消');}
        const reply=expression?.speech||`（本地规则）我刚在${ACTIONS[r.action]}呢。你说的“${content.slice(0,50)}”我记下啦！有空一起聊聊${r.persona.likes.split('、')[0]}吧。`;
        if(expression){this.applyExpression(r,expression);this.state.stats.at(-1).applied=true;}else this.localSpeech(r,reply);
        r.messages.push({role:'assistant',content:reply,...(expression?{action:expression.action,thought:expression.thought,source:'api'}:{}),time:this.state.clock});r.messages=r.messages.slice(-120);
        this.remember(r,`镇长说：${content.slice(0,180)}；我回应：${reply.slice(0,180)}`);return reply;
      }
      catch(e) { r.messages.push({role:'error',content:e.message,time:this.state.clock});r.messages=r.messages.slice(-120);this.event(`${r.name}回复失败：${e.message}`,'error',[id]);if(this.apiBound(r))this.waitAfterError(r,intent);throw e; }
    });
  }
}
module.exports={Town,clamp};
