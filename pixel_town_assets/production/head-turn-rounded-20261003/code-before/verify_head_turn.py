#!/usr/bin/env python3
"""Check bounded refusal yaw, two complete shakes, fixed body and asset scope."""
import json, hashlib
import numpy as np
from PIL import Image
from build_daily_actions import ROOT, residents, prepare_human, sha
from head_turn import REVISION
from revise_head_turn import AUDIT, BACKUP

def main():
    before=json.loads((AUDIT/'before.json').read_text());errors=[];checks=[]
    for name,value in before['preservedFileSHA256'].items():
        if not (ROOT/name).exists() or sha(ROOT/name)!=value:errors.append('protected file changed: '+name)
    for name,value in before['replacedFileSHA256'].items():
        if sha(BACKUP/name)!=value:errors.append('backup changed: '+name)
    for folder in residents('characters'):
        prefix=folder.name+': '
        mf=json.loads((folder/'animation.json').read_text())
        previous=json.loads((BACKUP/folder.relative_to(ROOT)/'animation.json').read_text())
        for action in previous['animations']:
            if action!='shake_head' and mf['animations'].get(action)!=previous['animations'][action]:
                errors.append(prefix+'other clip definition changed: '+action)
        clip=mf['animations']['shake_head'];meta=clip.get('headTurn',{})
        if meta.get('revision')!=REVISION:errors.append(prefix+'yaw revision missing');continue
        front,_=prepare_human(folder)
        atlas=Image.open(folder/clip['atlas'])
        if atlas.mode!='RGBA' or atlas.size!=(25*256,256) or clip['frames']!=25:
            errors.append(prefix+'invalid 25-frame atlas');continue
        array=np.asarray(atlas)
        poses=[array[:,i*256:(i+1)*256] for i in range(25)]
        neutral=[0,6,12,18,24]
        front_exact=all(np.array_equal(poses[i],front) for i in neutral)
        if not front_exact:errors.append(prefix+'neutral frontal identity changed')
        if meta.get('neutralFrameIndices')!=neutral:errors.append(prefix+'neutral key indices incorrect')
        fixed=meta['bodyFixedFromY']
        if fixed!=meta['cutY']:errors.append(prefix+'neck cutoff mismatch')
        if any(not np.array_equal(a[fixed:],front[fixed:]) for a in poses):errors.append(prefix+'lower body moves')
        angles=meta.get('yawDegreesSequence',[])
        if len(angles)!=25 or meta.get('maxYawDegrees')!=30 or max(map(abs,angles),default=999)>30:
            errors.append(prefix+'yaw exceeds 30 degrees or has wrong sequence length')
        else:
            minima=[i for i in range(1,24) if angles[i]<angles[i-1] and angles[i]<angles[i+1]]
            maxima=[i for i in range(1,24) if angles[i]>angles[i-1] and angles[i]>angles[i+1]]
            if minima!=[3,15] or maxima!=[9,21] or any(angles[i]!=0 for i in neutral):
                errors.append(prefix+'not exactly two left/right shakes ending neutral')
            if any(angles[i]!=-30 for i in minima) or any(angles[i]!=30 for i in maxima):
                errors.append(prefix+'extreme angles incorrect')
        if meta.get('shakeCount')!=2 or any(not np.array_equal(poses[i],poses[i+12]) for i in range(13)):
            errors.append(prefix+'second shake differs from first')
        unique=len({hashlib.sha256(a.tobytes()).hexdigest() for a in poses})
        if unique!=7:errors.append(prefix+'expected seven small yaw poses')
        if meta.get('rollDegrees')!=0 or meta.get('verticalMotion')!=0:errors.append(prefix+'pendulum motion enabled')
        if clip.get('sources')!=['frame_01.png']:errors.append(prefix+'full-profile source still enabled')
        if sha(folder/'frame_01.png')!=mf['sourceSHA256']['frame_01.png']:errors.append(prefix+'source hash mismatch')
        if clip.get('loop') is not False or clip.get('previewLoop') is not True:errors.append(prefix+'event/preview loop flags incorrect')
        durations=clip.get('durations',[])
        if durations!=[30]*24+[480] or clip['frameMs']!=30 or meta.get('activeDurationMs')!=720 or meta.get('neutralPauseMs')!=480:
            errors.append(prefix+'quick shake or neutral pause timing incorrect')
        with Image.open(folder/clip['gif']) as gif:
            actual=[]
            for i in range(gif.n_frames):gif.seek(i);actual.append(gif.info.get('duration',0))
            duration=sum(actual)
            if actual!=durations or duration!=1200:errors.append(prefix+'GIF frame timing incorrect')
        with Image.open(folder/'animations/daily/overview.gif') as overview:
            overview_duration=0
            for i in range(overview.n_frames):overview.seek(i);overview_duration+=overview.info.get('duration',0)
            if overview_duration!=4080:errors.append(prefix+'overview does not preserve clip timing')
        checks.append({'role':folder.name,'uniqueYawPoses':unique,'lowerBodyFixedFromY':fixed,
            'neutralFramesExact':front_exact,'maxYawDegrees':30,'shakeCount':2,
            'activeDurationMs':720,'neutralPauseMs':480,'gifDurationMs':duration,
            'overviewDurationMs':overview_duration,'source':'frame_01.png'})
    result={'revision':REVISION,'roles':len(checks),'replacedClips':len(checks),'frames':25*len(checks),
        'preservedFiles':len(before['preservedFileSHA256']),'backupFiles':len(before['replacedFileSHA256']),
        'errors':errors,'checks':checks,'humanApproval':'pending visual review of 30-degree two-shake refusal clips'}
    (AUDIT/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='checks'},ensure_ascii=False,indent=2))
    return bool(errors)

if __name__=='__main__':raise SystemExit(main())
