import sys,math
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
from build_daily_actions import residents,prepare_human
from head_turn import head_layer,CUT_Y

def norm(path):
 im=Image.open(path).convert('RGBA');bb=im.getbbox();im=im.crop(bb);s=min(210/im.height,198/im.width)
 im=im.resize((round(im.width*s),round(im.height*s)),Image.Resampling.NEAREST)
 result=Image.new('RGBA',(256,256));result.paste(im,((256-im.width)//2,230-im.height));return result

def solid_yaw(front,back,angle,role):
 a=np.array(front);b=np.array(back);out=np.zeros_like(a);theta=math.radians(angle)
 # Every head point uses one common rigid Y-axis rotation. No face-only warp.
 for y in range(256):
  xs=np.flatnonzero(a[y,:,3])
  if not len(xs):continue
  left,right=int(xs[0]),int(xs[-1]);cx=(left+right)/2;rx=max((right-left)/2,1);rz=rx*.95
  center_z=-.22*rx
  screen_cx=128+(cx-128)*math.cos(theta)+center_z*math.sin(theta)
  radius=math.hypot(rx*math.cos(theta),rz*math.sin(theta));delta=math.atan2(rz*math.sin(theta),rx*math.cos(theta))
  target=np.arange(max(0,math.ceil(screen_cx-radius)),min(255,math.floor(screen_cx+radius))+1)
  phi=np.arcsin(np.clip((target-screen_cx)/radius,-1,1));lam=phi-delta
  source=np.rint(cx+rx*np.sin(lam)).astype(int)
  # Ink at the old frontal silhouette is not a seam painted on a 3D skull.
  rim=1 if role<=20 else 3
  source=np.clip(source,min(left+rim,right),max(right-rim,left))
  front_side=np.abs(lam)<=math.pi/2
  out[y,target[front_side]]=a[y,source[front_side]]
  bx=np.flatnonzero(b[y,:,3])
  if len(bx):
   bc=(bx[0]+bx[-1])/2;br=max((bx[-1]-bx[0])/2,1)
   requested=np.rint(bc-br*np.sin(lam[~front_side])).astype(int)
   near=np.abs(bx[:,None]-requested[None,:]).argmin(axis=0)
   out[y,target[~front_side]]=b[y,bx[near]]
  else:
   out[y,target[~front_side]]=a[y,source[~front_side]]
  # Contour follows the rendered solid; it is never fixed at the frontal rim.
  live=target[out[y,target,3]>0]
  if len(live)>rim*4:
   out[y,live[:rim]]=a[y,left];out[y,live[-rim:]]=a[y,right]
 return Image.fromarray(out)

chosen=[p for p in residents('characters') if int(p.name[:2]) in [1,2,4,8,21,35,36]]
board=Image.new('RGB',(1024,256*len(chosen)),'#e1e6de');draw=ImageDraw.Draw(board)
for row,p in enumerate(chosen):
 f,box=prepare_human(p);role=int(p.name[:2]);cut=CUT_Y[role-1]
 head=head_layer(Image.fromarray(f),role,0,cut);rear=head_layer(norm(p/'frame_10.png'),role,0,cut)
 base=f.copy();base[np.asarray(head)[:,:,3]>0]=0;body=Image.fromarray(base)
 old=Image.open(p/'animations/daily/shake_head.png').crop((768,0,1024,256))
 ims=[]
 for ang in [-30,30]:
  im=body.copy();im.alpha_composite(solid_yaw(head,rear,ang,role));ims.append(im)
 for col,(label,im) in enumerate(zip(['front','old face-only','solid -30','solid +30'],[Image.fromarray(f),old,*ims])):
  board.paste(im,(col*256,row*256),im);draw.text((col*256+4,row*256+240),p.name[:2]+' '+label,fill='#223c2c')
board.save(Path(__file__).with_name('solid-prototype.png'))
