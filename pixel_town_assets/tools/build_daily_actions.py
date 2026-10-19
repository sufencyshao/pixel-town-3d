#!/usr/bin/env python3
"""Add daily animation clips without overwriting approved/base sprite artwork.

Extends the project's editable pixel rigs; generated tabby poses are only
sliced, palette-limited, and normalized by the established pixel export flow.
"""
from pathlib import Path
import hashlib, json, math, shutil, html
import numpy as np
from PIL import Image, ImageDraw
from animate_existing import NECK, NEW_NECK, smooth, rotate_inverse, palette_frames, save_atlas

ROOT = Path(__file__).resolve().parents[1]
VERSION = '20261003-daily-v1'
DEST = ROOT / 'validation/daily-actions'
PRODUCTION = ROOT / 'production/action-expansion-20261003'
N = 16
Y, X = np.mgrid[:256, :256].astype(float)
HUMAN_ACTIONS = ['nod', 'shake_head', 'chat']
PET_ACTIONS = {
    'cat': ['wag', 'pounce'], 'dog': ['wag', 'stretch'],
    'bird': ['peck', 'hop'], 'rabbit': ['hop', 'chew'],
    'small_mammal': ['forage', 'chew'], 'tortoise': ['bask', 'forage'],
    'equine': ['wag', 'graze'],
}
LABELS = {'nod':'点头', 'shake_head':'摇头', 'chat':'交谈手势', 'wag':'摆尾',
          'pounce':'扑动', 'stretch':'舒展', 'sleep':'蜷睡', 'peck':'啄食',
          'hop':'跳步', 'chew':'啃咬', 'forage':'低头觅食', 'bask':'晒暖探头', 'graze':'低头采食'}

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write_json(path, value): path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
def residents(family):
    return sorted(p for p in (ROOT / family).iterdir()
                  if p.is_dir() and (p / 'animation.json').exists())

def prepare_human(folder):
    # Retain the white-hat outline; generic old cleanup considers it a fragment.
    original = Image.open(folder / 'frame_01.png').convert('RGBA')
    box = original.getbbox(); cut = original.crop(box)
    scale = min(210 / cut.height, 198 / cut.width)
    cut = cut.resize((round(cut.width * scale), round(cut.height * scale)), Image.Resampling.NEAREST)
    out = Image.new('RGBA', (256, 256)); left = (256-cut.width)//2; top = 230-cut.height
    out.paste(cut, (left, top))
    return np.asarray(out), (left, top, cut.width, cut.height)

def sample(source, xx, yy):
    ix = np.rint(xx).astype(int); iy = np.rint(yy).astype(int)
    valid = (ix >= 0) & (ix < 256) & (iy >= 0) & (iy < 256)
    out = np.zeros_like(source); out[valid] = source[iy[valid], ix[valid]]
    out[out[:, :, 3] == 0] = 0
    return Image.fromarray(out)

def human_frames(folder, action):
    role = int(folder.name[:2]); src, (left, top, w, h) = prepare_human(folder)
    if action == 'shake_head':
        from head_turn import frames
        return frames(folder,src,(left,top,w,h))[0]
    neck = top + h * (NEW_NECK[role-21] if role >= 21 else NECK[role-1])
    head = 1 - smooth((Y-(neck-5))/14)
    shoulder = neck + h*.075; hip = top + h*.76
    frames = []
    for i in range(N):
        t = i*2*math.pi/N; xx=X.copy(); yy=Y.copy()
        if action == 'nod':
            # Two gentle vertical nods; feet and lower torso remain planted.
            yy -= 5*(1-math.cos(2*t))/2*head
            xx = 128+(xx-128)/(1-.025*(1-math.cos(2*t))/2*head)
        else:
            # Body-language clip: original mouth and personal facial pixels.
            xx, yy = rotate_inverse(xx, yy, 128, neck, math.radians(1.4)*math.sin(t), head)
            arms = smooth((yy-(shoulder-6))/9)*(1-smooth((yy-(hip-7))/10))
            for side in (-1, 1):
                weight = arms*smooth((side*(xx-128)-w*.225)/(w*.105))
                angle = math.radians(10)*math.sin(t+(0 if side<0 else math.pi/2))
                xx, yy = rotate_inverse(xx, yy, 128+side*w*.20, shoulder, angle, weight)
        frames.append(sample(src, xx, yy))
    return frames

def pet_frames(folder, rig, action):
    base=Image.open(folder/'frame_01.png').convert('RGBA'); src=np.asarray(base)
    x0,y0,x1,y1=base.getbbox();w=x1-x0;h=y1-y0;frames=[]
    for i in range(N):
        t=i*2*math.pi/N; pulse=(1-math.cos(t))/2; xx=X.copy(); yy=Y.copy()
        head=smooth((xx-(x0+w*.59))/(w*.22))*(1-smooth((yy-(y0+h*.57))/(h*.17)))
        feet=smooth((yy-(y0+h*.74))/(h*.19))
        if action=='wag':
            tail=(1-smooth((xx-(x0+w*.07))/(w*.20)))*(1-smooth((yy-(y0+h*.64))/(h*.15)))
            xx,yy=rotate_inverse(xx,yy,x0+w*.22,y0+h*.58,math.radians(12)*math.sin(2*t),tail)
        elif action=='pounce':
            # Low four-legged bounding approximation, no upright animal pose.
            yy += 14*pulse
            yy -= 3*math.cos(t)*feet
            xx -= 2*math.sin(t)*feet
            xx,yy=rotate_inverse(xx,yy,x0+w*.65,y0+h*.50,math.radians(3)*math.sin(t),head)
        elif action=='stretch':
            # Forequarter bow from existing four-foot stance. A rig approximation.
            fore=smooth((xx-(x0+w*.36))/(w*.35))
            yy -= 9*pulse*fore*(1-feet)
            xx -= 6*pulse*fore*feet
            xx,yy=rotate_inverse(xx,yy,x0+w*.66,y0+h*.53,math.radians(10)*pulse,head)
        elif action=='peck':
            xx,yy=rotate_inverse(xx,yy,x0+w*.66,y0+h*.55,math.radians(18)*pulse,head)
        elif action=='hop':
            lift=9 if rig=='bird' else 12
            yy += lift*pulse
            xx,yy=rotate_inverse(xx,yy,x0+w*.69,y0+h*.56,math.radians(2)*math.sin(t),head)
            xx += math.sin(t)*2*feet
        elif action=='chew':
            muzzle=smooth((xx-(x0+w*.80))/(w*.13))*smooth((yy-(y0+h*.40))/(h*.15))*(1-feet)
            yy -= 2*math.sin(3*t)*muzzle
            xx,yy=rotate_inverse(xx,yy,x0+w*.65,y0+h*.53,math.radians(2)*math.sin(t),head)
        elif action=='bask':
            xx -= 4*pulse*head
            xx,yy=rotate_inverse(xx,yy,x0+w*.68,y0+h*.55,math.radians(-4)*pulse,head)
        elif action in ('forage','graze'):
            bend=12 if action=='graze' else 9
            xx,yy=rotate_inverse(xx,yy,x0+w*.65,y0+h*.54,math.radians(bend)*pulse,head)
            xx += math.sin(2*t)*2*head
        out=sample(src,xx,yy)
        # The pet export flow already uses a 128px hard-edge working grid.
        out=out.resize((128,128),Image.Resampling.NEAREST).resize((256,256),Image.Resampling.NEAREST)
        frames.append(out)
    return frames

def generated_tabby(folder):
    source=PRODUCTION/'01_cat_tabby-stretch-sleep-source.png'
    local=folder/'source/daily-tabby-poses.png';local.parent.mkdir(exist_ok=True)
    shutil.copy2(source,local)
    sheet=Image.open(source).convert('RGBA');cells=[]
    # The model returned 1254px, not the requested 1024. Read actual dimensions.
    for row in range(4):
        for col in range(4):
            cells.append(sheet.crop((round(col*sheet.width/4),round(row*sheet.height/4),
                                     round((col+1)*sheet.width/4),round((row+1)*sheet.height/4))))
    bounds=[]
    for im in cells:
        im.putalpha(im.getchannel('A').point(lambda a:255 if a>=128 else 0))
        bounds.append(im.getbbox())
    if any(b is None for b in bounds):raise ValueError('Generated cat sheet contains empty cells')
    scale=min(208/max(b[2]-b[0] for b in bounds),176/max(b[3]-b[1] for b in bounds))
    shared_palette=sheet.convert('RGB').quantize(colors=32,dither=Image.Dither.NONE)
    frames=[]
    for im,b in zip(cells,bounds):
        # Common scale, centered CELL coordinates and fixed ground line.
        resized=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST)
        out=Image.new('RGBA',(256,256));out.paste(resized,
            (round(128-im.width*scale/2),round(232-b[3]*scale)))
        logical=out.resize((64,64),Image.Resampling.NEAREST)
        logical.putalpha(logical.getchannel('A').point(lambda a:255 if a>=128 else 0))
        # Flat 32-color pixel clusters from the generated art; no dithering.
        alpha=logical.getchannel('A');colored=logical.convert('RGB').quantize(palette=shared_palette,dither=Image.Dither.NONE).convert('RGBA')
        colored.putalpha(alpha)
        arr=np.array(colored);arr[arr[:,:,3]==0]=0
        frames.append(Image.fromarray(arr).resize((256,256),Image.Resampling.NEAREST))
    return {'stretch':frames[:8], 'sleep':frames[8:]}, local

def save_clip(folder,action,frames,ms,technique,source,*,durations=None,loop=True):
    dest=folder/'animations/daily';dest.mkdir(parents=True,exist_ok=True)
    keydir=dest/action;keydir.mkdir(exist_ok=True)
    for i,frame in enumerate(frames):frame.save(keydir/f'frame_{i+1:02d}.png')
    save_atlas(frames,dest/(action+'.png'))
    gifs=palette_frames(frames)
    gifs[0].save(dest/(action+'.gif'),save_all=True,append_images=gifs[1:],duration=durations or ms,
                 transparency=0,disposal=2,optimize=False,loop=0)
    with Image.open(dest/(action+'.gif')) as gif:gif_count=gif.n_frames
    clip=dict(atlas=f'animations/daily/{action}.png',gif=f'animations/daily/{action}.gif',
                frames=len(frames),frameMs=ms,loop=loop,gifFrames=gif_count,
                source=source,technique=technique,individualFrames=f'animations/daily/{action}',
                humanApproval='pending review of this new clip')
    if durations is not None:clip['durations']=list(durations)
    if not loop:clip['previewLoop']=True
    return clip

def restore_daily_metadata(folder):
    sidecar=folder/'animations/daily/manifest.json'
    if not sidecar.exists():return
    daily=json.loads(sidecar.read_text())
    for source,value in daily['sourceSHA256'].items():
        if sha(folder/source)!=value:raise ValueError(f'{folder.name}: daily source changed; rebuild daily actions')
    for name in ('animation.json','animation-manifest.json'):
        path=folder/name
        if not path.exists():continue
        mf=json.loads(path.read_text());mf['animations'].update(daily['animations'])
        mf.setdefault('sourceSHA256',{}).update(daily['sourceSHA256'])
        mf['dailyActionExpansion']={'version':VERSION,'manifest':'animations/daily/manifest.json',
                                    'actions':list(daily['animations']),'humanApproval':'pending new-action review'}
        write_json(path,mf)

def build_folder(folder,family):
    profile=json.loads((folder/'profile.json').read_text());clips={};sources={}
    if family=='characters':
        for action in HUMAN_ACTIONS:
            if action=='shake_head':
                from head_turn import frames
                src,box=prepare_human(folder);poses,registration=frames(folder,src,box)
                clip=save_clip(folder,action,poses,registration['frameMs'],
                    'imagegen whole-head keyposes from original directional sprites; original palette and body; +/-30-degree pose targets; two quick refusal shakes','frame_01.png',
                    durations=registration['durations'],loop=registration['loop'])
                clips[action]=clip
                clip['sources']=registration['sources']
                clip['headTurn']=registration
                for source in clip['sources']:sources[source]=sha(folder/source)
            else:
                clips[action]=save_clip(folder,action,human_frames(folder,action),90,
                    'existing pixel rig; personal face preserved; body language, no lip sync','frame_01.png')
        sources['frame_01.png']=sha(folder/'frame_01.png')
    else:
        rig=profile['animal']['rig']
        for action in PET_ACTIONS[rig]:
            clips[action]=save_clip(folder,action,pet_frames(folder,rig,action),
                                   130 if rig=='tortoise' else 80,
                                   f'existing {rig} pixel rig; approximate natural gesture','frame_01.png')
        sources['frame_01.png']=sha(folder/'frame_01.png')
        if folder.name=='01_cat_tabby':
            generated,local=generated_tabby(folder);key=local.relative_to(folder).as_posix()
            for action,frames in generated.items():
                clips[action]=save_clip(folder,action,frames,160 if action=='stretch' else 200,
                    'imagegen pose sheet; nearest-neighbour 64px logical grid; binary alpha; 32-color export',key)
            sources[key]=sha(local)
        profile['animal']['allowedActions']=list(dict.fromkeys(profile['animal']['allowedActions']+list(clips)))
        write_json(folder/'profile.json',profile)
        path=folder/'profile.md';text=path.read_text();marker='\n## 2026-10-03 新增日常动作\n'
        text=text.split(marker)[0]+marker+'\n'+', '.join(f'{a}（{LABELS[a]}）' for a in clips)+'。动作仅依据该物种姿态，程序分区动作属于近似表现；虎斑猫舒展/蜷睡使用新绘制的姿势。\n'
        path.write_text(text)
    sidecar={'version':1,'batch':VERSION,'frameWidth':256,'frameHeight':256,
             'animations':clips,'sourceSHA256':sources}
    write_json(folder/'animations/daily/manifest.json',sidecar);restore_daily_metadata(folder)
    save_daily_overview(folder,clips)
    return {'family':family,'id':folder.name,'name':profile['name'],'clips':clips}

def save_daily_overview(folder,clips):
    overview=[Image.open(folder/c['atlas']).crop((i*256,0,(i+1)*256,256))
              for c in clips.values() for i in range(c['frames'])]
    durations=[duration for c in clips.values() for duration in
               c.get('durations',[c['frameMs']]*c['frames'])]
    gifs=palette_frames(overview);gifs[0].save(folder/'animations/daily/overview.gif',save_all=True,
        append_images=gifs[1:],duration=durations,loop=0,transparency=0,disposal=2,optimize=False)

def baseline(selected):
    DEST.mkdir(parents=True,exist_ok=True);PRODUCTION.mkdir(parents=True,exist_ok=True)
    path=DEST/'baseline.json'
    if path.exists():return
    protected=[];metadata={}
    for _,folder in selected:
        protected += list(folder.glob('frame_*.png'))+[folder/'overview.gif']
        protected += [p for p in (folder/'animations').iterdir() if p.is_file() and p.suffix in ('.png','.gif')]
        protected += list((folder/'legacy_actions').glob('*.png'))
        for name in ('animation.json','animation-manifest.json','profile.json','profile.md'):
            if (folder/name).exists():metadata[(folder/name).relative_to(ROOT).as_posix()]=(folder/name).read_text()
    protected += list((ROOT/'raw_v2').glob('*.png'))+[ROOT/'validation/back-walk-approval.json']
    write_json(path,{p.relative_to(ROOT).as_posix():sha(p) for p in protected})
    write_json(PRODUCTION/'metadata-before.json',metadata)

def preview(rows):
    data=[]
    for row in rows:
        base=f"../../{row['family']}/{row['id']}/"
        data.append({**row,'base':base})
    markup='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>新增日常动作 · 人物与宠物</title><style>*{box-sizing:border-box}body{margin:0;background:#f0eddf;color:#233d32;font:15px/1.65 system-ui}header{padding:26px 5vw;background:#284f3e;color:#faf6e7}h1{margin:0;font-size:28px}main{padding:24px;display:grid;grid-template-columns:repeat(auto-fit,minmax(275px,1fr));gap:18px}article{padding:16px;background:#fffdf6;border:1px solid #cdcbbd;border-radius:8px}h2{font-size:18px;margin:0}small{color:#647468}img{display:block;width:256px;height:256px;margin:12px auto;max-width:100%;image-rendering:pixelated;background:repeating-conic-gradient(#e0e5df 0 25%,#f5f5ee 0 50%) 0/16px 16px}select{width:100%;font:inherit;padding:7px;color:#234b36}p{font-size:13px}header a{color:#f4d6a1}</style><header><h1>新增日常动作 · 40 人物 / 20 宠物</h1><p>本批动作单独保存；原帧和已确认背面循环保留。人物以肢体语言表达交谈；宠物动作按物种分配。虎斑猫新增独立舒展与蜷睡姿势。</p><a href="completion.md">制作记录、完整清单与检查结果</a></header><main id="cards"></main><script id="data" type="application/json">'''+json.dumps(data,ensure_ascii=False).replace('</', r'<\/')+'''</script><script>const data=JSON.parse(document.getElementById('data').textContent),labels='''+json.dumps(LABELS,ensure_ascii=False)+''';for(const r of data){const card=document.createElement('article'),heading=document.createElement('h2'),small=document.createElement('small'),img=document.createElement('img'),select=document.createElement('select'),meta=document.createElement('p');heading.textContent=r.name;small.textContent=r.id;img.loading='lazy';for(const[a,c]of Object.entries(r.clips)){const o=document.createElement('option');o.value=a;o.textContent=labels[a]||a;select.append(o)}if(r.id==='01_cat_tabby')select.value='stretch';function update(){const c=r.clips[select.value];img.src=r.base+c.gif;img.alt=r.name+' '+labels[select.value];meta.textContent=c.headTurn?c.frames+'帧 · 左右约30° · 0.72秒摇两下 · 回正停顿0.48秒':c.frames+'帧 · '+c.frameMs+'ms/帧 · '+(c.technique.includes('imagegen')?'新姿势切片':'原素材分区动作近似');}select.onchange=update;update();card.append(heading,small,img,select,meta);document.getElementById('cards').append(card)}</script></html>'''
    (DEST/'preview.html').write_text(markup)
    for family in ('characters','pets'):
        chosen=[r for r in rows if r['family']==family]
        for page in range(math.ceil(len(chosen)/5)):
            group=chosen[page*5:page*5+5]
            board=Image.new('RGB',(6*128,5*160),'#e1e6de');draw=ImageDraw.Draw(board)
            for row,r in enumerate(group):
                first=list(r['clips'])[0];clip=r['clips'][first]
                atlas=Image.open(ROOT/family/r['id']/clip['atlas'])
                for col,index in enumerate([0,3,6,9,12,15]):
                    index=min(index,clip['frames']-1);tile=atlas.crop((index*256,0,(index+1)*256,256)).resize((128,128),Image.Resampling.NEAREST)
                    board.paste(tile,(col*128,row*160),tile)
                    draw.text((col*128+2,row*160+132),r['id'][:20],fill='#223c2c');draw.text((col*128+2,row*160+146),first+' '+str(index),fill='#223c2c')
            board.save(DEST/f'{family}-sample-page-{page+1}.png')

def main():
    selected=[(family,p) for family in ('characters','pets') for p in residents(family)]
    baseline(selected);rows=[]
    for family,folder in selected:
        row=build_folder(folder,family);rows.append(row);print(f'{family}/{folder.name}: '+', '.join(row['clips']),flush=True)
    preview(rows);write_json(DEST/'generation.json',{'batch':VERSION,'rows':rows})
    print(f'Created {sum(len(r["clips"]) for r in rows)} clips across {len(rows)} entities.')

if __name__=='__main__':main()
