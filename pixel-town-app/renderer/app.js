'use strict';
const $=s=>document.querySelector(s);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const actions=window.TownActions.labels;
const animalActions={idle:'观察',observe:'警戒观察',flee:'避开刺激',walk:'行走',run:'小跑',rest:'休息',sleep:'睡眠',eat:'进食',drink:'饮水',sniff:'嗅闻',groom:'梳理毛羽',scratch:'抓挠',play:'探索玩具',hop:'跳行',fly:'飞行',perch:'栖停',peck:'啄食',forage:'觅食',graze:'采食',swim:'游动',hide:'躲藏',explore:'探索',vocalize:'鸣叫',stretch:'舒展',flap:'振翅',pounce:'扑动',chew:'啃咬',dig:'挖掘',roll:'翻滚',wag:'摆尾',bask:'晒暖',burrow:'掘穴'};
const actionLabel=r=>(r.kind==='animal'?animalActions:actions)[r.action]||r.action;
const isAnimal=r=>r?.kind==='animal';
const moods={calm:'平静',happy:'开心',tired:'疲惫',sad:'低落'};
let state,catalog,petCatalog,selected,meta,zoom=1,page='world',inspectorSignature='',listSignature='',eventSignature='',statsSignature='',filter='',dragging=null,frameOverride=null,toastTimer,chatSending=false;
const nodes=new Map();
const time=n=>String(Math.floor(n/60)%24).padStart(2,'0')+':'+String(Math.floor(n)%60).padStart(2,'0');
const active=()=>state.residents.filter(r=>r.enabled);
const activePets=()=>state.pets.filter(r=>r.enabled);
const allPeople=()=>[...state.residents,...state.pets,...(state.player?[state.player]:[])];
const inhabitants=()=>[...active(),...activePets(),...(state.player?[state.player]:[])];
const current=()=>allPeople().find(r=>r.id===selected);
const img=(r,n=1)=>r.isPlayer?window.PlayerUI.image(r.appearance,n):`../assets/${r.assetFolder||('characters/'+r.asset)}/${n===1&&/\.(png|gif|webp)$/i.test(r.sprite||'')?r.sprite:r.kind==='codexmini'?'portrait.png':`frame_${String(n).padStart(2,'0')}.png`}`;
const invoke=(name,...args)=>window.townAPI.invoke(name,...args);
function toast(text){$('#toast').textContent=text;$('#toast').classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#toast').classList.remove('show'),4000);}
async function run(fn){try{return await fn();}catch(e){toast(e.message);return null;}}
function select(id){selected=id;frameOverride=null;inspectorSignature='';render();}
function setPage(name){page=name;listSignature='';$('#world-page').hidden=name!=='world';$('#api-page').hidden=name!=='api';document.querySelectorAll('.nav').forEach(b=>b.classList.toggle('active',b.dataset.page===name));render();}
function render(){
  if(!state)return;
  if(selected&&!(page==='api'?allPeople():inhabitants()).some(r=>r.id===selected))selected=null;
  $('#population-label').textContent=active().length;$('#resident-count').textContent=String(active().length).padStart(2,'0');
  $('#day').textContent=`第 ${Math.floor(state.clock/1440)+1} 天`;$('#clock').textContent=time(state.clock);
  window.TownEnvironment.render(state.clock);
  $('#pause').textContent=state.running?'Ⅱ':'▶';$('#pause').title=state.running?'暂停生活':'继续生活';$('#pause').setAttribute('aria-label',$('#pause').title);
  $('#speed').value=state.speed;$('#grid').checked=state.grid;$('#zones').checked=state.zones;
  $('#board').classList.toggle('grid',state.grid);document.querySelectorAll('.zone').forEach(n=>n.hidden=!state.zones);
  $('#board-status').textContent=state.running?'生活正在发生':'生活已暂停';
  $('#board-status-hud').textContent=state.running?'日常继续着':'时间停在这一刻';
  renderList();renderPetList();if(page==='world')renderSprites();renderEvents();renderInspector();updateChatModal();if(page==='api')renderAPI();window.PlayerUI.update(state);window.TownLifeUI.update();window.TownEmotionsUI.update();
  refreshImageRegions();
}
function applyImageRegion(image){
  if(!catalog)return;
  let match;try{match=decodeURIComponent(new URL(image.src,document.baseURI).pathname).match(/\/assets\/(.+)\/frame_(\d+)\.png$/);}catch{return;}
  if(!match){if(image.dataset.spriteRegion){image.style.clipPath='';image.style.translate='';delete image.dataset.spriteRegion;}return;}
  const animation=[...catalog,...(petCatalog||[])].find(r=>r.assetFolder===match[1])?.animation;
  const bounds=animation?.frameBounds?.[String(Number(match[2]))];
  if(bounds){window.SpriteRegions.imageStyle(image,bounds,animation.frameOffsets?.[String(Number(match[2]))]||0,animation.frameWidth,animation.frameHeight);image.dataset.spriteRegion='true';}
  else if(image.dataset.spriteRegion){image.style.clipPath='';image.style.translate='';delete image.dataset.spriteRegion;}
}
function refreshImageRegions(){document.querySelectorAll('img').forEach(applyImageRegion);}
document.addEventListener('load',e=>{if(e.target.tagName==='IMG')applyImageRegion(e.target);},true);
new MutationObserver(records=>{for(const r of records){if(r.type==='attributes')applyImageRegion(r.target);else for(const node of r.addedNodes)if(node.nodeType===1){if(node.tagName==='IMG')applyImageRegion(node);node.querySelectorAll?.('img').forEach(applyImageRegion);}}}).observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['src']});
window.addEventListener('resize',refreshImageRegions);
function renderList(){
  const residents=active().filter(r=>`${r.name}${r.occupation}${r.persona.personality}`.includes(filter));
  const sig=JSON.stringify(residents.map(r=>[r.id,r.name,r.asset,r.occupation,r.action,r.thinking]))+selected;
  if(sig===listSignature)return;listSignature=sig;
  $('#residents').innerHTML=residents.map(r=>`<button class="resident-row ${r.id===selected?'selected':''}" data-id="${r.id}"><img class="resident-avatar" src="${img(r)}" alt=""><div><div class="name">${esc(r.name)}</div><div class="job">${esc(r.occupation)}</div></div><span class="activity ${r.thinking?'thinking':''}">${r.thinking?'决策中':actionLabel(r)}</span></button>`).join('')||'<p class="empty">没有找到这位居民。</p>';
}
function frame(r,t){
  if(r.id===selected&&frameOverride)return frameOverride;
  const moving=r.moving||(r.target&&Math.hypot(r.x-r.target.x,r.y-r.target.y)>5);
  const phase=Math.floor(t/180)%3;
  if(moving){if(r.direction==='back')return r.isPlayer?[10,17,18][phase]:10;if(r.direction==='left')return [4,5,6][phase];if(r.direction==='right')return [7,8,9][phase];return [1,2,3][phase];}
  if(['rest','slack','doze'].includes(r.action))return 16;
  if(r.action==='lie_down')return 7;
  const backSteps=r.isPlayer?characterAnimation(r)?.backWalkCompletion:r.animation?.backWalkCompletion;
  if(r.action==='cheer')return backSteps?1:Math.floor(t/350)%2?11:12;
  if(r.action==='play')return backSteps?1:[1,13,11,1][Math.floor(t/650)%4];
  return {greet:14,jump:13,surprise:15}[r.action]||(r.isPlayer?{left:4,right:7,back:10}[r.direction]:1)||1;
}
function renderSprites(){
  const width=$('#board').clientWidth,height=$('#board').clientHeight;
  const stage=stageBounds();
  const size=Math.min(90,Math.max(62,Math.min(width/10,height/4.8)));
  const ids=new Set(inhabitants().map(r=>r.id));
  for(const [id,node]of nodes)if(!ids.has(id)){node.remove();nodes.delete(id);}
  for(const r of inhabitants()){
    let node=nodes.get(r.id);
    if(!node){node=document.createElement('button');node.className='sprite';node.dataset.id=r.id;node.innerHTML='<span class="bubble"></span><span class="atlas-sprite" aria-hidden="true"></span><img draggable="false" alt=""><span class="nametag"></span><span class="actiontag"></span>';$('#sprites').append(node);nodes.set(r.id,node);}
    node.classList.toggle('selected',r.id===selected);node.classList.toggle('player',!!r.isPlayer);node.setAttribute('aria-label',`${r.name}，${actionLabel(r)}`);
    const visualSize=size*(isAnimal(r)?Math.max(.22,Math.min(2,Number(r.animal?.scale)||.6)):1);
    const anchor=r.isPlayer?[.5,.9]:r.animation?.anchor||[.5,.9];
    node.dataset.anchorX=anchor[0]*.98+.01;node.dataset.anchorY=anchor[1];node.style.transform=`translate(-${(anchor[0]*.98+.01)*100}%, -${anchor[1]*.98/1.28*100}%)`;
    node.style.setProperty('--anchor-y',`${anchor[1]*visualSize*.98}px`);
    node.dataset.visualSize=visualSize;node.style.width=visualSize+'px';node.style.height=visualSize*1.28+'px';node.querySelector('img').style.width=visualSize*.98+'px';node.querySelector('img').style.height=visualSize*.98+'px';
    if(!dragging||dragging.id!==r.id){node.style.left=`${stage.left+(r.x-90)/1420*(stage.right-stage.left)}px`;node.style.top=`${stage.top+(r.y-120)/790*(stage.bottom-stage.top)}px`;}
    node.style.zIndex=String(10+Math.round(r.y));
    node.querySelector('.nametag').textContent=r.name;
    node.querySelector('.actiontag').textContent=r.thinking?(isAnimal(r)?'感官更新…':'思考中…'):r.meeting?'走向相遇区':r.behaviorStatus==='waiting'&&state.autonomous&&r.model.providerId!=='demo'?'等下一个想法':actionLabel(r);
    const thought=!isAnimal(r)&&!r.thinking&&!r.bubble&&!!r.thought;
    const bubble=node.querySelector('.bubble');bubble.classList.toggle('thought',thought);
    bubble.textContent=isAnimal(r)?'':r.bubble|| (r.thinking?'…':thought?'心声 · '+r.thought:'');
  }
  // 气泡在画布内排布，避免相邻人物的对话遮盖彼此。
  const placed=[];
  for(const r of inhabitants().sort((a,b)=>(b.id===selected)-(a.id===selected))){
    const node=nodes.get(r.id),bubble=node.querySelector('.bubble');if(!bubble.textContent)continue;
    const visualSize=Number(node.dataset.visualSize),anchorY=Number(node.dataset.anchorY);
    const nodeLeft=parseFloat(node.style.left)-visualSize*Number(node.dataset.anchorX),nodeTop=parseFloat(node.style.top)-visualSize*.98*anchorY;
    const bw=145,bh=bubble.offsetHeight||65,baseX=nodeLeft+visualSize/2-bw/2;
    let chosen;
    const candidates=[];
    for(const dy of [0,-bh-8,bh+8,-2*(bh+8)])for(const dx of [0,-bw/2-10,bw/2+10])candidates.push({x:Math.min(width-bw-10,Math.max(10,baseX+dx)),y:Math.min(height-bh-52,Math.max(35,(nodeTop-bh>35?nodeTop-bh-7:nodeTop+visualSize*1.28+7)+dy))});
    for(const c of candidates){if(!placed.some(p=>c.x<p.x+bw+5&&c.x+bw+5>p.x&&c.y<p.y+p.h+5&&c.y+bh+5>p.y)){chosen=c;break;}}
    chosen=chosen||candidates[0];placed.push({...chosen,h:bh});
    bubble.style.width=bw+'px';bubble.style.left=chosen.x-nodeLeft+'px';bubble.style.top=chosen.y-nodeTop+'px';bubble.style.bottom='auto';bubble.style.transform='none';
  }
}
let animationTime=0,lastAnimationAt=null;
function animate(t){
  if(lastAnimationAt!==null&&state?.running)animationTime+=(t-lastAnimationAt)*state.speed;
  lastAnimationAt=t;
  if(state&&page==='world')for(const r of inhabitants()){
    const node=nodes.get(r.id);if(!node)continue;
    const image=node.querySelector('img'),atlas=node.querySelector('.atlas-sprite');
    if(window.TownRecoveryUI.render(r,animationTime,node,window.PlayerUI.image))continue;
    delete node.dataset.recovery;delete node.dataset.recoveryKey;delete node.dataset.recoveryAt;node.classList.remove('sleeping');
    if(r.isPlayer&&r.appearance.styleMode==='preset'&&!(r.id===selected&&frameOverride)){
      const heroClip=window.PlayerUI.clipFor(r);
      if(heroClip){
        const heroKey=r.appearance.avatarPreset+'/'+heroClip.key+'/'+(r.actionVersion||0);
        if(node.dataset.heroClip!==heroKey){node.dataset.heroClip=heroKey;node.dataset.heroClipAt=animationTime;}
        if(!window.PlayerUI.isAnimationReady(r,heroClip.key))node.dataset.heroClipAt=animationTime;
        const source=window.PlayerUI.animationImage(r,animationTime-Number(node.dataset.heroClipAt),frame(r,animationTime));
        image.hidden=false;atlas.hidden=true;atlas.style.backgroundImage='';
        if(image.dataset.src!==source){image.src=source;image.dataset.src=source;}
        image.style.transform='';continue;
      }
    }
    if(r.isPlayer&&r.appearance.styleMode!=='preset'){delete node.dataset.heroClip;delete node.dataset.heroClipAt;}
    const clip=r.isPlayer?null:window.TownAnimation.clipFor(r);
    if(clip&&!(r.id===selected&&frameOverride)){
      const version=String(r.actionVersion||0);
      if(node.dataset.clip!==clip.key||node.dataset.asset!==r.assetFolder||node.dataset.actionVersion!==version){node.dataset.clip=clip.key;node.dataset.asset=r.assetFolder;node.dataset.actionVersion=version;node.dataset.clipAt=animationTime;}
      const sample=window.TownAnimation.sample(r,animationTime-Number(node.dataset.clipAt));
      const size=Number(node.dataset.visualSize)*.98;
      image.hidden=true;atlas.hidden=false;atlas.style.width=size+'px';atlas.style.height=size+'px';
      const atlasURL=`../assets/${r.assetFolder}/${sample.atlas}`;
      if(atlas.dataset.source!==atlasURL){atlas.style.backgroundImage=`url("${atlasURL}")`;atlas.dataset.source=atlasURL;}
      atlas.style.backgroundSize=`${sample.frames*size}px ${size}px`;atlas.style.backgroundPosition=`${-sample.frame*size}px 0px`;
      atlas.style.clipPath=window.SpriteRegions.inset(sample.visibleBounds?.[sample.frame],r.animation.frameWidth,r.animation.frameHeight);
      atlas.style.translate=sample.offsetX?`${sample.offsetX/r.animation.frameWidth*size}px 0px`:'';
    }else{
      image.hidden=false;atlas.hidden=true;atlas.style.backgroundImage='';delete atlas.dataset.source;const source=img(r,frame(r,animationTime));
      if(image.dataset.src!==source){image.src=source;image.dataset.src=source;}
      image.style.transform='';
      applyImageRegion(image);
    }
  }
  requestAnimationFrame(animate);
}
requestAnimationFrame(animate);
function renderEvents(){
  const type=$('#event-filter').value;
  const events=state.events.filter(e=>type==='all'||e.kind===type).slice(0,60);
  const sig=events.map(e=>e.id).join('')+type;if(sig===eventSignature)return;eventSignature=sig;
  $('#events').innerHTML=events.map(e=>`<div class="event ${esc(e.kind)}"><time>${time(e.time)}</time><span class="event-dot"></span><span>${esc(e.text)}</span></div>`).join('')||'<p class="empty">这一页还没有故事，试试让两位居民聊聊天。</p>';
}
function renderInspector(){
  const r=current();if(r&&isAnimal(r))return renderPetInspector(r);if(!r){$('#inspector').innerHTML='';return;}
  const sig=JSON.stringify([r.id,r.name,r.asset,r.appearance,r.occupation,r.model,r.thinking,state.busy,state.controlledId]);
  if(sig!==inspectorSignature){inspectorSignature=sig;
    $('#inspector').innerHTML=`<img class="interaction-portrait" src="${img(r)}" alt=""><div class="interaction-person"><strong>${esc(r.name)}</strong><span id="game-mood"></span></div><span class="control-divider"></span><div class="interaction-actions"><button data-action="greet">打招呼</button><button data-action="rest">坐一会儿</button>${r.isPlayer?'<button id="player-actions">动作与表情</button>':['human','codexmini'].includes(r.kind)?'<button id="resident-actions">更多动作</button>':'<button data-action="play">玩一玩</button>'}<button id="invite-dialogue">找邻居聊聊</button>${r.isPlayer?'':`<button id="open-chat">问问近况</button><button id="ask-ai" ${state.busy?'disabled':''}>${r.model.providerId==='demo'?'绑定 AI':'让 TA 想一想'}</button>`}${r.isPlayer?'':'<button id="life-direction">生活方向</button>'}<button id="actor-mood">心情</button><button id="actor-diary">每日日志</button><button id="control-person" class="${state.controlledId===r.id?'primary':''}">${r.isPlayer?(state.controlledId===r.id?'暂停操控':'操控主角'):(state.controlledId===r.id?'放手让 TA 生活':'操控 TA')}</button></div><button id="deselect" aria-label="取消选择">×</button><div class="character-mind" id="character-mind" hidden><strong>心声</strong><span id="character-thought"></span></div>`;
  }
  $('#game-mood').textContent=`${window.TownEmotions.label(r.happiness)} ${Math.round(r.happiness)} · 精力 ${Math.round(r.energy)}${r.energy<32?' · 疲倦':''}${state.controlledId===r.id?' · WASD / 方向键移动':''}`;
  $('#character-mind').hidden=!r.thought;$('#character-thought').textContent=r.thought||'';
}
function chatModal(){
  const r=current();
  modal(`和 ${esc(r.name)} 聊聊`,`<div class="dialogue-portrait"><img src="${img(r)}" alt=""><p>${esc(r.persona.personality)}<br><span class="muted">正在${actions[r.action]} · ${moods[r.mood]}</span></p></div><div id="modal-chat-log" class="chat-log dialogue-log"></div><form class="chat-form" id="chat-form"><input id="chat-input" maxlength="4000" placeholder="今天过得怎么样？" aria-label="聊天消息"><button type="submit">说句话</button></form><p class="note" id="chat-mode">${r.model.providerId==='demo'?'本地规则人物：回应由生活规则生成。':'TA 的模型会同时决定回复、心声与动作。'}</p>`);
  $('#modal').dataset.chatResident=r.id;updateChatModal();
}
function updateChatModal(){
  if(!$('#modal').open||!$('#modal-chat-log'))return;
  const r=state.residents.find(r=>r.id===$('#modal').dataset.chatResident);if(!r)return;
  const sig=JSON.stringify(r.messages)+r.thinking;
  if($('#modal-chat-log').dataset.signature===sig)return;
  $('#modal-chat-log').dataset.signature=sig;
  $('#modal-chat-log').innerHTML=r.messages.slice(-20).map(m=>`<div class="chat-message ${m.role}">${m.role==='assistant'&&m.source==='api'?`<p class="chat-expression">${esc(actions[m.action]||m.action)} · 心声：${esc(m.thought)}</p>`:''}${esc(m.content)}</div>`).join('')+(r.thinking?'<p class="muted">正在想怎么回答你…</p>':'');
  $('#modal-chat-log').scrollTop=$('#modal-chat-log').scrollHeight;
  $('#chat-form button').disabled=state.busy;
}
function inviteModal(){
  const r=current(),neighbors=active().filter(a=>a.id!==r.id);
  modal(`${esc(r.name)}想找谁聊聊？`,`<div class="neighbor-choice">${neighbors.map(n=>`<button data-invite="${n.id}"><img src="${img(n)}" alt=""><strong>${esc(n.name)}</strong><small>${esc(n.occupation)}</small></button>`).join('')||'<p class="empty">小镇里暂时还没有别的居民。</p>'}</div>`);
}
function characterAnimation(r){return r.isPlayer?(r.appearance.styleMode==='preset'?catalog.find(c=>c.asset===r.appearance.avatarPreset)?.animation:null):r.animation;}
function motionChoices(r){
  const animation=characterAnimation(r);
  return [['idle','站好',1],['greet','挥挥手',14],['nod','点点头',1],['shake_head','摇头拒绝',1],['chat','交谈手势',1],['cheer','欢呼',animation?.backWalkCompletion?1:11],['jump','跳一下',13],['rest','坐下来',16],['slack','偷个懒',16],['doze','打个盹',16],['lie_down','躺下来',7],['play','玩一玩',animation?.backWalkCompletion?1:12],['surprise','惊讶',15],['work','工作',1]].filter(([a])=>r.kind==='codexmini'?window.TownActions.available(animation).includes(a):!['nod','shake_head','chat'].includes(a)||!!animation?.animations?.[a]);
}
async function performAction(id,action,point){
  const r=allPeople().find(p=>p.id===id);if(!r)return;
  releaseKeys();frameOverride=null;
  if(r.isPlayer)await window.PlayerUI.prepareAction(r,action);
  return invoke('town:act',id,action,point);
}
function residentActionModal(){
  const r=current();if(!r||!['human','codexmini'].includes(r.kind)||r.isPlayer)return;
  modal(`${esc(r.name)} · 动作`, `<div class="player-action-section"><div class="player-action-choices">${motionChoices(r).map(([a,l,n])=>`<button data-character-action="${a}" data-character-id="${esc(r.id)}"><img src="${img(r,n)}" alt=""><span>${l}</span></button>`).join('')}</div><p class="note">点头播放一次；摇头左右各约 30°，快速摇两下后回正。交谈手势可单独播放，也会在对话时出现。</p></div>`);
}
function timeModal(){
  releaseKeys();
  modal('小镇的下一刻',`<p class="muted">现在是第 ${Math.floor(state.clock/1440)+1} 天 ${time(state.clock)}。选择想等到的下一次时刻。</p><div class="time-choices">${[[360,'日出'],[720,'正午'],[1080,'日落'],[1320,'夜晚']].map(([minute,label])=>`<button class="time-choice" data-time="${minute}"><strong>等到${label}</strong><small>${time(minute)}</small></button>`).join('')}</div>`);
}
function playerActionModal(){
  const r=state.player;if(!r)return;
  const expressions=window.Appearance.fields.find(f=>f.key==='expression').options;
  modal('今天，想怎样表达自己？',`<div class="player-action-section"><h3>做个动作</h3><div class="player-action-choices">${motionChoices(r).map(([a,l,n])=>`<button data-player-action="${a}"><img src="${img(r,n)}" alt=""><span>${l}</span></button>`).join('')}</div><h3>换个表情</h3><div class="player-expression-choices">${expressions.map(o=>`<button data-player-expression="${o.value}" class="${r.appearance.expression===o.value?'active':''}"><img src="${window.PlayerUI.image({...r.appearance,expression:o.value})}" alt=""><span>${o.label}</span></button>`).join('')}</div><p class="note">动作在原地播放；WASD 或方向键可以随时继续移动。预设形象支持点头、快速摇头两下与交谈手势。表情会保留在你的主角存档中。</p></div>`);
}
function renderAPI(){
  const signature=JSON.stringify([state.providers,state.stats.map(s=>[s.id,s.ok,s.tokens,s.error,s.action,s.applied])]);
  if(statsSignature!==signature){statsSignature=signature;
    $('#providers').innerHTML=state.providers.map(p=>`<div class="provider-row"><span class="provider-logo">${p.type==='demo'?'町':esc(p.name.slice(0,1))}</span><div class="provider-info"><h3>${esc(p.name)}</h3><p>${p.type==='demo'?'本地性格与需求规则 · 不发起网络请求':esc(p.type==='anthropic'?'Anthropic / Messages':'OpenAI 兼容 / Chat Completions')}<br>${esc(p.baseUrl)}${p.type==='demo'?'':`<br>${p.hasKey?'密钥已保存':'未设置密钥（本地模型可留空）'}`}</p></div>${p.type!=='demo'?`<button data-provider="${esc(p.id)}">设置</button>`:'<small>内置</small>'}</div>`).join('');
    $('#stats').innerHTML=state.stats.length?`<table class="stats-table"><thead><tr><th>人物</th><th>服务商 / 模型</th><th>用途 / 动作</th><th>Tokens</th><th>状态</th></tr></thead><tbody>${state.stats.slice(-20).reverse().map(s=>`<tr><td>${esc([...state.residents,...state.pets].find(r=>r.id===s.residentId)?.name)}</td><td>${esc(s.provider)} / ${esc(s.model)}</td><td>${{'animal-decision':'动物感官决策',decision:'想法与行为',conversation:'人物对话','user-chat':'镇长聊天'}[s.purpose]}${s.action?'<br>'+esc(actions[s.action]||animalActions[s.action]||s.action):''}</td><td>${s.tokens||'—'}</td><td title="${esc(s.error||'')}">${s.applied===false?'已忽略':s.ok?'成功 · '+s.latency+'ms':s.error?'失败':'进行中'}</td></tr>`).join('')}</tbody></table>`:'<p class="empty">还没有模型调用。绑定人物的模型后，点击“让 TA 想一想”即可观察。</p>';
  }
  if(document.activeElement!==$('#api-interval'))$('#api-interval').value=state.apiInterval;
  if(document.activeElement!==$('#daily-limit'))$('#daily-limit').value=state.dailyLimit;
  $('#autonomous').checked=state.autonomous;
  const bound=active().filter(r=>r.model.providerId!=='demo');
  $('#api-ownership').textContent=bound.length?`${bound.length} 位人物已绑定 API。开启自主生活后，TA 们的想法、台词与动作由各自模型决定；完成当前行为后再思考下一步。`:'还没有人物绑定 API。添加或复制服务商后，可批量分配模型，再开启自主生活。';
  const today=new Date().toLocaleDateString('en-CA');const stats=state.stats.filter(s=>s.day===today);$('#calls').textContent=stats.length;$('#tokens').textContent=stats.reduce((a,s)=>a+(s.tokens||0),0)+' tokens';
  window.ModelAssignmentUI.update();
  $('#storage-note').textContent=`${meta.encrypted===null?'保存或读取 API 密钥时，系统可能请求钥匙串授权。密钥始终加密存储。':meta.encrypted?'API 密钥通过系统钥匙串加密存储。':'系统密钥加密不可用，无法保存含 API Key 的配置，请检查系统钥匙串。'}\n独立存档：${meta.dataDir}`;
}
function modal(title,body,footer){releaseKeys();$('#modal-content').innerHTML=`<div class="modal-head"><h2>${title}</h2><button id="close-modal" aria-label="关闭">×</button></div><div class="modal-body">${body}</div>${footer?`<div class="modal-foot">${footer}</div>`:''}`;$('#close-modal').onclick=()=>$('#modal').close();if(!$('#modal').open)$('#modal').showModal();}
function field(label,id,value,type='text',full=false){return `<label class="field ${full?'full':''}">${label}<input id="${id}" type="${type}" value="${esc(value)}"></label>`;}
function area(label,id,value){return `<label class="field full">${label}<textarea id="${id}" rows="3">${esc(value)}</textarea></label>`;}
function residentModal(){
  const r=current();if(isAnimal(r))return petModal();
  modal(`编辑 ${esc(r.name)} 的档案`,`<div class="person-modal-summary"><img src="${img(r)}" alt=""><p>形象、个性与模型彼此独立。<br>修改档案会保留现有关系、对话和记忆。</p></div><div class="form-grid"><label class="field full">可选人设预设<select id="edit-preset"><option value="">自定义 / 保持当前</option>${(r.presets||[]).map(p=>`<option value="${esc(p.id)}">${esc(p.label)}</option>`).join('')}</select></label>${field('姓名','edit-name',r.name)}${field('职业','edit-job',r.occupation)}<label class="field full">人物形象<select id="edit-asset">${catalog.map(c=>`<option value="${c.asset}" ${c.asset===r.asset?'selected':''}>${esc(c.name)} · ${esc(c.occupation)}</option>`).join('')}</select></label>${area('性格特点','edit-traits',r.persona.personality)}${area('背景故事','edit-background',r.persona.background)}${field('兴趣爱好','edit-likes',r.persona.likes)}${field('说话风格','edit-style',r.persona.speakingStyle)}<label class="field full">API 服务商<select id="edit-provider">${state.providers.map(p=>`<option value="${esc(p.id)}" ${p.id===r.model.providerId?'selected':''}>${esc(p.name)}</option>`).join('')}</select></label><label class="field full">模型名称<input id="edit-model" list="model-options" value="${esc(r.model.model)}"><datalist id="model-options"></datalist></label>${field('Temperature（0–2）','edit-temp',r.model.temperature,'number')}${field('最大输出 Tokens（64–8192）','edit-tokens',r.model.maxTokens,'number')}${area('详细人物档案 / 长期记忆（Markdown）','edit-profile',r.profileMd)}</div>`,`<button id="import-persona">复制原 AI Chat 人设</button><div><button id="cancel-edit">取消</button><button class="primary" id="save-person">保存人物</button></div>`);
  $('#edit-preset').onchange=()=>{const p=r.presets?.find(p=>p.id===$('#edit-preset').value);if(!p)return;if(p.role)$('#edit-job').value=p.role;$('#edit-traits').value=p.personality||'';$('#edit-background').value=p.background||'';$('#edit-likes').value=Array.isArray(p.interests||p.likes)?(p.interests||p.likes).join('、'):p.interests||p.likes||'';$('#edit-style').value=p.speech||p.speakingStyle||'';};
  const testing=document.createElement('details');testing.innerHTML='<summary class="muted">动作素材与模型测试</summary><div class="inline-buttons"><select id="raw-frame"><option value="0">自动动作</option>'+Array.from({length:r.kind==='codexmini'?0:16},(_,i)=>`<option value="${i+1}">第 ${i+1} 帧</option>`).join('')+'</select><button id="test-decision">测试当前已保存的模型决策</button></div><p class="note">逐帧选择可在返回小镇后观察。模型测试使用已保存的配置，会调用 API。</p>';$('#modal .modal-body').append(testing);$('#test-decision').disabled=r.model.providerId==='demo';$('#test-decision').onclick=()=>run(async()=>{await invoke('town:decide',r.id);toast('模型行为决策成功，返回小镇即可观察');});
  $('#edit-temp').step='0.1';$('#edit-temp').min='0';$('#edit-temp').max='2';$('#edit-tokens').min='64';$('#edit-tokens').max='8192';
  const fillModels=()=>{const p=state.providers.find(p=>p.id===$('#edit-provider').value);$('#model-options').innerHTML=(p?.models||[]).map(m=>`<option value="${esc(m)}"></option>`).join('');};fillModels();$('#edit-provider').onchange=()=>{fillModels();const p=state.providers.find(p=>p.id===$('#edit-provider').value);$('#edit-model').value=p?.models?.[0]||'';};
  $('#cancel-edit').onclick=()=>$('#modal').close();
  $('#save-person').onclick=()=>run(async()=>{await invoke('town:update',r.id,{...($('#edit-preset').value?{presetId:$('#edit-preset').value}:{}),name:$('#edit-name').value,occupation:$('#edit-job').value,asset:$('#edit-asset').value,persona:{personality:$('#edit-traits').value,background:$('#edit-background').value,likes:$('#edit-likes').value,speakingStyle:$('#edit-style').value},profileMd:$('#edit-profile').value,model:{providerId:$('#edit-provider').value,model:$('#edit-model').value,temperature:Number($('#edit-temp').value),maxTokens:Number($('#edit-tokens').value)}});$('#modal').close();toast('人物档案已保存');});
  $('#import-persona').onclick=()=>run(async()=>{const friends=await invoke('legacy:friends');if(!friends.length)return toast('原 AI Chat 暂无可复制的人设');const select=document.createElement('select');select.className='wide';select.setAttribute('aria-label','原 AI Chat 人设');select.innerHTML='<option value="">选择原应用中的人设…</option>'+friends.map((f,i)=>`<option value="${i}">${esc(f.name)}</option>`).join('');select.onchange=()=>{if(select.value==='')return;const f=friends[Number(select.value)];$('#edit-name').value=f.name;$('#edit-job').value=f.occupation||r.occupation;$('#edit-traits').value=Array.isArray(f.persona?.personality)?f.persona.personality.join('、'):f.persona?.personality||'';$('#edit-background').value=f.persona?.background||'';$('#edit-likes').value=f.persona?.likes||'';$('#edit-style').value=f.persona?.speakingStyle||'';$('#edit-profile').value=f.profileMd||'';toast('已填入人设，保存后生效');};$('#modal .modal-body').prepend(select);$('#import-persona').disabled=true;});
}
function populationModal(){
  modal('谁会住进小镇？',`<p class="muted">${catalog.length} 套独立人物形象，可以自由选择居民。超过 ${catalog.length} 人时新增独立人物档案并复用形象；每人的 API、记忆与关系分别保存。</p><div class="inline-buttons"><input id="population-count" aria-label="居民人数" type="number" min="1" max="60" value="${active().length}"><button id="apply-count">按人数调整</button></div><div class="gallery">${state.residents.map(r=>`<label class="gallery-item"><input type="checkbox" name="resident-enabled" value="${r.id}" ${r.enabled?'checked':''}><img src="${img(r)}" alt=""><strong>${esc(r.name)}</strong><small>${esc(r.occupation)}</small></label>`).join('')}</div>`,`<span class="muted">离镇人物的档案与回忆仍会保留。</span><button class="primary" id="save-roster">让选中的居民入住</button>`);
  $('#apply-count').onclick=()=>run(async()=>{const n=Number($('#population-count').value);if(!Number.isInteger(n)||n<1||n>60)throw new Error('人数需要是 1–60 的整数');await invoke('town:count',n);$('#modal').close();toast(`已调整为 ${n} 位居民`);});
  $('#save-roster').onclick=()=>run(async()=>{const ids=Array.from(document.querySelectorAll('[name=resident-enabled]:checked')).map(x=>x.value);await invoke('town:roster',ids);$('#modal').close();toast('居民名单已保存');});
}
function providerModal(id){
  const p=state.providers.find(p=>p.id===id)||{name:'',type:'openai',baseUrl:'',models:[],hasKey:false};
  const presets={deepseek:['DeepSeek','openai','https://api.deepseek.com','deepseek-chat'],openai:['OpenAI','openai','https://api.openai.com/v1',''],anthropic:['Anthropic','anthropic','https://api.anthropic.com',''],ollama:['Ollama 本地','openai','http://localhost:11434/v1',''],qwen:['通义千问','openai','https://dashscope.aliyuncs.com/compatible-mode/v1',''],gemini:['Gemini 兼容端点','openai','https://generativelanguage.googleapis.com/v1beta/openai','']};
  modal(id?'API 服务商设置':'添加 API 服务商',`<div class="form-grid"><label class="field full">快速填入<select id="provider-preset"><option value="">自定义 / 中转站</option>${Object.entries(presets).map(([k,v])=>`<option value="${k}">${v[0]}</option>`).join('')}</select></label>${field('服务商名称','provider-name',p.name,'text',true)}<label class="field full">协议<select id="provider-type"><option value="openai" ${p.type==='openai'?'selected':''}>OpenAI 兼容</option><option value="anthropic" ${p.type==='anthropic'?'selected':''}>Anthropic</option></select></label>${field('Base URL','provider-url',p.baseUrl,'url',true)}<label class="field full">API Key<input id="provider-key" type="password" autocomplete="off" placeholder="${p.hasKey?'已有密钥；留空保持不变':'本地模型可以不填'}"><label class="muted"><input type="checkbox" id="clear-key"> 清除已保存密钥</label></label>${area('模型名称（每行一个；也可获取模型列表）','provider-models',(p.models||[]).join('\n'))}</div><div class="inline-buttons"><button id="fetch-models">获取模型列表</button><button id="test-provider">测试首个模型</button></div><p class="form-result" id="provider-result"></p><p class="note">获取列表和测试会访问此服务商。测试会发送 ping；部分模型可能产生少量费用。</p>`,`<div>${id?'<button id="delete-provider">删除服务商</button>':''}</div><div><button id="cancel-provider">取消</button><button class="primary" id="save-provider">保存 API 配置</button></div>`);
  $('#provider-preset').onchange=()=>{const v=presets[$('#provider-preset').value];if(!v)return;$('#provider-name').value=v[0];$('#provider-type').value=v[1];$('#provider-url').value=v[2];$('#provider-models').value=v[3];};
  const data=()=>({id,name:$('#provider-name').value,type:$('#provider-type').value,baseUrl:$('#provider-url').value,apiKey:$('#clear-key').checked?'':$('#provider-key').value||(p.hasKey?undefined:''),models:$('#provider-models').value.split(/[\n,]/).map(s=>s.trim()).filter(Boolean)});
  async function operation(button,fn){const b=$(button);b.disabled=true;$('#provider-result').textContent='正在连接…';try{await fn();}catch(e){$('#provider-result').textContent=e.message;}finally{b.disabled=false;}}
  $('#fetch-models').onclick=()=>operation('#fetch-models',async()=>{const result=await invoke('provider:models',data());if(!result.ok)throw new Error(result.error);const models=[...new Set([...result.models,...data().models])];$('#provider-models').value=models.join('\n');$('#provider-result').textContent=`获取成功：${result.models.length} 个模型`;});
  $('#test-provider').onclick=()=>operation('#test-provider',async()=>{const d=data();if(!d.models[0])throw new Error('请先填写一个模型名称');const result=await invoke('provider:test',d,d.models[0]);if(!result.ok)throw new Error(result.error);$('#provider-result').textContent=`连接成功 · ${result.latency}ms\n${result.text}`;});
  $('#save-provider').onclick=()=>run(async()=>{await invoke('provider:save',data());$('#modal').close();toast('API 配置已保存；可批量分配给多位人物');});
  $('#cancel-provider').onclick=()=>$('#modal').close();
  if(id)$('#delete-provider').onclick=()=>run(async()=>{await invoke('provider:remove',id);$('#modal').close();toast('服务商已删除');});
}
// 事件委托让实时快照不打断按钮监听。
document.addEventListener('click',e=>{
  if(e.target.closest('#time-button'))timeModal();
  const moment=e.target.closest('[data-time]');if(moment){$('#modal').close();run(()=>invoke('town:time',Number(moment.dataset.time)));}
  const row=e.target.closest('.resident-row[data-id]');if(row){select(row.dataset.id);residentModal();}
  const nav=e.target.closest('.nav');if(nav)setPage(nav.dataset.page);
  const action=e.target.closest('[data-action]');if(action)run(()=>performAction(selected,action.dataset.action));
  const petRow=e.target.closest('[data-pet-id]');if(petRow){select(petRow.dataset.petId);petModal();}
  if(e.target.closest('#pet-edit'))petModal();
  if(e.target.closest('#pet-decide'))run(()=>invoke('town:decide',selected));
  const p=e.target.closest('[data-provider]');if(p)providerModal(p.dataset.provider);
  if(e.target.closest('#edit-person'))residentModal();
  if(e.target.closest('#open-chat'))chatModal();
  if(e.target.closest('#ask-ai')){const r=current();if(r.model.providerId==='demo')residentModal();else run(async()=>{const result=await invoke('town:decide',r.id);toast(result?.discarded?'人物状态已改变，本次决策已取消':'TA 已决定接下来做什么');});}
  if(e.target.closest('#player-actions'))playerActionModal();
  if(e.target.closest('#resident-actions'))residentActionModal();
  const characterAction=e.target.closest('[data-character-action]');if(characterAction){const id=characterAction.dataset.characterId,r=allPeople().find(p=>p.id===id);$('#modal').close();if(r)run(()=>performAction(id,characterAction.dataset.characterAction,{x:r.x,y:r.y}));}
  const playerAction=e.target.closest('[data-player-action]');if(playerAction){$('#modal').close();run(()=>performAction('player',playerAction.dataset.playerAction));}
  const playerExpression=e.target.closest('[data-player-expression]');if(playerExpression){$('#modal').close();run(()=>invoke('player:expression',playerExpression.dataset.playerExpression));}
  if(e.target.closest('#invite-dialogue'))inviteModal();
  const invite=e.target.closest('[data-invite]');if(invite){$('#modal').close();run(()=>invoke('town:invite',selected,invite.dataset.invite));}
  if(e.target.closest('#control-person')){releaseKeys();run(()=>invoke('town:control',state.controlledId===selected?null:selected));}
  if(e.target.closest('#deselect')){if(state.controlledId)run(()=>invoke('town:control',null));selected=null;inspectorSignature='';render();}
  const settingsTab=e.target.closest('[data-settings-tab]');if(settingsTab){document.querySelectorAll('[data-settings-tab]').forEach(b=>b.classList.toggle('active',b===settingsTab));$('#character-settings').hidden=settingsTab.dataset.settingsTab!=='residents';$('#pet-settings').hidden=settingsTab.dataset.settingsTab!=='pets';$('#model-settings').hidden=settingsTab.dataset.settingsTab!=='api';$('#life-settings').hidden=settingsTab.dataset.settingsTab!=='life';renderAPI();}
  if(e.target.closest('#talk'))run(()=>invoke('town:talk',selected,$('#partner').value));
  if(e.target.closest('#decide'))run(()=>invoke('town:decide',selected));
});
document.addEventListener('change',e=>{if(e.target.id==='raw-frame')frameOverride=Number(e.target.value)||null;});
document.addEventListener('submit',e=>{if(e.target.id!=='chat-form')return;e.preventDefault();if(chatSending)return;const text=$('#chat-input').value.trim();if(!text)return;const id=$('#modal').dataset.chatResident||selected;$('#chat-input').value='';chatSending=true;run(()=>invoke('town:chat',id,text)).finally(()=>chatSending=false);});
$('#search').oninput=e=>{filter=e.target.value.trim();renderList();};
$('#population-button').onclick=populationModal;
$('#pet-population-button').onclick=petPopulationModal;
let beforeSettingsRunning=true;
$('#open-settings').onclick=()=>{if(page==='world'){beforeSettingsRunning=state.running;releaseKeys();run(()=>invoke('town:config',{running:false}));setPage('api');$('#open-settings').textContent='返回小镇';}else returnGame();};
$('#open-3d').onclick=()=>run(()=>invoke('town:open3d'));
let pendingAPISettings=false;
function openAPISettings(){if(!state){pendingAPISettings=true;return;}if(page!=='api')$('#open-settings').click();document.querySelector('[data-settings-tab="api"]').click();pendingAPISettings=false;}
window.townAPI.onOpenSettings?.(openAPISettings);
function returnGame(){setPage('world');$('#open-settings').textContent='设置';run(()=>invoke('town:config',{running:beforeSettingsRunning}));}
$('#back-game').onclick=returnGame;
$('#journal-toggle').onclick=()=>$('.journal').hidden=!$('.journal').hidden;
$('#daily-logs-toggle').onclick=()=>window.TownLifeUI.openDiary();
$('#close-journal').onclick=()=>$('.journal').hidden=true;
$('#board-tools-toggle').onclick=()=>$('.canvas-tools').classList.toggle('opened');
$('#pause').onclick=()=>run(()=>invoke('town:config',{running:!state.running}));
$('#speed').onchange=e=>run(()=>invoke('town:config',{speed:Number(e.target.value)}));
$('#step').onclick=()=>run(()=>invoke('town:step'));
$('#grid').onchange=e=>run(()=>invoke('town:config',{grid:e.target.checked}));$('#zones').onchange=e=>run(()=>invoke('town:config',{zones:e.target.checked}));
$('#event-filter').onchange=renderEvents;
$('#add-provider').onclick=()=>providerModal();
$('#import-api').onclick=()=>run(async()=>{const options=await invoke('legacy:provider-options');modal('选择要复用的 API',`<p class="muted">可以只复制需要的服务商，再分配给人物。</p><div class="legacy-provider-choices">${options.map(p=>`<label><input type="checkbox" name="legacy-provider" value="${esc(p.id)}" ${p.imported?'disabled':''}><span><strong>${esc(p.name)}</strong><small>${p.imported?'已经复制':esc(p.models.join('、'))}</small></span></label>`).join('')||'<p class="empty">原 AI Chat 暂无 API 配置。</p>'}</div>`,`<span class="muted">复制后，人物仍保留各自的人设与记忆。</span><button class="primary" id="copy-selected-api">复制选中配置</button>`);$('#copy-selected-api').onclick=()=>run(async()=>{const ids=Array.from(document.querySelectorAll('[name=legacy-provider]:checked')).map(n=>n.value);if(!ids.length)throw new Error('请先选择要复制的 API');const n=await invoke('legacy:providers',ids);$('#modal').close();toast(`已复制 ${n} 个服务商，可以分配给人物`);});});
$('#autonomous').onchange=e=>run(async()=>{await invoke('town:config',{autonomous:e.target.checked});toast(e.target.checked?'模型自主生活已开启，会产生 API 调用':'模型自主生活已关闭');});
$('#save-schedule').onclick=()=>run(async()=>{await invoke('town:config',{apiInterval:Number($('#api-interval').value),dailyLimit:Number($('#daily-limit').value)});toast('调度设置已保存');});
$('#export').onclick=()=>run(async()=>{if(await invoke('town:export'))toast('已导出不含密钥的小镇存档');});
function applyZoom(){const board=$('#board');board.style.width=zoom*100+'%';board.style.height=zoom*100+'%';$('#zoom-label').textContent=Math.round(zoom*100)+'%';}
$('#zoom-in').onclick=()=>{zoom=Math.min(2,zoom+0.25);applyZoom();};$('#zoom-out').onclick=()=>{zoom=Math.max(1,zoom-0.25);applyZoom();};$('#fit').onclick=()=>{zoom=1;applyZoom();$('#board-wrap').scrollTo(0,0);};
function stageBounds(){const width=$('#board').clientWidth,height=$('#board').clientHeight;return{left:75,right:width-75,top:165,bottom:height-145};}
function point(e){const rect=$('#board').getBoundingClientRect(),s=stageBounds();return{x:90+(e.clientX-rect.left-s.left)/(s.right-s.left)*1420,y:120+(e.clientY-rect.top-s.top)/(s.bottom-s.top)*790};}
$('#board').addEventListener('pointerdown',e=>{const n=e.target.closest('.sprite');if(!n)return;select(n.dataset.id);dragging={id:n.dataset.id,startX:e.clientX,startY:e.clientY,moved:false,node:n};n.setPointerCapture(e.pointerId);});
$('#board').addEventListener('pointermove',e=>{if(!dragging)return;if(Math.hypot(e.clientX-dragging.startX,e.clientY-dragging.startY)>4)dragging.moved=true;if(dragging.moved){const s=stageBounds(),rect=$('#board').getBoundingClientRect();dragging.node.style.transition='none';dragging.node.style.left=Math.min(s.right,Math.max(s.left,e.clientX-rect.left))+'px';dragging.node.style.top=Math.min(s.bottom,Math.max(s.top,e.clientY-rect.top))+'px';}});
$('#board').addEventListener('pointerup',e=>{if(dragging){const d=dragging;dragging=null;d.node.style.transition='';if(d.moved)run(()=>invoke('town:teleport',d.id,point(e)));return;}if(e.target.closest('.board-caption,.zone,.sprite')||!selected)return;frameOverride=null;run(()=>invoke('town:move',selected,point(e)));});
$('#board').addEventListener('pointercancel',()=>dragging=null);
$('#modal').addEventListener('click',e=>{if(e.target===$('#modal')){const r=$('#modal').getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)$('#modal').close();}});
window.townAPI.subscribe(s=>{state=s;render();});
new ResizeObserver(()=>{if(state&&page==='world')renderSprites();}).observe($('#board'));
window.TownEmotionsUI.init({getState:()=>state,current,image:img,releaseKeys});
window.TownLifeUI.init({getState:()=>state,current,image:img,invoke,toast,releaseKeys,refresh:async()=>{const data=await invoke('town:get');state=data.state;render();}});
window.ModelAssignmentUI.init({getState:()=>state,releaseKeys,image:img,invoke,toast,addProvider:()=>providerModal(),refresh:async()=>{const data=await invoke('town:get');state=data.state;render();}});
run(async()=>{meta=await invoke('town:get');state=meta.state;catalog=meta.catalog;petCatalog=meta.petCatalog;selected=null;render();await initPlayerUI();if(pendingAPISettings)openAPISettings();});

const held=new Set();
function sendKeys(){if(!state?.controlledId)return;const x=(held.has('d')||held.has('arrowright')?1:0)-(held.has('a')||held.has('arrowleft')?1:0),y=(held.has('s')||held.has('arrowdown')?1:0)-(held.has('w')||held.has('arrowup')?1:0);run(()=>invoke('town:input',{x,y}));}
function releaseKeys(){held.clear();sendKeys();}
document.addEventListener('keydown',e=>{const key=e.key.toLowerCase();if(page!=='world'||document.querySelector('dialog[open]')||!state?.controlledId||e.target.matches('input,textarea,select')||!['w','a','s','d','arrowup','arrowdown','arrowleft','arrowright'].includes(key))return;e.preventDefault();if(!held.has(key)){held.add(key);sendKeys();}});
document.addEventListener('keyup',e=>{const key=e.key.toLowerCase();if(held.delete(key))sendKeys();});
window.addEventListener('blur',releaseKeys);

function initPlayerUI(){return window.PlayerUI.init({invoke,run,toast,getState:()=>state,getCatalog:()=>catalog,select,setPage,getPage:()=>page,returnGame,releaseKeys,refresh:async()=>{const data=await invoke('town:get');state=data.state;render();}});}

let petListSignature='';
function renderPetList(){
  const sig=JSON.stringify(state.pets.map(p=>[p.id,p.name,p.enabled,p.action,p.thinking,p.model,p.persona]))+selected;
  if(sig===petListSignature)return;petListSignature=sig;
  $('#pets').innerHTML=state.pets.map(p=>`<button class="resident-row" data-pet-id="${esc(p.id)}"><img class="resident-avatar" src="${img(p)}" alt=""><div><div class="name">${esc(p.name)}</div><div class="job">${esc(p.animal?.species||p.occupation)} · ${esc(p.animal?.breed||'')}<br>${p.enabled?'已入住':'等待邀请'} · ${esc(p.animal?.bodySize||'')}</div></div><span class="activity">${p.thinking?'感官更新':actionLabel(p)}</span></button>`).join('')||'<p class="empty">动物素材尚未载入。</p>';
}
function renderPetInspector(p){
  const sig=JSON.stringify([p.id,p.action,p.thinking,state.busy,p.model,p.presets]);if(sig===inspectorSignature)return;inspectorSignature=sig;
  const supported=(p.animal?.allowedActions||['idle','walk','rest']).filter(a=>Object.hasOwn(animalActions,a));
  $('#inspector').innerHTML=`<img class="interaction-portrait" src="${img(p)}" alt=""><div class="interaction-person"><strong>${esc(p.name)}</strong><span>${esc(p.animal?.species||'动物')} · ${actionLabel(p)}</span></div><div class="interaction-actions">${supported.slice(0,5).map(a=>`<button data-action="${a}">${animalActions[a]}</button>`).join('')}<button id="actor-diary">每日日志</button><button id="pet-edit">习性与模型</button>${p.model.providerId!=='demo'?`<button id="pet-decide" ${state.busy?'disabled':''}>观察自然行为</button>`:''}</div><button id="deselect" aria-label="取消选择">×</button>`;
}
function petPopulationModal(){
  modal('邀请动物加入小镇',`<p class="muted">${state.pets.length} 个自然动物档案。每个个体保持物种习性、独立模型和生活记录。</p><div class="gallery">${state.pets.map(p=>`<label class="gallery-item"><input type="checkbox" name="pet-enabled" value="${esc(p.id)}" ${p.enabled?'checked':''}><img src="${img(p)}" alt=""><strong>${esc(p.name)}</strong><small>${esc(p.animal?.species||p.occupation)} · ${esc(p.animal?.breed||'')}</small></label>`).join('')}</div>`,`<button id="cancel-pets">取消</button><button class="primary" id="save-pets">邀请选中的动物</button>`);
  $('#cancel-pets').onclick=()=>$('#modal').close();
  $('#save-pets').onclick=()=>run(async()=>{await invoke('town:pets',[...document.querySelectorAll('[name=pet-enabled]:checked')].map(n=>n.value));$('#modal').close();toast('动物邀请已保存');});
}
function petModal(){
  const p=current();if(!p)return;
  modal(`${esc(p.name)} 的动物档案`,`<div class="person-modal-summary"><img src="${img(p)}" alt=""><p>${esc(p.animal?.species||'动物')} / ${esc(p.animal?.breed||'')} / ${esc(p.animal?.coat||'')}<br>${esc(p.animal?.bodySize||'')} · ${esc(p.sex||p.gender)}<br>${esc(p.persona.personality)}</p></div><div class="form-grid">${field('个体名字','pet-name',p.name)}<label class="field">自然气质预设<select id="pet-preset"><option value="">保持当前</option>${(p.presets||[]).map(v=>`<option value="${esc(v.id)}">${esc(v.label)}</option>`).join('')}</select></label><label class="field full">感官与习性<textarea readonly rows="5">${esc([typeof p.animal?.senses==='string'?p.animal.senses:'按物种感官观察周边环境',p.animal?.behavior,'可执行自然行为：'+(p.animal?.allowedActions||[]).map(a=>animalActions[a]||a).join('、')].filter(Boolean).join('\n\n'))}</textarea></label><label class="field full">API 服务商<select id="pet-provider">${state.providers.map(v=>`<option value="${esc(v.id)}" ${v.id===p.model.providerId?'selected':''}>${esc(v.name)}</option>`).join('')}</select></label>${field('模型名称','pet-model',p.model.model,'text',true)}${field('Temperature（0–2）','pet-temp',p.model.temperature,'number')}${field('最大输出 Tokens','pet-tokens',p.model.maxTokens,'number')}</div><p class="note">API 返回物种允许的动作、感官代码与生理需求。无效输出转为本地习性。动物不说人话，也不会被赋予职业或人类社交。</p>`,`<button id="cancel-pet">取消</button><button class="primary" id="save-pet">保存动物配置</button>`);
  $('#pet-provider').onchange=()=>{const provider=state.providers.find(v=>v.id===$('#pet-provider').value);$('#pet-model').value=provider?.models?.[0]||'';};
  $('#pet-temp').step='.1';$('#pet-temp').min='0';$('#pet-temp').max='2';$('#pet-tokens').min='64';$('#pet-tokens').max='8192';
  $('#cancel-pet').onclick=()=>$('#modal').close();
  $('#save-pet').onclick=()=>run(async()=>{const data={name:$('#pet-name').value,model:{providerId:$('#pet-provider').value,model:$('#pet-model').value,temperature:Number($('#pet-temp').value),maxTokens:Number($('#pet-tokens').value)}};if($('#pet-preset').value)data.presetId=$('#pet-preset').value;await invoke('town:update',p.id,data);$('#modal').close();toast('动物配置已保存');});
}
