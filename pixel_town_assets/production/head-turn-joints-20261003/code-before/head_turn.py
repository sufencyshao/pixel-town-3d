"""Whole-head yaw keyposes, illustrated from original directional references.

Slicing, palette matching and registration retain hard edges and original body.
"""
import math
import json
import hashlib
from pathlib import Path
import numpy as np
from PIL import Image

REVISION = '20261003-refusal-whole-head-v5'
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

def head_layer(layer,role,direction,cut):
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
    role=int(folder.name[:2]);cut=CUT_Y[role-1]
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
        cx=(x0+x1)/2;half=(x1-x0)*.08
        stripe=a[y0:y1,round(cx-half):round(cx+half),3]
        ny=y0+np.where(stripe.any(axis=1))[0][-1]+1
        neck=a[max(y0,ny-12):ny,:,3]>0
        xx=np.where(neck)[1];nx=float(np.median(xx)) if len(xx) else cx
        if str(i) in overrides:nx,ny=overrides[str(i)]
        cells.append((im,bb,nx,ny));anchors.append([nx,int(ny)])
    sx=(target[2]-target[0])/(cells[0][1][2]-cells[0][1][0])
    top=target[1];head_height=cut-top;layers={0:front_head};registration={}
    # Two legacy chef frames have transparent white hat interiors. A matching
    # illustrated neutral avoids flashing between an empty and a solid hat.
    illustrated_neutral=role in (4,11)
    for cell,angle in ([(0,0)] if illustrated_neutral else [])+KEY_CELLS:
        im,bb,nx,ny=cells[cell];sy=head_height/(ny-bb[1])
        crop=im.crop(bb).resize((max(1,round((bb[2]-bb[0])*sx)),max(1,round((bb[3]-bb[1])*sy))),Image.Resampling.NEAREST)
        paste=[round(128-(nx-bb[0])*sx),top]
        canvas=Image.new('RGBA',(256,256));canvas.paste(crop,paste);layers[angle]=canvas
        registration[str(angle)]={'sheetCell':cell,'cropBox':list(bb),'neckAnchor':[nx,int(ny)],'scale':[sx,sy],'paste':paste}
    return layers,{'anchors':anchors,'keyRegistration':registration,'cutY':cut,'originalHeadBox':list(target),'rawSheetSize':list(raw.size),'neutralUsesOriginal':not illustrated_neutral}

def frames(folder,front,box):
    layers,registration=registered_heads(folder,front)
    source_dir=folder/'source/shake-head-solid';source_dir.mkdir(exist_ok=True)
    paths={};hashes={}
    for angle,layer in layers.items():
        name=f'key_{angle:+g}.png';path=source_dir/name;layer.save(path)
        rel=path.relative_to(folder).as_posix();paths[str(angle)]=rel
        hashes[rel]=hashlib.sha256(path.read_bytes()).hexdigest()
    cut=registration['cutY'];head=head_layer(Image.fromarray(front),int(folder.name[:2]),0,cut);mask=np.asarray(head)[:,:,3]>0
    base=front.copy();base[mask]=0
    fixed=max(im.getbbox()[3] for im in layers.values())
    # Reveal only shirt pixels formerly covered by a braid/ponytail. Reuse
    # an opaque body colour from this same row, within its existing span.
    for y in range(cut,min(fixed,256)):
        body_x=np.flatnonzero(base[y,:,3])
        if not len(body_x):continue
        missing=np.flatnonzero(mask[y]&(np.arange(256)>=body_x[0])&(np.arange(256)<=body_x[-1]))
        for x in missing:base[y,x]=base[y,body_x[np.argmin(np.abs(body_x-x))]]
    body=Image.fromarray(base);poses={0:Image.fromarray(front)}
    for angle,layer in layers.items():
        if angle==0 and registration['neutralUsesOriginal']:continue
        im=body.copy();im.alpha_composite(layer);poses[angle]=im
    metadata={'revision':REVISION,**registration,'bodyFixedFromY':fixed,
        'maxYawDegrees':MAX_YAW_DEGREES,'yawDegreesSequence':YAW_DEGREES,
        'angleInterpretation':'illustrated pose targets; not a measured 3D model',
        'shakeCount':SHAKE_COUNT,'activeDurationMs':24*FRAME_MS,
        'neutralPauseMs':DURATIONS[-1],'durations':DURATIONS,'frameMs':FRAME_MS,
        'loop':False,'previewLoop':True,'neutralFrameIndices':[0,6,12,18,24],
        'sources':['frame_01.png','frame_04.png','frame_07.png','source/shake-head-solid-poses.png'],
        'method':'imagegen whole-head keyposes referenced to original front and side sprites',
        'registeredHeadPaths':paths,'registeredHeadSHA256':hashes,
        'wholeHeadTurns':True,'headSilhouetteFixed':False,'palette':'original frame_01 opaque colours',
        'rollDegrees':0,'verticalMotion':0}
    return [poses[angle].copy() for angle in YAW_DEGREES],metadata
