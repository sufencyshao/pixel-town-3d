(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(require('./appearance.js'));
  else root.ParametricAvatar = factory(root.Appearance);
})(typeof globalThis !== 'undefined' ? globalThis : this, function (Appearance) {
  'use strict';
  const width = 128, height = 160;
  const faceRegion = Object.freeze({ x: 34, y: 8, width: 60, height: 62 });
  const tint = (hex, amount, target) => {
    const rgb = [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16));
    const to = target || (amount >= 0 ? [255, 246, 228] : [67, 51, 70]);
    return '#' + rgb.map((v, i) => Math.round(v + (to[i] - v) * Math.abs(amount)).toString(16).padStart(2, '0')).join('');
  };
  function renderPixels(input, frame = 1, pose = {}) {
    const a = Appearance.normalize(input);
    if (!Number.isInteger(frame) || frame < 1 || frame > 18) throw new RangeError('动作帧必须是 1 到 18 的整数');
    const data = new Uint8ClampedArray(width * height * 4);
    const side = frame >= 4 && frame <= 9, back = frame === 10 || frame >= 17;
    const mirror = frame >= 4 && frame <= 6;
    const walking = [2, 3, 5, 6, 8, 9, 17, 18].includes(frame);
    const phase = [2, 5, 8, 17].includes(frame) ? -1 : 1;
    const cheer = frame === 11 || frame === 12, wave = frame === 14, sitting = frame === 16;
    const dy = frame === 13 ? -4 : sitting ? 12 : walking ? -1 : frame === 12 ? -2 : 0;
    const hy = 18 - (a.height - 2) + dy;
    const bt = hy + 48, bb = sitting ? 115 : 104 + dy, fy = sitting ? 148 : 147 + dy;
    const waist = 10 + a.build, sh = 13 + a.shoulders, chest = 10 + a.build + a.chest;
    const skin = a.skin, skinLine = tint(skin, -.44, [148, 94, 93]), skinShadow = tint(skin, -.21, [180, 116, 106]), skinSoft = tint(skin, .17), skinLight = tint(skin, .30);
    const hair = a.hairColor, hairLine = tint(hair, -.53), hairShade = tint(hair, -.22), hairDeep = tint(hair, -.40), hairLight = tint(hair, .24), hairShine = tint(hair, .38);
    const cloth = a.clothesColor, clothLine = tint(cloth, -.48), clothShade = tint(cloth, -.20), clothDark = tint(cloth, -.34), clothLight = tint(cloth, .21), clothSoft = tint(cloth, .10);
    const accent = a.accentColor, accentShade = tint(accent, -.23), bottom = a.bottomColor, bottomLine = tint(bottom, -.50), bottomShade = tint(bottom, -.22), bottomLight = tint(bottom, .17);
    const eyesInk = '#594550', lip = tint(skin, -.34, [153, 70, 88]);
    const colors = new Map();
    function color(c) { if (!colors.has(c)) colors.set(c, [parseInt(c.slice(1, 3), 16), parseInt(c.slice(3, 5), 16), parseInt(c.slice(5, 7), 16), 255]); return colors.get(c); }
    function px(x, y, c) { x = Math.round(x); y = Math.round(y); if (mirror) x = width - 1 - x; if (x >= 0 && x < width && y >= 0 && y < height) data.set(color(c), (y * width + x) * 4); }
    function rect(x, y, w, h, c) { for (let yy = Math.round(y); yy < Math.round(y + h); yy++) for (let xx = Math.round(x); xx < Math.round(x + w); xx++) px(xx, yy, c); }
    function line(x1, y1, x2, y2, c, weight = 1) {
      x1 = Math.round(x1); y1 = Math.round(y1); x2 = Math.round(x2); y2 = Math.round(y2);
      const dx = Math.abs(x2 - x1), sx = x1 < x2 ? 1 : -1, dy = -Math.abs(y2 - y1), sy = y1 < y2 ? 1 : -1; let e = dx + dy;
      for (;;) { rect(x1 - Math.floor(weight / 2), y1 - Math.floor(weight / 2), weight, weight, c); if (x1 === x2 && y1 === y2) break; const n = 2 * e; if (n >= dy) { e += dy; x1 += sx; } if (n <= dx) { e += dx; y1 += sy; } }
    }
    function polygon(points, fill, outline) {
      if (fill) {
        const first = Math.floor(Math.min(...points.map(p => p[1]))), last = Math.ceil(Math.max(...points.map(p => p[1])));
        for (let y = first; y < last; y++) {
          const intersections = [];
          for (let i = 0, j = points.length - 1; i < points.length; j = i++) { const p = points[i], q = points[j]; if ((p[1] > y + .5) !== (q[1] > y + .5)) intersections.push(p[0] + (y + .5 - p[1]) * (q[0] - p[0]) / (q[1] - p[1])); }
          intersections.sort((x, y) => x - y);
          for (let n = 0; n < intersections.length; n += 2) for (let x = Math.ceil(intersections[n] - .5); x < intersections[n + 1] - .5; x++) px(x, y, fill);
        }
      }
      if (outline) for (let i = 0; i < points.length; i++) line(...points[i], ...points[(i + 1) % points.length], outline);
    }
    // Cubic and quadratic curves are sampled, then rasterized into solid native pixels.
    // They never use canvas antialiasing or a scaled copy of a smaller sprite.
    function path(commands, fill, outline, close = true) {
      const p = []; let x = 0, y = 0;
      for (const c of commands) {
        if (c[0] === 'M' || c[0] === 'L') { x = c[1]; y = c[2]; p.push([x, y]); }
        else if (c[0] === 'Q') { const ox = x, oy = y; for (let i = 1; i <= 12; i++) { const t = i / 12, u = 1 - t; p.push([u * u * ox + 2 * u * t * c[1] + t * t * c[3], u * u * oy + 2 * u * t * c[2] + t * t * c[4]]); } x = c[3]; y = c[4]; }
        else if (c[0] === 'C') { const ox = x, oy = y; for (let i = 1; i <= 18; i++) { const t = i / 18, u = 1 - t; p.push([u * u * u * ox + 3 * u * u * t * c[1] + 3 * u * t * t * c[3] + t * t * t * c[5], u * u * u * oy + 3 * u * u * t * c[2] + 3 * u * t * t * c[4] + t * t * t * c[6]]); } x = c[5]; y = c[6]; }
      }
      if (close) polygon(p, fill, outline);
      else if (outline) for (let i = 1; i < p.length; i++) line(...p[i - 1], ...p[i], outline);
      return p;
    }
    function stroke(commands, c) { path(commands, null, c, false); }
    function ellipse(cx, cy, rx, ry, fill, outline) { const p = []; for (let i = 0; i < 48; i++) { const n = i * Math.PI / 24; p.push([cx + Math.cos(n) * rx, cy + Math.sin(n) * ry]); } polygon(p, fill, outline); }
    function hairLock(commands, lightCommands) { path(commands, hair, hairLine); if (lightCommands) path(lightCommands, hairLight); }
    function rearHair() {
      if (a.hairStyle === 'bald') return;
      const long = ['long', 'ponytail', 'twintails', 'curly'].includes(a.hairStyle), end = hy + (long ? 78 : a.hairStyle === 'bob' ? 49 : 39);
      path([['M',43,hy+23],['C',39,hy+5,48,hy-4,63,hy-4],['C',80,hy-5,91,hy+9,88,hy+27],['L',88,end-10],['Q',90,end,80,end],['Q',73,end-3,65,end],['Q',54,end+2,43,end-4],['Q',39,end-8,41,hy+37]],hairShade,hairLine);
      if (long) {
        path([['M',43,hy+28],['Q',47,hy+23,51,hy+34],['C',49,hy+55,52,end-8,48,end],['Q',40,end+1,40,end-7],['Q',43,hy+54,43,hy+28]],hair,hairLine);
        path([['M',78,hy+26],['Q',88,hy+22,88,hy+37],['C',85,hy+55,90,end-6,85,end+1],['Q',79,end+5,76,end-1],['Q',81,hy+61,78,hy+26]],hair,hairLine);
        stroke([['M',46,hy+37],['C',44,hy+52,49,end-15,46,end-5]],hairLight);
        stroke([['M',84,hy+37],['C',82,hy+55,86,end-14,83,end-4]],hairLight);
        stroke([['M',49,hy+42],['Q',47,end-13,50,end-4]],hairDeep);
      }
      if (a.hairStyle === 'ponytail') {
        hairLock([['M',84,hy+18],['C',100,hy+14,108,hy+34,101,hy+50],['C',95,hy+63,98,hy+79,89,hy+78],['Q',83,hy+74,89,hy+63],['C',97,hy+44,86,hy+39,84,hy+18]], [['M',91,hy+25],['C',102,hy+35,96,hy+48,93,hy+59],['Q',94,hy+43,90,hy+35]]);
        stroke([['M',96,hy+31],['Q',100,hy+42,94,hy+52]],hairShine);
        ellipse(87,hy+26,4,3,accent,hairLine);
      }
      if (a.hairStyle === 'twintails') for (const sign of [-1, 1]) {
        const x = sign < 0 ? 29 : 85;
        hairLock([['M',x+5,hy+25],['C',x-4,hy+28,x-5,hy+50,x+1,hy+60],['C',x+7,hy+69,x+1,hy+80,x+8,hy+80],['Q',x+17,hy+76,x+13,hy+64],['C',x+10,hy+55,x+19,hy+37,x+11,hy+27],['Q',x+8,hy+24,x+5,hy+25]], [['M',x+5,hy+31],['C',x,hy+39,x+2,hy+51,x+6,hy+58],['Q',x+3,hy+43,x+9,hy+33]]);
        stroke([['M',x+8,hy+43],['C',x+5,hy+54,x+13,hy+65,x+9,hy+75]],hairLight);
        ellipse(x+9,hy+29,5,2,accent,hairLine);px(x+7,hy+28,tint(accent,.3));
      }
      if (a.hairStyle === 'bun') {
        hairLock([['M',56,hy-1],['C',49,hy-5,55,hy-10,63,hy-10],['C',75,hy-10,79,hy-3,72,hy+3],['Q',62,hy+7,56,hy-1]], [['M',57,hy-5],['Q',65,hy-9,71,hy-4],['Q',65,hy-6,57,hy-3]]);
        stroke([['M',69,hy-7],['Q',76,hy-3,69,hy+1]],hairShade);
        stroke([['M',55,hy+1],['Q',64,hy+5,73,hy+1]],accent);
      }
    }
    function shoe(x, y, far) {
      const c = a.shoeColor, o = tint(c, -.49), s = tint(c, -.23), h = tint(c, .22), w = side ? 15 : 12;
      if (a.shoes === 'boots') {
        path([['M',x+3,y-10],['L',x+10,y-10],['Q',x+11,y-4,x+10,y],['Q',x+15,y+1,x+14,y+5],['L',x+1,y+5],['Q',x,y+1,x+3,y-1]],c,o);
        line(x+4,y-8,x+9,y-8,s);line(x+3,y+3,x+13,y+3,s);rect(x+9,y-5,2,2,accent);line(x+4,y-6,x+4,y-1,h);
      } else if (a.shoes === 'flats') {
        path([['M',x+3,y-1],['Q',x+8,y-2,x+11,y],['Q',x+15,y+1,x+13,y+5],['L',x+1,y+5],['Q',x,y+1,x+3,y-1]],c,o);
        ellipse(x+7,y,3,2,skin);line(x+2,y+4,x+12,y+4,s);px(x+10,y+1,h);rect(x+5,y+2,3,1,accent);
      } else if (a.shoes === 'sandals') {
        path([['M',x+3,y-2],['L',x+10,y-2],['Q',x+10,y+1,x+13,y+2],['L',x+13,y+5],['L',x+1,y+5],['Q',x,y+1,x+3,y-2]],skin,skinLine);
        line(x+2,y+3,x+12,y+3,c,2);line(x+4,y-1,x+5,y+3,c);line(x+9,y,x+8,y+3,c);line(x+1,y+5,x+13,y+5,o);
      } else {
        path([['M',x+3,y-3],['Q',x+7,y-4,x+10,y-2],['L',x+11,y],['Q',x+w,y+1,x+w-1,y+4],['Q',x+8,y+6,x+1,y+4],['Q',x-1,y+1,x+3,y-3]],c,o);
        stroke([['M',x+1,y+3],['Q',x+7,y+5,x+w-1,y+3]],s);rect(x+4,y-1,5,1,h);rect(x+5,y+1,4,1,accent);px(x+10,y+2,h);
      }
      if (far) px(x+2,y+2,s);
    }
    function leg(sign, far) {
      const lx = sign < 0 ? 54 - Math.floor(a.build / 2) : 68, shift = walking ? sign * phase * 4 : 0;
      const endX = lx + shift, foot = fy - (walking && sign === phase ? 3 : 0), lw = 6 + Math.floor(a.build / 2);
      const c = a.bottom === 'pants' ? bottom : skin, o = a.bottom === 'pants' ? bottomLine : skinLine;
      if (sitting) {
        path([['M',lx,bb-5],['Q',lx+lw+1,bb-6,lx+lw+4,bb+1],['L',lx+lw+7,bb+13],['Q',lx+lw+5,bb+20,lx+2,bb+17],['L',lx-2,bb+2]],c,o);
        if(a.bottom==='pants')stroke([['M',lx+3,bb],['Q',lx+9,bb+7,lx+7,bb+13]],bottomLight);
        shoe(lx+3,bb+18,far);return;
      }
      path([['M',lx-1,bb-1],['L',lx+lw+1,bb-1],['Q',lx+lw+2,bb+12,endX+lw,foot-8],['Q',endX+4,foot-5,endX,foot-8],['Q',lx,bb+16,lx-1,bb-1]],c,o);
      if (a.bottom === 'pants') {
        path([['M',lx+lw-2,bb+3],['Q',lx+lw+1,bb+13,endX+lw,foot-8],['L',endX+lw-2,foot-8],['Q',lx+lw-2,bb+14,lx+lw-2,bb+3]],bottomShade);
        stroke([['M',lx+1,bb+6],['Q',lx+1,bb+16,endX+1,foot-11]],bottomLight);
        line(endX,foot-9,endX+lw,foot-9,bottomShade);px(endX+1,foot-11,bottomLight);
      } else {
        stroke([['M',lx+lw,bb+9],['Q',lx+lw,bb+16,endX+lw-1,foot-8]],skinShadow);
        rect(endX,foot-10,lw,3,a.shoes==='sandals'?skin:tint(a.shoeColor,.14));
      }
      shoe(endX-2,foot-5,far);
    }
    function arm(sign, far, foreground) {
      const sx = 64 + sign * (sh - 2), sy = bt + 4;
      let ex = 64 + sign * (sh + 3), ey = bb + 1, mx = ex + sign * 1, my = bt + 23;
      if (cheer || wave && sign === 1) { ex = 64 + sign * (sh + (wave ? 11 : 12)); ey = hy + (wave ? 19 : 8); mx = ex + sign * 2; my = bt - 10; }
      if (walking) { ex += sign * phase * 3; ey -= sign === phase ? 5 : 0; mx += sign * phase; }
      if (sitting) { ex = 64 + sign * (waist + 3); ey = bb - 1; my = bt + 21; }
      const c = far ? clothShade : cloth, o = clothLine, long = ['hoodie','sweater','jacket','suit'].includes(a.outfit);
      const ux = sx + sign * 3, ox = sign * 3;
      path([['M',sx-ox,sy-2],['Q',ux+ox,sy-1,mx+ox,my],['Q',ex+ox,ey-3,ex+ox-1,ey+1],['Q',ex,ey+5,ex-ox,ey+1],['Q',mx-ox,my+2,sx-ox,sy-2]],skin,skinLine);
      const endX = long ? ex : sx + (mx - sx) * .55, endY = long ? ey-4 : sy + (my - sy) * .53;
      path([['M',sx-ox,sy-4],['Q',sx+ox+sign*2,sy-5,mx+ox,my-3],['L',endX+ox,endY],['Q',endX,endY+3,endX-ox,endY+1],['L',sx-ox,sy-4]],c,o);
      stroke([['M',sx-ox+sign,sy],['Q',mx-ox+sign,my-5,endX-ox+sign,endY-2]],far?clothDark:clothLight);
      line(endX-ox,endY,endX+ox,endY,accentShade);
      if (long)line(endX-ox,endY-2,endX+ox,endY-2,accent);
      ellipse(ex,ey+1,3,4,skin,skinLine);px(ex+sign*2,ey,skinShadow);px(ex-sign,ey+1,skinLight);
      if(cheer||wave&&sign===1){line(ex-2,ey-1,ex-2,ey-5,skinLine);line(ex,ey-1,ex,ey-6,skinLine);line(ex+2,ey-1,ex+2,ey-4,skinLine);line(ex-sign*3,ey,ex-sign*4,ey-2,skinLine);rect(ex-1,ey-3,3,5,skin);px(ex,ey-4,skinLight);}
    }
    function torso() {
      const hem = a.outfit === 'dress' ? waist + 5 : waist;
      path([['M',57,bt-2],['Q',64,bt+1,71,bt-2],['Q',64+sh,bt,64+sh,bt+7],['Q',64+chest,bt+15,64+waist,bb-9],['L',64+hem,bb],['Q',64,bb+2,64-hem,bb],['L',64-waist,bb-9],['Q',64-chest,bt+15,64-sh,bt+7],['Q',64-sh,bt,57,bt-2]],cloth,clothLine);
      path([['M',64+sh-3,bt+4],['Q',64+chest,bt+18,64+waist-1,bb-9],['L',64+hem-1,bb-1],['L',64+hem-4,bb-1],['Q',64+waist-5,bt+21,64+sh-3,bt+4]],clothShade);
      stroke([['M',64-sh+2,bt+7],['Q',64-chest+2,bt+19,64-waist+2,bb-6]],clothLight);
      stroke([['M',64-sh+5,bt+5],['Q',58,bt+7,59,bt+14]],clothSoft);
      // The neck is narrow, with a soft cast shadow and a curved collar.
      path([['M',59,hy+42],['L',69,hy+42],['L',70,bt+1],['Q',64,bt+5,58,bt+1]],skin,skinLine);
      path([['M',59,hy+42],['L',69,hy+42],['L',69,hy+46],['Q',63,hy+49,59,hy+45]],skinShadow);
      if(a.gender==='male')line(60,hy+47,67,hy+47,tint(skin,-.12));
      const front = !back;
      if(a.outfit==='shirt') {
        path([['M',57,bt-1],['L',64,bt+5],['L',60,bt+10],['L',54,bt+3]],accent,accentShade);
        path([['M',71,bt-1],['L',64,bt+5],['L',68,bt+10],['L',74,bt+3]],accent,accentShade);
        if(front){line(64,bt+7,64,bb-2,clothShade);line(66,bt+10,66,bb-3,clothLight);for(let y=bt+12;y<bb-2;y+=7){ellipse(65,y,1,1,accentShade);px(65,y-1,accent);}path([['M',70,bt+13],['L',77,bt+13],['L',77,bt+19],['Q',73,bt+22,70,bt+19]],clothSoft,clothShade);line(71,bt+14,76,bt+14,accent);}
        stroke([['M',56,bb-6],['Q',59,bb-7,61,bb-5]],clothShade);
      } else if(a.outfit==='hoodie') {
        path([['M',55,bt-1],['Q',54,bt+9,59,bt+12],['Q',64,bt+15,70,bt+11],['Q',75,bt+7,73,bt-1],['L',69,bt+2],['Q',64,bt+9,59,bt+2]],clothShade,clothLine);
        stroke([['M',56,bt+3],['Q',56,bt+10,61,bt+11]],clothLight);
        if(front){line(60,bt+9,59,bt+19,accent);line(69,bt+9,70,bt+19,accent);rect(58,bt+18,2,3,accentShade);rect(69,bt+18,2,3,accentShade);path([['M',57,bb-13],['L',71,bb-13],['Q',76,bb-8,75,bb-4],['Q',64,bb-2,53,bb-4],['Q',53,bb-8,57,bb-13]],clothShade,clothShade);stroke([['M',58,bb-12],['Q',63,bb-10,70,bb-12]],clothLight);line(54,bb-8,57,bb-11,clothLine);line(71,bb-11,74,bb-8,clothLine);}
        stroke([['M',64-waist+1,bb-2],['Q',64,bb+1,64+waist-1,bb-2]],accentShade);
      } else if(a.outfit==='dress') {
        stroke([['M',57,bt+1],['Q',64,bt+8,71,bt+1]],accent,1);
        path([['M',64-waist+1,bt+22],['Q',64,bt+24,64+waist-1,bt+22],['L',64+waist,bt+25],['Q',64,bt+28,64-waist,bt+25]],accent,accentShade);
        for(let n=-2;n<=2;n++)stroke([['M',64+n*4,bt+28],['Q',64+n*5,bb-7,64+n*6,bb-2]],n>0?clothShade:clothLight);
        if(front){path([['M',63,bt+24],['L',58,bt+21],['Q',56,bt+23,58,bt+26],['L',63,bt+24],['L',68,bt+21],['Q',70,bt+24,68,bt+26]],accent,accentShade);rect(63,bt+23,2,3,accentShade);}
        stroke([['M',64-hem+2,bb-2],['Q',64,bb+1,64+hem-2,bb-2]],accentShade);
      } else if(a.outfit==='overalls') {
        path([['M',54,bt+1],['L',58,bt+2],['L',59,bb-2],['L',55,bb-2]],accent,accentShade);path([['M',70,bt+2],['L',74,bt+1],['L',73,bb-2],['L',69,bb-2]],accent,accentShade);
        path([['M',55,bt+17],['L',73,bt+17],['Q',76,bt+23,75,bb],['L',53,bb],['Q',52,bt+23,55,bt+17]],bottom,bottomLine);
        path([['M',58,bt+21],['L',70,bt+21],['L',70,bt+29],['Q',64,bt+32,58,bt+29]],bottomLight,bottomShade);line(59,bt+22,69,bt+22,accent);ellipse(56,bt+16,1.5,1.5,accent,accentShade);ellipse(72,bt+16,1.5,1.5,accent,accentShade);px(59,bt+28,accentShade);px(69,bt+28,accentShade);
      } else if(a.outfit==='suit'||a.outfit==='jacket') {
        if(front){path([['M',58,bt],['Q',64,bt+5,70,bt],['L',69,bb-2],['L',59,bb-2]],accent,accentShade);
          path([['M',54,bt+1],['L',58,bt+1],['L',64,bt+20],['L',56,bt+13],['L',59,bt+9],['L',55,bt+7]],clothLight,clothShade);
          path([['M',74,bt+1],['L',70,bt+1],['L',64,bt+20],['L',72,bt+13],['L',69,bt+9],['L',73,bt+7]],clothSoft,clothShade);
          line(64,bt+20,64,bb-2,clothShade);ellipse(66,bt+24,1,1,accentShade);ellipse(66,bt+31,1,1,accentShade);line(54,bb-8,60,bb-7,accent);line(69,bb-7,75,bb-8,accent);
          if(a.outfit==='suit')path([['M',63,bt+5],['L',65,bt+5],['L',67,bt+13],['L',64,bt+17],['L',61,bt+13]],clothDark,clothLine);
          else {line(64,bt+9,64,bb-4,accentShade);rect(72,bt+18,6,5,clothShade);line(72,bt+19,77,bt+19,accent);px(66,bb-4,accent);}}
        else {stroke([['M',54,bt+12],['Q',64,bt+15,74,bt+12]],clothShade);line(64,bt+13,64,bb-4,clothShade);}
      } else {
        path([['M',56,bt+1],['Q',64,bt+9,72,bt+1],['L',71,bt+4],['Q',64,bt+11,57,bt+4]],accent,accentShade);
        stroke([['M',64-waist+1,bb-4],['Q',64,bb-1,64+waist-1,bb-4]],accentShade);
        stroke([['M',64-waist+1,bb-2],['Q',64,bb+1,64+waist-1,bb-2]],accent);
        for(let x=64-waist+3;x<64+waist-1;x+=3)line(x,bb-3,x,bb-1,clothShade);
        if(front){path([['M',64,bt+16],['C',60,bt+10,56,bt+17,60,bt+21],['L',64,bt+25],['L',68,bt+21],['C',73,bt+16,67,bt+11,64,bt+16]],accent);px(60,bt+16,tint(accent,.28));}
        else stroke([['M',58,bt+7],['Q',64,bt+9,70,bt+7]],clothLight);
        for(const sign of [-1,1])stroke([['M',64+sign*8,bb-10],['Q',64+sign*7,bb-8,64+sign*9,bb-7]],clothShade);
      }
      // Visible under the upper hem, each lower-garment option retains its own silhouette.
      if(a.bottom==='skirt') {
        const y = bb-2, ext = a.outfit==='dress'?waist+5:waist+2;
        path([['M',64-waist,y],['Q',64,y+1,64+waist,y],['L',64+ext,y+13],['Q',64,y+17,64-ext,y+13]],bottom,bottomLine);
        for(let n=-2;n<=2;n++)stroke([['M',64+n*4,y+2],['Q',64+n*5,y+8,64+n*6,y+12]],n>0?bottomShade:bottomLight);
        stroke([['M',64-ext+2,y+12],['Q',64,y+15,64+ext-2,y+12]],bottomLight);
      } else {
        path([['M',64-waist+1,bb-1],['Q',64,bb+1,64+waist-1,bb-1],['L',64+waist-1,bb+(a.bottom==='shorts'?12:4)],['L',65,bb+(a.bottom==='shorts'?12:4)],['L',64,bb+5],['L',63,bb+(a.bottom==='shorts'?12:4)],['L',64-waist+1,bb+(a.bottom==='shorts'?12:4)]],bottom,bottomLine);
        stroke([['M',64-waist+2,bb+1],['Q',64,bb+3,64+waist-2,bb+1]],bottomShade);
        if(front){rect(62,bb,4,2,accentShade);line(64,bb+3,64,bb+7,bottomShade);stroke([['M',64-waist+2,bb+3],['Q',64-waist+6,bb+6,64-waist+3,bb+9]],bottomLight);}
        if(a.bottom==='shorts'){line(64-waist+2,bb+11,62,bb+11,bottomLight);line(66,bb+11,64+waist-2,bb+11,bottomLight);}
      }
    }
    function face() {
      const rounded = a.faceShape==='round', oval=a.faceShape==='oval', square=a.faceShape==='square';
      const cheek = rounded?23:oval?20:22, jaw = square?14:rounded?11:oval?7:9;
      if(side)path([['M',55,hy+5],['C',72,hy-1,84,hy+9,84,hy+24],['Q',84,hy+29,88,hy+31],['Q',89,hy+33,84,hy+34],['L',83,hy+39],['Q',79,hy+45,72,hy+45],['Q',60,hy+43,53,hy+35],['Q',47,hy+22,55,hy+5]],skin,skinLine);
      else path([['M',45,hy+15],['C',46,hy+1,58,hy,65,hy+1],['C',79,hy,86,hy+10,86,hy+22],['Q',64+cheek,hy+31,64+jaw,hy+40],['Q',69,hy+45,64,hy+45],['Q',59,hy+45,64-jaw,hy+40],['Q',64-cheek,hy+31,43,hy+23],['Q',42,hy+19,45,hy+15]],skin,skinLine);
      if(side){path([['M',81,hy+21],['Q',86,hy+31,82,hy+39],['Q',77,hy+44,71,hy+44],['L',69,hy+42],['Q',79,hy+39,81,hy+21]],skinShadow);ellipse(52,hy+29,3.5,5,skin,skinLine);stroke([['M',53,hy+27],['Q',50,hy+26,52,hy+31]],skinShadow);}
      else {
        path([['M',44,hy+22],['Q',46,hy+34,64-jaw+1,hy+40],['Q',59,hy+44,65,hy+44],['Q',54,hy+46,48,hy+37],['Q',41,hy+29,44,hy+22]],skinShadow);
        path([['M',84,hy+24],['Q',84,hy+34,74,hy+40],['Q',71,hy+42,69,hy+42],['Q',79,hy+34,82,hy+25]],tint(skin,-.10,[180,116,106]));
        for(const x of [42,86]){ellipse(x,hy+29,3,5,skin,skinLine);stroke([['M',x,hy+27],['Q',x+(x<64?1:-1)*2,hy+27,x,hy+32]],skinShadow);px(x,hy+28,skinSoft);}
      }
      ellipse(side?71:59,hy+13,8,3,skinSoft);px(side?76:56,hy+12,skinLight);
      if(back)return;
      const expression = pose.sleeping?'neutral':frame===15?'surprised':a.expression;
      const ey = hy+24, locations=side?[72]:[51,72];
      for(const x of locations) {
        const type=a.eyes, h=type==='sleepy'?5:type==='sharp'?7:type==='almond'?8:9;
        if(pose.sleeping){stroke([['M',x,ey+5],['Q',x+4,ey+8,x+8,ey+5]],eyesInk);if(a.gender==='female'){px(x-1,ey+4,eyesInk);px(x+9,ey+4,eyesInk);}}
        else if(type==='smile') {stroke([['M',x,ey+6],['Q',x+4,ey+1,x+8,ey+6]],eyesInk);px(x,ey+5,eyesInk);px(x+8,ey+5,eyesInk);}
        else {
          const top=expression==='serious'?ey+2:ey;
          path([['M',x,top+3],['Q',x+3,top-1,x+6,top+1],['Q',x+10,top+3,x+8,ey+h],['Q',x+4,ey+h+2,x+1,ey+h],['Q',x-1,ey+6,x,top+3]],'#FFF4E6');
          const irisX=x+(side?4:3);
          ellipse(irisX+2,ey+5,3,h/2+.5,a.eyeColor);
          path([['M',irisX,ey+2],['L',irisX+4,ey+2],['L',irisX+4,ey+6],['Q',irisX+2,ey+8,irisX,ey+6]],tint(a.eyeColor,-.38));
          ellipse(irisX+2,ey+5,1.5,2.5,tint(a.eyeColor,-.58));
          rect(irisX,ey+2,2,2,'#FFF9ED');px(irisX+3,ey+7,tint(a.eyeColor,.49));px(irisX+4,ey+8,'#FFF7E8');
          stroke([['M',x-1,top+3],['Q',x+3,top-1,x+7,top+1],['L',x+9,top+3]],eyesInk);
          stroke([['M',x+1,ey+h],['Q',x+4,ey+h+2,x+7,ey+h]],tint(skin,-.27,[143,88,99]));
          if(type==='sleepy')stroke([['M',x,ey+3],['Q',x+4,ey+4,x+8,ey+3]],eyesInk);
          if(type==='sharp')line(x,ey+2,x+8,ey+4,eyesInk);
          if(a.gender==='female'){line(x-2,top+1,x,top+3,eyesInk);line(x+8,top+1,x+9,top+3,eyesInk);px(x+8,top,eyesInk);}
          if(expression==='sad'){px(x+8,ey+h+2,'#B4D9D9');px(x+8,ey+h+3,'#D8E9DD');}
        }
        const by=ey-5-(expression==='surprised'?2:0), bc=a.browColor;
        if(a.brows==='soft')stroke([['M',x,by+2],['Q',x+4,by,x+7,by+1]],tint(bc,.12));
        if(a.brows==='straight')line(x,by+1,x+7,by+1,bc);
        if(a.brows==='arched')stroke([['M',x,by+2],['Q',x+3,by-2,x+7,by+1]],bc);
        if(a.brows==='thick'){stroke([['M',x,by+2],['Q',x+3,by,x+7,by+1]],bc);stroke([['M',x+1,by+3],['Q',x+4,by+1,x+7,by+2]],bc);}
        if(a.brows!=='none'&&expression==='sad')px(x+3,by-1,bc);
        if(a.brows!=='none'&&expression==='serious')line(x,by,x+7,by+2,bc);
      }
      const nx=side?83:64,ny=hy+35;
      if(a.nose==='button'){ellipse(nx,ny,1.5,1.2,skinShadow);px(nx-1,ny-1,skinLight);}
      if(a.nose==='small'){px(nx,ny,skinShadow);px(nx+1,ny,skinSoft);}
      if(a.nose==='pointed'){line(nx,ny-2,nx+1,ny,skinShadow);px(nx+2,ny,skinLine);px(nx+1,ny-1,skinSoft);}
      if(a.nose==='flat'){line(nx-1,ny,nx+2,ny,skinShadow);px(nx,ny-1,skinSoft);}
      const mx=side?76:64,my=hy+40;
      if(expression==='surprised'){ellipse(mx,my,2,2.5,lip);px(mx,my-1,tint(lip,-.13));}
      else {
        if(a.mouth==='small')line(mx-1,my,mx+1,my,lip);
        if(a.mouth==='wide')stroke([['M',mx-3,my-1],['Q',mx,my+1,mx+3,my-1]],lip);
        if(a.mouth==='smile')stroke([['M',mx-3,my-1],['Q',mx,my+2,mx+3,my-1]],lip);
        if(a.mouth==='pout'){line(mx-1,my-1,mx+1,my-1,lip);line(mx-2,my,mx+2,my,lip);px(mx,my+1,skinShadow);}
        if(expression==='happy'){path([['M',mx-3,my-1],['Q',mx,my+4,mx+3,my-1]],lip);line(mx-1,my,mx+1,my,'#FFF4E6');}
        if(expression==='sad')stroke([['M',mx-3,my+1],['Q',mx,my-2,mx+3,my+1]],lip);
        if(expression==='shy')px(mx+2,my,skinShadow);
        if(expression==='serious')line(mx-2,my,mx+2,my,lip);
      }
      const blush=a.blush+(expression==='shy'?1:0), blushColor=tint(skin,.38,[233,145,151]);
      for(const x of side?[76]:[50,77]) {
        if(blush){ellipse(x,hy+35,2+blush*.65,blush>2?1.5:1,blushColor);if(blush>1){px(x-1,hy+34,tint(skin,.22,[236,139,151]));px(x+1,hy+35,tint(skin,.22,[236,139,151]));}}
        for(let n=0;n<a.freckles;n++){px(x-3+n*3,hy+33+(n%2),tint(skin,-.30,[157,91,74]));px(x-2+n*3,hy+35+(n%2),tint(skin,-.20,[157,91,74]));}
      }
    }
    function frontHair() {
      if(a.hairStyle==='bald'){stroke([['M',51,hy+6],['Q',63,hy,77,hy+7]],skinSoft);return;}
      const short=a.hairStyle==='short'||a.hairStyle==='pixie';
      if(back) {
        path([['M',42,hy+19],['C',40,hy+5,48,hy-4,64,hy-4],['C',81,hy-4,91,hy+7,88,hy+25],['Q',87,hy+39,78,hy+44],['Q',66,hy+50,51,hy+44],['Q',41,hy+37,42,hy+19]],hair,hairLine);
        path([['M',48,hy+8],['C',52,hy,62,hy-1,67,hy+1],['C',53,hy+6,48,hy+21,50,hy+37],['Q',44,hy+28,48,hy+8]],hairLight);
        path([['M',79,hy+9],['Q',86,hy+16,83,hy+31],['Q',80,hy+41,74,hy+44],['Q',79,hy+31,79,hy+9]],hairShade);
        for(const [x,n] of [[52,-2],[59,-1],[65,0],[72,1],[79,2]])stroke([['M',x,hy+12],['C',x+n,hy+22,x+n*2,hy+35,x+n,hy+42]],n<0?hairLight:hairShade);
        stroke([['M',50,hy+8],['Q',57,hy+1,65,hy+1]],hairShine);
        if(short)path([['M',48,hy+36],['Q',53,hy+43,57,hy+42],['L',60,hy+45],['L',63,hy+41],['L',68,hy+45],['L',71,hy+41],['L',77,hy+43],['Q',82,hy+37,82,hy+33],['Q',84,hy+45,73,hy+47],['L',54,hy+47]],hairDeep);
        if(a.hairStyle==='curly')curls();
        return;
      }
      const pixie=a.hairStyle==='pixie';
      hairLock([['M',42,hy+23],['C',39,hy+9,46,hy-3,61,hy-4],['C',74,hy-7,86,hy+1,88,hy+15],['Q',89,hy+25,83,hy+31],['L',80,hy+17],['Q',74,hy+10,65,hy+11],['Q',53,hy+10,47,hy+22]], [['M',47,hy+9],['C',52,hy+1,65,hy-2,74,hy+3],['Q',59,hy+1,49,hy+14]]);
      stroke([['M',50,hy+7],['Q',58,hy+1,67,hy+2]],hairShine);
      stroke([['M',73,hy+5],['Q',83,hy+12,82,hy+22]],hairShade);
      stroke([['M',56,hy+4],['Q',49,hy+12,47,hy+22]],hairLight);
      if(!short){
        hairLock([['M',43,hy+14],['Q',51,hy+12,49,hy+28],['Q',48,hy+40,53,hy+48],['Q',47,hy+51,43,hy+43],['Q',38,hy+33,43,hy+14]], [['M',44,hy+21],['Q',46,hy+18,46,hy+28],['Q',44,hy+37,48,hy+43],['Q',42,hy+35,44,hy+21]]);
        hairLock([['M',81,hy+15],['Q',89,hy+21,86,hy+36],['Q',84,hy+44,78,hy+48],['Q',77,hy+47,80,hy+41],['Q',82,hy+28,81,hy+15]], [['M',84,hy+22],['Q',87,hy+32,81,hy+43],['Q',85,hy+32,84,hy+22]]);
        stroke([['M',45,hy+29],['Q',43,hy+39,48,hy+46]],hairShade);
      } else {
        path([['M',42,hy+14],['Q',47,hy+13,48,hy+20],['L',46,hy+32],['L',43,hy+27],['L',41,hy+30],['Q',39,hy+24,42,hy+14]],hair,hairLine);
        path([['M',81,hy+14],['Q',90,hy+20,86,hy+30],['L',82,hy+28],['L',80,hy+22]],hairShade,hairLine);
        if(pixie){path([['M',52,hy+1],['L',56,hy-6],['Q',59,hy-3,62,hy-3],['L',65,hy-7],['Q',66,hy-3,74,hy-1],['L',69,hy+3]],hair,hairLine);stroke([['M',57,hy-2],['Q',63,hy+1,69,hy]],hairLight);}
      }
      if(a.bangs==='straight') {
        path([['M',48,hy+11],['Q',65,hy+7,81,hy+13],['L',81,hy+23],['Q',77,hy+24,74,hy+22],['L',72,hy+24],['Q',68,hy+24,65,hy+22],['L',63,hy+24],['Q',56,hy+23,50,hy+24],['Q',47,hy+20,48,hy+11]],hair,hairLine);
        path([['M',51,hy+13],['Q',64,hy+10,77,hy+14],['L',77,hy+16],['Q',64,hy+13,51,hy+16]],hairLight);
        for(const x of [54,61,69,76])stroke([['M',x,hy+16],['Q',x-1,hy+20,x,hy+23]],hairShade);
      } else if(a.bangs==='side') {
        hairLock([['M',47,hy+12],['Q',61,hy+4,78,hy+11],['Q',77,hy+17,67,hy+23],['Q',63,hy+27,59,hy+26],['Q',65,hy+20,67,hy+17],['Q',57,hy+24,50,hy+24],['Q',46,hy+21,47,hy+12]], [['M',50,hy+13],['Q',62,hy+7,73,hy+12],['Q',66,hy+13,54,hy+19],['L',50,hy+19]]);
        stroke([['M',55,hy+17],['Q',64,hy+11,73,hy+12]],hairShine);stroke([['M',58,hy+21],['Q',70,hy+18,75,hy+13]],hairShade);
      } else if(a.bangs==='curtain') {
        hairLock([['M',47,hy+14],['Q',52,hy+6,63,hy+9],['Q',60,hy+17,49,hy+26],['L',47,hy+25]], [['M',51,hy+13],['Q',55,hy+9,60,hy+11],['Q',55,hy+16,50,hy+21]]);
        hairLock([['M',65,hy+9],['Q',76,hy+6,82,hy+15],['L',82,hy+27],['Q',70,hy+22,65,hy+9]], [['M',69,hy+11],['Q',76,hy+12,79,hy+21],['Q',73,hy+17,69,hy+11]]);
        stroke([['M',59,hy+13],['Q',55,hy+20,50,hy+24]],hairShade);
      } else {
        path([['M',47,hy+14],['Q',52,hy+7,64,hy+8],['Q',63,hy+14,51,hy+17],['L',47,hy+22]],hair,hairLine);
        path([['M',65,hy+8],['Q',78,hy+8,83,hy+18],['L',82,hy+24],['Q',76,hy+14,65,hy+8]],hair,hairLine);
        stroke([['M',50,hy+13],['Q',57,hy+9,61,hy+10]],hairLight);
      }
      if(a.hairStyle==='curly')curls();
    }
    function curls() {
      for(const [x,y,flip] of [[43,15,1],[86,15,-1],[41,29,1],[87,34,-1],[44,44,1],[83,49,-1],[42,60,1],[86,65,-1]]) {
        path([['M',x,hy+y],['C',x-8*flip,hy+y-3,x-8*flip,hy+y+10,x,hy+y+10],['C',x+7*flip,hy+y+11,x+5*flip,hy+y+2,x,hy+y+3],['Q',x-3*flip,hy+y+6,x,hy+y+8]],hair,hairLine);
        stroke([['M',x-2*flip,hy+y+1],['Q',x-6*flip,hy+y+5,x-2*flip,hy+y+8]],hairLight);
        px(x+2*flip,hy+y+6,hairShade);
      }
    }
    function accessories() {
      const c=a.accessoryColor,o=tint(c,-.39),h=tint(c,.34);
      if(a.accessory==='ribbon') {
        path([['M',80,hy+16],['Q',71,hy+8,72,hy+16],['Q',70,hy+23,79,hy+20],['Q',88,hy+27,89,hy+19],['Q',92,hy+10,82,hy+16]],c,o);
        path([['M',79,hy+19],['L',78,hy+28],['L',81,hy+26],['L',83,hy+29],['L',84,hy+20]],c,o);ellipse(81,hy+18,2,2,o);stroke([['M',74,hy+15],['Q',76,hy+16,78,hy+18]],h);line(85,hy+17,88,hy+15,h);
      }
      if(a.accessory==='earrings')for(const x of side?[52]:[42,86]) {line(x,hy+33,x,hy+36,o);ellipse(x,hy+38,2.5,3,c,o);px(x-1,hy+37,h);px(x,hy+39,tint(c,-.17));}
      if(back)return;
      if(a.accessory==='glasses'||a.accessory==='roundGlasses') {
        const xs=side?[70]:[49,70];
        for(const x of xs) {
          if(a.accessory==='roundGlasses')ellipse(x+6,hy+29,7,6,null,o);
          else path([['M',x,hy+23],['Q',x+6,hy+21,x+12,hy+23],['L',x+12,hy+32],['Q',x+6,hy+35,x,hy+32]],null,o);
          stroke([['M',x+1,hy+23],['Q',x+4,hy+22,x+7,hy+23]],c);px(x+1,hy+25,h);
        }
        stroke([['M',side?67:61,hy+27],['Q',side?69:65,hy+25,side?70:70,hy+27]],o);line(side?52:43,hy+26,side?70:49,hy+25,o);if(!side)line(82,hy+25,86,hy+26,o);
      }
    }
    function hat() {
      if(a.hat==='none')return;
      const c=a.hatColor,o=tint(c,-.46),s=tint(c,-.22),h=tint(c,.22);
      if(a.hat==='cap') {
        path([['M',43,hy+12],['C',43,hy-3,59,hy-8,73,hy-4],['Q',86,hy,86,hy+13]],c,o);
        path([['M',45,hy+11],['Q',64,hy+7,85,hy+12],['Q',97,hy+15,91,hy+19],['Q',69,hy+15,47,hy+15]],s,o);
        stroke([['M',47,hy+6],['Q',54,hy-2,65,hy-3]],h);stroke([['M',71,hy-4],['Q',81,hy+3,80,hy+11]],s);ellipse(65,hy-5,2,1,o);path([['M',61,hy+3],['L',66,hy+2],['L',69,hy+7],['L',63,hy+8]],accent,accentShade);
      } else if(a.hat==='beanie') {
        path([['M',43,hy+12],['C',43,hy-4,56,hy-8,66,hy-7],['C',80,hy-7,86,hy+2,86,hy+12]],c,o);
        path([['M',43,hy+10],['Q',64,hy+7,86,hy+10],['L',86,hy+16],['Q',64,hy+13,43,hy+16]],s,o);
        for(let x=47;x<84;x+=4)stroke([['M',x,hy+10],['Q',x-1,hy+12,x,hy+15]],h);
        stroke([['M',49,hy+5],['Q',51,hy-2,55,hy-4]],h);stroke([['M',74,hy-4],['Q',79,hy+2,80,hy+8]],s);rect(73,hy+11,6,4,accent);rect(74,hy+12,4,2,accentShade);
      } else if(a.hat==='straw') {
        path([['M',49,hy+6],['Q',49,hy-7,61,hy-8],['Q',79,hy-10,81,hy+6]],c,o);
        path([['M',39,hy+8],['Q',64,hy+1,90,hy+8],['Q',100,hy+13,92,hy+17],['Q',67,hy+20,36,hy+17],['Q',30,hy+14,39,hy+8]],c,o);
        path([['M',49,hy+2],['Q',64,hy+5,81,hy+2],['L',81,hy+7],['Q',64,hy+10,49,hy+7]],accent,accentShade);
        stroke([['M',39,hy+11],['Q',64,hy+6,90,hy+11]],h);stroke([['M',39,hy+15],['Q',65,hy+18,90,hy+15]],s);stroke([['M',53,hy-3],['Q',64,hy-7,76,hy-2]],h);
        for(let x=41;x<91;x+=5)px(x,hy+14,s);
      } else {
        path([['M',42,hy+8],['C',38,hy-1,55,hy-9,69,hy-7],['C',86,hy-8,94,hy+1,87,hy+9],['Q',73,hy+15,43,hy+11]],c,o);
        path([['M',47,hy+10],['Q',65,hy+7,82,hy+10],['L',81,hy+14],['Q',66,hy+12,48,hy+14]],s,o);
        stroke([['M',47,hy+1],['Q',57,hy-6,72,hy-4]],h);stroke([['M',79,hy-4],['Q',88,hy+2,82,hy+7]],s);line(65,hy-9,66,hy-11,o);px(64,hy-10,c);
      }
    }
    rearHair();
    if(!pose.headOnly){
      if(side)arm(-1,true,false);
      leg(-1,true);leg(1,false);
      if(!side){arm(-1,back,false);arm(1,back,false);}
      torso();
      if(side)arm(1,false,true);
    }
    face();frontHair();accessories();hat();
    return { width, height, data };
  }
  return { width, height, faceRegion, renderPixels };
});
