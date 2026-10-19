'use strict';
(function(){
  const stars=[[5,57],[17,121],[28,33],[39,104],[49,20],[58,121],[68,37],[78,105],[91,42],[95,131],[33,69],[62,83]];
  const sky=document.querySelector('#sky');
  const icon=(moon)=>{
    let pixels='';
    for(let y=2;y<30;y++)for(let x=2;x<30;x++){
      const r=(x-15.5)**2+(y-15.5)**2;
      if(r<=100&&(!moon||(x-21)**2+(y-11)**2>91))pixels+=`<rect x="${x}" y="${y}" width="1" height="1"/>`;
    }
    return `<svg viewBox="0 0 32 32" aria-hidden="true" shape-rendering="crispEdges">${pixels}${moon?'':'<path d="M15 0h2v3h-2zM15 29h2v3h-2zM0 15h3v2H0zM29 15h3v2h-3zM3 3h2v2H3zM27 3h2v2h-2zM3 27h2v2H3zM27 27h2v2h-2z"/>'}</svg>`;
  };
  sky.innerHTML=stars.map(([x,y],i)=>`<i class="sky-star" style="left:${x}%;top:${y}px;--star-size:${i%3===0?3:2}px"></i>`).join('')+`<span class="celestial sun" id="sun">${icon(false)}</span><span class="celestial moon" id="moon">${icon(true)}</span>`;
  window.TownEnvironment={render(clock){
    const value=window.WorldTime.sample(clock),board=document.querySelector('#board');
    board.dataset.phase=value.phase;
    for(const [property,color] of Object.entries({sky:value.sky,horizon:value.horizon,ground:value.ground,'scene-ink':value.ink,'scene-grid':value.grid,'night-stars':value.night**2,'sprite-brightness':value.spriteBrightness,'sprite-warmth':value.spriteWarmth}))board.style.setProperty('--'+property,color);
    for(const key of ['sun','moon']){
      const element=document.querySelector('#'+key),body=value[key];
      element.hidden=!body.visible;element.style.left=body.x+'%';element.style.top=body.y+'px';
    }
    document.querySelector('#time-phase').textContent=value.label;
    document.querySelector('#town-weather').textContent='白板小镇 · '+value.label;
    document.querySelector('#scene-time-label').textContent=value.label+' · 日出 06:00 / 日落 18:00';
    return value;
  }};
})();
