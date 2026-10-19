'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const vm = require('node:vm');
const Appearance = require('../shared/appearance.js');
const PixelAvatar = require('../shared/parametric-avatar.js');
const hash = image => crypto.createHash('sha256').update(image.data).digest('hex');
const originalFields=Appearance.fields.filter(f=>!['mode','preset'].includes(f.group));
const draw = (changes, frame = 1) => PixelAvatar.renderPixels({ ...Appearance.customDefaults, ...changes }, frame);
const colorCount = (image, color) => { const rgb=[1,3,5].map(i=>parseInt(color.slice(i,i+2),16));let count=0;for(let i=0;i<image.data.length;i+=4)if(image.data[i+3]&&rgb.every((v,n)=>image.data[i+n]===v))count++;return count; };

test('schema is complete, strict, normalized and usable without a DOM', () => {
  assert.equal(originalFields.length, 30);
  assert.equal(Appearance.fields.length, 37);
  assert.deepEqual(new Set(Appearance.fields.map(f=>f.key)),new Set(Object.keys(Appearance.defaults)));
  assert.deepEqual(Appearance.normalize(),Appearance.defaults);
  assert.equal(Appearance.normalize({ skin:'#abcdef' }).skin,'#ABCDEF');
  assert.equal(Appearance.normalize({ height:0 }).height,0);
  for(const input of [null,[],new Date(),{unknown:1},{skin:'red'},{skin:'#abc'},{gender:'other'},{height:2.5},{height:5},{blush:-1},{eyeColor:null},{[Symbol('extra')]:1},JSON.parse('{"__proto__":{}}')])assert.throws(()=>Appearance.normalize(input));
  for(const field of originalFields) {
    if(field.type==='select')for(const option of field.options)assert.equal(Appearance.normalize({[field.key]:option.value})[field.key],option.value);
    if(field.type==='range')for(let n=field.min;n<=field.max;n++)assert.equal(Appearance.normalize({[field.key]:n})[field.key],n);
  }
});

test('random presets are legal and do not share mutable defaults', () => {
  for(let i=0;i<100;i++){const a=Appearance.randomize();assert.deepEqual(Appearance.normalize(a),a);a.skin='#000000';assert.notEqual(Appearance.defaults.skin,a.skin);}
  for(const preset of Appearance.presets)assert.deepEqual(Appearance.normalize(preset.appearance),preset.appearance);
});

test('two styles validate independently and older face edits keep their original renderer',()=>{
  const legacy=Object.fromEntries(originalFields.map(f=>[f.key,Appearance.customDefaults[f.key]]));
  const migrated=Appearance.normalize(legacy);
  assert.equal(migrated.styleMode,'custom');
  for(const [key,value]of Object.entries(legacy))assert.equal(migrated[key],value);
  assert.equal(Appearance.defaults.styleMode,'preset');assert.equal(Appearance.gamePresets.length,8);
  assert.equal(Appearance.normalize({styleMode:'preset',presetHairColor:'original'}).presetHairColor,'original');
  assert.equal(Appearance.normalize({presetClothesColor:'#aAbBcC'}).presetClothesColor,'#AABBCC');
  for(const invalid of [{styleMode:'other'},{avatarPreset:'../../bad'},{presetSkinColor:'original.jpg'},{skin:'original'},{presetAccessory:'unknown'}])assert.throws(()=>Appearance.normalize(invalid));
});

test('all 18 actions have opaque hard pixels, a clear border and deterministic output', () => {
  const distinct=new Set();
  const configurations=[Appearance.customDefaults,...Appearance.presets.map(p=>p.appearance),{...Appearance.defaults,height:0,build:4,shoulders:4,chest:4,hat:'beret',hairStyle:'twintails'},{...Appearance.defaults,height:4,build:0,hat:'straw',hairStyle:'bun'}];
  for(const appearance of configurations)for(let frame=1;frame<=18;frame++) {
    const image=PixelAvatar.renderPixels(appearance,frame);
    assert.equal(image.width,128);assert.equal(image.height,160);assert.ok(image.data instanceof Uint8ClampedArray);assert.equal(image.data.length,128*160*4);
    assert.equal(hash(image),hash(PixelAvatar.renderPixels(appearance,frame)));
    let opaque=0;
    for(let i=0;i<image.data.length;i+=4){const alpha=image.data[i+3];assert.ok(alpha===0||alpha===255);if(!alpha)assert.deepEqual(Array.from(image.data.slice(i,i+3)),[0,0,0]);else opaque++;}
    assert.ok(opaque>2000&&opaque<11000,`frame ${frame}: plausible silhouette ${opaque}`);
    for(let x=0;x<128;x++){assert.equal(image.data[x*4+3],0);assert.equal(image.data[((159*128)+x)*4+3],0,`frame ${frame}: clipped bottom`);}
    for(let y=0;y<160;y++){assert.equal(image.data[(y*128)*4+3],0);assert.equal(image.data[(y*128+127)*4+3],0);}
    if(appearance===Appearance.customDefaults)distinct.add(hash(image));
  }
  assert.equal(distinct.size,18,'all documented actions have distinct renderings');
  for(const frame of [0,19,1.5,'1',null])assert.throws(()=>draw({},frame));
});

test('each visible customization changes the artwork and body scales vary at every step', () => {
  const base=hash(draw({}));
  for(const field of originalFields) {
    const context=field.key==='hatColor'?{hat:'cap'}:field.key==='accessoryColor'?{accessory:'ribbon'}:{};
    const reference=hash(draw(context));
    const values=field.type==='select'?field.options.map(o=>o.value):field.type==='color'?['#1248AF']:Array.from({length:field.max+1},(_,i)=>i);
    const changes=new Set(values.map(value=>hash(draw({...context,[field.key]:value}))));
    assert.ok(changes.size>1||!changes.has(reference),`${field.key} must influence visible pixels`);
    if(['height','build','shoulders','chest'].includes(field.key))assert.equal(changes.size,5,`${field.key} has five visible levels`);
  }
  for(const field of ['faceShape','hairStyle','bangs','brows','eyes','nose','mouth','outfit','bottom','shoes','hat','accessory']){
    const options=Appearance.fields.find(f=>f.key===field).options;
    const hashes=options.map(o=>hash(draw({[field]:o.value})));
    assert.equal(new Set(hashes).size,options.length,`${field} variants are visually distinct`);
  }
  assert.equal(hash(draw({})),base,'rendering does not mutate defaults');
});

test('front walking preserves face colors, opposite directions mirror, and backs hide facial details', () => {
  const a={hairStyle:'bald',eyeColor:'#00AAE1',browColor:'#D81AE1',eyes:'round',brows:'thick',hat:'none',accessory:'none',blush:0};
  for(const frame of [1,2,3,11,12,13,14,15,16])assert.ok(colorCount(draw(a,frame),a.eyeColor)>0,`front frame ${frame} keeps iris`);
  for(const frame of [10,17,18]){assert.equal(colorCount(draw(a,frame),a.eyeColor),0);assert.equal(colorCount(draw(a,frame),a.browColor),0);}
  for(const [left,right] of [[4,7],[5,8],[6,9]]){const l=draw({},left),r=draw({},right);for(let y=0;y<160;y++)for(let x=0;x<128;x++)for(let c=0;c<4;c++)assert.equal(l.data[(y*128+x)*4+c],r.data[(y*128+127-x)*4+c]);}
  for(const frame of [1,4,7,10,11,12,13,14,15,16,17,18])for(const hat of ['cap','beanie','straw','beret']){
    const image=draw({hat,hatColor:'#ED12A3'},frame);
    assert.ok(colorCount(image,'#ED12A3')>0);
    for(let y=78;y<160;y++)for(let x=0;x<128;x++){const i=(y*128+x)*4;assert.ok(!(image.data[i]===237&&image.data[i+1]===18&&image.data[i+2]===163),'hat stays on crown');}
  }
});

test('browser UMD exposes the same APIs and RGBA output', () => {
  const context=vm.createContext({});
  for(const name of ['appearance','parametric-avatar'])vm.runInContext(fs.readFileSync(require.resolve('../shared/'+name+'.js'),'utf8'),context);
  assert.equal(typeof context.Appearance.normalize,'function');assert.equal(typeof context.ParametricAvatar.renderPixels,'function');
  const image=vm.runInContext('ParametricAvatar.renderPixels(Appearance.customDefaults, 1)',context);
  assert.equal(hash(image),hash(draw({})));
});
