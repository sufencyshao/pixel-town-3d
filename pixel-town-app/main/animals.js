'use strict';
const worldTime=require('../shared/world-time');
const ANIMAL_ACTIONS = Object.freeze({ idle:'观察环境', observe:'警戒观察', flee:'避开刺激', walk:'行走', run:'小跑', rest:'休息', sleep:'睡眠',
  eat:'进食', drink:'饮水', sniff:'嗅闻', groom:'梳理毛羽', scratch:'抓挠', play:'探索玩具',
  hop:'跳行', fly:'飞行', perch:'栖停', peck:'啄食', forage:'觅食', graze:'采食', swim:'游动',
  hide:'躲藏', explore:'探索', vocalize:'自然鸣叫', stretch:'舒展', flap:'振翅', pounce:'扑动',
  chew:'啃咬', dig:'挖掘', roll:'翻滚', wag:'摆尾', bask:'晒暖', burrow:'掘穴' });
const SENSES = ['smell', 'sound', 'motion', 'light', 'touch', 'temperature'];
const NEEDS = ['food', 'water', 'rest', 'safety', 'exploration'];
function allowedAnimalActions(p) {
  const specified = p.animal?.allowedActions;
  return Array.isArray(specified) ? specified.filter(a => Object.hasOwn(ANIMAL_ACTIONS, a)) : ['idle', 'walk', 'rest', 'eat', 'drink'];
}
function parseAnimalDecision(text, p) {
  const match = String(text).match(/\{[\s\S]*\}/);
  const value = JSON.parse(match ? match[0] : text);
  if (!value || Object.keys(value).some(k => !['action', 'senses', 'need'].includes(k)) ||
    !allowedAnimalActions(p).includes(value.action) || !NEEDS.includes(value.need) ||
    !Array.isArray(value.senses) || value.senses.length > 6 || value.senses.some(s => !SENSES.includes(s)))
    throw new Error('动物模型必须返回允许的感官、需求和物种动作');
  return { action:value.action, senses:[...new Set(value.senses)], need:value.need };
}
function animalPrompt(p, state) {
  return `你是动物行为控制器。模拟真实动物 ${p.animal?.species || ''}，品种 ${p.animal?.breed || ''}，花色 ${p.animal?.coat || ''}，体型 ${p.animal?.bodySize || ''}。\n` +
    `该动物的感官特征：${JSON.stringify(p.animal?.senses || {})}；自然行为：${JSON.stringify(p.animal?.behavior || {})}；个体气质：${p.persona.personality}。\n` +
    `局部可见运动与距离（只提供生物刺激，不推断人的意图）：${JSON.stringify([...state.residents,...(state.pets||[]),...(state.player?[state.player]:[])].filter(r=>r.enabled&&r.id!==p.id&&Math.hypot(r.x-p.x,r.y-p.y)<260).map(r=>({stimulusClass:r.kind==='animal'?'animal':'human',species:r.animal?.species,bodySize:r.animal?.bodySize||'human',distance:Math.round(Math.hypot(r.x-p.x,r.y-p.y)),moving:!!r.moving,relativeX:Math.round(r.x-p.x),relativeY:Math.round(r.y-p.y)})))}。\n` +
    `时间 ${worldTime.format(state.clock)}，光照时段：${worldTime.sample(state.clock).label}（日出06:00，日落18:00）；精力 ${Math.round(p.energy)}；生理需求 ${JSON.stringify(p.needs)}。\n` +
    '只依据动物生理、感官与物种习性决策。不得赋予人类职业、社会角色、语言、思想独白或人类对话；不得说人话。\n' +
    `只返回 JSON，恰含三个键：{"action":"${allowedAnimalActions(p).join('|')}","senses":["${SENSES.join('|')}"],"need":"${NEEDS.join('|')}"}。senses 只选适用的英文感官代码。`;
}
module.exports = { ANIMAL_ACTIONS, allowedAnimalActions, parseAnimalDecision, animalPrompt };
