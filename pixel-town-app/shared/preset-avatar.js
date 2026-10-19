(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(require('./sprite-regions'));
  else root.PresetAvatar = factory(root.SpriteRegions);
})(typeof globalThis !== 'undefined' ? globalThis : this, function (Regions) {
  'use strict';
  const width = 256, height = 256;
  const faceRegion = Object.freeze({ x: 62, y: 8, width: 132, height: 116 });
  const presetIds = Object.freeze(['01_hero_male','02_hero_female','03_barista_male','10_musician_male','12_florist_female','16_librarian_female','18_artist_female','20_student_female']);
  const cache = new Map(), pending = new Map(), clipPending = new Map(), analysisCache = new WeakMap();
  const colorKeys = ['presetHairColor','presetClothesColor','presetSkinColor','presetEyeColor'];
  const clipNames = ['idle','walk_down','walk_left','walk_right','walk_up','wave','surprise','sit','jump','cheer','work','nod','shake_head','chat','lie_down'];
  function checkedId(id) { if (!presetIds.includes(id)) throw new TypeError('未知角色预设: ' + id); return id; }
  function rgb(hex) { return [1,3,5].map(i=>parseInt(hex.slice(i,i+2),16)); }
  function options(input) {
    if (!input || typeof input !== 'object') throw new TypeError('预设外观必须是对象');
    const a = { ...input, avatarPreset: checkedId(input.avatarPreset || presetIds[0]), presetAccessory: input.presetAccessory || 'none', accessoryColor: input.accessoryColor || '#80644F', expression: input.expression || 'neutral' };
    for (const key of colorKeys) { a[key] = input[key] === undefined ? 'original' : input[key]; if (a[key] !== 'original' && (typeof a[key] !== 'string' || !/^#[0-9a-f]{6}$/i.test(a[key]))) throw new TypeError('无效预设颜色: ' + key); }
    if (!['none','glasses','roundGlasses','ribbon','scarf'].includes(a.presetAccessory)) throw new TypeError('无效预设配饰');
    if (!/^#[0-9a-f]{6}$/i.test(a.accessoryColor)) throw new TypeError('无效配饰颜色');
    if (!['neutral','happy','shy','serious','surprised','sad'].includes(a.expression)) throw new TypeError('无效预设表情');
    return a;
  }
  function copyImage(image) {
    if (!image || image.width !== width || image.height !== height || !image.data || image.data.length !== width*height*4) throw new TypeError('预设帧必须是 256×256 RGBA');
    return { width, height, data: new Uint8ClampedArray(image.data) };
  }
  function atlasFrames(image) {
    if (!image || image.height !== height || !Number.isInteger(image.width/width) || image.width<width || image.data.length!==image.width*height*4) throw new TypeError('无效预设动作图集');
    const frames=[];
    for(let n=0;n<image.width/width;n++){const data=new Uint8ClampedArray(width*height*4);for(let y=0;y<height;y++)data.set(image.data.subarray((y*image.width+n*width)*4,(y*image.width+(n+1)*width)*4),y*width*4);frames.push({width,height,data});}
    return frames;
  }
  // Test/server injection accepts an array (1-based frame numbers at array index 0),
  // or {frames: [...], walkUp: RGBA atlas, animation: metadata, animations: {name: atlas|frames}}.
  function registerPreset(id, input) {
    checkedId(id);
    const source=Array.isArray(input)?input:input?.frames;
    if(!source || source.length<16)throw new TypeError('至少需要16张预设帧');
    const frames=Array.from(source,image=>copyImage(image));
    const animations=new Map();
    if(input.walkUp)animations.set('walk_up',atlasFrames(input.walkUp));
    if(input.animations)for(const [name,images] of Object.entries(input.animations)){if(!clipNames.includes(name))throw new TypeError('未知动画');animations.set(name,Array.isArray(images)?images.map(copyImage):atlasFrames(images));}
    if(frames.length<18){const up=animations.get('walk_up');frames[16]=up?copyImage(up[Math.min(4,up.length-1)]):copyImage(frames[9]);frames[17]=up?copyImage(up[Math.min(12,up.length-1)]):copyImage(frames[9]);}
    const entry={frames,animations,animation:input.animation||null};cache.set(id,entry);return entry;
  }
  function isLoaded(id) { return presetIds.includes(id) && cache.has(id); }
  function assetUrl(id, relative) { return new URL('../assets/characters/'+checkedId(id)+'/'+relative, document.baseURI).href; }
  function loadImage(url) {
    return new Promise((resolve,reject)=>{const image=new Image();image.onload=()=>{try{const canvas=document.createElement('canvas');canvas.width=image.naturalWidth;canvas.height=image.naturalHeight;const context=canvas.getContext('2d',{willReadFrequently:true});context.imageSmoothingEnabled=false;context.drawImage(image,0,0);const pixels=context.getImageData(0,0,canvas.width,canvas.height);resolve({width:canvas.width,height:canvas.height,data:pixels.data});}catch(error){reject(error);}};image.onerror=()=>reject(new Error('无法加载原始角色素材: '+url));image.src=url;});
  }
  function loadJSON(url) {
    return new Promise((resolve,reject)=>{const xhr=new XMLHttpRequest();xhr.open('GET',url);xhr.onload=()=>{try{if(xhr.status!==0&&(xhr.status<200||xhr.status>=300))throw new Error('HTTP '+xhr.status);resolve(JSON.parse(xhr.responseText));}catch(error){reject(new Error('无法读取角色动画配置: '+error.message));}};xhr.onerror=()=>reject(new Error('无法读取角色动画配置'));xhr.send();});
  }
  async function ensureLoaded(id, animationMetadata = null) {
    checkedId(id);if(cache.has(id)){const entry=cache.get(id);if(animationMetadata)entry.animation=animationMetadata;return entry;}if(pending.has(id))return pending.get(id);
    if(typeof document==='undefined')throw new Error('Node 环境请先 registerPreset 注入原始帧');
    const work=(async()=>{const results=await Promise.all([...Array.from({length:16},(_,n)=>loadImage(assetUrl(id,'frame_'+String(n+1).padStart(2,'0')+'.png'))),loadImage(assetUrl(id,'animations/walk_up.png')),animationMetadata?Promise.resolve(animationMetadata):loadJSON(assetUrl(id,'animation.json'))]);return registerPreset(id,{frames:results.slice(0,16),walkUp:results[16],animation:results[17]});})();
    pending.set(id,work);try{return await work;}finally{pending.delete(id);}
  }
  async function ensureAnimation(id,clipName) {
    checkedId(id);if(!clipNames.includes(clipName))throw new TypeError('未知角色动画: '+clipName);
    const entry=await ensureLoaded(id);if(entry.animations.has(clipName))return entry.animations.get(clipName);
    const key=id+'/'+clipName;if(clipPending.has(key))return clipPending.get(key);
    if(typeof document==='undefined')throw new Error('Node 环境请注入动画图集');
    const descriptor=entry.animation?.animations?.[clipName];
    if(!descriptor || !/^animations\/(?:daily\/)?[a-z_]+\.png$/.test(descriptor.atlas))throw new Error('缺少有效角色动画: '+clipName);
    const work=(async()=>{const frames=atlasFrames(await loadImage(assetUrl(id,descriptor.atlas)));entry.animations.set(clipName,frames);return frames;})();
    clipPending.set(key,work);try{return await work;}finally{clipPending.delete(key);}
  }
  function getAnimation(id) { return cache.get(checkedId(id))?.animation || null; }
  const luminance=(r,g,b)=>r*.299+g*.587+b*.114;
  const skinLike=(r,g,b)=>g>95&&b>65&&r-g>5&&r-g<85&&r-b>8&&r-b<120&&g-b>-4&&g-b<70;
  function analyze(image,id,direction) {
    if(analysisCache.has(image))return analysisCache.get(image);
    const d=image.data,candidates=new Uint8Array(width*height),visited=new Uint8Array(width*height);let best=[];
    // A source-colored skin component locates the face independently of sitting/jumping poses.
    for(let y=22;y<132;y++)for(let x=55;x<201;x++){const p=y*width+x,i=p*4;if(d[i+3]>80&&skinLike(d[i],d[i+1],d[i+2]))candidates[p]=1;}
    for(let p=0;p<candidates.length;p++)if(candidates[p]&&!visited[p]){const component=[p];visited[p]=1;for(let k=0;k<component.length;k++){const v=component[k],x=v%width;for(const n of [v-width,v+width,x?v-1:-1,x<width-1?v+1:-1])if(n>=0&&n<candidates.length&&candidates[n]&&!visited[n]){visited[n]=1;component.push(n);}}if(component.length>best.length)best=component;}
    let minX=95,maxX=163,minY=48,maxY=108;
    if(best.length>100){minX=Math.min(...best.map(p=>p%width));maxX=Math.max(...best.map(p=>p%width));minY=Math.min(...best.map(p=>Math.floor(p/width)));maxY=Math.max(...best.map(p=>Math.floor(p/width)));}
    const face={x:minX,y:minY,width:maxX-minX+1,height:maxY-minY+1,cx:(minX+maxX)/2,cy:(minY+maxY)/2,bottom:maxY};
    const faceSkin=new Set(best);
    const result={face,labels:new Uint8Array(width*height),bases:[0,0,0,0,0]},samples=[[],[],[],[],[]];
    for(let y=0;y<height;y++)for(let x=0;x<width;x++) {
      const p=y*width+x,i=p*4;if(!d[i+3])continue;const r=d[i],g=d[i+1],b=d[i+2],l=luminance(r,g,b),warm=skinLike(r,g,b),spread=Math.max(r,g,b)-Math.min(r,g,b);
      const eyeY=minY+face.height*.48,eyeLeft=face.cx-face.width*.24,eyeRight=face.cx+face.width*.24;
      const eyeSpot=Math.abs(y-eyeY)<face.height*.13&&(Math.abs(x-eyeLeft)<face.width*.13||Math.abs(x-eyeRight)<face.width*.13);
      let label=0;
      if(eyeSpot&&l>30&&l<153&&spread>15&&!warm)label=4;
      const above=y<minY+face.height*.23,outer=Math.abs(x-face.cx)>face.width*.39&&y<maxY+8;
      const braid=id==='12_florist_female'&&x>face.cx+18&&x<face.cx+48&&y>maxY&&y<maxY+80;
      const hairColor=(r>=g*.92&&g>=b*.84&&l<185)||(spread<25&&l<130);
      if(!label&&hairColor&&((above&&l<170)||(outer&&(!warm||l<175))||(braid&&(!warm||l<175))||(direction==='back'&&y<maxY-8&&!warm))&&!(id==='18_artist_female'&&y<minY-5))label=1;
      const legStart=({'02_hero_female':218,'12_florist_female':215,'16_librarian_female':225,'20_student_female':205})[id]||235;
      const exposedNeck=y>=maxY-3&&y<maxY+12&&Math.abs(x-face.cx)<11;
      const profile=direction==='left'||direction==='right',armCenter=profile?128:face.cx;
      const armEnd=({'01_hero_male':195,'02_hero_female':185,'03_barista_male':197,'10_musician_male':212,'12_florist_female':184,'16_librarian_female':172,'18_artist_female':201,'20_student_female':189})[id];
      const exposedArms=y>maxY+11&&y<armEnd&&Math.abs(x-armCenter)>(profile||direction==='back'?10:25);
      const raisedHands=y<maxY&&Math.abs(x-face.cx)>face.width*.55;
      const exposedLegs=y>=legStart&&Math.abs(x-face.cx)<25;
      if(!label&&warm&&(faceSkin.has(p)||exposedNeck||exposedArms||exposedLegs||raisedHands))label=3;
      const prop=(id==='10_musician_male'&&x>166&&y<185)||(id==='12_florist_female'&&x<126&&y>103&&y<167)||(id==='16_librarian_female'&&x>110&&x<147&&y>124&&y<164)||(id==='18_artist_female'&&spread>85);
      if(!label&&y>maxY-2&&y<223&&x>65&&x<191&&!prop)label=2;
      // Original deepest ink pixels remain unchanged to preserve the source outlines.
      if(l<24)label=0;
      result.labels[p]=label;if(label&&d[i+3]>180)samples[label].push(l);
    }
    for(let n=1;n<=4;n++){samples[n].sort((a,b)=>a-b);result.bases[n]=samples[n][Math.floor(samples[n].length*.62)]||[0,65,180,210,80][n];}
    analysisCache.set(image,result);return result;
  }
  function shade(rgb,amount) { return rgb.map(c=>Math.round(amount<=1?c*amount:c+(255-c)*Math.min(.62,amount-1))); }
  function analyzeSide(image,id,pose){
    const f=pose.face,labels=new Uint8Array(width*height),samples=[[],[],[],[],[]],bases=[0,0,0,0,0];
    for(let y=0;y<height;y++)for(let x=0;x<width;x++){
      const p=y*width+x,i=p*4,d=image.data;if(!d[i+3])continue;
      const r=d[i],g=d[i+1],b=d[i+2],l=luminance(r,g,b),warm=r>140&&r-g>28&&r-g<90&&g-b>8&&g-b<80&&(r-g)/(g-b)>.8;
      const pillow=x<48&&y>202,head=x<106&&y>=pose.headBounds[1]&&y<205,braid=id==='12_florist_female'&&x<148&&y>160&&y<210&&l<140;
      const beret=id==='18_artist_female'&&Math.max(r,g,b)-Math.min(r,g,b)<18&&l<90;
      const arms=x>=42&&x<150&&y>=188&&y<224,legs=['02_hero_female','12_florist_female','20_student_female'].includes(id)&&x>=184&&x<232&&y>=186;
      let label=0;
      if(!pillow&&(warm&&(head||arms)||legs&&skinLike(r,g,b)))label=3;
      else if((head&&!beret||braid)&&l<165&&r>=g*.9&&g>=b*.82)label=1;
      else if(x>=106&&x<218&&y>=154&&y<224)label=2;
      if(l<24)label=0;labels[p]=label;if(label)samples[label].push(l);
    }
    for(let n=1;n<=4;n++){samples[n].sort((a,b)=>a-b);bases[n]=samples[n][Math.floor(samples[n].length*.62)]||[0,65,180,210,80][n];}
    return{face:f,labels,bases};
  }
  function composite(source,a,direction,pose=null) {
    const result=copyImage(source),d=result.data;
    if(colorKeys.every(k=>a[k]==='original')&&a.presetAccessory==='none'&&a.expression==='neutral')return result;
    const analysis=pose?analyzeSide(source,a.avatarPreset,pose):analyze(source,a.avatarPreset,direction),f=analysis.face,targets=[null,...colorKeys.map(k=>a[k]==='original'?null:rgb(a[k]))];
    for(let p=0;p<analysis.labels.length;p++){const n=analysis.labels[p],target=targets[n];if(!target)continue;const i=p*4,l=luminance(source.data[i],source.data[i+1],source.data[i+2]);const ratio=l/analysis.bases[n],amount=n===3?Math.max(.48,Math.min(1.28,.48+.52*ratio)):Math.max(.30,Math.min(1.55,.15+.85*ratio));const c=shade(target,amount);d[i]=c[0];d[i+1]=c[1];d[i+2]=c[2];}
    const accessory=rgb(a.accessoryColor),dark=shade(accessory,.47),light=shade(accessory,1.34),skin=a.presetSkinColor==='original'?[250,214,180]:rgb(a.presetSkinColor);
    const angle=pose?pose.headAngle*Math.PI/180:0,cs=Math.cos(angle),sn=Math.sin(angle);
    function dot(x,y,c,alpha=255){if(pose){const dx=x-f.cx,dy=y-f.cy;x=f.cx+cs*dx-sn*dy;y=f.cy+sn*dx+cs*dy;}x=Math.round(x);y=Math.round(y);if(x<0||x>=width||y<0||y>=height)return;const i=(y*width+x)*4;d[i]=c[0];d[i+1]=c[1];d[i+2]=c[2];d[i+3]=alpha;}
    function line(x0,y0,x1,y1,c,weight=1){const distance=Math.max(Math.abs(x1-x0),Math.abs(y1-y0),1);for(let n=0;n<=distance;n++){const x=x0+(x1-x0)*n/distance,y=y0+(y1-y0)*n/distance;for(let j=0;j<weight;j++)for(let k=0;k<weight;k++)dot(x+j,y+k,c);}}
    function ellipse(cx,cy,rx,ry,c,fill=false){for(let y=Math.floor(cy-ry);y<=cy+ry;y++)for(let x=Math.floor(cx-rx);x<=cx+rx;x++){const v=((x-cx)/rx)**2+((y-cy)/ry)**2;if(fill?v<=1:v<=1.14&&v>=.72)dot(x,y,c);}}
    function polygon(points,c){for(let y=Math.floor(Math.min(...points.map(p=>p[1])));y<=Math.max(...points.map(p=>p[1]));y++)for(let x=Math.floor(Math.min(...points.map(p=>p[0])));x<=Math.max(...points.map(p=>p[0]));x++){let inside=false;for(let i=0,j=points.length-1;i<points.length;j=i++){const p=points[i],q=points[j];if((p[1]>y)!==(q[1]>y)&&x<(q[0]-p[0])*(y-p[1])/(q[1]-p[1])+p[0])inside=!inside;}if(inside)dot(x,y,c);}}
    const isBack=direction==='back',profile=direction==='left'||direction==='right';
    const ey=f.y+f.height*.48,eyeXs=profile?[f.cx+(direction==='left'?-1:1)*f.width*.20]:[f.cx-f.width*.24,f.cx+f.width*.24];
    if(!isBack&&(a.presetAccessory==='glasses'||a.presetAccessory==='roundGlasses')) {
      const rx=Math.max(8,Math.min(12,f.width*.16)),ry=8;
      for(const x of eyeXs){if(a.presetAccessory==='roundGlasses')ellipse(x,ey,rx,ry,dark);else{line(x-rx,ey-ry,x+rx,ey-ry,dark);line(x-rx,ey-ry,x-rx,ey+ry-2,dark);line(x+rx,ey-ry,x+rx,ey+ry-2,dark);line(x-rx,ey+ry-2,x+rx,ey+ry-2,dark);}line(x-rx+2,ey-ry+1,x-2,ey-ry+1,accessory);dot(x-rx+3,ey-ry+2,light);}
      if(!profile)line(eyeXs[0]+rx,ey-2,eyeXs[1]-rx,ey-2,dark);line(f.x+2,ey-3,eyeXs[0]-rx,ey-3,dark);
    }
    if(a.presetAccessory==='ribbon') {
      const x=f.cx+(profile?(direction==='left'?1:-1):1)*f.width*.48,y=f.y+f.height*.09;
      polygon([[x,y],[x-10,y-6],[x-12,y+4],[x-7,y+7],[x,y+3],[x+9,y+8],[x+13,y+2],[x+10,y-5]],dark);
      polygon([[x,y+1],[x-9,y-4],[x-10,y+3],[x-7,y+5],[x,y+2],[x+9,y+6],[x+11,y+2],[x+9,y-3]],accessory);line(x-7,y-2,x-3,y+1,light);line(x+3,y+1,x+8,y-2,light);ellipse(x,y+2,2.5,3,dark,true);polygon([[x,y+4],[x-4,y+13],[x,y+11],[x+3,y+14],[x+4,y+4]],accessory);
    }
    if(a.presetAccessory==='scarf') {
      const neck=pose?.neck||[109,190],cy=pose?f.cy-sn*(neck[0]-f.cx)+cs*(neck[1]-f.cy):f.bottom+5,cx=pose?f.cx+cs*(neck[0]-f.cx)+sn*(neck[1]-f.cy):f.cx,rx=Math.max(12,Math.min(20,f.width*.24));
      ellipse(cx,cy,rx,5,dark,true);ellipse(cx,cy-1,rx-1,3,accessory,true);line(cx-rx+4,cy-2,cx+rx-5,cy-2,light);
      polygon([[cx+3,cy+2],[cx+12,cy+2],[cx+10,cy+27],[cx+3,cy+24]],dark);polygon([[cx+4,cy+3],[cx+10,cy+3],[cx+9,cy+24],[cx+4,cy+22]],accessory);line(cx+5,cy+6,cx+5,cy+20,light);line(cx+4,cy+22,cx+9,cy+24,light);
    }
    if(!pose&&!isBack&&a.expression!=='neutral') {
      const mx=f.cx+(profile?(direction==='left'?-1:1)*f.width*.13:0),my=f.bottom-f.height*.17;
      if(a.expression==='shy'||a.expression==='happy'){for(const x of eyeXs)ellipse(x,ey+13,4,1.7,shade(skin,.92).map((v,i)=>i===0?Math.min(255,v+12):i===2?Math.max(70,v-9):v),true);}
      if(a.expression==='shy')for(const x of eyeXs){line(x-2,ey+12,x-1,ey+14,[194,127,124]);line(x+1,ey+12,x+2,ey+14,[194,127,124]);}
      if(['serious','sad','surprised'].includes(a.expression)){
        // Patch only the mouth, sampling the original cheek color; face and eyes stay original.
        let sample=[...skin];const sy=Math.round(my),sx=Math.round(mx+13),si=(sy*width+sx)*4;if(d[si+3]&&skinLike(d[si],d[si+1],d[si+2]))sample=[d[si],d[si+1],d[si+2]];
        ellipse(mx,my,Math.max(6,f.width*.105),Math.max(4,f.height*.095),sample,true);
        const mouth=[137,67,63];if(a.expression==='surprised')ellipse(mx,my,3,4,mouth,true);else if(a.expression==='serious')line(mx-4,my,mx+4,my,mouth);else{line(mx-4,my+1,mx,my-1,mouth);line(mx,my-1,mx+4,my+1,mouth);}
      }
    }
    return result;
  }
  function frameDirection(frame,entry){return frame>=4&&frame<=6?'left':frame>=7&&frame<=9?'right':frame===10||frame>=17||entry.animation?.backWalkCompletion&&(frame===11||frame===12)?'back':'front';}
  function renderPixels(input,frame=1) {
    if(!Number.isInteger(frame)||frame<1||frame>18)throw new RangeError('预设动作帧必须是1到18');
    const a=options(input),entry=cache.get(a.avatarPreset);if(!entry)throw new Error('预设尚未加载，请先 await PresetAvatar.ensureLoaded(id)');
    const bounds=frame>=17?entry.animation?.animations?.walk_up?.visibleBounds?.[frame===17?4:12]:entry.animation?.frameBounds?.[String(frame)];
    const offset=frame>=17?entry.animation?.animations?.walk_up?.offsetX:entry.animation?.frameOffsets?.[String(frame)];
    const source=Regions?Regions.pixels(entry.frames[frame-1],bounds,offset||0):entry.frames[frame-1];
    return composite(source,a,frameDirection(frame,entry));
  }
  function renderAnimationPixels(input,clipName,index=0) {
    if(!clipNames.includes(clipName)||!Number.isInteger(index)||index<0)throw new TypeError('无效连续动画帧');
    const a=options(input),entry=cache.get(a.avatarPreset),frames=entry?.animations.get(clipName);if(!frames)throw new Error('动画尚未加载，请先 await ensureAnimation(id, clipName)');
    const direction=clipName==='walk_up'?'back':clipName==='walk_left'?'left':clipName==='walk_right'?'right':'front';
    const n=index%frames.length,clip=entry.animation?.animations?.[clipName];
    const source=Regions?Regions.pixels(frames[n],clip?.visibleBounds?.[n],clip?.offsetX||0):frames[n];
    return composite(source,a,direction,clip?.sideLying||null);
  }
  return {width,height,faceRegion,presetIds,registerPreset,isLoaded,ensureLoaded,ensureAnimation,getAnimation,renderPixels,renderAnimationPixels};
});
