'use strict';
(function(root){
  const actions=Object.freeze(['slack','doze','lie_down']);
  const is=action=>actions.includes(action);
  function bounds(image){let x0=image.width,y0=image.height,x1=0,y1=0;for(let y=0;y<image.height;y++)for(let x=0;x<image.width;x++)if(image.data[(y*image.width+x)*4+3]){x0=Math.min(x0,x);y0=Math.min(y0,y);x1=Math.max(x1,x+1);y1=Math.max(y1,y+1);}return x1>x0?[x0,y0,x1,y1]:null;}
  // Sitting/waiting can be reused. Lying requires its own designed anatomy.
  function pixels(image,action,phase=0){
    if(!is(action))return image;
    if(action==='lie_down')throw new TypeError('侧躺必须读取专门绘制的侧躺素材');
    const box=bounds(image),width=256,height=256,data=new Uint8ClampedArray(width*height*4),out={width,height,data};if(!box)return out;
    const [x0,y0,x1,y1]=box,w=x1-x0,h=y1-y0,rw=w,rh=h;
    const factor=Math.min(1,240/rw,210/rh),dw=Math.max(1,Math.floor(rw*factor)),dh=Math.max(1,Math.floor(rh*factor));
    const ox=Math.floor((width-dw)/2),oy=226-dh+(phase===2?1:0);
    function rect(x,y,w,h,c){for(let j=Math.max(0,y);j<Math.min(height,y+h);j++)for(let i=Math.max(0,x);i<Math.min(width,x+w);i++)data.set(c,(j*width+i)*4);}
    for(let y=0;y<dh;y++)for(let x=0;x<dw;x++){
      const u=Math.min(rw-1,Math.floor(x/factor)),v=Math.min(rh-1,Math.floor(y/factor));
      const sx=x0+u,sy=y0+v,index=(sy*image.width+sx)*4;if(!image.data[index+3])continue;
      data.set(image.data.subarray(index,index+4),((oy+y)*width+ox+x)*4);
    }
    if(action==='doze'){
      const glyph=['11111','00010','00100','01000','11111'],gx=Math.min(236,ox+dw-16),gy=Math.max(8,oy+12-(phase%3)*3);
      for(let row=0;row<5;row++)for(let col=0;col<5;col++)if(glyph[row][col]==='1')rect(gx+col*2,gy+row*2,2,2,[95,119,112,255]);
    }
    return out;
  }
  const api={actions,is,bounds,pixels};if(typeof module==='object'&&module.exports)module.exports=api;else root.TownRecoveryPoses=api;
})(typeof globalThis==='object'?globalThis:this);
