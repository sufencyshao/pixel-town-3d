import sys,math,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
from build_daily_actions import prepare_human
from head_turn import head_layer,CUT_Y,YAW_DEGREES,DURATIONS
from animate_existing import palette_frames

def original_palette(original):
 a=np.asarray(original);colors=np.unique(a[a[:,:,3]==255,:3],axis=0).astype(int)
 q=original.convert('RGB').quantize(colors=256,dither=Image.Dither.NONE)
 p=np.array(q.getpalette()).reshape(-1,3).astype(int)
 chosen=colors[((p[:,None]-colors[None])**2).sum(axis=2).argmin(axis=1)]
 pal=Image.new('P',(1,1));pal.putpalette(chosen.astype('uint8').ravel().tolist());return pal

def head_poses(folder):
 f,box=prepare_human(folder);role=int(folder.name[:2]);cut=CUT_Y[role-1]
 front_head=head_layer(Image.fromarray(f),role,0,cut);target=front_head.getbbox()
 source=ROOT/'production/head-turn-solid-20261003'/folder.name/'generated-head-poses.png';sheet=Image.open(source).convert('RGBA')
 alpha=sheet.getchannel('A').point(lambda v:255 if v>=128 else 0)
 colors=sheet.convert('RGB').quantize(palette=original_palette(Image.fromarray(f)),dither=Image.Dither.NONE).convert('RGBA');colors.putalpha(alpha)
 arr=np.array(colors);arr[arr[:,:,3]==0]=0;sheet=Image.fromarray(arr)
 cells=[];anchors=[]
 for i in range(8):
  row,col=divmod(i,4);im=sheet.crop((round(col*sheet.width/4),round(row*sheet.height/2),round((col+1)*sheet.width/4),round((row+1)*sheet.height/2)))
  a=np.asarray(im);bb=im.getbbox();x0,y0,x1,y1=bb
  # Neck anchor: low opaque pixels at the centre, away from lateral hair.
  span=a[y0:y1,round((x0+x1)/2-(x1-x0)*.08):round((x0+x1)/2+(x1-x0)*.08),3]
  neck_y=y0+np.where(span.any(axis=1))[0][-1]+1
  aa=np.asarray(im);neck_rows=aa[max(y0,neck_y-12):neck_y,:,3]>0
  xx=np.where(neck_rows)[1];neck_x=float(np.median(xx)) if len(xx) else (x0+x1)/2
  cells.append((im,bb,neck_x,neck_y));anchors.append([neck_x,neck_y])
 neutral=cells[0];sx=(target[2]-target[0])/(neutral[1][2]-neutral[1][0])
 target_top=target[1];target_height=cut-target_top
 layer={0:front_head}
 for i,angle in [(1,-15),(2,-25.980762),(3,-30),(5,15),(6,25.980762),(7,30)]:
  im,bb,nx,ny=cells[i];sy=target_height/(ny-bb[1])
  crop=im.crop(bb).resize((round((bb[2]-bb[0])*sx),round((bb[3]-bb[1])*sy)),Image.Resampling.NEAREST)
  canvas=Image.new('RGBA',(256,256));canvas.paste(crop,(round(128-(nx-bb[0])*sx),target_top));layer[angle]=canvas
 base=f.copy();base[np.asarray(front_head)[:,:,3]>0]=0;body=Image.fromarray(base)
 out=[]
 for angle in YAW_DEGREES:
  if angle==0:im=Image.fromarray(f)
  else:im=body.copy();im.alpha_composite(layer[angle])
  out.append(im)
 return out,anchors
folder=ROOT/'characters/01_hero_male';poses,anchors=head_poses(folder);dest=Path(__file__).parent
imgs=palette_frames(poses);imgs[0].save(dest/'hero-whole-head-sample.gif',save_all=True,append_images=imgs[1:],duration=DURATIONS,loop=0,transparency=0,disposal=2,optimize=False)
board=Image.new('RGB',(7*256,256),'#e1e6de');draw=ImageDraw.Draw(board)
for col,index in enumerate([0,1,2,3,7,8,9]):
 board.paste(poses[index],(col*256,0),poses[index]);draw.text((col*256+4,240),str(YAW_DEGREES[index]),fill='#223c2c')
board.save(dest/'hero-generated-poses.png');print(anchors)
