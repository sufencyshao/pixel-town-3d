"""Registered whole skull and separate neck, composited over a stable body.

Landmarks are frozen after source and sprite review. Raw artwork is unchanged;
all sampling uses nearest neighbour and the original character palette.
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageDraw
from head_turn import CALIBRATION,original_palette,clean_cell,head_layer,joint_masks
ANATOMY=json.loads(Path(__file__).with_name('head_anatomy_calibration.json').read_text())
KEYS=[(0,0),(1,-15),(2,-25.980762),(3,-30),(5,15),(6,25.980762),(7,30)]

def skin_mask(a,role):
    cfg=CALIBRATION[str(role)];r,g,b=a[:,:,:3].astype(int).transpose(2,0,1)
    minr,ming=cfg['skinMinR'],cfg['skinMinG']
    if role in (9,21,22,26,28,31):minr,ming=80,45
    return (a[:,:,3]>128)&(r>=minr)&(g>=ming)&(r-g>=12)&(g-b>=8)

def neck_mask(raw,role,nx,ny,jaw):
    a=np.asarray(raw);skin=skin_mask(a,role);mask=np.zeros(skin.shape,bool)
    radius=round(raw.width*.15);prev=None
    for y in range(max(0,jaw+3),min(raw.height,ny+7)):
        xs=np.flatnonzero(skin[y]&(np.arange(raw.width)>=nx-radius)&(np.arange(raw.width)<=nx+radius))
        if len(xs):prev=(max(0,int(xs.min())-4),min(raw.width,int(xs.max())+5))
        if prev:mask[y,prev[0]:prev[1]]=a[y,prev[0]:prev[1],3]>128
    return mask

def anatomy_masks(front,role):
    moving,fixed,region,tail=joint_masks(front,role)
    yy,xx=np.mgrid[:256,:256];cfg=CALIBRATION[str(role)]
    r,g,b=front[:,:,:3].astype(int).transpose(2,0,1)
    hair=(r>=g-4)&(g>=b-15)&(g-b<=50)&(np.maximum.reduce([r,g,b])<=150)&(front[:,:,3]>0)
    if role==12:
        pol=Image.new('1',(256,256));d=ImageDraw.Draw(pol)
        for points in cfg['originalHairPolygons']:d.polygon([tuple(v) for v in points],fill=1)
        tail|=np.array(pol)&hair
    if role==39:
        # Original short hair behind the other ear is not a fixed shoulder.
        tail|=hair&(yy>=119)&(yy<124)&(xx>=148)&(xx<178)
    if role==38:
        # Tight bounds exclude the olive coat, whose hue overlaps a generic
        # dark-hair threshold. Only the grey/purple bob ends are selected.
        for x0,y0,x1,y1 in ((76,116,115,124),(143,116,184,123)):
            tail[y0:y1,x0:x1]|=hair[y0:y1,x0:x1]&((g-b)[y0:y1,x0:x1]<=9)
    moving|=tail;fixed&=~tail
    return moving,fixed,region,tail

def repair_shoulder_cap(base,front,role):
    if role==39:
        # The neutral braid hides the entire left shoulder cap. Its original
        # opposite shoulder provides the matching uniform and outer outline;
        # use only exposed body pixels, never the old hair or face.
        original_base=base.copy()
        for y in range(119,156):
            for x in range(74,117):
                mirror=original_base[y,255-x];rgb=mirror[:3].astype(int)
                cloth=(rgb[2]>rgb[0]*1.1 and rgb[2]>rgb[1]*1.05) or rgb.max()<42
                # The upper-arm insignia can be revealed beside the braid;
                # exclude the different shield on the opposite chest.
                cloth|=x<=101 and rgb[0]>110 and rgb[1]>85 and rgb[2]<90
                if base[y,x,3]==0 and mirror[3] and cloth:base[y,x]=mirror
        return
    if role!=38:return
    pol=Image.new('1',(256,256));d=ImageDraw.Draw(pol)
    for pts in [[(95,126),(103,122),(110,119),(116,120),(117,128),(94,128)],
                [(140,120),(147,120),(155,123),(164,126),(164,129),(140,129)]]:
        d.polygon(pts,fill=1)
    mask=np.asarray(pol)&(base[:,:,3]==0)
    for y,x in zip(*np.where(mask)):
        for sy in range(y+1,min(256,y+15)):
            rgb=front[sy,x,:3].astype(int)
            if front[sy,x,3] and rgb[1]-rgb[2]>18 and rgb[0]<155:
                base[y,x]=front[sy,x];break
    # Continue the coat's dark contour across the newly exposed cap. The
    # line uses a real original outline colour and belongs to the body only.
    edge=Image.new('1',(256,256));ed=ImageDraw.Draw(edge)
    ed.line([(95,126),(103,122),(110,119),(116,120)],fill=1,width=1)
    ed.line([(140,120),(147,120),(155,123),(164,126)],fill=1,width=1)
    dark=front[126:143,84:104];samples=dark[(dark[:,:,3]>0)&(dark[:,:,:3].max(axis=2)<35)]
    if len(samples):base[np.asarray(edge)&(base[:,:,3]>0)]=samples[0]

def original_braids(front,base,role):
    if role not in (33,39):return None,np.zeros((256,256),bool)
    pol=Image.new('1',(256,256));d=ImageDraw.Draw(pol)
    if role==33:polygons=[[(96,114),(120,114),(120,148),(114,179),(99,184),(95,146)],[(135,114),(164,114),(165,154),(160,183),(136,182),(134,147)]]
    else:polygons=[[(78,109),(114,109),(116,137),(111,161),(96,168),(79,162),(76,138)]]
    for points in polygons:d.polygon(points,fill=1)
    r,g,b=front[:,:,:3].astype(int).transpose(2,0,1)
    mask=np.asarray(pol)&(r>=g-4)&(g>=b-15)&(np.maximum.reduce([r,g,b])<110)&(front[:,:,3]>0)
    base[mask]=0
    # Reveal only the hidden shirt, cloning actual unobscured row pixels.
    for y,x in zip(*np.where(mask)):
        if y<ANATOMY[str(role)]["targetNeckEndY"]-4:continue
        opaque=np.flatnonzero(base[y,:,3]>0)
        if not len(opaque) or x<opaque.min() or x>opaque.max():continue
        candidates=np.flatnonzero((base[y,:,3]>0)&(np.arange(256)>=116)&(np.arange(256)<=140))
        if len(candidates):base[y,x]=front[y,candidates[np.argmin(abs(candidates-x))]]
    a=front.copy();a[~mask]=0
    return a,mask

def bend_braid(a,angle,role):
    if a is None:return Image.new('RGBA',(256,256))
    out=np.zeros_like(a);start={33:114,39:109}[role];end={33:181,39:167}[role]
    for y in range(start,end+1):
        dx=round(angle/30*5*max(0,1-(y-start)/(end-start)))
        if dx>=0:out[y,dx:]=a[y,:256-dx]
        else:out[y,:256+dx]=a[y,-dx:]
    return Image.fromarray(out)

def build_poses(p,front):
    role=int(p.name[:2]);cfg=CALIBRATION[str(role)];anatomy=ANATOMY[str(role)]
    moving,fixed,region,tail=anatomy_masks(front,role)
    base=front.copy();base[moving]=0
    # Restore small original shirt regions hidden by the neutral hairstyle.
    envelopes={17:(146,166,109,138),30:(100,158,124,139),36:(98,162,129,146)}
    if role in envelopes:
        x0,x1,y0,y1=envelopes[role]
        for y,x in zip(*np.where(tail&region)):
            if not(x0<=x<x1 and y0<=y<y1):continue
            cand=np.flatnonzero(fixed[y]&(np.arange(256)>=112)&(np.arange(256)<=145))
            if role==17:
                if fixed[y,255-x]:base[y,x]=front[y,255-x]
            elif len(cand):base[y,x]=front[y,cand[np.argmin(abs(cand-x))]]
    braid,braid_mask=original_braids(front,base,role);moving|=braid_mask;fixed&=~braid_mask
    repair_shoulder_cap(base,front,role)
    original_head=np.asarray(head_layer(Image.fromarray(front),role,0,cfg['targetNeckEnd'][1]))
    jaw=anatomy["targetJawY"];oy=anatomy["targetNeckEndY"]
    top=int(np.where(original_head[:,:,3]>0)[0].min())
    yy,xx=np.mgrid[:256,:256]
    original_neck=skin_mask(front,role)&(yy>=jaw)&(yy<oy)&(xx>=cfg['neckRoot'][0]-3)&(xx<=cfg['neckRoot'][1]+3)
    base[original_neck]=front[original_neck]
    raw=Image.open(p/'source/shake-head-solid-poses.png').convert('RGBA')
    sheet=raw.convert('RGB').quantize(palette=original_palette(Image.fromarray(front)),dither=Image.Dither.NONE).convert('RGBA')
    sheet.putalpha(raw.getchannel('A').point(lambda v:255 if v>=128 else 0))
    rawcells=[]
    for i in range(8):
        col=i%4;row=i//4
        im=clean_cell(sheet.crop((round(col*raw.width/4),round(row*raw.height/2),round((col+1)*raw.width/4),round((row+1)*raw.height/2))))
        # Landmarks measured before palette reduction: dark hair must not
        # acquire the same palette colour as a shaded neck.
        orig=raw.crop((round(col*raw.width/4),round(row*raw.height/2),round((col+1)*raw.width/4),round((row+1)*raw.height/2)))
        point=anatomy['sourceLandmarks'][i];nx=point['neckX'];ny=point['neckEndY'];jy=point['jawY']
        if role==12:
            # Pale hair-tie pixels at the braid tip are a bad generated remnant.
            ia=np.array(im);rows=np.indices(ia.shape[:2])[0];bad=skin_mask(np.array(orig),role)&(rows>ny+15)&(ia[:,:,3]>0)
            for by,bx in zip(*np.where(bad)):
                local=ia[max(0,by-9):by+10,max(0,bx-9):bx+10];dark=(local[:,:,3]>0)&(local[:,:,:3].max(axis=2)<135)
                if dark.any():ia[by,bx,:3]=local[dark,:3][0]
            im=Image.fromarray(ia)
        nm=neck_mask(orig,role,nx,ny,jy)
        rawcells.append((im,im.getbbox(),nx,ny,jy,nm))
    skull=(original_head[:,:,3]>0)&(yy<jaw+1)
    sx=(np.where(skull)[1].max()-np.where(skull)[1].min()+1)/(rawcells[0][1][2]-rawcells[0][1][0])
    heads={};poses={};record={'role':p.name,'originalJawY':jaw,'originalSkinEnd':oy,'source':[]}
    for cell,angle in KEYS:
        if cell==0 and role not in (4,11):
            a=front.copy();a[~moving]=0;heads[angle]=Image.fromarray(a)
            if role in (38,39):
                neutral=Image.fromarray(base);neutral.alpha_composite(heads[angle]);poses[angle]=neutral
            else:poses[angle]=Image.fromarray(front)
            continue
        im,bb,nx,ny,jy,nm=rawcells[cell]
        sy=(jaw-top)/(jy-bb[1]);scale_y=sy
        full=im.copy();ia=np.array(im);ia[nm]=0;im=Image.fromarray(ia)
        crop=im.crop(bb).resize((round((bb[2]-bb[0])*sx),round((bb[3]-bb[1])*sy)),Image.Resampling.NEAREST)
        x=round(cfg['targetNeckEnd'][0]-(nx-bb[0])*sx)
        layer=Image.new('RGBA',(256,256));layer.paste(crop,(x,top))
        pixels=np.array(rawcells[cell][0]);pixels[~nm]=0
        neck_crop=Image.fromarray(pixels).crop((bb[0],jy+3,bb[2],ny)).resize((crop.width,max(1,oy-jaw+2)),Image.Resampling.NEAREST)
        nc=Image.new('RGBA',(256,256));nc.paste(neck_crop,(x,jaw-2));neck=np.array(nc)
        neck[(yy>=jaw+4)&fixed&~original_neck]=0
        b=Image.fromarray(base);b.alpha_composite(bend_braid(braid,angle,role));b.alpha_composite(Image.fromarray(neck));b.alpha_composite(layer)
        # Reuse the uncut source at the two-pixel jaw overlap. Masking must
        # never introduce a transparent horizontal slit inside the chin.
        parent=Image.new('RGBA',(256,256));parent.paste(full.crop(bb).resize(crop.size,Image.Resampling.NEAREST),(x,top));pa=np.array(parent);ba=np.array(b)
        repair=(ba[:,:,3]==0)&(pa[:,:,3]>0)&(yy>=jaw-3)&(yy<=jaw+3)&(xx>=cfg['neckRoot'][0]-8)&(xx<=cfg['neckRoot'][1]+8)
        ba[repair]=pa[repair]
        # Close sub-pixel-source slits between the real chin and fitted neck.
        # Both anchors must exist in this column; no skin is added outside the
        # neck footprint. Colours are copied from this registered neck.
        closure=np.zeros((256,256),bool);head_pixels=np.array(layer);face_skin=skin_mask(head_pixels,role)
        for cx in range(max(0,cfg['neckRoot'][0]-8),min(256,cfg['neckRoot'][1]+9)):
            bottom=np.flatnonzero(neck[jaw+1:min(jaw+6,256),cx,3]>0)
            if not len(bottom):continue
            by=jaw+1+int(bottom[0])
            upper=np.flatnonzero(face_skin[max(0,jaw-6):by,cx])
            if not len(upper):continue
            ty=max(0,jaw-6)+int(upper[-1])
            if by-ty>5:continue
            for cy in range(ty+1,by):
                if ba[cy,cx,3]==0:ba[cy,cx]=neck[by,cx];closure[cy,cx]=True
        poses[angle]=Image.fromarray(ba)
        component=bend_braid(braid,angle,role);component.alpha_composite(Image.fromarray(neck));component.alpha_composite(layer)
        ca=np.array(component);ca[repair]=pa[repair];ca[closure]=ba[closure];ca[ca[:,:,3]==0]=0;heads[angle]=Image.fromarray(ca)
        record['source'].append({'cell':cell,'cropBox':list(bb),'neck':[nx,ny],'jawY':jy,'scale':[sx,sy],'paste':[x,top],'closedJointPixels':int(closure.sum())})
    record.update({"anatomyCalibration":anatomy,"originalHeadBox":list(Image.fromarray(original_head).getbbox()),"neutralUsesOriginal":role not in (4,11),"neutralBodyRepaired":role in (38,39),"rawSheetSize":list(raw.size),"cutY":oy})
    return poses,heads,base,moving,record
