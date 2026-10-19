'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {catalog}=require('../main/catalog'),A=require('../shared/appearance'),S=require('../shared/side-lying-avatar'),P=require('../shared/preset-avatar'),Actions=require('../shared/actions');
const {readPNG}=require('./side-lying-assets');
function hardPixels(image){
  assert.equal(image.height,256);assert.equal(image.width%256,0);
  let visible=0;
  for(let y=0;y<image.height;y+=2)for(let x=0;x<image.width;x+=2){const i=(y*image.width+x)*4,v=image.data.subarray(i,i+4);assert.ok(v[3]===0||v[3]===255);if(v[3])visible++;for(const [dx,dy] of [[1,0],[0,1],[1,1]])assert.deepEqual(image.data.subarray(((y+dy)*image.width+x+dx)*4,((y+dy)*image.width+x+dx)*4+4),v);}
  assert.ok(visible>1000);assert.equal(image.data[3],0);
}
test('45 identities provide designed side-lying atlases with opaque pixel clusters and preserved source exports',()=>{
  assert.equal(catalog.length,45);
  for(const r of catalog){const clip=r.animation.animations.lie_down;assert.equal(clip.frames,4);assert.equal(clip.sideLying.nativeGrid,2);assert.equal(clip.revision,'20261004-side-lying-v1');assert.deepEqual(clip.durations,[1200,800,800,1000]);assert.ok(Actions.available(r.animation).includes('lie_down'));
    const file=path.join(__dirname,'../assets',r.assetFolder,clip.atlas),raw=fs.readFileSync(file);assert.deepEqual(raw,fs.readFileSync(path.join(__dirname,'../../pixel_town_assets',r.assetFolder,clip.atlas)));const image=readPNG(file);assert.equal(image.width,1024);hardPixels(image);
  }
});
test('editable custom avatars retain accessories and independent palette in a new articulated pose',()=>{
  for(const p of A.presets)for(let n=0;n<4;n++)hardPixels(S.renderPixels({...p.appearance,styleMode:'custom'},n));
  const base=A.normalize({styleMode:'custom'}),before=JSON.stringify(base),plain=S.renderPixels(base),hat=S.renderPixels({...base,hat:'straw',hatColor:'#CC7F2A'}),glasses=S.renderPixels({...base,accessory:'roundGlasses',accessoryColor:'#6B348A'}),dyed=S.renderPixels({...base,clothesColor:'#256CAB',hairColor:'#AC3154'});
  assert.equal(JSON.stringify(base),before);for(const image of [hat,glasses,dyed])assert.notDeepEqual(image.data,plain.data);
});
test('eight preset players reuse exact new artwork and customize it without mutating source pixels',()=>{
  for(const id of P.presetIds){const folder=path.join(__dirname,'../assets/characters',id),metadata=JSON.parse(fs.readFileSync(path.join(folder,'animation.json'))),frames=Array.from({length:16},(_,n)=>readPNG(path.join(folder,'frame_'+String(n+1).padStart(2,'0')+'.png'))),atlas=readPNG(path.join(folder,metadata.animations.lie_down.atlas));P.registerPreset(id,{frames,animation:metadata,animations:{lie_down:atlas}});const a=A.normalize({styleMode:'preset',avatarPreset:id}),im=P.renderAnimationPixels(a,'lie_down',0),raw=readPNG(path.join(__dirname,'../../pixel_town_assets/characters',id,'animations/daily/lie_down/frame_01.png'));assert.deepEqual(im.data,raw.data);const saved=new Uint8ClampedArray(im.data);assert.notDeepEqual(P.renderAnimationPixels({...a,presetHairColor:'#AC3154',presetAccessory:'glasses'},'lie_down',0).data,saved);assert.deepEqual(P.renderAnimationPixels(a,'lie_down',0).data,saved);}
});
