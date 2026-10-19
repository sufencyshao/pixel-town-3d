'use strict';
const fs = require('fs');
const path = require('path');
const appearance = require('../shared/appearance');
const { ACTIONS } = require('./catalog');
const Life = require('../shared/life');
const Emotions = require('../shared/emotions');

function validateState(state) {
  const invalid = () => { throw new Error('存档结构不正确'); };
  if (!state || state.version !== 1 || !Array.isArray(state.residents) || !state.residents.length ||
      !Array.isArray(state.providers) || !Array.isArray(state.events) || !Array.isArray(state.stats) ||
      !Number.isFinite(state.clock) || ![1, 2, 4].includes(state.speed)) invalid();
  const ids = new Set();
  for (const p of state.providers) {
    if (!p || typeof p.id !== 'string' || ids.has(p.id) || !['demo', 'openai', 'anthropic'].includes(p.type)) invalid();
    ids.add(p.id);
    if (p.apiKey !== undefined && typeof p.apiKey !== 'string') invalid();
    if (p.sealedKey !== undefined && (typeof p.sealedKey !== 'string' || !p.sealedKey.length)) invalid();
  }
  if (state.pets !== undefined && !Array.isArray(state.pets)) invalid();
  if (state.player !== undefined && state.player !== null) {
    const player=state.player;
    if (!player || typeof player!=='object' || Array.isArray(player) || player.id!=='player' || player.isPlayer!==true || player.kind!=='human' || player.enabled!==true ||
        typeof player.name!=='string' || !player.name.trim() || player.name.length>30 ||
        !player.model || player.model.providerId!=='demo' || player.model.model!=='demo' ||
        !Number.isFinite(player.model.temperature) || !Number.isFinite(player.model.maxTokens) ||
        !Object.hasOwn(ACTIONS,player.action) || !player.appearance || typeof player.appearance!=='object' ||
        !player.relationships || Array.isArray(player.relationships) || Object.values(player.relationships).some(v=>!Number.isFinite(v)||v < -100||v > 100) ||
        !Array.isArray(player.messages) || player.messages.some(m=>!m||!['user','assistant','error'].includes(m.role)||typeof m.content!=='string')) invalid();
    try { player.appearance=appearance.normalize(player.appearance); } catch { invalid(); }
    if(player.gender!==({male:'男',female:'女',nonbinary:'中性'})[player.appearance.gender]) invalid();
    if(player.target!==null&&player.target!==undefined&&(!Number.isFinite(player.target.x)||!Number.isFinite(player.target.y))) invalid();
    if(player.meeting!==null&&player.meeting!==undefined&&(typeof player.meeting.partner!=='string'||typeof player.meeting.initiator!=='boolean'||typeof player.meeting.automatic!=='boolean')) invalid();
  }
  const residents = new Set();
  for (const r of [...state.residents, ...(state.pets || []), ...(state.player ? [state.player] : [])]) {
    if (!r || typeof r.id !== 'string' || residents.has(r.id) || !r.model || !ids.has(r.model.providerId) ||
        !r.persona || ['personality', 'background', 'likes', 'speakingStyle'].some(k => typeof r.persona[k] !== 'string') ||
        !Array.isArray(r.memory) || r.memory.some(m => typeof m !== 'string') || !Array.isArray(r.messages) ||
        !r.relationships || typeof r.relationships !== 'object' ||
        ['x', 'y', 'remaining', 'energy', 'social', 'happiness'].some(k => !Number.isFinite(r[k]))) invalid();
    residents.add(r.id);
  }
  if(state.residents.some(r=>r.id==='player'||r.isPlayer)||(state.pets||[]).some(r=>r.id==='player'||r.isPlayer)) invalid();
  if (state.stats.some(s => !s || typeof s.day !== 'string')) invalid();
  if(state.worldInfo!==undefined)try{Life.validateWorld(state.worldInfo);}catch{invalid();}
  if(state.resumeAutonomy!==undefined&&typeof state.resumeAutonomy!=='boolean')invalid();
  for(const r of state.residents)if(r.life!==undefined){const l=r.life;if(!l||typeof l.aspiration!=='string'||l.aspiration.length>300||typeof l.routine!=='string'||l.routine.length>500||typeof l.custom!=='boolean'||(l.focus!==null&&!Life.validFocus(l.focus))||!Array.isArray(l.history)||l.history.length>12||l.history.some(g=>!Life.validFocus(g)))invalid();}
  for(const r of [...state.residents,...(state.player?[state.player]:[])])if(r.emotion!==undefined&&!Emotions.valid(r.emotion))invalid();
  return state;
}

class Persistence {
  constructor(dir, safeStorage) {
    this.dir = dir; this.safe = safeStorage;
    // macOS may ask for keychain authorization after an app update. Query only when keys are actually needed.
    this.encryptionAvailable = null;
    fs.mkdirSync(dir, { recursive: true });
    this.file = path.join(dir, 'town.json');
  }
  decode(raw) {
    const state = validateState(JSON.parse(raw));
    for (const p of state.providers) if (p.sealedKey) {
      this.encryptionAvailable = this.safe.isEncryptionAvailable();
      if (!this.encryptionAvailable) throw new Error('系统钥匙串暂不可用，请稍后重试');
      try { p.apiKey = this.safe.decryptString(Buffer.from(p.sealedKey, 'base64')); }
      catch { throw new Error('存档密钥无法解密，请检查系统钥匙串后重试'); }
      delete p.sealedKey;
    }
    for (const r of [...state.residents, ...(state.pets || [])]) { r.thinking = false; r.moving = false; r.dialoguePending=false; }
    state.player ||= null;
    if(state.player) {
      Object.assign(state.player,{thinking:false,moving:false,target:null,meeting:null,action:'idle',remaining:10,bubble:'',bubbleUntil:0,direction:'front'});
      for(const r of state.residents)if(r.meeting?.partner==='player'){r.meeting=null;r.target=null;r.action='idle';}
    }
    state.controlledId = null;
    // A previously enabled persistent life mode resumes; older saves stay opt-out.
    state.autonomous = state.resumeAutonomy === true && state.autonomous === true;
    return state;
  }
  load() {
    this.recovered = false;
    if (!fs.existsSync(this.file)) return null;
    try { return this.decode(fs.readFileSync(this.file, 'utf8')); }
    catch (error) {
      // 钥匙串暂不可用不代表存档损坏，不能悄悄改用较旧数据。
      if (/钥匙串|解密/.test(error.message)) throw error;
      const backup = this.file + '.bak';
      if (!fs.existsSync(backup)) throw error;
      const recovered = this.decode(fs.readFileSync(backup, 'utf8'));
      const damaged = this.file + '.damaged-' + Date.now();
      fs.copyFileSync(this.file, damaged);
      fs.chmodSync(damaged, 0o600);
      this.recovered = true;
      return recovered;
    }
  }
  save(state) {
    const copy = validateState(structuredClone(state));
    const hasKeys = copy.providers.some(p => p.apiKey);
    if (hasKeys) {
      this.encryptionAvailable = this.safe.isEncryptionAvailable();
      if (!this.encryptionAvailable) throw new Error('系统钥匙串暂不可用，含 API 密钥的存档未保存；请稍后重试');
    }
    for (const p of copy.providers) {
      delete p.sealedKey;
      if (p.apiKey) p.sealedKey = this.safe.encryptString(p.apiKey).toString('base64');
      delete p.apiKey;
    }
    const tmp = this.file + '.tmp';
    try {
      fs.writeFileSync(tmp, JSON.stringify(copy, null, 2), { mode: 0o600 });
      fs.chmodSync(tmp, 0o600);
      // 恢复后的第一次保存保留可用备份，避免用损坏主档覆盖它。
      if (fs.existsSync(this.file) && !this.recovered) {
        fs.copyFileSync(this.file, this.file + '.bak');
        fs.chmodSync(this.file + '.bak', 0o600);
      }
      fs.renameSync(tmp, this.file);
      this.recovered = false;
    } finally {
      if (fs.existsSync(tmp)) fs.unlinkSync(tmp);
    }
  }
}
module.exports = { Persistence };
