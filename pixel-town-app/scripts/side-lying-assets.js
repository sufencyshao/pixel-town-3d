'use strict';
// Export imagegen's redesigned poses through the existing trim / nearest-neighbor
// sprite workflow. This does not synthesize a pose from a standing frame.
const fs=require('node:fs'),path=require('node:path'),zlib=require('node:zlib'),crypto=require('node:crypto');
const app=path.resolve(__dirname,'..'),source=path.resolve(app,'../pixel_town_assets');
const production=path.join(source,'production/side-lying-20261004');
const crcTable=Uint32Array.from({length:256},(_,n)=>{let c=n;for(let k=0;k<8;k++)c=c&1?0xedb88320^(c>>>1):c>>>1;return c>>>0;});
function crc(b){let c=0xffffffff;for(const n of b)c=crcTable[(c^n)&255]^(c>>>8);return(c^0xffffffff)>>>0;}
function readPNG(file){
  const png=fs.readFileSync(file);let width,height,kind,offset=8,parts=[];
  while(offset<png.length){const n=png.readUInt32BE(offset),name=png.toString('ascii',offset+4,offset+8),b=png.subarray(offset+8,offset+8+n);if(name==='IHDR'){width=b.readUInt32BE(0);height=b.readUInt32BE(4);kind=b[9];if(b[8]!==8||![2,6].includes(kind)||b[12])throw new Error('Expected noninterlaced RGB/RGBA PNG: '+file);}if(name==='IDAT')parts.push(b);offset+=n+12;}
  const channels=kind===6?4:3,stride=width*channels,raw=zlib.inflateSync(Buffer.concat(parts)),decoded=new Uint8Array(stride*height),data=new Uint8ClampedArray(width*height*4);let p=0;
  const paeth=(a,b,c)=>{const v=a+b-c,pa=Math.abs(v-a),pb=Math.abs(v-b),pc=Math.abs(v-c);return pa<=pb&&pa<=pc?a:pb<=pc?b:c;};
  for(let y=0;y<height;y++){const f=raw[p++];for(let x=0;x<stride;x++){const l=x>=channels?decoded[y*stride+x-channels]:0,u=y?decoded[(y-1)*stride+x]:0,c=y&&x>=channels?decoded[(y-1)*stride+x-channels]:0;const prediction=f===0?0:f===1?l:f===2?u:f===3?Math.floor((l+u)/2):f===4?paeth(l,u,c):NaN;if(!Number.isFinite(prediction))throw new Error('PNG filter');decoded[y*stride+x]=(raw[p++]+prediction)&255;}}
  for(let n=0;n<width*height;n++){data.set(decoded.subarray(n*channels,n*channels+3),n*4);data[n*4+3]=channels===4?decoded[n*channels+3]:255;}return{width,height,data};
}
function pngBuffer(image){
  const chunk=(name,bytes)=>{const b=Buffer.alloc(bytes.length+12);b.writeUInt32BE(bytes.length);b.write(name,4,4,'ascii');bytes.copy(b,8);b.writeUInt32BE(crc(b.subarray(4,8+bytes.length)),8+bytes.length);return b;};
  const header=Buffer.alloc(13);header.writeUInt32BE(image.width);header.writeUInt32BE(image.height,4);header[8]=8;header[9]=6;
  const scan=Buffer.alloc((image.width*4+1)*image.height);for(let y=0;y<image.height;y++)Buffer.from(image.data.subarray(y*image.width*4,(y+1)*image.width*4)).copy(scan,y*(image.width*4+1)+1);
  return Buffer.concat([Buffer.from([137,80,78,71,13,10,26,10]),chunk('IHDR',header),chunk('IDAT',zlib.deflateSync(scan,{level:9})),chunk('IEND',Buffer.alloc(0))]);
}
function bounds(image,alpha=1){let x0=image.width,y0=image.height,x1=0,y1=0;for(let y=0;y<image.height;y++)for(let x=0;x<image.width;x++)if(image.data[(y*image.width+x)*4+3]>=alpha){x0=Math.min(x0,x);x1=Math.max(x1,x+1);y0=Math.min(y0,y);y1=Math.max(y1,y+1);}return[x0,y0,x1,y1];}
function palette(image,max=48){
  const colors=new Map();for(let i=0;i<image.data.length;i+=4)if(image.data[i+3]){const rgb=[image.data[i],image.data[i+1],image.data[i+2]],key=rgb.join(',');const entry=colors.get(key);if(entry)entry.weight++;else colors.set(key,{rgb,weight:1});}
  const stats=box=>{const range=[0,1,2].map(c=>Math.max(...box.map(v=>v.rgb[c]))-Math.min(...box.map(v=>v.rgb[c])));return {axis:range.indexOf(Math.max(...range)),score:Math.max(...range)*Math.sqrt(box.reduce((n,v)=>n+v.weight,0))};};
  const boxes=[Array.from(colors.values())];while(boxes.length<max){let chosen=-1,best=-1;for(let i=0;i<boxes.length;i++)if(boxes[i].length>1){const score=stats(boxes[i]).score;if(score>best){best=score;chosen=i;}}if(chosen<0)break;const box=boxes.splice(chosen,1)[0],axis=stats(box).axis;box.sort((a,b)=>a.rgb[axis]-b.rgb[axis]);const total=box.reduce((n,v)=>n+v.weight,0);let sum=0,mid=1;for(;mid<box.length-1;mid++){sum+=box[mid-1].weight;if(sum>=total/2)break;}boxes.push(box.slice(0,mid),box.slice(mid));}
  return boxes.map(box=>{const total=box.reduce((n,v)=>n+v.weight,0);return[0,1,2].map(c=>Math.round(box.reduce((n,v)=>n+v.rgb[c]*v.weight,0)/total));});
}
function normalize(image){
  const box=bounds(image,160),w=box[2]-box[0],h=box[3]-box[1];if(w<=0||h<=0||w/h<1.25)throw new Error('Missing horizontal side-lying art');
  // Sample a 128px native grid, then enlarge by integer 2. Alpha is thresholded,
  // never flood-filled; enclosed white hats, sleeves and the pillow stay opaque.
  const dw=116,dh=Math.round(h/w*dw),ox=(128-dw)/2,oy=112-dh;
  if(dh>88)throw new Error('Pose too tall for lying frame');
  const low={width:128,height:128,data:new Uint8ClampedArray(128*128*4)};
  for(let y=0;y<dh;y++)for(let x=0;x<dw;x++){const sx=box[0]+Math.min(w-1,Math.floor((x+.5)*w/dw)),sy=box[1]+Math.min(h-1,Math.floor((y+.5)*h/dh)),i=(sy*image.width+sx)*4;if(image.data[i+3]<160)continue;low.data.set([image.data[i],image.data[i+1],image.data[i+2],255],((oy+y)*128+ox+x)*4);}
  const colors=palette(low),memo=new Map();for(let i=0;i<low.data.length;i+=4)if(low.data[i+3]){const rgb=Array.from(low.data.subarray(i,i+3)),key=rgb.join(',');let color=memo.get(key);if(!color){color=colors.reduce((a,b)=>rgb.reduce((n,v,c)=>n+(v-b[c])**2,0)<rgb.reduce((n,v,c)=>n+(v-a[c])**2,0)?b:a);memo.set(key,color);}low.data.set(color,i);}
  const result={width:256,height:256,data:new Uint8ClampedArray(256*256*4)};for(let y=0;y<256;y++)for(let x=0;x<256;x++){const i=(Math.floor(y/2)*128+Math.floor(x/2))*4;result.data.set(low.data.subarray(i,i+4),(y*256+x)*4);}return{image:result,sourceBounds:box,palette:colors};
}
function sleepFrame(base,phase){
  const data=new Uint8ClampedArray(base.data);if(phase===0)return{...base,data};
  const glyph=['11111','00010','00100','01000','11111'],x0=112+(phase-1)*8,y0=bounds(base)[1]-22-(phase-1)*8;
  for(let y=0;y<5;y++)for(let x=0;x<5;x++)if(glyph[y][x]==='1')for(let dy=0;dy<2;dy++)for(let dx=0;dx<2;dx++)data.set([95,119,112,255],((y0+y*2+dy)*256+x0+x*2+dx)*4);return{...base,data};
}
function exportOne(person){
  const raw=path.join(production,'generated',person.id+'.png');if(!fs.existsSync(raw))return null;
  const normalized=normalize(readPNG(raw)),base=normalized.image,frames=Array.from({length:4},(_,n)=>sleepFrame(base,n));
  const folder=path.join(source,person.assetFolder),dest=path.join(app,'assets',person.assetFolder),frameDir=path.join(folder,'animations/daily/lie_down');fs.mkdirSync(frameDir,{recursive:true});fs.mkdirSync(path.join(dest,'animations/daily'),{recursive:true});
  fs.mkdirSync(path.join(folder,'source'),{recursive:true});fs.copyFileSync(raw,path.join(folder,'source','side-lying-v1.png'));
  frames.forEach((frame,i)=>fs.writeFileSync(path.join(frameDir,'frame_'+String(i+1).padStart(2,'0')+'.png'),pngBuffer(frame)));
  const atlas={width:1024,height:256,data:new Uint8ClampedArray(1024*256*4)};for(let n=0;n<4;n++)for(let y=0;y<256;y++)atlas.data.set(frames[n].data.subarray(y*256*4,(y+1)*256*4),(y*1024+n*256)*4);
  const relative='animations/daily/lie_down.png',buffer=pngBuffer(atlas);fs.writeFileSync(path.join(folder,relative),buffer);fs.writeFileSync(path.join(dest,relative),buffer);
  const descriptor={atlas:relative,frames:4,frameMs:900,loop:true,durations:[1200,800,800,1000],individualFrames:'animations/daily/lie_down',source:'source/side-lying-v1.png',revision:'20261004-side-lying-v1',technique:'imagegen redesigned side-lying pose, folded forearms and bent knees; native 2px grid, 48-color palette; stationary anatomy, animated sleep indicator',sideLying:{nativeGrid:2,groundY:224,face:{x:32,y:146,width:66,height:58,cx:65,cy:175,bottom:204},headBounds:[12,96,122,218],headAngle:-27},humanApproval:'not yet reviewed by user'};
  for(const relative of ['animation.json','animation-manifest.json','animations/daily/manifest.json']){const file=path.join(folder,relative);if(!fs.existsSync(file))continue;const meta=JSON.parse(fs.readFileSync(file));meta.animations.lie_down=descriptor;fs.writeFileSync(file,JSON.stringify(meta,null,2)+'\n');if(relative==='animation.json')fs.copyFileSync(file,path.join(dest,relative));}
  const report={id:person.id,name:person.name,kind:person.kind,raw:raw,sourceBounds:normalized.sourceBounds,bounds:bounds(base),colors:normalized.palette.length,atlasSHA256:crypto.createHash('sha256').update(buffer).digest('hex')};return report;
}
function main(){const roster=JSON.parse(fs.readFileSync(path.join(app,'assets/roster.json'))),reports=roster.characters.map(exportOne).filter(Boolean);fs.writeFileSync(path.join(production,'export.json'),JSON.stringify(reports,null,2)+'\n');console.log(JSON.stringify({exported:reports.length,total:roster.characters.length}));}
if(require.main===module)main();module.exports={readPNG,pngBuffer,bounds,normalize,sleepFrame,production};
