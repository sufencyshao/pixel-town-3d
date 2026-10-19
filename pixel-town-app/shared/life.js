'use strict';
(function(root){
  const defaults=Object.freeze({
    name:'像素小镇',
    background:'这里是一座逐渐熟悉彼此的小镇。居民各有职业、兴趣、性格和独立生活，不必总等镇长安排。可以从一件具体的小事开始，在工作、休息、爱好和认识邻居之间找到自己的节奏。',
    values:'尊重彼此的意愿和界限；记得别人真正说过的话；邀请可以被拒绝；允许独处和休息；主动关心、分享观察，也可以表达不同意见。',
    facts:'居民的姓名、人设、模型、记忆与关系各自独立。人物档案中的职业和地点提供生活背景；当前场景使用工作、游玩、相遇和休息四个公共区域。'
  });
  const text=(v,n)=>typeof v==='string'?v.slice(0,n):'';
  const keys={name:40,background:2400,values:1600,facts:3000};
  function world(value={}){return Object.fromEntries(Object.entries(keys).map(([k,n])=>[k,typeof value[k]==='string'?text(value[k],n):defaults[k]]));}
  function validateWorld(value){
    if(!value||typeof value!=='object'||Array.isArray(value)||Object.keys(value).some(k=>!Object.hasOwn(keys,k)))throw new Error('小镇资料格式无效');
    for(const [k,n] of Object.entries(keys))if(typeof value[k]!=='string'||value[k].length>n||(k==='name'&&!value[k].trim()))throw new Error('小镇资料字段或长度无效');
    return Object.fromEntries(Object.keys(keys).map(k=>[k,value[k].trim()]));
  }
  function defaultProfile(r){
    const likes=(r.persona?.likes||'观察小镇、认识邻居').split(/[、，,]/).filter(Boolean);
    const job=r.occupation||'小镇居民';
    return {
      aspiration:`在小镇建立自己的生活，认真对待${job}的日常，通过${likes.slice(0,2).join('、')}积累经验，慢慢认识愿意交流的邻居。`,
      routine:`结合当前性格与职业日常安排时间；精力不足先休息，有余力时做一件与${likes[0]||'自己的兴趣'}有关的小事；交流前尊重对方是否有空。`,
      custom:false,focus:null,history:[]
    };
  }
  function validFocus(g){return !!g&&typeof g==='object'&&!Array.isArray(g)&&typeof g.title==='string'&&!!g.title.trim()&&g.title.length<=80&&typeof g.reason==='string'&&g.reason.length<=120&&['ongoing','completed','abandoned'].includes(g.status)&&['startedAt','updatedAt'].every(k=>Number.isFinite(g[k])&&g[k]>=0);}
  function profile(value,r){
    const d=defaultProfile(r),v=value&&typeof value==='object'?value:{};
    return {...d,aspiration:typeof v.aspiration==='string'?text(v.aspiration,300):d.aspiration,routine:typeof v.routine==='string'?text(v.routine,500):d.routine,custom:v.custom===true,focus:validFocus(v.focus)?structuredClone(v.focus):null,history:Array.isArray(v.history)?v.history.filter(validFocus).slice(-12).map(g=>structuredClone(g)):[]};
  }
  function validateProfile(value){
    if(!value||typeof value!=='object'||Array.isArray(value)||Object.keys(value).some(k=>!['aspiration','routine','resetGoal'].includes(k))||typeof value.aspiration!=='string'||!value.aspiration.trim()||value.aspiration.length>300||typeof value.routine!=='string'||value.routine.length>500||(value.resetGoal!==undefined&&typeof value.resetGoal!=='boolean'))throw new Error('生活方向需要 1–300 字，日常参考最多 500 字');
    return {aspiration:value.aspiration.trim(),routine:value.routine.trim(),resetGoal:value.resetGoal===true};
  }
  function minute(value){const m=String(value||'').match(/^(\d{2}):(\d{2})$/);return m&&+m[1]<24&&+m[2]<60?+m[1]*60 + +m[2]:null;}
  function routineAt(r,clock){
    const now=((Math.floor(clock)%1440)+1440)%1440;
    const row=(Array.isArray(r.schedule)?r.schedule:[]).find(s=>{const a=minute(s?.start),b=minute(s?.end);return a!==null&&b!==null&&(a<b?now>=a&&now<b:now>=a||now<b);});
    return row?{time:`${row.start}–${row.end}`,backgroundPlace:text(row.location,100),reference:text(row.behavior,260)}:null;
  }
  function guide(zones={}){
    return `你在一个持续运行的 2D 像素生活应用里扮演自己的角色。你表达人物的意愿，不充当解释 API 的客服。\n`+
      `实际功能：角色可以行走、工作、休息、偷懒、打盹、躺下、游玩、表达情绪、邀请邻居交流；镇长可以聊天、管理居民和动物、编辑档案、手动操控和调整游戏时间。主角由玩家控制。\n`+
      `场景坐标 x=90–1510、y=120–910；公共区域：${JSON.stringify(zones)}。档案中的咖啡馆、图书馆、住宅等是背景地点，目前由公共区域承载职业日常与兴趣活动。移动只需给实际坐标。\n`+
      `工作和游玩是可执行的生活状态与动画。职业可以影响话题、练习和观察，但应用目前没有职业产出、建筑开关、货币、交易、物品库存或制造任务；不能把打算做的物品或未完成的事情说成已经获得或交付。\n`+
      `游戏时钟驱动昼夜，06:00 日出、18:00 日落，暂停和倍速会影响动作推进。只有 API 返回的可用动作会被执行；不能替别人行动、替别人回答、操作设置或强迫主角。\n`+
      `每次只决定下一步。可维持或调整自己的持续目标：从人设、兴趣、精力、当前心情与压力、个人情绪倾向、社交需要、当前时段和真实经历中选一个具体目的，再选择支持它的动作。不要机械循环挥手、点头、拒绝；不必每次说话。\n`+
      `人物交流可以分享今天亲眼所见、追问别人真正说过的事、介绍自己的兴趣、提出邀请或表达界限。也可以不赞同、争论，或因为不投缘结束交流；你有自己的立场，不必事事答应。可邀请名单表示现在有空的人。远处发生的事、他人的私人心声和未在场人物不算亲眼见闻。\n`+
      `日志区分行动开始、移动到达、行为结束、目击、心声、台词与目标计划。计划不等于完成；行为结束也不等于虚构物品制作完成。根据日志和当前状态决定继续、休息、换话题或放弃，不能编造昨天的经历。`;
  }
  const api={defaults,world,validateWorld,defaultProfile,profile,validateProfile,routineAt,validFocus,guide};
  if(typeof module==='object'&&module.exports)module.exports=api;else root.TownLife=api;
})(typeof globalThis==='object'?globalThis:this);
