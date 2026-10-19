#!/usr/bin/env python3
"""Verify new clips, true transparency, source preservation and approval scope."""
from pathlib import Path
import json, hashlib
import numpy as np
from PIL import Image
from build_daily_actions import ROOT, DEST, sha

def main():
    generated=json.loads((DEST/'generation.json').read_text());errors=[];warnings=[];checks=[]
    baseline=json.loads((DEST/'baseline.json').read_text())
    for name,value in baseline.items():
        if not (ROOT/name).exists() or sha(ROOT/name)!=value:errors.append('original changed: '+name)
    for row in generated['rows']:
        folder=ROOT/row['family']/row['id'];mf=json.loads((folder/'animation.json').read_text())
        if (folder/'animation-manifest.json').exists() and mf!=json.loads((folder/'animation-manifest.json').read_text()):
            errors.append(row['id']+': manifest mismatch')
        for name,value in mf.get('sourceSHA256',{}).items():
            if sha(folder/name)!=value:errors.append(row['id']+': source hash mismatch '+name)
        allowed=json.loads((folder/'profile.json').read_text()).get('animal',{}).get('allowedActions',[])
        for action,clip in row['clips'].items():
            key=row['id']+'/'+action
            if mf['animations'].get(action)!=clip:errors.append(key+': clip metadata mismatch')
            if row['family']=='pets' and action not in allowed:errors.append(key+': missing action whitelist')
            atlas=Image.open(folder/clip['atlas'])
            if atlas.mode!='RGBA' or atlas.size!=(256*clip['frames'],256):errors.append(key+': invalid atlas');continue
            array=np.asarray(atlas)
            if set(np.unique(array[:,:,3]))!={0,255}:errors.append(key+': nonbinary alpha')
            frames=[array[:,i*256:(i+1)*256] for i in range(clip['frames'])]
            unique=len({hashlib.sha256(a.tobytes()).hexdigest() for a in frames})
            if unique<3:errors.append(key+': fewer than 3 unique poses')
            if any(not a[:,:,3].any() for a in frames):errors.append(key+': empty pose')
            if any(any(np.any(edge) for edge in (a[0,:,3],a[-1,:,3],a[:,0,3],a[:,-1,3])) for a in frames):
                errors.append(key+': canvas clipping')
            for i,a in enumerate(frames):
                png=Image.open(folder/clip['individualFrames']/f'frame_{i+1:02d}.png')
                if png.mode!='RGBA' or png.size!=(256,256) or png.tobytes()!=a.tobytes():errors.append(key+': individual frame mismatch')
            if 'imagegen' not in clip['technique'] or clip.get('headTurn'):
                original_colors=set()
                for source_name in ([clip['source']] if clip.get('headTurn') else clip.get('sources',[clip['source']])):
                    source=np.asarray(Image.open(folder/source_name).convert('RGBA'))
                    original_colors.update(map(tuple,source[source[:,:,3]>0]))
                new_colors=set(map(tuple,array[array[:,:,3]>0]))-original_colors
                if new_colors:errors.append(key+': changed original palette')
            else:
                for a in frames:
                    logical=Image.fromarray(a).resize((64,64),Image.Resampling.NEAREST).resize((256,256),Image.Resampling.NEAREST)
                    if not np.array_equal(a,np.asarray(logical)):errors.append(key+': not a 64px hard-edge grid')
            diffs=[int(np.count_nonzero(np.any(frames[i]!=frames[(i+1)%len(frames)],axis=2))) for i in range(len(frames))]
            if diffs[-1]>max(diffs[:-1])*1.5+10:warnings.append(key+': visible wrap should be reviewed')
            with Image.open(folder/clip['gif']) as gif:
                duration=0
                if gif.info.get('loop')!=0:errors.append(key+': GIF not looped')
                for i in range(gif.n_frames):
                    gif.seek(i);duration+=gif.info.get('duration',0)
                    if gif.convert('RGBA').getpixel((0,0))[3]!=0:errors.append(key+': GIF background not transparent')
                expected=sum(clip['durations']) if 'durations' in clip else clip['frames']*clip['frameMs']
                if duration!=expected:errors.append(key+': GIF timing mismatch')
                if gif.n_frames!=clip['gifFrames']:errors.append(key+': GIF metadata mismatch')
            checks.append({'entity':row['id'],'action':action,'frames':clip['frames'],
                           'uniquePoses':unique,'durationMs':duration,'alpha':[0,255],
                           'wrapChangedPixels':diffs[-1],'maxAdjacentChangedPixels':max(diffs)})
    approval=json.loads((ROOT/'validation/back-walk-approval.json').read_text())
    for role,entry in approval['roles'].items():
        for name,value in entry['assetSHA256'].items():
            if sha(ROOT/'characters'/role/name)!=value:errors.append(role+': previously approved back-walk art changed')
    result={'entities':len(generated['rows']),'newClips':len(checks),'newFrames':sum(c['frames'] for c in checks),
            'preservedOriginalFiles':len(baseline),'errors':errors,'warnings':warnings,'checks':checks,
            'humanApproval':'pending for new daily actions only; previous back-walk approval retained'}
    (DEST/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='checks'},ensure_ascii=False,indent=2))
    return bool(errors)

if __name__=='__main__':raise SystemExit(main())
