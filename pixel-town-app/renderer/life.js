'use strict';
(function(){
  const $=s=>document.querySelector(s),esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const types={profile:'档案',action:'行为',arrival:'到达',outcome:'进展',observation:'见闻',thought:'心声',speech:'交流',goal:'目标',relation:'关系',emotion:'心情',environment:'环境',system:'小镇',error:'异常',need:'感官需求'};
  const sources={api:'模型表达',engine:'实际进展',player:'玩家操作',manual:'手动行为',local:'本地生活',witness:'现场观察',heard:'听到的交流',history:'历史手记',environment:'环境变化',system:'系统记录'};
  let ctx,signature='',worldSignature='',dirty=false,diary=null,queryVersion=0,loading=false,lastDiaryRevision=-1,diaryTimer;
  const people=()=>[...ctx.getState().residents,...ctx.getState().pets,...(ctx.getState().player?[ctx.getState().player]:[])];
  const actor=id=>people().find(r=>r.id===id);
  const day=()=>Math.floor(ctx.getState().clock/1440)+1;
  const hhmm=n=>window.TownWorldTime?window.TownWorldTime.format(n):`${String(Math.floor(n/60)%24).padStart(2,'0')}:${String(Math.floor(n)%60).padStart(2,'0')}`;
  const subjects=()=>[...people().map(r=>({id:r.id,name:r.name,kind:r.kind,enabled:r.enabled})),{id:'town',name:'小镇',kind:'world'},{id:'sky-sun',name:'太阳',kind:'celestial'},{id:'sky-moon',name:'月亮',kind:'celestial'},...Object.entries({work:'工作区域',rest:'休息区域',play:'游玩区域',chat:'相遇区域'}).map(([id,name])=>({id:'place-'+id,name,kind:'place'}))];
  async function safe(fn){try{return await fn();}catch(e){ctx.toast(e.message);return null;}}
  function closeButton(d){d.querySelector('[data-life-close]').onclick=()=>{if(d.dataset.saving!=='true')d.close();};}
  function dialog(d,title,body,foot=''){
    ctx.releaseKeys();d.innerHTML=`<div class="modal-head"><h2>${esc(title)}</h2><button data-life-close aria-label="关闭">×</button></div><div class="modal-body">${body}</div>${foot?`<div class="modal-foot">${foot}</div>`:''}`;closeButton(d);if(!d.open)d.showModal();
  }
  function focusHtml(life){const f=life?.focus;return f?`<span class="life-eyebrow">${{ongoing:'当前的小目标',completed:'最近完成的目标',abandoned:'最近放下的目标'}[f.status]}</span><strong>${esc(f.title)}</strong><p>${esc(f.reason)}</p>`:'<span class="life-eyebrow">当前的小目标</span><p>还没有拟定。下次思考时，TA 可以根据人设和经历自己决定。</p>';}
  function update(){
    if(!ctx?.getState())return;const s=ctx.getState();
    const w=JSON.stringify(s.worldInfo);if(w!==worldSignature&&!dirty){worldSignature=w;const v=window.TownLife.world(s.worldInfo);for(const key of ['name','background','values','facts'])$('#world-'+key).value=v[key];}
    const sig=JSON.stringify(people().map(r=>[r.id,r.name,r.enabled,r.life,r.model.providerId]));
    if(sig!==signature){signature=sig;
      $('#life-people').innerHTML=s.residents.map(r=>`<article class="life-person"><img src="${ctx.image(r)}" alt=""><div><strong>${esc(r.name)}</strong><small>${esc(r.occupation)} · ${r.enabled?'已入住':'暂未入住'}</small><p>${esc(r.life?.focus?.title||r.life?.aspiration||window.TownLife.defaultProfile(r).aspiration)}</p><div class="life-card-actions"><button data-life-person="${esc(r.id)}">生活方向</button><button data-mood-person="${esc(r.id)}">心情</button><button data-diary-person="${esc(r.id)}">每日日志</button></div></div></article>`).join('');
      $('#life-other-count').textContent=`动物、主角和场景区域也分别保存日志。当前共 ${subjects().length} 个日志对象。`;
    }
    const r=ctx.current?.();if(r){
      const mind=$('#character-mind');
      if(mind&&r.life?.focus){mind.hidden=false;$('#character-thought').textContent=(r.thought?r.thought+' · ':'')+'想做：'+r.life.focus.title;}
    }
    if($('#daily-diary').open&&diary&&diary.day===day()&&!diary.olderLoaded&&!loading&&s.journalRevision!==lastDiaryRevision){clearTimeout(diaryTimer);diaryTimer=setTimeout(()=>{if($('#daily-diary').open)loadDiary();},600);}
  }
  function openPerson(id){
    const r=actor(id);if(!r||r.kind==='animal'||r.isPlayer)return;
    const life=window.TownLife.profile(r.life,r),d=$('#life-editor');
    const schedule=(r.schedule||[]).map(x=>`${x.start}–${x.end} · ${x.location} · ${x.behavior}`).join('\n');
    dialog(d,r.name+' · 生活方向',`<div class="life-profile-summary"><img src="${ctx.image(r)}" alt=""><p>${esc(r.occupation)}<br>${esc(r.persona.personality)}<br>兴趣：${esc(r.persona.likes)}</p></div><div class="life-focus">${focusHtml(life)}</div><div class="form-grid"><label class="field full">希望怎样生活<textarea id="life-aspiration" maxlength="300" rows="3">${esc(life.aspiration)}</textarea></label><label class="field full">日常参考与习惯<textarea id="life-routine" maxlength="500" rows="3">${esc(life.routine)}</textarea></label></div><p class="note">模型会参考这些方向，自己选择下一步。目标与日常是参考，允许按精力、时段和交流改变主意。</p>${schedule?`<details class="life-reference"><summary>职业作息参考</summary><pre>${esc(schedule)}</pre><p class="note">背景地点由当前公共区域承载，参考作息不会凭空创建建筑或物品。</p></details>`:''}<label class="life-reset"><input type="checkbox" id="life-reset"> 保存时清空当前目标，让 TA 重新拟定</label><p class="life-status" id="life-person-status" role="status"></p>`,`<button data-life-context="${esc(id)}">查看 TA 收到的资料</button><button class="primary" id="save-life-person">保存生活方向</button>`);
    $('#save-life-person').onclick=()=>safe(async()=>{
      const value={aspiration:$('#life-aspiration').value,routine:$('#life-routine').value,resetGoal:$('#life-reset').checked};const b=$('#save-life-person');b.disabled=true;d.dataset.saving='true';
      try{await ctx.invoke('town:life',id,value);d.close();ctx.toast('生活方向已保存，下次思考会带上这些资料');await ctx.refresh();}catch(e){$('#life-person-status').textContent=e.message;}finally{b.disabled=false;delete d.dataset.saving;}
    });
  }
  async function openContext(id){
    const value=await ctx.invoke('town:context',id),d=$('#life-context');
    dialog(d,value.name+'收到的基础资料',`<p class="note">这是下一次生活决策会收到的应用说明、独立人设、当前环境、目标和最近经历。查看资料不调用模型。</p><textarea readonly class="life-context-text" aria-label="模型基础资料"></textarea>`);
    d.querySelector('textarea').value=value.system;
  }
  function renderEntries(entries,append=false){
    const html=entries.map(e=>`<article class="diary-entry ${esc(e.type)}"><div><time>${hhmm(e.time)}</time><span>${esc(types[e.type]||e.type)}</span><small>${esc(sources[e.source]||e.source)}</small></div><p>${esc(e.text)}</p></article>`).join('');
    if(append)$('#diary-entries').insertAdjacentHTML('beforeend',html);else $('#diary-entries').innerHTML=html||'<p class="empty">这一天尚未记录到活动。日志从真实发生的经历开始，不补写虚构见闻。</p>';
  }
  async function loadDiary(append=false){
    if(!diary)return;const version=++queryVersion,request={...diary};loading=true;$('#diary-more').disabled=true;$('#diary-refresh').disabled=true;
    try{
      const p=await ctx.invoke('journal:get',request.id,{day:request.day,limit:120,cursor:append?request.cursor:null,type:request.type});
      if(version!==queryVersion||!$('#daily-diary').open)return;
      lastDiaryRevision=ctx.getState().journalRevision;diary.olderLoaded=append;
      diary.cursor=p.nextCursor;diary.hasMore=p.hasMore;
      const days=[...new Set([day(),p.day,...p.days])].sort((a,b)=>b-a);
      $('#diary-day').innerHTML=days.map(n=>`<option value="${n}" ${n===p.day?'selected':''}>第 ${n} 天</option>`).join('');
      $('#diary-subject').value=request.id;$('#diary-type').value=request.type;
      $('#diary-summary').textContent=`${p.subject.name} · 第 ${p.day} 天 · ${p.total} 条记录`+(request.type!=='all'?` · ${types[request.type]} ${p.filteredTotal} 条`:'')+(p.warning?' · '+p.warning:'');
      renderEntries(p.entries,append);$('#diary-more').hidden=!p.hasMore;
    }catch(e){if(version===queryVersion)$('#diary-summary').textContent='读取失败：'+e.message;}
    finally{if(version===queryVersion){loading=false;$('#diary-more').disabled=false;$('#diary-refresh').disabled=false;}}
  }
  function openDiary(id='town'){
    const d=$('#daily-diary');diary={id,day:day(),type:'all',cursor:null,hasMore:false};
    dialog(d,'每日日志',`<div class="diary-toolbar"><label>人物或事物<select id="diary-subject">${subjects().map(s=>`<option value="${esc(s.id)}" ${s.id===id?'selected':''}>${esc(s.name)}${s.enabled===false?'（暂未入住）':''}</option>`).join('')}</select></label><label>游戏日期<select id="diary-day"><option value="${day()}">第 ${day()} 天</option></select></label><label>记录类别<select id="diary-type"><option value="all">全部经历</option>${Object.entries(types).map(([k,v])=>`<option value="${k}">${v}</option>`).join('')}</select></label><button id="diary-refresh">刷新</button></div><p class="note" id="diary-summary">正在读取…</p><div class="diary-entries" id="diary-entries"></div><button id="diary-more" hidden>查看更早记录</button>`,`<span class="note">计划、心声与实际行为分别标记；日志按游戏日期持续保存。</span><button id="diary-export">导出这一天</button>`);
    $('#diary-subject').onchange=()=>{diary.id=$('#diary-subject').value;diary.day=day();diary.cursor=null;loadDiary();};
    $('#diary-day').onchange=()=>{diary.day=Number($('#diary-day').value);diary.cursor=null;loadDiary();};
    $('#diary-type').onchange=()=>{diary.type=$('#diary-type').value;diary.cursor=null;loadDiary();};
    $('#diary-more').onclick=()=>{if(!loading)loadDiary(true);};$('#diary-refresh').onclick=()=>loadDiary();
    $('#diary-export').onclick=()=>safe(async()=>{if(await ctx.invoke('journal:export',diary.id,diary.day))ctx.toast('这一天的完整日志已导出');});
    loadDiary();
  }
  function init(options){
    ctx=options;for(const id of ['life-editor','life-context','daily-diary']){const d=document.createElement('dialog');d.id=id;d.className='life-dialog';d.addEventListener('cancel',e=>{if(d.dataset.saving==='true')e.preventDefault();});document.body.appendChild(d);}
    const panel=$('#life-settings');panel.innerHTML=`<div class="life-intro"><div><span class="overline">让每一天都有自己的来由</span><h2>小镇基础资料与生活记录</h2><p>每次思考带上共同背景、当前功能、独立人设、持续目标和最近经历。人物可以主动追求小目标，接着自己的生活行动与交流。</p></div><button id="open-daily-diary">查看每日日志</button></div><form id="world-info-form" class="life-world-form"><div class="section-heading"><h3>大家共同知道的小镇</h3><button type="submit" class="primary">保存基础资料</button></div><div class="form-grid"><label class="field full">小镇名称<input id="world-name" maxlength="40" required></label><label class="field full">小镇背景<textarea id="world-background" rows="3" maxlength="2400"></textarea></label><label class="field full">相处方式与生活约定<textarea id="world-values" rows="3" maxlength="1600"></textarea></label><label class="field full">共同资料与背景事实<textarea id="world-facts" rows="3" maxlength="3000"></textarea></label></div><p class="note">当前功能、可用动作、时刻、邻居状态和人物自己的日志会自动补充。这里可以添加小镇背景与约定，模型会结合自己的身份理解。</p><p class="life-status" id="world-info-status" role="status"></p></form><div class="section-heading"><h3>各自的生活方向</h3><p class="note">每人独立保存目标。离镇时保留资料与经历。</p></div><div id="life-people" class="life-people"></div><p class="note" id="life-other-count"></p>`;
    $('#world-info-form').addEventListener('input',()=>dirty=true);
    $('#world-info-form').onsubmit=e=>{e.preventDefault();safe(async()=>{const form=e.currentTarget,value=Object.fromEntries(['name','background','values','facts'].map(k=>[k,$('#world-'+k).value]));const b=form.querySelector('button');b.disabled=true;try{await ctx.invoke('town:knowledge',value);dirty=false;worldSignature='';$('#world-info-status').textContent='基础资料已保存，之后的思考和交流会使用新资料。';await ctx.refresh();}catch(error){$('#world-info-status').textContent=error.message;}finally{b.disabled=false;}});};
    document.addEventListener('click',e=>{
      if(e.target.closest('#open-daily-diary,#actor-diary'))openDiary(ctx.current?.()?.id||'town');
      if(e.target.closest('#life-direction'))openPerson(ctx.current?.()?.id);
      const person=e.target.closest('[data-life-person]');if(person)openPerson(person.dataset.lifePerson);
      const diaryPerson=e.target.closest('[data-diary-person]');if(diaryPerson)openDiary(diaryPerson.dataset.diaryPerson);
      const context=e.target.closest('[data-life-context]');if(context)safe(()=>openContext(context.dataset.lifeContext));
    });update();
  }
  window.TownLifeUI={init,update,openDiary,openPerson,openContext};
})();
