'use strict';
// Shared by the renderer and Node tests. Time is supplied by the game, allowing
// pause/speed controls without GIF decoding or loading individual frame files.
(function (root) {
  const gestures = typeof module === 'object' && module.exports ? require('../shared/actions').gestures : root.TownActions.gestures;
  function clipFor(entity) {
    const a = entity.animation?.animations;
    if (!a) return null;
    const walking = entity.moving || (entity.target && Math.hypot(entity.x-entity.target.x, entity.y-entity.target.y)>5);
    const direction = entity.direction || 'front';
    const action = entity.thinking && a.think ? 'think' : walking ? (entity.kind !== 'animal' ? 'walk' : entity.action) : entity.action;
    if(action==='lie_down')return a.lie_down?{key:action,...a.lie_down,pose:action}:null;
    if(['slack','doze'].includes(action)){
      const sourceKey=a.sit?'sit':a.wait?'wait':'idle';
      if(!a[sourceKey])return null;
      return { ...a[sourceKey],key:action,sourceKey,pose:action };
    }
    const alt = direction === 'front' ? 'down' : direction === 'back' ? 'up' : direction;
    const aliases = { greet:'wave', rest:a.sit?'sit':entity.kind==='codexmini'&&a.wait?'wait':'idle', play:a.cheer?'cheer':a.jump?'jump':'idle' };
    const alias = a[action] ? action : (aliases[action] || action);
    const miniWalk = action==='walk'&&entity.kind==='codexmini' ? (entity.target?.x<entity.x&&a.walk_left?'walk_left':a.walk_right?'walk_right':a.walk_left?'walk_left':null) : null;
    const key = a[action + '_' + direction] ? action + '_' + direction : a[action + '_' + alt] ? action + '_' + alt : a[alias] ? alias : miniWalk || 'idle';
    return a[key] ? { key, ...a[key], ...(gestures.includes(key)?{loop:false}:{}) } : null;
  }
  function sample(entity, elapsed) {
    const clip = clipFor(entity);
    if (!clip) return null;
    if (Array.isArray(clip.durations) && clip.durations.length === clip.frames) {
      const total = clip.durations.reduce((sum, ms) => sum + ms, 0);
      const phase = clip.loop === false ? Math.min(Math.max(0, elapsed), total - 1) : Math.max(0, elapsed) % total;
      let boundary = 0;
      for (let frame = 0; frame < clip.frames; frame++) { boundary += clip.durations[frame]; if (phase < boundary) return { ...clip, frame }; }
    }
    const raw = Math.max(0, Math.floor(elapsed / (clip.frameMs || 80)));
    return { ...clip, frame:clip.loop === false ? Math.min(clip.frames - 1, raw) : raw % clip.frames };
  }
  const api = { clipFor, sample };
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.TownAnimation = api;
})(typeof globalThis === 'object' ? globalThis : this);
