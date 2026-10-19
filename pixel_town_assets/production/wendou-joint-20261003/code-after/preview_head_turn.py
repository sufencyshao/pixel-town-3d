"""Frame-controlled whole-body and neck-detail review for all characters."""
import json,html,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
from build_daily_actions import ROOT,prepare_human

KEY_PHASES=[0,1,2,3,7,8,9]

def build_preview(roles,audit,backup,revision,aliases=True):
    signatures=[]
    for folder in roles:
        meta=json.loads((folder/'animations/daily/manifest.json').read_text())['animations']['shake_head']['headTurn']
        signatures.append(meta['fixedBodySHA256']+json.dumps(meta['registeredHeadSHA256'],sort_keys=True))
    cache_revision=revision+'-'+hashlib.sha256('\n'.join(signatures).encode()).hexdigest()[:12]
    cards=[];options=['<option value="">全部角色</option>']
    for folder in roles:
        name=json.loads((folder/'profile.json').read_text())['name'];rel=folder.relative_to(ROOT).as_posix()
        meta=json.loads((folder/'animations/daily/manifest.json').read_text())['animations']['shake_head']['headTurn']
        old='../../'+(backup/folder.relative_to(ROOT)/'animations/daily/shake_head').relative_to(ROOT).as_posix()
        new='../../'+rel+'/animations/daily/shake_head'
        options.append(f'<option value="{folder.name}">{html.escape(name)} · {folder.name[:2]}</option>')
        figures=''.join(f'<figure><div class="sprite"><img width="256" height="256" src="{base}/frame_01.png?v={cache_revision}" alt="{html.escape(name)}{label}"></div><figcaption>{label}</figcaption><canvas class="neck" width="288" height="180" aria-label="{html.escape(name)}{label}颈肩放大"></canvas></figure>' for base,label in ((old,'此前'),(new,'修正后')))
        cards.append(f'<article id="role-{folder.name[:2]}" data-role="{folder.name}" data-old="{old}" data-new="{new}" data-jaw="{meta["anatomyCalibration"]["targetJawY"]}"><h2>{html.escape(name)}</h2><small>{folder.name}</small><div class="pair">{figures}</div></article>')
    markup='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>人物摇头 · 逐帧颈肩复查</title><style>
*{box-sizing:border-box}body{margin:0;background:#eeeddf;color:#234335;font:15px/1.55 system-ui}header{padding:22px 28px;background:#244e3b;color:#fff8e4}h1{margin:0;font-size:25px}header p{max-width:900px;margin:8px 0}a{color:#f4d5a1}.controls{position:sticky;top:0;z-index:2;background:#fffdf6;border-bottom:1px solid #bac7b8;padding:12px 22px;display:flex;align-items:center;gap:12px;flex-wrap:wrap}button,select{font:inherit;padding:6px 10px;border:1px solid #94aa98;border-radius:4px;background:#f5f7ec;color:#234335}button{cursor:pointer}input[type=range]{width:210px}output{font-variant-numeric:tabular-nums;min-width:175px}main{padding:20px;display:grid;grid-template-columns:repeat(auto-fit,minmax(min(610px,100%),1fr));gap:18px}article{background:#fffdf6;border:1px solid #c3c9b9;border-radius:8px;padding:15px}article[hidden]{display:none}h2{font-size:20px;margin:0}small{color:#68796b}.pair{display:grid;grid-template-columns:repeat(2,minmax(0,288px));gap:14px;justify-content:center}figure{margin:12px 0 0;min-width:0}.sprite{width:256px;max-width:100%;margin:auto}img,canvas{display:block;width:100%;height:auto;image-rendering:pixelated;background:repeating-conic-gradient(#dce4dc 0 25%,#f6f6ef 0 50%) 0/16px 16px}figcaption{text-align:center;margin:4px 0}.neck{margin-top:8px}body.hide-neck .neck{display:none}.legend{color:#637261;font-size:13px}#status{font-size:13px;color:#637261}@media(max-width:600px){header{padding:16px}.controls{padding:10px;gap:8px}main{padding:10px}.pair{gap:8px}article{padding:10px}input[type=range]{width:150px}}
</style><header><h1>人物摇头：颈肩逐帧对照</h1><p>整头转向约 30°，快速摇动两下，再回正停顿。上排看完整人物，下排看放大的下巴、脖子、衣领和双肩。可暂停、逐帧查看或慢放。</p><a href="../head-turn-anatomy/completion.md">修改文件与检查记录</a></header><div class="controls"><button id="toggle">暂停</button><button id="previous" aria-label="上一帧">← 上一帧</button><button id="next" aria-label="下一帧">下一帧 →</button><label>速度 <select id="speed"><option value="1">正常</option><option value="0.25">慢放 ¼</option></select></label><input id="phase" aria-label="动作相位" type="range" min="0" max="24" value="0"><output id="readout"></output><label>角色 <select id="role">'''+''.join(options)+'''</select></label><label><input id="neck" type="checkbox" checked>颈肩放大</label><span id="status"></span></div><main>'''+''.join(cards)+'''</main><script>
const revision='''+json.dumps(cache_revision)+''';
const angles=[0,-15,-25.980762,-30,-25.980762,-15,0,15,25.980762,30,25.980762,15,0,-15,-25.980762,-30,-25.980762,-15,0,15,25.980762,30,25.980762,15,0];
const representative=[0,1,2,3,2,1,0,7,8,9,8,7,0,1,2,3,2,1,0,7,8,9,8,7,0];
const cards=[...document.querySelectorAll('article')],cache=new Map(),visible=new Set();
let playing=true,phase=0,rate=1,clock=0,last=performance.now();
const phaseInput=document.querySelector('#phase'),readout=document.querySelector('#readout'),toggle=document.querySelector('#toggle');
function source(card,before,index){return `${before?card.dataset.old:card.dataset.new}/frame_${String(index+1).padStart(2,'0')}.png?v=${revision}`}
function picture(url){if(!cache.has(url)){const im=new Image();im.src=url;cache.set(url,im)}return cache.get(url)}
function preload(card){for(const index of [0,1,2,3,7,8,9])for(const before of [true,false])picture(source(card,before,index));}
function draw(card){if(card.hidden)return;const key=representative[phase],imgs=[...card.querySelectorAll('img')],canvases=[...card.querySelectorAll('canvas')];imgs.forEach((im,i)=>{const url=source(card,i===0,key),ready=picture(url);if(im.src!==ready.src)im.src=ready.src;const paint=()=>{const ctx=canvases[i].getContext('2d');ctx.imageSmoothingEnabled=false;ctx.clearRect(0,0,288,180);ctx.drawImage(ready,80,Number(card.dataset.jaw)-20,96,60,0,0,288,180)};if(ready.complete&&ready.naturalWidth)paint();else ready.onload=()=>{if(representative[phase]===key)paint()};});card.dataset.phase=String(phase);}
function render(){phaseInput.value=phase;readout.textContent=`第 ${phase+1}/25 帧 · ${Math.abs(angles[phase]).toFixed(1)}° ${angles[phase]<0?'左转':angles[phase]>0?'右转':'回正'}`;for(const card of visible)draw(card);}
const observer=new IntersectionObserver(entries=>{for(const entry of entries){if(entry.isIntersecting){visible.add(entry.target);preload(entry.target);draw(entry.target)}else visible.delete(entry.target)}},{rootMargin:'160px'});cards.forEach(card=>observer.observe(card));
function pause(){playing=false;toggle.textContent='播放'}
function setPhase(n){pause();phase=(n+25)%25;clock=phase*30;render()}
toggle.onclick=()=>{playing=!playing;toggle.textContent=playing?'暂停':'播放';last=performance.now()};
document.querySelector('#previous').onclick=()=>setPhase(phase-1);document.querySelector('#next').onclick=()=>setPhase(phase+1);phaseInput.oninput=()=>setPhase(Number(phaseInput.value));
document.querySelector('#speed').onchange=e=>{rate=Number(e.target.value);last=performance.now()};
document.querySelector('#neck').onchange=e=>document.body.classList.toggle('hide-neck',!e.target.checked);
document.querySelector('#role').onchange=e=>{cards.forEach(card=>{card.hidden=Boolean(e.target.value&&card.dataset.role!==e.target.value);if(!card.hidden){preload(card);draw(card)}});document.querySelector('#status').textContent=e.target.value?'已筛选 1 位角色':'共 40 位角色';render()};
function tick(now){if(playing){clock=(clock+(now-last)*rate)%1200;const next=clock>=720?24:Math.floor(clock/30);if(next!==phase){phase=next;render()}}last=now;requestAnimationFrame(tick)}
render();requestAnimationFrame(tick);document.querySelector('#status').textContent='共 40 位角色';
</script></html>'''
    markup=markup.replace('共 40 位角色',f'共 {len(roles)} 位角色')
    markup=markup.replace('../head-turn-anatomy/completion.md',f'../{audit.name}/completion.md')
    if audit.name=='wendou-joint':
        markup=markup.replace('人物摇头：颈肩逐帧对照','闻豆摇头：颈根修正对照')
        markup=markup.replace('整头转向约 30°，快速摇动两下，再回正停顿。',
            '闻豆的脖子重新接回原领口，下巴和头部按原图位置配准。整头转向约 30°，快速摇动两下，再回正停顿。')
    path=audit/'preview.html';path.write_text(markup)
    if aliases:
        for alias in ('head-turn-joints','head-turn-revision'):(ROOT/'validation'/alias/'preview.html').write_text(markup)
    # All seven unique poses, plus enlarged seams, are retained for review.
    for page in range((len(roles)+4)//5):
        group=roles[page*5:page*5+5]
        board=Image.new('RGB',(1792,1280),'#dce4dc');seams=Image.new('RGB',(2016,1000),'#ecdfda');db=ImageDraw.Draw(board);ds=ImageDraw.Draw(seams)
        for row,folder in enumerate(group):
            meta=json.loads((folder/'animation.json').read_text())['animations']['shake_head']['headTurn'];jaw=meta['anatomyCalibration']['targetJawY']
            for col,i in enumerate(KEY_PHASES):
                tile=Image.open(folder/'animations/daily/shake_head'/f'frame_{i+1:02d}.png').convert('RGBA');board.paste(tile,(col*256,row*256),tile);db.text((col*256+2,row*256),folder.name+f' phase {i}',fill='#1a3828')
                crop=tile.crop((80,jaw-20,176,jaw+40)).resize((288,180),Image.Resampling.NEAREST);seams.paste(crop,(col*288,row*200+20),crop);ds.text((col*288+2,row*200),folder.name+f' phase {i}',fill='#1a3828')
        board.save(audit/f'keyposes-{page+1}.png');seams.save(audit/f'seams-{page+1}.png')
