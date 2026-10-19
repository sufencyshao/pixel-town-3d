'use strict';
// Render a reviewable art sheet from the same code used by the game.
const {app,BrowserWindow}=require('electron');
const fs=require('node:fs');const path=require('node:path');const os=require('node:os');
const Appearance=require('../shared/appearance');const Avatar=require('../shared/parametric-avatar');
const PreviousAppearance=require('../build/avatar-v0.2/appearance');const PreviousAvatar=require('../build/avatar-v0.2/pixel-avatar');
app.setPath('userData',fs.mkdtempSync(path.join(os.tmpdir(),'town-art-preview-')));
app.whenReady().then(async()=>{
 const out=path.join(__dirname,'../build/previews');fs.mkdirSync(out,{recursive:true});
 const pack=p=>({width:p.width,height:p.height,data:Array.from(p.data)});
 const old=pack(PreviousAvatar.renderPixels(PreviousAppearance.defaults,1));
 const current=pack(Avatar.renderPixels(Appearance.defaults,1));
 const styles=Appearance.presets.map(p=>({id:p.id,label:p.label,pixels:pack(Avatar.renderPixels(p.appearance,1))}));
 const poses=[1,4,7,10,14,11,13,16].map(n=>pack(Avatar.renderPixels(Appearance.presets[1].appearance,n)));
 const html=`<!doctype html><html lang="zh-CN"><meta charset="utf-8"><style>
 *{box-sizing:border-box}body{margin:0;padding:40px;background:#F5F1E7;color:#3E4B42;font-family:'PingFang SC',sans-serif}header{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:26px}h1{font:32px 'Songti SC',serif;margin:0}header span{font-size:11px;letter-spacing:2px;color:#879381}.comparison{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:25px}.compare-card{height:260px;display:flex;align-items:center;justify-content:center;gap:28px;border:1px solid #DEDCCD;background:#FAF9F2}.compare-card canvas{width:166px;height:208px;image-rendering:pixelated;object-fit:contain}.compare-card h2{font:21px 'Songti SC',serif;margin:0 0 12px}.compare-card p{font-size:11px;color:#899385;line-height:1.9}.new{background:#EEF1E5;border-color:#CDDAC2}.lineup{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.card{height:322px;background:#FFFEF7;border:1px solid #DEDCCD;position:relative;display:flex;flex-direction:column;align-items:center;justify-content:center}.card:nth-child(3n+1){background:#EDF1E8}.card:nth-child(3n+2){background:#F8EEE1}.card:nth-child(3n){background:#F4EAE9}.card canvas{width:208px;height:260px;image-rendering:pixelated;object-fit:contain;z-index:1}.card small{font:14px 'Songti SC',serif;color:#6A7966;margin-top:5px}.poses{display:flex;gap:9px;justify-content:space-around;border-top:1px solid #DADCCE;margin-top:26px;padding-top:16px}.poses canvas{width:98px;height:122px;image-rendering:pixelated;object-fit:contain}footer{font-size:10px;color:#96A18D;text-align:center;margin-top:16px;letter-spacing:1px}
 </style><header><h1>小镇的新面孔</h1><span>PLAYER ATELIER / v0.2.1</span></header><div class="comparison"><div class="compare-card"><canvas id="before"></canvas><div><h2>原造型</h2><p>64 × 80 像素<br>原先的比例与图层</p></div></div><div class="compare-card new"><canvas id="after"></canvas><div><h2>重绘造型</h2><p>128 × 160 像素<br>柔和轮廓 · 分束头发 · 细致衣橱</p></div></div></div><div class="lineup">${styles.map((p,i)=>`<div class="card"><canvas id="s${i}"></canvas><small>${p.label}</small></div>`).join('')}</div><div class="poses">${poses.map((_,i)=>`<canvas id="p${i}"></canvas>`).join('')}</div><footer>实际游戏渲染 · 30 项外观参数可编辑 · 正侧背面与动作保留</footer><script>
 const paint=(id,p)=>{const c=document.getElementById(id);c.width=p.width;c.height=p.height;c.getContext('2d').putImageData(new ImageData(new Uint8ClampedArray(p.data),p.width,p.height),0,0)};
 paint('before',${JSON.stringify(old)});paint('after',${JSON.stringify(current)});${styles.map((p,i)=>`paint('s${i}',${JSON.stringify(p.pixels)});`).join('')}${poses.map((p,i)=>`paint('p${i}',${JSON.stringify(p)});`).join('')}window.ready=true;
 </script></html>`;
 const file=path.join(out,'avatar-refined-lineup.html');fs.writeFileSync(file,html);
 const win=new BrowserWindow({show:false,width:1230,height:1280,enableLargerThanScreen:true,frame:false,useContentSize:true,webPreferences:{sandbox:true,nodeIntegration:false,contextIsolation:true,backgroundThrottling:false}});
 win.webContents.on('console-message',(_,level,text)=>{if(level>=3)console.error(text)});try{await win.loadFile(file);await win.webContents.executeJavaScript('document.fonts.ready');await win.webContents.executeJavaScript('new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))');const png=await win.webContents.capturePage();fs.writeFileSync(path.join(out,'avatar-refined-lineup.png'),png.toPNG());console.log(path.join(out,'avatar-refined-lineup.png'));app.exit(0);}catch(e){console.error(e.stack);app.exit(1);}
});
