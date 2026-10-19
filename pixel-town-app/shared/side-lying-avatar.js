(function(root,factory){
  if(typeof module==='object'&&module.exports)module.exports=factory(require('./appearance'),require('./parametric-avatar'));
  else root.SideLyingAvatar=factory(root.Appearance,root.ParametricAvatar);
})(typeof globalThis==='object'?globalThis:this,function(A,Avatar){
  'use strict';
  // Free avatars have editable, native pixel layers. Their body is drawn with
  // a new articulated side pose; only the existing face/hair layers are reused.
  function renderPixels(input,phase=0){
    const a=A.normalize(input),w=128,h=128,d=new Uint8ClampedArray(w*h*4);
    const rgb=c=>[1,3,5].map(n=>parseInt(c.slice(n,n+2),16));
    const shade=(c,t)=>'#'+rgb(c).map(n=>Math.round(t<0?n*(1+t):n+(255-n)*t).toString(16).padStart(2,'0')).join('');
    const skin=a.skin,skinLine=shade(skin,-.46),skinShade=shade(skin,-.18),cloth=a.clothesColor,ink=shade(cloth,-.55),clothShade=shade(cloth,-.23),clothLight=shade(cloth,.22),accent=a.accentColor,bottom=a.bottomColor;
    const colors=new Map();
    function dot(x,y,c){x=Math.round(x);y=Math.round(y);if(x<0||x>=w||y<0||y>=h)return;if(!colors.has(c))colors.set(c,[...rgb(c),255]);d.set(colors.get(c),(y*w+x)*4);}
    function line(x0,y0,x1,y1,c,size=1){const len=Math.max(Math.abs(x1-x0),Math.abs(y1-y0),1);for(let n=0;n<=len;n++)for(let yy=0;yy<size;yy++)for(let xx=0;xx<size;xx++)dot(x0+(x1-x0)*n/len+xx,y0+(y1-y0)*n/len+yy,c);}
    function polygon(p,fill,outline){for(let y=Math.floor(Math.min(...p.map(v=>v[1])));y<=Math.max(...p.map(v=>v[1]));y++)for(let x=Math.floor(Math.min(...p.map(v=>v[0])));x<=Math.max(...p.map(v=>v[0]));x++){let inside=false;for(let i=0,j=p.length-1;i<p.length;j=i++){const v=p[i],q=p[j];if((v[1]>y)!==(q[1]>y)&&x<(q[0]-v[0])*(y-v[1])/(q[1]-v[1])+v[0])inside=!inside;}if(inside)dot(x,y,fill);}if(outline)for(let n=0;n<p.length;n++)line(...p[n],...p[(n+1)%p.length],outline);}
    function curve(commands,fill,outline){let points=[],x=0,y=0;for(const c of commands){if(c.length===2){[x,y]=c;points.push(c);}else{const [cx,cy,ex,ey]=c,ox=x,oy=y;for(let n=1;n<=12;n++){const t=n/12;points.push([(1-t)**2*ox+2*t*(1-t)*cx+t*t*ex,(1-t)**2*oy+2*t*(1-t)*cy+t*t*ey]);}[x,y]=[ex,ey];}}polygon(points,fill,outline);}
    function oval(cx,cy,rx,ry,fill,outline){const p=Array.from({length:32},(_,n)=>[cx+Math.cos(n*Math.PI/16)*rx,cy+Math.sin(n*Math.PI/16)*ry]);polygon(p,fill,outline);}
    const build=a.build,shoulder=a.shoulders;
    // Pillow, trailing long hair, far forearm and far bent leg sit behind body.
    curve([[8,104],[12,99,24,100],[36,99,45,106],[45,112,34,114],[14,115,7,110]],'#F0E5CF','#B6A994');line(11,110,33,112,'#D7C7AF');
    if(['long','ponytail','twintails','curly'].includes(a.hairStyle)){
      const hair=a.hairColor,hi=shade(hair,.22),dark=shade(hair,-.40);
      curve([[13,87],[14,107,28,111],[47,116,73,109],[83,108,85,102],[70,106,51,101],[35,93,13,87]],hair,dark);
      line(27,108,64,109,hi);line(35,104,71,106,shade(hair,-.17));
      if(a.hairStyle==='curly')for(let n=0;n<7;n++)oval(25+n*7,109-n%2,5,4,hair,dark);
      if(a.hairStyle==='ponytail'||a.hairStyle==='twintails'){line(49,106,52,111,accent,2);if(a.hairStyle==='twintails')line(23,107,23,112,accent,2);}
    }
    curve([[49,91],[43,98,32,101],[28,107,31,111],[40,113,53,108],[62,105,62,99]],skinShade,skinLine);
    const pants=a.bottom==='pants',leg=pants?bottom:skin,legLine=shade(leg,-.45),legShade=shade(leg,-.22);
    curve([[84,96],[92,87,106,90],[116,91,113,99],[109,104,99,106],[96,109,112,109],[116,113,104,114],[90,114,85,106]],legShade,legLine);
    function shoe(x,y){const color=a.shoeColor,dark=shade(color,-.48);curve([[x,y-4],[x+8,y-6,x+11,y-2],[x+15,y+2,x+11,y+4],[x+2,y+5,x,y]],color,dark);line(x+3,y+3,x+11,y+2,shade(color,.35));if(a.shoes==='sneakers')line(x+5,y-2,x+9,y-1,accent);if(a.shoes==='boots')polygon([[x-3,y-5],[x+3,y-5],[x+4,y+3],[x-2,y+3]],color,dark);if(a.shoes==='sandals')line(x+2,y-3,x+6,y+1,skin,2);}
    shoe(110,96);
    // Horizontal ribcage, short neck, dropped shoulder and curved waist.
    curve([[50,96],[51,88,61+shoulder,86],[73,86,79,91],[86+build,90,92+build,96],[94+build,104,87,108],[70,114,56,108],[50,104,50,96]],cloth,ink);
    curve([[70,105],[84,104,92,99],[94,104,87,108],[72,112,65,110]],clothShade);
    line(70,89,79,94,clothLight);line(76,106,87,104,clothLight);
    polygon([[48,94],[55,92],[58,98],[51,103],[46,101]],skin,skinLine);
    polygon([[48,101],[54,99],[59,94],[61,96],[56,104],[50,105]],accent,ink);
    if(['shirt','suit','jacket'].includes(a.outfit)){line(60,98,81,106,accent);for(const x of [66,72,78])dot(x,100+(x-66)/2,shade(accent,-.36));}
    if(a.outfit==='hoodie'){curve([[49,95],[47,91,54,88],[63,83,70,88],[64,95,58,98]],clothShade,ink);line(59,97,64,103,accent);line(65,94,69,100,accent);polygon([[71,98],[83,100],[80,106],[69,105]],clothShade,ink);}
    if(a.outfit==='overalls'){polygon([[56,96],[58,95],[65,103],[86,99],[91,106],[67,110]],bottom,shade(bottom,-.48));line(58,96,66,106,accent,2);polygon([[72,103],[81,102],[82,106],[73,107]],shade(bottom,.2),shade(bottom,-.3));}
    // Near thigh turns forward; knee folds down; calf returns toward the hip.
    curve([[87,102],[102,97,109,99],[117,101,115,107],[111,111,101,110],[103,114,110,110],[116,111,112,115],[98,117,87,111],[82,108,87,102]],leg,legLine);
    line(96,105,110,104,pants?shade(bottom,.23):shade(skin,.2));line(102,111,109,112,legShade);
    if(a.bottom==='shorts')curve([[87,103],[102,98,107,100],[104,104,100,108],[91,110,87,107]],bottom,shade(bottom,-.48));
    if(a.bottom==='skirt'||a.outfit==='dress'){const color=a.outfit==='dress'?cloth:bottom;curve([[78,95],[94,89,107,97],[104,105,112,110],[102,115,89,112],[79,108,78,95]],color,shade(color,-.5));line(90,96,91,107,shade(color,.25));line(97,98,101,109,shade(color,-.2));line(91,111,108,109,accent);}
    shoe(111,109);
    // Upper arm bends at the elbow, forearm points back toward the pillow.
    curve([[61,89],[70+shoulder,89,72,98],[70,104,63,103],[58,101,61,89]],cloth,ink);line(62,100,70,101,accent,2);
    curve([[63,102],[68,102,69,106],[68,111,61,112],[52,113,43,110],[42,106,48,105],[56,108,63,107]],skin,skinLine);line(50,109,62,110,shade(skin,.15));line(44,107,47,109,skinShade);line(46,106,49,108,skinShade);
    // Existing editable head layers retain facial geometry and accessories.
    const head=Avatar.renderPixels(a,1,{sleeping:true,headOnly:true}),hy=18-(a.height-2),scale=.96,angle=-26*Math.PI/180,cs=Math.cos(angle),sn=Math.sin(angle),cx=38,cy=81;
    for(let y=32;y<115;y++)for(let x=2;x<81;x++){
      const dx=x-cx,dy=y-cy,sx=Math.floor((cs*dx+sn*dy)/scale+64),sy=Math.floor((-sn*dx+cs*dy)/scale+hy+25);
      if(sx<0||sx>=head.width||sy<0||sy>=hy+51)continue;const i=(sy*head.width+sx)*4;if(head.data[i+3])d.set(head.data.subarray(i,i+4),(y*w+x)*4);
    }
    if(phase){const glyph=['11111','00010','00100','01000','11111'];for(let y=0;y<5;y++)for(let x=0;x<5;x++)if(glyph[y][x]==='1')dot(58+phase*4+x,44-phase*4+y,'#5F7770');}
    const out={width:256,height:256,data:new Uint8ClampedArray(256*256*4)};for(let y=0;y<256;y++)for(let x=0;x<256;x++){const i=(Math.floor(y/2)*w+Math.floor(x/2))*4;out.data.set(d.subarray(i,i+4),(y*256+x)*4);}return out;
  }
  return{renderPixels};
});
