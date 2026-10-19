(function(root,factory){
  if(typeof module==='object'&&module.exports)module.exports=factory();
  else root.SpriteRegions=factory();
})(typeof globalThis==='object'?globalThis:this,function(){
  'use strict';
  function valid(bounds,width=256,height=256){
    return Array.isArray(bounds)&&bounds.length===4&&bounds.every(Number.isInteger)&&bounds[0]>=0&&bounds[1]>=0&&bounds[2]<=width&&bounds[3]<=height&&bounds[2]>bounds[0]&&bounds[3]>bounds[1];
  }
  function inset(bounds,width=256,height=256){
    return valid(bounds,width,height)?`inset(${bounds[1]/height*100}% ${(width-bounds[2])/width*100}% ${(height-bounds[3])/height*100}% ${bounds[0]/width*100}%)`:'';
  }
  function pixels(image,bounds,offset=0){
    if(!valid(bounds,image.width,image.height)&&!offset)return image;
    const out={width:image.width,height:image.height,data:new Uint8ClampedArray(image.data.length)};
    const box=valid(bounds,image.width,image.height)?bounds:[0,0,image.width,image.height];
    const dx=Math.round(offset);
    for(let y=box[1];y<box[3];y++)for(let x=box[0];x<box[2];x++){
      if(x+dx<0||x+dx>=image.width)continue;
      const a=(y*image.width+x)*4,b=(y*image.width+x+dx)*4;
      out.data.set(image.data.subarray(a,a+4),b);
    }
    return out;
  }
  function imageStyle(element,bounds,offset=0,width=256,height=256){
    const rect=element.getBoundingClientRect(),w=rect.width,h=rect.height;
    if(!w||!h)return;
    const scale=Math.min(w/width,h/height),px=(w-width*scale)/2,py=(h-height*scale)/2;
    element.style.clipPath=valid(bounds,width,height)?`inset(${(py+bounds[1]*scale)/h*100}% ${(px+(width-bounds[2])*scale)/w*100}% ${(py+(height-bounds[3])*scale)/h*100}% ${(px+bounds[0]*scale)/w*100}%)`:'';
    element.style.translate=offset?`${offset*scale}px 0px`:'';
  }
  return {valid,inset,pixels,imageStyle};
});
