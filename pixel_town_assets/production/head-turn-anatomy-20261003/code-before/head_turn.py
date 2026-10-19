"""Whole-head yaw keyposes, illustrated from original directional references.

Slicing, palette matching and registration retain hard edges and original body.
"""
import math
import json
import hashlib
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

REVISION = '20261003-refusal-fixed-joints-v6'
MAX_YAW_DEGREES = 30
FRAME_MS = 30
SHAKE_COUNT = 2
YAW_DEGREES = [round(-MAX_YAW_DEGREES*math.sin(i*math.pi/6),6) for i in range(25)]
YAW_DEGREES[0] = YAW_DEGREES[12] = YAW_DEGREES[24] = 0
DURATIONS = [FRAME_MS]*24+[480]
CUT_Y = [113,116,115,138,115,124,121,122,119,122,
         139,118,140,126,147,115,120,124,130,120,
         122,123,131,129,126,127,128,126,127,129,
         122,125,136,129,130,134,126,125,124,135]
# Only hair may extend below the neck. These registered rectangles exclude
# hands/props and the central shirt; their pixels are selected by hair colour.
HAIR_REGIONS = {
    12: {0:[(150,118,180,175)],-1:[(147,118,185,180)],1:[(74,118,119,180)]},
    17: {0:[(149,120,181,151)],-1:[(147,120,184,159)],1:[(74,120,116,159)]},
    19: {0:[(54,130,99,149),(157,130,202,149)],-1:[(150,130,211,181)],1:[(49,130,116,181)]},
    20: {0:[(149,120,195,158)],-1:[(149,120,205,178)],1:[(55,120,118,178)]},
    30: {0:[(50,129,100,154),(156,129,205,154)],-1:[(149,129,193,169)],1:[(63,129,117,169)]},
    33: {0:[(97,136,119,179),(138,136,163,179)],-1:[(143,136,176,175)],1:[(81,136,116,175)]},
    36: {0:[(47,134,106,148),(168,134,205,141)],-1:[(146,134,220,169)],1:[(37,134,116,169)]},
    39: {0:[(69,124,120,166)],-1:[(145,124,188,173)],1:[(65,124,117,173)]},
}

def legacy_head_layer(layer,role,direction,cut):
    a=np.array(layer);yy,xx=np.mgrid[:256,:256]
    mask=(yy<cut)&(a[:,:,3]>0)
    # Exclude isolated props above the neck (the musician's guitar neck).
    seen=np.zeros(mask.shape,bool);parts=[]
    for y,x in zip(*np.where(mask)):
        if seen[y,x]:continue
        q=[(int(y),int(x))];seen[y,x]=True;points=[]
        while q:
            cy,cx=q.pop();points.append((cy,cx))
            for dy,dx in ((-1,0),(1,0),(0,-1),(0,1)):
                ny,nx=cy+dy,cx+dx
                if 0<=ny<256 and 0<=nx<256 and mask[ny,nx] and not seen[ny,nx]:
                    seen[ny,nx]=True;q.append((ny,nx))
        parts.append(points)
    largest=max(parts,key=len);ys,xs=zip(*largest)
    box=(min(xs),min(ys),max(xs)+1,max(ys)+1)
    mask[:]=False
    for points in parts:
        py,px=zip(*points)
        b=(min(px),min(py),max(px)+1,max(py)+1)
        dx=max(box[0]-b[2],b[0]-box[2],0);dy=max(box[1]-b[3],b[1]-box[3],0)
        if role in (4,11) or points is largest or (dx<=3 and dy<=3):mask[py,px]=True
    r,g,b=a[:,:,:3].astype(int).transpose(2,0,1)
    maximum=110 if role in (33,36,39) else 150
    value=np.maximum.reduce([r,g,b])
    hair=(r>=g-4)&(g>=b-15)&(g-b<=50)&(value<=maximum)&(value>=35)&(a[:,:,3]>0)
    for x0,y0,x1,y1 in HAIR_REGIONS.get(role,{}).get(direction,[]):
        region=(xx>=x0)&(xx<x1)&(yy>=y0)&(yy<y1)
        candidate=(xx>=x0)&(xx<x1)&(yy>=y0-3)&(yy<y1)&hair
        selected=np.zeros_like(mask);q=[]
        for sy,sx in zip(*np.where(candidate&mask)):
            selected[sy,sx]=True;q.append((int(sy),int(sx)))
        while q:
            cy,cx=q.pop()
            for dy,dx in ((-1,0),(1,0),(0,-1),(0,1)):
                ny,nx=cy+dy,cx+dx
                if 0<=ny<256 and 0<=nx<256 and candidate[ny,nx] and not selected[ny,nx]:
                    selected[ny,nx]=True;q.append((ny,nx))
        # A one-pixel opaque outline belongs to the same hair cluster.
        expanded=selected.copy()
        for _ in range(2):
            old=expanded.copy();expanded[1:]|=old[:-1];expanded[:-1]|=old[1:]
            expanded[:,1:]|=old[:,:-1];expanded[:,:-1]|=old[:,1:]
        mask|=expanded&region&(a[:,:,3]>0)
    if role==36 and direction==0:
        # The final black tip of this ponytail has no coloured core, so the
        # colour-seeded extension misses it. It is above the shirt shoulder.
        mask|=(xx>=47)&(xx<107)&(yy>=cut)&(yy<144)&(a[:,:,3]>0)
    a[~mask]=0
    return Image.fromarray(a)

CALIBRATION = json.loads((Path(__file__).with_name('head_joint_calibration.json')).read_text())

def joint_masks(front, role):
    """Keep the original collar, shoulder contour and lower neck as foreground.

    Each contour is annotated on the original normalized sprite. Detached head
    pixels are included: old connected-component selection lost complete faces.
    """
    yy,xx=np.mgrid[:256,:256];cfg=CALIBRATION[str(role)]
    points=np.asarray(cfg['bodyBoundary'])
    boundary=np.interp(np.arange(256),points[:,0],points[:,1])
    body_region=yy>=boundary[None,:]
    tail_image=Image.new('1',(256,256));draw=ImageDraw.Draw(tail_image)
    for polygon in cfg['originalHairPolygons']:draw.polygon([tuple(p) for p in polygon],fill=1)
    r,g,b=front[:,:,:3].astype(int).transpose(2,0,1)
    hair=(r>=g-4)&(g>=b-15)&(g-b<=50)&(np.maximum.reduce([r,g,b])<=150)
    tail=np.asarray(tail_image)&hair&(front[:,:,3]>0)
    # Fine hair tips under the head/body contour are not garment pixels.
    if role in (2,12,13,14,15,16,18,19,20,30,32,35,36,38,40):
        xl,xr,_=cfg['neckRoot']
        fringe=body_region&(yy<boundary[None,:]+6)&((xx<xl-9)|(xx>xr+9))
        tail|=fringe&hair&(front[:,:,3]>0)
        if role==35:
            blonde=(r>=140)&(g>=80)&(g-b>=30)&(r>=g-5)
            tail|=body_region&(yy<boundary[None,:]+12)&((xx<xl)|(xx>xr))&blonde&(front[:,:,3]>0)
    # Lower braids rest against the torso; preserve their original overlap
    # with clothing instead of inventing hidden shoulder/shirt pixels.
    braid_join={12:108,33:128,39:119}.get(role)
    if braid_join is not None:tail[braid_join:]=False
    xl,xr,join=cfg['neckRoot'];join=min(join,cfg['targetNeckEnd'][1]-3)
    neck_root=(xx>=xl)&(xx<=xr)&(yy>=join)
    body_region|=neck_root
    body=body_region&(front[:,:,3]>0)&~tail
    # Independent original garment landmarks also preserve pale/transparent
    # shirt interiors and small collar outlines at the traced boundary.
    for x0,y0,x1,y1 in cfg['fixedGarmentRects']:
        body[y0:y1,x0:x1]=True;body_region[y0:y1,x0:x1]=True;tail[y0:y1,x0:x1]=False
    moving=(front[:,:,3]>0)&~body
    # The guitar neck is a fixed prop, spatially separate from the skull.
    if role==10:
        prop=(xx>=172)&(yy>=110);body|=prop&(front[:,:,3]>0);moving&=~prop
    return moving,body,body_region,tail

def head_layer(layer,role,direction,cut):
    if direction!=0:return legacy_head_layer(layer,role,direction,cut)
    a=np.array(layer);moving,_,_,_=joint_masks(a,role);a[~moving]=0
    return Image.fromarray(a)

def skin_neck_anchor(im, minimum, minimum_g):
    """Locate the bottom of the face/neck skin component, excluding long hair.

    Work on a small mask to find the face, then measure its full-resolution
    neck pixels. This anchor never uses the bottom extent of a braid/ponytail.
    """
    a=np.asarray(im);r,g,b=a[:,:,:3].astype(int).transpose(2,0,1)
    skin=(a[:,:,3]>0)&(r>=minimum)&(g>=minimum_g)&(r-g>=12)&(g-b>=8)
    small=np.asarray(Image.fromarray(skin).resize((im.width//4,im.height//4),Image.Resampling.NEAREST))
    seen=np.zeros_like(small);largest=[]
    for y,x in zip(*np.where(small)):
        if seen[y,x]:continue
        q=[(int(y),int(x))];seen[y,x]=True;points=[]
        while q:
            cy,cx=q.pop();points.append((cy,cx))
            for dy,dx in ((-1,0),(1,0),(0,-1),(0,1)):
                ny,nx=cy+dy,cx+dx
                if 0<=ny<small.shape[0] and 0<=nx<small.shape[1] and small[ny,nx] and not seen[ny,nx]:
                    seen[ny,nx]=True;q.append((ny,nx))
        if len(points)>len(largest):largest=points
    if not largest:raise ValueError('No face skin component for neck registration')
    sy,sx=zip(*largest);x0=max(0,min(sx)*4-4);x1=min(im.width,(max(sx)+1)*4+4)
    y0=max(0,min(sy)*4-4);y1=min(im.height,(max(sy)+1)*4+4)
    local=skin[y0:y1,x0:x1];rows=np.where(local.any(axis=1))[0]
    ny=y0+int(rows[-1])+2
    xx=np.where(skin[max(y0,ny-8):min(ny,y1),x0:x1])[1]+x0
    nx=float(np.median(xx))
    return nx,ny

def original_palette(original):
    """Every quantizer entry is an actual opaque colour from the original."""
    a=np.asarray(original);colors=np.unique(a[a[:,:,3]==255,:3],axis=0).astype(int)
    q=original.convert('RGB').quantize(colors=256,dither=Image.Dither.NONE)
    p=np.array(q.getpalette()).reshape(-1,3).astype(int)
    chosen=colors[((p[:,None]-colors[None])**2).sum(axis=2).argmin(axis=1)]
    pal=Image.new('P',(1,1));pal.putpalette(chosen.astype('uint8').ravel().tolist())
    return pal

KEY_CELLS=[(1,-15),(2,-25.980762),(3,-30),(5,15),(6,25.980762),(7,30)]

def clean_cell(im):
    """Drop distant generated flecks, retaining detached pixels within the head."""
    a=np.array(im);small=np.asarray(im.getchannel('A').resize((im.width//4,im.height//4),Image.Resampling.NEAREST))>0
    seen=np.zeros_like(small);largest=[]
    for y,x in zip(*np.where(small)):
        if seen[y,x]:continue
        points=[];q=[(int(y),int(x))];seen[y,x]=True
        while q:
            cy,cx=q.pop();points.append((cy,cx))
            for dy,dx in ((-1,0),(1,0),(0,-1),(0,1)):
                ny,nx=cy+dy,cx+dx
                if 0<=ny<small.shape[0] and 0<=nx<small.shape[1] and small[ny,nx] and not seen[ny,nx]:
                    seen[ny,nx]=True;q.append((ny,nx))
        if len(points)>len(largest):largest=points
    yy,xx=zip(*largest);sx=im.width/small.shape[1];sy=im.height/small.shape[0]
    bb=[max(0,round(min(xx)*sx)-10),max(0,round(min(yy)*sy)-10),min(im.width,round((max(xx)+1)*sx)+10),min(im.height,round((max(yy)+1)*sy)+10)]
    a[:bb[1]]=0;a[bb[3]:]=0;a[:,:bb[0]]=0;a[:,bb[2]:]=0
    return Image.fromarray(a)

def registered_heads(folder,front):
    role=int(folder.name[:2]);cut=CALIBRATION[str(role)]['targetNeckEnd'][1]
    original=Image.fromarray(front);front_head=head_layer(original,role,0,cut)
    target=front_head.getbbox()
    path=folder/'source/shake-head-solid-poses.png'
    raw=Image.open(path).convert('RGBA')
    alpha=raw.getchannel('A').point(lambda v:255 if v>=128 else 0)
    sheet=raw.convert('RGB').quantize(palette=original_palette(original),dither=Image.Dither.NONE).convert('RGBA')
    sheet.putalpha(alpha);a=np.array(sheet);a[a[:,:,3]==0]=0;sheet=Image.fromarray(a)
    overrides_path=folder/'source/shake-head-solid-anchors.json'
    overrides=json.loads(overrides_path.read_text()) if overrides_path.exists() else {}
    cells=[];anchors=[]
    for i in range(8):
        row,col=divmod(i,4)
        im=sheet.crop((round(col*sheet.width/4),round(row*sheet.height/2),round((col+1)*sheet.width/4),round((row+1)*sheet.height/2)))
        im=clean_cell(im);a=np.asarray(im);bb=im.getbbox()
        if not bb:raise ValueError(folder.name+': empty generated head cell '+str(i))
        x0,y0,x1,y1=bb
        nx,ny=CALIBRATION[str(role)]['sourceNeckAnchors'][i]
        if str(i) in overrides:nx,ny=overrides[str(i)]
        cells.append((im,bb,nx,ny));anchors.append([nx,int(ny)])
    scale_box=target if role==36 else CALIBRATION[str(role)]['originalScaleBox']
    sx=(scale_box[2]-scale_box[0])/(cells[0][1][2]-cells[0][1][0])
    top=target[1];head_height=cut-top;layers={0:front_head};registration={}
    # Two legacy chef frames have transparent white hat interiors. A matching
    # illustrated neutral avoids flashing between an empty and a solid hat.
    illustrated_neutral=role in (4,11)
    for cell,angle in ([(0,0)] if illustrated_neutral else [])+KEY_CELLS:
        im,bb,nx,ny=cells[cell];sy=head_height/(ny-bb[1])
        crop=im.crop(bb).resize((max(1,round((bb[2]-bb[0])*sx)),max(1,round((bb[3]-bb[1])*sy))),Image.Resampling.NEAREST)
        paste=[round(CALIBRATION[str(role)]['targetNeckEnd'][0]-(nx-bb[0])*sx),top]
        canvas=Image.new('RGBA',(256,256));canvas.paste(crop,paste);layers[angle]=canvas
        registration[str(angle)]={'sheetCell':cell,'cropBox':list(bb),'neckAnchor':[nx,int(ny)],'scale':[sx,sy],'paste':paste}
    return layers,{'anchors':anchors,'keyRegistration':registration,'cutY':cut,'originalHeadBox':list(target),'rawSheetSize':list(raw.size),'neutralUsesOriginal':not illustrated_neutral}

def frames(folder,front,box):
    layers,registration=registered_heads(folder,front)
    role=int(folder.name[:2]);cut=registration['cutY']
    moving,foreground,region,tail=joint_masks(front,role)
    base=front.copy();base[moving]=0
    # Reconstruct only the torso area hidden by original strands. Sample the
    # unobscured original shirt toward the centre, never flowers/props/skin.
    envelopes={17:(146,166,109,138),30:(100,158,124,139),36:(98,162,129,146)}
    if role in envelopes:
        x0,x1,y0,y1=envelopes[role]
        for y,x in zip(*np.where(tail & region)):
            if not (x0<=x<x1 and y0<=y<y1):continue
            candidates=np.flatnonzero(foreground[y] & (np.arange(256)>=112) & (np.arange(256)<=145))
            if role==17:
                other=255-x
                if foreground[y,other]:base[y,x]=front[y,other]
            elif len(candidates):base[y,x]=front[y,candidates[np.argmin(abs(candidates-x))]]
    body=Image.fromarray(base);poses={0:Image.fromarray(front)}
    # Clothing and neck root remain in front of the rotating head. Clip the
    # generated neck to the original seam; long hair can still turn behind it.
    for angle,layer in list(layers.items()):
        if angle==0 and registration['neutralUsesOriginal']:continue
        a=np.array(layer)
        xl,xr,join=CALIBRATION[str(role)]['neckRoot'];join=min(join,cut-3);yy,xx=np.mgrid[:256,:256]
        neck_zone=(yy>=join)&(xx>=xl-8)&(xx<=xr+8)
        a[foreground | (neck_zone & region)]=0
        braid_join={12:108,33:128,39:119}.get(role)
        if braid_join is not None:a[(yy>=braid_join)&((xx<xl)|(xx>xr))]=0
        layers[angle]=Image.fromarray(a)
        im=body.copy();im.alpha_composite(layers[angle]);poses[angle]=im
    source_dir=folder/'source/shake-head-solid';source_dir.mkdir(exist_ok=True)
    paths={};hashes={}
    # Save the actual immutable original body selection for inspection.
    fixed_layer=front.copy();fixed_layer[~foreground]=0
    fixed_path=folder/'source/shake-head-joint-body.png';Image.fromarray(fixed_layer).save(fixed_path)
    moving_layer=front.copy();moving_layer[~moving]=0
    moving_path=folder/'source/shake-head-joint-original-head.png';Image.fromarray(moving_layer).save(moving_path)
    for angle,layer in layers.items():
        name=f'key_{angle:+g}.png';path=source_dir/name;layer.save(path)
        rel=path.relative_to(folder).as_posix();paths[str(angle)]=rel
        hashes[rel]=hashlib.sha256(path.read_bytes()).hexdigest()
    fixed=max(cut,int(np.where(moving)[0].max())+1,max(im.getbbox()[3] for im in layers.values()))
    metadata={'revision':REVISION,**registration,'bodyFixedFromY':fixed,
        'maxYawDegrees':MAX_YAW_DEGREES,'yawDegreesSequence':YAW_DEGREES,
        'angleInterpretation':'illustrated pose targets; not a measured 3D model',
        'shakeCount':SHAKE_COUNT,'activeDurationMs':24*FRAME_MS,
        'neutralPauseMs':DURATIONS[-1],'durations':DURATIONS,'frameMs':FRAME_MS,
        'loop':False,'previewLoop':True,'neutralFrameIndices':[0,6,12,18,24],
        'sources':['frame_01.png','frame_04.png','frame_07.png','source/shake-head-solid-poses.png'],
        'method':'imagegen whole-head keyposes referenced to original front and side sprites',
        'registeredHeadPaths':paths,'registeredHeadSHA256':hashes,
        'jointCalibration':CALIBRATION[str(role)],'fixedBodyPath':fixed_path.relative_to(folder).as_posix(),
        'fixedBodySHA256':hashlib.sha256(fixed_path.read_bytes()).hexdigest(),
        'originalHeadPath':moving_path.relative_to(folder).as_posix(),
        'originalHeadSHA256':hashlib.sha256(moving_path.read_bytes()).hexdigest(),
        'calibrationSHA256':hashlib.sha256(Path(__file__).with_name('head_joint_calibration.json').read_bytes()).hexdigest(),
        'lowerHairPolicy':'original lower braids against torso retained for roles 12,33,39','fixedOriginalBodyPixels':int((foreground & (front[:,:,3]>0)).sum()),
        'neckAnchorMethod':'per-role source anchors; neck skin corrections for roles 12,17,19,33,36,39','originalBodyForeground':True,
        'wholeHeadTurns':True,'headSilhouetteFixed':False,'palette':'original frame_01 opaque colours',
        'rollDegrees':0,'verticalMotion':0}
    return [poses[angle].copy() for angle in YAW_DEGREES],metadata
