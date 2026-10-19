/* Both hero styles live here: resident artwork with components, and free face editing. */
(function () {
  'use strict';
  let hooks, editor, profileSignature='', lastPreview=0;
  const cache=new Map(),loadedClips=new Set(),loadingClips=new Map();
  const escape=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const q=s=>document.querySelector(s);
  const groups=[['identity','身份与肤色','01'],['hair','发型与发色','02'],['face','五官与表情','03'],['body','体型与轮廓','04'],['clothes','衣物与配色','05'],['accessories','鞋帽与配饰','06']];
  const presetGroups=[['identity','身份与形象','01'],['preset','组件与配色','02'],['face','表情','03']];
  const gameMode=a=>a.styleMode==='preset';
  const activeGroups=()=>gameMode(editor.draft)?presetGroups:groups;
  const palettes={skin:['#FFE0BF','#F3C49B','#DBA47D','#BD805E','#955C42','#613D31'],hairColor:['#29232D','#58372C','#A56B3F','#D9B777','#C1C5CE','#A95E6D','#527E86'],eyeColor:['#473B35','#7F583A','#648765','#557B9C','#7B648C'],clothesColor:['#738E68','#E6D8B6','#769BAF','#B76E74','#C5A058','#484956'],accentColor:['#FFF1D2','#BB844F','#A4C0C1','#D8A1A4','#5E6B59'],bottomColor:['#4A5C77','#766653','#BAA084','#566D55','#383A43'],shoeColor:['#574337','#EAE4D2','#765C4D','#9E5A49','#34323C'],hatColor:['#C5A26F','#617D66','#995E5F','#E9DDC4','#414755'],accessoryColor:['#554E48','#C1A359','#C58091','#789797']};
  function pixels(a,frame){return window.PixelAvatar.renderPixels(a,frame);}
  function encode(p,key){
    const c=document.createElement('canvas');c.width=p.width;c.height=p.height;
    c.getContext('2d').putImageData(new ImageData(p.data,p.width,p.height),0,0);
    const url=c.toDataURL('image/png');cache.set(key,url);if(cache.size>180)cache.delete(cache.keys().next().value);return url;
  }
  function image(a,frame=1){
    const config=window.Appearance.normalize(a),key=JSON.stringify(config)+'/'+frame;
    if(cache.has(key))return cache.get(key);
    if(gameMode(config)&&!window.PresetAvatar.isLoaded(config.avatarPreset))return `../assets/characters/${config.avatarPreset}/frame_${String(Math.min(frame,16)).padStart(2,'0')}.png`;
    return encode(pixels(config,frame),key);
  }
  function animationEntity(entity){return {...entity,animation:window.PresetAvatar.getAnimation(entity.appearance.avatarPreset)};}
  async function prepareAction(entity,action){
    if(action==='lie_down'){await sideLyingFrames(entity);return;}
    if(entity.appearance.styleMode!=='preset'||window.TownRecoveryPoses.is(action))return;
    const clip=window.TownAnimation.clipFor(animationEntity({...entity,action,moving:false,target:null}));
    if(!clip)return;
    await window.PresetAvatar.ensureAnimation(entity.appearance.avatarPreset,clip.key);
    loadedClips.add(entity.appearance.avatarPreset+'/'+clip.key);
  }
  function clipFor(entity){
    const moving=entity.moving||(entity.target&&Math.hypot(entity.x-entity.target.x,entity.y-entity.target.y)>5);
    if(!moving&&entity.action==='idle'&&['left','right','back'].includes(entity.direction))return null;
    return window.TownAnimation.clipFor(animationEntity(entity));
  }
  function animationImage(entity,elapsed,fallbackFrame){
    const sample=window.TownAnimation.sample(animationEntity(entity),elapsed);
    if(!sample)return image(entity.appearance,fallbackFrame);
    const clipKey=entity.appearance.avatarPreset+'/'+sample.key;
    if(!loadedClips.has(clipKey)){
      if(!loadingClips.has(clipKey))loadingClips.set(clipKey,window.PresetAvatar.ensureAnimation(entity.appearance.avatarPreset,sample.key).then(()=>loadedClips.add(clipKey)).catch(error=>hooks.toast('动作素材加载失败：'+error.message)).finally(()=>loadingClips.delete(clipKey)));
      return image(entity.appearance,fallbackFrame);
    }
    const key=JSON.stringify(entity.appearance)+'/clip/'+sample.key+'/'+sample.frame;
    return cache.get(key)||encode(window.PresetAvatar.renderAnimationPixels(entity.appearance,sample.key,sample.frame),key);
  }
  function tab(){q('[data-settings-tab="player"]').click();}
  async function init(h){
    hooks=h;
    try{await Promise.all(window.Appearance.gamePresets.map(p=>window.PresetAvatar.ensureLoaded(p.id,hooks.getCatalog().find(c=>c.asset===p.id)?.animation)));}
    catch(error){hooks.toast('形象素材加载失败：'+error.message);}
    const button=document.createElement('button');button.id='player-entry';button.title='选择和创建你的主角';button.textContent='创建主角';q('#open-settings').before(button);
    const t=document.createElement('button');t.dataset.settingsTab='player';t.textContent='我的主角';q('.settings-tabs').prepend(t);
    const section=document.createElement('section');section.id='player-settings';section.hidden=true;q('#character-settings').before(section);
    const dialog=document.createElement('dialog');dialog.id='player-editor';dialog.setAttribute('aria-labelledby','player-editor-title');document.body.append(dialog);
    q('#player-entry').onclick=()=>{if(hooks.getPage()==='world')q('#open-settings').click();tab();};
    document.addEventListener('click',e=>{
      const settings=e.target.closest('[data-settings-tab]');if(settings)q('#player-settings').hidden=settings.dataset.settingsTab!=='player';
      if(e.target.closest('#create-player,#edit-player'))open();
      if(e.target.closest('#play-as-player'))hooks.run(async()=>{hooks.returnGame();hooks.select('player');await hooks.invoke('town:control','player');});
    });
    dialog.addEventListener('cancel',e=>{if(editor?.saving){e.preventDefault();return;}hooks.releaseKeys();editor=null;});
    dialog.addEventListener('close',()=>{if(!dialog.open){hooks.releaseKeys();editor=null;}});
    update(hooks.getState());
    requestAnimationFrame(animate);
  }
  function update(state){
    if(!state||!hooks||!q('#player-entry'))return;
    const p=state.player;
    const signature=JSON.stringify(p?[p.name,p.appearance]:null);
    if(signature===profileSignature&&q('#player-settings').children.length)return;profileSignature=signature;
    q('#player-entry').innerHTML=p?`<img src="${image(p.appearance)}" alt=""><span>${escape(p.name)}</span>`:'创建主角';
    const gender=p?window.Appearance.fields.find(f=>f.key==='gender').options.find(o=>o.value===p.appearance.gender)?.label:'';
    q('#player-settings').innerHTML=`<div class="player-setting-heading"><div><h2>你的故事，从你开始。</h2><p>游戏预设与自由捏脸，两种形象方案都为你保留。</p></div><button class="primary" id="${p?'edit-player':'create-player'}">${p?'更换主角形象':'创建我的主角'}</button></div><div class="player-profile"><div class="player-profile-stage">${p?`<img src="${image(p.appearance)}" alt="${escape(p.name)}的主角形象">`:`<div class="profile-samples">${window.Appearance.gamePresets.slice(0,3).map(p=>`<img src="${image({...window.Appearance.defaults,avatarPreset:p.id})}" alt="${escape(p.label)}参考形象">`).join('')}</div>`}<div class="pixel-ground"></div></div><div class="player-profile-copy"><span class="overline">${p?'我的小镇身份':'还没有选择主角'}</span><h3>${p?escape(p.name):'选择属于你的生活模样'}</h3><p>${p?escape(gender)+' · '+(gameMode(p.appearance)?'游戏预设形象':'自由捏脸形象'):'选择与邻居同画风的预设，搭配颜色和小组件；也可切换到原来的自由捏脸。'}</p><p class="player-description">创建后进入小镇，通过 WASD 或方向键自由移动，也可以点击地面走过去，与邻居相遇。</p>${p?'<button id="play-as-player">用这个主角进入小镇</button>':'<p class="muted">主角独立保存，居民人数与现有 NPC 保持各自设置。</p>'}</div></div><div class="player-feature-notes"><span>游戏预设形象</span><span>可替换组件</span><span>自由捏脸保留</span><span>正面 · 侧面 · 背面</span></div>`;
  }
  function open(){
    const saved=hooks.getState().player;
    editor={draft:window.Appearance.normalize(saved?.appearance||window.Appearance.defaults),name:saved?.name||'夏风',group:'identity',direction:'front',action:'idle',closeup:false,saving:false};
    const dialog=q('#player-editor');
    dialog.innerHTML=`<div class="creator-head"><div><span class="creator-eyebrow">我的主角 / CHARACTER</span><h2 id="player-editor-title">捏一个你喜欢的自己</h2></div><nav class="creator-mode-switch" aria-label="主角形象方案"><button data-style-mode="preset">游戏预设形象<small>与小镇居民同画风 · 配色与组件</small></button><button data-style-mode="custom">自由捏脸<small>保留原方案 · 五官与身体参数</small></button></nav><button id="close-player-editor" aria-label="关闭捏脸">×</button></div><div class="creator-layout"><aside class="creator-preview"><div class="creator-preview-caption"><span>实时预览</span><button id="toggle-face-preview">看五官</button></div><div class="creator-avatar-stage"><canvas id="creator-canvas" width="128" height="160" aria-label="主角实时像素预览"></canvas><span class="creator-stage-ground"></span></div><div class="creator-view-controls">${[['front','正面'],['left','左侧'],['right','右侧'],['back','背面']].map(([v,l])=>`<button data-view="${v}" class="${v==='front'?'active':''}">${l}</button>`).join('')}</div><select id="creator-pose" aria-label="预览动作"><option value="idle">站立</option><option value="walk">走路</option><option value="greet">挥手</option><option value="cheer">欢呼</option><option value="rest">坐下</option><option value="jump">跳跃</option></select><p class="creator-preview-note">换个角度，看看每一个细节。</p><div class="creator-presets"><span>从一个造型开始</span><div>${window.Appearance.presets.map(p=>`<button data-preset="${p.id}" title="${escape(p.label)}"><img src="${image(p.appearance)}" alt="${escape(p.label)}"><small>${escape(p.label)}</small></button>`).join('')}</div></div></aside><section class="creator-customization"><nav class="creator-tabs">${groups.map(([key,label,num])=>`<button data-group="${key}" class="${key==='identity'?'active':''}"><small>${num}</small>${label}</button>`).join('')}</nav><div class="creator-controls" id="creator-controls"></div></section></div><div class="creator-footer"><div><button id="random-player">随机外貌</button><button id="reset-player">恢复初始造型</button></div><div><button id="cancel-player">暂不保存</button><button id="save-player" class="primary">保存并进入小镇</button></div></div>`;
    hooks.releaseKeys();dialog.showModal();renderModeUI();renderControls();drawPreview(0);
    q('#close-player-editor').onclick=q('#cancel-player').onclick=()=>{if(!editor.saving)dialog.close();};
    q('#toggle-face-preview').onclick=()=>{editor.closeup=!editor.closeup;q('#toggle-face-preview').textContent=editor.closeup?'看全身':'看五官';drawPreview(0);};
    q('#creator-pose').onchange=e=>{editor.action=e.target.value;if(!['idle','walk'].includes(editor.action)){editor.direction='front';selectDirection();}drawPreview(0);};
    q('#random-player').onclick=()=>{if(gameMode(editor.draft)){const p=window.Appearance.gamePresets[Math.floor(Math.random()*window.Appearance.gamePresets.length)];editor.draft={...editor.draft,avatarPreset:p.id,gender:p.gender,presetHairColor:'original',presetClothesColor:'original',presetSkinColor:'original',presetEyeColor:'original',presetAccessory:'none'};}else setCustomLook(window.Appearance.randomize());renderModeUI();renderControls();drawPreview(0);};
    q('#reset-player').onclick=()=>{editor.draft=window.Appearance.normalize(saved?.appearance||window.Appearance.defaults);editor.group='identity';renderModeUI();renderControls();drawPreview(0);};
    dialog.onclick=e=>{
      if(editor?.saving)return;
      const mode=e.target.closest('button[data-style-mode]');if(mode){editor.draft.styleMode=mode.dataset.styleMode;editor.group='identity';renderModeUI();renderControls();drawPreview(0);}
      const group=e.target.closest('[data-group]');if(group){editor.group=group.dataset.group;renderControls();}
      const view=e.target.closest('[data-view]');if(view){editor.direction=view.dataset.view;if(!['idle','walk'].includes(editor.action)){editor.action='idle';q('#creator-pose').value='idle';}selectDirection();drawPreview(0);}
      const preset=e.target.closest('[data-preset]');if(preset){if(gameMode(editor.draft)){const p=window.Appearance.gamePresets.find(p=>p.id===preset.dataset.preset);editor.draft.avatarPreset=p.id;editor.draft.gender=p.gender;}else setCustomLook(window.Appearance.presets.find(p=>p.id===preset.dataset.preset).appearance);renderModeUI();renderControls();drawPreview(0);}
      const color=e.target.closest('[data-color]');if(color){editor.draft[color.dataset.key]=color.dataset.color;renderControls();drawPreview(0);}
    };
    q('#save-player').onclick=()=>hooks.run(async()=>{
      if(editor.saving)return;const name=editor.name.trim();if(!name)throw new Error('给主角起一个名字吧');
      const session=editor;session.saving=true;
      dialog.querySelectorAll('button,input,select').forEach(el=>el.disabled=true);
      q('#save-player').textContent='正在保存…';
      try{
        await hooks.invoke('player:save',{name,appearance:{...session.draft}});
        await hooks.refresh();if(editor!==session)return;
        dialog.close();hooks.returnGame();hooks.select('player');await hooks.invoke('town:control','player');hooks.toast('主角已保存，WASD / 方向键开始你的生活');
      }finally{if(editor===session){session.saving=false;dialog.querySelectorAll('button,input,select').forEach(el=>el.disabled=false);q('#save-player').textContent='保存并进入小镇';}}
    });
  }
  function setCustomLook(look){
    for(const f of window.Appearance.fields.filter(f=>groups.some(g=>g[0]===f.group)))editor.draft[f.key]=look[f.key];
    editor.draft.styleMode='custom';
  }
  function renderModeUI(){
    const preset=gameMode(editor.draft),dialog=q('#player-editor');dialog.dataset.styleMode=editor.draft.styleMode;
    dialog.querySelectorAll('[data-style-mode]').forEach(b=>b.classList.toggle('active',b.dataset.styleMode===editor.draft.styleMode));
    q('#player-editor-title').textContent=preset?'选择你的小镇形象':'捏一个你喜欢的自己';
    q('.creator-tabs').innerHTML=activeGroups().map(([key,label,num])=>`<button data-group="${key}" class="${editor.group===key?'active':''}"><small>${num}</small>${label}</button>`).join('');
    const options=preset?window.Appearance.gamePresets:window.Appearance.presets;
    q('.creator-presets').innerHTML=`<span>${preset?'小镇形象预设':'从一个造型开始'}</span><div>${options.map(p=>`<button data-preset="${p.id}" class="${preset&&editor.draft.avatarPreset===p.id?'active':''}" title="${escape(p.label)}"><img src="${image(preset?{...window.Appearance.defaults,avatarPreset:p.id}:p.appearance)}" alt="${escape(p.label)}"><small>${escape(p.label)}</small></button>`).join('')}</div>`;
    q('.creator-preview-note').textContent=preset?'原有人物素材 · 与邻居相同的比例和笔触。':'换个角度，看看每一个细节。';
  }
  function selectDirection(){q('#player-editor').querySelectorAll('[data-view]').forEach(b=>b.classList.toggle('active',b.dataset.view===editor.direction));}
  function renderControls(){
    q('#player-editor').querySelectorAll('[data-group]').forEach(b=>b.classList.toggle('active',b.dataset.group===editor.group));
    const preset=gameMode(editor.draft),title=activeGroups().find(g=>g[0]===editor.group)[1];
    const fields=window.Appearance.fields.filter(f=>preset?(editor.group==='identity'?['gender','avatarPreset'].includes(f.key):editor.group==='face'?f.key==='expression':f.group==='preset'&&f.key!=='avatarPreset'||f.key==='accessoryColor'):f.group===editor.group);
    if(preset&&editor.group==='preset'){const order=['presetAccessory','accessoryColor','presetHairColor','presetClothesColor','presetSkinColor','presetEyeColor'];fields.sort((a,b)=>order.indexOf(a.key)-order.indexOf(b.key));}
    q('#creator-controls').innerHTML=`<div class="creator-group-heading"><h3>${title}</h3><span>每次调整都会立即呈现</span></div>${editor.group==='identity'?`<label class="creator-name-field">主角姓名<input id="player-name" maxlength="30" value="${escape(editor.name)}" placeholder="你希望大家如何称呼你" autocomplete="off"></label>`:''}${preset?`<p class="creator-mode-note">${editor.group==='identity'?'先选择完整形象，再搭配小组件。发型和服装版型随预设切换。':editor.group==='preset'?'原配色保留素材的笔触和明暗；换色与附加组件随动作一起显示。':'表情只调整面部细节，保留原有角色的画风。'}</p>`:''}<div class="creator-field-list">${fields.map(f=>field(f)).join('')}</div>`;
    if(q('#player-name'))q('#player-name').oninput=e=>editor.name=e.target.value;
    q('#creator-controls').querySelectorAll('[data-field]').forEach(input=>input.addEventListener('input',()=>{
      const f=window.Appearance.fields.find(f=>f.key===input.dataset.field),value=f.type==='range'?Number(input.value):input.value;
      editor.draft[f.key]=value;
      if(preset&&f.key==='avatarPreset'){editor.draft.gender=window.Appearance.gamePresets.find(p=>p.id===value).gender;renderModeUI();renderControls();}
      if(preset&&f.key==='gender'&&value!=='nonbinary'){
        const current=window.Appearance.gamePresets.find(p=>p.id===editor.draft.avatarPreset);
        if(current.gender!==value){editor.draft.avatarPreset=window.Appearance.gamePresets.find(p=>p.gender===value).id;renderModeUI();renderControls();}
      }
      if(f.type==='range')input.closest('.creator-field').querySelector('output').textContent=rangeLabel(f,value);
      if(f.type==='color'){input.closest('.creator-field').querySelector('.color-value').textContent=value.toUpperCase();input.closest('.creator-field').querySelectorAll('.color-swatch').forEach(b=>b.classList.toggle('active',b.dataset.color.toUpperCase()===value.toUpperCase()));}
      drawPreview(0);
    }));
  }
  function rangeLabel(f,value){return ({blush:['无','淡','适中','明显'],freckles:['无','淡','适中','明显'],height:['矮小','偏矮','适中','偏高','高挑'],build:['纤细','偏瘦','适中','丰润','圆润'],shoulders:['窄肩','偏窄','适中','偏宽','宽肩'],chest:['平缓','轻微','适中','饱满','丰满']})[f.key][value];}
  function field(f){
    const value=editor.draft[f.key];
    if(f.type==='select')return `<label class="creator-field select-field"><span>${escape(f.label)}</span><select data-field="${f.key}" aria-label="${escape(f.label)}">${f.options.map(o=>`<option value="${o.value}" ${value===o.value?'selected':''}>${escape(o.label)}</option>`).join('')}</select></label>`;
    if(f.type==='range')return `<label class="creator-field range-field"><span>${escape(f.label)}<output>${rangeLabel(f,value)}</output></span><input type="range" data-field="${f.key}" aria-label="${escape(f.label)}" min="${f.min}" max="${f.max}" step="${f.step||1}" value="${value}"><div class="range-endpoints"><small>${f.key==='height'?'矮小':f.key==='build'?'纤细':f.key==='shoulders'?'窄肩':f.key==='chest'?'平缓':'无'}</small><small>${f.key==='height'?'高挑':f.key==='build'?'圆润':f.key==='shoulders'?'宽肩':f.key==='chest'?'丰满':'明显'}</small></div></label>`;
    const paletteKey=f.key==='presetSkinColor'?'skin':f.key.startsWith('preset')?f.key[6].toLowerCase()+f.key.slice(7):f.key;
    const colors=palettes[paletteKey]||palettes.hairColor;
    return `<div class="creator-field color-field"><span>${escape(f.label)}<small class="color-value">${value==='original'?'原配色':escape(value.toUpperCase())}</small></span><div class="color-choices">${f.allowOriginal?`<button class="original-swatch ${value==='original'?'active':''}" data-key="${f.key}" data-color="original">原色</button>`:''}${colors.map(c=>`<button class="color-swatch ${c.toUpperCase()===value.toUpperCase()?'active':''}" data-key="${f.key}" data-color="${c}" style="--swatch:${c}" title="${escape(f.label)} ${c}" aria-label="${escape(f.label)} ${c}"></button>`).join('')}<label class="custom-color" title="自选颜色"><input type="color" value="${value==='original'?colors[0]:value}" data-field="${f.key}" aria-label="自选${escape(f.label)}"></label></div></div>`;
  }
  function previewFrame(t){
    if(editor.action==='walk'){const phase=Math.floor(t/180)%3;return ({front:[1,2,3],left:[4,5,6],right:[7,8,9],back:[10,17,18]})[editor.direction][phase];}
    if(editor.action==='greet')return 14;if(editor.action==='rest')return 16;if(editor.action==='jump')return 13;if(editor.action==='cheer')return Math.floor(t/350)%2?11:12;
    return {front:1,left:4,right:7,back:10}[editor.direction];
  }
  function drawPreview(t){
    if(!editor||!q('#player-editor').open)return;
    let p;
    if(gameMode(editor.draft)&&editor.action==='cheer'){
      const entity={appearance:editor.draft,action:'cheer',kind:'human'},clip=clipFor(entity);
      if(clip&&isAnimationReady(entity,clip.key)){const sample=window.TownAnimation.sample(animationEntity(entity),t);p=window.PresetAvatar.renderAnimationPixels(editor.draft,sample.key,sample.frame);}
      else{p=pixels(editor.draft,1);prepareAction(entity,'cheer').catch(error=>hooks.toast('动作素材加载失败：'+error.message));}
    }else p=pixels(editor.draft,previewFrame(t));
    const canvas=q('#creator-canvas'),ctx=canvas.getContext('2d');
    if(editor.closeup){const region=window.PixelAvatar.getFaceRegion(editor.draft);const source=document.createElement('canvas');source.width=p.width;source.height=p.height;source.getContext('2d').putImageData(new ImageData(p.data,p.width,p.height),0,0);canvas.width=region.width;canvas.height=region.height;ctx.imageSmoothingEnabled=false;ctx.clearRect(0,0,region.width,region.height);ctx.drawImage(source,region.x,region.y,region.width,region.height,0,0,region.width,region.height);canvas.classList.add('face-closeup');}
    else{canvas.width=p.width;canvas.height=p.height;ctx.putImageData(new ImageData(p.data,p.width,p.height),0,0);canvas.classList.remove('face-closeup');}
  }
  function animate(t){if(editor&&t-lastPreview>90){drawPreview(t);lastPreview=t;}requestAnimationFrame(animate);}
  const isAnimationReady=(entity,key)=>loadedClips.has(entity.appearance.avatarPreset+'/'+key);
  async function sideLyingFrames(entity){
    const config=window.Appearance.normalize(entity.appearance),key=JSON.stringify(config)+'/side-lying-v1';
    if(gameMode(config)){
      await window.PresetAvatar.ensureLoaded(config.avatarPreset);
      const frames=await window.PresetAvatar.ensureAnimation(config.avatarPreset,'lie_down');
      return frames.map((_,n)=>cache.get(key+'/'+n)||encode(window.PresetAvatar.renderAnimationPixels(config,'lie_down',n),key+'/'+n));
    }
    return Array.from({length:4},(_,n)=>cache.get(key+'/'+n)||encode(window.SideLyingAvatar.renderPixels(config,n),key+'/'+n));
  }
  window.PlayerUI={init,update,image,clipFor,animationImage,isAnimationReady,prepareAction,sideLyingFrames};
})();
