#!/usr/bin/env python3
"""Register whole-head refusal poses over a stable original body underlay."""
from pathlib import Path
import json, shutil, html
from PIL import Image, ImageDraw
from build_daily_actions import (ROOT, DEST, residents, sha, write_json, prepare_human,
    save_clip, save_daily_overview, restore_daily_metadata, preview)
from head_turn import frames, REVISION

AUDIT=ROOT/'validation/head-turn-anatomy'
BACKUP=ROOT/'production/head-turn-anatomy-20261003/before'

def selected_files(folder):
    return sorted([folder/'animation.json',folder/'animation-manifest.json',
        folder/'animations/daily/manifest.json',folder/'animations/daily/overview.gif',
        folder/'animations/daily/shake_head.png',folder/'animations/daily/shake_head.gif']+
        list((folder/'animations/daily/shake_head').glob('*.png'))+list((folder/'source/shake-head-solid').glob('*.png'))+list((folder/'source').glob('shake-head-joint-*.png'))+list((folder/'source').glob('shake-head-body-repair-mask.png')))

def backup(roles):
    AUDIT.mkdir(parents=True,exist_ok=True)
    record=AUDIT/'before.json'
    if record.exists():return
    protected=json.loads((DEST/'baseline.json').read_text());changed={}
    for p in roles:
        protected[(p/'source/shake-head-solid-poses.png').relative_to(ROOT).as_posix()]=sha(p/'source/shake-head-solid-poses.png')
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
    write_json(record,{'revision':REVISION,'revisionBefore':'20261003-refusal-fixed-joints-v6','reason':'User reports disappearing shoulders and displaced necks across nearly all characters. Correct all 40 original body boundaries and generated neck anchors; preserve whole-head turning and timing.',
                       'replacedFileSHA256':changed,'preservedFileSHA256':protected})

def comparison(roles):
    from preview_head_turn import build_preview
    build_preview(roles,AUDIT,BACKUP,REVISION)

def main():
    roles=residents('characters');backup(roles)
    generation=json.loads((DEST/'generation.json').read_text());updated={}
    for folder in roles:
        source,box=prepare_human(folder);poses,registration=frames(folder,source,box)
        clip=save_clip(folder,'shake_head',poses,registration['frameMs'],
            'whole-head poses reused; independent jaw and neck registration over stable body; original hair detail; +/-30-degree targets; two quick refusal shakes','frame_01.png',
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
            'tools/head_anatomy.py','tools/head_anatomy_calibration.json','tools/preview_head_turn.py'],
        'newAssetFiles':sorted(p.relative_to(ROOT).as_posix() for folder in roles for p in (folder/'source').glob('shake-head-body-repair-mask.png')),
        'reportsAndPreview':['validation/head-turn-anatomy/','validation/head-turn-joints/preview.html','validation/head-turn-joints/preview-v6.html','validation/head-turn-joints/completion.md','validation/head-turn-revision/preview.html','validation/daily-actions/generation.json',
            'validation/daily-actions/preview.html','validation/daily-actions/completion.md','asset-gallery.html',
            '人物工作交接.md'],
        'productionRecords':'production/head-turn-anatomy-20261003/',
        'backup':'production/head-turn-anatomy-20261003/before/'})
    print(f'Revised {len(roles)} shake_head clips; {len(changed)} asset/metadata files changed.')

if __name__=='__main__':main()
