"""Bounded head yaw using each resident's original frontal pixels.

The frontal body is immutable. No head roll, y motion or alpha cross-fade.
"""
import math
import numpy as np
from PIL import Image

REVISION = '20261003-refusal-rounded-v4'
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

def bounded_yaw(head,degrees,cut):
    """Yaw the curved face texture while retaining the head's full silhouette.

    v=u+a*(1-u*u), a=0.6*tan(theta), maps both contour endpoints to
    themselves. At +/-30 degrees it is monotonic, so no folded texture or
    flattening occurs. This is a 2D volume-preserving yaw approximation,
    not a recovered 3D head. The original opaque mask and colours remain.
    """
    a=np.asarray(head);out=a.copy()
    if degrees==0:return Image.fromarray(out)
    for y in range(min(cut,256)):
        xs=np.flatnonzero(a[y,:,3])
        if len(xs)<5:continue
        left,right=int(xs[0]),int(xs[-1])
        center=(left+right)/2;radius=max((right-left)/2,1)
        theta=math.radians(degrees)*np.clip((cut-y)/18,0,1)
        v=(xs-center)/radius;amount=.6*math.tan(theta)
        discriminant=np.maximum(1-4*amount*(v-amount),0)
        u=2*(v-amount)/(1+np.sqrt(discriminant))
        requested=np.rint(center+radius*u).astype(int)
        # Sample only existing opaque pixels in this row. Never pull empty
        # alpha into the rear head, hair or glasses as the face turns.
        nearest=np.abs(xs[:,None]-requested[None,:]).argmin(axis=0)
        out[y,xs]=a[y,xs[nearest]]
    return Image.fromarray(out)

def frames(folder,front,box):
    role=int(folder.name[:2]);cut=CUT_Y[role-1]
    head=head_layer(Image.fromarray(front),role,0,cut)
    # Below the neck yaw is zero. All frontal hair/garments are restored
    # exactly, so no newly exposed shoulder pixels need reconstruction.
    base=front.copy();base[np.asarray(head)[:,:,3]>0]=0;body=Image.fromarray(base)
    poses={}
    for angle in set(YAW_DEGREES):
        im=body.copy();im.alpha_composite(bounded_yaw(head,angle,cut));poses[angle]=im
    metadata={'revision':REVISION,'cutY':cut,'bodyFixedFromY':cut,
        'maxYawDegrees':MAX_YAW_DEGREES,'yawDegreesSequence':YAW_DEGREES,
        'shakeCount':SHAKE_COUNT,'activeDurationMs':24*FRAME_MS,
        'neutralPauseMs':DURATIONS[-1],'durations':DURATIONS,
        'frameMs':FRAME_MS,'loop':False,'previewLoop':True,
        'neutralFrameIndices':[0,6,12,18,24],'sources':['frame_01.png'],
        'projection':'volume-preserving curved texture yaw with original silhouette',
        'outlinePreserved':True,'headWidthRatio':1.0,'curveDepthRatio':.6,
        'rollDegrees':0,'verticalMotion':0}
    return [poses[angle].copy() for angle in YAW_DEGREES],metadata
