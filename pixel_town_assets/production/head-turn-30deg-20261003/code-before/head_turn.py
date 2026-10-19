"""Pixel head-yaw key poses from each resident's original directional frames.

The frontal body is immutable. No head roll, y motion or alpha cross-fade.
"""
from pathlib import Path
import numpy as np
from PIL import Image

REVISION = '20261003-shake-yaw-v2'
CUT_Y = [113,116,115,138,115,124,121,122,119,122,
         139,118,140,126,147,115,120,124,130,120,
         122,123,131,129,126,127,128,126,127,129,
         122,125,136,129,130,134,126,125,124,135]
PHASES = [0,-1,-2,-3,-3,-3,-2,-1,0,1,2,3,3,3,2,1]
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
        if points is largest or (dx<=3 and dy<=3):mask[py,px]=True
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

def trimmed_pose(path):
    im=Image.open(path).convert('RGBA'); a=np.asarray(im); mask=a[:,:,3]>0
    seen=np.zeros(mask.shape,bool); components=[]
    for y,x in zip(*np.where(mask)):
        if seen[y,x]:continue
        q=[(int(y),int(x))];seen[y,x]=True;points=[]
        while q:
            cy,cx=q.pop();points.append((cy,cx))
            for dy,dx in ((-1,0),(1,0),(0,-1),(0,1)):
                ny,nx=cy+dy,cx+dx
                if 0<=ny<256 and 0<=nx<256 and mask[ny,nx] and not seen[ny,nx]:
                    seen[ny,nx]=True;q.append((ny,nx))
        ys,xs=zip(*points);components.append((len(points),(min(xs),min(ys),max(xs)+1,max(ys)+1)))
    _,box=max(components)
    # Keep nearby disconnected outlines (notably white chefs' hats), while
    # dropping distant neighbouring-grid fragments in several right frames.
    changed=True
    while changed:
        changed=False
        for size,b in components:
            dx=max(box[0]-b[2],b[0]-box[2],0);dy=max(box[1]-b[3],b[1]-box[3],0)
            if size>=2 and dx<=5 and dy<=5:
                merged=(min(box[0],b[0]),min(box[1],b[1]),max(box[2],b[2]),max(box[3],b[3]))
                if merged!=box:box=merged;changed=True
    return im.crop(box),box

def source_keys(folder,front,box):
    role=int(folder.name[:2]);cut=CUT_Y[role-1];_,top,_,height=box
    front_head=head_layer(Image.fromarray(front),role,0,cut)
    keys={0:front_head};registrations={}
    for direction,frame,mirror in ((-1,7 if role==2 else 4,role==2),(1,7,False)):
        pose,cropbox=trimmed_pose(folder/f'frame_{frame:02d}.png')
        # Directional sources are independently trimmed; fit the same head
        # height, then align their neck using the torso's centre, not the nose.
        source_cut=round(pose.height*(cut-top)/height)
        source_cut=max(1,min(source_cut,pose.height))
        scale=(cut-top)/source_cut
        head=pose.resize((round(pose.width*scale),round(pose.height*scale)),Image.Resampling.NEAREST)
        arr=np.asarray(pose); centers=[]
        for y in range(round(pose.height*.67),round(pose.height*.87)):
            xs=np.flatnonzero(arr[y,:,3])
            if len(xs):centers.append((xs[0]+xs[-1])/2)
        anchor=float(np.median(centers)) if centers else pose.width/2
        if mirror:
            head=head.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            anchor=pose.width-1-anchor
        x=round(128-anchor*scale);y=round(top)
        layer=Image.new('RGBA',(256,256));layer.paste(head,(x,y))
        keys[direction]=head_layer(layer,role,direction,cut)
        registrations[str(direction)]={'source':f'frame_{frame:02d}.png','mirrored':mirror,
            'trimBox':list(cropbox),'sourceHeadCut':source_cut,'scale':scale,'paste':[x,y]}
    fixed=max([cut]+[r[3] for regions in HAIR_REGIONS.get(role,{}).values() for r in regions])
    return keys,{'revision':REVISION,'cutY':cut,'bodyFixedFromY':fixed,
        'hairRegions':HAIR_REGIONS.get(role,{}),
        'yawKeySequence':PHASES,'leftProfilePhase':3,'rightProfilePhase':11,
        'registrations':registrations,'rollDegrees':0,'verticalMotion':0}

def frontal_quarter(front_head,direction,cut):
    a=np.asarray(front_head);yy,xx=np.mgrid[:256,:256]
    bb=front_head.getbbox();radius=max((bb[2]-bb[0])/2,1)
    z=(xx-128)/radius
    neck_weight=np.clip((cut-yy)/18,0,1)
    amount=direction*.16*neck_weight
    disc=np.maximum(1-4*amount*(z-amount),0)
    u=2*(z-amount)/(1+np.sqrt(disc))
    sx=np.rint(np.where(np.abs(z)<=1,128+radius*u,xx)).astype(int)
    valid=(sx>=0)&(sx<256)
    out=np.zeros_like(a);out[valid]=a[yy[valid],sx[valid]]
    return Image.fromarray(out)

def frames(folder,front,box):
    keys,metadata=source_keys(folder,front,box);cut=metadata['cutY']
    poses={0:keys[0]}
    for direction in (-1,1):
        poses[direction]=frontal_quarter(keys[0],direction,cut)
        # A small horizontal perspective step toward the registered profile;
        # y and the neck stay fixed and pixels are selected with nearest sampling.
        a=np.asarray(keys[direction]);yy,xx=np.mgrid[:256,:256]
        weight=np.clip((cut-yy)/18,0,1)
        sx=np.rint(128+(xx-128)/(1+.06*weight)).astype(int)
        valid=(sx>=0)&(sx<256);out=np.zeros_like(a)
        out[valid]=a[yy[valid],sx[valid]]
        poses[2*direction]=Image.fromarray(out);poses[3*direction]=keys[direction]
    # Reconstruct only the tiny shirt areas occluded by the original hair,
    # reusing opaque frontal-body pixels in the same row. Outside the actual
    # body span, the old hair is removed to transparency, avoiding ghost tails.
    base=front.copy();mask=np.asarray(keys[0])[:,:,3]>0;base[mask]=0
    for y in range(cut,metadata['bodyFixedFromY']):
        body_x=np.flatnonzero(base[y,:,3])
        if not len(body_x):continue
        missing=np.flatnonzero(mask[y]&(np.arange(256)>=body_x[0])&(np.arange(256)<=body_x[-1]))
        for x in missing:
            nearest=body_x[np.argmin(np.abs(body_x-x))];base[y,x]=base[y,nearest]
    body=Image.fromarray(base)
    output=[]
    for phase in PHASES:
        im=body.copy();im.alpha_composite(poses[phase]);output.append(im)
    return output,metadata
