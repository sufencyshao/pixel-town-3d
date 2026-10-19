'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const zlib=require('node:zlib');
const crypto=require('node:crypto');
const vm=require('node:vm');
const P=require('../shared/preset-avatar.js');
const root=path.join(__dirname,'../assets/characters');
const hash=image=>crypto.createHash('sha256').update(image.data).digest('hex');
// Small, dependency-free decoder for the repository's original 8-bit RGBA PNGs.
// These are source fixtures, not newly generated art or test copies of the compositor.
function readPNG(file){
  const png=fs.readFileSync(file);assert.deepEqual(Array.from(png.subarray(0,8)),[137,80,78,71,13,10,26,10]);
  let width,height,offset=8,parts=[];
  while(offset<png.length){const n=png.readUInt32BE(offset),name=png.toString('ascii',offset+4,offset+8),bytes=png.subarray(offset+8,offset+8+n);if(name==='IHDR'){width=bytes.readUInt32BE(0);height=bytes.readUInt32BE(4);assert.equal(bytes[8],8);assert.equal(bytes[9],6);}if(name==='IDAT')parts.push(bytes);offset+=n+12;}
  const raw=zlib.inflateSync(Buffer.concat(parts)),stride=width*4,data=new Uint8ClampedArray(stride*height);let p=0;
  const paeth=(a,b,c)=>{const v=a+b-c,pa=Math.abs(v-a),pb=Math.abs(v-b),pc=Math.abs(v-c);return pa<=pb&&pa<=pc?a:pb<=pc?b:c;};
  for(let y=0;y<height;y++){const filter=raw[p++];for(let x=0;x<stride;x++){const left=x>=4?data[y*stride+x-4]:0,up=y?data[(y-1)*stride+x]:0,corner=y&&x>=4?data[(y-1)*stride+x-4]:0;const predict=filter===0?0:filter===1?left:filter===2?up:filter===3?Math.floor((left+up)/2):filter===4?paeth(left,up,corner):NaN;assert.ok(Number.isFinite(predict));data[y*stride+x]=(raw[p++]+predict)&255;}}
  return{width,height,data};
}
const originals=new Map();
for(const id of P.presetIds){const frames=Array.from({length:16},(_,n)=>readPNG(path.join(root,id,'frame_'+String(n+1).padStart(2,'0')+'.png'))),walkUp=readPNG(path.join(root,id,'animations/walk_up.png')),animation=JSON.parse(fs.readFileSync(path.join(root,id,'animation.json'),'utf8'));originals.set(id,{frames,walkUp,animation});P.registerPreset(id,{frames,walkUp,animation});}
const a={avatarPreset:'01_hero_male',expression:'neutral',presetAccessory:'none'};
function changed(image,reference){let count=0;for(let i=0;i<image.data.length;i+=4)if(image.data[i]!==reference.data[i]||image.data[i+1]!==reference.data[i+1]||image.data[i+2]!==reference.data[i+2])count++;return count;}

test('all eight original presets preserve every RGBA byte of all 16 NPC source frames',()=>{
  assert.equal(P.width,256);assert.equal(P.height,256);assert.deepEqual(P.faceRegion,{x:62,y:8,width:132,height:116});
  for(const[id,source]of originals)for(let f=1;f<=16;f++){const rendered=P.renderPixels({avatarPreset:id},f);assert.deepEqual(rendered.data,source.frames[f-1].data);rendered.data[0]=17;assert.deepEqual(P.renderPixels({avatarPreset:id},f).data,source.frames[f-1].data,'returned arrays do not mutate cached originals');}
});

test('walk-up steps 17 and 18 are distinct original atlas slices and continuous clips use zero-based indices',async()=>{
  for(const[id,source]of originals){assert.equal(P.isLoaded(id),true);await P.ensureLoaded(id);const up=await P.ensureAnimation(id,'walk_up');assert.equal(up.length,16);for(const[frame,index]of[[17,4],[18,12]])assert.deepEqual(P.renderPixels({avatarPreset:id},frame).data,up[index].data);assert.notEqual(hash(P.renderPixels({avatarPreset:id},17)),hash(P.renderPixels({avatarPreset:id},18)));assert.deepEqual(P.renderAnimationPixels({avatarPreset:id},'walk_up',20).data,up[4].data);assert.equal(P.getAnimation(id).animations.walk_up.frames,16);}
  const left=readPNG(path.join(root,a.avatarPreset,'animations/walk_left.png'));P.registerPreset(a.avatarPreset,{...originals.get(a.avatarPreset),animations:{walk_left:left}});const frames=await P.ensureAnimation(a.avatarPreset,'walk_left');assert.deepEqual(P.renderAnimationPixels(a,'walk_left',0).data,frames[0].data);assert.deepEqual(P.renderAnimationPixels(a,'walk_left',16).data,frames[0].data);
});

test('four source-specific recolors change pixels while preserving source alpha and shading',()=>{
  const source=P.renderPixels(a);
  for(const key of ['presetHairColor','presetClothesColor','presetSkinColor','presetEyeColor']){
    const image=P.renderPixels({...a,[key]:'#79918E'});assert.ok(changed(image,source)>5,key+' visibly changes its source component');const tones=new Set();for(let i=0;i<image.data.length;i+=4){assert.equal(image.data[i+3],source.data[i+3],key+' keeps alpha');if(!source.data[i+3])assert.deepEqual(image.data.subarray(i,i+4),source.data.subarray(i,i+4));if(source.data[i+3]&&image.data[i]!==source.data[i])tones.add(image.data.slice(i,i+3).join(','));}assert.ok(tones.size>4,key+' retains several light/shadow levels');
  }
  const facePixel=(78*256+127)*4,clothes=P.renderPixels({...a,presetClothesColor:'#CF7293'});assert.deepEqual(clothes.data.slice(facePixel,facePixel+4),source.data.slice(facePixel,facePixel+4),'clothes mask stays off the central face');
  assert.deepEqual(P.renderPixels(a).data,source.data,'all transformations leave original cache intact');
});

test('accessories are attached in front and both profiles; backs contain no added glasses or expression',()=>{
  for(const frame of [1,4,7,14,16])for(const presetAccessory of ['glasses','roundGlasses','ribbon','scarf']){const image=P.renderPixels({...a,presetAccessory,accessoryColor:'#9E6D8F'},frame);assert.notEqual(hash(image),hash(P.renderPixels(a,frame)),presetAccessory+' adapts to frame '+frame);for(let y=0;y<256;y++)for(const x of [0,255])assert.equal(image.data[(y*256+x)*4+3],0,'no edge clipping');}
  for(const frame of [10,11,12,17,18])for(const presetAccessory of ['glasses','roundGlasses'])for(const expression of ['happy','shy','serious','surprised','sad'])assert.deepEqual(P.renderPixels({...a,presetAccessory,expression},frame).data,P.renderPixels(a,frame).data);
  for(const frame of [10,17,18])assert.notEqual(hash(P.renderPixels({...a,presetAccessory:'scarf'},frame)),hash(P.renderPixels(a,frame)));
  for(const frame of [4,7,10,17,18]){const image=P.renderPixels({...a,presetHairColor:'#A86F82'},frame);assert.ok(changed(image,P.renderPixels(a,frame))>30,'hair color works in all four directions');}
});

test('neutral is untouched, local expressions visibly vary, and invalid requests fail explicitly',async()=>{
  const source=P.renderPixels(a);for(const expression of ['happy','shy','serious','surprised','sad'])assert.notEqual(hash(P.renderPixels({...a,expression})),hash(source),expression);
  for(const options of [{avatarPreset:'missing'},{presetHairColor:'red'},{presetSkinColor:'#abc'},{presetAccessory:'hat'},{expression:'angry'}])assert.throws(()=>P.renderPixels({...a,...options}));
  for(const frame of [0,19,-1,1.5])assert.throws(()=>P.renderPixels(a,frame));
  assert.equal(P.isLoaded('missing'),false);assert.throws(()=>P.registerPreset('missing',[]));await assert.rejects(P.ensureAnimation(a.avatarPreset,'unknown'));assert.throws(()=>P.renderAnimationPixels(a,'walk_up',-1));assert.throws(()=>P.renderAnimationPixels(a,'work',0),/尚未加载/);
});

test('browser UMD has no Appearance dependency and unloaded state is explicit',()=>{
  const context=vm.createContext({});vm.runInContext(fs.readFileSync(require.resolve('../shared/preset-avatar.js'),'utf8'),context);const api=context.PresetAvatar;assert.equal(api.width,256);assert.equal(api.getAnimation(a.avatarPreset),null);assert.equal(api.isLoaded(a.avatarPreset),false);assert.throws(()=>api.renderPixels({avatarPreset:a.avatarPreset}),/尚未加载/);api.registerPreset(a.avatarPreset,originals.get(a.avatarPreset));assert.equal(api.isLoaded(a.avatarPreset),true);assert.equal(hash(api.renderPixels(a)),hash(P.renderPixels(a)));
});

test('supplied catalog metadata loads through image-only CSP without any JSON/network request',async()=>{
  let imageRequests=0;const urls=[];
  class ImageStub{set src(value){imageRequests++;urls.push(value);this.naturalWidth=value.endsWith('/shake_head.png')?6400:/\/(walk_up|nod|chat)\.png$/.test(value)?4096:256;this.naturalHeight=256;queueMicrotask(()=>this.onload());}}
  const document={baseURI:'file:///town/renderer/index.html',createElement(){return{width:0,height:0,getContext(){return{drawImage(){},getImageData(x,y,w,h){return{data:new Uint8ClampedArray(w*h*4)};}};}};}};
  const context=vm.createContext({document,Image:ImageStub,URL,XMLHttpRequest:class{constructor(){throw new Error('CSP forbids JSON connection');}}});
  vm.runInContext(fs.readFileSync(require.resolve('../shared/preset-avatar.js'),'utf8'),context);const api=context.PresetAvatar,metadata=originals.get(a.avatarPreset).animation;
  await Promise.all([api.ensureLoaded(a.avatarPreset,metadata),api.ensureLoaded(a.avatarPreset,metadata)]);assert.equal(imageRequests,17,'concurrent loading shares the same images');assert.equal(api.getAnimation(a.avatarPreset),metadata);assert.equal(api.isLoaded(a.avatarPreset),true);await api.ensureLoaded(a.avatarPreset,metadata);assert.equal(imageRequests,17,'completed load is cached');
  for(const key of ['nod','shake_head','chat']){const clips=await Promise.all([api.ensureAnimation(a.avatarPreset,key),api.ensureAnimation(a.avatarPreset,key)]);assert.equal(clips[0].length,metadata.animations[key].frames);assert.equal(clips[0],clips[1]);assert.ok(urls.includes('file:///town/assets/characters/'+a.avatarPreset+'/animations/daily/'+key+'.png'));}
  assert.equal(imageRequests,20,'each daily atlas is loaded once without a JSON request');
});

test('preset heroes keep the exact source RGBA for every phase of nod, refusal, and conversation',async()=>{
  for(const[id,source]of originals){
    const atlases=Object.fromEntries(['nod','shake_head','chat'].map(key=>[key,readPNG(path.join(root,id,source.animation.animations[key].atlas))]));
    P.registerPreset(id,{...source,animations:atlases});
    for(const key of Object.keys(atlases)){
      const frames=await P.ensureAnimation(id,key);assert.equal(frames.length,source.animation.animations[key].frames);
      for(let n=0;n<frames.length;n++)assert.deepEqual(P.renderAnimationPixels({avatarPreset:id},key,n).data,frames[n].data,id+'/'+key+'/'+n);
    }
  }
});
