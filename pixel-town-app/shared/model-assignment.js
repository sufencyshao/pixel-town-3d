(function(root,factory){
  if(typeof module==='object'&&module.exports)module.exports=factory();
  else root.ModelAssignment=factory();
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  const plain=v=>v&&typeof v==='object'&&!Array.isArray(v)&&[Object.prototype,null].includes(Object.getPrototypeOf(v));
  function plan(state,payload){
    if(!plain(payload))throw new Error('批量分配配置无效');
    for(const key of Reflect.ownKeys(payload))if(!['targets','configs','strategy','preserveParameters'].includes(key))throw new Error('批量分配包含未知设置');
    if(!Array.isArray(payload.targets)||!payload.targets.length||payload.targets.length>120||payload.targets.some(id=>typeof id!=='string')||new Set(payload.targets).size!==payload.targets.length)throw new Error('请选择 1–120 个不同的人物或动物');
    if(payload.targets.includes('player'))throw new Error('玩家主角由你操控，不参与批量 API 分配');
    if(!Array.isArray(payload.configs)||!payload.configs.length||payload.configs.length>120)throw new Error('请至少选择一组 API 配置');
    const strategy=payload.strategy||'round-robin';
    if(!['round-robin','grouped'].includes(strategy))throw new Error('不支持此分配方式');
    const preserve=payload.preserveParameters===undefined?true:payload.preserveParameters;
    if(typeof preserve!=='boolean')throw new Error('模型参数设置无效');
    const providers=new Map(state.providers.map(p=>[p.id,p]));
    const seen=new Set();
    const configs=payload.configs.map(c=>{
      if(!plain(c)||Reflect.ownKeys(c).some(k=>!['providerId','model','temperature','maxTokens'].includes(k)))throw new Error('API 分配条目无效');
      const provider=providers.get(c.providerId);
      if(!provider)throw new Error('API 配置已不存在，请重新选择');
      if(seen.has(provider.id))throw new Error('同一 API 配置不能重复选择');seen.add(provider.id);
      if(typeof c.model!=='string'||(provider.type!=='demo'&&!c.model.trim())||c.model.trim().length>120)throw new Error('请为「'+provider.name+'」填写有效的模型名称');
      if(!preserve&&(!Number.isFinite(c.temperature)||c.temperature<0||c.temperature>2||!Number.isInteger(c.maxTokens)||c.maxTokens<64||c.maxTokens>8192))throw new Error('Temperature 需要为 0–2，Tokens 需要为 64–8192 的整数');
      return {providerId:provider.id,model:provider.type==='demo'?'demo':c.model.trim(),temperature:c.temperature,maxTokens:c.maxTokens};
    });
    const selected=new Set(payload.targets),all=[...state.residents,...(state.pets||[])];
    const targets=all.filter(r=>selected.has(r.id));
    if(targets.length!==selected.size||targets.some(r=>r.isPlayer||!r.model))throw new Error('选择的人物或动物已不存在，请刷新后重试');
    const slots=[];
    if(strategy==='round-robin')targets.forEach((_,i)=>slots.push(i%configs.length));
    else{
      const per=Math.floor(targets.length/configs.length),extra=targets.length%configs.length;
      configs.forEach((_,i)=>{for(let n=0;n<per+(i<extra?1:0);n++)slots.push(i);});
    }
    const counts=configs.map(c=>({providerId:c.providerId,count:0}));
    const assignments=targets.map((r,i)=>{
      const c=configs[slots[i]];counts[slots[i]].count++;
      const before={providerId:r.model.providerId,model:r.model.model,temperature:r.model.temperature,maxTokens:r.model.maxTokens};
      const model={providerId:c.providerId,model:c.model,temperature:preserve?r.model.temperature:c.temperature,maxTokens:preserve?r.model.maxTokens:c.maxTokens};
      return {id:r.id,name:r.name,kind:r.kind,before,model};
    });
    return {assignments,counts,strategy};
  }
  return {plan};
});
