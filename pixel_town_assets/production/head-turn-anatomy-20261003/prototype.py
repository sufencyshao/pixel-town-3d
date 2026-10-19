from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
from build_daily_actions import residents,prepare_human
from head_turn import CALIBRATION,original_palette,clean_cell,head_layer,joint_masks
DEST=ROOT/'validation/head-turn-anatomy'
SOURCE_JAW={12:[308,306,311,308,None,296,294,296],17:[350,350,351,349,None,318,319,318],40:[350,347,343,345,None,345,342,339]}
KEYS=[(0,0),(1,-15),(2,-25.980762),(3,-30),(5,15),(6,25.980762),(7,30)]
JAW=[107,107,112,136,102,121,112,120,112,117,
     136,101,137,111,132,101,103,114,121,105,
     118,123,124,127,123,116,120,122,121,117,
     118,117,122,128,123,128,119,117,119,126]
NECK_END=[116,114,125,142,112,125,118,128,128,129,
          140,111,143,122,141,110,115,124,133,111,
          121,134,136,133,137,130,130,128,127,129,
          120,129,132,133,139,135,130,127,132,139]

def skin_mask(a,role):
    cfg=CALIBRATION[str(role)];r,g,b=a[:,:,:3].astype(int).transpose(2,0,1)
    minr,ming=cfg['skinMinR'],cfg['skinMinG']
    if role in (9,21,22,26,28,31):minr,ming=80,45
    return (a[:,:,3]>128)&(r>=minr)&(g>=ming)&(r-g>=12)&(g-b>=8)

def landmarks(a,role,end=None):
    skin=skin_mask(a,role)
    if end is not None:skin[end:]=False
    ny=int(np.where(skin)[0].max())+1
    nx=float(np.median(np.where(skin[max(0,ny-8):ny])[1]))
    counts=skin.sum(axis=1)
    # Jaw-to-neck narrowing, evaluated below the cheeks rather than the hat.
    start=max(0,ny-round(a.shape[0]*.23))
    local=counts[start:ny]
    if role==28:
        mask=a[:,:,3]>128;counts=mask.sum(axis=1);local=counts[start:ny]
    threshold=skin[max(0,ny-8):ny].sum(axis=1).max()*1.50
    candidates=np.where(counts[start:ny]>threshold)[0]
    jaw=start+int(candidates[-1])+1 if len(candidates) else ny-10
    return nx,ny,jaw

def neck_mask(raw,role,nx,ny,jaw):
    a=np.asarray(raw);skin=skin_mask(a,role);mask=np.zeros(skin.shape,bool)
    radius=round(raw.width*.15);prev=None
    for y in range(max(0,jaw+3),min(raw.height,ny+7)):
        xs=np.flatnonzero(skin[y]&(np.arange(raw.width)>=nx-radius)&(np.arange(raw.width)<=nx+radius))
        if len(xs):prev=(max(0,int(xs.min())-4),min(raw.width,int(xs.max())+5))
        if prev:mask[y,prev[0]:prev[1]]=a[y,prev[0]:prev[1],3]>128
    return mask

def draft_masks(front,role):
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
    if role!=38:return
    pol=Image.new('1',(256,256));d=ImageDraw.Draw(pol)
    for pts in [[(103,123),(110,120),(115,120),(117,124),(104,126)],[(141,120),(149,122),(154,126),(140,125)]]:
        d.polygon(pts,fill=1)
    mask=np.asarray(pol)&(base[:,:,3]==0)
    for y,x in zip(*np.where(mask)):
        for sy in range(y+1,min(256,y+9)):
            rgb=front[sy,x,:3].astype(int)
            if front[sy,x,3] and rgb[1]-rgb[2]>18 and rgb[0]<155:
                base[y,x]=front[sy,x];break

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
        if y<NECK_END[role-1]-4:continue
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

def make(p):
    role=int(p.name[:2]);cfg=CALIBRATION[str(role)];front,box=prepare_human(p)
    moving,fixed,region,tail=draft_masks(front,role)
    base=front.copy();base[moving]=0
    # Retain bounded v6 occluded-shirt repair for the first candidate only.
    envelopes={17:(146,166,109,138),30:(100,158,124,139),36:(98,162,129,146)}
    if role in envelopes:
        x0,x1,y0,y1=envelopes[role]
        for y,x in zip(*np.where(tail&region)):
            if not(x0<=x<x1 and y0<=y<y1):continue
            cand=np.flatnonzero(fixed[y]&(np.arange(256)>=112)&(np.arange(256)<=145))
            if role==17:
                if fixed[y,255-x]:base[y,x]=front[y,255-x]
            elif len(cand):base[y,x]=front[y,cand[np.argmin(abs(cand-x))]]
    repair_shoulder_cap(base,front,role)
    braid,braid_mask=original_braids(front,base,role);moving|=braid_mask;fixed&=~braid_mask
    original_head=np.asarray(head_layer(Image.fromarray(front),role,0,cfg['targetNeckEnd'][1]))
    jaw=JAW[role-1];oy=NECK_END[role-1]
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
        nx,ny,jy=landmarks(np.asarray(orig),role,end=round(cfg['sourceNeckAnchors'][i][1])+3)
        if role in SOURCE_JAW and SOURCE_JAW[role][i] is not None:jy=SOURCE_JAW[role][i]
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
    poses={};record={'role':p.name,'originalJawY':jaw,'originalSkinEnd':oy,'source':[]}
    for cell,angle in KEYS:
        if cell==0 and role not in (4,11):poses[angle]=Image.fromarray(front);continue
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
        ba[repair]=pa[repair];poses[angle]=Image.fromarray(ba)
        record['source'].append({'cell':cell,'neck':[nx,ny],'jawY':jy,'scale':[sx,sy],'paste':[x,top]})
    return poses,record

def run():
    records=[]
    for page in range(8):
        board=Image.new('RGB',(1932,1100),'#dce2d9');draw=ImageDraw.Draw(board)
        for row,p in enumerate(residents('characters')[page*5:page*5+5]):
            poses,rec=make(p);records.append(rec);stage=DEST/'candidate'/p.name;stage.mkdir(parents=True,exist_ok=True)
            for col,(_,angle) in enumerate(KEYS):
                im=poses[angle];im.save(stage/f'{angle:g}.png')
                tile=im.crop((59,65,197,165)).resize((276,200),Image.Resampling.NEAREST)
                x=col*276;y=row*220;board.paste(tile,(x,y+20),tile);draw.text((x+4,y+3),p.name+f' {angle:g}',fill='#173423')
        board.save(DEST/f'candidate-{page+1}.png');print('Candidate page',page+1,flush=True)
    (DEST/'candidate-registration.json').write_text(json.dumps(records,indent=2)+'\n')

if __name__=='__main__':run()
