'use strict';
(function(root){
  const clamp=(n,a=0,b=100)=>Math.min(b,Math.max(a,Number(n)||0));
  const recovering=Object.freeze(['rest','slack','doze','lie_down']);
  const patterns=Object.freeze({share:'交流分享',focus:'专注爱好',exercise:'活动身体',alone:'安静独处',confide:'向熟人倾诉'});
  const hash=s=>[...String(s)].reduce((n,c)=>(n*33+c.charCodeAt(0))>>>0,5381);
  function traits(r){
    const p=r.persona?.personality||'',likes=r.persona?.likes||'',seed=hash(r.catalogId||r.asset||r.id);
    let sociability=40+seed%25,sensitivity=40+(seed>>>4)%30,diligence=45+(seed>>>8)%30;
    if(/健谈|开朗|热情|活泼|豪爽|爱分享|外向|元气|热闹/.test(p))sociability+=25;
    if(/安静|独立|独处|慢热|腼腆|话少|木讷|克制/.test(p))sociability-=25;
    if(/敏感|细腻|浪漫|腼腆/.test(p))sensitivity+=20;
    if(/理性|冷静|乐观|乐天|随和/.test(p))sensitivity-=15;
    if(/认真|严谨|踏实|守时|责任|可靠|原则|细致/.test(p))diligence+=25;
    if(/偷懒|慵懒|分心|爱玩|随性/.test(p))diligence-=25;
    const positive=/运动|跑步|晨跑|骑车|骑行/.test(likes)?'exercise':/独处|阅读|文学|读书|画画|木工|下棋/.test(likes)&&sociability<65?'focus':sociability>60?'share':seed%2?'focus':'exercise';
    const negative=/照顾朋友|关心伙伴|善于倾听|体贴|喜爱动物|照顾邻里/.test(p+likes)?'confide':/独立|独处|安静|木讷/.test(p)?'alone':/运动|跑步|骑车/.test(likes)&&seed%3===0?'exercise':sensitivity>60&&seed%2===0?'confide':'alone';
    return {sociability:clamp(sociability),sensitivity:clamp(sensitivity),diligence:clamp(diligence),positive,negative};
  }
  function label(value){return value>=80?'愉快':value>=62?'舒心':value>=42?'平静':value>=25?'低落':'烦闷';}
  function mood(value){return value>=75?'happy':value<42?'sad':'calm';}
  function normalize(r,clock=0){
    const e=r.emotion&&typeof r.emotion==='object'&&!Array.isArray(r.emotion)?r.emotion:{};
    return {stress:clamp(e.stress??20),workStreak:clamp(e.workStreak,0,360),reason:typeof e.reason==='string'?e.reason.slice(0,240):'此刻的心情还没有新的记录。',updatedAt:Number.isFinite(e.updatedAt)?e.updatedAt:clock,
      recent:Array.isArray(e.recent)?e.recent.filter(x=>x&&Number.isFinite(x.time)&&typeof x.reason==='string'&&Number.isFinite(x.change)).slice(-8):[],
      lastLoggedValue:Number.isFinite(e.lastLoggedValue)?clamp(e.lastLoggedValue):clamp(r.happiness??75),lastLoggedStress:Number.isFinite(e.lastLoggedStress)?clamp(e.lastLoggedStress):clamp(e.stress??20),lastLoggedAt:Number.isFinite(e.lastLoggedAt)?e.lastLoggedAt:clock,
      observed:e.observed&&typeof e.observed==='object'&&!Array.isArray(e.observed)?Object.fromEntries(Object.entries(e.observed).filter(([,v])=>Number.isFinite(v)).slice(-24)):{} };
  }
  function valid(e){return !!e&&typeof e==='object'&&!Array.isArray(e)&&Number.isFinite(e.stress)&&e.stress>=0&&e.stress<=100&&Number.isFinite(e.workStreak)&&e.workStreak>=0&&e.workStreak<=360&&typeof e.reason==='string'&&e.reason.length<=240&&['updatedAt','lastLoggedAt','lastLoggedValue','lastLoggedStress'].every(k=>Number.isFinite(e[k])&&e[k]>=0)&&e.lastLoggedValue<=100&&e.lastLoggedStress<=100&&Array.isArray(e.recent)&&e.recent.length<=8&&e.recent.every(x=>x&&Number.isFinite(x.time)&&x.time>=0&&Number.isFinite(x.change)&&typeof x.reason==='string'&&x.reason.length<=240)&&e.observed&&typeof e.observed==='object'&&!Array.isArray(e.observed)&&Object.keys(e.observed).length<=24&&Object.values(e.observed).every(x=>Number.isFinite(x)&&x>=0);}
  function apply(r,{change=0,stress=0,reason,source='life',relatedId=null},clock){
    if(r.kind==='animal'||!reason)return null;
    r.emotion ||= normalize(r,clock);const e=r.emotion,before=r.happiness;
    r.happiness=clamp(before+clamp(change,-12,12));e.stress=clamp(e.stress+clamp(stress,-12,12));
    const actual=Math.round((r.happiness-before)*10)/10;
    e.reason=String(reason).slice(0,240);e.updatedAt=clock;e.recent.push({time:clock,reason:e.reason,change:actual,source,relatedId});e.recent=e.recent.slice(-8);
    r.mood=mood(r.happiness);e.lastLoggedValue=r.happiness;e.lastLoggedStress=e.stress;e.lastLoggedAt=clock;
    return {change:actual,stress:e.stress,value:r.happiness,reason:e.reason,source,relatedId};
  }
  function advance(r,d,clock,{alone=false,moving=false}={}){
    if(r.kind==='animal')return null;r.emotion ||= normalize(r,clock);const e=r.emotion,p=traits(r),a=moving?'walk':r.action;
    let gain=0,strain=0,reason='';
    if(a==='work'){e.workStreak=clamp(e.workStreak+d,0,360);gain=(p.diligence-65)*.002-.045;strain=.25+(e.workStreak>35?.15:0);reason=e.workStreak>35?'工作持续了一阵，开始觉得压力和疲惫。':'做了一段工作，也在留意自己的节奏。';}
    else{if(recovering.includes(a)||a==='play')e.workStreak=Math.max(0,e.workStreak-d*.6);
      if(a==='slack'){gain=p.diligence>75?-.08:.13;strain=-.38;reason=p.diligence>75?'偷闲缓了缓压力，但惦记着还没忙完的事情。':'暂时把工作放下，偷个闲，压力松了一点。';}
      else if(a==='doze'){gain=.14;strain=-.5;reason='打了个盹，困意和紧绷感正在缓解。';}
      else if(a==='lie_down'){gain=.12;strain=-.45;reason='躺下来休息，给身体和心情一点恢复时间。';}
      else if(a==='rest'){gain=.1;strain=-.32;reason='休息了一会儿，慢慢放松下来。';}
      else if(a==='play'){gain=p.positive==='focus'&&alone?.28:.2;strain=-.23;reason=alone&&p.positive==='focus'?'自己做喜欢的事情，安静也让人满足。':'做喜欢的事情，心情轻松了一点。';}
      else if(a==='walk'){gain=p.positive==='exercise'||p.negative==='exercise'?.17:.08;strain=-.16;reason='走动活动了一阵，心情和身体都舒展了一点。';}
      else if(a==='chat'){gain=.035;strain=p.sociability<30?.03:-.06;reason='交流占用了些精力，也带来新的感受。';}
      else if(a==='idle'){gain=alone&&p.negative==='alone'&&r.happiness<42?.1:(50-r.happiness)*.002;strain=-.04;reason=alone&&r.happiness<42?'安静待一会儿，不必急着回应别人。':'此刻安静待着，心情缓慢回稳。';}}
    if(r.energy<20&&!recovering.includes(a)&&a!=='idle'){gain-=.16;strain+=.08;reason+=' 身体很累，心情也受到影响。';}
    r.happiness=clamp(r.happiness+gain*d);e.stress=clamp(e.stress+strain*d);r.mood=mood(r.happiness);
    if(clock-e.lastLoggedAt>=5&&(Math.abs(r.happiness-e.lastLoggedValue)>=4||Math.abs(e.stress-e.lastLoggedStress)>=6||label(r.happiness)!==label(e.lastLoggedValue))){
      const change=r.happiness-e.lastLoggedValue,recorded=apply(r,{change:0,reason,source:'life'},clock);if(recorded){recorded.change=Math.round(change*10)/10;e.recent.at(-1).change=recorded.change;}return recorded;
    }return null;
  }
  function words(r,speaker,text,clock){
    const p=traits(r),s=String(text),f=.6+p.sensitivity/100;let change=0,stress=0;
    if(/讨厌你|你真没用|你没用|滚开|滚吧|闭嘴|别烦我|你真差|蠢货/.test(s)){change=-7*f;stress=5;}
    else if(/辛苦了|谢谢你|谢谢|做得很好|你很棒|陪着你|陪你|愿意听|可以跟我说|别太勉强/.test(s)){change=3*f;stress=-3;}
    else if(/不同意|不完全同意|不赞同/.test(s)&&p.sensitivity>65){change=-.8;stress=.5;}
    if(!change&&!stress)return null;
    return apply(r,{change,stress,reason:`听到${speaker.name}说“${s.slice(0,70)}”，${change>0?'感到被关心或认可':change<-2?'有些受伤和紧张':'产生一点分歧带来的不安'}。`,source:'heard',relatedId:speaker.id},clock);
  }
  function witness(r,actor,action,clock){
    if(r.kind==='animal'||recovering.includes(r.action)&&['doze','lie_down'].includes(r.action))return null;
    r.emotion ||= normalize(r,clock);const e=r.emotion,key=actor.id+':'+action;if(Number.isFinite(e.observed[key])&&clock-e.observed[key]<15)return null;
    const p=traits(r),close=(r.relationships[actor.id]||0)>=15;let change=0,stress=0,reason='';
    if(['cheer','jump','chat'].includes(action)&&p.sociability<35){change=-.7;stress=1.2;reason=`附近${actor.name}比较热闹，我现在更想安静一点。`;}
    else if(['play','cheer','greet'].includes(action)&&close){change=1.5;reason=`看到熟悉的${actor.name}在${action==='greet'?'打招呼':'开心活动'}，自己的心情也轻快了一点。`;}
    else if(action==='slack'&&r.action==='work'&&p.diligence>75){change=-1;stress=1;reason=`忙碌时看到${actor.name}偷闲，心里有一点不平衡。`;}
    else if(action==='work'&&close&&p.diligence>70){change=.7;reason=`看到熟悉的${actor.name}认真做事，也受到一点鼓舞。`;}
    if(!reason)return null;e.observed[key]=clock;e.observed=Object.fromEntries(Object.entries(e.observed).slice(-24));return apply(r,{change,stress,reason,source:'witness',relatedId:actor.id},clock);
  }
  function intention(r,neighbors=[]){
    const p=traits(r),low=r.happiness<42,pattern=low?p.negative:p.positive;
    const confidants=neighbors.filter(n=>n.id!==r.id&&!n.isPlayer&&!n.thinking&&!n.meeting&&!['doze','lie_down'].includes(n.action)&&(r.relationships[n.id]||0)>=15).sort((a,b)=>(r.relationships[b.id]||0)-(r.relationships[a.id]||0)).slice(0,3).map(n=>({id:n.id,name:n.name,relationship:r.relationships[n.id]}));
    return {value:Math.round(r.happiness),label:label(r.happiness),stress:Math.round(r.emotion?.stress||0),tired:r.energy<32,reason:r.emotion?.reason||'',traits:p,pattern,preference:patterns[pattern],confidants,
      guidance:low&&pattern==='confide'?(confidants.length?'心情低落时，可以找信任的熟人倾诉；由对方决定是否回应。':'低落时希望有人理解，暂时没有足够熟悉的空闲邻居，可以先安静恢复。'):low&&pattern==='alone'?'低落时偏好独处，暂时不必勉强社交。':pattern==='focus'?'心情好也可以自己做喜欢的事情，不必一定找人分享。':pattern==='exercise'?'可以通过走动、运动和游玩调节心情。':'有余力时愿意分享或邀请，但仍可改变主意。'};
  }
  function localPlan(r,clock,neighbors=[],random=Math.random){
    const hour=(clock/60)%24,night=hour>=21||hour<6,p=traits(r),i=intention(r,neighbors);
    if(r.energy<16)return {action:'lie_down'};
    if(r.energy<35)return {action:night?'lie_down':'doze'};
    if(night&&r.energy<70)return {action:'lie_down'};
    if((r.emotion?.stress||0)>65||(r.emotion?.workStreak||0)>30&&p.diligence<60)return {action:night?'lie_down':'slack'};
    if(r.happiness<42){if(p.negative==='confide'&&i.confidants.length)return {action:'chat',partnerId:i.confidants[0].id};if(p.negative==='exercise')return {action:random()<.5?'walk':'play'};return {action:random()<.55?'rest':'play'};}
    if(r.happiness>=80){if(p.positive==='share'&&r.social<85&&neighbors.length>1)return {action:'chat'};if(p.positive==='exercise')return {action:random()<.5?'walk':'play'};if(p.positive==='focus')return {action:hour>=9&&hour<17&&p.diligence>75&&random()<.55?'work':'play'};}
    if(hour>=9&&hour<17&&/偷懒|慵懒|分心/.test(r.persona?.personality||'')&&random()<.18)return {action:'slack'};
    return null;
  }
  const api={recovering,patterns,traits,label,mood,normalize,valid,apply,advance,words,witness,intention,localPlan};
  if(typeof module==='object'&&module.exports)module.exports=api;else root.TownEmotions=api;
})(typeof globalThis==='object'?globalThis:this);
