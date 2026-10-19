(function(){
  'use strict';
  let hooks,session;
  const q=s=>document.querySelector(s);
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const members=()=>[...hooks.getState().residents,...hooks.getState().pets];
  const providerOrder=()=>[...hooks.getState().providers.filter(p=>p.type!=='demo'),...hooks.getState().providers.filter(p=>p.type==='demo')];
  function init(h){
    hooks=h;
    for(const [anchorId,id,scope]of [['population-button','batch-resident-api','residents'],['pet-population-button','batch-pet-api','pets']]){
      const anchor=q('#'+anchorId),group=document.createElement('div');group.className='inline-buttons';anchor.before(group);
      const button=document.createElement('button');button.id=id;button.textContent='批量分配 API';button.onclick=()=>open(scope);group.append(button,anchor);
    }
    const button=document.createElement('button');button.id='batch-all-api';button.textContent='批量分配给人物';q('#add-provider').before(button);button.onclick=()=>open('all');
    const dialog=document.createElement('dialog');dialog.id='batch-api-editor';dialog.setAttribute('aria-labelledby','batch-api-title');document.body.append(dialog);
    dialog.addEventListener('cancel',e=>{if(session?.saving)e.preventDefault();});
    dialog.addEventListener('close',()=>{if(!dialog.open)session=null;});
    document.addEventListener('click',e=>{const button=e.target.closest('[data-batch-provider]');if(button)open('all',button.dataset.batchProvider);});
  }
  function open(scope='residents',providerId){
    const state=hooks.getState();if(!state)return;
    hooks.releaseKeys();
    const list=scope==='pets'?state.pets:scope==='all'?members():state.residents;
    const choices=providerOrder(),first=providerId||choices.find(p=>p.type!=='demo')?.id||'demo';
    session={scope,search:'',targets:new Set(list.filter(r=>r.enabled).map(r=>r.id)),configs:new Map(choices.map(p=>[p.id,{providerId:p.id,model:p.type==='demo'?'demo':p.models?.[0]||'',temperature:.8,maxTokens:300}])),selectedProviders:new Set([first]),strategy:'round-robin',preserveParameters:true,saving:false,saveError:''};
    const dialog=q('#batch-api-editor');
    dialog.innerHTML=`<div class="batch-head"><div><span class="batch-eyebrow">小镇设置 / API ASSIGNMENT</span><h2 id="batch-api-title">让一组 API 照顾多位居民</h2><p>选择人物与 API 配置，预览分配后一次保存。</p></div><button id="batch-close" aria-label="关闭批量分配">×</button></div><div class="batch-layout"><section class="batch-target-panel"><div class="batch-section-title"><h3>01 · 选择人物</h3><span id="batch-target-count"></span></div><div class="batch-target-filter"><select id="batch-scope" aria-label="显示的人物类型"><option value="residents">居民与人物</option><option value="pets">动物与宠物</option><option value="all">全部伙伴</option></select><input id="batch-search" placeholder="搜索名字或职业" aria-label="搜索批量分配人物"></div><div class="batch-selection-tools"><button id="batch-select-visible">全选当前列表</button><button id="batch-select-active">只选已入住</button><button id="batch-clear-targets">清空</button></div><div id="batch-target-list"></div></section><section class="batch-config-panel"><div class="batch-section-title"><h3>02 · 选择 API 配置</h3><button id="batch-add-api">添加 API</button></div><p class="batch-help">每个 Key 保存为一条 API 配置，即可重复分配给多人。</p><div class="batch-strategy"><label>分配方式<select id="batch-strategy"><option value="round-robin">轮流均分 · A / B / A / B</option><option value="grouped">按组均分 · A / A / B / B</option></select></label><label class="batch-preserve"><input type="checkbox" id="batch-preserve" checked> 保留各人物的 Temperature 与 Tokens</label></div><div id="batch-config-list"></div><section class="batch-review"><div class="batch-section-title"><h3>03 · 分配预览</h3><span id="batch-review-count"></span></div><div id="batch-counts"></div><div id="batch-preview"></div></section></section></div><div class="batch-footer"><p id="batch-message" role="status"></p><div><button id="batch-cancel">取消</button><button id="batch-apply" class="primary">应用分配</button></div></div>`;
    q('#batch-scope').value=scope;
    q('#batch-close').onclick=q('#batch-cancel').onclick=()=>{if(!session.saving)dialog.close();};
    q('#batch-add-api').onclick=()=>{dialog.close();hooks.addProvider();};
    q('#batch-scope').onchange=e=>{session.scope=e.target.value;renderTargets();};
    q('#batch-search').oninput=e=>{session.search=e.target.value.trim();renderTargets();};
    q('#batch-select-visible').onclick=()=>{visibleMembers().forEach(r=>session.targets.add(r.id));renderTargets();};
    q('#batch-select-active').onclick=()=>{session.targets=new Set(members().filter(r=>r.enabled&&matchesScope(r)).map(r=>r.id));renderTargets();};
    q('#batch-clear-targets').onclick=()=>{session.targets.clear();renderTargets();};
    q('#batch-strategy').onchange=e=>{session.strategy=e.target.value;preview(true);};
    q('#batch-preserve').onchange=e=>{session.preserveParameters=e.target.checked;setConfigControls();preview(true);};
    q('#batch-target-list').onchange=e=>{if(!e.target.matches('[data-batch-target]'))return;const id=e.target.dataset.batchTarget;if(e.target.checked)session.targets.add(id);else session.targets.delete(id);preview(true);};
    q('#batch-config-list').oninput=e=>{
      const row=e.target.closest('[data-batch-config]');if(!row)return;
      const id=row.dataset.batchConfig,config=session.configs.get(id);
      if(e.target.matches('[data-batch-api-check]')){if(e.target.checked)session.selectedProviders.add(id);else session.selectedProviders.delete(id);setConfigControls();}
      else if(e.target.dataset.batchField){const key=e.target.dataset.batchField;config[key]=key==='model'?e.target.value:Number(e.target.value);}
      preview(true);
    };
    q('#batch-apply').onclick=apply;
    renderConfigs();renderTargets();dialog.showModal();
  }
  function matchesScope(r){return session.scope==='all'||(session.scope==='pets'?r.kind==='animal':r.kind!=='animal');}
  function visibleMembers(){const term=session.search.toLowerCase();return members().filter(r=>matchesScope(r)&&(!term||[r.name,r.occupation].join(' ').toLowerCase().includes(term)));}
  function renderTargets(){
    const state=hooks.getState(),providers=new Map(state.providers.map(p=>[p.id,p]));
    q('#batch-target-list').innerHTML=visibleMembers().map(r=>`<label class="batch-target ${r.enabled?'':'inactive'}"><input type="checkbox" data-batch-target="${esc(r.id)}" ${session.targets.has(r.id)?'checked':''}><img src="${hooks.image(r)}" alt=""><span><strong>${esc(r.name)}</strong><small>${esc(r.occupation)} · ${r.enabled?'已入住':'未入住'}</small><small>${esc(providers.get(r.model.providerId)?.name||'配置不存在')} / ${esc(r.model.model)}</small></span></label>`).join('')||'<p class="empty">没有符合条件的人物。</p>';
    preview(true);
  }
  function renderConfigs(){
    q('#batch-config-list').innerHTML=providerOrder().map((p,i)=>{
      const c=session.configs.get(p.id);
      return `<div class="batch-config" data-batch-config="${esc(p.id)}"><label class="batch-config-name"><input type="checkbox" data-batch-api-check ${session.selectedProviders.has(p.id)?'checked':''}><span><strong>${esc(p.name)}</strong><small>${p.type==='demo'?'本地规则 · 不使用 API':p.hasKey?'密钥已保存': '无密钥 · 可用于本地服务'}</small></span></label><div class="batch-config-fields"><label class="batch-model-field">模型<input data-batch-field="model" aria-label="${esc(p.name)}的模型" maxlength="120" list="batch-models-${i}" value="${esc(c.model)}" placeholder="选择或填写模型"><datalist id="batch-models-${i}">${(p.models||[]).map(m=>`<option value="${esc(m)}"></option>`).join('')}</datalist></label><label>Temperature<input data-batch-field="temperature" aria-label="${esc(p.name)}的 Temperature" type="number" min="0" max="2" step="0.1" value="${c.temperature}"></label><label>最大 Tokens<input data-batch-field="maxTokens" aria-label="${esc(p.name)}的 Tokens" type="number" min="64" max="8192" step="1" value="${c.maxTokens}"></label></div></div>`;
    }).join('');
    setConfigControls();
  }
  function setConfigControls(){
    q('#batch-config-list').querySelectorAll('[data-batch-config]').forEach(row=>{
      const id=row.dataset.batchConfig,selected=session.selectedProviders.has(id),local=hooks.getState().providers.find(p=>p.id===id)?.type==='demo';row.classList.toggle('selected',selected);
      row.querySelectorAll('[data-batch-field]').forEach(input=>input.disabled=!selected||(input.dataset.batchField==='model'?local:session.preserveParameters));
    });
  }
  function payload(){return {targets:Array.from(session.targets),configs:providerOrder().filter(p=>session.selectedProviders.has(p.id)).map(p=>({...session.configs.get(p.id)})),strategy:session.strategy,preserveParameters:session.preserveParameters};}
  function preview(clearError=false){
    if(!session||session.saving)return;
    if(clearError)session.saveError='';
    q('#batch-target-count').textContent=`已选 ${session.targets.size} 位`;
    const names=new Map(hooks.getState().providers.map(p=>[p.id,p.name]));
    try{
      const plan=window.ModelAssignment.plan(hooks.getState(),payload());session.plan=plan;
      q('#batch-review-count').textContent=`${plan.assignments.length} 位 · ${plan.counts.length} 组配置`;
      q('#batch-counts').innerHTML=plan.counts.map(c=>`<span>${esc(names.get(c.providerId))} <b>${c.count}</b> 位</span>`).join('');
      q('#batch-preview').innerHTML=`<table><thead><tr><th>人物</th><th>分配后的 API / 模型</th><th>参数</th></tr></thead><tbody>${plan.assignments.map(a=>`<tr data-batch-preview="${esc(a.id)}"><td><strong>${esc(a.name)}</strong><small>${esc(names.get(a.before.providerId)||'原配置')} → ${esc(names.get(a.model.providerId))}</small></td><td>${esc(names.get(a.model.providerId))}<small>${esc(a.model.model)}</small></td><td>${a.model.temperature} / ${a.model.maxTokens}</td></tr>`).join('')}</tbody></table>`;
      q('#batch-apply').textContent=`应用到 ${plan.assignments.length} 位`;
      q('#batch-apply').disabled=!!hooks.getState().busy;
      message(session.saveError||(hooks.getState().busy?'当前模型任务完成后即可分配。':'只保存模型绑定与参数，不发起模型调用。'),!!session.saveError);
    }catch(error){session.plan=null;q('#batch-review-count').textContent='等待选择';q('#batch-counts').innerHTML='';q('#batch-preview').innerHTML='<p class="batch-preview-empty">选择人物和 API 后，分配结果会显示在这里。</p>';q('#batch-apply').textContent='应用分配';q('#batch-apply').disabled=true;message(error.message,false);}
  }
  function message(text,error){q('#batch-message').textContent=text;q('#batch-message').classList.toggle('error',error);}
  async function apply(){
    if(!session||session.saving)return;
    const current=session,data=payload();
    try{window.ModelAssignment.plan(hooks.getState(),data);}catch(error){message(error.message,true);return;}
    current.saving=true;q('#batch-api-editor').querySelectorAll('button,input,select').forEach(el=>el.disabled=true);q('#batch-apply').textContent='正在保存…';message('正在保存批量分配结果…',false);
    let result;
    try{result=await hooks.invoke('town:models:assign',data);}
    catch(error){if(session===current){current.saving=false;current.saveError='保存失败：'+error.message;q('#batch-api-editor').querySelectorAll('button,input,select').forEach(el=>el.disabled=false);setConfigControls();preview();}return;}
    // The assignment has already been committed; a refresh failure must not invite a second save.
    try{await hooks.refresh();}
    catch(error){if(session===current){q('#batch-api-editor').close();hooks.toast(`已保存 ${result.assigned} 位的 API 分配；界面刷新失败，请重新打开设置。`);}return;}
    if(session===current){q('#batch-api-editor').close();hooks.toast(`已为 ${result.assigned} 位人物 / 动物分配 API 配置`);}
  }
  function update(){
    if(!hooks?.getState())return;
    q('#providers').querySelectorAll('.provider-row').forEach((row,i)=>{
      const provider=hooks.getState().providers[i];if(!provider||row.querySelector('[data-batch-provider]'))return;
      const button=document.createElement('button');button.dataset.batchProvider=provider.id;button.textContent='分配给人物';row.append(button);
    });
    if(session&&!session.saving)preview();
  }
  window.ModelAssignmentUI={init,update,open};
})();
