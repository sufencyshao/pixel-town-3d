'use strict';
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const ROOT = path.resolve(__dirname, '../assets');
const Regions = require('../shared/sprite-regions');
const regionsFile = path.join(ROOT, 'sprite-regions.json');
const spriteRegions = fs.existsSync(regionsFile) ? JSON.parse(fs.readFileSync(regionsFile,'utf8')) : {entries:{}};
// Paths are local asset references, never arbitrary filesystem access or remote URLs.
function assetPath(relative) {
  if (typeof relative !== 'string' || !relative || relative.includes('\\') || path.isAbsolute(relative)) return null;
  const result = path.resolve(ROOT, relative);
  return result.startsWith(ROOT + path.sep) ? result : null;
}
function normalizePersona(p = {}) {
  return { personality: String(p.personality || ''), background: String(p.background || ''),
    likes: Array.isArray(p.likes || p.interests) ? (p.likes || p.interests).join('、') : String(p.likes || p.interests || ''), speakingStyle: String(p.speakingStyle || p.speech || '') };
}
function animationFor(folder) {
  for (const name of ['animation.json', 'animations/manifest.json', 'manifest.json']) {
    const file = assetPath(folder + '/' + name);
    if (!file || !fs.existsSync(file)) continue;
    const a = JSON.parse(fs.readFileSync(file, 'utf8'));
    if (a.version !== 1 || !Number.isInteger(a.frameWidth) || !Number.isInteger(a.frameHeight) ||
      a.frameWidth < 1 || a.frameHeight < 1 || !a.animations ||
      (a.anchor !== undefined && (!Array.isArray(a.anchor) || a.anchor.length !== 2 || a.anchor.some(n=>!Number.isFinite(n)||n<0||n>1)))) throw new Error('动画目录格式无效：' + folder);
    for (const clip of Object.values(a.animations)) if (!Number.isInteger(clip.frames) || clip.frames < 1 ||
      (!Array.isArray(clip.durations) && (!Number.isFinite(clip.frameMs) || clip.frameMs < 16)) ||
      (Array.isArray(clip.durations) && (clip.durations.length !== clip.frames || clip.durations.some(ms => !Number.isFinite(ms) || ms < 1))) || !assetPath(folder + '/' + clip.atlas))
      throw new Error('动画帧格式无效：' + folder);
    const regions=spriteRegions.entries[folder];
    if(regions){
      const current=relative=>{
        const file=assetPath(folder+'/'+relative),hash=regions.hashes?.[relative];
        if(!file||!hash||!fs.existsSync(file))return false;
        return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex')===hash;
      };
      for(const bounds of Object.values(regions.frames))if(!Regions.valid(bounds,a.frameWidth,a.frameHeight))throw new Error('人物显示边界无效：'+folder);
      a.frameBounds={};a.frameOffsets={};
      for(const [n,bounds] of Object.entries(regions.frames))if(current('frame_'+String(n).padStart(2,'0')+'.png')){a.frameBounds[n]=bounds;a.frameOffsets[n]=regions.frameOffsets[n]||0;}
      for(const [name,bounds] of Object.entries(regions.clips)){
        const clip=a.animations[name];
        if(!clip||bounds.length!==clip.frames||bounds.some(b=>b!==null&&!Regions.valid(b,a.frameWidth,a.frameHeight)))throw new Error('动作显示边界无效：'+folder);
        if(current(clip.atlas)){clip.visibleBounds=bounds;clip.offsetX=regions.clipOffsets[name]||0;}
      }
    }
    return a;
  }
  return null;
}
function loadRoster() {
  const file = path.join(ROOT, 'roster.json');
  if (!fs.existsSync(file)) return { characters: [], pets: [] };
  const roster = JSON.parse(fs.readFileSync(file, 'utf8'));
  if (roster.version !== 1 || !Array.isArray(roster.characters) || !Array.isArray(roster.pets)) throw new Error('角色目录格式无效');
  const ids = new Set();
  for (const p of [...roster.characters, ...roster.pets]) {
    if (!p || typeof p.id !== 'string' || ids.has(p.id) || !assetPath(p.assetFolder) || !['human', 'animal', 'codexmini'].includes(p.kind))
      throw new Error('角色目录有无效角色');
    ids.add(p.id);
    p.animation = animationFor(p.assetFolder);
  }
  return roster;
}
module.exports = { loadRoster, normalizePersona, assetPath };
