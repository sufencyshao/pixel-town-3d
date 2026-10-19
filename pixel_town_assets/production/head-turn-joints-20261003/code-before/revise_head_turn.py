#!/usr/bin/env python3
"""Reduce head yaw to 30 degrees and perform two quick refusal shakes."""
from pathlib import Path
import json, shutil, html
from PIL import Image, ImageDraw
from build_daily_actions import (ROOT, DEST, residents, sha, write_json, prepare_human,
    save_clip, save_daily_overview, restore_daily_metadata, preview)
from head_turn import frames, REVISION

AUDIT=ROOT/'validation/head-turn-solid'
BACKUP=ROOT/'production/head-turn-solid-20261003/before'

def selected_files(folder):
    return sorted([folder/'animation.json',folder/'animation-manifest.json',
        folder/'animations/daily/manifest.json',folder/'animations/daily/overview.gif',
        folder/'animations/daily/shake_head.png',folder/'animations/daily/shake_head.gif']+
        list((folder/'animations/daily/shake_head').glob('*.png')))

def backup(roles):
    AUDIT.mkdir(parents=True,exist_ok=True)
    record=AUDIT/'before.json'
    if record.exists():return
    protected=json.loads((DEST/'baseline.json').read_text());changed={}
    for p in roles:
        for path in selected_files(p):
            key=path.relative_to(ROOT).as_posix();changed[key]=sha(path)
            target=BACKUP/key;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(path,target)
        for path in (p/'animations/daily').rglob('*'):
            if path.is_file() and 'shake_head' not in path.relative_to(p/'animations/daily').parts[0] and path.name!='overview.gif':
                if path.suffix in ('.png','.gif'):protected[path.relative_to(ROOT).as_posix()]=sha(path)
    for p in residents('pets'):
        for path in list((p/'animations/daily').rglob('*'))+[p/'animation.json',p/'profile.json',p/'profile.md']:
            if path.is_file():protected[path.relative_to(ROOT).as_posix()]=sha(path)
    write_json(record,{'revision':REVISION,'reason':'User requires the entire rounded head, hair, ears and accessories to turn together; preserve two quick shakes and small-angle timing.',
                       'replacedFileSHA256':changed,'preservedFileSHA256':protected})

def comparison(roles):
    cards=[]
    for page in range(8):
        group=roles[page*5:page*5+5];board=Image.new('RGB',(1536,1280),'#e1e6de');draw=ImageDraw.Draw(board)
        for row,p in enumerate(group):
            atlas=Image.open(p/'animations/daily/shake_head.png')
            for col,i in enumerate((0,3,9,15,21,24)):
                tile=atlas.crop((i*256,0,(i+1)*256,256));board.paste(tile,(col*256,row*256),tile)
                draw.text((col*256+4,row*256+240),p.name[:2]+f' phase {i}',fill='#223c2c')
        board.save(AUDIT/f'keyposes-{page+1}.png')
    for p in roles:
        name=json.loads((p/'profile.json').read_text())['name'];rel=p.relative_to(ROOT).as_posix()
        old=f'../../production/head-turn-solid-20261003/before/{rel}/animations/daily/shake_head.gif'
        new=f'../../{rel}/animations/daily/shake_head.gif?v={REVISION}'
        cards.append(f'<article><h2>{html.escape(name)}</h2><small>{p.name}</small><div class="pair"><figure><img loading="lazy" width="256" height="256" src="{old}" alt="此前固定外轮廓的摇头"><figcaption>此前：五官在固定轮廓中转向</figcaption></figure><figure><img loading="lazy" width="256" height="256" src="{new}" alt="约30度快速摇两下后回正"><figcaption>当前：头发、耳朵、脸一起转向</figcaption></figure></div></article>')
    markup='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>人物摇头 · 整个头部一起转动</title><style>*{box-sizing:border-box}body{margin:0;background:#f0eddf;color:#233d32;font:15px/1.6 system-ui}header{padding:24px;background:#284f3e;color:#faf6e7}h1{font-size:26px;margin:0}main{padding:20px;display:grid;grid-template-columns:repeat(auto-fit,minmax(min(570px,100%),1fr));gap:20px}article{padding:16px;background:#fffdf6;border:1px solid #cdcbbd;border-radius:8px}h2{margin:0;font-size:18px}small{color:#647468}.pair{display:grid;grid-template-columns:repeat(2,minmax(0,256px));justify-content:center;gap:14px}figure{margin:12px 0;width:100%;max-width:256px}img{display:block;max-width:100%;height:auto;image-rendering:pixelated;background:repeating-conic-gradient(#e0e5df 0 25%,#f5f5ee 0 50%) 0/16px 16px}figcaption{text-align:center}a{color:#f4d6a1}</style><header><h1>摇头修正：整个头部一起转动</h1><p>40 位角色：正面 → 左右往返两次 → 回正。动作 0.72 秒；回正停顿 0.48 秒后，预览重复播放。参考原正面和侧面素材补画整头姿势，头发、耳朵、脸和附属配饰一起转向，身体复用原图；256×256 透明硬边帧。</p><a href="../head-turn-solid/completion.md">制作与验证记录</a></header><main>'''+''.join(cards)+'</main></html>'
    (AUDIT/'preview.html').write_text(markup)
    # Keep the user's already-open preview URL current.
    (ROOT/'validation/head-turn-revision/preview.html').write_text(markup)

def main():
    roles=residents('characters');backup(roles)
    generation=json.loads((DEST/'generation.json').read_text());updated={}
    for folder in roles:
        source,box=prepare_human(folder);poses,registration=frames(folder,source,box)
        clip=save_clip(folder,'shake_head',poses,registration['frameMs'],
            'imagegen whole-head keyposes from original directional sprites; original palette and body; +/-30-degree pose targets; two quick refusal shakes','frame_01.png',
            durations=registration['durations'],loop=registration['loop'])
        clip['sources']=registration['sources']
        clip['headTurn']=registration
        path=folder/'animations/daily/manifest.json';daily=json.loads(path.read_text())
        daily['animations']['shake_head']=clip
        for name in clip['sources']:daily['sourceSHA256'][name]=sha(folder/name)
        write_json(path,daily);restore_daily_metadata(folder);save_daily_overview(folder,daily['animations'])
        updated[folder.name]=clip;print(folder.name+': +/-30 degrees, two quick shakes, neutral finish',flush=True)
    for row in generation['rows']:
        if row['family']=='characters':row['clips']['shake_head']=updated[row['id']]
    generation['headTurnRevision']=REVISION;write_json(DEST/'generation.json',generation)
    preview(generation['rows']);comparison(roles)
    before=json.loads((AUDIT/'before.json').read_text())
    changed=[name for name,value in before['replacedFileSHA256'].items() if sha(ROOT/name)!=value]
    write_json(AUDIT/'changed-files.json',{'revision':REVISION,'changedAssetAndMetadataFiles':changed,
        'implementation':['tools/head_turn.py','tools/revise_head_turn.py','tools/verify_head_turn.py',
            'tools/build_daily_actions.py','tools/verify_daily_actions.py'],
        'newAssetFiles':sorted(p.relative_to(ROOT).as_posix() for folder in roles for p in (folder/'source').rglob('shake-head-solid*') if p.is_file())+sorted(p.relative_to(ROOT).as_posix() for folder in roles for p in (folder/'source/shake-head-solid').glob('*.png')),
        'reportsAndPreview':['validation/head-turn-solid/','validation/head-turn-revision/preview.html','validation/daily-actions/generation.json',
            'validation/daily-actions/preview.html','validation/daily-actions/completion.md','人物工作交接.md'],
        'backup':'production/head-turn-solid-20261003/before/'})
    print(f'Revised {len(roles)} shake_head clips; {len(changed)} asset/metadata files changed.')

if __name__=='__main__':main()
