#!/usr/bin/env python3
"""Verify the observed collar/neck defect against original pixels and scope."""
import json
import numpy as np
from PIL import Image
from build_daily_actions import ROOT,sha,write_json,prepare_human
from revise_wendou_joint import AUDIT,BACKUP,ROLE,protected_guard

def main():
    errors=[];before=json.loads((AUDIT/'before.json').read_text())
    try:protected_guard(before)
    except RuntimeError as e:errors.append(str(e))
    folder=ROOT/'characters'/ROLE;front,_=prepare_human(folder)
    mf=json.loads((folder/'animations/daily/manifest.json').read_text());clip=mf['animations']['shake_head'];meta=clip['headTurn']
    samples=json.loads((AUDIT/'garment-check-regions.json').read_text())
    poses=[np.array(Image.open(folder/clip['individualFrames']/f'frame_{i+1:02d}.png').convert('RGBA')) for i in range(25)]
    x0,y0,x1,y1=samples['fixedCentralJointRect']
    exact=[np.array_equal(p[y0:y1,x0:x1],front[y0:y1,x0:x1]) for p in poses]
    if not all(exact):errors.append('Original neck root and collar changed at phases '+str([i for i,v in enumerate(exact) if not v]))
    original_tip=front[137,140].tolist()
    if any(p[137,140].tolist()!=original_tip for p in poses):errors.append('V-neck tip moved or changed colour')
    body=np.array(Image.open(folder/meta['fixedBodyPath']).convert('RGBA'))
    moving=np.array(Image.open(folder/meta['originalHeadPath']).convert('RGBA'))
    garment_pixels=0
    for x0,y0,x1,y1 in samples['fixedGarmentRects']:
        if not np.array_equal(body[y0:y1,x0:x1],front[y0:y1,x0:x1]):errors.append(f'Actual garment sample missing from fixed body: {x0,y0,x1,y1}')
        if np.any(moving[y0:y1,x0:x1,3]):errors.append(f'Actual garment sample in moving head: {x0,y0,x1,y1}')
        garment_pixels+=(x1-x0)*(y1-y0)
    old=json.loads((BACKUP/f'characters/{ROLE}/animation.json').read_text())
    new=json.loads((folder/'animation.json').read_text())
    if any(new['animations'].get(k)!=v for k,v in old['animations'].items() if k!='shake_head'):errors.append('Other basic or daily clip metadata changed')
    for name in ['animation.json','animation-manifest.json']:
        if json.loads((folder/name).read_text())['animations']['shake_head']!=clip:errors.append('Manifest differs: '+name)
    if meta.get('roleRevision')!='20261003-wendou-joint-v1':errors.append('Missing role revision')
    if sha(ROOT/meta['roleCalibrationPath'])!=meta['roleCalibrationSHA256']:errors.append('Corrective calibration hash differs')
    if meta['jointCalibration']['targetNeckEnd']!=[140,138] or meta['anatomyCalibration']['targetJawY']!=125:errors.append('Wrong corrective anchors')
    neutral=[0,6,12,18,24]
    if not all(np.array_equal(poses[i],front) for i in neutral):errors.append('Original neutral frame changed')
    colors={tuple(c) for c in front[front[:,:,3]==255,:3]}
    for i,p in enumerate(poses):
        if p.shape!=(256,256,4) or set(np.unique(p[:,:,3]).tolist())!={0,255}:errors.append(f'Invalid hard-edge RGBA frame {i}')
        if any(tuple(c) not in colors for c in np.unique(p[p[:,:,3]==255,:3],axis=0)):errors.append(f'Colour outside original palette at phase {i}')
    changed=[n for n,v in before['replacedFileSHA256'].items() if sha(ROOT/n)!=v]
    result={'role':ROLE,'revision':meta['roleRevision'],'framesChecked':25,'uniquePoses':len({p.tobytes() for p in poses}),
        'neckAndCollarExactPhases':sum(exact),'independentGarmentSamples':len(samples['fixedGarmentRects']),
        'independentGarmentPixels':garment_pixels,'neckTipXY':[140,137],'originalNeckTipRGBA':original_tip,
        'neutralExactPhases':len(neutral),'preservedFileHashes':len(before['preservedFileSHA256'])-1,
        'separatelyProtectedDailyManifest':True,'frozenBackupFiles':len(before['replacedFileSHA256']),
        'changedAssetAndMetadataFiles':len(changed),'errors':errors,'userApproval':'pending for this corrective revision'}
    write_json(AUDIT/'validation.json',result);print(json.dumps(result,ensure_ascii=False,indent=2));return bool(errors)

if __name__=='__main__':raise SystemExit(main())
