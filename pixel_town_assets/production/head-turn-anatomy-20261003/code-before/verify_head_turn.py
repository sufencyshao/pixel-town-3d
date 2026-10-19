#!/usr/bin/env python3
"""Check illustrated whole-head refusal poses and protected asset scope."""
import json,hashlib
import numpy as np
from PIL import Image
from build_daily_actions import ROOT,residents,prepare_human,sha
from head_turn import REVISION,head_layer
from revise_head_turn import AUDIT,BACKUP

def digest(a):return hashlib.sha256(a.tobytes()).hexdigest()

def main():
    before=json.loads((AUDIT/'before.json').read_text());errors=[];checks=[]
    garment_regions=json.loads((AUDIT/'garment-check-regions.json').read_text())
    for name,value in before['preservedFileSHA256'].items():
        if not (ROOT/name).exists() or sha(ROOT/name)!=value:errors.append('protected file changed: '+name)
    for name,value in before['replacedFileSHA256'].items():
        if sha(BACKUP/name)!=value:errors.append('backup changed: '+name)
    for folder in residents('characters'):
        prefix=folder.name+': ';mf=json.loads((folder/'animation.json').read_text())
        previous=json.loads((BACKUP/folder.relative_to(ROOT)/'animation.json').read_text())
        for action in previous['animations']:
            if action!='shake_head' and mf['animations'].get(action)!=previous['animations'][action]:errors.append(prefix+'other clip changed: '+action)
        clip=mf['animations']['shake_head'];meta=clip.get('headTurn',{})
        if meta.get('revision')!=REVISION:errors.append(prefix+'wrong revision');continue
        front,_=prepare_human(folder);atlas=Image.open(folder/clip['atlas'])
        if atlas.mode!='RGBA' or atlas.size!=(6400,256) or clip['frames']!=25:errors.append(prefix+'invalid 25-frame atlas');continue
        a=np.asarray(atlas);poses=[a[:,i*256:(i+1)*256] for i in range(25)]
        neutral=[0,6,12,18,24];front_exact=all(np.array_equal(poses[i],front) for i in neutral)
        expected_original=int(folder.name[:2]) not in (4,11)
        if meta.get('neutralUsesOriginal')!=expected_original or meta.get('neutralFrameIndices')!=neutral:errors.append(prefix+'neutral source policy mismatch')
        if expected_original and not front_exact:errors.append(prefix+'original neutral frames changed')
        if any(not np.array_equal(poses[i],poses[0]) for i in neutral):errors.append(prefix+'return-to-neutral pose differs')
        head_paths=meta.get('registeredHeadPaths',{});heads={};union=np.asarray(head_layer(Image.fromarray(front),int(folder.name[:2]),0,meta['cutY']))[:,:,3]>0
        for angle,name in head_paths.items():
            head=np.asarray(Image.open(folder/name));heads[angle]=head;union|=head[:,:,3]>0
            if sha(folder/name)!=meta['registeredHeadSHA256'][name]:errors.append(prefix+'registered head hash mismatch')
        if len(heads)!=7:errors.append(prefix+'missing registered whole-head poses');continue
        if any(not np.array_equal(p[~union],front[~union]) for p in poses):errors.append(prefix+'pixels outside moving head changed')
        fixed=meta['bodyFixedFromY']
        if any(not np.array_equal(p[fixed:],front[fixed:]) for p in poses):errors.append(prefix+'lower body moves')
        # Check the original clothing itself, independently of the moving-head
        # union. A shoulder accidentally admitted into that union must still fail.
        fixed_body=np.asarray(Image.open(folder/meta['fixedBodyPath']))
        fixed_mask=fixed_body[:,:,3]>0
        if sha(folder/meta['fixedBodyPath'])!=meta['fixedBodySHA256']:errors.append(prefix+'fixed body hash mismatch')
        body_exact=all(np.array_equal(p[fixed_mask],front[fixed_mask]) for p in poses)
        if not body_exact:errors.append(prefix+'original collar/shoulder/neck-root pixels changed')
        landmark_exact=True
        for x0,y0,x1,y1 in garment_regions[folder.name]['fixedGarmentRects']:
            if any(not np.array_equal(p[y0:y1,x0:x1],front[y0:y1,x0:x1]) for p in poses):landmark_exact=False
        if not landmark_exact:errors.append(prefix+'independent original garment landmark changed')
        xl,xr,join=meta['jointCalibration']['neckRoot'];join=min(join,meta['cutY']-3)
        bridges=[]
        for p in poses:
            # An 8-connected opaque path must cross the actual central joint.
            # This also supports original one-pixel diagonal outlines.
            x0=max(0,xl-6);x1=min(256,xr+7);y0=max(0,join-14);y1=min(256,join+8)
            local=p[y0:y1,x0:x1,3]>0;seen=np.zeros_like(local);q=[]
            for y,x in zip(*np.where(local)):
                if y+y0>=join+1 and xl<=x+x0<=xr:seen[y,x]=True;q.append((int(y),int(x)))
            while q:
                y,x=q.pop()
                for dy in (-1,0,1):
                    for dx in (-1,0,1):
                        ny,nx=y+dy,x+dx
                        if 0<=ny<local.shape[0] and 0<=nx<local.shape[1] and local[ny,nx] and not seen[ny,nx]:seen[ny,nx]=True;q.append((ny,nx))
            bridges.append(bool(seen[:max(1,join-y0-4)].any()))
        if not all(bridges):errors.append(prefix+'disconnected central neck joint at phases '+str([i for i,v in enumerate(bridges) if not v]))
        angles=meta.get('yawDegreesSequence',[])
        if len(angles)!=25 or meta.get('maxYawDegrees')!=30 or max(map(abs,angles),default=999)>30:errors.append(prefix+'invalid small-angle targets');continue
        for angle,pose in zip(angles,poses):
            key=str(int(angle)) if float(angle).is_integer() else str(angle)
            head=heads[key];mask=head[:,:,3]>0
            if not np.array_equal(pose[mask],head[mask]):errors.append(prefix+'registered head not composited intact')
        minima=[i for i in range(1,24) if angles[i]<angles[i-1] and angles[i]<angles[i+1]]
        maxima=[i for i in range(1,24) if angles[i]>angles[i-1] and angles[i]>angles[i+1]]
        if minima!=[3,15] or maxima!=[9,21] or any(angles[i]!=0 for i in neutral):errors.append(prefix+'not two full shakes ending neutral')
        if meta.get('shakeCount')!=2 or any(not np.array_equal(poses[i],poses[i+12]) for i in range(13)):errors.append(prefix+'second shake differs')
        unique=len({digest(p) for p in poses});silhouettes=len({digest(p[:,:,3]) for p in heads.values()})
        if unique!=7 or silhouettes<5:errors.append(prefix+'whole-head silhouettes do not turn')
        top=meta['originalHeadBox'][1];crown_bottom=round(top+(meta['cutY']-top)*.35)
        crown_changes=[int(np.count_nonzero(np.any(heads[str(v)][top:crown_bottom]!=heads['0'][top:crown_bottom],axis=2))) for v in (-30,30)]
        if min(crown_changes)<40:errors.append(prefix+'hair/hat crown frozen during turn')
        if not meta.get('wholeHeadTurns') or meta.get('headSilhouetteFixed') is not False:errors.append(prefix+'whole-head method missing')
        if meta.get('rollDegrees')!=0 or meta.get('verticalMotion')!=0:errors.append(prefix+'pendulum settings present')
        for name in clip['sources']:
            if sha(folder/name)!=mf['sourceSHA256'][name]:errors.append(prefix+'source hash mismatch')
        if clip.get('loop') is not False or clip.get('previewLoop') is not True:errors.append(prefix+'event/preview loop flags wrong')
        durations=clip.get('durations',[])
        if durations!=[30]*24+[480] or clip['frameMs']!=30 or meta.get('activeDurationMs')!=720:errors.append(prefix+'two-shake timing wrong')
        with Image.open(folder/clip['gif']) as gif:
            actual=[]
            for i in range(gif.n_frames):gif.seek(i);actual.append(gif.info.get('duration',0))
            if actual!=durations:errors.append(prefix+'GIF frame timing wrong')
        with Image.open(folder/'animations/daily/overview.gif') as overview:
            overview_ms=0
            for i in range(overview.n_frames):overview.seek(i);overview_ms+=overview.info.get('duration',0)
            if overview_ms!=4080:errors.append(prefix+'overview timing wrong')
        checks.append({'role':folder.name,'uniquePoses':unique,'headSilhouettes':silhouettes,'crownChangedPixelsAtExtremes':crown_changes,'neutralFramesExact':front_exact,'originalBodyExact':body_exact,
            'garmentLandmarksExact':landmark_exact,'connectedNeckPhases':sum(bridges),
            'fixedBodyOpaquePixels':int(fixed_mask.sum()),'bodyFixedFromY':fixed,'angleTargets':[-30,30],'shakeCount':2,'activeDurationMs':720,'gifDurationMs':sum(actual),'overviewDurationMs':overview_ms})
    result={'revision':REVISION,'roles':len(checks),'replacedClips':len(checks),'frames':25*len(checks),'preservedFiles':len(before['preservedFileSHA256']),'backupFiles':len(before['replacedFileSHA256']),'errors':errors,'checks':checks,'humanApproval':'pending visual review of all 40 illustrated whole-head clips'}
    (AUDIT/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='checks'},ensure_ascii=False,indent=2));return bool(errors)
if __name__=='__main__':raise SystemExit(main())
