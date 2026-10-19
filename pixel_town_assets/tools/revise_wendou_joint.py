#!/usr/bin/env python3
"""Rebuild Wendou only, with a frozen v7 backup and protected-file guard."""
import json
from build_daily_actions import (ROOT,DEST,residents,sha,write_json,prepare_human,
    save_clip,restore_daily_metadata,save_daily_overview,preview)
from head_turn import frames,REVISION
from head_anatomy import WENDOU
from preview_head_turn import build_preview
from revise_head_turn import selected_files

AUDIT=ROOT/'validation/wendou-joint'
BACKUP=ROOT/'production/wendou-joint-20261003/before'
ROLE='36_barista_female'

def protected_guard(before):
    # The original snapshot accidentally includes the complete daily manifest
    # in both sets. Its shake_head entry is an authorized replacement; every
    # other entry is compared separately instead of dropping this protection.
    overlap=set(before['preservedFileSHA256'])&set(before['replacedFileSHA256'])
    expected={f'characters/{ROLE}/animations/daily/manifest.json'}
    if overlap!=expected:raise RuntimeError('Unexpected protection overlap: '+str(overlap))
    bad=[name for name,value in before['preservedFileSHA256'].items()
         if name not in overlap and (not (ROOT/name).exists() or sha(ROOT/name)!=value)]
    if bad:raise RuntimeError('Protected files differ: '+', '.join(bad[:10]))
    bad=[name for name,value in before['replacedFileSHA256'].items()
         if not (BACKUP/name).exists() or sha(BACKUP/name)!=value]
    if bad:raise RuntimeError('Frozen v7 backup differs: '+', '.join(bad[:10]))
    for name in overlap:
        old=json.loads((BACKUP/name).read_text());new=json.loads((ROOT/name).read_text())
        old['animations'].pop('shake_head');new['animations'].pop('shake_head')
        if old!=new:raise RuntimeError('Other daily actions or sources changed: '+name)

def main():
    before=json.loads((AUDIT/'before.json').read_text());protected_guard(before)
    folder=ROOT/'characters'/ROLE
    front,box=prepare_human(folder);poses,meta=frames(folder,front,box)
    clip=save_clip(folder,'shake_head',poses,meta['frameMs'],
        'whole skull turns; original shaded V neck at actual collar; +/-30-degree pose targets; two quick refusal shakes',
        'frame_01.png',durations=meta['durations'],loop=meta['loop'])
    clip['sources']=meta['sources'];clip['headTurn']=meta
    path=folder/'animations/daily/manifest.json';daily=json.loads(path.read_text())
    daily['animations']['shake_head']=clip
    for name in clip['sources']:daily['sourceSHA256'][name]=sha(folder/name)
    write_json(path,daily);restore_daily_metadata(folder);save_daily_overview(folder,daily['animations'])
    generation=json.loads((DEST/'generation.json').read_text())
    for row in generation['rows']:
        if row['family']=='characters' and row['id']==ROLE:row['clips']['shake_head']=clip
    generation.setdefault('roleHeadTurnRevisions',{})[ROLE]=WENDOU['revision']
    write_json(DEST/'generation.json',generation);preview(generation['rows'])
    build_preview([folder],AUDIT,BACKUP,WENDOU['revision'],aliases=False)
    build_preview(residents('characters'),ROOT/'validation/head-turn-anatomy',
                  ROOT/'production/head-turn-anatomy-20261003/before',REVISION)
    protected_guard(before)
    changed=[name for name,value in before['replacedFileSHA256'].items() if sha(ROOT/name)!=value]
    write_json(AUDIT/'changed-files.json',{'role':ROLE,'revision':WENDOU['revision'],
        'changedAssetAndMetadataFiles':changed,
        'unchangedSelectedAssetAndMetadataFiles':[name for name in before['replacedFileSHA256'] if name not in changed],
        'implementation':['tools/head_anatomy.py','tools/head_turn.py','tools/wendou_joint_calibration.json',
                          'tools/revise_wendou_joint.py','tools/verify_wendou_joint.py','tools/verify_head_turn.py','tools/preview_head_turn.py'],
        'reportsAndPreview':['validation/wendou-joint/','validation/head-turn-anatomy/','validation/head-turn-joints/preview.html',
            'validation/head-turn-revision/preview.html','validation/daily-actions/generation.json','validation/daily-actions/preview.html',
            'validation/daily-actions/completion.md','asset-gallery.html','人物工作交接.md'],
        'preservedFiles':len(before['preservedFileSHA256'])-1,
        'separatelyCheckedManifest':f'characters/{ROLE}/animations/daily/manifest.json',
        'backup':'production/wendou-joint-20261003/before/'})
    print(f'{ROLE}: {len(poses)} frames rebuilt; {len(changed)} files changed; {len(before["preservedFileSHA256"])-1} protected hashes unchanged; other daily entries unchanged.')

if __name__=='__main__':main()
