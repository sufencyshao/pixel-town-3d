'use strict';
(function(){
  const cache=new Map(),pending=new Map(),failed=new Set();
  function source(r,playerImage){
    if(r.action==='lie_down'){
      if(r.isPlayer)return{url:JSON.stringify(r.appearance)+'/side-lying-v1',player:r,designed:true,width:256,height:256,frames:4,durations:[1200,800,800,1000]};
      const clip=r.animation.animations.lie_down;
      if(!clip?.sideLying)throw new Error('缺少专门绘制的侧躺素材：'+r.name);
      return{url:`../assets/${r.assetFolder}/${clip.atlas}`,designed:true,width:256,height:256,frames:clip.frames,durations:clip.durations};
    }
    if(r.isPlayer)return{url:playerImage(r.appearance,16),width:r.appearance.styleMode==='preset'?256:128,height:r.appearance.styleMode==='preset'?256:160,frames:1};
    if(r.kind==='human')return{url:`../assets/${r.assetFolder}/frame_16.png`,width:256,height:256,frames:1,bounds:r.animation.frameBounds?.['16'],offset:r.animation.frameOffsets?.['16']||0};
    const clip=r.animation.animations[r.animation.animations.wait?'wait':'idle'];return{url:`../assets/${r.assetFolder}/${clip.atlas}`,width:256,height:256,frames:1,bounds:clip.visibleBounds?.[0]};
  }
  function encode(p){const c=document.createElement('canvas');c.width=p.width;c.height=p.height;c.getContext('2d').putImageData(new ImageData(p.data,p.width,p.height),0,0);return c.toDataURL('image/png');}
  function ensure(s,action){
    const key=s.url+'/'+action;if(cache.has(key))return cache.get(key);if(pending.has(key)||failed.has(key))return null;
    const work=s.player?window.PlayerUI.sideLyingFrames(s.player):new Promise((resolve,reject)=>{const image=new Image();image.onload=()=>{try{
      const c=document.createElement('canvas');c.width=s.width;c.height=s.height;const x=c.getContext('2d',{willReadFrequently:true});x.imageSmoothingEnabled=false;const images=[];
      if(s.designed&&(image.naturalWidth!==s.width*s.frames||image.naturalHeight!==s.height))throw new Error('侧躺图集帧数无效');
      for(let n=0;n<(s.designed?s.frames:1);n++){x.clearRect(0,0,s.width,s.height);x.drawImage(image,n*s.width,0,s.width,s.height,0,0,s.width,s.height);const raw=x.getImageData(0,0,s.width,s.height);
        if(s.designed)images.push(encode({width:s.width,height:s.height,data:raw.data}));
        else{const clean=window.SpriteRegions.pixels({width:s.width,height:s.height,data:raw.data},s.bounds,s.offset||0);for(let phase=0;phase<4;phase++)images.push(encode(window.TownRecoveryPoses.pixels(clean,action,phase)));}
      }resolve(images);
    }catch(e){reject(e);}};image.onerror=()=>reject(new Error('休息姿势素材无法加载：'+s.url));image.src=s.url;});
    pending.set(key,work);work.then(frames=>{cache.set(key,frames);if(cache.size>96)cache.delete(cache.keys().next().value);}).catch(e=>{failed.add(key);console.error(e);}).finally(()=>pending.delete(key));return null;
  }
  function phaseAt(elapsed,s,frames){if(!s.durations)return Math.floor(elapsed/650)%frames.length;let phase=Math.max(0,elapsed)%s.durations.reduce((n,d)=>n+d,0);for(let n=0;n<s.durations.length;n++){if(phase<s.durations[n])return n;phase-=s.durations[n];}return 0;}
  function render(r,elapsed,node,playerImage){
    if(!window.TownRecoveryPoses.is(r.action)||r.moving||r.target&&Math.hypot(r.x-r.target.x,r.y-r.target.y)>5)return false;
    const s=source(r,playerImage),frames=ensure(s,r.action);if(!frames)return false;
    const key=s.url+'/'+r.action+'/'+(r.actionVersion||0);
    if(node.dataset.recoveryKey!==key){node.dataset.recoveryKey=key;node.dataset.recoveryAt=elapsed;}
    const image=node.querySelector('img'),atlas=node.querySelector('.atlas-sprite');
    atlas.hidden=true;atlas.style.backgroundImage='';delete atlas.dataset.source;image.hidden=false;image.style.transform='';image.style.clipPath='';image.style.translate='';delete image.dataset.spriteRegion;
    const src=frames[phaseAt(elapsed-Number(node.dataset.recoveryAt),s,frames)];if(image.dataset.src!==src){image.src=src;image.dataset.src=src;}
    node.dataset.recovery=r.action;node.classList.toggle('sleeping',r.action==='doze'||r.action==='lie_down');return true;
  }
  async function prepare(r,playerImage){const s=source(r,playerImage),key=s.url+'/'+r.action;const cached=ensure(s,r.action);if(cached)return cached;const work=pending.get(key);if(!work)throw new Error('休息素材准备失败');return await work;}
  window.TownRecoveryUI={render,prepare,source};
})();
