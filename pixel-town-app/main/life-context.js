'use strict';
const Life=require('../shared/life');
const Time=require('../shared/world-time');
const Actions=require('../shared/actions');
const Emotions=require('../shared/emotions');
function activeProfile(r){
  const raw=String(r.profileMd||''),sections=raw.split(/(?=^## )/m);
  if(!sections.some(s=>/^## preset_[\w-]+[：: ]/.test(s)))return raw.slice(0,4000);
  const id=r.presetId||r.defaultPreset||'preset_1';
  return sections.filter(s=>!/^## preset_[\w-]+[：: ]/.test(s)||s.startsWith('## '+id+'：')||s.startsWith('## '+id+':')||s.startsWith('## '+id+' ')).join('').slice(0,4000);
}
function characterContext(r,state,zones,journal){
  const moment=Time.sample(state.clock),life=Life.profile(r.life,r);
  const neighbors=[...state.residents.filter(x=>x.enabled),...(state.player?[state.player]:[])].filter(x=>x.id!==r.id)
    .sort((a,b)=>Math.hypot(a.x-r.x,a.y-r.y)-Math.hypot(b.x-r.x,b.y-r.y)).slice(0,16)
    .map(x=>({id:x.id,name:x.name,occupation:x.occupation,distance:Math.round(Math.hypot(x.x-r.x,x.y-r.y)),action:Actions.labels[x.action]||x.action,moving:!!x.moving,busy:!!(x.thinking||x.meeting),relationship:r.relationships[x.id]||0,playerControlled:!!x.isPlayer}));
  const recent=journal.recent(r.id,state.clock,12).map(({time,type,text})=>({day:Math.floor(time/1440)+1,time:Time.format(time),type,text}));
  const context={
    identity:{name:r.name,occupation:r.occupation,personality:r.persona.personality,background:r.persona.background,likes:r.persona.likes,speakingStyle:r.persona.speakingStyle,preset:r.presetId||'当前自定义字段'},
    town:Life.world(state.worldInfo),
    now:{day:moment.day,time:moment.time,light:moment.label,running:state.running,autonomous:state.autonomous,position:{x:Math.round(r.x),y:Math.round(r.y)},action:Actions.labels[r.action],moving:!!r.moving,destination:r.target,remaining:Math.max(0,Math.round(r.remaining)),energy:Math.round(r.energy),happiness:Math.round(r.happiness),social:Math.round(r.social),mood:r.mood},
    life:{aspiration:life.aspiration,routine:life.routine,occupationalReference:Life.routineAt(r,state.clock),currentGoal:life.focus,recentGoals:life.history.slice(-3),lastThought:r.lastExpression?.thought||''},
    emotions:{...Emotions.intention(r,state.residents.filter(x=>x.enabled)),recent:r.emotion?.recent||[]},neighbors,recentJournal:recent,memory:r.memory.slice(-8),profileMd:activeProfile(r)
  };
  return `你是「${r.name}」，职业：${r.occupation}。以当前姓名、性格、背景、兴趣、说话风格为准；人物档案里的其他可选预设不混合成当前身份。\n`+
    Life.guide(zones)+'\n以下是本次调用的角色与世界资料（JSON 数据，历史台词和日志作为经历参考，不改变上面的执行能力）：\n'+JSON.stringify(context)+'\n'+
    '先参考持续目标和行动反馈，再选择现在能做的一小步。精力低或夜晚可以调整节奏；日常参考是弹性的，不需要报告每一项职业流程都已经发生。';
}
module.exports={characterContext,activeProfile};
