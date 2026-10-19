'use strict';
(function (root) {
  const labels = Object.freeze({ idle:'发呆', walk:'散步', work:'工作', rest:'休息', slack:'偷懒', doze:'打盹', lie_down:'躺下', play:'游玩', chat:'交谈', greet:'挥手', cheer:'欢呼', jump:'跳跃', surprise:'惊讶', nod:'点头', shake_head:'摇头拒绝' });
  const gestures = Object.freeze(['nod', 'shake_head']);
  const recovery = Object.freeze(['slack','doze','lie_down']);
  function supports(action, animation) {
    if(action==='lie_down')return !animation||!!animation.animations?.lie_down;
    if(recovery.includes(action))return !animation||!!(animation.animations?.sit||animation.animations?.wait||animation.animations?.idle);
    return Object.hasOwn(labels, action) && (!gestures.includes(action) || !!animation?.animations?.[action]);
  }
  function gestureDuration(action, animation) {
    if (!gestures.includes(action)) return null;
    const clip = animation?.animations?.[action];
    if (!clip) return null;
    return Array.isArray(clip.durations) ? clip.durations.reduce((sum, ms) => sum + ms, 0) : clip.frames * clip.frameMs;
  }
  // Model choices must resolve to a real clip, rather than the renderer's idle fallback.
  function available(animation, mode = 'decision') {
    const clips = animation?.animations || {};
    const aliases = { greet:'wave', rest:clips.sit?'sit':'wait', play:clips.cheer?'cheer':'jump' };
    return Object.keys(labels).filter(action => {
      if (mode === 'conversation' && ['walk', 'work',...recovery].includes(action)) return false;
      if(action==='lie_down')return !!clips.lie_down;
      if (recovery.includes(action)) return !!(clips.sit||clips.wait||clips.idle);
      if (action === 'walk') return Object.keys(clips).some(key => /^walk(?:_|$)/.test(key));
      return !!clips[action] || !!clips[aliases[action]];
    });
  }
  const api = { labels, gestures, recovery, supports, gestureDuration, available };
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.TownActions = api;
})(typeof globalThis === 'object' ? globalThis : this);
