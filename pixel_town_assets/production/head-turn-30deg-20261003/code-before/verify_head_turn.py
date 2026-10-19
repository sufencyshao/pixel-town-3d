#!/usr/bin/env python3
"""Check yaw sources, fixed body, held-key timing and limited replacement scope."""
import json, hashlib
import numpy as np
from PIL import Image
from build_daily_actions import ROOT, residents, prepare_human, sha
from head_turn import REVISION, source_keys
from revise_head_turn import AUDIT, BACKUP

def main():
    before=json.loads((AUDIT/'before.json').read_text());errors=[];checks=[]
    for name,value in before['preservedFileSHA256'].items():
        if not (ROOT/name).exists() or sha(ROOT/name)!=value:errors.append('protected file changed: '+name)
    for name,value in before['replacedFileSHA256'].items():
        if sha(BACKUP/name)!=value:errors.append('backup changed: '+name)
    for folder in residents('characters'):
        mf=json.loads((folder/'animation.json').read_text())
        previous=json.loads((BACKUP/folder.relative_to(ROOT)/'animation.json').read_text())
        for action in ('nod','chat'):
            if mf['animations'][action]!=previous['animations'][action]:errors.append(folder.name+': other clip definition changed')
        clip=mf['animations']['shake_head'];meta=clip.get('headTurn',{})
        if meta.get('revision')!=REVISION:errors.append(folder.name+': yaw revision missing');continue
        front,box=prepare_human(folder);keys,registration=source_keys(folder,front,box)
        atlas=np.asarray(Image.open(folder/clip['atlas']).convert('RGBA'))
        frames=[atlas[:,i*256:(i+1)*256] for i in range(16)]
        if not np.array_equal(frames[0],front) or not np.array_equal(frames[8],front):
            errors.append(folder.name+': frontal identity changed')
        fixed=meta['bodyFixedFromY'];cut=meta['cutY']
        for a in frames:
            if not np.array_equal(a[fixed:],front[fixed:]):errors.append(folder.name+': lower body moves')
            if not np.array_equal(a[cut+10:,124:132],front[cut+10:,124:132]):errors.append(folder.name+': central torso moves')
        # Extremes must contain the actual registered directional head pixels,
        # preventing a regression back to an all-frontal roll/translation.
        for direction,index in ((-1,3),(1,11)):
            key=np.asarray(keys[direction]);visible=key[:,:,3]>0
            if not np.array_equal(frames[index][visible],key[visible]):errors.append(folder.name+': directional head key lost')
        unique=len({hashlib.sha256(a.tobytes()).hexdigest() for a in frames})
        if unique<7:errors.append(folder.name+': yaw transitions missing')
        if meta.get('rollDegrees')!=0 or meta.get('verticalMotion')!=0:errors.append(folder.name+': pendulum motion enabled')
        if any(sha(folder/name)!=mf['sourceSHA256'][name] for name in clip['sources']):errors.append(folder.name+': source hash mismatch')
        with Image.open(folder/clip['gif']) as gif:
            duration=0
            for i in range(gif.n_frames):gif.seek(i);duration+=gif.info.get('duration',0)
            if duration!=1440:errors.append(folder.name+': held pose timing lost')
        checks.append({'role':folder.name,'uniqueYawPoses':unique,'lowerBodyFixedFromY':fixed,
            'frontExact':True,'nativeDirectionalHeads':True,'durationMs':duration,
            'leftSource':registration['registrations']['-1'],'rightSource':registration['registrations']['1']})
    result={'revision':REVISION,'roles':len(checks),'replacedClips':len(checks),'frames':16*len(checks),
        'preservedFiles':len(before['preservedFileSHA256']),'backupFiles':len(before['replacedFileSHA256']),
        'errors':errors,'checks':checks,'humanApproval':'pending visual review of the corrected shake_head clips'}
    (AUDIT/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='checks'},ensure_ascii=False,indent=2))
    return bool(errors)

if __name__=='__main__':raise SystemExit(main())
