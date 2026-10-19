'use strict';
const { labels, available } = require('../shared/actions');

function choices(animation, mode, partners = []) {
  return available(animation, mode).filter(action => mode !== 'decision' || action !== 'chat' || partners.length);
}

function behaviorPrompt(animation, { mode = 'decision', partners = [], zones = {}, currentGoal = null } = {}) {
  const actions = choices(animation, mode, partners);
  const descriptions = actions.map(action => `${action}=${labels[action]}`).join('，');
  const emotion = '可额外返回 emotion:{"change":整数,"stress":整数,"reason":"此刻为什么产生这种感受"}。change 为 -6 至 6 的个人心情变化，stress 为 -6 至 6 的压力变化，reason 1–120 字。结合真实经历、当前心情、你的性格和关系表达，不必总开心或把分歧当侮辱；这是自己的感受，不替别人定义感受。';
  const common = emotion + `只输出一个 JSON 对象，不加解释或 Markdown。格式：{"action":"${actions.join('|')}","thought":"此刻一句简短心声","speech":"真正说出口的话"}。action 必须是一个值，当前可用动作：${descriptions}。thought 是虚构人物此刻的想法，1–120 字，不输出推理过程；speech 是对外台词，最多 600 字。想法与台词分别表达，动作与情绪、台词保持一致。赞同可以 nod，拒绝可以 shake_head，也可选择其他合适动作，不要每句话都做同一动作。点头播放一次；摇头使用现有左右约 30° 快速两下的动画。不能创造动作、改变形象、替别人行动或说话。`+
    `可额外返回 goal:{"title":"一个具体、可通过当前动作推进的小目标","reason":"为什么想做","status":"ongoing"}。title 1–80 字，reason 1–120 字；维持同一目标沿用原 title，已有目标合适时不必换。没有目标时主动提出一个；有需要可省略 goal 保持原目标。只有当前目标已存在且日志支持自评时才可用 completed 或 abandoned，并沿用当前 title。当前目标：${JSON.stringify(currentGoal)}。目标是人物计划和自评，不作为外部事件完成的证据；不要声称新提出的目标已完成。`;
  if (mode === 'conversation') return common + '你正在交谈，speech 必须有内容，1–3 句。动作在原地表达；不要返回 destination 或 partnerId。交谈时请同时返回 interaction:{"feeling":整数,"continue":布尔值}。feeling 为 -3 至 3，是你对这次交流的主观好感变化；continue 表示你是否还想聊下一轮。愿意继续可 true，已经聊够、想回去做事或不舒服可 false。可以好奇、赞同、质疑、反驳或争执，不必总迎合对方；分歧不一定等于讨厌。对话没有固定轮数上限，愿意时继续，尊重任一方的结束意愿，不替对方回答。省略 interaction 时本次交流按原两轮结束。';
  return common + `slack 是暂时偷闲，留在原处缓解工作压力；doze 是原地或安静处短暂打盹；lie_down 是到安静处躺下恢复，夜晚可用于睡觉。疲劳、长时间工作、困意或想休息时可以选择，正在恢复时不必马上又工作。心情好坏参考个人情绪倾向：有些人想交流分享，有些人想独自做爱好或运动；低落时有些人想独处，有些人想向关系较好的熟人倾诉。倾向不是强制命令，你可因实际情况改变安排。选择下一步生活行为，可以为了职业日常、锻炼身体、自己的兴趣、结识邻居或独处恢复而行动。你可以主动找有空的人交流，并不需要镇长先打招呼。没有想说的话时 speech 为空字符串。walk 必须额外给出 destination:{"x":数字,"y":数字}，坐标范围 x=90–1510、y=120–910；工作、休息、游玩、打盹、躺下可以指定坐标，否则走向对应场所，其他动作留在原地。work、rest、play、idle、slack、doze、lie_down 可额外给出 duration（1–180 整数游戏分钟），表示到达后这段行为持续多久；不提供时采用约半小时的小步安排，点头与摇头仍按原单次时长。场所坐标：${JSON.stringify(zones)}。选择 chat 时必须额外给出 partnerId，并用 speech 发出邀请；可邀请人物：${partners.map(r=>`${r.id}=${r.name}`).join('，')||'无'}。不邀请主角，不选择未在场或忙碌人物。`;
}

function parseExpression(text, animation, { mode = 'decision', partners = [], currentGoal = null } = {}) {
  const invalid = detail => { throw new Error('模型没有返回有效的动作与表达：' + detail); };
  if (typeof text !== 'string' || text.length > 10000) invalid('需要 JSON 对象');
  let input = text.trim();
  const fenced = input.match(/^```(?:json)?\s*\n?([\s\S]*?)\n?```$/i);
  if (fenced) input = fenced[1].trim();
  let data;
  try { data = JSON.parse(input); } catch { invalid('JSON 格式错误'); }
  if (!data || typeof data !== 'object' || Array.isArray(data)) invalid('需要 JSON 对象');
  if (Object.keys(data).some(key => !['action','thought','speech','destination','partnerId','goal','interaction','duration','emotion'].includes(key))) invalid('包含未知字段');
  if (!choices(animation, mode, partners).includes(data.action)) invalid('动作没有可用素材或不适合当前场景');
  if (typeof data.thought !== 'string' || !data.thought.trim() || data.thought.length > 120) invalid('心声需要 1–120 字');
  // Older life-decision prompts only returned action and thought; silence remains valid.
  const speech = data.speech === undefined && mode === 'decision' ? '' : data.speech;
  if (typeof speech !== 'string' || speech.length > 600 || (mode === 'conversation' && !speech.trim())) invalid('台词格式或长度错误');
  let destination = null, partnerId = null;
  if (data.destination !== undefined && data.destination !== null) {
    const point = data.destination;
    if (mode !== 'decision' || !['walk','work','rest','play','doze','lie_down'].includes(data.action) || !point || typeof point !== 'object' || Array.isArray(point) ||
        Object.keys(point).length !== 2 || !Object.hasOwn(point,'x') || !Object.hasOwn(point,'y') ||
        !Number.isFinite(point.x) || !Number.isFinite(point.y) || point.x < 90 || point.x > 1510 || point.y < 120 || point.y > 910) invalid('移动目的地无效');
    destination = { x:point.x, y:point.y };
  }
  if (data.action === 'walk' && !destination) invalid('散步需要目的地');
  if (data.partnerId !== undefined && data.partnerId !== null) {
    if (mode !== 'decision' || data.action !== 'chat' || typeof data.partnerId !== 'string' || !partners.some(r=>r.id===data.partnerId)) invalid('邀请对象无效');
    partnerId = data.partnerId;
  }
  if (mode === 'decision' && data.action === 'chat' && (!partnerId || !speech.trim())) invalid('交谈需要邀请对象和台词');
  let goal;
  if(data.goal!==undefined){
    const g=data.goal;
    if(!g||typeof g!=='object'||Array.isArray(g)||Object.keys(g).length!==3||Object.keys(g).some(k=>!['title','reason','status'].includes(k))||typeof g.title!=='string'||!g.title.trim()||g.title.length>80||typeof g.reason!=='string'||!g.reason.trim()||g.reason.length>120||!['ongoing','completed','abandoned'].includes(g.status))invalid('目标格式或长度无效');
    if(g.status!=='ongoing'&&(!currentGoal||currentGoal.status!=='ongoing'||currentGoal.title!==g.title.trim()))invalid('只能结束当前持续目标');
    goal={title:g.title.trim(),reason:g.reason.trim(),status:g.status};
  }
  let interaction;
  if(data.interaction!==undefined){const i=data.interaction;if(mode!=='conversation'||!i||typeof i!=='object'||Array.isArray(i)||Object.keys(i).length!==2||Object.keys(i).some(k=>!['feeling','continue'].includes(k))||!Number.isInteger(i.feeling)||i.feeling<-3||i.feeling>3||typeof i.continue!=='boolean')invalid('交流意愿格式无效');interaction={feeling:i.feeling,continue:i.continue};}
  let emotion;
  if(data.emotion!==undefined){const e=data.emotion;if(!e||typeof e!=='object'||Array.isArray(e)||Object.keys(e).length!==3||Object.keys(e).some(k=>!['change','stress','reason'].includes(k))||!Number.isInteger(e.change)||Math.abs(e.change)>6||!Number.isInteger(e.stress)||Math.abs(e.stress)>6||typeof e.reason!=='string'||!e.reason.trim()||e.reason.length>120)invalid('心情表达格式无效');emotion={change:e.change,stress:e.stress,reason:e.reason.trim()};}
  if(data.duration!==undefined&&(mode!=='decision'||!['work','rest','play','idle','slack','doze','lie_down'].includes(data.action)||!Number.isInteger(data.duration)||data.duration<1||data.duration>180))invalid('本段行为时长无效');
  return { action:data.action, thought:data.thought.trim(), speech:speech.trim(), destination, partnerId,...(goal?{goal}:{}),...(interaction?{interaction}:{}),...(emotion?{emotion}:{}),...(data.duration===undefined?{}:{duration:data.duration}) };
}

module.exports = { choices, behaviorPrompt, parseExpression };
